"""Generate a developer guide PDF for the trading bot project using reportlab."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Preformatted,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib import colors


def generate():
    output_path = "/home/user/crypto-trading-bot-binance-futures-python-rsi-algorithmic-trading/Developer_Guide.pdf"
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=60,
        leftMargin=60,
        topMargin=60,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        "MainTitle", parent=styles["Title"], fontSize=28, spaceAfter=12,
        textColor=HexColor("#1a1a1a"),
    ))
    styles.add(ParagraphStyle(
        "SubTitle", parent=styles["Title"], fontSize=18, spaceAfter=10,
        textColor=HexColor("#555555"),
    ))
    styles.add(ParagraphStyle(
        "SectionTitle", parent=styles["Heading1"], fontSize=16, spaceAfter=10,
        spaceBefore=16, textColor=HexColor("#1e1e1e"),
    ))
    styles.add(ParagraphStyle(
        "SubSection", parent=styles["Heading2"], fontSize=13, spaceAfter=8,
        spaceBefore=10, textColor=HexColor("#333333"),
    ))
    styles.add(ParagraphStyle(
        "SubSubSection", parent=styles["Heading3"], fontSize=11, spaceAfter=6,
        spaceBefore=8, textColor=HexColor("#3c3c3c"),
    ))
    styles.add(ParagraphStyle(
        "BodyText2", parent=styles["Normal"], fontSize=10, spaceAfter=6,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        "BulletItem", parent=styles["Normal"], fontSize=10, spaceAfter=4,
        leftIndent=20, bulletIndent=10, leading=14,
    ))
    styles.add(ParagraphStyle(
        "CodeBlock", parent=styles["Code"], fontSize=8, spaceAfter=8,
        spaceBefore=4, backColor=HexColor("#f0f0f0"), leftIndent=10,
        rightIndent=10, leading=12,
    ))

    story = []

    # ── Title Page ──
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("Crypto Trading Bot", styles["MainTitle"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Binance Futures | RSI + MEV Prediction", styles["SubTitle"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Developer Guide", styles["SubTitle"]))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("<i>Version 1.0 | February 2026</i>", styles["BodyText2"]))
    story.append(PageBreak())

    # ── 1. Overview ──
    story.append(Paragraph("1. Project Overview", styles["SectionTitle"]))
    story.append(Paragraph(
        "This is a cryptocurrency algorithmic trading bot for Binance Futures. "
        "It uses two complementary signal sources:",
        styles["BodyText2"],
    ))
    story.append(Paragraph(
        "<bullet>&bull;</bullet> <b>RSI (Relative Strength Index)</b> - Technical momentum indicator on price data",
        styles["BulletItem"],
    ))
    story.append(Paragraph(
        "<bullet>&bull;</bullet> <b>MEV Prediction (Optional)</b> - Mempool monitoring for large pending DEX swaps",
        styles["BulletItem"],
    ))
    story.append(Paragraph(
        "The bot connects to Binance Futures API to execute trades, with support for "
        "dry-run/paper-trading mode, configurable risk management (stop-loss, take-profit, "
        "position sizing), and structured logging for audit trails.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 0.1 * inch))

    # ── 2. Architecture ──
    story.append(Paragraph("2. Architecture", styles["SectionTitle"]))
    story.append(Paragraph(
        "The project follows a modular architecture with clear separation of concerns:",
        styles["BodyText2"],
    ))
    story.append(Paragraph("Core Modules", styles["SubSubSection"]))
    for item in [
        "src/main.py - Entry point with signal handling and graceful shutdown",
        "src/bot.py - TradingBot class orchestrating the polling loop",
        "src/exchange.py - Binance Futures API client wrapper",
        "src/strategy.py - RSI and combined RSI+MEV signal evaluation",
        "src/indicators.py - RSI calculation from OHLCV data",
        "src/risk_manager.py - Position sizing, stop-loss, take-profit",
        "src/utils.py - Logging setup and rounding helpers",
    ]:
        story.append(Paragraph(f"<bullet>&bull;</bullet> {item}", styles["BulletItem"]))

    story.append(Paragraph("MEV Prediction Modules", styles["SubSubSection"]))
    for item in [
        "src/mempool_monitor.py - Connects to Ethereum/BSC node, monitors pending transactions",
        "src/mev_analyzer.py - Computes pressure score, whale detection, swap velocity",
        "src/dex_abis.py - DEX router addresses and ABI definitions",
        "src/token_price_cache.py - Cached token-to-USD price lookups",
    ]:
        story.append(Paragraph(f"<bullet>&bull;</bullet> {item}", styles["BulletItem"]))

    story.append(Paragraph("Configuration", styles["SubSubSection"]))
    story.append(Paragraph(
        "<bullet>&bull;</bullet> config/settings.py - All bot parameters loaded from environment variables",
        styles["BulletItem"],
    ))
    story.append(Paragraph(
        "<bullet>&bull;</bullet> .env.example - Template for required environment variables",
        styles["BulletItem"],
    ))

    # ── 3. Project Structure ──
    story.append(PageBreak())
    story.append(Paragraph("3. Project Structure", styles["SectionTitle"]))
    tree = """.
+-- config/
|   +-- settings.py            # Bot configuration
+-- src/
|   +-- __init__.py
|   +-- main.py                # Entry point
|   +-- bot.py                 # Trading loop
|   +-- exchange.py            # Binance API wrapper
|   +-- strategy.py            # RSI + MEV strategy
|   +-- indicators.py          # RSI calculation
|   +-- risk_manager.py        # Risk management
|   +-- utils.py               # Helpers
|   +-- mempool_monitor.py     # Mempool monitoring
|   +-- mev_analyzer.py        # MEV signal analysis
|   +-- dex_abis.py            # DEX ABIs & addresses
|   +-- token_price_cache.py   # Token price cache
+-- tests/
|   +-- test_indicators.py
|   +-- test_strategy.py
|   +-- test_strategy_mev.py
|   +-- test_risk_manager.py
|   +-- test_mev_analyzer.py
|   +-- test_mempool_monitor.py
|   +-- test_dex_abis.py
+-- logs/
+-- requirements.txt
+-- .env.example
+-- .gitignore"""
    story.append(Preformatted(tree, styles["CodeBlock"]))

    # ── 4. Setup Instructions ──
    story.append(Paragraph("4. Setup Instructions", styles["SectionTitle"]))
    story.append(Paragraph("Prerequisites", styles["SubSubSection"]))
    for item in [
        "Python 3.9 or higher",
        "pip package manager",
        "Binance API credentials (testnet recommended for development)",
        "(Optional) Ethereum/BSC node RPC URL for MEV monitoring",
    ]:
        story.append(Paragraph(f"<bullet>&bull;</bullet> {item}", styles["BulletItem"]))

    story.append(Paragraph("Installation", styles["SubSubSection"]))
    install_code = """# Clone the repository
git clone <repo-url>
cd crypto-trading-bot-binance-futures-python-rsi-algorithmic-trading

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your credentials"""
    story.append(Preformatted(install_code, styles["CodeBlock"]))

    story.append(Paragraph("Running the Bot", styles["SubSubSection"]))
    story.append(Preformatted("python -m src.main", styles["CodeBlock"]))
    story.append(Paragraph(
        "The bot starts in DRY_RUN mode by default (paper trading, no real orders).",
        styles["BodyText2"],
    ))

    # ── 5. Configuration ──
    story.append(PageBreak())
    story.append(Paragraph("5. Configuration Reference", styles["SectionTitle"]))

    story.append(Paragraph("Binance API", styles["SubSubSection"]))
    api_data = [
        ["Variable", "Description"],
        ["BINANCE_API_KEY", "Your Binance API key"],
        ["BINANCE_API_SECRET", "Your Binance API secret"],
        ["BINANCE_TESTNET", "Set 'true' for testnet (default: true)"],
    ]
    t = Table(api_data, colWidths=[2.5 * inch, 4 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#dddddd")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Trading Parameters", styles["SubSubSection"]))
    trading_data = [
        ["Parameter", "Default / Description"],
        ["SYMBOL", "BTCUSDT"],
        ["TIMEFRAME", "1h"],
        ["RSI_PERIOD", "14 candles"],
        ["RSI_OVERSOLD", "30 (buy signal threshold)"],
        ["RSI_OVERBOUGHT", "70 (sell signal threshold)"],
        ["LEVERAGE", "1x"],
        ["RISK_PER_TRADE_PCT", "1.0% of balance per trade"],
        ["STOP_LOSS_PCT", "2.0% from entry"],
        ["TAKE_PROFIT_PCT", "4.0% from entry"],
        ["MAX_OPEN_POSITIONS", "1"],
        ["POLL_INTERVAL_SECONDS", "60"],
        ["DRY_RUN", "True (paper trading mode)"],
    ]
    t = Table(trading_data, colWidths=[2.5 * inch, 4 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#dddddd")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("MEV Monitoring (Optional)", styles["SubSubSection"]))
    mev_data = [
        ["Variable", "Default / Description"],
        ["MEV_ENABLED", "false (master toggle)"],
        ["MEV_CHAIN", "ethereum (or 'bsc')"],
        ["MEV_RPC_URL", "WebSocket or HTTP RPC endpoint"],
        ["MEV_MIN_SWAP_VALUE_USD", "50000 (min swap to track)"],
        ["MEV_WHALE_THRESHOLD_USD", "500000 (whale alert level)"],
        ["MEV_PRESSURE_WEIGHT", "0.3 (0.0=RSI only, 1.0=MEV only)"],
        ["MEV_POLL_INTERVAL_SECONDS", "5"],
    ]
    t = Table(mev_data, colWidths=[2.5 * inch, 4 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#dddddd")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)

    # ── 6. How the Strategy Works ──
    story.append(PageBreak())
    story.append(Paragraph("6. How the Strategy Works", styles["SectionTitle"]))

    story.append(Paragraph("RSI Strategy (Core)", styles["SubSubSection"]))
    story.append(Paragraph(
        "RSI (Relative Strength Index) measures momentum on a 0-100 scale. "
        "The bot uses standard RSI thresholds:",
        styles["BodyText2"],
    ))
    story.append(Paragraph("<bullet>&bull;</bullet> RSI &lt; 30 (oversold) -> BUY signal", styles["BulletItem"]))
    story.append(Paragraph("<bullet>&bull;</bullet> RSI &gt; 70 (overbought) -> SELL signal", styles["BulletItem"]))
    story.append(Paragraph("<bullet>&bull;</bullet> RSI between 30-70 -> HOLD", styles["BulletItem"]))

    story.append(Paragraph("Combined RSI + MEV Strategy", styles["SubSubSection"]))
    story.append(Paragraph(
        "When MEV monitoring is enabled, the bot combines RSI with mempool "
        "pressure data using a weighted score:",
        styles["BodyText2"],
    ))
    story.append(Paragraph("1. RSI is mapped to a -100 to +100 directional score:", styles["BodyText2"]))
    story.append(Preformatted("rsi_score = -1 * (rsi - 50) * 2", styles["CodeBlock"]))
    story.append(Paragraph("2. The combined score is computed:", styles["BodyText2"]))
    story.append(Preformatted("combined = (1 - mev_weight) * rsi_score + mev_weight * mev_pressure", styles["CodeBlock"]))
    story.append(Paragraph("3. Signal thresholds on the combined score:", styles["BodyText2"]))
    story.append(Paragraph("<bullet>&bull;</bullet> combined &gt; +40  ->  BUY", styles["BulletItem"]))
    story.append(Paragraph("<bullet>&bull;</bullet> combined &lt; -40  ->  SELL", styles["BulletItem"]))
    story.append(Paragraph("<bullet>&bull;</bullet> Between -40 and +40  ->  HOLD", styles["BulletItem"]))

    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "<b>Example 1:</b> RSI=25 (oversold, rsi_score=+50) with MEV pressure=+60 (buy pressure) "
        "at weight=0.3: combined = 0.7*50 + 0.3*60 = +53 -> strong BUY.",
        styles["BodyText2"],
    ))
    story.append(Paragraph(
        "<b>Example 2:</b> RSI=25 (oversold) but MEV pressure=-80 (sell pressure) at weight=0.3: "
        "combined = 0.7*50 + 0.3*(-80) = +11 -> HOLD. MEV prevented a bad entry.",
        styles["BodyText2"],
    ))

    story.append(Paragraph("MEV Mempool Monitor", styles["SubSubSection"]))
    story.append(Paragraph(
        "The mempool monitor connects to an Ethereum or BSC node via WebSocket "
        "and watches for pending transactions sent to DEX routers:",
        styles["BodyText2"],
    ))
    for item in ["Uniswap V2 Router", "Uniswap V3 SwapRouter", "PancakeSwap Router (BSC)"]:
        story.append(Paragraph(f"<bullet>&bull;</bullet> {item}", styles["BulletItem"]))
    story.append(Paragraph(
        "It decodes swap function calls, estimates USD values, determines if each swap "
        "is a buy or sell of tracked assets (WETH, WBTC, WBNB), and computes a net "
        "pressure score from -100 (sell pressure) to +100 (buy pressure).",
        styles["BodyText2"],
    ))

    # ── 7. Testing ──
    story.append(PageBreak())
    story.append(Paragraph("7. Testing", styles["SectionTitle"]))
    story.append(Paragraph("The project includes 55 tests covering all modules:", styles["BodyText2"]))
    test_code = """# Run all tests
pytest -v

# Run a specific test file
pytest tests/test_strategy_mev.py -v"""
    story.append(Preformatted(test_code, styles["CodeBlock"]))
    story.append(Paragraph("Test Files", styles["SubSubSection"]))
    for item in [
        "test_indicators.py - 5 tests (RSI calculation)",
        "test_strategy.py - 4 tests (RSI signal evaluation)",
        "test_strategy_mev.py - 8 tests (combined RSI+MEV evaluation)",
        "test_risk_manager.py - 10 tests (position sizing, SL/TP)",
        "test_mev_analyzer.py - 13 tests (pressure, whales, velocity)",
        "test_mempool_monitor.py - 10 tests (monitoring, direction, USD estimation)",
        "test_dex_abis.py - 5 tests (token resolution, router mapping)",
    ]:
        story.append(Paragraph(f"<bullet>&bull;</bullet> {item}", styles["BulletItem"]))

    # ── 8. Dependencies ──
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("8. Dependencies", styles["SectionTitle"]))
    dep_data = [
        ["Package", "Purpose"],
        ["python-binance", "Binance Futures API client"],
        ["pandas", "OHLCV data manipulation"],
        ["numpy", "Numerical computations"],
        ["ta", "Technical analysis indicators"],
        ["python-dotenv", "Environment variable loading"],
        ["websocket-client", "Real-time market data"],
        ["web3", "Ethereum/BSC node interaction (MEV)"],
        ["pytest", "Test framework"],
    ]
    t = Table(dep_data, colWidths=[2.5 * inch, 4 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#dddddd")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)

    # ── 9. Security ──
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("9. Security Notes", styles["SectionTitle"]))
    for item in [
        "NEVER commit .env files or API keys to version control",
        "NEVER hardcode credentials in source files",
        "Always use Binance testnet for development (BINANCE_TESTNET=true)",
        "The bot defaults to DRY_RUN=True (paper trading)",
        "All sensitive config is loaded from environment variables",
        "API keys and secrets are stored only in .env (gitignored)",
    ]:
        story.append(Paragraph(f"<bullet>&bull;</bullet> {item}", styles["BulletItem"]))

    # ── 10. Code Conventions ──
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("10. Code Conventions", styles["SectionTitle"]))
    for item in [
        "PEP 8 style guidelines",
        "Type hints on all function signatures",
        "logging module for all output (no print statements)",
        "Descriptive variable names (e.g. rsi_period, not rp)",
        "Single-purpose functions",
        "Graceful error handling with retries for API calls",
    ]:
        story.append(Paragraph(f"<bullet>&bull;</bullet> {item}", styles["BulletItem"]))

    doc.build(story)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    generate()
