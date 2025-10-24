"""
yFinance Data Extractor
========================
Downloads historical and real-time market data for multiple asset classes:
- Stocks (AAPL, MSFT, GOOGL, etc.)
- ETFs (SPY, QQQ, IWM, etc.)
- Cryptocurrencies (BTC-USD, ETH-USD, etc.)
- Forex (EURUSD=X, GBPUSD=X, etc.)
- Commodities (GC=F for Gold, CL=F for Oil, etc.)

Data is saved in the same format as Binance extractor for compatibility with existing ETL pipeline.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)


class YFinanceExtractor:
    """
    yFinance data extractor for multi-asset market data

    Supports:
    - Historical data download (1m, 5m, 15m, 1h, 1d, 1wk, 1mo)
    - Real-time data fetching (latest candles)
    - Multiple asset classes (stocks, crypto, ETFs, forex)
    - Data caching to avoid rate limits
    """

    # yFinance interval mapping
    INTERVAL_MAP = {
        '1m': '1m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '1h',
        '1d': '1d',
        '1wk': '1wk',
        '1mo': '1mo'
    }

    # Asset type mapping for validation
    ASSET_TYPES = {
        'stock': 'Stock',
        'etf': 'ETF',
        'crypto': 'Cryptocurrency',
        'forex': 'Forex',
        'commodity': 'Commodity',
        'index': 'Index'
    }

    def __init__(self, output_dir: str = 'data/raw/yfinance', cache_ttl: int = 60):
        """
        Initialize yFinance extractor

        Args:
            output_dir: Directory to save downloaded data
            cache_ttl: Cache time-to-live in seconds (default 60s)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.cache_ttl = cache_ttl
        self._cache = {}  # Symbol -> (timestamp, data)
        self._executor = ThreadPoolExecutor(max_workers=5)

        logger.info(f"YFinanceExtractor initialized - Output: {self.output_dir}")

    def _normalize_symbol(self, symbol: str, asset_type: str = 'stock') -> str:
        """
        Normalize symbol for yFinance API

        Args:
            symbol: Input symbol
            asset_type: Asset type ('stock', 'crypto', 'forex', 'commodity')

        Returns:
            Normalized symbol for yFinance

        Examples:
            'AAPL' -> 'AAPL' (stock)
            'BTC' -> 'BTC-USD' (crypto)
            'EURUSD' -> 'EURUSD=X' (forex)
            'GOLD' -> 'GC=F' (commodity)
        """
        symbol = symbol.upper()

        # Crypto: ensure -USD suffix
        if asset_type == 'crypto':
            if not symbol.endswith('-USD') and not symbol.endswith('-USDT'):
                symbol = f"{symbol}-USD"

        # Forex: ensure =X suffix
        elif asset_type == 'forex':
            if not symbol.endswith('=X'):
                symbol = f"{symbol}=X"

        # Commodity: ensure =F suffix (futures)
        elif asset_type == 'commodity':
            if not symbol.endswith('=F'):
                symbol = f"{symbol}=F"

        return symbol

    async def download_historical(
        self,
        symbol: str,
        period: str = '1y',
        interval: str = '1d',
        asset_type: str = 'stock',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Download historical OHLCV data

        Args:
            symbol: Trading symbol
            period: Data period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            interval: Candle interval ('1m', '5m', '15m', '1h', '1d', '1wk', '1mo')
            asset_type: Asset type ('stock', 'crypto', 'etf', 'forex', 'commodity')
            start_date: Start date (YYYY-MM-DD) - overrides period
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data

        Notes:
            - 1m data only available for last 7 days
            - 5m data only available for last 60 days
            - For longer history, use 1h or 1d intervals
        """
        try:
            normalized_symbol = self._normalize_symbol(symbol, asset_type)
            logger.info(f"Downloading {normalized_symbol} - Period: {period}, Interval: {interval}")

            # Download data in thread pool (yfinance is blocking)
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(
                self._executor,
                lambda: yf.Ticker(normalized_symbol)
            )

            # Download with period or date range
            if start_date:
                data = await loop.run_in_executor(
                    self._executor,
                    lambda: ticker.history(
                        start=start_date,
                        end=end_date,
                        interval=interval,
                        auto_adjust=True
                    )
                )
            else:
                data = await loop.run_in_executor(
                    self._executor,
                    lambda: ticker.history(
                        period=period,
                        interval=interval,
                        auto_adjust=True
                    )
                )

            if data.empty:
                logger.warning(f"No data returned for {normalized_symbol}")
                return pd.DataFrame()

            # Normalize to match Binance format
            data = self._normalize_dataframe(data, normalized_symbol, interval)

            # Save to disk
            filename = self.output_dir / f"{normalized_symbol}_{interval}_{period}.parquet"
            data.to_parquet(filename, index=False)
            logger.info(f"Saved {len(data)} candles to {filename}")

            # Also save as CSV for compatibility
            csv_filename = self.output_dir / f"{normalized_symbol}_{interval}_{period}.csv"
            data.to_csv(csv_filename, index=False)

            return data

        except Exception as e:
            logger.error(f"Error downloading {symbol}: {e}")
            raise

    def _normalize_dataframe(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        """
        Normalize yFinance DataFrame to match Binance format

        Binance format:
            timestamp, open, high, low, close, volume, close_time, quote_volume, trades, ...

        yFinance format:
            Date, Open, High, Low, Close, Volume
        """
        # Reset index to get Date as column
        df = df.reset_index()

        # Rename columns to lowercase
        df.columns = [col.lower() for col in df.columns]

        # Ensure 'date' column is renamed to 'timestamp'
        if 'date' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'])
            df = df.drop('date', axis=1)
        elif 'datetime' in df.columns:
            df['timestamp'] = pd.to_datetime(df['datetime'])
            df = df.drop('datetime', axis=1)

        # Convert timestamp to milliseconds (Binance format)
        df['timestamp'] = df['timestamp'].astype(np.int64) // 10**6

        # Add missing columns for compatibility
        df['close_time'] = df['timestamp'] + self._interval_to_ms(interval)
        df['symbol'] = symbol
        df['interval'] = interval

        # Ensure standard column order
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'symbol', 'interval']
        df = df[[col for col in columns if col in df.columns]]

        # Fill NaN values
        df = df.fillna(0)

        return df

    def _interval_to_ms(self, interval: str) -> int:
        """Convert interval string to milliseconds"""
        mapping = {
            '1m': 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '30m': 30 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '1wk': 7 * 24 * 60 * 60 * 1000,
            '1mo': 30 * 24 * 60 * 60 * 1000,
        }
        return mapping.get(interval, 60 * 1000)

    async def get_latest_data(
        self,
        symbol: str,
        interval: str = '1m',
        asset_type: str = 'stock'
    ) -> Optional[pd.Series]:
        """
        Get latest candle data (real-time)

        Args:
            symbol: Trading symbol
            interval: Candle interval
            asset_type: Asset type

        Returns:
            Latest candle as pandas Series or None
        """
        try:
            normalized_symbol = self._normalize_symbol(symbol, asset_type)

            # Check cache
            cache_key = f"{normalized_symbol}_{interval}"
            if cache_key in self._cache:
                cached_time, cached_data = self._cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_data

            # Download recent data
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(
                self._executor,
                lambda: yf.Ticker(normalized_symbol)
            )

            # Get last 5 periods to ensure we have latest complete candle
            data = await loop.run_in_executor(
                self._executor,
                lambda: ticker.history(period='5d', interval=interval, auto_adjust=True)
            )

            if data.empty:
                logger.warning(f"No data for {normalized_symbol}")
                return None

            # Get latest candle
            latest = data.iloc[-1]
            latest['symbol'] = normalized_symbol
            latest['interval'] = interval

            # Update cache
            self._cache[cache_key] = (time.time(), latest)

            return latest

        except Exception as e:
            logger.error(f"Error getting latest data for {symbol}: {e}")
            return None

    async def get_current_price(self, symbol: str, asset_type: str = 'stock') -> Optional[float]:
        """
        Get current market price

        Args:
            symbol: Trading symbol
            asset_type: Asset type

        Returns:
            Current price or None
        """
        try:
            normalized_symbol = self._normalize_symbol(symbol, asset_type)

            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(
                self._executor,
                lambda: yf.Ticker(normalized_symbol)
            )

            # Get fast info (cached)
            info = await loop.run_in_executor(
                self._executor,
                lambda: ticker.fast_info
            )

            # Try different price fields
            price = info.get('lastPrice') or info.get('regularMarketPrice')

            if price:
                return float(price)

            # Fallback: get from history
            data = await loop.run_in_executor(
                self._executor,
                lambda: ticker.history(period='1d', interval='1m')
            )

            if not data.empty:
                return float(data['Close'].iloc[-1])

            return None

        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None

    async def get_ticker_info(self, symbol: str, asset_type: str = 'stock') -> Dict:
        """
        Get ticker information

        Args:
            symbol: Trading symbol
            asset_type: Asset type

        Returns:
            Dictionary with ticker info (name, exchange, type, etc.)
        """
        try:
            normalized_symbol = self._normalize_symbol(symbol, asset_type)

            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(
                self._executor,
                lambda: yf.Ticker(normalized_symbol)
            )

            info = await loop.run_in_executor(
                self._executor,
                lambda: ticker.info
            )

            return {
                'symbol': normalized_symbol,
                'name': info.get('longName', info.get('shortName', normalized_symbol)),
                'exchange': info.get('exchange', 'N/A'),
                'asset_type': asset_type,
                'currency': info.get('currency', 'USD'),
                'market_cap': info.get('marketCap', 0),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
            }

        except Exception as e:
            logger.error(f"Error getting ticker info for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}

    async def validate_symbol(self, symbol: str, asset_type: str = 'stock') -> bool:
        """
        Validate if symbol exists and is tradable

        Args:
            symbol: Trading symbol
            asset_type: Asset type

        Returns:
            True if valid
        """
        try:
            normalized_symbol = self._normalize_symbol(symbol, asset_type)

            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(
                self._executor,
                lambda: yf.Ticker(normalized_symbol)
            )

            # Try to get info
            info = await loop.run_in_executor(
                self._executor,
                lambda: ticker.info
            )

            # Valid if we got meaningful info
            return bool(info and 'symbol' in info)

        except Exception:
            return False

    async def download_multiple_symbols(
        self,
        symbols: List[str],
        period: str = '1y',
        interval: str = '1d',
        asset_type: str = 'stock'
    ) -> Dict[str, pd.DataFrame]:
        """
        Download data for multiple symbols concurrently

        Args:
            symbols: List of symbols
            period: Data period
            interval: Candle interval
            asset_type: Asset type

        Returns:
            Dictionary of symbol -> DataFrame
        """
        tasks = [
            self.download_historical(symbol, period, interval, asset_type)
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            symbol: result
            for symbol, result in zip(symbols, results)
            if isinstance(result, pd.DataFrame) and not result.empty
        }

    def clear_cache(self):
        """Clear price cache"""
        self._cache.clear()
        logger.info("Cache cleared")

    def __del__(self):
        """Cleanup executor"""
        self._executor.shutdown(wait=False)


# Example usage
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def main():
        extractor = YFinanceExtractor()

        # Test stock download
        print("\n=== Downloading AAPL (Stock) ===")
        aapl_data = await extractor.download_historical(
            symbol='AAPL',
            period='1mo',
            interval='1d',
            asset_type='stock'
        )
        print(aapl_data.tail())

        # Test crypto download
        print("\n=== Downloading BTC (Crypto) ===")
        btc_data = await extractor.download_historical(
            symbol='BTC',
            period='1mo',
            interval='1d',
            asset_type='crypto'
        )
        print(btc_data.tail())

        # Test current price
        print("\n=== Getting Current Prices ===")
        aapl_price = await extractor.get_current_price('AAPL', 'stock')
        print(f"AAPL: ${aapl_price}")

        btc_price = await extractor.get_current_price('BTC', 'crypto')
        print(f"BTC: ${btc_price}")

        # Test ticker info
        print("\n=== Getting Ticker Info ===")
        info = await extractor.get_ticker_info('AAPL', 'stock')
        print(f"Name: {info['name']}")
        print(f"Exchange: {info['exchange']}")
        print(f"Sector: {info['sector']}")

    asyncio.run(main())
