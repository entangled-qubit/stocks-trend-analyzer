import pandas as pd
import numpy as np

def calculate_sma(data: pd.DataFrame, window: int) -> pd.Series:
    return data['Close'].rolling(window=window).mean()

def calculate_rsi(data: pd.DataFrame, window: int = 14) -> pd.Series:
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data: pd.DataFrame) -> pd.Series:
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def analyze_stock(data: pd.DataFrame, info: dict = {}) -> dict:
    """
    Performs advanced technical and fundamental analysis based on specific user criteria.
    Returns a dictionary of indicators, signals, and a detailed score breakdown (Max 100 pts).
    """
    if data is None or len(data) < 200:
        return {"error": "Insufficient data for analysis"}

    df = data.copy()
    
    # Calculate Indicators
    df['SMA_50'] = calculate_sma(df, 50)
    df['SMA_200'] = calculate_sma(df, 200)
    df['RSI'] = calculate_rsi(df)
    macd, macd_signal = calculate_macd(df)
    
    latest = df.iloc[-1]
    
    # --- SCORING LOGIC (Max 100) ---
    score = 0
    breakdown = {}
    signals = []

    # 1. Trend (Max 30 pts)
    # Strong Uptrend: Price > SMA50 AND Price > SMA200 (30 pts)
    # Emerging Uptrend: Price > SMA50 AND Price <= SMA200 (15 pts)
    # No Uptrend: Price <= SMA50 (0 pts)
    
    close = latest['Close']
    sma50 = latest['SMA_50']
    sma200 = latest['SMA_200']
    
    trend_status = "Downtrend/Neutral"
    if close > sma50 and close > sma200:
        score += 30
        breakdown["Trend (Strong Uptrend: > SMA50 & SMA200)"] = 30
        trend_status = "Strong Uptrend"
    elif close > sma50:
        score += 15
        breakdown["Trend (Emerging Uptrend: > SMA50)"] = 15
        trend_status = "Emerging Uptrend"
    else:
        breakdown["Trend (No Uptrend: < SMA50)"] = 0

    # 2. Momentum (RSI) (Max 20 pts)
    # Healthy: 50-70 (20 pts)
    # Neutral: 30-50 (10 pts)
    # Overbought/Oversold: >70 or <30 (0 pts)
    rsi_val = latest['RSI']
    rsi_status = "Neutral"
    
    if 50 <= rsi_val <= 70:
        score += 20
        breakdown["Momentum (Healthy RSI: 50-70)"] = 20
        rsi_status = "Bullish/Healthy"
    elif 30 <= rsi_val < 50:
        score += 10
        breakdown["Momentum (Neutral RSI: 30-50)"] = 10
        rsi_status = "Neutral/Weak"
    else:
        breakdown["Momentum (Extreme RSI: >70 or <30)"] = 0
        if rsi_val > 70: rsi_status = "Overbought"
        if rsi_val < 30: rsi_status = "Oversold"

    # 3. MACD (Max 15 pts)
    # Bullish Crossover in last 3 days (15 pts)
    # Bullish Alignment (MACD > Signal) (5 pts)
    # Bearish (0 pts)
    
    # Get last 3 rows for MACD check
    recent_macd = macd.iloc[-3:]
    recent_signal = macd_signal.iloc[-3:]
    
    macd_val = macd.iloc[-1]
    signal_val = macd_signal.iloc[-1]
    macd_status = "Bearish"
    
    # Check for crossover in last 3 days
    # Crossover means: Prev(MACD <= Signal) AND Curr(MACD > Signal)
    crossover_found = False
    for i in range(1, len(recent_macd)):
        if recent_macd.iloc[i] > recent_signal.iloc[i] and recent_macd.iloc[i-1] <= recent_signal.iloc[i-1]:
            crossover_found = True
            break
            
    if crossover_found:
        score += 15
        breakdown["MACD (Bullish Crossover < 3 days)"] = 15
        macd_status = "Bullish Crossover"
        signals.append("MACD Buy Signal")
    elif macd_val > signal_val:
        score += 5
        breakdown["MACD (Bullish Alignment)"] = 5
        macd_status = "Bullish"
    else:
        breakdown["MACD (Bearish/Neutral)"] = 0

    # 4. Valuation (P/E) (Max 15 pts)
    # Attractive: < 25 (15 pts)
    # Acceptable: 25-40 (8 pts)
    # High: > 40 (0 pts)
    pe = info.get('trailingPE', None)
    if pe is not None:
        if 0 < pe < 25:
            score += 15
            breakdown["Valuation (Attractive P/E < 25)"] = 15
        elif 25 <= pe <= 40:
            score += 8
            breakdown["Valuation (Acceptable P/E 25-40)"] = 8
        else:
            breakdown["Valuation (High P/E > 40)"] = 0
    else:
        breakdown["Valuation (No P/E Data)"] = 0

    # 5. Profitability (Margins) (Max 20 pts)
    # Strong: > 10% (20 pts)
    # Positive: 0-10% (10 pts)
    # Unprofitable: < 0% (0 pts)
    margins = info.get('profitMargins', 0) # Usually float, e.g. 0.12 for 12%
    if margins > 0.10:
        score += 20
        breakdown["Profitability (Strong Margins > 10%)"] = 20
    elif 0 < margins <= 0.10:
        score += 10
        breakdown["Profitability (Positive Margins 0-10%)"] = 10
    else:
        breakdown["Profitability (Unprofitable/Negative)"] = 0

    # Volume Spike Check (Just for signals, not score)
    avg_vol = df['Volume'].tail(20).mean()
    vol_status = "Normal"
    if latest['Volume'] > avg_vol * 1.5:
        vol_status = "High Volume Spike"
        signals.append("High Volume Interest")

    # --- TIMEFRAME VERDICT (ENHANCED) ---
    verdict = "👀 Watchlist"
    boosters_met = []
    boosters_not_met = []
    
    # Data for Boosters
    debt_eq = info.get('debtToEquity')
    roe = info.get('returnOnEquity')
    rev_growth = info.get('revenueGrowth')
    inst_hold = info.get('heldPercentInstitutions')
    
    # 52 Week High/Low (Prefer info, fallback to data)
    high_52 = info.get('fiftyTwoWeekHigh')
    low_52 = info.get('fiftyTwoWeekLow')
    if high_52 is None: high_52 = df['Close'].tail(252).max()
    if low_52 is None: low_52 = df['Close'].tail(252).min()
    
    # Criteria Checks
    # Long Term Primary
    lt_primary = (pe is not None and pe < 40) and (margins > 0) and (latest['Close'] > latest['SMA_200'])
    
    # Short Term Primary
    st_primary = (50 <= rsi_val <= 70) and (macd_status in ["Bullish", "Bullish Crossover"]) and (latest['Close'] > latest['SMA_50'])
    
    # Safety Boosters Checks & Tracking
    lt_boosters_met = 0
    lt_boosters_expected = 3  # Debt, ROE, Sales Growth
    st_boosters_met = 0
    st_boosters_expected = 2  # Volume, 52W High
    ar_boosters_met = 0
    ar_boosters_expected = 1  # Institutional
    
    if lt_primary:
        if debt_eq is not None and debt_eq < 100:
            boosters_met.append(f"🛡️ Low Debt (D/E: {debt_eq:.1f} < 100)")
            lt_boosters_met += 1
        else:
            debt_val = f"{debt_eq:.1f}" if debt_eq is not None else "N/A"
            boosters_not_met.append(f"🛡️ Low Debt (D/E: {debt_val})")
            
        if roe is not None and roe > 0.15:
            boosters_met.append(f"📈 High ROE ({roe*100:.1f}% > 15%)")
            lt_boosters_met += 1
        else:
            roe_val = f"{roe*100:.1f}%" if roe is not None else "N/A"
            boosters_not_met.append(f"📈 High ROE ({roe_val})")
            
        if rev_growth is not None and rev_growth > 0.10:
            boosters_met.append(f"🚀 Sales Growth ({rev_growth*100:.1f}% > 10%)")
            lt_boosters_met += 1
        else:
            growth_val = f"{rev_growth*100:.1f}%" if rev_growth is not None else "N/A"
            boosters_not_met.append(f"🚀 Sales Growth ({growth_val})")
        
    if st_primary:
        if vol_status == "High Volume Spike":
            boosters_met.append("🔊 Volume Spike")
            st_boosters_met += 1
        else:
            boosters_not_met.append("🔊 Volume Spike")
            
        if high_52 and latest['Close'] >= 0.85 * high_52:
            pct_from_high = ((latest['Close'] / high_52) * 100) if high_52 else 0
            boosters_met.append(f"🏔️ Near 52W High ({pct_from_high:.1f}% of high)")
            st_boosters_met += 1
        else:
            pct_from_high = ((latest['Close'] / high_52) * 100) if high_52 else 0
            boosters_not_met.append(f"🏔️ Near 52W High ({pct_from_high:.1f}% of high)")
        
    if lt_primary and st_primary:
        if inst_hold is not None and inst_hold > 0:
            boosters_met.append(f"🏦 Institutional Holding ({inst_hold*100:.1f}%)")
            ar_boosters_met += 1
        else:
            inst_val = f"{inst_hold*100:.1f}%" if inst_hold is not None else "N/A"
            boosters_not_met.append(f"🏦 Institutional Holding ({inst_val})")

    # Final Verdict with Safety Check (only warn if >10% missing, i.e., <90% completion)
    booster_completion_rate = 1.0  # Default to 100%
    
    if lt_primary and st_primary:
        verdict = "🌟 All-Rounder"
        # Check all boosters (LT + ST + AR)
        total_expected = lt_boosters_expected + st_boosters_expected + ar_boosters_expected
        total_met = lt_boosters_met + st_boosters_met + ar_boosters_met
        booster_completion_rate = total_met / total_expected if total_expected > 0 else 1.0
    elif lt_primary:
        verdict = "💎 Long Term Gem"
        booster_completion_rate = lt_boosters_met / lt_boosters_expected if lt_boosters_expected > 0 else 1.0
    elif st_primary:
        verdict = "⚡ Short Term Swing"
        booster_completion_rate = st_boosters_met / st_boosters_expected if st_boosters_expected > 0 else 1.0
    
    # Add warning if <90% of boosters are met (i.e., >10% are missing)
    if booster_completion_rate < 0.90 and verdict != "👀 Watchlist":
        verdict += " (⚠️ Check Safety)"

    # 52 Week High/Low (Prefer info, fallback to data)
    high_52 = info.get('fiftyTwoWeekHigh')
    low_52 = info.get('fiftyTwoWeekLow')
    
    if high_52 is None:
        high_52 = df['Close'].tail(252).max()
    if low_52 is None:
        low_52 = df['Close'].tail(252).min()

    return {
        "analysis_date": latest.name.strftime('%Y-%m-%d'),
        "current_price": round(latest['Close'], 2),
        "sma_50": round(latest['SMA_50'], 2),
        "sma_200": round(latest['SMA_200'], 2),
        "rsi": round(rsi_val, 2),
        "rsi_status": rsi_status,
        "volume_status": vol_status,
        "trend": trend_status,
        "macd_status": macd_status,
        "macd_line": round(macd_val, 2),
        "macd_signal": round(signal_val, 2),
        "52w_high": round(high_52, 2) if high_52 else None,
        "52w_low": round(low_52, 2) if low_52 else None,
        "signals": signals,
        "score": min(score, 100),
        "score_breakdown": breakdown,
        "verdict": verdict,
        "boosters": boosters_met,
        "boosters_not_met": boosters_not_met
    }
