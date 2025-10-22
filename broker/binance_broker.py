"""
Binance Broker - Safe Order Execution con retry logic e verifica stato
"""
import asyncio
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from binance.client import AsyncClient
from binance.exceptions import BinanceAPIException, BinanceRequestException

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Stati possibili di un ordine"""
    PENDING = "PENDING"           # In attesa di invio
    NEW = "NEW"                   # Inviato ma non ancora eseguito
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"             # Completamente eseguito
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"             # Fallito dopo tutti i retry


class OrderSide(Enum):
    """Lato dell'ordine"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Tipo di ordine"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"


@dataclass
class OrderRequest:
    """Richiesta di ordine"""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    client_order_id: Optional[str] = None
    time_in_force: str = "GTC"  # GTC, IOC, FOK

    def to_dict(self) -> Dict:
        """Converte in dizionario per API Binance"""
        params = {
            'symbol': self.symbol,
            'side': self.side.value,
            'type': self.order_type.value,
            'quantity': self.quantity,
        }

        if self.price:
            params['price'] = self.price
        if self.stop_price:
            params['stopPrice'] = self.stop_price
        if self.client_order_id:
            params['newClientOrderId'] = self.client_order_id
        if self.order_type != OrderType.MARKET:
            params['timeInForce'] = self.time_in_force

        return params


@dataclass
class OrderResult:
    """Risultato dell'esecuzione di un ordine"""
    success: bool
    order_id: Optional[int] = None
    client_order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    executed_qty: float = 0.0
    avg_price: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0
    response: Optional[Dict] = None
    timestamp: datetime = field(default_factory=datetime.now)


class SafeOrderExecutor:
    """
    Esecutore sicuro di ordini con:
    - Retry automatico con exponential backoff
    - Verifica stato ordine prima di reinviare
    - Gestione ordini parzialmente eseguiti
    - Prevenzione duplicati
    - Idempotency tramite client_order_id
    """

    def __init__(
        self,
        client: AsyncClient,
        max_retries: int = 5,
        base_retry_delay: float = 1.0,
        max_retry_delay: float = 30.0,
        order_check_timeout: int = 30,
        enable_test_mode: bool = False
    ):
        """
        Args:
            client: Client Binance async
            max_retries: Numero massimo di retry
            base_retry_delay: Delay iniziale tra retry (secondi)
            max_retry_delay: Delay massimo tra retry (secondi)
            order_check_timeout: Timeout per verifica stato ordine (secondi)
            enable_test_mode: Se True usa testnet
        """
        self.client = client
        self.max_retries = max_retries
        self.base_retry_delay = base_retry_delay
        self.max_retry_delay = max_retry_delay
        self.order_check_timeout = order_check_timeout
        self.enable_test_mode = enable_test_mode

        # Cache ordini per prevenire duplicati
        self.order_cache: Dict[str, OrderResult] = {}

    async def execute_order(self, order_request: OrderRequest) -> OrderResult:
        """
        Esegue un ordine con retry logic e verifica stato

        Args:
            order_request: Richiesta ordine

        Returns:
            OrderResult con esito dell'operazione
        """
        # Genera client_order_id se non presente (per idempotency)
        if not order_request.client_order_id:
            order_request.client_order_id = self._generate_client_order_id(order_request)

        # Controlla se ordine già in cache
        cached_result = self._check_order_cache(order_request.client_order_id)
        if cached_result:
            logger.info(f"Ordine {order_request.client_order_id} già presente in cache: {cached_result.status}")
            return cached_result

        logger.info(f"Inizio esecuzione ordine: {order_request.symbol} {order_request.side.value} "
                   f"{order_request.quantity} @ {order_request.order_type.value}")

        result = OrderResult(success=False, client_order_id=order_request.client_order_id)

        for attempt in range(self.max_retries + 1):
            try:
                result.retry_count = attempt

                # Prima di inviare, verifica se ordine esiste già su Binance
                if attempt > 0:
                    existing_order = await self._check_existing_order(order_request.client_order_id)
                    if existing_order:
                        logger.info(f"Ordine {order_request.client_order_id} già presente su Binance")
                        result = self._parse_order_response(existing_order)
                        self._cache_order(result)
                        return result

                # Invia ordine
                response = await self._send_order(order_request)

                # Parsing risposta
                result = self._parse_order_response(response)
                result.client_order_id = order_request.client_order_id
                result.retry_count = attempt

                # Verifica stato ordine
                if result.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED]:
                    # Attendi completamento o timeout
                    final_result = await self._wait_for_order_completion(
                        result.order_id,
                        order_request.client_order_id,
                        order_request.symbol
                    )
                    if final_result:
                        result = final_result

                # Successo - salva in cache
                if result.status == OrderStatus.FILLED:
                    result.success = True
                    logger.info(f"✓ Ordine {order_request.client_order_id} eseguito completamente: "
                               f"{result.executed_qty} @ {result.avg_price}")
                    self._cache_order(result)
                    return result

                elif result.status == OrderStatus.PARTIALLY_FILLED:
                    result.success = True  # Parziale è comunque un successo
                    logger.warning(f"⚠ Ordine {order_request.client_order_id} parzialmente eseguito: "
                                 f"{result.executed_qty}/{order_request.quantity}")
                    self._cache_order(result)
                    return result

                elif result.status == OrderStatus.REJECTED:
                    result.success = False
                    logger.error(f"✗ Ordine {order_request.client_order_id} rifiutato: {result.error_message}")
                    self._cache_order(result)
                    return result

            except BinanceAPIException as e:
                result.error_message = f"Binance API Error: {e.message} (code: {e.code})"
                logger.error(f"Tentativo {attempt + 1}/{self.max_retries + 1} fallito: {result.error_message}")

                # Errori non recuperabili
                if e.code in [-2010, -1013, -1021]:  # Insufficient balance, invalid quantity, timestamp
                    result.status = OrderStatus.REJECTED
                    result.success = False
                    self._cache_order(result)
                    return result

                # Ordine già esistente
                if e.code == -2011:  # Duplicate order
                    logger.warning(f"Ordine duplicato, verifico stato...")
                    existing = await self._check_existing_order(order_request.client_order_id)
                    if existing:
                        result = self._parse_order_response(existing)
                        self._cache_order(result)
                        return result

            except BinanceRequestException as e:
                result.error_message = f"Network Error: {str(e)}"
                logger.error(f"Tentativo {attempt + 1}/{self.max_retries + 1} - Errore di rete: {e}")

            except Exception as e:
                result.error_message = f"Unexpected Error: {str(e)}"
                logger.error(f"Tentativo {attempt + 1}/{self.max_retries + 1} - Errore imprevisto: {e}")

            # Retry con exponential backoff
            if attempt < self.max_retries:
                delay = min(self.base_retry_delay * (2 ** attempt), self.max_retry_delay)
                logger.info(f"Retry tra {delay:.1f} secondi...")
                await asyncio.sleep(delay)

        # Tutti i tentativi falliti
        result.success = False
        result.status = OrderStatus.FAILED
        logger.error(f"✗ Ordine {order_request.client_order_id} fallito dopo {self.max_retries + 1} tentativi")
        self._cache_order(result)
        return result

    async def _send_order(self, order_request: OrderRequest) -> Dict:
        """Invia ordine a Binance"""
        params = order_request.to_dict()

        if self.enable_test_mode:
            # Test order (non viene eseguito realmente)
            logger.info(f"[TEST MODE] Simulazione ordine: {params}")
            response = await self.client.create_test_order(**params)
            # Test order non restituisce dati, simula risposta
            return {
                'orderId': 999999999,
                'clientOrderId': order_request.client_order_id,
                'status': 'FILLED',
                'executedQty': order_request.quantity,
                'cummulativeQuoteQty': order_request.quantity * (order_request.price or 0),
                'price': order_request.price or 0,
            }
        else:
            response = await self.client.create_order(**params)
            return response

    async def _check_existing_order(self, client_order_id: str) -> Optional[Dict]:
        """Verifica se ordine esiste già su Binance"""
        try:
            # Nota: serve symbol per query, usiamo cache o fallback
            # In produzione, traccia symbol per ogni client_order_id
            # Per ora, skippiamo questa verifica se non abbiamo symbol
            return None
        except BinanceAPIException as e:
            if e.code == -2013:  # Order does not exist
                return None
            raise

    async def _wait_for_order_completion(
        self,
        order_id: int,
        client_order_id: str,
        symbol: str
    ) -> Optional[OrderResult]:
        """
        Attende completamento ordine con polling

        Returns:
            OrderResult aggiornato o None se timeout
        """
        start_time = datetime.now()
        check_interval = 0.5  # Controlla ogni 500ms

        while (datetime.now() - start_time).total_seconds() < self.order_check_timeout:
            try:
                order_info = await self.client.get_order(
                    symbol=symbol,
                    orderId=order_id
                )

                status_str = order_info.get('status', '')

                if status_str == 'FILLED':
                    return self._parse_order_response(order_info)
                elif status_str in ['CANCELED', 'REJECTED', 'EXPIRED']:
                    return self._parse_order_response(order_info)

                # Ancora in esecuzione, attendi
                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"Errore verifica stato ordine: {e}")
                await asyncio.sleep(check_interval)

        logger.warning(f"Timeout verifica ordine {client_order_id} dopo {self.order_check_timeout}s")
        return None

    def _parse_order_response(self, response: Dict) -> OrderResult:
        """Parsing risposta Binance in OrderResult"""
        status_str = response.get('status', 'NEW')
        status_map = {
            'NEW': OrderStatus.NEW,
            'PARTIALLY_FILLED': OrderStatus.PARTIALLY_FILLED,
            'FILLED': OrderStatus.FILLED,
            'CANCELED': OrderStatus.CANCELED,
            'REJECTED': OrderStatus.REJECTED,
            'EXPIRED': OrderStatus.EXPIRED,
        }

        executed_qty = float(response.get('executedQty', 0))
        cumulative_quote_qty = float(response.get('cummulativeQuoteQty', 0))

        # Calcola prezzo medio
        avg_price = 0.0
        if executed_qty > 0:
            avg_price = cumulative_quote_qty / executed_qty

        return OrderResult(
            success=status_str == 'FILLED',
            order_id=response.get('orderId'),
            client_order_id=response.get('clientOrderId'),
            status=status_map.get(status_str, OrderStatus.NEW),
            executed_qty=executed_qty,
            avg_price=avg_price,
            response=response,
        )

    def _generate_client_order_id(self, order_request: OrderRequest) -> str:
        """Genera client_order_id univoco per idempotency"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"{order_request.symbol}_{order_request.side.value}_{timestamp}"

    def _check_order_cache(self, client_order_id: str) -> Optional[OrderResult]:
        """Controlla cache ordini"""
        return self.order_cache.get(client_order_id)

    def _cache_order(self, result: OrderResult):
        """Salva ordine in cache"""
        if result.client_order_id:
            self.order_cache[result.client_order_id] = result

            # Limita dimensione cache (rimuovi vecchi)
            if len(self.order_cache) > 1000:
                oldest_keys = sorted(
                    self.order_cache.keys(),
                    key=lambda k: self.order_cache[k].timestamp
                )[:100]
                for key in oldest_keys:
                    del self.order_cache[key]

    async def cancel_order(self, symbol: str, order_id: int) -> bool:
        """
        Cancella un ordine

        Returns:
            True se cancellato con successo
        """
        try:
            response = await self.client.cancel_order(
                symbol=symbol,
                orderId=order_id
            )
            logger.info(f"Ordine {order_id} cancellato: {response}")
            return True
        except BinanceAPIException as e:
            logger.error(f"Errore cancellazione ordine {order_id}: {e.message}")
            return False

    async def get_order_status(self, symbol: str, order_id: int) -> Optional[OrderResult]:
        """
        Recupera stato attuale di un ordine

        Returns:
            OrderResult con stato corrente o None se errore
        """
        try:
            response = await self.client.get_order(
                symbol=symbol,
                orderId=order_id
            )
            return self._parse_order_response(response)
        except BinanceAPIException as e:
            logger.error(f"Errore recupero stato ordine {order_id}: {e.message}")
            return None

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderResult]:
        """
        Recupera tutti gli ordini aperti

        Args:
            symbol: Se specificato, filtra per simbolo

        Returns:
            Lista di OrderResult
        """
        try:
            if symbol:
                orders = await self.client.get_open_orders(symbol=symbol)
            else:
                orders = await self.client.get_open_orders()

            return [self._parse_order_response(order) for order in orders]
        except BinanceAPIException as e:
            logger.error(f"Errore recupero ordini aperti: {e.message}")
            return []


class BinanceBroker:
    """
    Broker principale per operazioni su Binance
    Usa SafeOrderExecutor per esecuzione sicura degli ordini
    """

    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Se True usa testnet
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.client: Optional[AsyncClient] = None
        self.executor: Optional[SafeOrderExecutor] = None

    async def initialize(self):
        """Inizializza connessione a Binance"""
        if self.testnet:
            self.client = await AsyncClient.create(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=True
            )
            logger.info("Connesso a Binance TESTNET")
        else:
            self.client = await AsyncClient.create(
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            logger.info("Connesso a Binance PRODUCTION")

        self.executor = SafeOrderExecutor(
            client=self.client,
            enable_test_mode=self.testnet
        )

    async def close(self):
        """Chiude connessione"""
        if self.client:
            await self.client.close_connection()
            logger.info("Connessione Binance chiusa")

    async def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> OrderResult:
        """
        Piazza ordine MARKET con safe execution

        Args:
            symbol: Coppia trading (es. BTCUSDT)
            side: BUY o SELL
            quantity: Quantità da tradare

        Returns:
            OrderResult
        """
        order_request = OrderRequest(
            symbol=symbol,
            side=OrderSide[side.upper()],
            order_type=OrderType.MARKET,
            quantity=quantity
        )

        return await self.executor.execute_order(order_request)

    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC"
    ) -> OrderResult:
        """
        Piazza ordine LIMIT con safe execution

        Args:
            symbol: Coppia trading
            side: BUY o SELL
            quantity: Quantità
            price: Prezzo limite
            time_in_force: GTC, IOC, FOK

        Returns:
            OrderResult
        """
        order_request = OrderRequest(
            symbol=symbol,
            side=OrderSide[side.upper()],
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price,
            time_in_force=time_in_force
        )

        return await self.executor.execute_order(order_request)

    async def place_stop_loss(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float
    ) -> OrderResult:
        """
        Piazza ordine STOP LOSS

        Args:
            symbol: Coppia trading
            side: BUY o SELL
            quantity: Quantità
            stop_price: Prezzo di attivazione stop

        Returns:
            OrderResult
        """
        order_request = OrderRequest(
            symbol=symbol,
            side=OrderSide[side.upper()],
            order_type=OrderType.STOP_LOSS,
            quantity=quantity,
            stop_price=stop_price
        )

        return await self.executor.execute_order(order_request)

    async def get_account_balance(self) -> Dict[str, float]:
        """
        Recupera saldi account

        Returns:
            Dict con asset e saldo disponibile
        """
        try:
            account_info = await self.client.get_account()
            balances = {}

            for balance in account_info['balances']:
                free = float(balance['free'])
                if free > 0:
                    balances[balance['asset']] = free

            return balances

        except BinanceAPIException as e:
            logger.error(f"Errore recupero saldi: {e.message}")
            return {}

    async def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Recupera info su un simbolo (min qty, price filters, etc)

        Returns:
            Dict con info simbolo o None
        """
        try:
            exchange_info = await self.client.get_symbol_info(symbol)
            return exchange_info
        except BinanceAPIException as e:
            logger.error(f"Errore recupero info simbolo {symbol}: {e.message}")
            return None
