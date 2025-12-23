import sys
import os

# Add local directory to path to find src
sys.path.append(os.getcwd())

from src.market_data import get_stock_data, get_batch_stock_data
import yfinance as yf

def test_yfinance_fix():
    print("--- Testing Market Data Fix ---")
    ticker = "RELIANCE.NS"
    print(f"Fetching data for {ticker}...")
    try:
        df = get_stock_data(ticker, period="5d")
        if df is not None and not df.empty:
            print(f"✅ Success: Fetched {len(df)} rows.")
            print(df.tail(2))
        else:
            print("❌ Failed: No data returned.")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\nTesting Batch Download...")
    tickers = ["TCS.NS", "INFY.NS"]
    try:
        df = get_batch_stock_data(tickers, period="5d")
        if not df.empty:
            print(f"✅ Success: Batch fetch ok. Shape: {df.shape}")
        else:
            print("❌ Failed: Batch data empty.")
    except Exception as e:
        print(f"❌ Batch Error: {e}")

def test_genai_migration():
    print("\n--- Testing Google GenAI Migration ---")
    # We can only test this if we have a key. 
    # If not, we just check if the import works and function exists.
    try:
        from src.ai_agent import get_gemini_report
        import google.generativeai as genai
        print("✅ google.generativeai imported successfully.")
    except ImportError:
        print("❌ google.generativeai NOT found. Did you install requirements?")

if __name__ == "__main__":
    test_yfinance_fix()
    test_genai_migration()
