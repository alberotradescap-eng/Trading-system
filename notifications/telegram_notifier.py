"""
Telegram Notifier

Invia notifiche, statistiche e grafici su Telegram
"""

import asyncio
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from loguru import logger
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


class TelegramNotifier:
    """
    Notifiche Telegram per eventi di trading
    """

    def __init__(self, bot_token, chat_id):
        """
        Args:
            bot_token: Token del bot Telegram
            chat_id: ID della chat dove inviare messaggi
        """
        self.bot_token = bot_token
        self.chat_id = chat_id

        if not bot_token or not chat_id:
            logger.warning("Telegram bot token o chat_id mancanti. Notifiche disabilitate.")
            self.enabled = False
            return

        self.bot = Bot(token=bot_token)
        self.enabled = True

        logger.info(f"Telegram Notifier inizializzato. Chat ID: {chat_id}")

    async def send_message(self, text, parse_mode='Markdown'):
        """
        Invia un messaggio testuale

        Args:
            text: Testo del messaggio
            parse_mode: 'Markdown' o 'HTML'
        """
        if not self.enabled:
            return

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode
            )
            logger.debug("Messaggio Telegram inviato")
        except TelegramError as e:
            logger.error(f"Errore invio messaggio Telegram: {e}")

    async def send_trade_notification(self, order_info):
        """
        Notifica esecuzione trade

        Args:
            order_info: Dictionary con info ordine
                - symbol
                - side (BUY/SELL)
                - price
                - quantity
                - timestamp
        """
        emoji = "🟢" if order_info['side'] == 'BUY' else "🔴"

        message = f"""
{emoji} *TRADE EXECUTED*

*Symbol:* `{order_info['symbol']}`
*Type:* {order_info['side']}
*Price:* ${order_info['price']:.2f}
*Quantity:* {order_info['quantity']:.6f}
*Value:* ${order_info['price'] * order_info['quantity']:.2f}
*Time:* {order_info['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
"""

        if 'reason' in order_info:
            message += f"\n*Reason:* {order_info['reason']}"

        await self.send_message(message)

    async def send_position_closed(self, position_info):
        """
        Notifica chiusura posizione

        Args:
            position_info: Dictionary con info posizione
                - symbol
                - entry_price
                - exit_price
                - pnl
                - pnl_pct
                - duration
        """
        emoji = "💰" if position_info['pnl'] > 0 else "📉"

        message = f"""
{emoji} *POSITION CLOSED*

*Symbol:* `{position_info['symbol']}`
*Entry:* ${position_info['entry_price']:.2f}
*Exit:* ${position_info['exit_price']:.2f}
*PnL:* ${position_info['pnl']:.2f} ({position_info['pnl_pct']:.2f}%)
*Duration:* {position_info.get('duration', 'N/A')}
*Reason:* {position_info.get('reason', 'N/A')}
"""

        await self.send_message(message)

    async def send_daily_stats(self, stats):
        """
        Invia statistiche giornaliere

        Args:
            stats: Dictionary con statistiche
                - date
                - total_trades
                - win_rate
                - pnl
                - best_trade
                - worst_trade
                - etc.
        """
        emoji = "📊"

        message = f"""
{emoji} *DAILY STATISTICS* - {stats.get('date', datetime.now().strftime('%Y-%m-%d'))}

*Trades:* {stats.get('total_trades', 0)}
*Winners:* {stats.get('winning_trades', 0)} | *Losers:* {stats.get('losing_trades', 0)}
*Win Rate:* {stats.get('win_rate', 0):.1f}%

*Total PnL:* ${stats.get('pnl', 0):.2f}
*Best Trade:* ${stats.get('best_trade', 0):.2f}
*Worst Trade:* ${stats.get('worst_trade', 0):.2f}

*Avg Win:* ${stats.get('avg_win', 0):.2f}
*Avg Loss:* ${stats.get('avg_loss', 0):.2f}
*Profit Factor:* {stats.get('profit_factor', 0):.2f}
"""

        await self.send_message(message)

    async def send_final_limit_alert(self, limit_type, value):
        """
        Alert quando raggiunto TP/SL FINAL

        Args:
            limit_type: 'TAKE_PROFIT' o 'STOP_LOSS'
            value: Valore raggiunto
        """
        if limit_type == 'TAKE_PROFIT':
            emoji = "🎯"
            title = "TAKE PROFIT FINAL REACHED"
        else:
            emoji = "⛔"
            title = "STOP LOSS FINAL REACHED"

        message = f"""
{emoji} *{title}*

Il sistema ha raggiunto il limite giornaliero di {limit_type}!

*Value:* ${value:.2f}
*Time:* {datetime.now().strftime('%H:%M:%S')}

⚠️ *Trading bloccato fino a sblocco manuale*
"""

        await self.send_message(message)

    async def send_error_alert(self, error_msg):
        """
        Alert per errori

        Args:
            error_msg: Messaggio di errore
        """
        message = f"""
🚨 *ERROR ALERT*

{error_msg}

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        await self.send_message(message)

    async def send_photo(self, photo_path, caption=None):
        """
        Invia un'immagine (es. grafico)

        Args:
            photo_path: Path al file immagine
            caption: Caption opzionale
        """
        if not self.enabled:
            return

        try:
            with open(photo_path, 'rb') as photo:
                await self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=photo,
                    caption=caption
                )
            logger.debug(f"Foto inviata: {photo_path}")
        except Exception as e:
            logger.error(f"Errore invio foto Telegram: {e}")

    async def send_equity_curve(self, equity_data, filename='equity_curve.png'):
        """
        Genera e invia grafico equity curve

        Args:
            equity_data: DataFrame o lista con valori portfolio nel tempo
            filename: Nome file temporaneo per il grafico
        """
        # Genera grafico
        plt.figure(figsize=(12, 6))

        if isinstance(equity_data, pd.DataFrame):
            plt.plot(equity_data.index, equity_data['equity'])
            plt.xlabel('Time')
        else:
            plt.plot(equity_data)
            plt.xlabel('Trades')

        plt.ylabel('Portfolio Value ($)')
        plt.title('Equity Curve')
        plt.grid(True, alpha=0.3)

        # Salva temporaneamente
        temp_path = Path('temp') / filename
        temp_path.parent.mkdir(exist_ok=True)
        plt.savefig(temp_path, dpi=100, bbox_inches='tight')
        plt.close()

        # Invia
        await self.send_photo(temp_path, caption="📈 Equity Curve")

        # Rimuovi file temporaneo
        temp_path.unlink()

    # ========================================================================
    # SINCRONOUS WRAPPERS (per compatibilità)
    # ========================================================================

    def send_message_sync(self, text):
        """Wrapper sincrono per send_message"""
        asyncio.run(self.send_message(text))

    def send_trade_notification_sync(self, order_info):
        """Wrapper sincrono per send_trade_notification"""
        asyncio.run(self.send_trade_notification(order_info))


# ============================================================================
# ESEMPIO DI UTILIZZO
# ============================================================================

async def main():
    from config.settings import TELEGRAM_CONFIG

    notifier = TelegramNotifier(
        bot_token=TELEGRAM_CONFIG['bot_token'],
        chat_id=TELEGRAM_CONFIG['chat_id']
    )

    # Test messaggio
    await notifier.send_message("🤖 Trading System avviato!")

    # Test trade notification
    test_order = {
        'symbol': 'BTCUSDT',
        'side': 'BUY',
        'price': 43250.50,
        'quantity': 0.01,
        'timestamp': datetime.now(),
        'reason': 'RSI oversold + MACD bullish cross'
    }
    await notifier.send_trade_notification(test_order)

    # Test daily stats
    test_stats = {
        'date': '2024-01-15',
        'total_trades': 10,
        'winning_trades': 7,
        'losing_trades': 3,
        'win_rate': 70,
        'pnl': 325.50,
        'best_trade': 85.20,
        'worst_trade': -45.30,
        'avg_win': 60.25,
        'avg_loss': -35.10,
        'profit_factor': 1.85
    }
    await notifier.send_daily_stats(test_stats)


if __name__ == '__main__':
    asyncio.run(main())
