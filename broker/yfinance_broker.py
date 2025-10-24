"""
yFinance Paper Trading Broker
===============================
Simulates trading with yFinance data for paper trading across multiple asset classes.

Features:
- Paper trading simulation (no real money)
- Market, limit, and stop-loss orders
- Realistic slippage and commission
- Position tracking and P&L calculation
- Support for stocks, ETFs, crypto, forex
- Compatible with existing TradingSystem

WARNING: This is a PAPER TRADING broker. No real orders are executed.
"""

import asyncio
import uuid
import time
from typing import Optional, Dict, List
from datetime import datetime
import logging
from pathlib import Path
import json

from broker.base_broker import (
    BaseBroker, OrderRequest, OrderResult, Balance, Position,
    OrderStatus, OrderType, OrderSide
)
from extractors.yfinance_extractor import YFinanceExtractor

logger = logging.getLogger(__name__)


class YFinanceBroker(BaseBroker):
    """
    Paper trading broker using yFinance data

    Simulates order execution with:
    - Market orders: executed at current price + slippage
    - Limit orders: executed when price crosses limit
    - Stop-loss orders: executed when price crosses stop
    - Commission: configurable per trade
    - Slippage: configurable percentage
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission_pct: float = 0.001,  # 0.1%
        slippage_pct: float = 0.0005,  # 0.05%
        data_dir: str = 'data/paper_trading',
        config: Optional[Dict] = None
    ):
        """
        Initialize paper trading broker

        Args:
            initial_capital: Starting capital in USD
            commission_pct: Commission percentage per trade
            slippage_pct: Slippage percentage for market orders
            data_dir: Directory to save trading logs
            config: Additional configuration
        """
        super().__init__(config or {})

        self.initial_capital = initial_capital
        self.balance_usd = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct

        # Positions: symbol -> Position
        self.positions: Dict[str, Position] = {}

        # Orders: order_id -> order details
        self.orders: Dict[str, Dict] = {}
        self.open_orders: Dict[str, Dict] = {}  # Pending limit/stop orders

        # Trading history
        self.trade_history: List[Dict] = []
        self.balance_history: List[Dict] = []

        # Data extractor
        self.extractor = YFinanceExtractor()

        # Data directory
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_commission = 0.0
        self.total_pnl = 0.0

        logger.info(
            f"YFinanceBroker initialized - Capital: ${initial_capital}, "
            f"Commission: {commission_pct*100}%, Slippage: {slippage_pct*100}%"
        )

    async def initialize(self) -> bool:
        """Initialize broker"""
        self.is_initialized = True
        self._save_state()
        logger.info("YFinanceBroker ready for paper trading")
        return True

    async def shutdown(self):
        """Cleanup and save state"""
        self._save_state()
        self._generate_report()
        logger.info("YFinanceBroker shutdown complete")

    # Order Execution Methods

    async def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        client_order_id: Optional[str] = None
    ) -> OrderResult:
        """
        Execute simulated market order

        Args:
            symbol: Trading symbol
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            client_order_id: Optional unique ID

        Returns:
            OrderResult with execution details
        """
        try:
            # Validate
            if side not in ['BUY', 'SELL']:
                return OrderResult(
                    success=False,
                    error_message=f"Invalid side: {side}"
                )

            # Get current price from yFinance
            asset_type = self._detect_asset_type(symbol)
            current_price = await self.extractor.get_current_price(symbol, asset_type)

            if not current_price:
                return OrderResult(
                    success=False,
                    error_message=f"Unable to get price for {symbol}"
                )

            # Apply slippage (buy higher, sell lower)
            if side == 'BUY':
                execution_price = current_price * (1 + self.slippage_pct)
            else:
                execution_price = current_price * (1 - self.slippage_pct)

            # Calculate cost/proceeds
            if side == 'BUY':
                cost = execution_price * quantity
                commission = cost * self.commission_pct
                total_cost = cost + commission

                # Check balance
                if total_cost > self.balance_usd:
                    return OrderResult(
                        success=False,
                        error_message=f"Insufficient funds. Need ${total_cost:.2f}, have ${self.balance_usd:.2f}"
                    )

                # Execute buy
                self.balance_usd -= total_cost
                self.total_commission += commission

                # Update position
                if symbol in self.positions:
                    # Average up
                    pos = self.positions[symbol]
                    total_qty = pos.quantity + quantity
                    avg_price = (pos.entry_price * pos.quantity + execution_price * quantity) / total_qty
                    pos.quantity = total_qty
                    pos.entry_price = avg_price
                else:
                    # New position
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        side='LONG',
                        quantity=quantity,
                        entry_price=execution_price,
                        timestamp=int(time.time() * 1000)
                    )

            else:  # SELL
                # Check if we have position
                if symbol not in self.positions:
                    return OrderResult(
                        success=False,
                        error_message=f"No position to sell for {symbol}"
                    )

                pos = self.positions[symbol]
                if pos.quantity < quantity:
                    return OrderResult(
                        success=False,
                        error_message=f"Insufficient quantity. Have {pos.quantity}, trying to sell {quantity}"
                    )

                # Execute sell
                proceeds = execution_price * quantity
                commission = proceeds * self.commission_pct
                total_proceeds = proceeds - commission

                self.balance_usd += total_proceeds
                self.total_commission += commission

                # Calculate P&L
                pnl = (execution_price - pos.entry_price) * quantity - commission
                self.total_pnl += pnl

                if pnl > 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1

                # Update position
                pos.quantity -= quantity
                if pos.quantity <= 0:
                    del self.positions[symbol]

            # Create order record
            order_id = str(uuid.uuid4())
            client_order_id = client_order_id or order_id

            order = {
                'order_id': order_id,
                'client_order_id': client_order_id,
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': quantity,
                'price': execution_price,
                'commission': commission,
                'status': 'FILLED',
                'timestamp': int(time.time() * 1000)
            }

            self.orders[order_id] = order
            self.trade_history.append(order)
            self.total_trades += 1

            # Log balance
            self._record_balance()

            logger.info(
                f"Paper trade executed: {side} {quantity} {symbol} @ ${execution_price:.2f} "
                f"(Commission: ${commission:.2f})"
            )

            return OrderResult(
                success=True,
                order_id=order_id,
                client_order_id=client_order_id,
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=quantity,
                filled_quantity=quantity,
                avg_price=execution_price,
                status='FILLED',
                timestamp=int(time.time() * 1000)
            )

        except Exception as e:
            logger.error(f"Error executing market order: {e}")
            return OrderResult(
                success=False,
                error_message=str(e)
            )

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
        Place limit order (simulated)

        Note: Limit orders are stored but not actively monitored in this simple implementation.
        For full simulation, you'd need a background task checking prices.
        """
        try:
            order_id = str(uuid.uuid4())
            client_order_id = client_order_id or order_id

            order = {
                'order_id': order_id,
                'client_order_id': client_order_id,
                'symbol': symbol,
                'side': side,
                'type': 'LIMIT',
                'quantity': quantity,
                'price': price,
                'time_in_force': time_in_force,
                'status': 'NEW',
                'timestamp': int(time.time() * 1000)
            }

            self.orders[order_id] = order
            self.open_orders[order_id] = order

            logger.info(f"Limit order placed: {side} {quantity} {symbol} @ ${price:.2f}")

            return OrderResult(
                success=True,
                order_id=order_id,
                client_order_id=client_order_id,
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                quantity=quantity,
                filled_quantity=0,
                avg_price=price,
                status='NEW',
                timestamp=int(time.time() * 1000)
            )

        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            return OrderResult(success=False, error_message=str(e))

    async def place_stop_loss(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float,
        client_order_id: Optional[str] = None
    ) -> OrderResult:
        """
        Place stop-loss order (simulated)

        Note: Stop orders are stored but not actively monitored in this simple implementation.
        """
        try:
            order_id = str(uuid.uuid4())
            client_order_id = client_order_id or order_id

            order = {
                'order_id': order_id,
                'client_order_id': client_order_id,
                'symbol': symbol,
                'side': side,
                'type': 'STOP_LOSS',
                'quantity': quantity,
                'stop_price': stop_price,
                'status': 'NEW',
                'timestamp': int(time.time() * 1000)
            }

            self.orders[order_id] = order
            self.open_orders[order_id] = order

            logger.info(f"Stop-loss placed: {side} {quantity} {symbol} @ ${stop_price:.2f}")

            return OrderResult(
                success=True,
                order_id=order_id,
                client_order_id=client_order_id,
                symbol=symbol,
                side=side,
                order_type='STOP_LOSS',
                quantity=quantity,
                status='NEW',
                timestamp=int(time.time() * 1000)
            )

        except Exception as e:
            logger.error(f"Error placing stop-loss: {e}")
            return OrderResult(success=False, error_message=str(e))

    async def cancel_order(
        self,
        symbol: str,
        order_id: Optional[str] = None,
        client_order_id: Optional[str] = None
    ) -> OrderResult:
        """Cancel pending order"""
        try:
            # Find order
            target_order_id = None
            if order_id:
                target_order_id = order_id
            elif client_order_id:
                for oid, order in self.orders.items():
                    if order.get('client_order_id') == client_order_id:
                        target_order_id = oid
                        break

            if not target_order_id or target_order_id not in self.open_orders:
                return OrderResult(
                    success=False,
                    error_message="Order not found or already filled"
                )

            # Cancel order
            order = self.open_orders[target_order_id]
            order['status'] = 'CANCELED'
            del self.open_orders[target_order_id]

            logger.info(f"Order canceled: {target_order_id}")

            return OrderResult(
                success=True,
                order_id=target_order_id,
                status='CANCELED'
            )

        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            return OrderResult(success=False, error_message=str(e))

    async def get_order_status(
        self,
        symbol: str,
        order_id: Optional[str] = None,
        client_order_id: Optional[str] = None
    ) -> OrderResult:
        """Get order status"""
        try:
            # Find order
            order = None
            if order_id:
                order = self.orders.get(order_id)
            elif client_order_id:
                for o in self.orders.values():
                    if o.get('client_order_id') == client_order_id:
                        order = o
                        break

            if not order:
                return OrderResult(
                    success=False,
                    error_message="Order not found"
                )

            return OrderResult(
                success=True,
                order_id=order['order_id'],
                client_order_id=order.get('client_order_id'),
                symbol=order['symbol'],
                side=order['side'],
                order_type=order['type'],
                quantity=order['quantity'],
                status=order['status']
            )

        except Exception as e:
            return OrderResult(success=False, error_message=str(e))

    # Account Information Methods

    async def get_account_balance(self, asset: Optional[str] = None) -> Dict[str, Balance]:
        """Get account balance"""
        balances = {
            'USD': Balance(
                asset='USD',
                free=self.balance_usd,
                locked=0.0,
                total=self.balance_usd
            )
        }

        # Add position values
        for symbol, pos in self.positions.items():
            asset_type = self._detect_asset_type(symbol)
            current_price = await self.extractor.get_current_price(symbol, asset_type)

            if current_price:
                value = pos.quantity * current_price

                balances[symbol] = Balance(
                    asset=symbol,
                    free=pos.quantity,
                    locked=0.0,
                    total=pos.quantity
                )

        if asset:
            return {asset: balances.get(asset, Balance(asset=asset, free=0, locked=0, total=0))}

        return balances

    async def get_positions(self) -> List[Position]:
        """Get all open positions with current P&L"""
        positions = []

        for symbol, pos in self.positions.items():
            asset_type = self._detect_asset_type(symbol)
            current_price = await self.extractor.get_current_price(symbol, asset_type)

            if current_price:
                pos.current_price = current_price
                pos.unrealized_pnl = (current_price - pos.entry_price) * pos.quantity

            positions.append(pos)

        return positions

    async def get_symbol_info(self, symbol: str) -> Dict:
        """Get symbol information"""
        asset_type = self._detect_asset_type(symbol)
        info = await self.extractor.get_ticker_info(symbol, asset_type)
        return info

    async def get_current_price(self, symbol: str) -> float:
        """Get current price"""
        asset_type = self._detect_asset_type(symbol)
        price = await self.extractor.get_current_price(symbol, asset_type)
        return price or 0.0

    async def get_ticker(self, symbol: str) -> Dict:
        """Get ticker data"""
        latest = await self.extractor.get_latest_data(symbol, '1m')
        if latest is not None:
            return {
                'symbol': symbol,
                'price': float(latest.get('Close', 0)),
                'volume': float(latest.get('Volume', 0))
            }
        return {'symbol': symbol, 'price': 0, 'volume': 0}

    # Broker Metadata

    def get_broker_name(self) -> str:
        return "yFinance Paper Trading"

    def is_paper_trading(self) -> bool:
        return True

    def supports_asset_type(self, asset_type: str) -> bool:
        """Support all asset types via yFinance"""
        return asset_type in ['stock', 'etf', 'crypto', 'forex', 'commodity', 'index']

    # Helper Methods

    def _detect_asset_type(self, symbol: str) -> str:
        """Detect asset type from symbol"""
        symbol = symbol.upper()

        if '-USD' in symbol or '-USDT' in symbol:
            return 'crypto'
        elif '=X' in symbol:
            return 'forex'
        elif '=F' in symbol:
            return 'commodity'
        else:
            return 'stock'  # Default

    def _record_balance(self):
        """Record balance snapshot"""
        self.balance_history.append({
            'timestamp': int(time.time() * 1000),
            'balance': self.balance_usd,
            'total_value': self._calculate_total_portfolio_value()
        })

    def _calculate_total_portfolio_value(self) -> float:
        """Calculate total portfolio value (cash + positions)"""
        total = self.balance_usd

        # Add unrealized P&L from positions (synchronous version)
        for symbol, pos in self.positions.items():
            # Use cached price or entry price
            try:
                current_price = asyncio.run(self.get_current_price(symbol))
                if current_price:
                    total += pos.quantity * current_price
            except:
                total += pos.quantity * pos.entry_price

        return total

    def _save_state(self):
        """Save broker state to disk"""
        state = {
            'initial_capital': self.initial_capital,
            'balance_usd': self.balance_usd,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_commission': self.total_commission,
            'total_pnl': self.total_pnl,
            'positions': {
                symbol: {
                    'symbol': pos.symbol,
                    'side': pos.side,
                    'quantity': pos.quantity,
                    'entry_price': pos.entry_price
                }
                for symbol, pos in self.positions.items()
            },
            'timestamp': int(time.time() * 1000)
        }

        filename = self.data_dir / 'broker_state.json'
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)

    def _generate_report(self):
        """Generate trading report"""
        total_value = self._calculate_total_portfolio_value()
        total_return = ((total_value - self.initial_capital) / self.initial_capital) * 100

        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        report = f"""
{'='*60}
PAPER TRADING REPORT - yFinance Broker
{'='*60}
Initial Capital:    ${self.initial_capital:,.2f}
Current Balance:    ${self.balance_usd:,.2f}
Portfolio Value:    ${total_value:,.2f}
Total Return:       {total_return:+.2f}%

Total Trades:       {self.total_trades}
Winning Trades:     {self.winning_trades}
Losing Trades:      {self.losing_trades}
Win Rate:           {win_rate:.1f}%

Total P&L:          ${self.total_pnl:+,.2f}
Total Commission:   ${self.total_commission:,.2f}

Open Positions:     {len(self.positions)}
{'='*60}
"""

        logger.info(report)

        # Save to file
        with open(self.data_dir / 'trading_report.txt', 'w') as f:
            f.write(report)

    def get_statistics(self) -> Dict:
        """Get trading statistics"""
        total_value = self._calculate_total_portfolio_value()
        return {
            'initial_capital': self.initial_capital,
            'current_balance': self.balance_usd,
            'portfolio_value': total_value,
            'total_return_pct': ((total_value - self.initial_capital) / self.initial_capital) * 100,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
            'total_pnl': self.total_pnl,
            'total_commission': self.total_commission,
            'open_positions': len(self.positions)
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)

    async def main():
        # Create paper trading broker
        broker = YFinanceBroker(initial_capital=10000)
        await broker.initialize()

        # Test buy order
        print("\n=== Buying 10 shares of AAPL ===")
        result = await broker.place_market_order('AAPL', 'BUY', 10)
        print(f"Success: {result.success}")
        if result.success:
            print(f"Price: ${result.avg_price:.2f}")

        # Check positions
        print("\n=== Checking Positions ===")
        positions = await broker.get_positions()
        for pos in positions:
            print(f"{pos.symbol}: {pos.quantity} @ ${pos.entry_price:.2f} (P&L: ${pos.unrealized_pnl:.2f})")

        # Check balance
        print("\n=== Checking Balance ===")
        balances = await broker.get_account_balance()
        for asset, balance in balances.items():
            print(f"{asset}: {balance.total}")

        # Statistics
        print("\n=== Statistics ===")
        stats = broker.get_statistics()
        for key, value in stats.items():
            print(f"{key}: {value}")

        await broker.shutdown()

    asyncio.run(main())
