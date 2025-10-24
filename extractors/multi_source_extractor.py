"""
Multi-Source Data Extractor
============================
Smart router that automatically selects the correct data source (Binance or yFinance)
based on symbol and asset type.

Features:
- Automatic routing to Binance for crypto pairs (BTCUSDT, ETHUSDT, etc.)
- Automatic routing to yFinance for stocks, ETFs, forex, commodities
- Unified interface for data extraction
- Caching and rate limiting
- Error handling and fallback
"""

import logging
from typing import Optional, List, Dict, Union
import pandas as pd
from pathlib import Path

from extractors.binance_extractor import BinanceExtractor
from extractors.yfinance_extractor import YFinanceExtractor

logger = logging.getLogger(__name__)


class MultiSourceExtractor:
    """
    Multi-source data extractor with automatic routing

    Routes data requests to appropriate source:
    - Binance: BTCUSDT, ETHUSDT, BNBUSDT, etc. (crypto trading pairs)
    - yFinance: AAPL, MSFT, SPY, BTC-USD, EURUSD=X, etc.
    """

    # Binance symbol patterns
    BINANCE_SUFFIXES = ['USDT', 'BUSD', 'BTC', 'ETH', 'BNB']

    def __init__(
        self,
        binance_extractor: Optional[BinanceExtractor] = None,
        yfinance_extractor: Optional[YFinanceExtractor] = None,
        output_dir: str = 'data/raw/multi'
    ):
        """
        Initialize multi-source extractor

        Args:
            binance_extractor: Optional BinanceExtractor instance
            yfinance_extractor: Optional YFinanceExtractor instance
            output_dir: Output directory for combined data
        """
        self.binance = binance_extractor or BinanceExtractor()
        self.yfinance = yfinance_extractor or YFinanceExtractor()

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("MultiSourceExtractor initialized with Binance + yFinance")

    def detect_source(self, symbol: str) -> tuple[str, str]:
        """
        Detect data source and asset type for a symbol

        Args:
            symbol: Trading symbol

        Returns:
            Tuple of (source, asset_type)
            source: 'binance' or 'yfinance'
            asset_type: 'crypto', 'stock', 'etf', 'forex', 'commodity'

        Examples:
            'BTCUSDT' -> ('binance', 'crypto')
            'AAPL' -> ('yfinance', 'stock')
            'BTC-USD' -> ('yfinance', 'crypto')
            'SPY' -> ('yfinance', 'etf')
            'EURUSD=X' -> ('yfinance', 'forex')
        """
        symbol_upper = symbol.upper()

        # Check for Binance patterns (crypto trading pairs)
        for suffix in self.BINANCE_SUFFIXES:
            if symbol_upper.endswith(suffix):
                logger.debug(f"{symbol} -> Binance (crypto pair)")
                return ('binance', 'crypto')

        # Check for yFinance patterns
        if '-USD' in symbol_upper or '-USDT' in symbol_upper:
            # yFinance crypto format
            logger.debug(f"{symbol} -> yFinance (crypto)")
            return ('yfinance', 'crypto')

        elif '=X' in symbol_upper:
            # Forex
            logger.debug(f"{symbol} -> yFinance (forex)")
            return ('yfinance', 'forex')

        elif '=F' in symbol_upper:
            # Commodity futures
            logger.debug(f"{symbol} -> yFinance (commodity)")
            return ('yfinance', 'commodity')

        elif symbol_upper in ['SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO']:
            # Common ETFs
            logger.debug(f"{symbol} -> yFinance (etf)")
            return ('yfinance', 'etf')

        else:
            # Default to stock
            logger.debug(f"{symbol} -> yFinance (stock)")
            return ('yfinance', 'stock')

    async def download_historical(
        self,
        symbol: str,
        period: Optional[str] = None,
        interval: str = '1d',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        force_source: Optional[str] = None,
        asset_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Download historical data from appropriate source

        Args:
            symbol: Trading symbol
            period: Data period (e.g., '1y', '6mo') - yFinance only
            interval: Candle interval ('1m', '5m', '1h', '1d', etc.)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            force_source: Force specific source ('binance' or 'yfinance')
            asset_type: Force specific asset type

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Detect source
            if force_source:
                source = force_source
                detected_asset_type = asset_type or 'crypto' if source == 'binance' else 'stock'
            else:
                source, detected_asset_type = self.detect_source(symbol)
                if asset_type:
                    detected_asset_type = asset_type

            logger.info(f"Downloading {symbol} from {source} ({detected_asset_type})")

            # Route to appropriate extractor
            if source == 'binance':
                # Binance uses start_time/end_time instead of period
                if start_date and end_date:
                    # Convert dates to timestamps (Binance format)
                    import pandas as pd
                    start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
                    end_ts = int(pd.Timestamp(end_date).timestamp() * 1000)

                    data = await self.binance.download_historical_data(
                        symbol=symbol,
                        interval=interval,
                        start_time=start_ts,
                        end_time=end_ts
                    )
                else:
                    # Download last N days (default)
                    data = await self.binance.download_historical_data(
                        symbol=symbol,
                        interval=interval
                    )

                # Add source metadata
                data['source'] = 'binance'
                data['asset_type'] = detected_asset_type

                return data

            elif source == 'yfinance':
                data = await self.yfinance.download_historical(
                    symbol=symbol,
                    period=period or '1y',
                    interval=interval,
                    asset_type=detected_asset_type,
                    start_date=start_date,
                    end_date=end_date
                )

                # Add source metadata
                data['source'] = 'yfinance'
                data['asset_type'] = detected_asset_type

                return data

            else:
                raise ValueError(f"Unknown source: {source}")

        except Exception as e:
            logger.error(f"Error downloading {symbol}: {e}")
            raise

    async def get_current_price(
        self,
        symbol: str,
        force_source: Optional[str] = None,
        asset_type: Optional[str] = None
    ) -> Optional[float]:
        """
        Get current price from appropriate source

        Args:
            symbol: Trading symbol
            force_source: Force specific source
            asset_type: Force specific asset type

        Returns:
            Current price or None
        """
        try:
            # Detect source
            if force_source:
                source = force_source
                detected_asset_type = asset_type or 'crypto' if source == 'binance' else 'stock'
            else:
                source, detected_asset_type = self.detect_source(symbol)
                if asset_type:
                    detected_asset_type = asset_type

            # Route to appropriate extractor
            if source == 'binance':
                # Get latest ticker from Binance
                ticker = await self.binance.get_ticker_24h(symbol)
                return float(ticker.get('lastPrice', 0))

            elif source == 'yfinance':
                return await self.yfinance.get_current_price(symbol, detected_asset_type)

            else:
                raise ValueError(f"Unknown source: {source}")

        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None

    async def get_latest_data(
        self,
        symbol: str,
        interval: str = '1m',
        force_source: Optional[str] = None,
        asset_type: Optional[str] = None
    ) -> Optional[Union[pd.Series, Dict]]:
        """
        Get latest candle data

        Args:
            symbol: Trading symbol
            interval: Candle interval
            force_source: Force specific source
            asset_type: Force specific asset type

        Returns:
            Latest candle as Series/Dict or None
        """
        try:
            # Detect source
            if force_source:
                source = force_source
                detected_asset_type = asset_type or 'crypto' if source == 'binance' else 'stock'
            else:
                source, detected_asset_type = self.detect_source(symbol)
                if asset_type:
                    detected_asset_type = asset_type

            # Route to appropriate extractor
            if source == 'binance':
                # Get latest klines from Binance
                klines = await self.binance.get_klines(symbol, interval, limit=1)
                if klines:
                    return klines[0]  # Return latest
                return None

            elif source == 'yfinance':
                return await self.yfinance.get_latest_data(symbol, interval, detected_asset_type)

            else:
                raise ValueError(f"Unknown source: {source}")

        except Exception as e:
            logger.error(f"Error getting latest data for {symbol}: {e}")
            return None

    async def get_symbol_info(
        self,
        symbol: str,
        force_source: Optional[str] = None,
        asset_type: Optional[str] = None
    ) -> Dict:
        """
        Get symbol information

        Args:
            symbol: Trading symbol
            force_source: Force specific source
            asset_type: Force specific asset type

        Returns:
            Dictionary with symbol info
        """
        try:
            # Detect source
            if force_source:
                source = force_source
                detected_asset_type = asset_type or 'crypto' if source == 'binance' else 'stock'
            else:
                source, detected_asset_type = self.detect_source(symbol)
                if asset_type:
                    detected_asset_type = asset_type

            # Route to appropriate extractor
            if source == 'binance':
                # Get exchange info from Binance
                info = await self.binance.get_exchange_info(symbol)
                return {
                    'symbol': symbol,
                    'source': 'binance',
                    'asset_type': detected_asset_type,
                    'info': info
                }

            elif source == 'yfinance':
                info = await self.yfinance.get_ticker_info(symbol, detected_asset_type)
                info['source'] = 'yfinance'
                return info

            else:
                raise ValueError(f"Unknown source: {source}")

        except Exception as e:
            logger.error(f"Error getting info for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}

    async def download_multiple_symbols(
        self,
        symbols: List[str],
        period: str = '1y',
        interval: str = '1d'
    ) -> Dict[str, pd.DataFrame]:
        """
        Download data for multiple symbols concurrently

        Args:
            symbols: List of symbols
            period: Data period
            interval: Candle interval

        Returns:
            Dictionary of symbol -> DataFrame
        """
        import asyncio

        tasks = [
            self.download_historical(symbol, period, interval)
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            symbol: result
            for symbol, result in zip(symbols, results)
            if isinstance(result, pd.DataFrame) and not result.empty
        }

    def get_supported_sources(self) -> List[str]:
        """Get list of supported data sources"""
        return ['binance', 'yfinance']

    def get_supported_asset_types(self) -> List[str]:
        """Get list of supported asset types"""
        return ['crypto', 'stock', 'etf', 'forex', 'commodity', 'index']


# Example usage
if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)

    async def main():
        extractor = MultiSourceExtractor()

        # Test symbol detection
        print("\n=== Symbol Detection ===")
        test_symbols = ['BTCUSDT', 'AAPL', 'BTC-USD', 'SPY', 'EURUSD=X', 'GC=F']
        for symbol in test_symbols:
            source, asset_type = extractor.detect_source(symbol)
            print(f"{symbol:15} -> {source:10} ({asset_type})")

        # Test downloading from Binance
        print("\n=== Downloading BTCUSDT (Binance) ===")
        btc_data = await extractor.download_historical('BTCUSDT', interval='1d')
        print(btc_data.tail())

        # Test downloading from yFinance
        print("\n=== Downloading AAPL (yFinance) ===")
        aapl_data = await extractor.download_historical('AAPL', period='1mo', interval='1d')
        print(aapl_data.tail())

        # Test current prices
        print("\n=== Current Prices ===")
        for symbol in ['BTCUSDT', 'AAPL', 'BTC-USD']:
            price = await extractor.get_current_price(symbol)
            print(f"{symbol}: ${price}")

    asyncio.run(main())
