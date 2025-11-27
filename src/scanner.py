import pandas as pd
import streamlit as st
import os
from src.analysis import analyze_stock
from src.market_data import FUNDAMENTALS_CACHE_FILE

@st.cache_data(ttl=3600, show_spinner="Scanning Market...")
def run_scanner(batch_data: pd.DataFrame) -> pd.DataFrame:
    """
    Runs the technical and fundamental analysis on the provided market data.
    This function is cached to prevent re-running on every interaction.
    """
    if batch_data.empty:
        return pd.DataFrame()

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
        return pd.DataFrame(scored_stocks)
    return pd.DataFrame()
