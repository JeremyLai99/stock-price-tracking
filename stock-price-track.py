# Install packages
# pip install yfinance matplotlib


import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

plt.show()
plt.style.use('default')  # Use clean style

print("✅ Setup completed successfully")

# Input stock symbols
symbols_input = input("Enter US stock symbols separated by comma (e.g., AAPL,MSFT,TSLA): ")
symbols = [s.strip().upper() for s in symbols_input.split(",")]

print(f"Will analyze: {', '.join(symbols)}")
print("=" * 50)

# Analyze each stock
for i, symbol in enumerate(symbols):
    try:
        print(f"\n📊 Analyzing {symbol} ({i+1}/{len(symbols)})")
        
        # Download 15 months data from Yahoo Finance (to show complete 200-day MA in 6-month chart)
        data = yf.download(symbol, period="15mo", progress=False)
        
        # Check if data exists
        if data.empty:
            print(f"❌ No data found for {symbol}. Please check the symbol.")
            continue
        
        # Handle MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        
        # Calculate 20-day and 200-day moving averages (using full data)
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['MA200'] = data['Close'].rolling(window=200).mean()
        
        # Only take last 6 months for display
        data_6m = data.tail(130)  # Approximately 6 months of trading days

        # Create the chart (using 6-month data)
        plt.figure(figsize=(6, 3.5))
        
        # Main stock price line
        plt.plot(data_6m.index, data_6m['Close'], 
                label=f'{symbol} Close Price', 
                linewidth=2.5, 
                color='#2E86AB')
        
        # Moving average lines
        plt.plot(data_6m.index, data_6m['MA20'], 
                label='20-Day Moving Average', 
                linestyle='--', 
                linewidth=2, 
                color='#F24236',
                alpha=0.8)
        
        # 200-day moving average (now displays properly)
        plt.plot(data_6m.index, data_6m['MA200'], 
                label='200-Day Moving Average', 
                linestyle=':', 
                linewidth=2, 
                color='#A23B72',
                alpha=0.9)
        
        # Chart formatting
        plt.title(f"{symbol} - 6 Month Price Chart with Moving Averages", 
                 fontsize=14, fontweight='bold', pad=15)
        plt.xlabel("Date", fontsize=10)
        plt.ylabel("Price (USD)", fontsize=10)
        plt.legend(fontsize=9, loc='best')
        plt.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        plt.xticks(rotation=45)
        
        # Add latest price annotation
        latest_price = data_6m['Close'].iloc[-1]
        plt.annotate(f'Latest: ${latest_price:.2f}', 
                    xy=(data_6m.index[-1], latest_price),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8),
                    fontsize=10,
                    arrowprops=dict(arrowstyle='->', color='black', alpha=0.5))
        
        plt.tight_layout()
        plt.show()

        # Calculate statistics (using 6-month data)
        start_price = data_6m["Close"].iloc[0]
        end_price = data_6m["Close"].iloc[-1]
        return_rate = (end_price - start_price) / start_price * 100
        
        max_price = data_6m["Close"].max()
        min_price = data_6m["Close"].min()
        avg_price = data_6m["Close"].mean()
        volatility = data_6m["Close"].pct_change().std() * np.sqrt(252) * 100
        
        # Calculate maximum drawdown
        rolling_max = data_6m['Close'].expanding().max()
        drawdown = (data_6m['Close'] - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        print(f"📈 {symbol} Analysis Results:")
        print(f"   Latest Price: ${end_price:.2f}")
        print(f"   6-Month Return: {return_rate:+.2f}%")
        print(f"   Average Price: ${avg_price:.2f}")
        print(f"   Period High: ${max_price:.2f}")
        print(f"   Period Low: ${min_price:.2f}")
        print(f"   Price Range: {((max_price-min_price)/min_price*100):.1f}%")
        print(f"   Annualized Volatility: {volatility:.1f}%")
        print(f"   Maximum Drawdown: {max_drawdown:.1f}%")
        
        # Technical analysis hint
        current_vs_ma20 = data_6m['Close'].iloc[-1] / data_6m['MA20'].iloc[-1]
        if current_vs_ma20 > 1.02:
            trend = "📈 Strong (Price well above 20-day MA)"
        elif current_vs_ma20 > 1.00:
            trend = "📊 Neutral-Bullish (Price slightly above 20-day MA)"
        elif current_vs_ma20 > 0.98:
            trend = "📊 Neutral-Bearish (Price slightly below 20-day MA)"
        else:
            trend = "📉 Weak (Price well below 20-day MA)"
        
        print(f"   Technical Trend: {trend}")
        
    except Exception as e:
        print(f"❌ Error analyzing {symbol}: {str(e)}")
        continue
    
    print("-" * 60)

print(f"\n✅ Analysis completed! Processed {len(symbols)} stocks")