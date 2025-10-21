"""
Trading System - Main Entry Point

Sistema di trading automatizzato per criptovalute.

Usage:
    python main.py --mode live                    # Live trading
    python main.py --mode backtest                # Backtesting
    python main.py --unlock                       # Sblocca dopo FINAL TP/SL
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

# Import componenti
from config.settings import CONFIG
from config.trading_rules import ACTIVE_STRATEGY
from extractors.binance_extractor import BinanceExtractor
from etl.indicator_calculator import IndicatorCalculator
from plugins.llm_advisor import LLMAdvisor
from notifications.audio_notifier import AudioNotifier
from notifications.telegram_notifier import TelegramNotifier


class TradingSystem:
    """
    Sistema di trading principale
    """

    def __init__(self, config):
        self.config = config
        self.is_running = False
        self.is_blocked = False  # Blocco per FINAL TP/SL
        self.daily_pnl = 0
        self.positions = []
        self.trades_today = 0

        # Setup logging
        self._setup_logging()

        # Inizializza componenti
        self._init_components()

    def _setup_logging(self):
        """Configura logging"""
        log_config = self.config['logging']

        # Crea directory logs
        Path(log_config['log_dir']).mkdir(exist_ok=True)

        # Configura loguru
        logger.remove()  # Rimuovi handler default

        # Console handler
        logger.add(
            sys.stdout,
            format=log_config['format'],
            level=log_config['level'],
            colorize=True
        )

        # File handler
        logger.add(
            Path(log_config['log_dir']) / log_config['log_file'],
            format=log_config['format'],
            level=log_config['level'],
            rotation=log_config['max_file_size'],
            retention=log_config['backup_count']
        )

        logger.info("=" * 70)
        logger.info("TRADING SYSTEM STARTED")
        logger.info("=" * 70)

    def _init_components(self):
        """Inizializza tutti i componenti del sistema"""
        logger.info("Inizializzazione componenti...")

        # Extractor
        self.extractor = BinanceExtractor(
            api_key=self.config['binance']['api_key'],
            api_secret=self.config['binance']['api_secret'],
            output_dir=self.config['extraction']['raw_dir']
        )

        # ETL
        self.etl = IndicatorCalculator(
            input_dir=self.config['extraction']['raw_dir'] + 'klines',
            output_dir=self.config['extraction']['processed_dir'] + 'indicators'
        )

        # Strategy
        self.strategy = ACTIVE_STRATEGY
        logger.info(f"Strategia attiva: {self.strategy.name}")

        # LLM Advisor (se abilitato)
        if self.config['llm']['enabled']:
            self.llm = LLMAdvisor(
                provider=self.config['llm']['provider'],
                api_key=self.config['llm']['api_key'],
                model=self.config['llm']['model'],
                temperature=self.config['llm']['temperature']
            )
        else:
            self.llm = None
            logger.info("LLM Advisor disabilitato")

        # Audio Notifier
        if self.config['audio']['enabled']:
            self.audio = AudioNotifier(
                sounds_dir=self.config['audio']['sounds_dir'],
                volume=self.config['audio']['volume']
            )
        else:
            self.audio = None
            logger.info("Audio Notifier disabilitato")

        # Telegram Notifier
        if self.config['telegram']['enabled']:
            self.telegram = TelegramNotifier(
                bot_token=self.config['telegram']['bot_token'],
                chat_id=self.config['telegram']['chat_id']
            )
        else:
            self.telegram = None
            logger.info("Telegram Notifier disabilitato")

        logger.info("Componenti inizializzati con successo")

    async def run_live(self):
        """Esegue il sistema in modalità live trading"""
        logger.info("MODALITÀ: LIVE TRADING")

        # Connetti a Binance
        await self.extractor.connect()

        # Invia notifica avvio
        if self.telegram:
            await self.telegram.send_message("🤖 *Trading System AVVIATO*\n\nModalità: Live Trading")

        # Avvia extractors in background per i simboli configurati
        # TODO: Carica simboli da config/symbols.yaml
        symbols = ['BTCUSDT', 'ETHUSDT']
        intervals = ['1m', '5m']

        logger.info(f"Avvio stream per {len(symbols)} simboli: {symbols}")

        # Avvia streams in background
        stream_tasks = []
        for symbol in symbols:
            for interval in intervals:
                task = asyncio.create_task(
                    self.extractor.start_kline_stream(symbol, interval)
                )
                stream_tasks.append(task)

        # Main loop
        self.is_running = True

        try:
            while self.is_running:
                # TODO: Implementa logica trading
                # 1. Carica ultimi dati
                # 2. Calcola indicatori
                # 3. Genera segnali
                # 4. Chiedi consenso LLM (se abilitato)
                # 5. Esegui trade
                # 6. Gestisci posizioni
                # 7. Controlla FINAL TP/SL

                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Interruzione utente (Ctrl+C)")

        finally:
            await self.shutdown()

    async def shutdown(self):
        """Shutdown pulito del sistema"""
        logger.info("Shutdown sistema...")

        self.is_running = False

        # Chiudi posizioni aperte
        if self.positions:
            logger.warning(f"Chiusura {len(self.positions)} posizioni aperte...")
            # TODO: Chiudi tutte le posizioni

        # Disconnetti da Binance
        await self.extractor.disconnect()

        # Invia statistiche finali
        if self.telegram:
            await self.telegram.send_message("⏸️ *Trading System FERMATO*")

        logger.info("Sistema terminato")

    def unlock_system(self):
        """Sblocca il sistema dopo FINAL TP/SL"""
        if not self.is_blocked:
            logger.info("Sistema già sbloccato")
            return

        logger.info("SBLOCCO SISTEMA dopo FINAL TP/SL")

        self.is_blocked = False
        self.daily_pnl = 0
        self.trades_today = 0

        if self.telegram:
            asyncio.run(self.telegram.send_message("🔓 *Sistema SBLOCCATO*\n\nIl trading può riprendere."))

        logger.info("Sistema sbloccato con successo")


# ============================================================================
# MAIN
# ============================================================================

def parse_args():
    """Parsa argomenti da command line"""
    parser = argparse.ArgumentParser(description='Crypto Trading System')

    parser.add_argument(
        '--mode',
        choices=['live', 'backtest'],
        default='live',
        help='Modalità di esecuzione (default: live)'
    )

    parser.add_argument(
        '--unlock',
        action='store_true',
        help='Sblocca il sistema dopo FINAL TP/SL'
    )

    parser.add_argument(
        '--symbols',
        type=str,
        help='Simboli da tradare (comma-separated). Es: BTCUSDT,ETHUSDT'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path a file di configurazione custom'
    )

    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()

    # Inizializza sistema
    system = TradingSystem(CONFIG)

    # Modalità sblocco
    if args.unlock:
        system.unlock_system()
        return

    # Modalità backtest
    if args.mode == 'backtest':
        logger.info("Modalità backtest - usa backtest.py invece!")
        logger.info("python backtest.py --symbol BTCUSDT --start 2024-01-01")
        return

    # Modalità live
    await system.run_live()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Terminato dall'utente")
    except Exception as e:
        logger.exception(f"Errore fatale: {e}")
        sys.exit(1)
