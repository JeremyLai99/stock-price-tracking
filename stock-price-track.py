# 互動式多重移動平均線股票分析
# 請先安裝: pip install yfinance matplotlib

import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['axes.unicode_minus'] = False
plt.style.use('default')

print("✅ Setup completed successfully")
print("=" * 60)

# 定義移動平均線參數
MA_PERIODS = {
    'MA10': (10, '#FF6B6B', '-'),
    'MA20': (20, '#4ECDC4', '--'),
    'MA50': (50, '#45B7D1', '-.'),
    'MA60': (60, '#FFA07A', ':'),
    'MA200': (200, '#9B59B6', '-.')
}

def create_interactive_chart(symbol, data_6m, data_full):
    """創建互動式圖表"""
    
    # 創建圖表和軸
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # 繪製股價
    price_line, = ax.plot(data_6m.index, data_6m['Close'], 
                          label=f'{symbol} Close Price', 
                          linewidth=3, 
                          color='#2C3E50',
                          zorder=10,
                          picker=True,
                          pickradius=5)
    
    # 儲存所有MA線條
    lines = [price_line]
    labels = [f'{symbol} Close Price']
    
    # 繪製所有移動平均線（初始全部隱藏，但要確保圖例中可見）
    for ma_name, (period, color, style) in MA_PERIODS.items():
        if ma_name in data_6m.columns:
            line, = ax.plot(data_6m.index, data_6m[ma_name], 
                           label=f'{ma_name} ({period}-day)', 
                           linewidth=2.5,  # 增加圖表線條粗細
                           color=color,
                           linestyle=style,
                           alpha=1.0,  # 完全不透明
                           picker=True,
                           pickradius=5,
                           visible=False)  # 初始隱藏
            lines.append(line)
            labels.append(f'{ma_name} ({period}-day)')
    
    # 圖表設定
    ax.set_title(f"{symbol} - 6 Month Price Chart with Multiple Moving Averages", 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Price (USD)", fontsize=12)
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    plt.xticks(rotation=45)
    
    # 添加最新價格標註
    latest_price = data_6m['Close'].iloc[-1]
    ax.annotate(f'Latest: ${latest_price:.2f}', 
                xy=(data_6m.index[-1], latest_price),
                xytext=(10, 10), textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                fontsize=11,
                fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
    
    # 創建可點擊的圖例（確保所有線條樣本都清晰可見）
    leg = ax.legend(loc='upper left', 
                    fontsize=11, 
                    framealpha=0.95,
                    edgecolor='black',
                    fancybox=True,
                    shadow=True)
    
    # 設定圖例可互動，並強制顯示所有線條樣本
    lined = {}  # 將圖例線條映射到圖表線條
    for legline, origline in zip(leg.get_lines(), lines):
        legline.set_picker(True)
        legline.set_pickradius(5)
        # 強制設定圖例中的線條樣本屬性
        legline.set_linewidth(4)  # 圖例中的線條設為粗線
        legline.set_alpha(1.0)  # 完全不透明
        legline.set_visible(True)  # 強制顯示
        # 保持原始顏色和線型
        legline.set_color(origline.get_color())
        legline.set_linestyle(origline.get_linestyle())
        lined[legline] = origline
    
    # 點擊圖例切換線條顯示
    def on_pick(event):
        legline = event.artist
        
        # 檢查是否點擊圖例
        if legline in lined:
            origline = lined[legline]
            visible = not origline.get_visible()
            origline.set_visible(visible)
            
            # 圖表線條顯示/隱藏，但圖例線條保持清晰可見
            fig.canvas.draw()
    
    fig.canvas.mpl_connect('pick_event', on_pick)
    
    # 添加使用說明（移到右上角避免與圖例重疊）
    ax.text(0.98, 0.98, '💡 Click legend to toggle lines', 
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', alpha=0.8))
    
    plt.tight_layout()
    return fig

# 主程式
symbols_input = input("Enter US stock symbols separated by comma (e.g., AAPL,MSFT,TSLA): ")
symbols = [s.strip().upper() for s in symbols_input.split(",")]

print(f"\nWill analyze: {', '.join(symbols)}")
print("=" * 60)

for i, symbol in enumerate(symbols):
    try:
        print(f"\n📊 Analyzing {symbol} ({i+1}/{len(symbols)})")
        print(f"   Downloading data for {symbol}...")
        
        # 下載15個月資料（確保MA200完整）
        data = yf.download(symbol, period="15mo", progress=False)
        
        if data.empty:
            print(f"❌ No data found for {symbol}. Please check if the symbol is correct.")
            print(f"   Skipping {symbol}...\n")
            continue
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        
        if 'Close' not in data.columns or len(data) < 50:
            print(f"⚠️ Insufficient data for {symbol}. Skipping...")
            continue
        
        print(f"   ✅ Successfully downloaded {len(data)} days of data")
        
        # 計算所有移動平均線
        print(f"   Calculating moving averages...")
        for ma_name, (period, _, _) in MA_PERIODS.items():
            data[ma_name] = data['Close'].rolling(window=period).mean()
        
        # 取最近6個月顯示
        data_6m = data.tail(130)
        
        # 創建互動式圖表
        print(f"   Creating interactive chart...")
        fig = create_interactive_chart(symbol, data_6m, data)
        
        plt.show()
        
        # 計算統計資訊
        start_price = data_6m["Close"].iloc[0]
        end_price = data_6m["Close"].iloc[-1]
        return_rate = (end_price - start_price) / start_price * 100
        
        max_price = data_6m["Close"].max()
        min_price = data_6m["Close"].min()
        avg_price = data_6m["Close"].mean()
        volatility = data_6m["Close"].pct_change().std() * np.sqrt(252) * 100
        
        rolling_max = data_6m['Close'].expanding().max()
        drawdown = (data_6m['Close'] - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        print(f"\n📈 {symbol} Analysis Results:")
        print(f"   Latest Price: ${end_price:.2f}")
        print(f"   6-Month Return: {return_rate:+.2f}%")
        print(f"   Average Price: ${avg_price:.2f}")
        print(f"   Period High: ${max_price:.2f}")
        print(f"   Period Low: ${min_price:.2f}")
        print(f"   Price Range: {((max_price-min_price)/min_price*100):.1f}%")
        print(f"   Annualized Volatility: {volatility:.1f}%")
        print(f"   Maximum Drawdown: {max_drawdown:.1f}%")
        
        # 顯示MA資訊
        print(f"\n📊 Moving Averages (Latest Values):")
        for ma_name, (period, _, _) in MA_PERIODS.items():
            if ma_name in data_6m.columns and not pd.isna(data_6m[ma_name].iloc[-1]):
                ma_value = data_6m[ma_name].iloc[-1]
                diff_pct = ((end_price - ma_value) / ma_value) * 100
                print(f"   {ma_name}: ${ma_value:.2f} ({diff_pct:+.2f}% from current)")
        
        # 技術分析
        if 'MA20' in data_6m.columns:
            current_vs_ma20 = data_6m['Close'].iloc[-1] / data_6m['MA20'].iloc[-1]
            if current_vs_ma20 > 1.02:
                trend = "📈 Strong (Price well above MA20)"
            elif current_vs_ma20 > 1.00:
                trend = "📊 Neutral-Bullish"
            elif current_vs_ma20 > 0.98:
                trend = "📊 Neutral-Bearish"
            else:
                trend = "📉 Weak (Price well below MA20)"
            print(f"   Technical Trend: {trend}")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Analysis interrupted by user")
        break
    except Exception as e:
        print(f"❌ Error analyzing {symbol}: {str(e)}")
        print(f"   Skipping {symbol}...")
        import traceback
        traceback.print_exc()
        continue
    
    print("-" * 60)

print(f"\n✅ Analysis completed! Processed {len(symbols)} stocks")
print("\n💡 Tip: Click on legend items to show/hide MA lines")
print("Close all chart windows to exit the program.")