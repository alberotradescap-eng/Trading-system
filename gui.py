"""
Trading System GUI - Interfaccia grafica per gestire strategie e monitorare il trading
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import asyncio
from typing import Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import ACTIVE_STRATEGY, POSITION_SIZE_PCT, MAX_POSITIONS, TAKE_PROFIT_FINAL, STOP_LOSS_FINAL, CONFIG
from config.trading_rules import TradingRules, MeanReversionStrategy, TrendFollowingStrategy
from main import TradingSystem


class TradingGUI:
    """Interfaccia grafica principale per il sistema di trading"""

    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Trading System - Dashboard")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e2e')

        # Trading system instance
        self.trading_system: Optional[TradingSystem] = None
        self.trading_thread: Optional[threading.Thread] = None
        self.is_running = False

        # Strategy mapping
        self.strategy_map = {
            'TradingRules': TradingRules(),
            'MeanReversionStrategy': MeanReversionStrategy(),
            'TrendFollowingStrategy': TrendFollowingStrategy()
        }

        # Selected strategy
        self.selected_strategy = tk.StringVar(value=ACTIVE_STRATEGY.__class__.__name__)

        # Style configuration
        self.setup_styles()

        # Create main layout
        self.create_layout()

        # Start monitoring updates
        self.update_dashboard()

    def setup_styles(self):
        """Configura gli stili per la GUI"""
        style = ttk.Style()
        style.theme_use('clam')

        # Colors
        bg_dark = '#1e1e2e'
        bg_panel = '#2d2d44'
        fg_text = '#e0e0e0'
        accent_green = '#50fa7b'
        accent_red = '#ff5555'
        accent_blue = '#8be9fd'
        accent_yellow = '#f1fa8c'

        # Button styles
        style.configure('Start.TButton',
                       background=accent_green,
                       foreground='black',
                       borderwidth=0,
                       focuscolor='none',
                       padding=10,
                       font=('Arial', 12, 'bold'))
        style.map('Start.TButton',
                 background=[('active', '#3dd75d')])

        style.configure('Stop.TButton',
                       background=accent_red,
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=10,
                       font=('Arial', 12, 'bold'))
        style.map('Stop.TButton',
                 background=[('active', '#ff3333')])

        # Frame styles
        style.configure('Panel.TFrame', background=bg_panel)
        style.configure('Dark.TFrame', background=bg_dark)

        # Label styles
        style.configure('Title.TLabel',
                       background=bg_panel,
                       foreground=fg_text,
                       font=('Arial', 14, 'bold'))
        style.configure('Subtitle.TLabel',
                       background=bg_panel,
                       foreground=fg_text,
                       font=('Arial', 11))
        style.configure('Value.TLabel',
                       background=bg_panel,
                       foreground=accent_blue,
                       font=('Arial', 13, 'bold'))
        style.configure('Positive.TLabel',
                       background=bg_panel,
                       foreground=accent_green,
                       font=('Arial', 16, 'bold'))
        style.configure('Negative.TLabel',
                       background=bg_panel,
                       foreground=accent_red,
                       font=('Arial', 16, 'bold'))

        # Radiobutton style
        style.configure('Strategy.TRadiobutton',
                       background=bg_panel,
                       foreground=fg_text,
                       font=('Arial', 11))

    def create_layout(self):
        """Crea il layout principale della GUI"""
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top section - Strategy Selection & Controls
        top_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # Left: Strategy Selection
        self.create_strategy_panel(top_frame)

        # Right: Trading Controls
        self.create_control_panel(top_frame)

        # Middle section - System Status
        self.create_status_panel(main_frame)

        # Bottom section - Monitoring Dashboard
        self.create_monitoring_panel(main_frame)

    def create_strategy_panel(self, parent):
        """Pannello di selezione strategia"""
        panel = ttk.LabelFrame(parent, text="  STRATEGIA  ", style='Panel.TFrame')
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Title
        title = ttk.Label(panel, text="Seleziona Strategia di Trading", style='Title.TLabel')
        title.pack(pady=10)

        # Strategy options
        strategies = [
            ("RSI + MACD Strategy", "TradingRules",
             "Entry: RSI<30 + MACD bullish | Exit: TP 2% / SL 1%"),
            ("Mean Reversion Strategy", "MeanReversionStrategy",
             "Entry: Bollinger extremes + RSI | Exit: Mean reversion"),
            ("Trend Following Strategy", "TrendFollowingStrategy",
             "Entry: SMA alignment | Exit: TP 5% / SL 2%")
        ]

        for display_name, value, description in strategies:
            frame = ttk.Frame(panel, style='Panel.TFrame')
            frame.pack(fill=tk.X, padx=20, pady=5)

            rb = ttk.Radiobutton(
                frame,
                text=display_name,
                variable=self.selected_strategy,
                value=value,
                style='Strategy.TRadiobutton',
                command=self.on_strategy_changed
            )
            rb.pack(anchor=tk.W)

            desc = ttk.Label(frame, text=f"   → {description}",
                           style='Subtitle.TLabel', foreground='#a0a0a0')
            desc.pack(anchor=tk.W, padx=20)

    def create_control_panel(self, parent):
        """Pannello di controllo trading"""
        panel = ttk.LabelFrame(parent, text="  CONTROLLI  ", style='Panel.TFrame')
        panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Title
        title = ttk.Label(panel, text="Controllo Sistema", style='Title.TLabel')
        title.pack(pady=10)

        # Status indicator
        status_frame = ttk.Frame(panel, style='Panel.TFrame')
        status_frame.pack(pady=10)

        ttk.Label(status_frame, text="Status:", style='Subtitle.TLabel').pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(status_frame, text="FERMO", style='Negative.TLabel')
        self.status_label.pack(side=tk.LEFT)

        # Control buttons
        button_frame = ttk.Frame(panel, style='Panel.TFrame')
        button_frame.pack(pady=20)

        self.start_button = ttk.Button(
            button_frame,
            text="▶ AVVIA TRADING",
            style='Start.TButton',
            command=self.start_trading,
            width=20
        )
        self.start_button.pack(pady=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="⬛ FERMA TRADING",
            style='Stop.TButton',
            command=self.stop_trading,
            state=tk.DISABLED,
            width=20
        )
        self.stop_button.pack(pady=5)

        # Settings info
        info_frame = ttk.Frame(panel, style='Panel.TFrame')
        info_frame.pack(pady=10, padx=20, fill=tk.X)

        settings_info = [
            f"Position Size: {POSITION_SIZE_PCT}%",
            f"Max Positions: {MAX_POSITIONS}",
            f"Daily TP: ${TAKE_PROFIT_FINAL}",
            f"Daily SL: ${STOP_LOSS_FINAL}"
        ]

        for info in settings_info:
            lbl = ttk.Label(info_frame, text=f"• {info}", style='Subtitle.TLabel', foreground='#8be9fd')
            lbl.pack(anchor=tk.W)

    def create_status_panel(self, parent):
        """Pannello stato sistema"""
        panel = ttk.LabelFrame(parent, text="  STATO SISTEMA  ", style='Panel.TFrame')
        panel.pack(fill=tk.X, pady=(0, 10))

        status_container = ttk.Frame(panel, style='Panel.TFrame')
        status_container.pack(fill=tk.X, padx=20, pady=15)

        # Create 4 status boxes
        self.create_status_box(status_container, "PnL GIORNALIERO", "$0.00", "pnl", 0)
        self.create_status_box(status_container, "POSIZIONI APERTE", "0", "positions", 1)
        self.create_status_box(status_container, "TRADE OGGI", "0", "trades", 2)
        self.create_status_box(status_container, "WIN RATE", "0%", "winrate", 3)

    def create_status_box(self, parent, title, initial_value, var_name, column):
        """Crea un box di stato"""
        box = ttk.Frame(parent, style='Panel.TFrame', relief=tk.RIDGE, borderwidth=2)
        box.grid(row=0, column=column, padx=10, pady=5, sticky='nsew')
        parent.columnconfigure(column, weight=1)

        ttk.Label(box, text=title, style='Subtitle.TLabel',
                 foreground='#a0a0a0').pack(pady=(10, 5))

        value_label = ttk.Label(box, text=initial_value, style='Value.TLabel')
        value_label.pack(pady=(0, 10))

        # Store reference
        setattr(self, f"{var_name}_value", value_label)

    def create_monitoring_panel(self, parent):
        """Pannello di monitoraggio dettagliato"""
        panel = ttk.LabelFrame(parent, text="  MONITORING  ", style='Panel.TFrame')
        panel.pack(fill=tk.BOTH, expand=True)

        # Create notebook for tabs
        notebook = ttk.Notebook(panel)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Positions tab
        positions_frame = ttk.Frame(notebook, style='Panel.TFrame')
        notebook.add(positions_frame, text='Posizioni Aperte')
        self.create_positions_table(positions_frame)

        # Trades history tab
        trades_frame = ttk.Frame(notebook, style='Panel.TFrame')
        notebook.add(trades_frame, text='Storico Trade')
        self.create_trades_table(trades_frame)

        # Logs tab
        logs_frame = ttk.Frame(notebook, style='Panel.TFrame')
        notebook.add(logs_frame, text='Log Sistema')
        self.create_logs_view(logs_frame)

    def create_positions_table(self, parent):
        """Tabella posizioni aperte"""
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview
        columns = ('Symbol', 'Side', 'Entry Price', 'Current Price', 'Quantity', 'PnL', 'PnL %', 'Duration')
        self.positions_tree = ttk.Treeview(parent, columns=columns, show='headings',
                                          yscrollcommand=scrollbar.set)

        for col in columns:
            self.positions_tree.heading(col, text=col)
            self.positions_tree.column(col, width=120, anchor=tk.CENTER)

        self.positions_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.positions_tree.yview)

    def create_trades_table(self, parent):
        """Tabella storico trade"""
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview
        columns = ('Timestamp', 'Symbol', 'Side', 'Entry', 'Exit', 'Quantity', 'PnL', 'PnL %', 'Duration')
        self.trades_tree = ttk.Treeview(parent, columns=columns, show='headings',
                                       yscrollcommand=scrollbar.set)

        for col in columns:
            self.trades_tree.heading(col, text=col)
            self.trades_tree.column(col, width=110, anchor=tk.CENTER)

        self.trades_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.trades_tree.yview)

    def create_logs_view(self, parent):
        """Vista log sistema"""
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Text widget
        self.logs_text = tk.Text(parent, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                                bg='#1e1e2e', fg='#e0e0e0', font=('Courier', 10))
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.logs_text.yview)

        # Initial message
        self.add_log("Sistema pronto. Seleziona una strategia e avvia il trading.")

    def add_log(self, message):
        """Aggiunge un messaggio al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.logs_text.see(tk.END)

    def on_strategy_changed(self):
        """Callback quando cambia la strategia selezionata"""
        strategy = self.selected_strategy.get()
        self.add_log(f"Strategia selezionata: {strategy}")

    def start_trading(self):
        """Avvia il sistema di trading"""
        if self.is_running:
            messagebox.showwarning("Attenzione", "Il trading è già attivo!")
            return

        strategy = self.selected_strategy.get()

        # Confirm
        confirm = messagebox.askyesno(
            "Conferma Avvio",
            f"Vuoi avviare il trading con la strategia:\n{strategy}\n\nIl sistema inizierà a fare trading reale!"
        )

        if not confirm:
            return

        # Update UI
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="ATTIVO", style='Positive.TLabel')

        self.add_log(f"Avvio trading con strategia: {strategy}")
        self.add_log("Connessione a Binance in corso...")

        # Start trading in separate thread
        self.trading_thread = threading.Thread(target=self.run_trading_system, daemon=True)
        self.trading_thread.start()

    def run_trading_system(self):
        """Esegue il sistema di trading in un thread separato"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Initialize trading system
            self.trading_system = TradingSystem(CONFIG)

            # Set selected strategy
            strategy_name = self.selected_strategy.get()
            if strategy_name in self.strategy_map:
                self.trading_system.strategy = self.strategy_map[strategy_name]
                self.root.after(0, self.add_log, f"Strategia impostata: {self.trading_system.strategy.name}")

            self.root.after(0, self.add_log, "Sistema di trading inizializzato")
            self.root.after(0, self.add_log, "Avvio streaming dati da Binance...")

            # Run the trading system
            loop.run_until_complete(self.trading_system.run_live())

        except Exception as e:
            error_msg = f"ERRORE: {str(e)}"
            self.root.after(0, self.add_log, error_msg)
            self.root.after(0, messagebox.showerror, "Errore Sistema", error_msg)
            self.root.after(0, self.stop_trading_internal)

    def stop_trading(self):
        """Ferma il sistema di trading"""
        if not self.is_running:
            messagebox.showwarning("Attenzione", "Il trading non è attivo!")
            return

        confirm = messagebox.askyesno(
            "Conferma Stop",
            "Vuoi fermare il trading?\n\nLe posizioni aperte rimarranno attive."
        )

        if not confirm:
            return

        self.add_log("Arresto sistema in corso...")

        # Stop trading system
        if self.trading_system:
            try:
                asyncio.run(self.trading_system.shutdown())
            except Exception as e:
                self.add_log(f"Errore durante shutdown: {str(e)}")

        self.stop_trading_internal()

    def stop_trading_internal(self):
        """Ferma il trading (uso interno)"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="FERMO", style='Negative.TLabel')
        self.add_log("Sistema fermato")

    def update_dashboard(self):
        """Aggiorna periodicamente il dashboard"""
        if self.is_running and self.trading_system:
            try:
                # Update PnL
                daily_pnl = getattr(self.trading_system, 'daily_pnl', 0.0)
                pnl_text = f"${daily_pnl:.2f}"
                self.pnl_value.config(text=pnl_text)

                # Change color based on PnL
                if daily_pnl > 0:
                    self.pnl_value.config(style='Positive.TLabel')
                elif daily_pnl < 0:
                    self.pnl_value.config(style='Negative.TLabel')
                else:
                    self.pnl_value.config(style='Value.TLabel')

                # Update positions count
                positions = getattr(self.trading_system, 'positions', [])
                self.positions_value.config(text=str(len(positions)))

                # Update trades count
                trades_today = getattr(self.trading_system, 'trades_today', 0)
                self.trades_value.config(text=str(trades_today))

                # Update positions table
                self.update_positions_table(positions)

            except Exception as e:
                self.add_log(f"Errore aggiornamento dashboard: {str(e)}")

        # Schedule next update (every 1 second)
        self.root.after(1000, self.update_dashboard)

    def update_positions_table(self, positions):
        """Aggiorna la tabella delle posizioni"""
        # Clear existing items
        for item in self.positions_tree.get_children():
            self.positions_tree.delete(item)

        # Add current positions
        for pos in positions:
            symbol = pos.get('symbol', 'N/A')
            side = pos.get('side', 'N/A')
            entry_price = pos.get('entry_price', 0.0)
            current_price = pos.get('current_price', 0.0)
            quantity = pos.get('quantity', 0.0)
            pnl = pos.get('pnl', 0.0)
            pnl_pct = pos.get('pnl_pct', 0.0)
            duration = pos.get('duration', 'N/A')

            values = (
                symbol,
                side,
                f"${entry_price:.2f}",
                f"${current_price:.2f}",
                f"{quantity:.4f}",
                f"${pnl:.2f}",
                f"{pnl_pct:.2f}%",
                duration
            )

            self.positions_tree.insert('', tk.END, values=values)


def main():
    """Funzione principale per avviare la GUI"""
    root = tk.Tk()
    app = TradingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
