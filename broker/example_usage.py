"""
Esempio di utilizzo del Binance Broker con Safe Order Execution

Questo esempio mostra come:
1. Inizializzare il broker
2. Piazzare ordini market/limit con retry automatico
3. Gestire posizioni con Position Manager
4. Gestire errori di rete
5. Verificare stato ordini
"""
import asyncio
import logging
from binance_broker import BinanceBroker, OrderStatus
from position_manager import PositionManager, PositionSide

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_market_order():
    """Esempio: Ordine Market con retry automatico"""

    # Inizializza broker (usa TESTNET per sicurezza)
    broker = BinanceBroker(
        api_key="YOUR_API_KEY",
        api_secret="YOUR_API_SECRET",
        testnet=True  # IMPORTANTE: usa testnet per test!
    )

    await broker.initialize()

    try:
        # Piazza ordine MARKET
        logger.info("Piazzando ordine MARKET...")
        result = await broker.place_market_order(
            symbol="BTCUSDT",
            side="BUY",
            quantity=0.001
        )

        if result.success:
            logger.info(f"✓ Ordine eseguito con successo!")
            logger.info(f"  Order ID: {result.order_id}")
            logger.info(f"  Quantità eseguita: {result.executed_qty}")
            logger.info(f"  Prezzo medio: {result.avg_price}")
            logger.info(f"  Retry effettuati: {result.retry_count}")
        else:
            logger.error(f"✗ Ordine fallito: {result.error_message}")
            logger.error(f"  Status: {result.status}")
            logger.error(f"  Retry effettuati: {result.retry_count}")

    finally:
        await broker.close()


async def example_limit_order_with_retry():
    """Esempio: Ordine Limit con gestione retry"""

    broker = BinanceBroker(
        api_key="YOUR_API_KEY",
        api_secret="YOUR_API_SECRET",
        testnet=True
    )

    await broker.initialize()

    try:
        # Piazza ordine LIMIT
        logger.info("Piazzando ordine LIMIT...")
        result = await broker.place_limit_order(
            symbol="BTCUSDT",
            side="BUY",
            quantity=0.001,
            price=40000.0,  # Prezzo limite
            time_in_force="GTC"  # Good Till Cancel
        )

        if result.success:
            logger.info(f"✓ Ordine piazzato: {result.status}")

            # Attendi un po' e verifica stato
            await asyncio.sleep(5)

            status = await broker.executor.get_order_status(
                symbol="BTCUSDT",
                order_id=result.order_id
            )

            logger.info(f"Stato ordine: {status.status}")

            # Se non eseguito, cancella
            if status.status == OrderStatus.NEW:
                logger.info("Ordine non ancora eseguito, cancellazione...")
                await broker.executor.cancel_order("BTCUSDT", result.order_id)

        else:
            logger.error(f"✗ Ordine fallito: {result.error_message}")

    finally:
        await broker.close()


async def example_position_management():
    """Esempio: Gestione completa di una posizione con Position Manager"""

    broker = BinanceBroker(
        api_key="YOUR_API_KEY",
        api_secret="YOUR_API_SECRET",
        testnet=True
    )

    position_manager = PositionManager()

    await broker.initialize()

    try:
        symbol = "BTCUSDT"

        # ===== 1. APRI POSIZIONE LONG =====
        logger.info("=== APERTURA POSIZIONE LONG ===")

        # Piazza ordine di entrata
        entry_result = await broker.place_market_order(
            symbol=symbol,
            side="BUY",
            quantity=0.001
        )

        if not entry_result.success:
            logger.error(f"Fallito ingresso: {entry_result.error_message}")
            return

        # Registra posizione nel manager
        position = position_manager.open_position(
            symbol=symbol,
            side="LONG",
            entry_price=entry_result.avg_price,
            quantity=entry_result.executed_qty,
            entry_order_id=entry_result.order_id,
            strategy_name="Example Strategy"
        )

        logger.info(f"✓ Posizione aperta: {position.quantity} @ {position.entry_price}")

        # ===== 2. IMPOSTA STOP LOSS =====
        stop_price = position.entry_price * 0.98  # Stop al -2%

        logger.info(f"Impostando Stop Loss @ {stop_price}...")
        sl_result = await broker.place_stop_loss(
            symbol=symbol,
            side="SELL",
            quantity=position.quantity,
            stop_price=stop_price
        )

        if sl_result.success:
            position_manager.set_stop_loss(symbol, sl_result.order_id)
            logger.info(f"✓ Stop Loss impostato: Order ID {sl_result.order_id}")

        # ===== 3. SIMULA ATTESA E VERIFICA P&L =====
        logger.info("\n=== MONITORAGGIO POSIZIONE ===")

        # Simula prezzo corrente (in realtà dovresti recuperarlo da API)
        current_price = position.entry_price * 1.01  # Simula +1%

        unrealized_pnl = position.calculate_unrealized_pnl(current_price)
        unrealized_pnl_pct = position.calculate_unrealized_pnl_percentage(current_price)

        logger.info(f"Prezzo corrente: {current_price}")
        logger.info(f"P&L non realizzato: {unrealized_pnl:.2f} ({unrealized_pnl_pct:.2f}%)")

        # ===== 4. CHIUDI POSIZIONE =====
        logger.info("\n=== CHIUSURA POSIZIONE ===")

        exit_result = await broker.place_market_order(
            symbol=symbol,
            side="SELL",
            quantity=position.remaining_quantity
        )

        if exit_result.success:
            # Registra chiusura
            position_manager.close_position(
                symbol=symbol,
                exit_price=exit_result.avg_price,
                exit_order_id=exit_result.order_id
            )

            logger.info(f"✓ Posizione chiusa @ {exit_result.avg_price}")
            logger.info(f"P&L realizzato: {position.realized_pnl:.2f} "
                       f"({position.realized_pnl_percentage:.2f}%)")

        # ===== 5. STATISTICHE =====
        logger.info("\n" + position_manager.get_summary())

    finally:
        await broker.close()


async def example_partial_position_close():
    """Esempio: Chiusura parziale di posizione (scale out)"""

    broker = BinanceBroker(
        api_key="YOUR_API_KEY",
        api_secret="YOUR_API_SECRET",
        testnet=True
    )

    position_manager = PositionManager()

    await broker.initialize()

    try:
        symbol = "BTCUSDT"

        # Apri posizione
        entry_result = await broker.place_market_order(
            symbol=symbol,
            side="BUY",
            quantity=0.01  # Quantità maggiore per scale out
        )

        if not entry_result.success:
            return

        position = position_manager.open_position(
            symbol=symbol,
            side="LONG",
            entry_price=entry_result.avg_price,
            quantity=entry_result.executed_qty,
            entry_order_id=entry_result.order_id
        )

        logger.info(f"Posizione aperta: {position.quantity} @ {position.entry_price}")

        # ===== SCALA USCITA (SCALE OUT) =====

        # Primo take profit al +1%
        tp1_price = position.entry_price * 1.01
        tp1_qty = position.quantity * 0.5  # Chiudi 50%

        logger.info(f"\n=== TAKE PROFIT 1: Chiudo 50% @ {tp1_price} ===")

        # Simula che il prezzo raggiunge TP1
        exit1_result = await broker.place_market_order(
            symbol=symbol,
            side="SELL",
            quantity=tp1_qty
        )

        if exit1_result.success:
            pnl1 = position_manager.partial_close_position(
                symbol=symbol,
                quantity=tp1_qty,
                exit_price=exit1_result.avg_price
            )
            logger.info(f"✓ TP1 eseguito, P&L: {pnl1:.2f}")

        # Secondo take profit al +2%
        tp2_price = position.entry_price * 1.02

        logger.info(f"\n=== TAKE PROFIT 2: Chiudo restante @ {tp2_price} ===")

        exit2_result = await broker.place_market_order(
            symbol=symbol,
            side="SELL",
            quantity=position.remaining_quantity
        )

        if exit2_result.success:
            position_manager.close_position(
                symbol=symbol,
                exit_price=exit2_result.avg_price,
                exit_order_id=exit2_result.order_id
            )

            logger.info(f"✓ Posizione completamente chiusa")
            logger.info(f"P&L totale: {position.realized_pnl:.2f} "
                       f"({position.realized_pnl_percentage:.2f}%)")

    finally:
        await broker.close()


async def example_error_handling():
    """Esempio: Gestione errori di rete e retry"""

    broker = BinanceBroker(
        api_key="YOUR_API_KEY",
        api_secret="YOUR_API_SECRET",
        testnet=True
    )

    await broker.initialize()

    # Configura retry aggressivo
    broker.executor.max_retries = 5
    broker.executor.base_retry_delay = 2.0

    try:
        logger.info("=== TEST GESTIONE ERRORI ===")

        # Prova ordine che potrebbe fallire
        result = await broker.place_market_order(
            symbol="BTCUSDT",
            side="BUY",
            quantity=0.001
        )

        # Il sistema automaticamente:
        # 1. Tenta invio ordine
        # 2. Se fallisce per rete -> retry con exponential backoff
        # 3. Se fallisce per ordine duplicato -> verifica stato su Binance
        # 4. Se ordine esiste -> ritorna quello esistente (idempotency)
        # 5. Se tutti i retry falliscono -> ritorna result con success=False

        if result.success:
            logger.info(f"✓ Ordine completato dopo {result.retry_count} retry")
        else:
            logger.error(f"✗ Ordine fallito definitivamente")
            logger.error(f"  Errore: {result.error_message}")
            logger.error(f"  Retry effettuati: {result.retry_count}")
            logger.error(f"  Status finale: {result.status}")

    finally:
        await broker.close()


async def example_check_balance():
    """Esempio: Verifica saldo account prima di tradare"""

    broker = BinanceBroker(
        api_key="YOUR_API_KEY",
        api_secret="YOUR_API_SECRET",
        testnet=True
    )

    await broker.initialize()

    try:
        logger.info("=== VERIFICA SALDI ===")

        balances = await broker.get_account_balance()

        for asset, balance in balances.items():
            logger.info(f"{asset}: {balance}")

        # Verifica saldo sufficiente
        if 'USDT' in balances and balances['USDT'] > 100:
            logger.info("✓ Saldo sufficiente per tradare")

            # Procedi con ordine...
            result = await broker.place_market_order(
                symbol="BTCUSDT",
                side="BUY",
                quantity=0.001
            )
        else:
            logger.warning("⚠ Saldo insufficiente")

    finally:
        await broker.close()


# ===== MAIN =====

async def main():
    """Esegui tutti gli esempi"""

    logger.info("╔═══════════════════════════════════════════════════════╗")
    logger.info("║  BINANCE SAFE ORDER EXECUTION - ESEMPI DI UTILIZZO   ║")
    logger.info("╚═══════════════════════════════════════════════════════╝\n")

    # Decommenta l'esempio che vuoi eseguire:

    # await example_market_order()
    # await example_limit_order_with_retry()
    # await example_position_management()
    # await example_partial_position_close()
    # await example_error_handling()
    # await example_check_balance()

    logger.info("\n✓ Esempi completati")
    logger.info("\nNOTA: Ricordati di sostituire YOUR_API_KEY e YOUR_API_SECRET")
    logger.info("      con le tue credenziali Binance TESTNET per testare!")


if __name__ == "__main__":
    asyncio.run(main())
