import sys
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from src.market_data import SAMPLE_TICKERS, filter_small_caps, get_stock_data
from src.analysis import analyze_stock
from src.prompt_generator import generate_prompt, copy_to_clipboard

console = Console()

def main():
    console.print("\n[bold green]🚀 AI Stock Researcher Initialized[/bold green]")
    console.print("[dim]Scanning for Small Cap opportunities...[/dim]\n")

    # 1. Filter Small Caps
    with Progress() as progress:
        task1 = progress.add_task("[cyan]Filtering Small Caps...", total=len(SAMPLE_TICKERS))
        candidates = filter_small_caps(SAMPLE_TICKERS)
        progress.update(task1, completed=len(SAMPLE_TICKERS))

    if not candidates:
        console.print("[red]No small cap candidates found in the sample list.[/red]")
        return

    console.print(f"\n[bold blue]Found {len(candidates)} Candidates. Analyzing Technicals...[/bold blue]")

    # 2. Analyze Technicals
    analyzed_stocks = []
    table = Table(title="Stock Analysis Preview")
    table.add_column("Symbol", style="cyan")
    table.add_column("Price", justify="right")
    table.add_column("Trend", style="magenta")
    table.add_column("RSI", justify="right")
    table.add_column("Signals", style="green")

    with Progress() as progress:
        task2 = progress.add_task("[green]Analyzing...", total=len(candidates))
        
        for stock in candidates:
            hist_data = get_stock_data(stock['symbol'])
            if hist_data is not None:
                analysis = analyze_stock(hist_data)
                stock['analysis'] = analysis
                analyzed_stocks.append(stock)
                
                # Add to preview table
                table.add_row(
                    stock['symbol'],
                    f"${analysis.get('current_price', 0)}",
                    analysis.get('trend', 'Unknown'),
                    str(analysis.get('rsi', 0)),
                    ", ".join(analysis.get('signals', [])) if analysis.get('signals') else "-"
                )
            progress.advance(task2)

    console.print(table)

    # 3. Generate Prompt
    console.print("\n[bold yellow]Generating AI Research Prompt...[/bold yellow]")
    prompt = generate_prompt(analyzed_stocks)
    
    # 4. Copy to Clipboard
    copy_to_clipboard(prompt)
    
    console.print("\n[bold white on green] DONE [/bold white on green]")
    console.print("👉 [bold]Paste the copied prompt into ChatGPT or Gemini to get your investment report![/bold]")

if __name__ == "__main__":
    main()
