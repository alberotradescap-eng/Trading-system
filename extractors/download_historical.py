"""
Download Historical Data

Scarica dati storici da Binance per backtesting.

Usage:
    python extractors/download_historical.py --symbol BTCUSDT --start 2024-01-01
    python extractors/download_historical.py --symbol ETHUSDT --start 2024-01-01 --end 2024-12-31 --interval 1h
"""

import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from loguru import logger

from binance_extractor import BinanceExtractor
from config.settings import BINANCE_CONFIG


async def download_historical(symbol, interval, start_date, end_date=None):
    """
    Scarica dati storici per un simbolo

    Args:
        symbol: Es. 'BTCUSDT'
        interval: '1m', '5m', '15m', '1h', '1d', etc.
        start_date: Data inizio
        end_date: Data fine (opzionale, default: oggi)
    """
    logger.info("=" * 70)
    logger.info("DOWNLOAD HISTORICAL DATA")
    logger.info("=" * 70)
    logger.info(f"Symbol: {symbol}")
    logger.info(f"Interval: {interval}")
    logger.info(f"Start: {start_date}")
    logger.info(f"End: {end_date or 'today'}")
    logger.info("=" * 70)

    # Inizializza extractor
    extractor = BinanceExtractor(
        api_key=BINANCE_CONFIG.get('api_key'),
        api_secret=BINANCE_CONFIG.get('api_secret')
    )

    await extractor.connect()

    try:
        # Download dati
        df = await extractor.download_historical_klines(
            symbol=symbol,
            interval=interval,
            start_date=start_date,
            end_date=end_date
        )

        logger.info(f"Download completato: {len(df)} candele")
        logger.info(f"Period: {df['timestamp'].min()} to {df['timestamp'].max()}")

        # Mostra sample
        logger.info("\nSample data:")
        print(df.head())

        return df

    finally:
        await extractor.disconnect()


def parse_args():
    parser = argparse.ArgumentParser(description='Download historical data from Binance')

    parser.add_argument(
        '--symbol',
        type=str,
        required=True,
        help='Symbol to download (es. BTCUSDT)'
    )

    parser.add_argument(
        '--interval',
        type=str,
        default='5m',
        choices=['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'],
        help='Candlestick interval (default: 5m)'
    )

    parser.add_argument(
        '--start',
        type=str,
        required=True,
        help='Start date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end',
        type=str,
        help='End date (YYYY-MM-DD, default: today)'
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Valida date
    try:
        start_dt = datetime.strptime(args.start, '%Y-%m-%d')
        end_dt = datetime.strptime(args.end, '%Y-%m-%d') if args.end else None
    except ValueError as e:
        logger.error(f"Formato data invalido: {e}")
        logger.info("Usa formato YYYY-MM-DD (es. 2024-01-01)")
        return

    # Download
    asyncio.run(download_historical(
        symbol=args.symbol,
        interval=args.interval,
        start_date=args.start,
        end_date=args.end
    ))

    logger.info("\n✅ Download completato!")
    logger.info(f"\nFile salvato in: data/backtest/{args.symbol}_{args.interval}_historical.parquet")
    logger.info("\nPer eseguire backtest:")
    logger.info(f"  python backtest.py --symbol {args.symbol} --start {args.start} --interval {args.interval}")


if __name__ == '__main__':
    main()
