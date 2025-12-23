import yfinance as yf
import pandas as pd
import concurrent.futures
import streamlit as st
from typing import List, Dict, Optional
import requests

# Fix for 401 Unauthorized Error
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})
# Configure yfinance to use this session (hacky global patch if needed, or pass session)
# Since yfinance global configuration is not always reliable for 'download', we might need to rely on the update.
# However, newer yfinance versions handle this better. 
# We will rely on the upgraded version but if that fails, we can't easily pass 'session' to download in all versions.
# Let's try to set it via pandas_datareader override if relevant, but yfinance is standalone here.
# NOTE: In yfinance >= 0.2, it manages sessions well if User-Agent is standard.


# Expanded list of Indian Small/Mid-cap stocks (NSE)
# Expanded list of Indian Stocks (Targeting NIFTY 500 coverage)
# Note: This is a static list. In a production app, this should be fetched dynamically.
SAMPLE_TICKERS = [
    # NIFTY 50
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LICI.NS", "LT.NS", "AXISBANK.NS", "HCLTECH.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "BAJFINANCE.NS", "ULTRACEMCO.NS",
    "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "ADANIENT.NS", "ADANIPORTS.NS", "TATAMOTORS.NS", "M&M.NS", "COALINDIA.NS",
    "HDFCLIFE.NS", "BAJAJFINSV.NS", "BPCL.NS", "GRASIM.NS", "BRITANNIA.NS", "TECHM.NS", "HINDALCO.NS", "WIPRO.NS", "CIPLA.NS", "SBILIFE.NS",
    "DRREDDY.NS", "EICHERMOT.NS", "INDUSINDBK.NS", "DIVISLAB.NS", "TATACONSUM.NS", "APOLLOHOSP.NS", "HEROMOTOCO.NS", "UPL.NS",
    
    # NIFTY Next 50 & Midcaps
    "PIDILITIND.NS", "BEL.NS", "LTIM.NS", "IOC.NS", "TRENT.NS", "DLF.NS", "SHREECEM.NS", "SIEMENS.NS", "TVSMOTOR.NS", "HAVELLS.NS",
    "ABB.NS", "AMBUJACEM.NS", "VEDL.NS", "GAIL.NS", "CHOLAFIN.NS", "BANKBARODA.NS", "CANBK.NS", "SRF.NS", "ZOMATO.NS", "VBL.NS",
    "ICICIPRULI.NS", "PNB.NS", "RECLTD.NS", "BOSCHLTD.NS", "TORNTPHARM.NS", "MOTHERSON.NS", "INDIGO.NS", "HAL.NS", "GODREJCP.NS", "DABUR.NS",
    "SHRIRAMFIN.NS", "MCDOWELL-N.NS", "BERGEPAINT.NS", "MARICO.NS", "ICICIGI.NS", "SBICARD.NS", "MUTHOOTFIN.NS", "PIIND.NS", "NAUKRI.NS", "COLPAL.NS",
    
    # Small/Mid Caps & Others (High Interest)
    "CUPID.NS", "CDSL.NS", "IEX.NS", "TATAELXSI.NS", "KPITTECH.NS", "HAPPSTMNDS.NS", "BSOFT.NS", "TANLA.NS", "ROUTE.NS", "AFFLE.NS",
    "LXCHEM.NS", "DEEPAKNI.NS", "ALKYLAMINE.NS", "FINEORG.NS", "NAVINFLUOR.NS", "ANGELONE.NS", "BSE.NS", "MCX.NS", "CENTRALBK.NS", "UCOBANK.NS",
    "IDFCFIRSTB.NS", "RENUKA.NS", "TRIDENT.NS", "SUZLON.NS", "PAYTM.NS", "NYKAA.NS", "POLICYBZR.NS", "DELHIVERY.NS", "MAPMYINDIA.NS",
    "LATENTVIEW.NS", "DATAPATTNS.NS", "MTARTECH.NS", "PARAS.NS", "ZENTECH.NS", "MAZDOCK.NS", "COCHINSHIP.NS", "GRSE.NS", "BDL.NS",
    "RVNL.NS", "IRFC.NS", "IRCON.NS", "RITES.NS", "GMDCLTD.NS", "GMMPFAUDLR.NS", "JUBLFOOD.NS", "DEVYANI.NS", "SAPPHIRE.NS",
    "KAYNES.NS", "SYRMA.NS", "DHOOTIN.NS", "EMAMILTD.NS", "ENDURANCE.NS", "ERIS.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS",
    "FACT.NS", "FSL.NS", "GLENMARK.NS", "GODREJPROP.NS", "GRANULES.NS", "GNFC.NS", "GUJGASLTD.NS", "GSPL.NS", "HEG.NS", "HFCL.NS",
    "HINDCOPPER.NS", "HINDPETRO.NS", "HUDCO.NS", "IDBI.NS", "IDFC.NS", "IIFL.NS", "INDIANB.NS", "ISEC.NS", "INDIGOPNTS.NS", "IGL.NS",
    "INDUSTOWER.NS", "INFIBEAM.NS", "INTELLECT.NS", "JBCHEPHARM.NS", "JINDALSAW.NS", "JSL.NS", "JINDALSTEL.NS", "JIOFIN.NS", "JKLAKSHMI.NS",
    "JKPAPER.NS", "JKTYRE.NS", "JMFINANCIL.NS", "JSWENERGY.NS", "KAJARIACER.NS", "KALPATPOWR.NS", "KALYANKJIL.NS", "KANSAINER.NS", "KARURVYSYA.NS",
    "KEI.NS", "KEC.NS", "KNRCON.NS", "LALPATHLAB.NS", "LAURUSLABS.NS", "LICHSGFIN.NS", "LODHA.NS", "LUPIN.NS", "MAHABANK.NS", "M&MFIN.NS",
    "MAHLIFE.NS", "MANAPPURAM.NS", "MRPL.NS", "MAXHEALTH.NS", "METROBRAND.NS", "METROPOLIS.NS", "MFSL.NS", "MINGROUP.NS", "MISHRA.NS", "MOIL.NS",
    "MRF.NS", "NAM-INDIA.NS", "NATIONALUM.NS", "NBCC.NS", "NCC.NS", "NHPC.NS", "NLCINDIA.NS", "NMDC.NS", "OBEROIRLTY.NS", "OIL.NS",
    "OFSS.NS", "PAGEIND.NS", "PATANJALI.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PHOENIXLTD.NS", "PVRINOX.NS", "POLYMED.NS", "POLYCAB.NS",
    "POONAWALLA.NS", "PRAJIND.NS", "PRESTIGE.NS", "PRINCEPIPE.NS", "RBLBANK.NS", "RADICO.NS", "RVNL.NS", "RAIN.NS", "RAJESHEXPO.NS", "RCF.NS",
    "REDINGTON.NS", "RHIM.NS", "RBA.NS", "RKFORGE.NS", "SAIL.NS", "SJVN.NS", "SKFINDIA.NS", "SONACOMS.NS", "STARHEALTH.NS", "SUMICHEM.NS",
    "SUNDARMFIN.NS", "SUNTV.NS", "SUVENPHAR.NS", "SYMPHONY.NS", "TEJASNET.NS", "RAMCOCEM.NS", "THERMAX.NS", "TIMKEN.NS", "TORNTPOWER.NS", "TTML.NS",
    "TIINDIA.NS", "UBL.NS", "UNITDSPR.NS", "VGUARD.NS", "VIPIND.NS", "VOLTAS.NS", "WELCORP.NS", "WELSPUNIND.NS", "WHIRLPOOL.NS", "YESBANK.NS",
    "ZEEL.NS", "ZFCVINDIA.NS"
]

def get_stock_data(ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """
    Fetches historical data for a given ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            return None
        return hist
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

def get_batch_stock_data(tickers: List[str], period: str = "1y") -> pd.DataFrame:
    """
    Fetches historical data for multiple tickers in one batch request.
    Returns a MultiIndex DataFrame (Ticker, Price Fields).
    """
    try:
        # yf.download is faster for batch
        # Added auto_adjust=True to suppress warning and ensure consistent data
        data = yf.download(tickers, period=period, group_by='ticker', threads=True, progress=False, auto_adjust=True)
        return data
    except Exception as e:
        print(f"Error in batch download: {e}")
        return pd.DataFrame()

def get_company_info(ticker: str) -> Dict:
    """
    Fetches basic company info (market cap, sector, summary).
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "symbol": ticker,
            "name": info.get("shortName", ticker),
            "marketCap": info.get("marketCap", 0),
            "currency": info.get("currency", "INR"),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "trailingPE": info.get("trailingPE", None),
            "profitMargins": info.get("profitMargins", 0),
            "debtToEquity": info.get("debtToEquity", None),
            "returnOnEquity": info.get("returnOnEquity", None),
            "revenueGrowth": info.get("revenueGrowth", None),
            "heldPercentInstitutions": info.get("heldPercentInstitutions", None),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh", None),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow", None),
            "summary": info.get("longBusinessSummary", "No summary available.")[:300] + "..."
        }
    except Exception:
        return {}

def filter_small_caps(tickers: List[str], min_cap: int = 1_000_000_000, max_cap: int = 500_000_000_000) -> List[Dict]:
    """
    Filters a list of tickers for those within a specific market cap range (in INR).
    Default: 100 Cr to 50,000 Cr (Small to Mid Cap range for India context).
    """
    candidates = []
    # print(f"Scanning {len(tickers)} stocks for candidates...")
    
    for ticker in tickers:
        info = get_company_info(ticker)
        cap = info.get("marketCap", 0)
        
        # Basic check: if cap is within range
        if min_cap <= cap <= max_cap:
            candidates.append(info)
            # print(f"  [+] Found Candidate: {ticker} (₹{cap/10000000:.2f} Cr)")
        else:
            pass
            
    return candidates

def scan_market(tickers: List[str]) -> List[Dict]:
    """
    Scans the provided list of tickers and returns basic info for all of them.
    Used for the bulk scanner.
    """
    results = []
    for ticker in tickers:
        info = get_company_info(ticker)
        if info:
            results.append(info)
    return results



def get_detailed_data(ticker: str) -> Dict:
    """
    Fetches detailed data including quarterly financials and news.
    """
    try:
        stock = yf.Ticker(ticker)
        return {
            "quarterly_financials": stock.quarterly_financials,
            "news": stock.news
        }
    except Exception as e:
        print(f"Error fetching detailed data for {ticker}: {e}")
        return {"quarterly_financials": None, "news": []}

# --- CACHING & FULL MARKET SCAN ---

CACHE_DIR = "data"
CACHE_FILE = f"{CACHE_DIR}/market_cache.parquet"
FUNDAMENTALS_CACHE_FILE = f"{CACHE_DIR}/fundamentals_cache.parquet"

def get_all_nse_tickers() -> List[str]:
    """
    Fetches the full list of NSE equity symbols.
    Falls back to SAMPLE_TICKERS if download fails.
    """
    url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
    try:
        # NSE blocks bots, so we need headers
        headers = {'User-Agent': 'Mozilla/5.0'}
        df = pd.read_csv(url, storage_options=headers)
        
        # Extract symbols and add .NS
        if 'SYMBOL' in df.columns:
            tickers = [f"{sym}.NS" for sym in df['SYMBOL'].tolist()]
            return tickers
        else:
            print("Column 'SYMBOL' not found in NSE CSV.")
            return SAMPLE_TICKERS
    except Exception as e:
        print(f"Error fetching NSE list: {e}")
        print("Falling back to static sample list.")
        # Expanded fallback list (Top 100 + others)
        return SAMPLE_TICKERS + [
            "ADANIGREEN.NS", "ADANITRANS.NS", "DMART.NS", "BAJAJHLDNG.NS", "SIEMENS.NS", "PIDILITIND.NS",
            "SBICARD.NS", "ICICIPRULI.NS", "ICICIGI.NS", "DLF.NS", "INDIGO.NS", "NYKAA.NS", "PAYTM.NS",
            "ZOMATO.NS", "LTIM.NS", "MOTHERSON.NS", "HAL.NS", "BEL.NS", "VBL.NS", "TRENT.NS", "TVSMOTOR.NS",
            "VEDL.NS", "HAVELLS.NS", "IOC.NS", "AMBUJACEM.NS", "GAIL.NS", "CHOLAFIN.NS", "BANKBARODA.NS",
            "CANBK.NS", "SRF.NS", "ABB.NS", "BOSCHLTD.NS", "TORNTPHARM.NS", "GODREJCP.NS", "DABUR.NS",
            "SHRIRAMFIN.NS", "MCDOWELL-N.NS", "BERGEPAINT.NS", "MARICO.NS", "MUTHOOTFIN.NS", "PIIND.NS",
            "NAUKRI.NS", "COLPAL.NS", "HINDZINC.NS", "JINDALSTEL.NS", "JSWENERGY.NS", "LUPIN.NS", "ALKEM.NS",
            "AUROPHARMA.NS", "BIOCON.NS", "TATACHEM.NS", "ACC.NS", "AUBANK.NS", "BANDHANBNK.NS", "FEDERALBNK.NS",
            "IDFCFIRSTB.NS", "PNB.NS", "INDUSINDBK.NS", "YESBANK.NS", "ABCAPITAL.NS", "ASHOKLEY.NS", "BALKRISIND.NS",
            "BATAINDIA.NS", "BHARATFORG.NS", "BHEL.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", "COFORGE.NS", "CONCOR.NS",
            "COROMANDEL.NS", "CROMPTON.NS", "CUB.NS", "CUMMINSIND.NS", "DEEPAKNTR.NS", "DELTACORP.NS", "DIXON.NS",
            "ESCORTS.NS", "EXIDEIND.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJPROP.NS", "GRANULES.NS",
            "GUJGASLTD.NS", "HAL.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "IBULHSGFIN.NS", "IDFC.NS", "IGL.NS",
            "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", "IPCALAB.NS", "IRCTC.NS", "JKCEMENT.NS", "JUBLFOOD.NS",
            "L&TFH.NS", "LALPATHLAB.NS", "LAURUSLABS.NS", "LICHSGFIN.NS", "LTTS.NS", "M&MFIN.NS", "MANAPPURAM.NS",
            "MFSL.NS", "MGL.NS", "MPHASIS.NS", "MRF.NS", "NAM-INDIA.NS", "NATIONALUM.NS", "NAVINFLUOR.NS", "NMDC.NS",
            "OBEROIRLTY.NS", "OFSS.NS", "PAGEIND.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "POLYCAB.NS",
            "PVR.NS", "RAIN.NS", "RAMCOCEM.NS", "RBLBANK.NS", "RECLTD.NS", "SAIL.NS", "SBILIFE.NS", "SRTRANSFIN.NS",
            "STAR.NS", "SUNTV.NS", "SYNGENE.NS", "TATACOMM.NS", "TATAPOWER.NS", "TORNTPOWER.NS", "TRENT.NS",
            "UBL.NS", "ULTRACEMCO.NS", "VOLTAS.NS", "WHIRLPOOL.NS", "ZEEL.NS"
        ]

def fetch_fundamentals_batch(tickers: List[str], max_workers: int = 5) -> pd.DataFrame:
    """
    Fetches fundamental data for a list of tickers in parallel.
    """
    import time
    import random
    
    def safe_float(val):
        try:
            if val is None: return 0.0
            if isinstance(val, str):
                if val.lower() in ['infinity', 'inf']: return 0.0
                return float(val)
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    def fetch_one(ticker):
        try:
            # Random delay to be nice to the API
            time.sleep(random.uniform(0.05, 0.2))
            
            info = yf.Ticker(ticker).info
            return {
                "Symbol": ticker,
                "Sector": info.get('sector', 'Unknown'),
                "Industry": info.get('industry', 'Unknown'),
                "Market Cap": safe_float(info.get('marketCap', 0)),
                "P/E": safe_float(info.get('trailingPE', 0)),
                "ROE": safe_float(info.get('returnOnEquity', 0)),
                "D/E": safe_float(info.get('debtToEquity', 0)),
                "Margins": safe_float(info.get('profitMargins', 0)),
                "Sales Growth": safe_float(info.get('revenueGrowth', 0)),
                "Inst Hold": safe_float(info.get('heldPercentInstitutions', 0)),
                "52W High": safe_float(info.get('fiftyTwoWeekHigh', 0)),
                "52W Low": safe_float(info.get('fiftyTwoWeekLow', 0))
            }
        except Exception:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(fetch_one, tickers))
        
    fundamentals = [r for r in results if r is not None]
    
    if not fundamentals:
        return pd.DataFrame()
        
    df = pd.DataFrame(fundamentals)
    df.set_index("Symbol", inplace=True)
    return df

def update_market_data(progress_callback=None, quick_mode=False) -> str:
    """
    Downloads data for ALL NSE stocks and saves to cache.
    quick_mode: If True, fetches only last 5 days and merges with cache.
    Returns a status message.
    """
    import os
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        
    tickers = sorted(list(set(get_all_nse_tickers())))
    total = len(tickers)
    
    # Determine period based on mode
    period = "5d" if quick_mode else "5y"
    mode_msg = "Quick Update (5d)" if quick_mode else "Full Update (5y)"
    
    if progress_callback:
        progress_callback(0.1, f"Found {total} stocks. Starting {mode_msg}...")
        
    # Batch download
    # Smaller chunk size = more frequent progress updates
    chunk_size = 50
    all_data = []
    
    for i in range(0, total, chunk_size):
        chunk = tickers[i:i+chunk_size]
        if progress_callback:
            progress_callback(0.1 + (0.8 * (i/total)), f"Downloading batch {i}-{min(i+chunk_size, total)} of {total}...")
            
        try:
            # Download chunk
            data = yf.download(chunk, period=period, group_by='ticker', threads=True, progress=False, auto_adjust=True)
            if not data.empty:
                all_data.append(data)
        except Exception as e:
            print(f"Error downloading chunk {i}: {e}")
            
    if not all_data:
        return "Failed to download any data."
        
    # Merge all chunks
    try:
        if progress_callback: progress_callback(0.90, "Processing downloaded data...")
        new_df = pd.concat(all_data, axis=1)
        
        if quick_mode and os.path.exists(CACHE_FILE):
            # Load existing cache
            try:
                if progress_callback: progress_callback(0.92, "Reading existing cache...")
                existing_df = pd.read_parquet(CACHE_FILE)
                
                if progress_callback: progress_callback(0.95, "Merging new prices...")
                # Combine and sort
                combined_df = pd.concat([existing_df, new_df])
                
                # Remove duplicate indices (Dates), keeping the new ones (last)
                combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
                
                # Sort by date
                combined_df = combined_df.sort_index()
                
                full_df = combined_df
            except Exception as e:
                print(f"Error merging cache: {e}. Overwriting with new data.")
                full_df = new_df
        else:
            full_df = new_df
        
        # Save to Parquet
        if progress_callback: progress_callback(0.98, "Finalizing and saving to disk...")
        full_df.to_parquet(CACHE_FILE)
        
        # Fetch Fundamentals if Full Update
        if not quick_mode:
            if progress_callback: progress_callback(0.99, "Fetching Fundamentals (this takes ~1-2 mins)...")
            fund_df = fetch_fundamentals_batch(tickers)
            if not fund_df.empty:
                fund_df.to_parquet(FUNDAMENTALS_CACHE_FILE)
        
        # Get actual file size
        file_size_mb = os.path.getsize(CACHE_FILE) / (1024 * 1024)
        return f"Update Complete! Cache saved ({file_size_mb:.1f} MB). You can now scan."
    except Exception as e:
        return f"Error saving cache: {e}"

@st.cache_data(ttl=3600, show_spinner="Loading Market Data...")
def load_market_cache() -> pd.DataFrame:
    """
    Loads market data from local parquet cache.
    """
    import os
    if os.path.exists(CACHE_FILE):
        try:
            return pd.read_parquet(CACHE_FILE)
        except Exception as e:
            print(f"Error reading cache: {e}")
            return pd.DataFrame()
    return pd.DataFrame()
