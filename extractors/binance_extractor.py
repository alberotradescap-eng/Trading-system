"""
Extractor per dati realtime da Binance

Connette a Binance WebSocket per ricevere dati in tempo reale:
- Candele (klines)
- Order book
- Trades

Salva i dati in data/raw/
"""

import asyncio
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from binance import AsyncClient, BinanceSocketManager
from loguru import logger


class BinanceExtractor:
    """
    Estrae dati realtime da Binance e li salva su file
    """

    def __init__(self, api_key=None, api_secret=None, output_dir='data/raw'):
        """
        Args:
            api_key: Binance API key (opzionale per dati pubblici)
            api_secret: Binance API secret
            output_dir: Directory dove salvare i dati
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.output_dir = Path(output_dir)
        self.client = None
        self.bm = None

        # Crea directory se non esistono
        (self.output_dir / 'klines').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'orderbook').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'trades').mkdir(parents=True, exist_ok=True)

        # Buffer per dati in memoria
        self.klines_buffer = {}
        self.orderbook_buffer = {}
        self.trades_buffer = {}

        logger.info(f"BinanceExtractor inizializzato. Output: {self.output_dir}")

    async def connect(self):
        """Connette al client Binance"""
        self.client = await AsyncClient.create(self.api_key, self.api_secret)
        self.bm = BinanceSocketManager(self.client)
        logger.info("Connesso a Binance API")

    async def disconnect(self):
        """Disconnette dal client Binance"""
        if self.client:
            await self.client.close_connection()
        logger.info("Disconnesso da Binance API")

    # ========================================================================
    # KLINES (CANDELE) STREAM
    # ========================================================================

    async def start_kline_stream(self, symbol, interval='1m'):
        """
        Avvia stream di candele per un simbolo

        Args:
            symbol: Es. 'BTCUSDT'
            interval: '1m', '5m', '15m', '1h', etc.
        """
        stream_key = f"{symbol}_{interval}"
        self.klines_buffer[stream_key] = []

        logger.info(f"Avvio kline stream: {symbol} {interval}")

        async with self.bm.kline_socket(symbol=symbol, interval=interval) as stream:
            while True:
                try:
                    msg = await stream.recv()

                    if msg['e'] == 'kline':
                        kline = msg['k']

                        # Estrai dati candela
                        candle_data = {
                            'timestamp': datetime.fromtimestamp(kline['t'] / 1000),
                            'open': float(kline['o']),
                            'high': float(kline['h']),
                            'low': float(kline['l']),
                            'close': float(kline['c']),
                            'volume': float(kline['v']),
                            'close_time': datetime.fromtimestamp(kline['T'] / 1000),
                            'quote_volume': float(kline['q']),
                            'trades': int(kline['n']),
                            'is_closed': kline['x']  # True se candela completata
                        }

                        # Aggiungi a buffer
                        self.klines_buffer[stream_key].append(candle_data)

                        # Se candela chiusa, salva su file
                        if candle_data['is_closed']:
                            await self._save_klines_to_file(stream_key, symbol, interval)

                        logger.debug(f"Kline {symbol} {interval}: {candle_data['close']}")

                except Exception as e:
                    logger.error(f"Errore kline stream {symbol} {interval}: {e}")
                    await asyncio.sleep(5)

    async def _save_klines_to_file(self, stream_key, symbol, interval):
        """Salva klines buffer su file"""
        if not self.klines_buffer[stream_key]:
            return

        df = pd.DataFrame(self.klines_buffer[stream_key])

        # Nome file con data
        date_str = datetime.now().strftime('%Y%m%d')
        filename = self.output_dir / 'klines' / f"{symbol}_{interval}_{date_str}.csv"

        # Append to file
        if filename.exists():
            df.to_csv(filename, mode='a', header=False, index=False)
        else:
            df.to_csv(filename, index=False)

        logger.info(f"Salvate {len(df)} candele in {filename}")

        # Pulisci buffer
        self.klines_buffer[stream_key] = []

    # ========================================================================
    # ORDER BOOK STREAM
    # ========================================================================

    async def start_orderbook_stream(self, symbol, depth=10):
        """
        Avvia stream order book

        Args:
            symbol: Es. 'BTCUSDT'
            depth: Livelli di profondità (5, 10, 20)
        """
        logger.info(f"Avvio orderbook stream: {symbol} depth={depth}")

        async with self.bm.depth_socket(symbol=symbol, depth=depth) as stream:
            while True:
                try:
                    msg = await stream.recv()

                    orderbook_data = {
                        'timestamp': datetime.now(),
                        'symbol': symbol,
                        'bids': msg['bids'][:depth],  # [[price, quantity], ...]
                        'asks': msg['asks'][:depth],
                    }

                    # Calcola spread
                    best_bid = float(msg['bids'][0][0]) if msg['bids'] else 0
                    best_ask = float(msg['asks'][0][0]) if msg['asks'] else 0
                    spread = best_ask - best_bid if best_bid and best_ask else 0

                    orderbook_data['best_bid'] = best_bid
                    orderbook_data['best_ask'] = best_ask
                    orderbook_data['spread'] = spread

                    # Salva a intervalli (es. ogni 10 secondi)
                    await self._save_orderbook_snapshot(symbol, orderbook_data)

                    logger.debug(f"OrderBook {symbol}: bid={best_bid} ask={best_ask} spread={spread}")

                except Exception as e:
                    logger.error(f"Errore orderbook stream {symbol}: {e}")
                    await asyncio.sleep(5)

    async def _save_orderbook_snapshot(self, symbol, data):
        """Salva snapshot order book"""
        date_str = datetime.now().strftime('%Y%m%d')
        filename = self.output_dir / 'orderbook' / f"{symbol}_orderbook_{date_str}.jsonl"

        # Salva come JSON Lines
        with open(filename, 'a') as f:
            f.write(json.dumps(data, default=str) + '\n')

    # ========================================================================
    # TRADES STREAM
    # ========================================================================

    async def start_trades_stream(self, symbol):
        """
        Avvia stream di trades eseguiti

        Args:
            symbol: Es. 'BTCUSDT'
        """
        logger.info(f"Avvio trades stream: {symbol}")

        async with self.bm.trade_socket(symbol=symbol) as stream:
            while True:
                try:
                    msg = await stream.recv()

                    trade_data = {
                        'timestamp': datetime.fromtimestamp(msg['T'] / 1000),
                        'symbol': msg['s'],
                        'price': float(msg['p']),
                        'quantity': float(msg['q']),
                        'is_buyer_maker': msg['m'],  # True se sell, False se buy
                    }

                    # Aggiungi a buffer
                    if symbol not in self.trades_buffer:
                        self.trades_buffer[symbol] = []

                    self.trades_buffer[symbol].append(trade_data)

                    # Salva ogni 100 trades
                    if len(self.trades_buffer[symbol]) >= 100:
                        await self._save_trades_to_file(symbol)

                    logger.debug(f"Trade {symbol}: {trade_data['price']} x {trade_data['quantity']}")

                except Exception as e:
                    logger.error(f"Errore trades stream {symbol}: {e}")
                    await asyncio.sleep(5)

    async def _save_trades_to_file(self, symbol):
        """Salva trades buffer su file"""
        if symbol not in self.trades_buffer or not self.trades_buffer[symbol]:
            return

        df = pd.DataFrame(self.trades_buffer[symbol])

        date_str = datetime.now().strftime('%Y%m%d')
        filename = self.output_dir / 'trades' / f"{symbol}_trades_{date_str}.csv"

        # Append to file
        if filename.exists():
            df.to_csv(filename, mode='a', header=False, index=False)
        else:
            df.to_csv(filename, index=False)

        logger.info(f"Salvati {len(df)} trades in {filename}")

        # Pulisci buffer
        self.trades_buffer[symbol] = []

    # ========================================================================
    # HISTORICAL DATA DOWNLOAD
    # ========================================================================

    async def download_historical_klines(self, symbol, interval, start_date, end_date=None):
        """
        Scarica dati storici di candele

        Args:
            symbol: Es. 'BTCUSDT'
            interval: '1m', '5m', '1h', '1d', etc.
            start_date: Data inizio (string o datetime)
            end_date: Data fine (opzionale, default: ora)
        """
        logger.info(f"Download historical klines: {symbol} {interval} from {start_date}")

        klines = await self.client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=str(start_date),
            end_str=str(end_date) if end_date else None
        )

        # Converti in DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])

        # Converti tipi
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

        for col in ['open', 'high', 'low', 'close', 'volume', 'quote_volume']:
            df[col] = df[col].astype(float)

        # Salva
        filename = self.output_dir.parent / 'backtest' / f"{symbol}_{interval}_historical.parquet"
        df.to_parquet(filename)

        logger.info(f"Salvate {len(df)} candele storiche in {filename}")
        return df

    # ========================================================================
    # MULTI-STREAM MANAGER
    # ========================================================================

    async def start_multi_stream(self, symbols, intervals=['1m', '5m']):
        """
        Avvia stream multipli per più simboli e timeframe

        Args:
            symbols: Lista di simboli ['BTCUSDT', 'ETHUSDT']
            intervals: Lista di intervalli ['1m', '5m']
        """
        tasks = []

        for symbol in symbols:
            for interval in intervals:
                task = asyncio.create_task(self.start_kline_stream(symbol, interval))
                tasks.append(task)

        logger.info(f"Avviati {len(tasks)} stream")

        # Esegui tutti i task in parallelo
        await asyncio.gather(*tasks)


# ============================================================================
# ESEMPIO DI UTILIZZO
# ============================================================================

async def main():
    """Esempio di utilizzo"""
    from config.settings import BINANCE_CONFIG

    extractor = BinanceExtractor(
        api_key=BINANCE_CONFIG['api_key'],
        api_secret=BINANCE_CONFIG['api_secret']
    )

    await extractor.connect()

    try:
        # Avvia stream multipli
        await extractor.start_multi_stream(
            symbols=['BTCUSDT', 'ETHUSDT'],
            intervals=['1m', '5m']
        )

    except KeyboardInterrupt:
        logger.info("Interruzione utente")

    finally:
        await extractor.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
