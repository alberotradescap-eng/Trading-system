"""
Portfolio Manager - Gestione del portfolio complessivo

Coordina tutte le posizioni, monitora il balance totale,
gestisce la diversificazione e l'allocazione del capitale.
"""

from datetime import datetime
from loguru import logger


class PortfolioManager:
    """
    Gestisce il portfolio completo di trading
    """

    def __init__(self, config, initial_capital):
        """
        Args:
            config: Dictionary con configurazione
            initial_capital: Capitale iniziale ($)
        """
        self.config = config
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.available_capital = initial_capital
        self.locked_capital = 0.0  # Capitale bloccato in posizioni aperte

        # Tracking
        self.total_deposits = 0.0
        self.total_withdrawals = 0.0
        self.total_fees = 0.0

        # Performance
        self.daily_returns = []
        self.equity_curve = []

        logger.info(f"PortfolioManager inizializzato con capitale: ${initial_capital:.2f}")

    # ========================================================================
    # CAPITAL MANAGEMENT
    # ========================================================================

    def update_portfolio(self, positions, account_info):
        """
        Aggiorna lo stato del portfolio

        Args:
            positions: Lista posizioni aperte
            account_info: Info account da broker (balance, etc.)
        """
        # Aggiorna balance da account info
        if 'totalWalletBalance' in account_info:
            self.current_capital = float(account_info['totalWalletBalance'])

        # Calcola capitale bloccato in posizioni
        self.locked_capital = sum(
            pos.get('entry_price', 0) * pos.get('quantity', 0)
            for pos in positions
        )

        # Calcola capitale disponibile
        self.available_capital = self.current_capital - self.locked_capital

        # Calcola unrealized PnL dalle posizioni aperte
        unrealized_pnl = sum(
            pos.get('unrealized_pnl', 0)
            for pos in positions
        )

        # Aggiungi a equity curve
        self.equity_curve.append({
            'timestamp': datetime.now(),
            'total_capital': self.current_capital,
            'locked_capital': self.locked_capital,
            'available_capital': self.available_capital,
            'unrealized_pnl': unrealized_pnl,
        })

        logger.debug(
            f"Portfolio aggiornato: Total=${self.current_capital:.2f} "
            f"Available=${self.available_capital:.2f} "
            f"Locked=${self.locked_capital:.2f}"
        )

    def get_available_capital(self):
        """
        Ritorna capitale disponibile per nuovi trade

        Returns:
            float: Capitale disponibile
        """
        return self.available_capital

    def get_total_capital(self):
        """
        Ritorna capitale totale (disponibile + locked)

        Returns:
            float: Capitale totale
        """
        return self.current_capital

    # ========================================================================
    # ALLOCATION & DIVERSIFICATION
    # ========================================================================

    def calculate_allocation(self, positions):
        """
        Calcola allocazione del capitale per simbolo

        Args:
            positions: Lista posizioni aperte

        Returns:
            dict: {symbol: {value: float, pct: float}}
        """
        if not positions:
            return {}

        allocation = {}

        for pos in positions:
            symbol = pos['symbol']
            value = pos.get('entry_price', 0) * pos.get('quantity', 0)
            pct = (value / self.current_capital * 100) if self.current_capital > 0 else 0

            allocation[symbol] = {
                'value': value,
                'pct': pct,
                'unrealized_pnl': pos.get('unrealized_pnl', 0),
            }

        return allocation

    def check_diversification(self, positions):
        """
        Controlla se il portfolio è ben diversificato

        Args:
            positions: Lista posizioni aperte

        Returns:
            dict: {
                'is_diversified': bool,
                'concentration_risk': float,  # % del capitale in posizione più grande
                'num_positions': int,
                'recommendations': list
            }
        """
        if not positions:
            return {
                'is_diversified': True,
                'concentration_risk': 0,
                'num_positions': 0,
                'recommendations': []
            }

        allocation = self.calculate_allocation(positions)
        recommendations = []

        # Trova posizione più grande
        max_allocation_pct = max(
            alloc['pct'] for alloc in allocation.values()
        ) if allocation else 0

        # Controlla concentrazione
        if max_allocation_pct > 40:
            recommendations.append(
                f"Concentrazione alta: {max_allocation_pct:.1f}% in singola posizione. "
                "Considera di diversificare."
            )

        # Controlla numero posizioni
        num_positions = len(positions)
        max_positions = self.config['trading'].get('max_positions', 3)

        if num_positions == 1:
            recommendations.append("Solo 1 posizione aperta. Considera di diversificare.")
        elif num_positions >= max_positions:
            recommendations.append(f"Max posizioni raggiunto ({num_positions}/{max_positions})")

        # Determina se diversificato
        is_diversified = max_allocation_pct < 40 and num_positions >= 2

        return {
            'is_diversified': is_diversified,
            'concentration_risk': max_allocation_pct,
            'num_positions': num_positions,
            'recommendations': recommendations,
        }

    def suggest_position_allocation(self, num_planned_positions):
        """
        Suggerisce allocazione ottimale del capitale

        Args:
            num_planned_positions: Numero di posizioni che si vogliono aprire

        Returns:
            float: % di capitale suggerito per ogni posizione
        """
        if num_planned_positions <= 0:
            return 0

        # Allocazione uguale per tutte le posizioni
        # Ma lasciamo sempre un buffer (es. 10%) disponibile
        max_total_allocation = 90  # Usa max 90% del capitale

        suggested_pct = max_total_allocation / num_planned_positions

        # Controlla limiti
        max_position_pct = self.config['trading'].get('position_size_pct', 2.0)

        if suggested_pct > max_position_pct:
            suggested_pct = max_position_pct

        return round(suggested_pct, 2)

    # ========================================================================
    # PERFORMANCE TRACKING
    # ========================================================================

    def calculate_returns(self):
        """
        Calcola returns del portfolio

        Returns:
            dict: {
                'total_return': float,  # % return from start
                'total_return_usd': float,  # $ return from start
                'daily_return': float,  # % return today
                'roi': float,  # Return on Investment %
            }
        """
        total_return_usd = self.current_capital - self.initial_capital
        total_return_pct = (
            (total_return_usd / self.initial_capital * 100)
            if self.initial_capital > 0 else 0
        )

        # Daily return (se abbiamo dati equity curve)
        daily_return = 0.0
        if len(self.equity_curve) > 1:
            yesterday_capital = self.equity_curve[-2]['total_capital']
            today_capital = self.equity_curve[-1]['total_capital']
            if yesterday_capital > 0:
                daily_return = ((today_capital - yesterday_capital) / yesterday_capital) * 100

        return {
            'total_return': total_return_pct,
            'total_return_usd': total_return_usd,
            'daily_return': daily_return,
            'roi': total_return_pct,  # Same as total_return
        }

    def calculate_sharpe_ratio(self, risk_free_rate=0.02):
        """
        Calcola Sharpe Ratio del portfolio

        Args:
            risk_free_rate: Tasso risk-free annuale (default: 2%)

        Returns:
            float: Sharpe ratio
        """
        if len(self.daily_returns) < 2:
            return 0.0

        import numpy as np

        returns = np.array(self.daily_returns)
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        # Sharpe Ratio annualizzato (assumendo ~252 trading days)
        daily_risk_free = risk_free_rate / 252
        sharpe = (mean_return - daily_risk_free) / std_return * np.sqrt(252)

        return round(sharpe, 2)

    def add_daily_return(self, return_pct):
        """
        Aggiunge return giornaliero allo storico

        Args:
            return_pct: Return percentuale del giorno
        """
        self.daily_returns.append(return_pct)
        logger.debug(f"Daily return aggiunto: {return_pct:.2f}%")

    # ========================================================================
    # DEPOSITS & WITHDRAWALS
    # ========================================================================

    def deposit(self, amount):
        """
        Deposita capitale aggiuntivo

        Args:
            amount: Importo da depositare ($)
        """
        self.current_capital += amount
        self.available_capital += amount
        self.total_deposits += amount

        logger.info(f"💰 Deposito: ${amount:.2f} | Nuovo capitale: ${self.current_capital:.2f}")

    def withdraw(self, amount):
        """
        Preleva capitale

        Args:
            amount: Importo da prelevare ($)

        Returns:
            bool: True se withdrawal riuscito
        """
        if amount > self.available_capital:
            logger.error(
                f"Withdrawal fallito: richiesto ${amount:.2f} "
                f"ma disponibile solo ${self.available_capital:.2f}"
            )
            return False

        self.current_capital -= amount
        self.available_capital -= amount
        self.total_withdrawals += amount

        logger.info(f"💸 Prelievo: ${amount:.2f} | Capitale rimanente: ${self.current_capital:.2f}")
        return True

    def add_fees(self, fee_amount):
        """
        Registra commissioni pagate

        Args:
            fee_amount: Importo commissioni ($)
        """
        self.total_fees += fee_amount
        logger.debug(f"Fee aggiunta: ${fee_amount:.2f} | Total fees: ${self.total_fees:.2f}")

    # ========================================================================
    # REPORTING
    # ========================================================================

    def get_portfolio_summary(self, positions):
        """
        Genera summary completo del portfolio

        Args:
            positions: Lista posizioni aperte

        Returns:
            dict: Portfolio summary
        """
        returns = self.calculate_returns()
        allocation = self.calculate_allocation(positions)
        diversification = self.check_diversification(positions)

        # Calcola unrealized PnL totale
        total_unrealized_pnl = sum(
            pos.get('unrealized_pnl', 0)
            for pos in positions
        )

        return {
            'capital': {
                'initial': self.initial_capital,
                'current': self.current_capital,
                'available': self.available_capital,
                'locked': self.locked_capital,
            },
            'returns': returns,
            'positions': {
                'count': len(positions),
                'allocation': allocation,
                'total_unrealized_pnl': total_unrealized_pnl,
            },
            'diversification': diversification,
            'fees': {
                'total_fees': self.total_fees,
                'deposits': self.total_deposits,
                'withdrawals': self.total_withdrawals,
            },
            'performance': {
                'sharpe_ratio': self.calculate_sharpe_ratio(),
                'num_data_points': len(self.equity_curve),
            }
        }

    def print_portfolio_summary(self, positions):
        """
        Stampa summary leggibile del portfolio

        Args:
            positions: Lista posizioni aperte
        """
        summary = self.get_portfolio_summary(positions)
        cap = summary['capital']
        ret = summary['returns']
        pos = summary['positions']
        div = summary['diversification']

        output = f"""
╔═══════════════════════════════════════════════════════════╗
║                  PORTFOLIO SUMMARY                        ║
╠═══════════════════════════════════════════════════════════╣
║ CAPITALE                                                  ║
║ Iniziale:               ${cap['initial']:>10.2f}                  ║
║ Corrente:               ${cap['current']:>10.2f}                  ║
║ Disponibile:            ${cap['available']:>10.2f}                  ║
║ Bloccato:               ${cap['locked']:>10.2f}                  ║
║                                                           ║
║ PERFORMANCE                                               ║
║ Total Return:           {ret['total_return']:>6.2f}% (${ret['total_return_usd']:>8.2f})      ║
║ Daily Return:           {ret['daily_return']:>6.2f}%                        ║
║ Sharpe Ratio:           {summary['performance']['sharpe_ratio']:>6.2f}                        ║
║                                                           ║
║ POSIZIONI                                                 ║
║ Aperte:                 {pos['count']:>3}                            ║
║ Unrealized PnL:         ${pos['total_unrealized_pnl']:>10.2f}                  ║
║ Concentration Risk:     {div['concentration_risk']:>6.2f}%                      ║
║                                                           ║
║ FEES & FLOWS                                              ║
║ Total Fees:             ${summary['fees']['total_fees']:>10.2f}                  ║
║ Total Deposits:         ${summary['fees']['deposits']:>10.2f}                  ║
║ Total Withdrawals:      ${summary['fees']['withdrawals']:>10.2f}                  ║
╚═══════════════════════════════════════════════════════════╝
        """

        if div['recommendations']:
            output += "\n\n📋 RACCOMANDAZIONI:\n"
            for i, rec in enumerate(div['recommendations'], 1):
                output += f"  {i}. {rec}\n"

        print(output)
        return output

    def save_equity_curve(self, filename='data/equity_curve.csv'):
        """
        Salva equity curve su file CSV

        Args:
            filename: Path del file
        """
        if not self.equity_curve:
            logger.warning("Equity curve vuota, niente da salvare")
            return

        import pandas as pd

        df = pd.DataFrame(self.equity_curve)
        df.to_csv(filename, index=False)
        logger.info(f"Equity curve salvata: {filename}")
