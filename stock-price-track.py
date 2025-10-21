import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons
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
    0: '#808080',
    0.236: '#9C27B0',
    0.382: '#2196F3',
    0.5: '#4CAF50',
    0.618: '#FF9800',
    0.786: '#F44336',
    1.0: '#808080'
}

def create_multi_stock_chart(stocks_data):
    """創建多股票切換圖表（使用自訂水平單選按鈕）"""
    symbols = list(stocks_data.keys())
    num_symbols = len(symbols)

    # 創建圖表
    fig = plt.figure(figsize=(14, 10))

    # 優化間距設計
    gs = fig.add_gridspec(2, 1,
                          height_ratios=[3, 1],
                          hspace=0.15,
                          top=0.85,
                          bottom=0.10)

    ax1 = fig.add_subplot(gs[0, 0])  # 價格圖
    ax2 = fig.add_subplot(gs[1, 0], sharex=ax1)  # 成交量圖

    # 建立自訂的水平 Radio Button
    radio_ypos = 0.93
    radio_ax = fig.add_axes([0.05, radio_ypos, 0.9, 0.055])
    radio_ax.set_xlim(0, 1)
    radio_ax.set_ylim(0, 1)
    radio_ax.axis('off')

    # 建立左側時間選項按鈕
    time_ypos = radio_ypos
    time_ax = fig.add_axes([0.01, time_ypos - 0.20, 0.08, 0.20])  # 增加高度以容納按鈕
    time_ax.set_xlim(0, 1)
    time_ax.set_ylim(0, 1)
    time_ax.axis('off')

    # 時間選項
    time_periods = ['1M', '3M', '6M']
    time_period_days = {'1M': 22, '3M': 65, '6M': 130}
    time_buttons = []
    active_time = ['6M']

    for i, period in enumerate(time_periods):
        y_pos = 0.80 - i * 0.25  # 縮小間距以確保按鈕分佈合理
        label = time_ax.text(
            0.5, y_pos, period,
            ha='center', va='center',
            fontsize=11,
            fontweight='bold',
            color='#FF4444' if period == '6M' else '#333333',
            bbox=dict(boxstyle='round,pad=0.4',
                      facecolor='#FFF3CD' if period == '6M' else '#F8F9FA',
                      edgecolor='#FF4444' if period == '6M' else '#CCCCCC',
                      linewidth=2 if period == '6M' else 1),
            transform=time_ax.transAxes
        )
        time_buttons.append(label)

    # 每個選項的間距
    spacing = 1 / max(num_symbols, 1)

    # 儲存文字標籤資料
    radio_buttons = []

    for i, symbol in enumerate(symbols):
        x_pos = (i + 0.5) * spacing
        label = radio_ax.text(
            x_pos, 0.5, symbol,
            ha='center', va='center',
            fontsize=13,
            fontweight='bold',
            color='#FF4444' if i == 0 else '#333333',
            bbox=dict(boxstyle='round,pad=0.5',
                      facecolor='#FFF3CD' if i == 0 else '#F8F9FA',
                      edgecolor='#FF4444' if i == 0 else '#CCCCCC',
                      linewidth=2 if i == 0 else 1),
            transform=radio_ax.transAxes
        )
        radio_buttons.append(label)

    # 第一個預設為選取狀態
    active_index = [0]
    current_stock = {'index': 0}

    # 費波那契工具狀態（每個股票獨立）
    fib_states = {}
    for symbol in stocks_data.keys():
        fib_states[symbol] = {
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
            'ignore_next_click': False
        }

    # 特殊元素（每個股票獨立）
    special_elements = {}
    for symbol in stocks_data.keys():
        special_elements[symbol] = {
            'bb_upper_line': None,
            'bb_lower_line': None,
            'bb_middle_line': None,
            'bb_fill': None,
            'fib_tool': None,
            'lines': [],
            'leg': None,
            'lined': {}
        }

    def get_current_symbol():
        return list(stocks_data.keys())[current_stock['index']]

    def get_current_fib_state():
        return fib_states[get_current_symbol()]

    def get_current_elements():
        return special_elements[get_current_symbol()]

    def clear_axes():
        ax1.clear()
        ax2.clear()

    def draw_stock_chart(symbol):
        clear_axes()
        current_time = active_time[0]
        days = time_period_days[current_time]
        data = stocks_data[symbol]['data_full'].tail(days)  # 動態選擇數據範圍
        fib_state = fib_states[symbol]
        elements = special_elements[symbol]

        # 繪製價格圖
        price_line, = ax1.plot(data.index, data['Close'],
                              label=f'{symbol} Close Price',
                              linewidth=3,
                              color='#2C3E50',
                              zorder=10,
                              picker=True,
                              pickradius=5)
        lines = [price_line]

        # 繪製移動平均線
        for ma_name, (period, color, style) in MA_PERIODS.items():
            if ma_name in data.columns:
                line, = ax1.plot(data.index, data[ma_name],
                                 label=f'{ma_name} ({period}-day)',
                                 linewidth=2.5,
                                 color=color,
                                 linestyle=style,
                                 alpha=1.0,
                                 picker=True,
                                 pickradius=5,
                                 visible=False)
                lines.append(line)

        # 繪製布林通道
        if 'BB_upper' in data.columns and not data['BB_upper'].isnull().all():
            bb_upper, = ax1.plot(data.index, data['BB_upper'],
                                label='Bollinger Bands',
                                linewidth=1.5,
                                color='#FF6B9D',
                                linestyle='--',
                                alpha=0.7,
                                picker=True,
                                pickradius=5,
                                visible=False)
            elements['bb_upper_line'] = bb_upper
            lines.append(bb_upper)

            bb_middle, = ax1.plot(data.index, data['BB_middle'],
                                 linewidth=1,
                                 color='#FF6B9D',
                                 linestyle=':',
                                 alpha=0.5,
                                 visible=False)
            elements['bb_middle_line'] = bb_middle

            bb_lower, = ax1.plot(data.index, data['BB_lower'],
                                linewidth=1.5,
                                color='#FF6B9D',
                                linestyle='--',
                                alpha=0.7,
                                visible=False)
            elements['bb_lower_line'] = bb_lower

            bb_fill = ax1.fill_between(data.index,
                                       data['BB_upper'],
                                       data['BB_lower'],
                                       alpha=0.1,
                                       color='#FF6B9D',
                                       visible=False)
            elements['bb_fill'] = bb_fill

        # 添加費波那契工具
        fib_tool_line, = ax1.plot([], [],
                                  label='[Fib] Fibonacci Tool (Click to Draw)',
                                  linewidth=0,
                                  marker='o',
                                  markersize=8,
                                  color='orange',
                                  picker=True,
                                  pickradius=5)
        elements['fib_tool'] = fib_tool_line
        lines.append(fib_tool_line)

        # 圖表設定
        ax1.set_title(f"{symbol} - {current_time} Price Chart with Technical Indicators",
                      fontsize=16, fontweight='bold', pad=12)
        ax1.set_ylabel("Price (USD)", fontsize=12)
        ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)

        # 最新價格標註
        latest_price = data['Close'].iloc[-1]
        ax1.annotate(f'Latest: ${latest_price:.2f}',
                     xy=(data.index[-1], latest_price),
                     xytext=(10, 10), textcoords='offset points',
                     bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                     fontsize=11,
                     fontweight='bold',
                     arrowprops=dict(arrowstyle='->', color='black', lw=1.5))

        # 繪製成交量圖
        if 'Volume' in data.columns:
            colors = []
            for i in range(len(data)):
                if i == 0:
                    colors.append('#808080')
                else:
                    if data['Close'].iloc[i] >= data['Close'].iloc[i-1]:
                        colors.append('#EF5350')
                    else:
                        colors.append('#26A69A')

            ax2.bar(data.index, data['Volume'],
                    color=colors,
                    alpha=0.7,
                    width=1.0,
                    edgecolor='none')

            ax2.set_ylabel('Volume', fontsize=12, fontweight='bold')
            ax2.set_xlabel('Date', fontsize=12)
            ax2.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, axis='y')
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M' if x >= 1e6 else f'{x/1e3:.0f}K'))

            ax2.text(0.02, 0.95, 'Red = Up Day | Green = Down Day',
                     transform=ax2.transAxes,
                     fontsize=9,
                     verticalalignment='top',
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

        # X 軸日期設定
        ax1.tick_params(labelbottom=False)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=0, ha='center')
        ax2.xaxis.set_tick_params(labelsize=9)

        # 創建圖例
        leg = ax1.legend(loc='upper left',
                         fontsize=11,
                         framealpha=0.95,
                         edgecolor='black',
                         fancybox=True,
                         shadow=True)
        elements['leg'] = leg
        elements['lines'] = lines

        # 設定圖例可互動
        lined = {}
        for legline, origline in zip(leg.get_lines(), lines):
            legline.set_picker(True)
            legline.set_pickradius(5)
            legline.set_linewidth(4)
            legline.set_alpha(1.0)
            legline.set_visible(True)
            try:
                legline.set_color(origline.get_color())
            except Exception:
                pass
            try:
                legline.set_linestyle(origline.get_linestyle())
            except Exception:
                pass
            lined[legline] = origline
        elements['lined'] = lined

        # 恢復已繪製的費波那契線條
        if len(fib_state['final_lines']) > 0:
            for line in fib_state['final_lines']:
                if line not in ax1.lines:
                    ax1.add_line(line)
            for text in fib_state['final_texts']:
                ax1.add_artist(text)

        # 添加使用說明
        ax1.text(0.98, 0.98, 'TIP: Click legend to toggle | Fib Tool: Click-Move-Click',
                 transform=ax1.transAxes,
                 fontsize=9,
                 verticalalignment='top',
                 horizontalalignment='right',
                 bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', alpha=0.8))

        fig.canvas.draw_idle()

    # 費波那契工具函數
    def clear_fib_preview():
        fib_state = get_current_fib_state()
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
        fib_state = get_current_fib_state()
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
        fib_state = get_current_fib_state()
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
        fib_state = get_current_fib_state()
        symbol = get_current_symbol()
        current_time = active_time[0]
        days = time_period_days[current_time]
        data_display = stocks_data[symbol]['data_full'].tail(days)

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

            text = ax1.text(data_display.index[-1], price,
                            f'  {label} (${price:.2f})',
                            verticalalignment='center',
                            color=color,
                            fontsize=8 if is_preview else 9,
                            fontweight='bold' if level == 0.618 else 'normal',
                            alpha=alpha_val + 0.2)
            texts_list.append(text)

    def on_fib_click(event):
        fib_state = get_current_fib_state()
        if not fib_state['active']:
            return
        if fib_state['ignore_next_click']:
            fib_state['ignore_next_click'] = False
            return
        if event.inaxes != ax1:
            return
        xdata = event.xdata
        ydata = event.ydata
        if xdata is None or ydata is None:
            return
        if fib_state['step'] == 0:
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
            fig.canvas.draw_idle()

    def on_fib_motion(event):
        fib_state = get_current_fib_state()
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
        fib_state = get_current_fib_state()
        if event.key == 'escape':
            if fib_state['active']:
                fib_state['active'] = False
                fib_state['step'] = 0
                fib_state['point1'] = None
                fib_state['point2'] = None
                fib_state['ignore_next_click'] = False
                clear_fib_preview()
                for marker in fib_state['markers']:
                    try:
                        marker.remove()
                    except (ValueError, AttributeError):
                        pass
                fib_state['markers'] = []
                if fib_state['status_text'] is not None:
                    try:
                        fib_state['status_text'].remove()
                    except (ValueError, AttributeError):
                        pass
                    fib_state['status_text'] = None
                fig.canvas.draw()
            elif len(fib_state['final_lines']) > 0 or len(fib_state['final_texts']) > 0 or len(fib_state['markers']) > 0:
                clear_fib_final()
                if fib_state['status_text'] is not None:
                    try:
                        fib_state['status_text'].remove()
                    except (ValueError, AttributeError):
                        pass
                    fib_state['status_text'] = None
                fig.canvas.draw()

    def on_pick(event):
        elements = get_current_elements()
        fib_state = get_current_fib_state()
        legline = event.artist
        if legline in elements['lined']:
            origline = elements['lined'][legline]
            if origline == elements.get('fib_tool'):
                if len(fib_state['final_lines']) > 0 or len(fib_state['final_texts']) > 0 or len(fib_state['markers']) > 0:
                    clear_fib_final()
                    if fib_state['status_text'] is not None:
                        try:
                            fib_state['status_text'].remove()
                        except (ValueError, AttributeError):
                            pass
                        fib_state['status_text'] = None
                if not fib_state['active']:
                    fib_state['active'] = True
                    fib_state['step'] = 0
                    fib_state['point1'] = None
                    fib_state['point2'] = None
                    fib_state['ignore_next_click'] = True
                    clear_fib_final()
                    clear_fib_preview()
                    update_status_text('[Fib] Step 1: Click on the FIRST point (High or Low) | ESC to cancel')
                    fig.canvas.draw_idle()
                return
            visible = not origline.get_visible()
            origline.set_visible(visible)
            if origline == elements.get('bb_upper_line'):
                if elements.get('bb_lower_line') is not None:
                    elements['bb_lower_line'].set_visible(visible)
                if elements.get('bb_middle_line') is not None:
                    elements['bb_middle_line'].set_visible(visible)
                if elements.get('bb_fill') is not None:
                    elements['bb_fill'].set_visible(visible)
            fig.canvas.draw()

    def on_button_click(event):
        time_clicked = False
        for i, label in enumerate(time_buttons):
            contains, _ = label.contains(event)
            if contains:
                time_clicked = True
                old_time = active_time[0]
                active_time[0] = time_periods[i]
                print(f"Time period changed from {old_time} to {active_time[0]}")
                for j, lbl in enumerate(time_buttons):
                    if j == i:
                        lbl.set_color('#FF4444')
                        lbl.set_bbox(dict(boxstyle='round,pad=0.4',
                                          facecolor='#FFF3CD',
                                          edgecolor='#FF4444',
                                          linewidth=2))
                    else:
                        lbl.set_color('#333333')
                        lbl.set_bbox(dict(boxstyle='round,pad=0.4',
                                          facecolor='#F8F9FA',
                                          edgecolor='#CCCCCC',
                                          linewidth=1))
                current_symbol = get_current_symbol()
                print(f"Redrawing chart for {current_symbol}")
                draw_stock_chart(current_symbol)
                fig.canvas.draw()
                return
        if not time_clicked:
            for i, label in enumerate(radio_buttons):
                contains, _ = label.contains(event)
                if contains:
                    active_index[0] = i
                    for j, lbl in enumerate(radio_buttons):
                        if j == i:
                            lbl.set_color('#FF4444')
                            lbl.set_bbox(dict(boxstyle='round,pad=0.5',
                                              facecolor='#FFF3CD',
                                              edgecolor='#FF4444',
                                              linewidth=2))
                        else:
                            lbl.set_color('#333333')
                            lbl.set_bbox(dict(boxstyle='round,pad=0.5',
                                              facecolor='#F8F9FA',
                                              edgecolor='#CCCCCC',
                                              linewidth=1))
                    current_stock['index'] = i
                    draw_stock_chart(symbols[i])
                    fig.canvas.draw()
                    break

    # 綁定事件
    fig.canvas.mpl_connect('button_press_event', on_button_click)
    fig.canvas.mpl_connect('pick_event', on_pick)
    fig.canvas.mpl_connect('button_press_event', on_fib_click)
    fig.canvas.mpl_connect('motion_notify_event', on_fib_motion)
    fig.canvas.mpl_connect('key_press_event', on_key_press)

    # 添加說明文字
    if num_symbols > 1:
        fig.text(0.5, 0.02, f'[Time Period] Select time range on left | [Stocks] Select stock above to switch | [Legend] Click to toggle indicators',
                 ha='center', fontsize=9, style='italic', color='#666666')
    else:
        fig.text(0.5, 0.02, f'[Time Period] Select time range on left | [Legend] Click to toggle indicators',
                 ha='center', fontsize=9, style='italic', color='#666666')

    # 初始繪製第一個股票
    if len(symbols) > 0:
        draw_stock_chart(symbols[0])

    return fig, radio_buttons

# 主程式
symbols_input = input("Enter US stock symbols separated by comma (e.g., AAPL,MSFT,TSLA): ")
symbols = [s.strip().upper() for s in symbols_input.split(",")]

print(f"\nWill analyze: {', '.join(symbols)}")
print("=" * 60)

# 儲存所有股票數據
stocks_data = {}

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
        stocks_data[symbol] = {
            'data_full': data
        }
        start_price = data.tail(130)["Close"].iloc[0]
        end_price = data["Close"].iloc[-1]
        return_rate = (end_price - start_price) / start_price * 100
        max_price = data.tail(130)["Close"].max()
        min_price = data.tail(130)["Close"].min()
        avg_price = data.tail(130)["Close"].mean()
        volatility = data.tail(130)["Close"].pct_change().std() * np.sqrt(252) * 100
        rolling_max = data.tail(130)['Close'].expanding().max()
        drawdown = (data.tail(130)['Close'] - rolling_max) / rolling_max * 100
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
            if ma_name in data.columns and not pd.isna(data[ma_name].iloc[-1]):
                ma_value = data[ma_name].iloc[-1]
                diff_pct = ((end_price - ma_value) / ma_value) * 100
                print(f"   {ma_name}: ${ma_value:.2f} ({diff_pct:+.2f}% from current)")
        if 'MA20' in data.columns:
            current_vs_ma20 = data['Close'].iloc[-1] / data['MA20'].iloc[-1]
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

print(f"\n[OK] Analysis completed! Processed {len(stocks_data)} stocks")

if len(stocks_data) > 0:
    print("\n[TIP] Click on legend items to show/hide MA lines")
    print("[TIP] Click 'Fibonacci Tool' in legend to draw retracement levels")
    if len(stocks_data) > 1:
        print(f"[TIP] Use radio buttons at the top to switch between {len(stocks_data)} stocks")
    print("\n[INFO] Creating interactive chart...")
    fig, radio_buttons = create_multi_stock_chart(stocks_data)
    print("[INFO] Chart displayed. Close the chart window to exit the program.")
    plt.show()
else:
    print("\n[X] No valid stock data to display.")