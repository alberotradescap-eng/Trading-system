"""
Position Manager - Gestione posizioni aperte con tracking P&L
"""
import logging
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PositionSide(Enum):
    """Lato della posizione"""
    LONG = "LONG"
    SHORT = "SHORT"


class PositionStatus(Enum):
    """Stato della posizione"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARTIAL = "PARTIAL"  # Parzialmente chiusa


@dataclass
class Position:
    """Rappresenta una posizione aperta"""
    symbol: str
    side: PositionSide
    entry_price: float
    quantity: float
    entry_time: datetime = field(default_factory=datetime.now)

    # Ordini associati
    entry_order_id: Optional[int] = None
    stop_loss_order_id: Optional[int] = None
    take_profit_order_id: Optional[int] = None

    # Stato posizione
    status: PositionStatus = PositionStatus.OPEN
    remaining_quantity: float = field(init=False)

    # Exit info
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_order_id: Optional[int] = None

    # P&L
    realized_pnl: float = 0.0
    realized_pnl_percentage: float = 0.0

    # Metadata
    strategy_name: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        self.remaining_quantity = self.quantity

    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """
        Calcola P&L non realizzato

        Args:
            current_price: Prezzo corrente di mercato

        Returns:
            P&L in valuta quote
        """
        if self.side == PositionSide.LONG:
            pnl = (current_price - self.entry_price) * self.remaining_quantity
        else:  # SHORT
            pnl = (self.entry_price - current_price) * self.remaining_quantity

        return pnl

    def calculate_unrealized_pnl_percentage(self, current_price: float) -> float:
        """Calcola P&L % non realizzato"""
        if self.entry_price == 0:
            return 0.0

        if self.side == PositionSide.LONG:
            return ((current_price - self.entry_price) / self.entry_price) * 100
        else:  # SHORT
            return ((self.entry_price - current_price) / self.entry_price) * 100

    def partial_close(self, quantity: float, exit_price: float) -> float:
        """
        Chiude parzialmente la posizione

        Args:
            quantity: Quantità da chiudere
            exit_price: Prezzo di uscita

        Returns:
            P&L realizzato per questa chiusura parziale
        """
        if quantity > self.remaining_quantity:
            quantity = self.remaining_quantity

        # Calcola P&L per la quantità chiusa
        if self.side == PositionSide.LONG:
            pnl = (exit_price - self.entry_price) * quantity
        else:
            pnl = (self.entry_price - exit_price) * quantity

        self.remaining_quantity -= quantity
        self.realized_pnl += pnl

        if self.remaining_quantity == 0:
            self.status = PositionStatus.CLOSED
            self.exit_price = exit_price
            self.exit_time = datetime.now()
        else:
            self.status = PositionStatus.PARTIAL

        # Calcola percentuale P&L
        total_entry_value = self.entry_price * self.quantity
        if total_entry_value > 0:
            self.realized_pnl_percentage = (self.realized_pnl / total_entry_value) * 100

        logger.info(f"Posizione {self.symbol} parzialmente chiusa: {quantity} @ {exit_price}, "
                   f"P&L: {pnl:.2f} ({self.realized_pnl_percentage:.2f}%)")

        return pnl

    def close(self, exit_price: float, exit_order_id: Optional[int] = None):
        """
        Chiude completamente la posizione

        Args:
            exit_price: Prezzo di uscita
            exit_order_id: ID ordine di uscita
        """
        pnl = self.partial_close(self.remaining_quantity, exit_price)
        self.exit_price = exit_price
        self.exit_time = datetime.now()
        self.exit_order_id = exit_order_id
        self.status = PositionStatus.CLOSED

        logger.info(f"Posizione {self.symbol} chiusa completamente @ {exit_price}, "
                   f"P&L totale: {self.realized_pnl:.2f} ({self.realized_pnl_percentage:.2f}%)")

    def is_open(self) -> bool:
        """Verifica se posizione è aperta"""
        return self.status in [PositionStatus.OPEN, PositionStatus.PARTIAL]

    def get_info(self) -> Dict:
        """Ritorna info posizione come dict"""
        return {
            'symbol': self.symbol,
            'side': self.side.value,
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'remaining_quantity': self.remaining_quantity,
            'status': self.status.value,
            'entry_time': self.entry_time.isoformat(),
            'exit_price': self.exit_price,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'realized_pnl': self.realized_pnl,
            'realized_pnl_percentage': self.realized_pnl_percentage,
            'entry_order_id': self.entry_order_id,
            'stop_loss_order_id': self.stop_loss_order_id,
            'take_profit_order_id': self.take_profit_order_id,
            'strategy_name': self.strategy_name,
        }


class PositionManager:
    """
    Manager per gestione posizioni multiple
    """

    def __init__(self):
        self.positions: Dict[str, Position] = {}  # symbol -> Position
        self.closed_positions: List[Position] = []

        # Statistiche
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0

    def open_position(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
        entry_order_id: Optional[int] = None,
        strategy_name: Optional[str] = None
    ) -> Position:
        """
        Apre una nuova posizione

        Args:
            symbol: Simbolo (es. BTCUSDT)
            side: LONG o SHORT
            entry_price: Prezzo di entrata
            quantity: Quantità
            entry_order_id: ID ordine di entrata
            strategy_name: Nome strategia

        Returns:
            Position creata
        """
        # Verifica se esiste già posizione aperta
        if symbol in self.positions and self.positions[symbol].is_open():
            logger.warning(f"Posizione {symbol} già aperta, chiudila prima di aprirne una nuova")
            raise ValueError(f"Posizione {symbol} già aperta")

        position = Position(
            symbol=symbol,
            side=PositionSide[side.upper()],
            entry_price=entry_price,
            quantity=quantity,
            entry_order_id=entry_order_id,
            strategy_name=strategy_name
        )

        self.positions[symbol] = position
        self.total_trades += 1

        logger.info(f"✓ Posizione {symbol} aperta: {side} {quantity} @ {entry_price}")

        return position

    def close_position(
        self,
        symbol: str,
        exit_price: float,
        exit_order_id: Optional[int] = None
    ) -> Optional[Position]:
        """
        Chiude una posizione

        Args:
            symbol: Simbolo
            exit_price: Prezzo di uscita
            exit_order_id: ID ordine di uscita

        Returns:
            Position chiusa o None se non trovata
        """
        if symbol not in self.positions:
            logger.warning(f"Posizione {symbol} non trovata")
            return None

        position = self.positions[symbol]

        if not position.is_open():
            logger.warning(f"Posizione {symbol} già chiusa")
            return None

        position.close(exit_price, exit_order_id)

        # Aggiorna statistiche
        self.total_pnl += position.realized_pnl
        if position.realized_pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        # Sposta in closed_positions
        self.closed_positions.append(position)
        del self.positions[symbol]

        logger.info(f"✓ Posizione {symbol} chiusa con P&L: {position.realized_pnl:.2f} "
                   f"({position.realized_pnl_percentage:.2f}%)")

        return position

    def partial_close_position(
        self,
        symbol: str,
        quantity: float,
        exit_price: float
    ) -> Optional[float]:
        """
        Chiude parzialmente una posizione

        Returns:
            P&L realizzato o None se errore
        """
        if symbol not in self.positions:
            logger.warning(f"Posizione {symbol} non trovata")
            return None

        position = self.positions[symbol]

        if not position.is_open():
            logger.warning(f"Posizione {symbol} non aperta")
            return None

        pnl = position.partial_close(quantity, exit_price)

        # Se completamente chiusa, sposta in closed_positions
        if position.status == PositionStatus.CLOSED:
            self.total_pnl += position.realized_pnl
            if position.realized_pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1

            self.closed_positions.append(position)
            del self.positions[symbol]

        return pnl

    def get_position(self, symbol: str) -> Optional[Position]:
        """Recupera posizione aperta per simbolo"""
        return self.positions.get(symbol)

    def get_all_positions(self) -> List[Position]:
        """Recupera tutte le posizioni aperte"""
        return list(self.positions.values())

    def has_open_position(self, symbol: str) -> bool:
        """Verifica se c'è una posizione aperta per il simbolo"""
        return symbol in self.positions and self.positions[symbol].is_open()

    def get_unrealized_pnl(self, symbol: str, current_price: float) -> Optional[float]:
        """
        Calcola P&L non realizzato per una posizione

        Args:
            symbol: Simbolo
            current_price: Prezzo corrente di mercato

        Returns:
            P&L o None se posizione non trovata
        """
        position = self.get_position(symbol)
        if not position:
            return None

        return position.calculate_unrealized_pnl(current_price)

    def get_total_unrealized_pnl(self, current_prices: Dict[str, float]) -> float:
        """
        Calcola P&L totale non realizzato per tutte le posizioni

        Args:
            current_prices: Dict con symbol -> prezzo corrente

        Returns:
            P&L totale
        """
        total_pnl = 0.0

        for symbol, position in self.positions.items():
            if symbol in current_prices:
                pnl = position.calculate_unrealized_pnl(current_prices[symbol])
                total_pnl += pnl

        return total_pnl

    def set_stop_loss(self, symbol: str, stop_loss_order_id: int):
        """Associa ordine stop loss a posizione"""
        if symbol in self.positions:
            self.positions[symbol].stop_loss_order_id = stop_loss_order_id
            logger.info(f"Stop loss impostato per {symbol}: order_id={stop_loss_order_id}")

    def set_take_profit(self, symbol: str, take_profit_order_id: int):
        """Associa ordine take profit a posizione"""
        if symbol in self.positions:
            self.positions[symbol].take_profit_order_id = take_profit_order_id
            logger.info(f"Take profit impostato per {symbol}: order_id={take_profit_order_id}")

    def get_statistics(self) -> Dict:
        """
        Ritorna statistiche trading

        Returns:
            Dict con statistiche
        """
        win_rate = 0.0
        if self.total_trades > 0:
            win_rate = (self.winning_trades / self.total_trades) * 100

        avg_win = 0.0
        avg_loss = 0.0

        if self.winning_trades > 0:
            total_wins = sum(p.realized_pnl for p in self.closed_positions if p.realized_pnl > 0)
            avg_win = total_wins / self.winning_trades

        if self.losing_trades > 0:
            total_losses = sum(p.realized_pnl for p in self.closed_positions if p.realized_pnl < 0)
            avg_loss = total_losses / self.losing_trades

        profit_factor = 0.0
        if avg_loss != 0:
            profit_factor = abs(avg_win / avg_loss)

        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_pnl': self.total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'open_positions': len(self.positions),
        }

    def get_summary(self) -> str:
        """Ritorna summary testuale delle statistiche"""
        stats = self.get_statistics()

        summary = f"""
╔════════════════════════════════════════╗
║       POSITION MANAGER STATISTICS      ║
╠════════════════════════════════════════╣
║ Total Trades: {stats['total_trades']:>23} ║
║ Winning Trades: {stats['winning_trades']:>21} ║
║ Losing Trades: {stats['losing_trades']:>22} ║
║ Win Rate: {stats['win_rate']:>28.2f}% ║
║ Total P&L: {stats['total_pnl']:>26.2f} ║
║ Avg Win: {stats['avg_win']:>28.2f} ║
║ Avg Loss: {stats['avg_loss']:>27.2f} ║
║ Profit Factor: {stats['profit_factor']:>22.2f} ║
║ Open Positions: {stats['open_positions']:>21} ║
╚════════════════════════════════════════╝
"""
        return summary

    def export_closed_positions(self) -> List[Dict]:
        """
        Esporta tutte le posizioni chiuse

        Returns:
            Lista di dict con info posizioni
        """
        return [pos.get_info() for pos in self.closed_positions]
