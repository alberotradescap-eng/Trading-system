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

# Import engine
from engine.signal_generator import SignalGenerator
from engine.position_manager import PositionManager
from engine.risk_manager import RiskManager
from engine.portfolio_manager import PortfolioManager

# Import broker
from broker.binance_client import BinanceClient
from broker.order_executor import OrderExecutor
from broker.account_monitor import AccountMonitor

import pandas as pd


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

        # Binance Client
        self.binance_client = BinanceClient(
            api_key=self.config['binance']['api_key'],
            api_secret=self.config['binance']['api_secret'],
            testnet=self.config['binance']['testnet']
        )

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

        # Engine components
        initial_capital = self.config['trading'].get('initial_capital', 10000)

        self.signal_gen = SignalGenerator(self.strategy)
        self.position_mgr = PositionManager(self.config)
        self.risk_mgr = RiskManager(self.config, initial_capital)
        self.portfolio_mgr = PortfolioManager(self.config, initial_capital)

        # Broker components
        self.order_executor = None  # Inizializzato dopo connessione
        self.account_monitor = None  # Inizializzato dopo connessione

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

        # Data buffer per ultimi dati
        self.data_buffer = {}  # {symbol: DataFrame}

        logger.info("Componenti inizializzati con successo")

    async def run_live(self):
        """Esegue il sistema in modalità live trading"""
        logger.info("MODALITÀ: LIVE TRADING")

        # Connetti a Binance
        await self.binance_client.connect()
        await self.extractor.connect()

        # Inizializza broker components
        self.order_executor = OrderExecutor(self.binance_client, self.config)
        self.account_monitor = AccountMonitor(self.binance_client, self.config)

        # Ottieni balance iniziale
        balance = await self.account_monitor.update_balance('USDT')
        if balance:
            initial_capital = balance['total']
            self.risk_mgr.update_balance(initial_capital)
            self.portfolio_mgr.current_capital = initial_capital
            logger.info(f"Balance iniziale: ${initial_capital:.2f} USDT")

        # Invia notifica avvio
        if self.telegram:
            await self.telegram.send_message(
                f"🤖 *Trading System AVVIATO*\n\n"
                f"Modalità: Live Trading\n"
                f"Balance: ${initial_capital:.2f} USDT"
            )

        # Carica simboli (per ora hardcoded, TODO: da config/symbols.yaml)
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
        loop_counter = 0

        try:
            while self.is_running:
                loop_counter += 1

                # 1. Controlla FINAL TP/SL
                if self.position_mgr.is_blocked:
                    logger.warning("Sistema BLOCCATO per FINAL TP/SL. Usa --unlock per sbloccare.")
                    await asyncio.sleep(60)
                    continue

                # 2. Aggiorna account info ogni 30 secondi
                if loop_counter % 30 == 0:
                    await self.account_monitor.update_account_info()
                    balance = await self.account_monitor.update_balance('USDT')
                    if balance:
                        self.risk_mgr.update_balance(balance['total'])
                        self.portfolio_mgr.update_portfolio(
                            self.position_mgr.get_open_positions(),
                            await self.binance_client.get_account_info()
                        )

                # 3. Carica ultimi dati per ogni simbolo
                for symbol in symbols:
                    try:
                        # Leggi ultimi dati da file (salvati dall'extractor)
                        data = await self._load_latest_data(symbol, '1m')

                        if data is None or data.empty:
                            continue

                        # 4. Calcola indicatori
                        indicators = self.etl.calculate_indicators_realtime(data, window_size=200)

                        # 5. Aggiorna posizioni esistenti
                        current_prices = {symbol: indicators['close']}
                        self.position_mgr.update_positions(current_prices)

                        # 6. Gestisci posizioni aperte (check exit)
                        await self._manage_open_positions(indicators)

                        # 7. Genera segnali (solo se non abbiamo già posizione)
                        if symbol not in self.position_mgr.positions:
                            signal = self.signal_gen.generate_signal(
                                indicators,
                                symbol,
                                self.position_mgr.get_open_positions()
                            )

                            if signal:
                                # 8. Chiedi consenso LLM (se abilitato)
                                if self.llm:
                                    approved, reason = await self.llm.ask_consent(signal)
                                    if not approved:
                                        logger.info(f"Trade rifiutato da LLM: {reason}")
                                        continue

                                # 9. Valida con risk manager
                                account_balance = self.portfolio_mgr.get_available_capital()
                                is_valid, reason, sizing = self.risk_mgr.validate_trade(
                                    signal,
                                    account_balance,
                                    self.position_mgr.get_open_positions()
                                )

                                if not is_valid:
                                    logger.info(f"Trade non valido: {reason}")
                                    continue

                                # 10. Esegui trade
                                await self._execute_trade(signal, sizing)

                        # 11. Controlla FINAL TP/SL
                        limit_reached, limit_reason = self.position_mgr.check_final_limits()
                        if limit_reached:
                            logger.warning(f"🛑 {limit_reason} raggiunto!")

                            # Chiudi tutte le posizioni
                            if self.position_mgr.get_open_positions():
                                await self._close_all_positions('final_limit_reached')

                            # Notifica
                            if self.telegram:
                                await self.telegram.send_message(
                                    f"🛑 *{limit_reason}*\n\n"
                                    f"PnL giornaliero: ${self.position_mgr.daily_pnl:.2f}\n"
                                    f"Sistema bloccato."
                                )
                            break

                    except Exception as e:
                        logger.error(f"Errore nel loop per {symbol}: {e}")

                # Sleep
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
        self.position_mgr.unlock_system()

        if self.telegram:
            asyncio.run(self.telegram.send_message("🔓 *Sistema SBLOCCATO*\n\nIl trading può riprendere."))

        logger.info("Sistema sbloccato con successo")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _load_latest_data(self, symbol, interval='1m', window_size=200):
        """
        Carica ultimi dati da file salvati dall'extractor

        Args:
            symbol: Simbolo
            interval: Timeframe
            window_size: Numero candles da caricare

        Returns:
            DataFrame: Ultimi dati
        """
        try:
            from pathlib import Path
            from datetime import datetime

            # Trova file più recente per questo simbolo
            klines_dir = Path(self.config['extraction']['raw_dir']) / 'klines'
            date_str = datetime.now().strftime('%Y%m%d')
            filename = klines_dir / f"{symbol}_{interval}_{date_str}.csv"

            if not filename.exists():
                logger.debug(f"File non trovato: {filename}")
                return None

            # Carica ultimi dati
            df = pd.read_csv(filename)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.tail(window_size)

            return df

        except Exception as e:
            logger.error(f"Errore caricamento dati per {symbol}: {e}")
            return None

    async def _manage_open_positions(self, current_data):
        """
        Gestisce posizioni aperte (check TP/SL e exit signals)

        Args:
            current_data: Dati correnti con indicatori
        """
        for position in list(self.position_mgr.positions.values()):
            symbol = position['symbol']

            # Check TP/SL
            should_close_tpsl, reason_tpsl = self.position_mgr.check_tp_sl(position)
            if should_close_tpsl:
                await self._close_position(position, reason_tpsl)
                continue

            # Check exit signal dalla strategia
            should_close_signal, reason_signal = self.signal_gen.check_exit_signal(
                position,
                current_data
            )
            if should_close_signal:
                await self._close_position(position, reason_signal)

    async def _execute_trade(self, signal, sizing):
        """
        Esegue un trade

        Args:
            signal: Segnale da eseguire
            sizing: Info sizing da risk manager
        """
        logger.info(f"💰 Eseguendo trade: {signal['type']} {signal['symbol']} qty={sizing['quantity']:.6f}")

        # Esegui ordine
        order_info = await self.order_executor.execute_signal(signal, sizing['quantity'])

        if order_info:
            # Apri posizione
            position = self.position_mgr.open_position(signal, order_info)

            # Notifica audio
            if self.audio and signal['type'] == 'BUY':
                self.audio.play('buy')
            elif self.audio and signal['type'] == 'SELL':
                self.audio.play('sell')

            # Notifica Telegram
            if self.telegram:
                await self.telegram.send_trade_notification({
                    'symbol': signal['symbol'],
                    'side': signal['type'],
                    'price': order_info['price'],
                    'quantity': order_info['executed_qty'],
                    'timestamp': datetime.now()
                })

            logger.info(f"✅ Trade eseguito con successo: {signal['symbol']}")
        else:
            logger.error(f"❌ Trade fallito per {signal['symbol']}")

    async def _close_position(self, position, reason):
        """
        Chiude una posizione

        Args:
            position: Posizione da chiudere
            reason: Motivo chiusura
        """
        logger.info(f"🏁 Chiudendo posizione: {position['symbol']} reason={reason}")

        # Esegui chiusura su broker
        order_info = await self.order_executor.close_position(position, reason)

        if order_info:
            # Chiudi nel position manager
            current_price = order_info['price']
            commission = order_info.get('commission', 0)

            closed = self.position_mgr.close_position(
                position['symbol'],
                current_price,
                reason,
                commission
            )

            # Notifica Telegram
            if self.telegram and closed:
                await self.telegram.send_trade_notification({
                    'symbol': position['symbol'],
                    'side': 'CLOSE',
                    'price': current_price,
                    'quantity': position['quantity'],
                    'pnl': closed['realized_pnl'],
                    'timestamp': datetime.now()
                })

            logger.info(f"✅ Posizione chiusa: {position['symbol']} | PnL: ${closed['realized_pnl']:.2f}")
        else:
            logger.error(f"❌ Errore chiusura posizione {position['symbol']}")

    async def _close_all_positions(self, reason):
        """
        Chiude tutte le posizioni aperte

        Args:
            reason: Motivo chiusura
        """
        positions = self.position_mgr.get_open_positions()

        logger.info(f"Chiudendo {len(positions)} posizioni. Reason: {reason}")

        for position in positions:
            await self._close_position(position, reason)


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
