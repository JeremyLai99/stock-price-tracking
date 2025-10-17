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

print("Setup completed successfully")
print("=" * 60)

# 定義移動平均線參數
MA_PERIODS = {
    'MA10': (10, '#FF6B6B', '-'),
    'MA20': (20, '#4ECDC4', '--'),
    'MA50': (50, '#45B7D1', '-.'),
    'MA60': (60, '#FFA07A', ':'),
    'MA200': (200, '#9B59B6', '-.')
}

# 布林通道參數
BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2

# 費波那契回調比例
FIBONACCI_LEVELS = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
FIBONACCI_COLORS = {
    0: '#808080',      # 0% - 灰色
    0.236: '#9C27B0',  # 23.6% - 紫色
    0.382: '#2196F3',  # 38.2% - 藍色
    0.5: '#4CAF50',    # 50% - 綠色
    0.618: '#FF9800',  # 61.8% - 橙色（黃金比例）
    0.786: '#F44336',  # 78.6% - 紅色
    1.0: '#808080'     # 100% - 灰色
}

# 費波那契工具狀態
fib_state = {
    'active': False,
    'step': 0,
    'point1': None,
    'point2': None,
    'preview_lines': [],
    'preview_texts': [],
    'final_lines': [],
    'final_texts': [],
    'markers': [],
    'connect_line': None,
    'status_text': None,
    'ignore_next_click': False  # 用來忽略圖例點擊後的下一次點擊
}

def create_interactive_chart(symbol, data_6m, data_full):
    """創建互動式圖表"""
    
    # 創建圖表和軸（上方為價格圖，下方為成交量圖）
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), 
                                     gridspec_kw={'height_ratios': [3, 1]},
                                     sharex=True)
    
    # 重置費波那契狀態
    fib_state['active'] = False
    fib_state['step'] = 0
    fib_state['point1'] = None
    fib_state['point2'] = None
    fib_state['preview_lines'] = []
    fib_state['preview_texts'] = []
    fib_state['final_lines'] = []
    fib_state['final_texts'] = []
    fib_state['markers'] = []
    fib_state['connect_line'] = None
    fib_state['status_text'] = None
    fib_state['ignore_next_click'] = False
    
    # 初始化 special_elements 字典
    special_elements = {
        'bb_upper_line': None,
        'bb_lower_line': None,
        'bb_middle_line': None,
        'bb_fill': None,
        'fib_tool': None
    }
    
    # === 上方圖表：股價 + MA + 布林通道 ===
    
    # 繪製股價
    price_line, = ax1.plot(data_6m.index, data_6m['Close'], 
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
            line, = ax1.plot(data_6m.index, data_6m[ma_name], 
                           label=f'{ma_name} ({period}-day)', 
                           linewidth=2.5,
                           color=color,
                           linestyle=style,
                           alpha=1.0,
                           picker=True,
                           pickradius=5,
                           visible=False)
            lines.append(line)
            labels.append(f'{ma_name} ({period}-day)')
    
    # 繪製布林通道（預設隱藏）
    if 'BB_upper' in data_6m.columns and not data_6m['BB_upper'].isnull().all():
        # 上軌
        bb_upper, = ax1.plot(data_6m.index, data_6m['BB_upper'],
                            label='Bollinger Bands',
                            linewidth=1.5,
                            color='#FF6B9D',
                            linestyle='--',
                            alpha=0.7,
                            picker=True,
                            pickradius=5,
                            visible=False)
        special_elements['bb_upper_line'] = bb_upper
        lines.append(bb_upper)
        labels.append('Bollinger Bands')
        
        # 中軌（通常與MA20相同，可選擇是否顯示）
        bb_middle, = ax1.plot(data_6m.index, data_6m['BB_middle'],
                             linewidth=1,
                             color='#FF6B9D',
                             linestyle=':',
                             alpha=0.5,
                             visible=False)
        special_elements['bb_middle_line'] = bb_middle
        
        # 下軌
        bb_lower, = ax1.plot(data_6m.index, data_6m['BB_lower'],
                            linewidth=1.5,
                            color='#FF6B9D',
                            linestyle='--',
                            alpha=0.7,
                            visible=False)
        special_elements['bb_lower_line'] = bb_lower
        
        # 填充區域
        bb_fill = ax1.fill_between(data_6m.index, 
                                    data_6m['BB_upper'], 
                                    data_6m['BB_lower'],
                                    alpha=0.1,
                                    color='#FF6B9D',
                                    visible=False)
        special_elements['bb_fill'] = bb_fill
    
    # 添加費波那契工具到圖例（使用隱藏線條）
    fib_tool_line, = ax1.plot([], [], 
                             label='[Fib] Fibonacci Tool (Click to Draw)',
                             linewidth=0,
                             marker='o',
                             markersize=8,
                             color='orange',
                             picker=True,
                             pickradius=5)
    special_elements['fib_tool'] = fib_tool_line
    lines.append(fib_tool_line)
    labels.append('[Fib] Fibonacci Tool (Click to Draw)')
    
    # 圖表設定
    ax1.set_title(f"{symbol} - 6 Month Price Chart with Technical Indicators", 
                 fontsize=16, fontweight='bold', pad=20)
    ax1.set_ylabel("Price (USD)", fontsize=12)
    ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    
    # 添加最新價格標註
    latest_price = data_6m['Close'].iloc[-1]
    ax1.annotate(f'Latest: ${latest_price:.2f}', 
                xy=(data_6m.index[-1], latest_price),
                xytext=(10, 10), textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                fontsize=11,
                fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
    
    # === 下方圖表：成交量 ===
    
    if 'Volume' in data_6m.columns:
        # 計算顏色（漲紅跌綠）
        colors = []
        for i in range(len(data_6m)):
            if i == 0:
                colors.append('#808080')
            else:
                if data_6m['Close'].iloc[i] >= data_6m['Close'].iloc[i-1]:
                    colors.append('#EF5350')
                else:
                    colors.append('#26A69A')
        
        # 繪製成交量柱狀圖
        ax2.bar(data_6m.index, data_6m['Volume'], 
                color=colors, 
                alpha=0.7,
                width=1.0,
                edgecolor='none')
        
        ax2.set_ylabel('Volume', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, axis='y')
        
        # 格式化成交量數字
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M' if x >= 1e6 else f'{x/1e3:.0f}K'))
        
        # 添加成交量說明
        ax2.text(0.02, 0.95, 'Red = Up Day | Green = Down Day', 
                transform=ax2.transAxes,
                fontsize=9,
                verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    plt.xticks(rotation=45)
    
    # 創建可點擊的圖例
    leg = ax1.legend(loc='upper left', 
                    fontsize=11, 
                    framealpha=0.95,
                    edgecolor='black',
                    fancybox=True,
                    shadow=True)
    
    # 設定圖例可互動
    lined = {}
    for legline, origline in zip(leg.get_lines(), lines):
        legline.set_picker(True)
        legline.set_pickradius(5)
        legline.set_linewidth(4)
        legline.set_alpha(1.0)
        legline.set_visible(True)
        legline.set_color(origline.get_color())
        legline.set_linestyle(origline.get_linestyle())
        lined[legline] = origline
    
    # === 費波那契工具互動功能 ===
    
    def clear_fib_preview():
        """清除預覽線條"""
        for line in fib_state['preview_lines']:
            try:
                line.remove()
            except (ValueError, AttributeError):
                pass
        for text in fib_state['preview_texts']:
            try:
                text.remove()
            except (ValueError, AttributeError):
                pass
        fib_state['preview_lines'] = []
        fib_state['preview_texts'] = []
        if fib_state['connect_line'] is not None:
            try:
                fib_state['connect_line'].remove()
            except (ValueError, AttributeError):
                pass
            fib_state['connect_line'] = None
    
    def clear_fib_final():
        """清除最終線條"""
        for line in fib_state['final_lines']:
            try:
                line.remove()
            except (ValueError, AttributeError):
                pass
        for text in fib_state['final_texts']:
            try:
                text.remove()
            except (ValueError, AttributeError):
                pass
        for marker in fib_state['markers']:
            try:
                marker.remove()
            except (ValueError, AttributeError):
                pass
        fib_state['final_lines'] = []
        fib_state['final_texts'] = []
        fib_state['markers'] = []
    
    def update_status_text(message):
        """更新狀態提示"""
        if fib_state['status_text'] is not None:
            try:
                fib_state['status_text'].remove()
            except (ValueError, AttributeError):
                pass
        fib_state['status_text'] = ax1.text(0.5, 1.02, message,
                                            transform=ax1.transAxes,
                                            ha='center',
                                            fontsize=10,
                                            bbox=dict(boxstyle='round,pad=0.5', 
                                                     facecolor='lightyellow', 
                                                     alpha=0.9))
    
    def draw_fib_lines(x1, y1, x2, y2, is_preview=True):
        """繪製費波那契線"""
        high_price = max(y1, y2)
        low_price = min(y1, y2)
        price_range = high_price - low_price
        
        if price_range < 0.01:
            return
        
        lines_list = fib_state['preview_lines'] if is_preview else fib_state['final_lines']
        texts_list = fib_state['preview_texts'] if is_preview else fib_state['final_texts']
        alpha_val = 0.4 if is_preview else 0.8
        linestyle = ':' if is_preview else '--'
        linewidth = 1 if is_preview else 1.5
        
        for level in FIBONACCI_LEVELS:
            price = high_price - (price_range * level)
            color = FIBONACCI_COLORS[level]
            
            line = ax1.axhline(y=price, 
                              color=color, 
                              linestyle=linestyle,
                              linewidth=linewidth if level != 0.618 else linewidth + 0.5,
                              alpha=alpha_val)
            lines_list.append(line)
            
            percentage = level * 100
            label = f'{percentage:.1f}%'
            if level == 0.618 and not is_preview:
                label += ' *GOLD*'
            
            text = ax1.text(data_6m.index[-1], price, 
                           f'  {label} (${price:.2f})',
                           verticalalignment='center',
                           color=color,
                           fontsize=8 if is_preview else 9,
                           fontweight='bold' if level == 0.618 else 'normal',
                           alpha=alpha_val + 0.2)
            texts_list.append(text)
    
    def on_fib_click(event):
        """處理費波那契工具的點擊"""
        print(f"Fib click event: Active={fib_state['active']}, Step={fib_state['step']}, Ignore={fib_state['ignore_next_click']}")  # 調試
        
        if not fib_state['active']:
            return
        
        # 如果需要忽略這次點擊（剛從圖例啟動）
        if fib_state['ignore_next_click']:
            print("Ignoring first click after activation")
            fib_state['ignore_next_click'] = False
            return
        
        # 必須點擊在圖表範圍內
        if event.inaxes != ax1:
            return
        
        xdata = event.xdata
        ydata = event.ydata
        
        if xdata is None or ydata is None:
            return
        
        if fib_state['step'] == 0:
            print(f"Setting first point at ({xdata}, {ydata})")
            fib_state['point1'] = (xdata, ydata)
            fib_state['step'] = 1
            
            marker = ax1.plot(xdata, ydata, 'ro', markersize=8, zorder=20)[0]
            fib_state['markers'].append(marker)
            
            vline = ax1.axvline(x=xdata, color='red', linestyle=':', alpha=0.5, linewidth=1)
            hline = ax1.axhline(y=ydata, color='red', linestyle=':', alpha=0.5, linewidth=1)
            fib_state['markers'].extend([vline, hline])
            
            update_status_text(f'[Fib] Step 2: Move mouse to preview, click to confirm | First: ${ydata:.2f} | ESC to cancel')
            fig.canvas.draw_idle()
            
        elif fib_state['step'] == 1:
            print(f"Setting second point at ({xdata}, {ydata})")
            fib_state['point2'] = (xdata, ydata)
            fib_state['step'] = 2
            
            marker = ax1.plot(xdata, ydata, 'bo', markersize=8, zorder=20)[0]
            fib_state['markers'].append(marker)
            
            vline = ax1.axvline(x=xdata, color='blue', linestyle=':', alpha=0.5, linewidth=1)
            hline = ax1.axhline(y=ydata, color='blue', linestyle=':', alpha=0.5, linewidth=1)
            fib_state['markers'].extend([vline, hline])
            
            clear_fib_preview()
            x1, y1 = fib_state['point1']
            x2, y2 = fib_state['point2']
            draw_fib_lines(x1, y1, x2, y2, is_preview=False)
            
            fib_state['connect_line'] = ax1.plot([x1, x2], [y1, y2], 
                                                  'k--', alpha=0.3, linewidth=1)[0]
            fib_state['final_lines'].append(fib_state['connect_line'])
            
            high = max(y1, y2)
            low = min(y1, y2)
            update_status_text(f'[OK] Fibonacci set! High: ${high:.2f} | Low: ${low:.2f} | Range: ${high-low:.2f} | Click tool to redraw')
            
            fib_state['active'] = False
            print(f"Fibonacci completed. Active now: {fib_state['active']}")
            fig.canvas.draw_idle()
    
    def on_fib_motion(event):
        """處理滑鼠移動（即時預覽）"""
        if not fib_state['active'] or fib_state['step'] != 1 or event.inaxes != ax1:
            return
        
        xdata = event.xdata
        ydata = event.ydata
        
        if xdata is None or ydata is None:
            return
        
        clear_fib_preview()
        
        x1, y1 = fib_state['point1']
        draw_fib_lines(x1, y1, xdata, ydata, is_preview=True)
        
        fib_state['connect_line'] = ax1.plot([x1, xdata], [y1, ydata], 
                                              'gray', linestyle=':', alpha=0.3, linewidth=1)[0]
        fib_state['preview_lines'].append(fib_state['connect_line'])
        
        fig.canvas.draw_idle()
    
    def on_key_press(event):
        """處理鍵盤事件"""
        # 調試：打印按鍵信息
        print(f"Key pressed: {event.key}, Fib active: {fib_state['active']}")
        
        if event.key == 'escape':
            # 情況1：工具啟動中，取消繪製過程
            if fib_state['active']:
                print("ESC detected - canceling Fibonacci tool (drawing in progress)")
                
                # 重置費波那契工具狀態
                fib_state['active'] = False
                fib_state['step'] = 0
                fib_state['point1'] = None
                fib_state['point2'] = None
                fib_state['ignore_next_click'] = False
                
                # 清除預覽線條
                clear_fib_preview()
                
                # 清除所有標記（紅點、藍點、十字線）
                for marker in fib_state['markers']:
                    try:
                        marker.remove()
                    except (ValueError, AttributeError):
                        pass
                fib_state['markers'] = []
                
                # 清除狀態文字
                if fib_state['status_text'] is not None:
                    try:
                        fib_state['status_text'].remove()
                    except (ValueError, AttributeError):
                        pass
                    fib_state['status_text'] = None
                
                print("Fibonacci tool canceled and cleared")
                
                # 強制重繪圖表
                fig.canvas.draw()
            
            # 情況2：已完成繪製，清除已繪製的費波那契線條
            elif len(fib_state['final_lines']) > 0 or len(fib_state['final_texts']) > 0 or len(fib_state['markers']) > 0:
                print("ESC detected - clearing completed Fibonacci lines")
                
                clear_fib_final()
                
                # 清除狀態文字
                if fib_state['status_text'] is not None:
                    try:
                        fib_state['status_text'].remove()
                    except (ValueError, AttributeError):
                        pass
                    fib_state['status_text'] = None
                
                print("Completed Fibonacci lines cleared")
                
                # 強制重繪圖表
                fig.canvas.draw()
    
    def on_pick(event):
        """點擊圖例切換線條顯示"""
        legline = event.artist
        
        if legline in lined:
            origline = lined[legline]
            
            # 如果點擊費波那契工具
            if origline == special_elements['fib_tool']:
                # 如果已有繪製完成的費波那契線條，先清除
                if len(fib_state['final_lines']) > 0 or len(fib_state['final_texts']) > 0 or len(fib_state['markers']) > 0:
                    print("Clearing existing Fibonacci lines before activating tool...")
                    clear_fib_final()
                    if fib_state['status_text'] is not None:
                        try:
                            fib_state['status_text'].remove()
                        except (ValueError, AttributeError):
                            pass
                        fib_state['status_text'] = None
                
                # 啟動工具
                if not fib_state['active']:
                    print("Activating Fibonacci tool...")  # 調試訊息
                    fib_state['active'] = True
                    fib_state['step'] = 0
                    fib_state['point1'] = None
                    fib_state['point2'] = None
                    fib_state['ignore_next_click'] = True  # 忽略這次圖例點擊
                    clear_fib_final()
                    clear_fib_preview()
                    update_status_text('[Fib] Step 1: Click on the FIRST point (High or Low) | ESC to cancel')
                    print(f"Fibonacci tool activated. Active: {fib_state['active']}, Step: {fib_state['step']}")  # 調試訊息
                    fig.canvas.draw_idle()
                return
            
            # 切換線條顯示
            visible = not origline.get_visible()
            origline.set_visible(visible)
            
            # 如果是布林通道，同步切換所有相關元素
            if origline == special_elements['bb_upper_line']:
                if special_elements['bb_lower_line'] is not None:
                    special_elements['bb_lower_line'].set_visible(visible)
                if special_elements['bb_middle_line'] is not None:
                    special_elements['bb_middle_line'].set_visible(visible)
                if special_elements['bb_fill'] is not None:
                    special_elements['bb_fill'].set_visible(visible)
            
            fig.canvas.draw()
    
    fig.canvas.mpl_connect('pick_event', on_pick)
    fig.canvas.mpl_connect('button_press_event', on_fib_click)
    fig.canvas.mpl_connect('motion_notify_event', on_fib_motion)
    fig.canvas.mpl_connect('key_press_event', on_key_press)
    
    # 添加使用說明
    ax1.text(0.98, 0.98, 'TIP: Click legend to toggle | Fib Tool: Click-Move-Click', 
            transform=ax1.transAxes,
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
        print(f"\n[Analyzing] {symbol} ({i+1}/{len(symbols)})")
        print(f"   Downloading data for {symbol}...")
        
        data = yf.download(symbol, period="15mo", progress=False)
        
        if data.empty:
            print(f"[X] No data found for {symbol}. Please check if the symbol is correct.")
            print(f"   Skipping {symbol}...\n")
            continue
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        
        if 'Close' not in data.columns or len(data) < 50:
            print(f"[!] Insufficient data for {symbol}. Skipping...")
            continue
        
        print(f"   [OK] Successfully downloaded {len(data)} days of data")
        
        print(f"   Calculating moving averages...")
        for ma_name, (period, _, _) in MA_PERIODS.items():
            data[ma_name] = data['Close'].rolling(window=period).mean()
        
        print(f"   Calculating Bollinger Bands...")
        data['BB_middle'] = data['Close'].rolling(window=BOLLINGER_PERIOD).mean()
        data['BB_std'] = data['Close'].rolling(window=BOLLINGER_PERIOD).std()
        data['BB_upper'] = data['BB_middle'] + (BOLLINGER_STD * data['BB_std'])
        data['BB_lower'] = data['BB_middle'] - (BOLLINGER_STD * data['BB_std'])
        
        if not data['BB_upper'].isnull().all():
            print(f"   [OK] Bollinger Bands calculated successfully")
        else:
            print(f"   [!] Warning: Bollinger Bands calculation may have issues")
        
        data_6m = data.tail(130)
        
        print(f"   Creating interactive chart...")
        
        fig = create_interactive_chart(symbol, data_6m, data)
        
        print(f"   [OK] Chart created successfully!")
        plt.show(block=False)  # 不阻塞，讓程式繼續執行
        plt.pause(0.1)  # 短暫暫停確保視窗顯示
        
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
        
        print(f"\n[Results] {symbol} Analysis Results:")
        print(f"   Latest Price: ${end_price:.2f}")
        print(f"   6-Month Return: {return_rate:+.2f}%")
        print(f"   Average Price: ${avg_price:.2f}")
        print(f"   Period High: ${max_price:.2f}")
        print(f"   Period Low: ${min_price:.2f}")
        print(f"   Price Range: {((max_price-min_price)/min_price*100):.1f}%")
        print(f"   Annualized Volatility: {volatility:.1f}%")
        print(f"   Maximum Drawdown: {max_drawdown:.1f}%")
        
        print(f"\n[MA Values] Moving Averages (Latest Values):")
        for ma_name, (period, _, _) in MA_PERIODS.items():
            if ma_name in data_6m.columns and not pd.isna(data_6m[ma_name].iloc[-1]):
                ma_value = data_6m[ma_name].iloc[-1]
                diff_pct = ((end_price - ma_value) / ma_value) * 100
                print(f"   {ma_name}: ${ma_value:.2f} ({diff_pct:+.2f}% from current)")
        
        if 'MA20' in data_6m.columns:
            current_vs_ma20 = data_6m['Close'].iloc[-1] / data_6m['MA20'].iloc[-1]
            if current_vs_ma20 > 1.02:
                trend = "[++] Strong (Price well above MA20)"
            elif current_vs_ma20 > 1.00:
                trend = "[+] Neutral-Bullish"
            elif current_vs_ma20 > 0.98:
                trend = "[-] Neutral-Bearish"
            else:
                trend = "[--] Weak (Price well below MA20)"
            print(f"   Technical Trend: {trend}")
        
    except KeyboardInterrupt:
        print(f"\n[!] Analysis interrupted by user")
        break
    except Exception as e:
        print(f"[X] Error analyzing {symbol}: {str(e)}")
        print(f"   Skipping {symbol}...")
        import traceback
        traceback.print_exc()
        continue
    
    print("-" * 60)

print(f"\n[OK] Analysis completed! Processed {len(symbols)} stocks")
print("\n[TIP] Click on legend items to show/hide MA lines")
print("[TIP] Click 'Fibonacci Tool' in legend to draw retracement levels")
print("\n[INFO] All charts are now displayed. Close all chart windows to exit the program.")

# 保持圖表視窗開啟，直到使用者關閉所有視窗
plt.show()