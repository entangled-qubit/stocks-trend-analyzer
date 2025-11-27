import streamlit as st
import pandas as pd
import yfinance as yf
import yfinance as yf
from src.market_data import SAMPLE_TICKERS, get_stock_data, get_company_info, get_detailed_data, get_batch_stock_data, update_market_data, load_market_cache, CACHE_FILE, FUNDAMENTALS_CACHE_FILE
from src.analysis import analyze_stock
from src.ai_agent import get_gemini_report
from src.prompt_generator import generate_prompt, generate_news_prompt

# Page Config
st.set_page_config(
    page_title="Indian Stock Researcher",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Mobile Friendliness
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🇮🇳 Market Tools")
selected_ticker = st.sidebar.selectbox("Select Stock", SAMPLE_TICKERS)
custom_ticker = st.sidebar.text_input("Or Enter Symbol (e.g., RELIANCE.NS)")

# --- AUTO-UPDATE LOGIC ---
if 'auto_update_done' not in st.session_state:
    import os
    import time
    from src.market_data import CACHE_FILE
    
    if os.path.exists(CACHE_FILE):
        mod_time = os.path.getmtime(CACHE_FILE)
        age_hours = (time.time() - mod_time) / 3600
        
        if age_hours > 4:
            st.toast("⚠️ Data is old (>4h). Auto-updating prices...", icon="🔄")
            with st.spinner("⚡ Auto-Running Quick Update (Last 5 Days)..."):
                update_market_data(quick_mode=True)
            st.toast("✅ Data Updated!", icon="🚀")
    
    st.session_state['auto_update_done'] = True

# API Key Input
st.sidebar.markdown("---")
use_default_key = st.sidebar.checkbox("Use Default API Key", value=False)
if use_default_key:
    api_key = "AIzaSyCK0bEUrwFepTYJX5JUVFEur7qNYnTyAOQ"
    st.sidebar.success("Default Key Active")
else:
    api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password", help="Get one from Google AI Studio")

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Data Management")

# Quick Update (Incremental)
if st.sidebar.button("⚡ Force Quick Update"):
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    
    def update_progress(pct, msg):
        progress_bar.progress(pct)
        status_text.text(msg)
        
    result_msg = update_market_data(progress_callback=update_progress, quick_mode=True)
    status_text.empty() # Clear the "Saving..." message
    progress_bar.empty() # Clear progress bar
    st.sidebar.success(result_msg)

# Full Update
if st.sidebar.button("🔄 Full Update (5Y History)"):
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    
    def update_progress(pct, msg):
        progress_bar.progress(pct)
        status_text.text(msg)
        
    result_msg = update_market_data(progress_callback=update_progress, quick_mode=False)
    status_text.empty() # Clear the "Saving..." message
    progress_bar.empty() # Clear progress bar
    st.sidebar.success(result_msg)

if custom_ticker:
    ticker = custom_ticker.upper()
else:
    ticker = selected_ticker

# Main Content
st.title("🚀 Indian Market Screener")

# Tabs
tab1, tab2 = st.tabs(["🔍 Market Scanner", "📊 Deep Analysis"])

import concurrent.futures

# Helper function for parallel processing
def process_ticker(ticker):
    try:
        hist_data = get_stock_data(ticker)
        if hist_data is not None:
            info = get_company_info(ticker)
            analysis = analyze_stock(hist_data, info)
            return {
                "Symbol": ticker,
                "Name": info.get('name', ticker),
                "Sector": info.get('sector', 'Unknown'),
                "Market Cap": info.get('marketCap', 0),
                "Price": analysis['current_price'],
                "Score": analysis.get('score', 0),
                "Trend": analysis['trend'],
                "RSI": analysis['rsi'],
                "Signal": "BUY" if analysis.get('score', 0) > 70 else "HOLD",
                "Verdict": analysis.get('verdict', 'N/A'),
                "Date": analysis.get('analysis_date', 'N/A')
            }
    except Exception as e:
        print(f"Error processing {ticker}: {e}")
    return None

with tab1:
    st.markdown("### Find Top Opportunities")
    
    # Check Cache Status
    import os
    import time
    from src.market_data import CACHE_FILE
    
    cache_time_msg = "⚠️ No Data Cached"
    if os.path.exists(CACHE_FILE):
        mod_time = os.path.getmtime(CACHE_FILE)
        time_diff = (time.time() - mod_time) / 60 # minutes
        if time_diff < 60:
            cache_time_msg = f"✅ Data Updated: {int(time_diff)} mins ago"
        else:
            cache_time_msg = f"⚠️ Data Updated: {int(time_diff/60)} hours ago"
            
    st.info(f"Instant Scanner: Scans 2000+ stocks in < 1 second. | {cache_time_msg}")
    
    if st.button("🚀 Scan Market Now (Instant)", type="primary"):
        # Load from Cache
        batch_data = load_market_cache()
        
        if batch_data.empty:
            st.error("No cached data found! Please click 'Full Update' in the sidebar first.")
        else:
            scored_stocks = []
            
            # Get all tickers from columns (MultiIndex level 0)
            if isinstance(batch_data.columns, pd.MultiIndex):
                tickers = batch_data.columns.levels[0].tolist()
            else:
                tickers = [batch_data.name] if hasattr(batch_data, 'name') else []

            # Load Fundamentals Cache
            fundamentals_df = pd.DataFrame()
            if os.path.exists(FUNDAMENTALS_CACHE_FILE):
                try:
                    fundamentals_df = pd.read_parquet(FUNDAMENTALS_CACHE_FILE)
                except Exception as e:
                    print(f"Error loading fundamentals: {e}")

            # Process in memory (Fast)
            for ticker in tickers:
                try:
                    if isinstance(batch_data.columns, pd.MultiIndex):
                        hist_data = batch_data[ticker].dropna()
                    else:
                        hist_data = batch_data.dropna()

                    if hist_data.empty or len(hist_data) < 200:
                        continue
                        
                    # Get Fundamentals
                    info = {}
                    if not fundamentals_df.empty and ticker in fundamentals_df.index:
                        row = fundamentals_df.loc[ticker]
                        info = {
                            "sector": row.get("Sector", "Unknown"),
                            "industry": row.get("Industry", "Unknown"),
                            "marketCap": row.get("Market Cap", 0),
                            "trailingPE": row.get("P/E", 0),
                            "returnOnEquity": row.get("ROE", 0),
                            "debtToEquity": row.get("D/E", 0),
                            "profitMargins": row.get("Margins", 0),
                            "revenueGrowth": row.get("Sales Growth", 0),
                            "heldPercentInstitutions": row.get("Inst Hold", 0),
                            "fiftyTwoWeekHigh": row.get("52W High", 0),
                            "fiftyTwoWeekLow": row.get("52W Low", 0)
                        }

                    # Full Analysis (Technical + Fundamental)
                    analysis = analyze_stock(hist_data, info)
                    
                    # Extract Metrics
                    current_price = analysis['current_price']
                    trend = analysis['trend']
                    rsi = analysis['rsi']
                    score = analysis.get('score', 0)
                    verdict = analysis.get('verdict', 'Watchlist')
                        
                    # Calculate Returns (1Y, 3Y, 5Y)
                    close_prices = hist_data['Close']
                    ret_1y = ((current_price / close_prices.iloc[-250]) - 1) * 100 if len(close_prices) > 250 else 0
                    ret_3y = ((current_price / close_prices.iloc[-750]) - 1) * 100 if len(close_prices) > 750 else 0
                    ret_5y = ((current_price / close_prices.iloc[-1250]) - 1) * 100 if len(close_prices) > 1250 else 0
                        
                    # Filter: Only Uptrend or Good Momentum (Keep the filter to reduce noise)
                    if trend == "Uptrend" or (40 <= rsi <= 70) or score > 50:
                        scored_stocks.append({
                            "Symbol": ticker,
                            "Price": float(current_price),
                            "Trend": trend,
                            "RSI": float(rsi),
                            "Score": int(score),
                            "Verdict": verdict,
                            "Sector": info.get("sector", "Unknown"),
                            "Market Cap": float(info.get("marketCap", 0)),
                            "1Y %": float(ret_1y),
                            "3Y %": float(ret_3y),
                            "5Y %": float(ret_5y),
                        })
                        
                except Exception:
                    continue
            
            if scored_stocks:
                df = pd.DataFrame(scored_stocks)
                st.session_state.scanned_df = df
                st.success(f"Scanned {len(tickers)} stocks. Found {len(df)} matches!")
            else:
                st.warning("No stocks matched criteria.")
    
    # Display Results if available
    if 'scanned_df' in st.session_state:
        df = st.session_state.scanned_df
        
        if not df.empty:
            # Rankings Tabs
            rank1, rank2, rank3, rank4 = st.tabs(["🏆 Top 40 Quality", "👀 Top 40 Lookout", "🏭 Sector Leaderboard", "💰 Market Cap Leaders"])
            
            column_config = {
                "Price": st.column_config.NumberColumn("Price", format="₹%.2f"),
                "RSI": st.column_config.NumberColumn("RSI", format="%.1f"),
                "Market Cap": st.column_config.NumberColumn("Market Cap", format="₹%d"),
            }

            with rank1:
                st.markdown("#### Top 40 by Quality Score")
                st.caption("Highest scoring stocks (> ₹500 Cr Market Cap) based on Trend, Momentum, MACD, Valuation, and Profitability.")
                
                # Filter for decent market cap to avoid penny stocks
                min_mcap = 500 * 10000000 # 500 Cr
                quality_df = df[df['Market Cap'] > min_mcap]
                
                top_quality = quality_df.sort_values(by="Score", ascending=False).head(40).reset_index(drop=True)
                
                # Drop return columns for display if they exist
                display_cols = [c for c in top_quality.columns if "%" not in c]
                
                st.dataframe(
                    top_quality[display_cols].style.highlight_max(axis=0, subset=['Score'], color='lightgreen'),
                    column_config=column_config,
                    use_container_width=True
                )

            with rank2:
                st.markdown("#### Top 40 Lookout (Momentum)")
                st.caption("Stocks (> ₹500 Cr Market Cap) with strong Momentum (RSI > 60) and Uptrend.")
                
                min_mcap = 500 * 10000000 # 500 Cr
                # Ensure RSI is numeric for filtering
                lookout = df[ (df['RSI'] > 60) & (df['Trend'].str.contains("Uptrend")) & (df['Market Cap'] > min_mcap) ]
                lookout = lookout.sort_values(by="RSI", ascending=False).head(40).reset_index(drop=True)
                
                display_cols = [c for c in lookout.columns if "%" not in c]
                
                st.dataframe(
                    lookout[display_cols].style.highlight_max(axis=0, subset=['RSI'], color='lightblue'),
                    column_config=column_config,
                    use_container_width=True
                )

            with rank3:
                st.markdown("#### Sector Leaderboard")
                st.caption("Deep dive into individual sectors.")
                
                if 'Sector' in df.columns:
                    # Sector Selector
                    sectors = sorted(df['Sector'].unique().tolist())
                    selected_sector = st.selectbox("Select Sector", sectors)
                    
                    if selected_sector:
                        sector_df = df[df['Sector'] == selected_sector].sort_values(by="Score", ascending=False).reset_index(drop=True)
                        display_cols = [c for c in sector_df.columns if "%" not in c]
                        st.dataframe(
                            sector_df[display_cols].style.highlight_max(axis=0, subset=['Score'], color='lightgreen'),
                            column_config=column_config,
                            use_container_width=True
                        )
                else:
                    st.info("⚠️ Sector data not available in Instant Mode. Run Deep Analysis on individual stocks to see details.")

            with rank4:
                st.markdown("#### Market Cap Leaders")
                st.caption("Top scoring stocks in Large, Mid, and Small Cap categories.")
                
                if 'Market Cap' in df.columns:
                    LARGE_CAP = 20000 * 10000000 # 20k Cr
                    MID_CAP = 5000 * 10000000    # 5k Cr
                    
                    large = df[df['Market Cap'] >= LARGE_CAP].sort_values(by="Score", ascending=False).head(10)
                    mid = df[(df['Market Cap'] < LARGE_CAP) & (df['Market Cap'] >= MID_CAP)].sort_values(by="Score", ascending=False).head(10)
                    small = df[df['Market Cap'] < MID_CAP].sort_values(by="Score", ascending=False).head(10)
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown("**Large Cap (>20k Cr)**")
                        st.dataframe(large[['Symbol', 'Score', 'Price']].reset_index(drop=True), use_container_width=True)
                    with c2:
                        st.markdown("**Mid Cap (5k-20k Cr)**")
                        st.dataframe(mid[['Symbol', 'Score', 'Price']].reset_index(drop=True), use_container_width=True)
                    with c3:
                        st.markdown("**Small Cap (<5k Cr)**")
                        st.dataframe(small[['Symbol', 'Score', 'Price']].reset_index(drop=True), use_container_width=True)
                else:
                    st.info("⚠️ Market Cap data not available in Instant Mode. Run Deep Analysis on individual stocks to see details.")

            st.markdown("### 👉 Next Step")
            st.write("Go to the **Deep Analysis** tab to get a full AI report.")
        else:
            st.error("No data found. Please check your internet connection.")

with tab2:
    st.markdown("### 🧠 Deep Stock Analysis")
    
    # Handle selection from scanner
    if st.session_state.get('selected_stock_from_scanner'):
        ticker = st.session_state.selected_stock_from_scanner
        # Reset to avoid getting stuck
        # st.session_state.selected_stock_from_scanner = None 
    elif custom_ticker:
        ticker = custom_ticker.upper()
    else:
        ticker = selected_ticker
        
    if not ticker:
        st.info("👈 Please select a stock from the Sidebar or Scanner results to view Deep Analysis.")
        st.stop()
        
    st.subheader(f"Analysis for {ticker}")

    # Fetch Data (Lazy Load for this tab)
    with st.spinner('Fetching Market Data...'):
        info = get_company_info(ticker)
        hist_data = get_stock_data(ticker)
        detailed_data = get_detailed_data(ticker) # Fetch News & Financials

    if not info or hist_data is None:
        st.error(f"Could not fetch data for {ticker}. Please check the symbol.")
    else:
        # Display Basic Info
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Sector:** {info.get('sector', 'N/A')}")
            st.markdown(f"**Industry:** {info.get('industry', 'N/A')}")
        with col2:
            mcap_cr = info.get('marketCap', 0) / 10000000
            st.markdown(f"**Market Cap:** ₹{mcap_cr:,.2f} Cr")

        with st.expander("Business Summary"):
            st.write(info.get('summary', 'No summary available.'))

        # Technical Analysis
        analysis = analyze_stock(hist_data, info)
        
        st.subheader("Technical Dashboard")
        
        # Display Verdict Prominently
        verdict = analysis.get('verdict', 'N/A')
        boosters = analysis.get('boosters', [])
        boosters_not_met = analysis.get('boosters_not_met', [])
        
        if "Gem" in verdict or "All-Rounder" in verdict:
            st.success(f"**Verdict:** {verdict}")
        elif "Swing" in verdict:
            st.info(f"**Verdict:** {verdict}")
        else:
            st.warning(f"**Verdict:** {verdict}")
            
        if boosters:
            st.caption(f"**✅ Safety Boosters Met:** {', '.join(boosters)}")
        if boosters_not_met:
            st.caption(f"**❌ Safety Boosters Not Met:** {', '.join(boosters_not_met)}")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Price", f"₹{analysis['current_price']}")
        m2.metric("Trend", analysis['trend'], delta_color="normal" if analysis['trend']=="Uptrend" else "inverse")
        m3.metric("RSI", f"{analysis['rsi']:.2f}", analysis['rsi_status'])
        m4.metric("Score", f"{analysis.get('score', 0)}/100")

        # Detailed Technicals
        # --- Live Intraday Chart ---
        with st.expander("📈 Live Intraday Chart (Today)", expanded=True):
            try:
                with st.spinner("Fetching live 1-minute data..."):
                    # Fetch 1-minute data for today
                    intraday_data = yf.download(ticker, period="1d", interval="1m", progress=False)
                    
                    if not intraday_data.empty:
                        # Plot using Streamlit's native chart
                        st.line_chart(intraday_data['Close'], use_container_width=True)
                        
                        # Show latest price and change
                        latest_price = intraday_data['Close'].iloc[-1]
                        first_price = intraday_data['Close'].iloc[0]
                        change = latest_price - first_price
                        pct_change = (change / first_price) * 100
                        
                        c1, c2 = st.columns(2)
                        c1.metric("Live Price", f"₹{latest_price:.2f}", f"{change:.2f} ({pct_change:.2f}%)")
                        c2.caption(f"Last Updated: {intraday_data.index[-1].strftime('%H:%M:%S')}")
                    else:
                        st.warning("No intraday data available right now (Market might be closed or data delayed).")
            except Exception as e:
                st.error(f"Error fetching live chart: {e}")

        # --- Technical Indicators ---
        with st.expander("📈 Technical Indicators (Detailed)", expanded=False):
            t1, t2, t3 = st.columns(3)
            with t1:
                st.markdown("**Moving Averages**")
                st.write(f"SMA 50: ₹{analysis.get('sma_50', 'N/A')}")
                st.write(f"SMA 200: ₹{analysis.get('sma_200', 'N/A')}")
            with t2:
                st.markdown("**MACD**")
                st.write(f"MACD Line: {analysis.get('macd_line', 'N/A')}")
                st.write(f"Signal Line: {analysis.get('macd_signal', 'N/A')}")
                st.caption(f"Status: {analysis.get('macd_status', 'N/A')}")
            with t3:
                st.markdown("**52-Week Range**")
                st.write(f"High: ₹{analysis.get('52w_high', 'N/A')}")
                st.write(f"Low: ₹{analysis.get('52w_low', 'N/A')}")

        # Score Breakdown
        with st.expander("📊 View Score Calculation (Why this score?)", expanded=True):
            st.caption(f"Analysis based on data from: {analysis.get('analysis_date', 'N/A')}")
            breakdown = analysis.get('score_breakdown', {})
            for criteria, points in breakdown.items():
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(criteria)
                with col_b:
                    if points > 0:
                        st.success(f"+{points}")
                    else:
                        st.caption("0")
        
        # Quarterly Financials
        with st.expander("📊 Quarterly Financials"):
            fin_df = detailed_data.get('quarterly_financials')
            if fin_df is not None and not fin_df.empty:
                st.dataframe(fin_df, use_container_width=True)
            else:
                st.info("No quarterly financial data available.")

        # Latest News
        with st.expander("📰 Latest News"):
            news_items = detailed_data.get('news', [])
            if news_items:
                for item in news_items[:5]:
                    # Handle nested structure (yfinance returns news inside 'content')
                    if 'content' in item:
                        content = item['content']
                        title = content.get('title', 'News')
                        link_obj = content.get('clickThroughUrl') or content.get('canonicalUrl')
                        link = link_obj.get('url', '#') if link_obj else '#'
                        publisher = content.get('provider', {}).get('displayName', 'Unknown')
                    else:
                        # Fallback for flat structure
                        title = item.get('title', 'News')
                        link = item.get('link', '#')
                        publisher = item.get('publisher', 'Unknown')
                    
                    st.markdown(f"**[{title}]({link})**")
                    st.caption(f"Source: {publisher}")
            else:
                st.info("No recent news found.")

        # AI News Insight
        st.markdown("---")
        st.subheader("🤖 AI News Insight")
        
        if not api_key:
            st.warning("⚠️ Enter API Key to analyze news with AI.")
            st.info("You can still generate the prompt manually below.")
            
            col_no_key_1, col_no_key_2 = st.columns([1, 1])
            with col_no_key_1:
                if st.button("Generate News Prompt Only"):
                    news_items = detailed_data.get('news', [])
                    if news_items:
                        news_prompt = generate_news_prompt(ticker, news_items)
                        st.code(news_prompt, language="markdown")
                    else:
                        st.warning("No news to generate prompt.")
        else:
            col_news_1, col_news_2 = st.columns([1, 1])
            with col_news_1:
                if st.button("Analyze News & Trends"):
                    news_items = detailed_data.get('news', [])
                    if news_items:
                        with st.spinner("Reading news and analyzing trends..."):
                            news_prompt = generate_news_prompt(ticker, news_items)
                            news_analysis = get_gemini_report(news_prompt, api_key)
                            st.markdown(news_analysis)
                    else:
                        st.warning("No news to analyze.")
            
            with col_news_2:
                with st.expander("View News Prompt"):
                    news_items = detailed_data.get('news', [])
                    if news_items:
                        news_prompt = generate_news_prompt(ticker, news_items)
                        st.code(news_prompt, language="markdown")
                    else:
                        st.info("No news data to generate prompt.")

        # Scoring Definitions
        with st.expander("ℹ️ Scoring Guide (Definitions)"):
            st.markdown("""
            **1. Trend (30 pts)**
            - **Strong Uptrend (30 pts)**: Price > 50-day SMA AND Price > 200-day SMA.
            - **Emerging Uptrend (15 pts)**: Price > 50-day SMA.
            - **No Uptrend (0 pts)**: Price < 50-day SMA.
            
            **2. Momentum (20 pts)**
            - **Healthy (20 pts)**: RSI between 50 and 70.
            - **Neutral (10 pts)**: RSI between 30 and 50.
            - **Extreme (0 pts)**: RSI > 70 (Overbought) or < 30 (Oversold).
            
            **3. MACD (15 pts)**
            - **Bullish Crossover (15 pts)**: MACD line crossed above Signal line in last 3 days.
            - **Bullish Alignment (5 pts)**: MACD line is above Signal line.
            
            **4. Valuation (15 pts)**
            - **Attractive (15 pts)**: P/E Ratio < 25.
            - **Acceptable (8 pts)**: P/E Ratio between 25 and 40.
            - **High (0 pts)**: P/E Ratio > 40.
            
            **5. Profitability (20 pts)**
            - **Strong (20 pts)**: Net Profit Margin > 10%.
            - **Positive (10 pts)**: Net Profit Margin between 0% and 10%.
            - **Unprofitable (0 pts)**: Negative Net Profit Margin.
            
            ---
            **🕰️ Timeframe Verdict Logic (Enhanced)**
            
            **💎 Long Term Gem**
            - *Primary*: P/E < 40, Margins > 0%, Price > 200 SMA.
            - *Safety Boosters*: Debt/Equity < 1.0, ROE > 15%, Sales Growth > 10%.
            
            **⚡ Short Term Swing**
            - *Primary*: RSI 50-70, MACD Bullish, Price > 50 SMA.
            - *Safety Boosters*: Volume > 1.5x Avg, Near 52-Week High (<15%).
            
            **🌟 All-Rounder**
            - Meets Primary criteria for **BOTH**.
            - *Safety Booster*: Institutional Buying > 0%.
            """)

        # Chart
        st.line_chart(hist_data['Close'])

        # Deep Research Section
        st.markdown("---")
        st.header("🧠 Deep Research Agent (Full Report)")
        
        if not api_key:
            st.warning("⚠️ Enter your Gemini API Key in the sidebar to unlock the AI Research Agent.")
            st.info("Don't have a key? You can still generate the prompt manually below.")
            if st.button("Generate Prompt Only"):
                 stock_payload = {**info, "analysis": analysis}
                 prompt = generate_prompt([stock_payload])
                 st.code(prompt, language="markdown")
        else:
            st.success("✅ AI Agent Ready (Model: Gemini 1.5 Pro)")
            if st.button("✨ Generate Deep Research Report"):
                with st.spinner("🤖 AI is researching Politics, Management, and Deals... (This may take 10-20s)"):
                    stock_payload = {**info, "analysis": analysis}
                    prompt = generate_prompt([stock_payload])
                    
                    report = get_gemini_report(prompt, api_key)
                    
                    st.markdown("### 📝 Research Verdict")
                    st.markdown(report)

# Footer
st.markdown("---")
st.caption("Built with Streamlit & Python | Data: Yahoo Finance")
