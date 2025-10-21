"""
Binance Client - Interfaccia con Binance Exchange

Gestisce connessione a Binance e esecuzione ordini.
Wrapper attorno alla libreria python-binance.
"""

import asyncio
from binance import AsyncClient, Client
from binance.exceptions import BinanceAPIException
from loguru import logger


class BinanceClient:
    """
    Client per interagire con Binance Exchange
    """

    def __init__(self, api_key, api_secret, testnet=False):
        """
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: True per usare testnet
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.client = None
        self.async_client = None

        logger.info(f"BinanceClient inizializzato | Testnet: {testnet}")

    # ========================================================================
    # CONNECTION
    # ========================================================================

    async def connect(self):
        """Connette al client Binance (async)"""
        try:
            self.async_client = await AsyncClient.create(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=self.testnet
            )
            logger.info("✅ Connesso a Binance API (async)")

            # Test connessione
            status = await self.async_client.get_system_status()
            logger.info(f"Binance system status: {status}")

        except BinanceAPIException as e:
            logger.error(f"❌ Errore connessione Binance API: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Errore inaspettato: {e}")
            raise

    def connect_sync(self):
        """Connette al client Binance (sync)"""
        try:
            self.client = Client(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=self.testnet
            )
            logger.info("✅ Connesso a Binance API (sync)")

            # Test connessione
            status = self.client.get_system_status()
            logger.info(f"Binance system status: {status}")

        except BinanceAPIException as e:
            logger.error(f"❌ Errore connessione Binance API: {e}")
            raise

    async def disconnect(self):
        """Disconnette dal client Binance"""
        if self.async_client:
            await self.async_client.close_connection()
            logger.info("Disconnesso da Binance API (async)")

    # ========================================================================
    # ACCOUNT INFO
    # ========================================================================

    async def get_account_info(self):
        """
        Ottiene informazioni account

        Returns:
            dict: Account info
        """
        try:
            account = await self.async_client.get_account()
            return account
        except BinanceAPIException as e:
            logger.error(f"Errore get_account_info: {e}")
            return None

    async def get_account_balance(self, asset='USDT'):
        """
        Ottiene balance di un asset specifico

        Args:
            asset: Asset symbol (es. 'USDT', 'BTC')

        Returns:
            dict: {'free': float, 'locked': float, 'total': float}
        """
        try:
            account = await self.get_account_info()
            if not account:
                return None

            for balance in account['balances']:
                if balance['asset'] == asset:
                    return {
                        'free': float(balance['free']),
                        'locked': float(balance['locked']),
                        'total': float(balance['free']) + float(balance['locked'])
                    }

            logger.warning(f"Asset {asset} non trovato in account")
            return None

        except Exception as e:
            logger.error(f"Errore get_account_balance: {e}")
            return None

    # ========================================================================
    # MARKET DATA
    # ========================================================================

    async def get_symbol_price(self, symbol):
        """
        Ottiene prezzo corrente di un simbolo

        Args:
            symbol: Es. 'BTCUSDT'

        Returns:
            float: Prezzo corrente
        """
        try:
            ticker = await self.async_client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            logger.error(f"Errore get_symbol_price per {symbol}: {e}")
            return None

    async def get_symbol_info(self, symbol):
        """
        Ottiene informazioni su un simbolo (filters, limits, etc.)

        Args:
            symbol: Es. 'BTCUSDT'

        Returns:
            dict: Symbol info
        """
        try:
            exchange_info = await self.async_client.get_exchange_info()

            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    return s

            logger.warning(f"Simbolo {symbol} non trovato")
            return None

        except Exception as e:
            logger.error(f"Errore get_symbol_info: {e}")
            return None

    async def get_orderbook(self, symbol, limit=20):
        """
        Ottiene order book

        Args:
            symbol: Es. 'BTCUSDT'
            limit: Depth (5, 10, 20, 50, 100, etc.)

        Returns:
            dict: Order book {'bids': [...], 'asks': [...]}
        """
        try:
            orderbook = await self.async_client.get_order_book(
                symbol=symbol,
                limit=limit
            )
            return orderbook
        except Exception as e:
            logger.error(f"Errore get_orderbook: {e}")
            return None

    # ========================================================================
    # ORDERS - MARKET
    # ========================================================================

    async def create_market_buy_order(self, symbol, quantity):
        """
        Crea ordine MARKET BUY

        Args:
            symbol: Es. 'BTCUSDT'
            quantity: Quantità da acquistare

        Returns:
            dict: Order info
        """
        try:
            logger.info(f"📈 Creando Market BUY: {symbol} qty={quantity}")

            order = await self.async_client.create_order(
                symbol=symbol,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )

            logger.info(f"✅ Market BUY eseguito: {order['orderId']} | Status: {order['status']}")
            return order

        except BinanceAPIException as e:
            logger.error(f"❌ Errore market buy: {e}")
            return None

    async def create_market_sell_order(self, symbol, quantity):
        """
        Crea ordine MARKET SELL

        Args:
            symbol: Es. 'BTCUSDT'
            quantity: Quantità da vendere

        Returns:
            dict: Order info
        """
        try:
            logger.info(f"📉 Creando Market SELL: {symbol} qty={quantity}")

            order = await self.async_client.create_order(
                symbol=symbol,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )

            logger.info(f"✅ Market SELL eseguito: {order['orderId']} | Status: {order['status']}")
            return order

        except BinanceAPIException as e:
            logger.error(f"❌ Errore market sell: {e}")
            return None

    # ========================================================================
    # ORDERS - LIMIT
    # ========================================================================

    async def create_limit_buy_order(self, symbol, quantity, price):
        """
        Crea ordine LIMIT BUY

        Args:
            symbol: Es. 'BTCUSDT'
            quantity: Quantità
            price: Prezzo limite

        Returns:
            dict: Order info
        """
        try:
            logger.info(f"Creando Limit BUY: {symbol} qty={quantity} @ {price}")

            order = await self.async_client.create_order(
                symbol=symbol,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_LIMIT,
                timeInForce=Client.TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=price
            )

            logger.info(f"✅ Limit BUY creato: {order['orderId']}")
            return order

        except BinanceAPIException as e:
            logger.error(f"❌ Errore limit buy: {e}")
            return None

    async def create_limit_sell_order(self, symbol, quantity, price):
        """
        Crea ordine LIMIT SELL

        Args:
            symbol: Es. 'BTCUSDT'
            quantity: Quantità
            price: Prezzo limite

        Returns:
            dict: Order info
        """
        try:
            logger.info(f"Creando Limit SELL: {symbol} qty={quantity} @ {price}")

            order = await self.async_client.create_order(
                symbol=symbol,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_LIMIT,
                timeInForce=Client.TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=price
            )

            logger.info(f"✅ Limit SELL creato: {order['orderId']}")
            return order

        except BinanceAPIException as e:
            logger.error(f"❌ Errore limit sell: {e}")
            return None

    # ========================================================================
    # ORDERS - STOP LOSS / TAKE PROFIT
    # ========================================================================

    async def create_stop_loss_order(self, symbol, quantity, stop_price):
        """
        Crea ordine STOP_LOSS

        Args:
            symbol: Es. 'BTCUSDT'
            quantity: Quantità
            stop_price: Prezzo di trigger

        Returns:
            dict: Order info
        """
        try:
            logger.info(f"Creando Stop Loss: {symbol} qty={quantity} stop={stop_price}")

            order = await self.async_client.create_order(
                symbol=symbol,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_STOP_LOSS_LIMIT,
                timeInForce=Client.TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=stop_price,
                stopPrice=stop_price
            )

            logger.info(f"✅ Stop Loss creato: {order['orderId']}")
            return order

        except BinanceAPIException as e:
            logger.error(f"❌ Errore stop loss: {e}")
            return None

    async def create_take_profit_order(self, symbol, quantity, limit_price):
        """
        Crea ordine TAKE_PROFIT

        Args:
            symbol: Es. 'BTCUSDT'
            quantity: Quantità
            limit_price: Prezzo di take profit

        Returns:
            dict: Order info
        """
        try:
            logger.info(f"Creando Take Profit: {symbol} qty={quantity} limit={limit_price}")

            order = await self.async_client.create_order(
                symbol=symbol,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_TAKE_PROFIT_LIMIT,
                timeInForce=Client.TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=limit_price,
                stopPrice=limit_price
            )

            logger.info(f"✅ Take Profit creato: {order['orderId']}")
            return order

        except BinanceAPIException as e:
            logger.error(f"❌ Errore take profit: {e}")
            return None

    # ========================================================================
    # ORDER MANAGEMENT
    # ========================================================================

    async def cancel_order(self, symbol, order_id):
        """
        Cancella un ordine

        Args:
            symbol: Es. 'BTCUSDT'
            order_id: ID ordine

        Returns:
            dict: Cancel result
        """
        try:
            result = await self.async_client.cancel_order(
                symbol=symbol,
                orderId=order_id
            )
            logger.info(f"✅ Ordine {order_id} cancellato")
            return result

        except BinanceAPIException as e:
            logger.error(f"❌ Errore cancel order: {e}")
            return None

    async def get_order(self, symbol, order_id):
        """
        Ottiene info su un ordine

        Args:
            symbol: Es. 'BTCUSDT'
            order_id: ID ordine

        Returns:
            dict: Order info
        """
        try:
            order = await self.async_client.get_order(
                symbol=symbol,
                orderId=order_id
            )
            return order

        except BinanceAPIException as e:
            logger.error(f"Errore get order: {e}")
            return None

    async def get_open_orders(self, symbol=None):
        """
        Ottiene tutti gli ordini aperti

        Args:
            symbol: Opzionale - filtra per simbolo

        Returns:
            list: Lista ordini aperti
        """
        try:
            if symbol:
                orders = await self.async_client.get_open_orders(symbol=symbol)
            else:
                orders = await self.async_client.get_open_orders()

            return orders

        except BinanceAPIException as e:
            logger.error(f"Errore get open orders: {e}")
            return []

    async def cancel_all_orders(self, symbol):
        """
        Cancella tutti gli ordini aperti per un simbolo

        Args:
            symbol: Es. 'BTCUSDT'

        Returns:
            list: Risultati cancellazione
        """
        try:
            result = await self.async_client.cancel_all_orders(symbol=symbol)
            logger.info(f"✅ Tutti gli ordini cancellati per {symbol}")
            return result

        except BinanceAPIException as e:
            logger.error(f"❌ Errore cancel all orders: {e}")
            return None

    # ========================================================================
    # UTILITY
    # ========================================================================

    def format_quantity(self, symbol_info, quantity):
        """
        Formatta quantity secondo i filters del simbolo

        Args:
            symbol_info: Info simbolo da get_symbol_info()
            quantity: Quantità raw

        Returns:
            float: Quantità formattata
        """
        # Trova LOT_SIZE filter
        for f in symbol_info['filters']:
            if f['filterType'] == 'LOT_SIZE':
                step_size = float(f['stepSize'])
                # Arrotonda a step_size più vicino
                precision = len(str(step_size).split('.')[-1].rstrip('0'))
                formatted = round(quantity - (quantity % step_size), precision)
                return formatted

        return quantity

    def format_price(self, symbol_info, price):
        """
        Formatta prezzo secondo i filters del simbolo

        Args:
            symbol_info: Info simbolo
            price: Prezzo raw

        Returns:
            float: Prezzo formattato
        """
        # Trova PRICE_FILTER
        for f in symbol_info['filters']:
            if f['filterType'] == 'PRICE_FILTER':
                tick_size = float(f['tickSize'])
                precision = len(str(tick_size).split('.')[-1].rstrip('0'))
                formatted = round(price - (price % tick_size), precision)
                return formatted

        return price
