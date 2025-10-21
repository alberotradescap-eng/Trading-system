"""
Order Executor - Esegue ordini su Binance

Layer di astrazione sopra BinanceClient che gestisce:
- Validazione ordini
- Formatting (quantity, price)
- Retry logic
- Tracking ordini eseguiti
"""

import asyncio
from datetime import datetime
from loguru import logger
from .binance_client import BinanceClient


class OrderExecutor:
    """
    Esegue ordini su Binance con validazione e retry
    """

    def __init__(self, binance_client: BinanceClient, config):
        """
        Args:
            binance_client: Istanza di BinanceClient
            config: Dictionary con configurazione
        """
        self.client = binance_client
        self.config = config
        self.executed_orders = []
        self.failed_orders = []

        logger.info("OrderExecutor inizializzato")

    # ========================================================================
    # EXECUTE SIGNAL
    # ========================================================================

    async def execute_signal(self, signal, quantity):
        """
        Esegue un segnale di trading

        Args:
            signal: Dictionary con segnale
            quantity: Quantità da tradare

        Returns:
            dict: Order info se successo, None se fallito
        """
        symbol = signal['symbol']
        signal_type = signal['type']  # 'BUY' o 'SELL'

        logger.info(f"🎯 Eseguendo segnale {signal_type} per {symbol} qty={quantity}")

        # Ottieni symbol info per formatting
        symbol_info = await self.client.get_symbol_info(symbol)
        if not symbol_info:
            logger.error(f"Impossibile ottenere symbol info per {symbol}")
            return None

        # Formatta quantity
        formatted_qty = self.client.format_quantity(symbol_info, quantity)

        logger.info(f"Quantity formattata: {quantity} -> {formatted_qty}")

        # Esegui ordine market
        if signal_type == 'BUY':
            order = await self.client.create_market_buy_order(symbol, formatted_qty)
        elif signal_type == 'SELL':
            order = await self.client.create_market_sell_order(symbol, formatted_qty)
        else:
            logger.error(f"Tipo segnale sconosciuto: {signal_type}")
            return None

        if order:
            # Arricchisci order info
            order_info = self._process_order_response(order, signal)
            self.executed_orders.append(order_info)
            return order_info
        else:
            self.failed_orders.append({
                'signal': signal,
                'quantity': formatted_qty,
                'timestamp': datetime.now(),
                'reason': 'order_execution_failed'
            })
            return None

    # ========================================================================
    # CLOSE POSITION
    # ========================================================================

    async def close_position(self, position, reason='manual'):
        """
        Chiude una posizione aperta

        Args:
            position: Dictionary con info posizione
            reason: Motivo chiusura

        Returns:
            dict: Order info se successo, None se fallito
        """
        symbol = position['symbol']
        quantity = position['quantity']
        position_type = position['type']

        logger.info(f"🏁 Chiudendo posizione {position_type} per {symbol} qty={quantity} | Reason: {reason}")

        # Ottieni symbol info
        symbol_info = await self.client.get_symbol_info(symbol)
        if not symbol_info:
            logger.error(f"Impossibile ottenere symbol info per {symbol}")
            return None

        # Formatta quantity
        formatted_qty = self.client.format_quantity(symbol_info, quantity)

        # Per chiudere LONG → SELL
        # Per chiudere SHORT → BUY
        if position_type == 'LONG':
            order = await self.client.create_market_sell_order(symbol, formatted_qty)
        elif position_type == 'SHORT':
            order = await self.client.create_market_buy_order(symbol, formatted_qty)
        else:
            logger.error(f"Tipo posizione sconosciuto: {position_type}")
            return None

        if order:
            # Arricchisci order info
            order_info = self._process_order_response(order, None)
            order_info['close_reason'] = reason
            order_info['position_closed'] = position
            self.executed_orders.append(order_info)
            return order_info
        else:
            self.failed_orders.append({
                'position': position,
                'quantity': formatted_qty,
                'timestamp': datetime.now(),
                'reason': f'close_failed_{reason}'
            })
            return None

    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================

    async def close_all_positions(self, positions, reason='close_all'):
        """
        Chiude tutte le posizioni in batch

        Args:
            positions: Lista di posizioni da chiudere
            reason: Motivo chiusura

        Returns:
            list: Lista order info
        """
        logger.info(f"Chiudendo {len(positions)} posizioni | Reason: {reason}")

        tasks = []
        for position in positions:
            task = self.close_position(position, reason)
            tasks.append(task)

        # Esegui in parallelo
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filtra successi
        successful = [r for r in results if r and not isinstance(r, Exception)]

        logger.info(f"Chiuse {len(successful)}/{len(positions)} posizioni")
        return successful

    # ========================================================================
    # ADVANCED ORDERS (con TP/SL)
    # ========================================================================

    async def execute_signal_with_tp_sl(self, signal, quantity, tp_price=None, sl_price=None):
        """
        Esegue segnale con Take Profit e Stop Loss automatici

        Args:
            signal: Dictionary segnale
            quantity: Quantità
            tp_price: Prezzo Take Profit (opzionale)
            sl_price: Prezzo Stop Loss (opzionale)

        Returns:
            dict: {
                'entry_order': dict,
                'tp_order': dict (se richiesto),
                'sl_order': dict (se richiesto)
            }
        """
        symbol = signal['symbol']

        # 1. Esegui entry order (market)
        entry_order = await self.execute_signal(signal, quantity)
        if not entry_order:
            logger.error("Entry order fallito, skip TP/SL")
            return None

        result = {'entry_order': entry_order}

        # Ottieni symbol info per formatting
        symbol_info = await self.client.get_symbol_info(symbol)
        formatted_qty = self.client.format_quantity(symbol_info, quantity)

        # 2. Piazza Take Profit (se richiesto)
        if tp_price:
            formatted_tp_price = self.client.format_price(symbol_info, tp_price)
            tp_order = await self.client.create_take_profit_order(
                symbol, formatted_qty, formatted_tp_price
            )
            if tp_order:
                result['tp_order'] = tp_order
                logger.info(f"✅ Take Profit piazzato @ {formatted_tp_price}")

        # 3. Piazza Stop Loss (se richiesto)
        if sl_price:
            formatted_sl_price = self.client.format_price(symbol_info, sl_price)
            sl_order = await self.client.create_stop_loss_order(
                symbol, formatted_qty, formatted_sl_price
            )
            if sl_order:
                result['sl_order'] = sl_order
                logger.info(f"✅ Stop Loss piazzato @ {formatted_sl_price}")

        return result

    # ========================================================================
    # ORDER TRACKING & MONITORING
    # ========================================================================

    async def check_order_status(self, symbol, order_id):
        """
        Controlla status di un ordine

        Args:
            symbol: Simbolo
            order_id: ID ordine

        Returns:
            dict: Order info
        """
        order = await self.client.get_order(symbol, order_id)
        if order:
            logger.debug(f"Order {order_id} status: {order['status']}")
        return order

    async def wait_for_order_fill(self, symbol, order_id, timeout=60, poll_interval=2):
        """
        Aspetta che un ordine venga filled

        Args:
            symbol: Simbolo
            order_id: ID ordine
            timeout: Timeout in secondi
            poll_interval: Intervallo polling in secondi

        Returns:
            dict: Order info quando filled, None se timeout
        """
        elapsed = 0

        while elapsed < timeout:
            order = await self.check_order_status(symbol, order_id)

            if not order:
                logger.warning(f"Impossibile ottenere status ordine {order_id}")
                return None

            if order['status'] == 'FILLED':
                logger.info(f"✅ Ordine {order_id} FILLED")
                return order

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        logger.warning(f"⏱️ Timeout waiting for order {order_id} to fill")
        return None

    # ========================================================================
    # UTILITY
    # ========================================================================

    def _process_order_response(self, order, signal):
        """
        Processa risposta ordine da Binance e arricchisce con info aggiuntive

        Args:
            order: Raw order response da Binance
            signal: Segnale originale (può essere None per chiusure)

        Returns:
            dict: Order info processato
        """
        # Calcola prezzo eseguito medio
        executed_qty = float(order.get('executedQty', 0))
        cummulative_quote_qty = float(order.get('cummulativeQuoteQty', 0))

        avg_price = cummulative_quote_qty / executed_qty if executed_qty > 0 else 0

        # Estrai commissioni (se presenti)
        commission = 0
        if 'fills' in order:
            for fill in order['fills']:
                commission += float(fill.get('commission', 0))

        order_info = {
            'order_id': order['orderId'],
            'symbol': order['symbol'],
            'side': order['side'],
            'type': order['type'],
            'status': order['status'],
            'price': avg_price,
            'quantity': float(order['origQty']),
            'executed_qty': executed_qty,
            'commission': commission,
            'timestamp': datetime.fromtimestamp(order['transactTime'] / 1000),
            'raw_order': order,
        }

        # Aggiungi segnale originale se presente
        if signal:
            order_info['signal'] = signal

        return order_info

    def get_executed_orders(self, symbol=None, limit=None):
        """
        Ottiene ordini eseguiti

        Args:
            symbol: Filtra per simbolo (opzionale)
            limit: Limita numero risultati (opzionale)

        Returns:
            list: Lista ordini eseguiti
        """
        orders = self.executed_orders

        if symbol:
            orders = [o for o in orders if o['symbol'] == symbol]

        if limit:
            orders = orders[-limit:]

        return orders

    def get_failed_orders(self, symbol=None, limit=None):
        """
        Ottiene ordini falliti

        Args:
            symbol: Filtra per simbolo (opzionale)
            limit: Limita numero risultati (opzionale)

        Returns:
            list: Lista ordini falliti
        """
        orders = self.failed_orders

        if symbol:
            orders = [o for o in orders if o.get('signal', {}).get('symbol') == symbol]

        if limit:
            orders = orders[-limit:]

        return orders

    def get_execution_stats(self):
        """
        Calcola statistiche di esecuzione

        Returns:
            dict: Statistiche
        """
        total_executed = len(self.executed_orders)
        total_failed = len(self.failed_orders)
        total_attempts = total_executed + total_failed

        success_rate = (total_executed / total_attempts * 100) if total_attempts > 0 else 0

        # Calcola commissioni totali
        total_commission = sum(
            order.get('commission', 0)
            for order in self.executed_orders
        )

        return {
            'total_executed': total_executed,
            'total_failed': total_failed,
            'total_attempts': total_attempts,
            'success_rate': success_rate,
            'total_commission': total_commission,
        }

    def print_execution_stats(self):
        """Stampa statistiche di esecuzione"""
        stats = self.get_execution_stats()

        output = f"""
╔═══════════════════════════════════════════════════════════╗
║              ORDER EXECUTION STATISTICS                   ║
╠═══════════════════════════════════════════════════════════╣
║ Total Executed:         {stats['total_executed']:>5}                         ║
║ Total Failed:           {stats['total_failed']:>5}                         ║
║ Total Attempts:         {stats['total_attempts']:>5}                         ║
║ Success Rate:           {stats['success_rate']:>6.2f}%                      ║
║ Total Commission:       ${stats['total_commission']:>10.2f}                  ║
╚═══════════════════════════════════════════════════════════╝
        """
        print(output)
        return output
