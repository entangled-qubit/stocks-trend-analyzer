import yfinance as yf
import pandas as pd

def test_reliance():
    print("Testing RELIANCE.NS fetch...")
    try:
        ticker = "RELIANCE.NS"
        data = yf.download(ticker, period="5d", progress=False)
        if not data.empty:
            print(f"✅ Success! Fetched {len(data)} rows for {ticker}")
            print(data.tail())
        else:
            print(f"❌ Failed! Empty data for {ticker}")
            
        info = yf.Ticker(ticker).info
        print(f"✅ Info fetched: Sector={info.get('sector')}, MarketCap={info.get('marketCap')}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_nifty_500():
    print("\nTesting NIFTY 500 list fetch...")
    # Try to get a cleaner list. 
    # Often EQUITY_L.csv contains everything. We might want to filter by Market Cap if possible, 
    # but we don't have market cap until we fetch info.
    # Alternative: Use a hardcoded NIFTY 50 list to verify the "Good" stocks work.
    
    nifty50 = ["RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "TCS.NS", "ITC.NS"]
    print(f"Checking NIFTY 50 sample: {nifty50}")
    
    data = yf.download(nifty50, period="5d", group_by='ticker', progress=False)
    for t in nifty50:
        if not data[t].empty:
             print(f"✅ {t}: OK")
        else:
             print(f"❌ {t}: No Data")

if __name__ == "__main__":
    test_reliance()
    test_nifty_500()
