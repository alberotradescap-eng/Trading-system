"""
Base Broker Interface
=====================
Abstract base class for all broker implementations (Binance, yFinance, Interactive Brokers, etc.)

This ensures consistent interface across different trading platforms.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"


class OrderSide(Enum):
    """Order side enumeration"""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class OrderRequest:
    """Order request parameters"""
    symbol: str
    side: str  # 'BUY' or 'SELL'
    order_type: str  # 'MARKET', 'LIMIT', 'STOP_LOSS'
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # Good Till Cancel
    client_order_id: Optional[str] = None


@dataclass
class OrderResult:
    """Order execution result"""
    success: bool
    order_id: Optional[str] = None
    client_order_id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    order_type: Optional[str] = None
    quantity: Optional[float] = None
    filled_quantity: Optional[float] = None
    avg_price: Optional[float] = None
    status: Optional[str] = None
    timestamp: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict] = None


@dataclass
class Balance:
    """Account balance information"""
    asset: str
    free: float
    locked: float
    total: float


@dataclass
class Position:
    """Trading position information"""
    symbol: str
    side: str  # 'LONG' or 'SHORT'
    quantity: float
    entry_price: float
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None
    timestamp: Optional[int] = None


class BaseBroker(ABC):
    """
    Abstract base class for all broker implementations.

    All brokers (Binance, yFinance, Interactive Brokers, etc.) must implement these methods.
    """

    def __init__(self, config: Dict):
        """
        Initialize broker with configuration

        Args:
            config: Broker-specific configuration dictionary
        """
        self.config = config
        self.is_initialized = False

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize broker connection and verify credentials

        Returns:
            bool: True if initialization successful
        """
        pass

    @abstractmethod
    async def shutdown(self):
        """
        Cleanup resources and close connections
        """
        pass

    # Order Execution Methods

    @abstractmethod
    async def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        client_order_id: Optional[str] = None
    ) -> OrderResult:
        """
        Place a market order

        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT', 'AAPL')
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            client_order_id: Optional unique identifier

        Returns:
            OrderResult with execution details
        """
        pass

    @abstractmethod
    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
        client_order_id: Optional[str] = None
    ) -> OrderResult:
        """
        Place a limit order

        Args:
            symbol: Trading symbol
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            price: Limit price
            time_in_force: Time in force (GTC, IOC, FOK)
            client_order_id: Optional unique identifier

        Returns:
            OrderResult with execution details
        """
        pass

    @abstractmethod
    async def place_stop_loss(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float,
        client_order_id: Optional[str] = None
    ) -> OrderResult:
        """
        Place a stop-loss order

        Args:
            symbol: Trading symbol
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            stop_price: Stop trigger price
            client_order_id: Optional unique identifier

        Returns:
            OrderResult with execution details
        """
        pass

    @abstractmethod
    async def cancel_order(
        self,
        symbol: str,
        order_id: Optional[str] = None,
        client_order_id: Optional[str] = None
    ) -> OrderResult:
        """
        Cancel an existing order

        Args:
            symbol: Trading symbol
            order_id: Exchange order ID
            client_order_id: Client order ID

        Returns:
            OrderResult with cancellation details
        """
        pass

    @abstractmethod
    async def get_order_status(
        self,
        symbol: str,
        order_id: Optional[str] = None,
        client_order_id: Optional[str] = None
    ) -> OrderResult:
        """
        Get order status

        Args:
            symbol: Trading symbol
            order_id: Exchange order ID
            client_order_id: Client order ID

        Returns:
            OrderResult with current status
        """
        pass

    # Account Information Methods

    @abstractmethod
    async def get_account_balance(self, asset: Optional[str] = None) -> Dict[str, Balance]:
        """
        Get account balance

        Args:
            asset: Specific asset to query (None for all)

        Returns:
            Dictionary of asset -> Balance
        """
        pass

    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """
        Get all open positions

        Returns:
            List of Position objects
        """
        pass

    # Market Data Methods

    @abstractmethod
    async def get_symbol_info(self, symbol: str) -> Dict:
        """
        Get symbol/contract information

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary with symbol details (min_quantity, price_precision, etc.)
        """
        pass

    @abstractmethod
    async def get_current_price(self, symbol: str) -> float:
        """
        Get current market price

        Args:
            symbol: Trading symbol

        Returns:
            Current price as float
        """
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict:
        """
        Get ticker information (last price, volume, etc.)

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary with ticker data
        """
        pass

    # Broker Metadata

    @abstractmethod
    def get_broker_name(self) -> str:
        """
        Get broker name

        Returns:
            Broker name (e.g., 'Binance', 'yFinance', 'InteractiveBrokers')
        """
        pass

    @abstractmethod
    def is_paper_trading(self) -> bool:
        """
        Check if this is a paper trading broker

        Returns:
            True if paper trading, False if real trading
        """
        pass

    @abstractmethod
    def supports_asset_type(self, asset_type: str) -> bool:
        """
        Check if broker supports an asset type

        Args:
            asset_type: 'crypto', 'stock', 'etf', 'forex', 'commodity', etc.

        Returns:
            True if supported
        """
        pass

    # Helper Methods

    def validate_order_request(self, request: OrderRequest) -> tuple[bool, Optional[str]]:
        """
        Validate order request parameters

        Args:
            request: OrderRequest to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not request.symbol:
            return False, "Symbol is required"

        if request.side not in ['BUY', 'SELL']:
            return False, f"Invalid side: {request.side}. Must be 'BUY' or 'SELL'"

        if request.quantity <= 0:
            return False, "Quantity must be positive"

        if request.order_type == 'LIMIT' and not request.price:
            return False, "Price required for LIMIT orders"

        if request.order_type == 'STOP_LOSS' and not request.stop_price:
            return False, "Stop price required for STOP_LOSS orders"

        return True, None

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"broker={self.get_broker_name()}, "
            f"paper_trading={self.is_paper_trading()}, "
            f"initialized={self.is_initialized})"
        )
