import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- TRANSLATIONS DICTIONARY ---
LANGUAGES = {
    "English": {
        "sb_header_1": "💼 Portfolio Input",
        "sb_desc_1": "Manage your stock holdings below. You can directly edit the table, add new rows, or delete existing ones.",
        "col_ticker": "Ticker",
        "col_shares": "Shares",
        "col_price": "Avg Price",
        "col_leverage": "Leverage",
        "col_yield": "Yield %",
        "col_yield_help": "Override auto-yield",
        "sb_header_2": "⚖️ Leverage & Debt",
        "margin_debt": "Total Margin/Debt (NT$)",
        "margin_rate": "Margin Interest Rate (%)",
        "fetching_prices": "Fetching live prices and 1-yr yields...",
        "main_title": "📊 Quantitative Portfolio & Macro Analyzer",
        "tab_1": "My Portfolio & Leverage",
        "tab_2": "Macro Environment",
        "tab_3": "Growth Projections",
        "port_overview": "Portfolio Overview",
        "total_assets": "Total Asset Value",
        "net_equity": "Net Equity",
        "unrealized_pl": "Total Unrealized P/L",
        "lev_ratio": "Leverage Ratio",
        "warn_lev": "Warning: High Leverage!",
        "healthy_lev": "Healthy",
        "holdings_detail": "Holdings Detail",
        "asset_alloc": "Asset Allocation",
        "no_holdings": "Please enter your holdings in the sidebar to see your portfolio analysis.",
        "macro_header": "Macro-Economic Indicators (1-Year Trend)",
        "fetching_macro": "Fetching macro indicators from Yahoo Finance...",
        "growth_header": "Future Portfolio Growth Estimator",
        "growth_desc": "Project your equity growth over time. Each holding grows at its **individual Expected Yield** (automatically calculated from 1-year historical returns unless overridden).",
        "years_project": "Years to Project",
        "annual_contrib": "Additional Annual Contribution (NT$)",
        "proj_engine": "💡 **Projection Engine:** Individual holdings grow at their specific yields. Your unallocated cash (new contributions minus margin interest) is assumed to grow at your portfolio's current weighted average yield of **{:.2f}%**.",
        "proj_chart_title": "Portfolio Composition Over Time (Individual Yield Models)",
        "proj_success": "📈 After **{} years**, contributing **NT${:,.0f}** yearly, your Net Equity is estimated to be **NT${:,.2f}**.",
        "proj_warning": "Your total asset value is 0. Add holdings in the sidebar to see projections.",
        "macro_meter_title": "🌡️ Market Sentiment:",
        "status_high_risk": "High Risk / Fear Driven (Protective assets and volatility are elevated)",
        "status_complacent": "Over-Optimistic (Low volatility and low yields indicate market complacency)",
        "status_neutral": "Neutral / Normal Environment",
        "meter_reason": "Drivers:",
        "rs_vix_high": "VIX > 25 (High Fear)",
        "rs_vix_low": "VIX < 15 (Complacency)",
        "rs_tnx_high": "10-Yr Yield > 4.5% (Tightening)",
        "rs_tnx_low": "10-Yr Yield < 3.5% (Easing)",
        "rs_oil_high": "Oil > $85 (Inflation Risk)",
        "rs_oil_low": "Oil < $70 (Low Energy Cost)",
        "rs_gold_high": "Gold Surge (Safe Haven Buying)",
        "rs_gold_low": "Gold Weakness (Risk-On)"
    },
    "繁體中文": {
        "sb_header_1": "💼 投資組合輸入",
        "sb_desc_1": "在下方管理您的持股。您可以直接編輯表格，新增或刪除資料列。",
        "col_ticker": "股票代號",
        "col_shares": "股數",
        "col_price": "平均買價",
        "col_leverage": "槓桿倍數",
        "col_yield": "預期殖利率 %",
        "col_yield_help": "手動覆寫自動計算的殖利率",
        "sb_header_2": "⚖️ 槓桿與債務",
        "margin_debt": "總融資/債務金額 (NT$)",
        "margin_rate": "融資利率 (%)",
        "fetching_prices": "正在獲取即時股價與一年期殖利率...",
        "main_title": "📊 量化投資組合與總體經濟分析",
        "tab_1": "我的投資組合與槓桿",
        "tab_2": "總體經濟環境",
        "tab_3": "資產成長預測",
        "port_overview": "投資組合總覽",
        "total_assets": "總資產價值",
        "net_equity": "淨值 (扣除債務)",
        "unrealized_pl": "總未實現損益",
        "lev_ratio": "槓桿比率",
        "warn_lev": "警告：高槓桿！",
        "healthy_lev": "健康",
        "holdings_detail": "持股明細",
        "asset_alloc": "資產配置",
        "no_holdings": "請在左側側邊欄輸入您的持股以查看投資組合分析。",
        "macro_header": "總體經濟指標 (一年趨勢)",
        "fetching_macro": "正在從 Yahoo Finance 獲取總經指標...",
        "growth_header": "未來資產成長預估",
        "growth_desc": "預估您的資產隨時間的成長。每檔持股將根據其**個別的預期殖利率**進行增長 (除非手動覆寫，否則將自動使用過去一年的歷史報酬率計算)。",
        "years_project": "預估年數",
        "annual_contrib": "每年額外投入金額 (NT$)",
        "proj_engine": "💡 **預測引擎：** 個別持股將依據其專屬殖利率成長。您未分配的現金 (新投入資金減去融資利息) 預設將以目前投資組合的加權平均殖利率 **{:.2f}%** 進行成長。",
        "proj_chart_title": "投資組合隨時間的變化 (個別殖利率模型)",
        "proj_success": "📈 經過 **{} 年**，每年投入 **NT${:,.0f}**，您的預估淨值將達到 **NT${:,.2f}**。",
        "proj_warning": "您的總資產價值為 0。請在側邊欄新增持股以查看預測結果。",
        "macro_meter_title": "🌡️ 市場情緒指標：",
        "status_high_risk": "高總經風險 / 恐慌主導 (避險資產與波動率偏高)",
        "status_complacent": "過度樂觀 (低波動與低殖利率顯示市場可能忽視風險)",
        "status_neutral": "中性 / 正常環境",
        "meter_reason": "判斷依據：",
        "rs_vix_high": "VIX > 25 (恐慌情緒高)",
        "rs_vix_low": "VIX < 15 (市場過度自滿)",
        "rs_tnx_high": "10年公債殖利率 > 4.5% (資金緊縮)",
        "rs_tnx_low": "10年公債殖利率 < 3.5% (資金寬鬆)",
        "rs_oil_high": "油價 > $85 (通膨風險升溫)",
        "rs_oil_low": "油價 < $70 (能源成本低)",
        "rs_gold_high": "金價飆升 (避險買盤湧入)",
        "rs_gold_low": "金價疲軟 (市場偏好風險)"
    }
}

st.set_page_config(
    page_title="Personal Portfolio & Macro Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def safe_extract_scalar(df, column_name='Close'):
    """
    Safely extracts a standard Python float from a yfinance DataFrame.
    Handles MultiIndex columns and single Series formats gracefully.
    """
    if df.empty:
        return None
    
    # Check if column is in DataFrame
    if column_name in df.columns:
        data_col = df[column_name]
    else:
        # Fallback to the first available column
        data_col = df.iloc[:, 0]
        
    # If the column itself contains multiple ticker levels (MultiIndex DataFrame)
    if isinstance(data_col, pd.DataFrame):
        data_series = data_col.iloc[:, 0]
    else:
        data_series = data_col
        
    # Drop NaNs and extract the last element
    clean_series = data_series.dropna()
    if clean_series.empty:
        return None
        
    last_val = clean_series.iloc[-1]
    
    # Cast potential numpy values to native Python floats
    if hasattr(last_val, 'item'):
        return float(last_val.item())
    return float(last_val)

@st.cache_data(ttl=3600)
def fetch_macro_data():
    """Fetches macro-economic indicators using yfinance."""
    tickers = {
        "S&P 500": "^GSPC",
        "VIX": "^VIX",
        "US 10-Year Yield": "^TNX",
        "USD Index": "DX-Y.NYB",
        "Brent Crude": "BZ=F",
        "Gold": "GC=F"
    }
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365) # 1 year of data
    
    data = {}
    current_vals = {}
    
    for name, ticker in tickers.items():
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not df.empty:
                # Store history series safely
                if 'Close' in df.columns:
                    series = df['Close']
                    if isinstance(series, pd.DataFrame):
                        series = series.iloc[:, 0]
                else:
                    series = df.iloc[:, 0]
                
                data[name] = series
                current_vals[name] = safe_extract_scalar(df, 'Close')
            else:
                current_vals[name] = None
        except Exception as e:
            current_vals[name] = None
            
    return data, current_vals

@st.cache_data(ttl=900)
def fetch_stock_stats(ticker):
    """Fetches the most recent closing price and 1-year historical return."""
    try:
        stock = yf.Ticker(ticker.strip().upper())
        # Fetch 1 year of data to calculate trailing yield
        hist = stock.history(period="1y")
        if not hist.empty:
            current_price = safe_extract_scalar(hist, 'Close') or 0.0
            
            # Calculate 1-year return if we have enough data (approx 252 trading days)
            if len(hist) > 200:
                first_price = hist['Close'].iloc[0]
                if isinstance(first_price, pd.Series):
                    first_price = first_price.iloc[0]
                first_price = float(first_price)
                
                if first_price > 0:
                    yearly_yield = ((current_price - first_price) / first_price) * 100
                else:
                    yearly_yield = 8.0 # fallback
            else:
                yearly_yield = 8.0 # fallback for new stocks
                
            return pd.Series([current_price, yearly_yield])
        return pd.Series([0.0, 8.0])
    except Exception:
        return pd.Series([0.0, 8.0])

# --- MEMORY & LANGUAGE SETUP ---
# 0. Read language memory
saved_lang = st.query_params.get("lang", "English")
if saved_lang not in LANGUAGES:
    saved_lang = "English"

# Language Selector
selected_lang = st.sidebar.selectbox("🌐 Language / 語言", ["English", "繁體中文"], index=0 if saved_lang=="English" else 1)
t = LANGUAGES[selected_lang] # The active translation dictionary

st.sidebar.header(t["sb_header_1"])
st.sidebar.markdown(t["sb_desc_1"])

# Helper function to parse URL text back into a DataFrame
def parse_portfolio_text(text):
    data = []
    for line in text.strip().split('\n'):
        if not line.strip(): continue
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 3:
            try:
                data.append({
                    "Ticker": parts[0].upper(), 
                    "Shares": float(parts[1]), 
                    "Avg Price": float(parts[2]),
                    "Leverage": float(parts[3]) if len(parts) >= 4 else 1.0,
                    "Custom Yield": float(parts[4]) if len(parts) >= 5 and parts[4] != 'None' else None
                })
            except ValueError:
                pass
    return pd.DataFrame(data, columns=["Ticker", "Shares", "Avg Price", "Leverage", "Custom Yield"])

# Helper function to serialize DataFrame to text for URL memory
def df_to_text(df):
    lines = []
    for _, row in df.iterrows():
        if pd.isna(row['Ticker']) or str(row['Ticker']).strip() in ["", "None"]: continue
        t = str(row['Ticker']).strip().upper()
        s = float(row['Shares']) if not pd.isna(row['Shares']) else 0.0
        p = float(row['Avg Price']) if not pd.isna(row['Avg Price']) else 0.0
        l = float(row['Leverage']) if not pd.isna(row['Leverage']) else 1.0
        y = float(row['Custom Yield']) if not pd.isna(row['Custom Yield']) else None
        
        if pd.isna(y):
            lines.append(f"{t},{s},{p},{l}")
        else:
            lines.append(f"{t},{s},{p},{l},{y}")
    return "\n".join(lines)

# Default portfolio example
default_portfolio = "00631L.TW,1000,150.00,2\nAAPL,50,4500.00,1\nMSFT,30,9500.00,1,15.0\nSPY,20,15000.00,1"

# 1. Read the saved memory from the URL (if it exists)
saved_portfolio_text = st.query_params.get("portfolio", default_portfolio)
saved_debt = float(st.query_params.get("debt", 0.0))
saved_rate = float(st.query_params.get("rate", 5.0))

initial_df = parse_portfolio_text(saved_portfolio_text)

# Interactive Data Editor
edited_df = st.sidebar.data_editor(
    initial_df,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "Ticker": st.column_config.TextColumn(t["col_ticker"], required=True),
        "Shares": st.column_config.NumberColumn(t["col_shares"], min_value=0.0, step=1.0),
        "Avg Price": st.column_config.NumberColumn(t["col_price"], min_value=0.0),
        "Leverage": st.column_config.NumberColumn(t["col_leverage"], min_value=1.0, step=0.1),
        "Custom Yield": st.column_config.NumberColumn(t["col_yield"], help=t["col_yield_help"])
    }
)

st.sidebar.header(t["sb_header_2"])
margin_debt = st.sidebar.number_input(t["margin_debt"], min_value=0.0, value=saved_debt, step=1000.0)
margin_interest_rate = st.sidebar.slider(t["margin_rate"], min_value=0.0, max_value=20.0, value=saved_rate, step=0.1)

# 2. Update memory
st.query_params["lang"] = selected_lang
st.query_params["portfolio"] = df_to_text(edited_df)
st.query_params["debt"] = margin_debt
st.query_params["rate"] = margin_interest_rate
# ----------------------------------

df_portfolio = edited_df.dropna(subset=['Ticker']).copy()
# Force convert types so calculations don't break
for col in ['Shares', 'Avg Price', 'Leverage', 'Custom Yield']:
    df_portfolio[col] = pd.to_numeric(df_portfolio[col], errors='coerce')

total_asset_value = 0.0
total_cost_basis = 0.0
total_effective_exposure = 0.0

if not df_portfolio.empty:
    with st.spinner(t["fetching_prices"]):
        stats = df_portfolio['Ticker'].apply(fetch_stock_stats)
        df_portfolio['Current Price'] = stats[0]
        df_portfolio['Auto Yield (%)'] = stats[1]
        
        # Merge custom yield with auto yield
        df_portfolio['Expected Yield (%)'] = df_portfolio['Custom Yield'].fillna(df_portfolio['Auto Yield (%)'])
        
        df_portfolio['Total Value'] = df_portfolio['Shares'] * df_portfolio['Current Price']
        df_portfolio['Effective Exposure'] = df_portfolio['Total Value'] * df_portfolio['Leverage']
        df_portfolio['Total Cost'] = df_portfolio['Shares'] * df_portfolio['Avg Price']
        df_portfolio['P/L (NT$)'] = df_portfolio['Total Value'] - df_portfolio['Total Cost']
        df_portfolio['P/L (%)'] = (df_portfolio['P/L (NT$)'] / df_portfolio['Total Cost']) * 100
        
        total_asset_value = df_portfolio['Total Value'].sum()
        total_cost_basis = df_portfolio['Total Cost'].sum()
        total_effective_exposure = df_portfolio['Effective Exposure'].sum()

net_equity = total_asset_value - margin_debt
leverage_ratio = (total_effective_exposure / net_equity) if net_equity > 0 else 0.0

st.title(t["main_title"])

tab1, tab2, tab3 = st.tabs([t["tab_1"], t["tab_2"], t["tab_3"]])

with tab1:
    st.header(t["port_overview"])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t["total_assets"], f"NT${total_asset_value:,.2f}")
    col2.metric(t["net_equity"], f"NT${net_equity:,.2f}")
    
    # Calculate overall P/L
    if not df_portfolio.empty and total_cost_basis > 0:
        total_pl_dollars = total_asset_value - total_cost_basis
        total_pl_percent = (total_pl_dollars / total_cost_basis) * 100
        col3.metric(t["unrealized_pl"], f"NT${total_pl_dollars:,.2f}", f"{total_pl_percent:.2f}%")
    else:
        col3.metric(t["unrealized_pl"], "NT$0.00")
        
    col4.metric(t["lev_ratio"], f"{leverage_ratio:.2f}x", 
                delta=t["warn_lev"] if leverage_ratio > 2.0 else t["healthy_lev"], 
                delta_color="inverse" if leverage_ratio > 2.0 else "normal")

    st.markdown("---")
    
    if not df_portfolio.empty:
        col_table, col_chart = st.columns([3, 2])
        
        with col_table:
            st.subheader(t["holdings_detail"])
            display_df = df_portfolio.drop(columns=['Custom Yield', 'Auto Yield (%)', 'Effective Exposure']).copy()
            for col in ['Avg Price', 'Current Price', 'Total Value', 'Total Cost', 'P/L (NT$)']:
                display_df[col] = display_df[col].apply(lambda x: f"NT${x:,.2f}")
            display_df['P/L (%)'] = display_df['P/L (%)'].apply(lambda x: f"{x:.2f}%")
            display_df['Expected Yield (%)'] = display_df['Expected Yield (%)'].apply(lambda x: f"{x:.2f}%")
            display_df['Leverage'] = display_df['Leverage'].apply(lambda x: f"{x}x")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
        with col_chart:
            st.subheader(t["asset_alloc"])
            fig = px.pie(df_portfolio, values='Total Value', names='Ticker', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(t["no_holdings"])

with tab2:
    st.header(t["macro_header"])
    
    with st.spinner(t["fetching_macro"]):
        macro_hist, macro_current = fetch_macro_data()
        
    risk_score = 0
    reasons = []

    vix = macro_current.get("VIX")
    if vix is not None and not np.isnan(vix):
        if vix > 25:
            risk_score += 1
            reasons.append(t["rs_vix_high"])
        elif vix < 15:
            risk_score -= 1
            reasons.append(t["rs_vix_low"])

    tnx = macro_current.get("US 10-Year Yield")
    if tnx is not None and not np.isnan(tnx):
        if tnx > 4.5:
            risk_score += 1
            reasons.append(t["rs_tnx_high"])
        elif tnx < 3.5:
            risk_score -= 1
            reasons.append(t["rs_tnx_low"])

    oil = macro_current.get("Brent Crude")
    if oil is not None and not np.isnan(oil):
        if oil > 85:
            risk_score += 1
            reasons.append(t["rs_oil_high"])
        elif oil < 70:
            risk_score -= 1
            reasons.append(t["rs_oil_low"])
            
    gold = macro_current.get("Gold")
    if gold is not None and not np.isnan(gold) and "Gold" in macro_hist and not macro_hist["Gold"].empty:
        gold_avg = macro_hist["Gold"].mean()
        if gold > gold_avg * 1.05:
            risk_score += 1
            reasons.append(t["rs_gold_high"])
        elif gold < gold_avg * 0.95:
            risk_score -= 1
            reasons.append(t["rs_gold_low"])

    if risk_score >= 2:
        st.error(f"**{t['macro_meter_title']}** {t['status_high_risk']}\n\n**{t['meter_reason']}** {', '.join(reasons)}")
    elif risk_score <= -2:
        st.warning(f"**{t['macro_meter_title']}** {t['status_complacent']}\n\n**{t['meter_reason']}** {', '.join(reasons)}")
    else:
        reason_str = ', '.join(reasons) if reasons else t["status_neutral"]
        st.success(f"**{t['macro_meter_title']}** {t['status_neutral']}\n\n**{t['meter_reason']}** {reason_str}")

    st.markdown("---")
    
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col4, m_col5, m_col6 = st.columns(3)
    
    def format_metric(val, is_pct=False):
        if val is None or np.isnan(val): 
            return "N/A"
        return f"{val:.2f}%" if is_pct else f"{val:,.2f}"

    m_col1.metric("S&P 500", format_metric(macro_current.get("S&P 500")))
    m_col2.metric("VIX (Volatility)", format_metric(macro_current.get("VIX")))
    m_col3.metric("US 10-Yr Yield", format_metric(macro_current.get("US 10-Year Yield"), True))
    
    m_col4.metric("USD Index", format_metric(macro_current.get("USD Index")))
    oil_val = macro_current.get("Brent Crude")
    m_col5.metric("Brent Crude", f"${format_metric(oil_val)}" if oil_val is not None else "N/A")
    gold_val = macro_current.get("Gold")
    m_col6.metric("Gold (Futures)", f"${format_metric(gold_val)}" if gold_val is not None else "N/A")
    
    st.markdown("---")
    
    if macro_hist:
        chart_col1, chart_col2 = st.columns(2)
        
        # S&P 500 Chart
        if "S&P 500" in macro_hist and not macro_hist["S&P 500"].empty:
            fig_sp = px.line(x=macro_hist["S&P 500"].index, y=macro_hist["S&P 500"].values, title="S&P 500 Index")
            fig_sp.update_xaxes(title="Date")
            fig_sp.update_yaxes(title="Price")
            chart_col1.plotly_chart(fig_sp, use_container_width=True)
            
        # VIX Chart
        if "VIX" in macro_hist and not macro_hist["VIX"].empty:
            fig_vix = px.line(x=macro_hist["VIX"].index, y=macro_hist["VIX"].values, title="VIX (Market Fear Index)")
            fig_vix.update_traces(line_color='red')
            fig_vix.update_xaxes(title="Date")
            fig_vix.update_yaxes(title="Points")
            chart_col2.plotly_chart(fig_vix, use_container_width=True)
            
        # US 10-Year Chart
        if "US 10-Year Yield" in macro_hist and not macro_hist["US 10-Year Yield"].empty:
            fig_tnx = px.line(x=macro_hist["US 10-Year Yield"].index, y=macro_hist["US 10-Year Yield"].values, title="US 10-Year Treasury Yield (%)")
            fig_tnx.update_traces(line_color='green')
            fig_tnx.update_xaxes(title="Date")
            fig_tnx.update_yaxes(title="Yield (%)")
            chart_col1.plotly_chart(fig_tnx, use_container_width=True)
            
        # USD Index
        if "USD Index" in macro_hist and not macro_hist["USD Index"].empty:
            fig_usd = px.line(x=macro_hist["USD Index"].index, y=macro_hist["USD Index"].values, title="US Dollar Index (DXY)")
            fig_usd.update_traces(line_color='purple')
            fig_usd.update_xaxes(title="Date")
            fig_usd.update_yaxes(title="Index Value")
            chart_col2.plotly_chart(fig_usd, use_container_width=True)
            
        # Gold Chart
        if "Gold" in macro_hist and not macro_hist["Gold"].empty:
            fig_gold = px.line(x=macro_hist["Gold"].index, y=macro_hist["Gold"].values, title="Gold Futures (GC=F)")
            fig_gold.update_traces(line_color='goldenrod')
            fig_gold.update_xaxes(title="Date")
            fig_gold.update_yaxes(title="Price (USD)")
            chart_col1.plotly_chart(fig_gold, use_container_width=True)
            
        # Brent Crude Chart
        if "Brent Crude" in macro_hist and not macro_hist["Brent Crude"].empty:
            fig_oil = px.line(x=macro_hist["Brent Crude"].index, y=macro_hist["Brent Crude"].values, title="Brent Crude Oil")
            fig_oil.update_traces(line_color='orange')
            fig_oil.update_xaxes(title="Date")
            fig_oil.update_yaxes(title="Price (USD)")
            chart_col2.plotly_chart(fig_oil, use_container_width=True)

with tab3:
    st.header(t["growth_header"])
    st.markdown(t["growth_desc"])
    
    g_col1, g_col2 = st.columns(2)
    years_to_project = g_col1.slider(t["years_project"], min_value=1, max_value=30, value=10, step=1)
    annual_contribution = g_col2.number_input(t["annual_contrib"], min_value=0.0, value=12000.0, step=1000.0)
    
    if total_asset_value > 0:
        weighted_avg_cagr = (df_portfolio['Expected Yield (%)'] * df_portfolio['Total Value']).sum() / total_asset_value
        st.info(t["proj_engine"].format(weighted_avg_cagr))
        
        years = np.arange(0, years_to_project + 1)
        projected_assets = np.zeros(len(years))
        projected_debt = np.zeros(len(years))
        projected_equity = np.zeros(len(years))
        
        projected_assets[0] = total_asset_value
        projected_debt[0] = margin_debt
        projected_equity[0] = net_equity
        
        weighted_r = weighted_avg_cagr / 100
        
        # Track the values over time arrays
        running_holdings = df_portfolio['Total Value'].values.copy()
        running_yields = (df_portfolio['Expected Yield (%)'] / 100).values
        running_extra_pool = 0.0
        
        for i in range(1, len(years)):
            # Grow original holdings individually
            running_holdings = running_holdings * (1 + running_yields)
            
            # Grow extra pool (contributions) at weighted average
            running_extra_pool = (running_extra_pool * (1 + weighted_r)) + annual_contribution
            
            # Subtract margin interest directly from the extra pool
            annual_interest_cost = margin_debt * (margin_interest_rate / 100)
            running_extra_pool -= annual_interest_cost
            
            projected_debt[i] = margin_debt
            projected_assets[i] = running_holdings.sum() + running_extra_pool
            projected_equity[i] = projected_assets[i] - projected_debt[i]
            
            if projected_equity[i] < 0:
                projected_equity[i] = 0 # Margin Wipeout Scenario
                
        df_projection = pd.DataFrame({
            "Year": [datetime.now().year + y for y in years],
            "Total Assets": projected_assets,
            "Net Equity": projected_equity,
            "Margin Debt": projected_debt
        })
        
        fig_proj = go.Figure()
        fig_proj.add_trace(go.Bar(x=df_projection["Year"], y=df_projection["Net Equity"], name="Net Equity", marker_color='rgb(55, 83, 109)'))
        fig_proj.add_trace(go.Bar(x=df_projection["Year"], y=df_projection["Margin Debt"], name="Margin Debt", marker_color='rgb(204, 51, 51)'))
        
        fig_proj.update_layout(
            title=t["proj_chart_title"],
            barmode='stack',
            xaxis_title="Year",
            yaxis_title="Value (NT$)",
            hovermode="x unified"
        )
        st.plotly_chart(fig_proj, use_container_width=True)
        
        st.success(t["proj_success"].format(years_to_project, annual_contribution, projected_equity[-1]))
    else:
        st.warning(t["proj_warning"])
