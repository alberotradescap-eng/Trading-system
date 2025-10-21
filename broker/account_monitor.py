"""
Account Monitor - Monitora account Binance

Tiene traccia di:
- Balance e variazioni
- Posizioni aperte
- Ordini aperti
- Trade history
- Performance metrics
"""

import asyncio
from datetime import datetime
from loguru import logger
from .binance_client import BinanceClient


class AccountMonitor:
    """
    Monitora lo stato dell'account Binance
    """

    def __init__(self, binance_client: BinanceClient, config):
        """
        Args:
            binance_client: Istanza BinanceClient
            config: Dictionary configurazione
        """
        self.client = binance_client
        self.config = config

        # State tracking
        self.current_balance = 0.0
        self.balance_history = []
        self.open_orders = []
        self.account_info = None
        self.last_update = None

        logger.info("AccountMonitor inizializzato")

    # ========================================================================
    # BALANCE MONITORING
    # ========================================================================

    async def update_balance(self, asset='USDT'):
        """
        Aggiorna balance dell'asset

        Args:
            asset: Asset da monitorare (default: USDT)

        Returns:
            dict: Balance info
        """
        balance = await self.client.get_account_balance(asset)

        if balance:
            self.current_balance = balance['total']

            # Aggiungi a history
            self.balance_history.append({
                'timestamp': datetime.now(),
                'asset': asset,
                'free': balance['free'],
                'locked': balance['locked'],
                'total': balance['total'],
            })

            self.last_update = datetime.now()

            logger.debug(f"Balance aggiornato: {asset} = ${balance['total']:.2f}")

            return balance

        return None

    def get_current_balance(self):
        """
        Ritorna balance corrente

        Returns:
            float: Balance corrente
        """
        return self.current_balance

    def get_balance_change(self, timeframe='1h'):
        """
        Calcola variazione balance in un timeframe

        Args:
            timeframe: '1h', '24h', '7d', etc.

        Returns:
            dict: {
                'change_usd': float,
                'change_pct': float,
                'from': float,
                'to': float
            }
        """
        if len(self.balance_history) < 2:
            return {
                'change_usd': 0,
                'change_pct': 0,
                'from': self.current_balance,
                'to': self.current_balance
            }

        # Per semplicità, compara con primo record
        # TODO: Implementare timeframe parsing (es. ultime 1h, 24h, etc.)
        first = self.balance_history[0]
        last = self.balance_history[-1]

        change_usd = last['total'] - first['total']
        change_pct = (change_usd / first['total'] * 100) if first['total'] > 0 else 0

        return {
            'change_usd': change_usd,
            'change_pct': change_pct,
            'from': first['total'],
            'to': last['total']
        }

    # ========================================================================
    # ACCOUNT INFO
    # ========================================================================

    async def update_account_info(self):
        """
        Aggiorna info complete dell'account

        Returns:
            dict: Account info
        """
        account = await self.client.get_account_info()

        if account:
            self.account_info = account
            self.last_update = datetime.now()

            # Estrai balances
            balances = {}
            for balance in account.get('balances', []):
                asset = balance['asset']
                total = float(balance['free']) + float(balance['locked'])
                if total > 0:  # Solo asset con balance > 0
                    balances[asset] = {
                        'free': float(balance['free']),
                        'locked': float(balance['locked']),
                        'total': total
                    }

            logger.debug(f"Account info aggiornato. {len(balances)} assets con balance > 0")

            return account

        return None

    def get_all_balances(self):
        """
        Ritorna tutti i balances (tutti gli assets)

        Returns:
            dict: {asset: balance_info}
        """
        if not self.account_info:
            return {}

        balances = {}
        for balance in self.account_info.get('balances', []):
            asset = balance['asset']
            total = float(balance['free']) + float(balance['locked'])
            if total > 0:
                balances[asset] = {
                    'free': float(balance['free']),
                    'locked': float(balance['locked']),
                    'total': total
                }

        return balances

    # ========================================================================
    # OPEN ORDERS MONITORING
    # ========================================================================

    async def update_open_orders(self, symbol=None):
        """
        Aggiorna lista ordini aperti

        Args:
            symbol: Filtra per simbolo (opzionale)

        Returns:
            list: Ordini aperti
        """
        orders = await self.client.get_open_orders(symbol)

        if orders is not None:
            self.open_orders = orders
            logger.debug(f"Ordini aperti aggiornati: {len(orders)} ordini")
            return orders

        return []

    def get_open_orders(self, symbol=None):
        """
        Ritorna ordini aperti

        Args:
            symbol: Filtra per simbolo (opzionale)

        Returns:
            list: Ordini aperti
        """
        if symbol:
            return [o for o in self.open_orders if o['symbol'] == symbol]

        return self.open_orders

    def count_open_orders(self, symbol=None):
        """
        Conta ordini aperti

        Args:
            symbol: Filtra per simbolo (opzionale)

        Returns:
            int: Numero ordini aperti
        """
        return len(self.get_open_orders(symbol))

    # ========================================================================
    # MONITORING LOOP
    # ========================================================================

    async def start_monitoring(self, interval=60, asset='USDT'):
        """
        Avvia loop di monitoring continuo

        Args:
            interval: Intervallo aggiornamenti in secondi
            asset: Asset da monitorare per balance

        """
        logger.info(f"Avvio monitoring loop (interval: {interval}s)")

        while True:
            try:
                # Aggiorna balance
                await self.update_balance(asset)

                # Aggiorna account info
                await self.update_account_info()

                # Aggiorna open orders
                await self.update_open_orders()

                # Sleep
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Errore nel monitoring loop: {e}")
                await asyncio.sleep(interval)

    # ========================================================================
    # REPORTING
    # ========================================================================

    def get_account_summary(self):
        """
        Genera summary dell'account

        Returns:
            dict: Account summary
        """
        balances = self.get_all_balances()
        balance_change = self.get_balance_change()

        # Calcola valore totale in USDT (semplificato)
        total_value_usdt = sum(
            bal['total'] for asset, bal in balances.items()
            if asset == 'USDT'
        )

        return {
            'last_update': self.last_update,
            'usdt_balance': self.current_balance,
            'balance_change': balance_change,
            'all_balances': balances,
            'total_value_usdt': total_value_usdt,
            'open_orders_count': len(self.open_orders),
        }

    def print_account_summary(self):
        """Stampa summary dell'account"""
        summary = self.get_account_summary()

        last_update_str = summary['last_update'].strftime('%Y-%m-%d %H:%M:%S') if summary['last_update'] else 'N/A'

        output = f"""
╔═══════════════════════════════════════════════════════════╗
║                   ACCOUNT SUMMARY                         ║
╠═══════════════════════════════════════════════════════════╣
║ Last Update:            {last_update_str}            ║
║                                                           ║
║ USDT Balance:           ${summary['usdt_balance']:>10.2f}                  ║
║ Balance Change:         ${summary['balance_change']['change_usd']:>10.2f} ({summary['balance_change']['change_pct']:>+6.2f}%)   ║
║                                                           ║
║ Total Value (USDT):     ${summary['total_value_usdt']:>10.2f}                  ║
║ Open Orders:            {summary['open_orders_count']:>5}                         ║
║                                                           ║
║ ASSETS WITH BALANCE:                                      ║
        """

        # Aggiungi balances per ogni asset
        for asset, balance in summary['all_balances'].items():
            output += f"║   {asset:>6}: {balance['total']:>12.8f} (free: {balance['free']:>10.8f})  ║\n"

        output += "╚═══════════════════════════════════════════════════════════╝"

        print(output)
        return output

    # ========================================================================
    # ALERTS & NOTIFICATIONS
    # ========================================================================

    def check_balance_alert(self, min_balance=100):
        """
        Controlla se balance è sotto soglia minima

        Args:
            min_balance: Balance minimo (USDT)

        Returns:
            bool: True se sotto soglia
        """
        if self.current_balance < min_balance:
            logger.warning(
                f"⚠️ Balance sotto soglia minima! "
                f"Current: ${self.current_balance:.2f} | Min: ${min_balance:.2f}"
            )
            return True

        return False

    def check_rapid_balance_change(self, threshold_pct=10):
        """
        Rileva variazioni rapide di balance

        Args:
            threshold_pct: Soglia % per alert

        Returns:
            bool: True se variazione rapida rilevata
        """
        change = self.get_balance_change()

        if abs(change['change_pct']) >= threshold_pct:
            logger.warning(
                f"⚠️ Variazione rapida balance rilevata: {change['change_pct']:+.2f}%"
            )
            return True

        return False

    # ========================================================================
    # DIAGNOSTICS
    # ========================================================================

    async def run_diagnostics(self):
        """
        Esegue diagnostics sull'account

        Returns:
            dict: Risultati diagnostics
        """
        logger.info("Eseguendo diagnostics account...")

        diagnostics = {
            'timestamp': datetime.now(),
            'tests': {}
        }

        # Test 1: Connessione API
        try:
            await self.update_account_info()
            diagnostics['tests']['api_connection'] = 'OK'
        except Exception as e:
            diagnostics['tests']['api_connection'] = f'FAILED: {e}'

        # Test 2: Balance disponibile
        await self.update_balance()
        if self.current_balance > 0:
            diagnostics['tests']['balance_check'] = f'OK (${self.current_balance:.2f})'
        else:
            diagnostics['tests']['balance_check'] = 'WARNING: Balance is 0'

        # Test 3: Open orders
        await self.update_open_orders()
        diagnostics['tests']['open_orders'] = f'{len(self.open_orders)} open orders'

        # Test 4: Account permissions
        if self.account_info:
            can_trade = self.account_info.get('canTrade', False)
            can_withdraw = self.account_info.get('canWithdraw', False)
            can_deposit = self.account_info.get('canDeposit', False)

            diagnostics['tests']['permissions'] = {
                'can_trade': can_trade,
                'can_withdraw': can_withdraw,
                'can_deposit': can_deposit
            }

        logger.info(f"Diagnostics completato: {diagnostics}")
        return diagnostics

    def print_diagnostics(self, diagnostics):
        """
        Stampa risultati diagnostics

        Args:
            diagnostics: Dict da run_diagnostics()
        """
        output = f"""
╔═══════════════════════════════════════════════════════════╗
║                ACCOUNT DIAGNOSTICS                        ║
╠═══════════════════════════════════════════════════════════╣
║ Timestamp: {diagnostics['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}          ║
║                                                           ║
        """

        for test_name, result in diagnostics['tests'].items():
            if isinstance(result, dict):
                output += f"║ {test_name}:\n"
                for k, v in result.items():
                    output += f"║   {k}: {v}\n"
            else:
                output += f"║ {test_name}: {result}\n"

        output += "╚═══════════════════════════════════════════════════════════╝"

        print(output)
        return output
