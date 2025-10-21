"""
Risk Manager - Gestione del rischio

Calcola position sizing, valida trade prima dell'esecuzione,
monitora drawdown e gestisce il rischio complessivo del portfolio.
"""

from loguru import logger


class RiskManager:
    """
    Gestisce tutti gli aspetti di risk management
    """

    def __init__(self, config, account_balance):
        """
        Args:
            config: Dictionary con configurazione trading
            account_balance: Capitale disponibile ($)
        """
        self.config = config
        self.initial_balance = account_balance
        self.current_balance = account_balance
        self.peak_balance = account_balance
        self.current_drawdown = 0.0
        self.max_drawdown_reached = 0.0

        logger.info(f"RiskManager inizializzato con capitale: ${account_balance:.2f}")

    # ========================================================================
    # POSITION SIZING
    # ========================================================================

    def calculate_position_size(self, symbol, signal_price, account_balance=None):
        """
        Calcola la size della posizione in base al risk management

        Args:
            symbol: Simbolo da tradare
            signal_price: Prezzo del segnale
            account_balance: Capitale disponibile (opzionale)

        Returns:
            dict: {
                'quantity': float,  # Quantità da acquistare
                'position_value': float,  # Valore totale posizione ($)
                'risk_amount': float,  # Quanto rischiamo su questo trade ($)
            }
        """
        if account_balance is None:
            account_balance = self.current_balance

        # Size come % del capitale
        position_size_pct = self.config['trading'].get('position_size_pct', 2.0)
        position_value = account_balance * (position_size_pct / 100)

        # Controlla size minimo
        min_trade_size = self.config['trading'].get('min_trade_size_usdt', 10)
        if position_value < min_trade_size:
            logger.warning(f"Position value ${position_value:.2f} sotto il minimo ${min_trade_size}")
            position_value = min_trade_size

        # Calcola quantity
        quantity = position_value / signal_price

        # Calcola rischio (in base allo stop loss %)
        stop_loss_pct = self.config['trading'].get('stop_loss_pct', 1.0)
        risk_amount = position_value * (stop_loss_pct / 100)

        return {
            'quantity': quantity,
            'position_value': position_value,
            'risk_amount': risk_amount,
        }

    def calculate_position_size_with_atr(self, symbol, signal_price, atr, account_balance=None):
        """
        Calcola position size usando ATR (volatilità)

        Quando la volatilità è alta, riduciamo la size per limitare il rischio.

        Args:
            symbol: Simbolo
            signal_price: Prezzo
            atr: Average True Range (volatilità)
            account_balance: Capitale

        Returns:
            dict: Position sizing info
        """
        if account_balance is None:
            account_balance = self.current_balance

        # Risk per trade (% del capitale)
        risk_per_trade_pct = self.config['trading'].get('risk_per_trade_pct', 1.0)
        risk_amount = account_balance * (risk_per_trade_pct / 100)

        # Stop loss in termini di ATR (es. 2 x ATR)
        atr_multiplier = 2.0
        stop_loss_distance = atr * atr_multiplier

        # Calcola quantity in base al rischio
        # Risk = Quantity * Stop Loss Distance
        # Quindi: Quantity = Risk / Stop Loss Distance
        quantity = risk_amount / stop_loss_distance

        position_value = quantity * signal_price

        # Controlla se va oltre il max position size
        max_position_pct = self.config['trading'].get('position_size_pct', 2.0)
        max_position_value = account_balance * (max_position_pct / 100)

        if position_value > max_position_value:
            # Riduci quantity
            quantity = max_position_value / signal_price
            position_value = max_position_value

        return {
            'quantity': quantity,
            'position_value': position_value,
            'risk_amount': risk_amount,
            'stop_loss_distance': stop_loss_distance,
        }

    # ========================================================================
    # VALIDAZIONE TRADE
    # ========================================================================

    def validate_trade(self, signal, account_balance, open_positions):
        """
        Valida se un trade può essere eseguito in base a regole di risk management

        Args:
            signal: Dictionary con segnale
            account_balance: Capitale disponibile
            open_positions: Lista posizioni aperte

        Returns:
            tuple: (is_valid: bool, reason: str, sizing_info: dict)
        """
        # 1. Controlla drawdown massimo
        max_drawdown_pct = self.config['trading'].get('max_drawdown_pct', 10)
        if self.current_drawdown >= max_drawdown_pct:
            return False, f'max_drawdown_exceeded_{self.current_drawdown:.1f}%', None

        # 2. Controlla balance sufficiente
        min_balance_required = self.config['trading'].get('min_trade_size_usdt', 10)
        if account_balance < min_balance_required:
            return False, 'insufficient_balance', None

        # 3. Calcola position sizing
        sizing = self.calculate_position_size(
            signal['symbol'],
            signal['price'],
            account_balance
        )

        # 4. Controlla se position value supera il balance disponibile
        if sizing['position_value'] > account_balance:
            return False, 'position_value_exceeds_balance', None

        # 5. Controlla esposizione totale (somma di tutte le posizioni aperte)
        total_exposure = sum(
            pos.get('entry_price', 0) * pos.get('quantity', 0)
            for pos in open_positions
        )
        total_exposure += sizing['position_value']

        max_total_exposure_pct = 50  # Max 50% del capitale esposto
        max_exposure = account_balance * (max_total_exposure_pct / 100)

        if total_exposure > max_exposure:
            return False, 'max_exposure_exceeded', None

        # 6. Controlla correlazione (evita aprire troppe posizioni correlate)
        # TODO: Implementare controllo correlazione tra assets

        # Trade valido
        return True, 'ok', sizing

    # ========================================================================
    # DRAWDOWN MANAGEMENT
    # ========================================================================

    def update_balance(self, new_balance):
        """
        Aggiorna balance e calcola drawdown

        Args:
            new_balance: Nuovo capitale totale
        """
        self.current_balance = new_balance

        # Aggiorna peak
        if new_balance > self.peak_balance:
            self.peak_balance = new_balance

        # Calcola drawdown corrente
        if self.peak_balance > 0:
            self.current_drawdown = ((self.peak_balance - new_balance) / self.peak_balance) * 100

            # Aggiorna max drawdown raggiunto
            if self.current_drawdown > self.max_drawdown_reached:
                self.max_drawdown_reached = self.current_drawdown

        logger.debug(f"Balance aggiornato: ${new_balance:.2f} | Drawdown: {self.current_drawdown:.2f}%")

    def check_drawdown_limit(self):
        """
        Controlla se il drawdown ha superato il limite

        Returns:
            bool: True se drawdown superato
        """
        max_drawdown_pct = self.config['trading'].get('max_drawdown_pct', 10)

        if self.current_drawdown >= max_drawdown_pct:
            logger.warning(f"⚠️ Max drawdown raggiunto: {self.current_drawdown:.2f}%")
            return True

        return False

    def reset_drawdown(self):
        """Reset drawdown (da chiamare dopo recovery o inizio nuova giornata)"""
        self.peak_balance = self.current_balance
        self.current_drawdown = 0.0
        logger.info("Drawdown reset")

    # ========================================================================
    # RISK METRICS
    # ========================================================================

    def calculate_risk_metrics(self, positions):
        """
        Calcola metriche di rischio del portfolio

        Args:
            positions: Lista posizioni aperte

        Returns:
            dict: Metriche di rischio
        """
        if not positions:
            return {
                'total_exposure': 0,
                'total_risk': 0,
                'exposure_pct': 0,
                'risk_pct': 0,
                'largest_position_pct': 0,
                'avg_position_size': 0,
            }

        # Calcola esposizione totale
        total_exposure = sum(
            pos.get('entry_price', 0) * pos.get('quantity', 0)
            for pos in positions
        )

        # Calcola rischio totale (somma degli SL possibili)
        total_risk = 0
        for pos in positions:
            entry_value = pos.get('entry_price', 0) * pos.get('quantity', 0)
            sl_pct = pos.get('stop_loss_pct', 1.0)
            risk = entry_value * (sl_pct / 100)
            total_risk += risk

        # Trova posizione più grande
        position_values = [
            pos.get('entry_price', 0) * pos.get('quantity', 0)
            for pos in positions
        ]
        largest_position = max(position_values) if position_values else 0

        return {
            'total_exposure': total_exposure,
            'total_risk': total_risk,
            'exposure_pct': (total_exposure / self.current_balance * 100) if self.current_balance > 0 else 0,
            'risk_pct': (total_risk / self.current_balance * 100) if self.current_balance > 0 else 0,
            'largest_position_pct': (largest_position / self.current_balance * 100) if self.current_balance > 0 else 0,
            'avg_position_size': total_exposure / len(positions) if positions else 0,
            'num_positions': len(positions),
        }

    def get_risk_summary(self, positions):
        """
        Genera summary leggibile delle metriche di rischio

        Args:
            positions: Lista posizioni aperte

        Returns:
            str: Summary formattato
        """
        metrics = self.calculate_risk_metrics(positions)

        summary = f"""
╔═══════════════════════════════════════════════════════════╗
║                    RISK SUMMARY                           ║
╠═══════════════════════════════════════════════════════════╣
║ Current Balance:        ${self.current_balance:>10.2f}                  ║
║ Peak Balance:           ${self.peak_balance:>10.2f}                  ║
║ Current Drawdown:       {self.current_drawdown:>6.2f}%                      ║
║ Max Drawdown Reached:   {self.max_drawdown_reached:>6.2f}%                      ║
║                                                           ║
║ Total Exposure:         ${metrics['total_exposure']:>10.2f} ({metrics['exposure_pct']:>5.1f}%)        ║
║ Total Risk:             ${metrics['total_risk']:>10.2f} ({metrics['risk_pct']:>5.1f}%)        ║
║ Num Positions:          {metrics['num_positions']:>3}                            ║
║ Avg Position Size:      ${metrics['avg_position_size']:>10.2f}                  ║
║ Largest Position:       {metrics['largest_position_pct']:>6.2f}%                      ║
╚═══════════════════════════════════════════════════════════╝
        """
        return summary.strip()

    def print_risk_summary(self, positions):
        """Stampa risk summary"""
        summary = self.get_risk_summary(positions)
        print(summary)
        return summary

    # ========================================================================
    # VOLATILITY-BASED ADJUSTMENTS
    # ========================================================================

    def adjust_for_volatility(self, sizing_info, current_volatility, avg_volatility):
        """
        Aggiusta position size in base alla volatilità corrente

        Se volatilità è alta, riduciamo la size.
        Se volatilità è bassa, possiamo aumentarla (cautamente).

        Args:
            sizing_info: Dictionary da calculate_position_size()
            current_volatility: Volatilità corrente (es. ATR)
            avg_volatility: Volatilità media storica

        Returns:
            dict: Sizing info aggiustato
        """
        if not self.config['advanced'].get('volatility_adjustment', True):
            return sizing_info

        # Calcola ratio volatilità
        volatility_ratio = current_volatility / avg_volatility if avg_volatility > 0 else 1.0

        # Se volatilità > media, riduci size
        if volatility_ratio > 1.5:
            # Volatilità molto alta: riduci del 50%
            adjustment_factor = 0.5
            logger.info(f"Alta volatilità ({volatility_ratio:.2f}x): riduzione size del 50%")
        elif volatility_ratio > 1.2:
            # Volatilità alta: riduci del 25%
            adjustment_factor = 0.75
            logger.info(f"Volatilità elevata ({volatility_ratio:.2f}x): riduzione size del 25%")
        elif volatility_ratio < 0.7:
            # Volatilità bassa: aumenta del 20% (cautamente)
            adjustment_factor = 1.2
            logger.info(f"Bassa volatilità ({volatility_ratio:.2f}x): aumento size del 20%")
        else:
            # Volatilità normale
            adjustment_factor = 1.0

        # Applica aggiustamento
        adjusted_sizing = sizing_info.copy()
        adjusted_sizing['quantity'] *= adjustment_factor
        adjusted_sizing['position_value'] *= adjustment_factor

        return adjusted_sizing
