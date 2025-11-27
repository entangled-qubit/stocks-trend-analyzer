from typing import List, Dict
import pyperclip

def generate_prompt(stock_data: List[Dict]) -> str:
    """
    Constructs a comprehensive 'Deep Research' prompt for an LLM.
    Focuses on Indian Market context, PESTLE, and Management analysis.
    """
    
    prompt = """
Act as a Senior Equity Research Analyst specializing in the Indian Stock Market (NSE/BSE).
I will provide you with a list of stocks (or a single stock) that I am interested in.
I have already done the basic technical screening (RSI, Trends are good).

Your Goal is to perform a "Deep Qualitative Research" (Gut Check) report.
For each stock provided below, please research and analyze the following 360-degree parameters:

1. **Business & Moat**: What exactly does the company do? What is their competitive advantage?
2. **Management Quality**: Who are the promoters/founders? Any history of fraud, political connections, or poor governance? 
3. **PESTLE Analysis**:
   - **Political**: How do current Govt policies (PLI schemes, Infra push) affect them?
   - **Economic**: Impact of inflation/interest rates.
   - **Social**: Changing consumer habits in India.
   - **Technological**: Are they being disrupted?
   - **Legal/Environmental**: Any ongoing court cases or NGT (National Green Tribunal) issues?
4. **Cross-Border & Deals**: Any recent big orders, exports, or mergers?
5. **Large Cap Impact**: How do moves by Reliance, Tata, or Adani affect this specific small cap?

Finally, give a **"High Conviction"** or **"Wait and Watch"** verdict based on this qualitative data.

Here is the Data:
--------------------------------------------------
"""

    for stock in stock_data:
        prompt += f"\nSymbol: {stock['symbol']} ({stock['name']})\n"
        prompt += f"Sector: {stock['sector']} | Market Cap: ₹{stock['marketCap']/10000000:.2f} Cr\n"
        prompt += f"Summary: {stock['summary']}\n"
        
        analysis = stock.get('analysis', {})
        prompt += f"Price: ₹{analysis.get('current_price', 'N/A')}\n"
        prompt += f"Trend: {analysis.get('trend', 'N/A')} | RSI: {analysis.get('rsi', 'N/A')}\n"
        prompt += "--------------------------------------------------\n"

    prompt += """
Please write the report in simple, easy-to-understand language with bullet points. 
Back up your claims with past data or known events where possible.
"""
    
    return prompt

def copy_to_clipboard(text: str):
    try:
        pyperclip.copy(text)
        print("\n[SUCCESS] Prompt copied to clipboard! You can now paste it into ChatGPT/Gemini.")
    except Exception as e:
        print(f"\n[WARNING] Could not copy to clipboard (expected on server): {e}")
        print("Please manually copy the prompt from the file 'generated_prompt.txt'.")
        with open("generated_prompt.txt", "w") as f:
            f.write(text)

def generate_news_prompt(ticker: str, news_data: List[Dict]) -> str:
    """
    Constructs a prompt to analyze recent news and sector trends.
    """
    prompt = f"""
Act as a Senior Market Analyst. I need a quick summary of the latest news for {ticker}.

Here are the recent news headlines and links:
"""
    for item in news_data[:5]: # Top 5 news items
        # Handle nested structure (yfinance often returns news inside 'content')
        if 'content' in item:
            content = item['content']
            title = content.get('title', 'No Title')
            link_obj = content.get('clickThroughUrl') or content.get('canonicalUrl')
            link = link_obj.get('url', 'No Link') if link_obj else 'No Link'
        else:
            # Fallback for flat structure
            title = item.get('title', 'No Title')
            link = item.get('link', 'No Link')
            
        prompt += f"- {title} (Link: {link})\n"

    prompt += f"""
Based on these headlines (and your own knowledge of the Indian market sector for {ticker}), please provide:
1. **Company Pulse**: What is the key narrative right now? (Earnings, New Orders, Legal Issues?)
2. **Sector Trends**: What is happening in this specific industry in India? (Govt Policy, Global Demand?)
3. **Sentiment**: Is the news generally Positive, Negative, or Neutral?

Keep it concise (max 200 words). Use bullet points.
"""
    return prompt
