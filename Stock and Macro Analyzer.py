import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

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
        "Brent Crude": "BZ=F"
    }

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1 year of data

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
                    yearly_yield = 8.0  # fallback
            else:
                yearly_yield = 8.0  # fallback for new stocks

            return pd.Series([current_price, yearly_yield])
        return pd.Series([0.0, 8.0])
    except Exception:
        return pd.Series([0.0, 8.0])


st.sidebar.header("💼 Portfolio Input")
st.sidebar.markdown("""
Enter your stock holdings below. 
Format: `Ticker, Shares, Avg Price, [Leverage], [Yearly Growth %]`  
*(Leverage and Growth are optional. Growth auto-calculates 1-yr return if omitted)*
""")

# Default portfolio example with leverage and custom yield
default_portfolio = """00631L.TW, 1000, 150.00, 2
AAPL, 50, 150.00
MSFT, 30, 310.50, 1, 15.0
SPY, 20, 450.00"""

portfolio_input = st.sidebar.text_area("Your Holdings:", value=default_portfolio, height=150)

st.sidebar.header("⚖️ Leverage & Debt")
margin_debt = st.sidebar.number_input("Total Margin/Debt ($)", min_value=0.0, value=0.0, step=1000.0)
margin_interest_rate = st.sidebar.slider("Margin Interest Rate (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.1)

portfolio_data = []
if portfolio_input:
    lines = portfolio_input.strip().split('\n')
    for line in lines:
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 3:
            ticker = parts[0].upper()
            try:
                shares = float(parts[1])
                avg_price = float(parts[2])
                leverage = float(parts[3]) if len(parts) >= 4 else 1.0
                custom_yield = float(parts[4]) if len(parts) >= 5 else None

                portfolio_data.append({
                    "Ticker": ticker,
                    "Shares": shares,
                    "Avg Price": avg_price,
                    "Leverage": leverage,
                    "Custom Yield": custom_yield
                })
            except ValueError:
                st.sidebar.error(f"Invalid number format in line: {line}")

df_portfolio = pd.DataFrame(portfolio_data)

total_asset_value = 0.0
total_cost_basis = 0.0
total_effective_exposure = 0.0

if not df_portfolio.empty:
    with st.spinner('Fetching live prices and 1-yr yields...'):
        stats = df_portfolio['Ticker'].apply(fetch_stock_stats)
        df_portfolio['Current Price'] = stats[0]
        df_portfolio['Auto Yield (%)'] = stats[1]

        # Merge custom yield with auto yield
        df_portfolio['Expected Yield (%)'] = df_portfolio['Custom Yield'].fillna(df_portfolio['Auto Yield (%)'])

        df_portfolio['Total Value'] = df_portfolio['Shares'] * df_portfolio['Current Price']
        df_portfolio['Effective Exposure'] = df_portfolio['Total Value'] * df_portfolio['Leverage']
        df_portfolio['Total Cost'] = df_portfolio['Shares'] * df_portfolio['Avg Price']
        df_portfolio['P/L ($)'] = df_portfolio['Total Value'] - df_portfolio['Total Cost']
        df_portfolio['P/L (%)'] = (df_portfolio['P/L ($)'] / df_portfolio['Total Cost']) * 100

        total_asset_value = df_portfolio['Total Value'].sum()
        total_cost_basis = df_portfolio['Total Cost'].sum()
        total_effective_exposure = df_portfolio['Effective Exposure'].sum()

net_equity = total_asset_value - margin_debt
leverage_ratio = (total_effective_exposure / net_equity) if net_equity > 0 else 0.0

st.title("📊 Quantitative Portfolio & Macro Analyzer")

tab1, tab2, tab3 = st.tabs(["My Portfolio & Leverage", "Macro Environment", "Growth Projections"])

with tab1:
    st.header("Portfolio Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Asset Value", f"${total_asset_value:,.2f}")
    col2.metric("Net Equity", f"${net_equity:,.2f}")

    # Calculate overall P/L
    if not df_portfolio.empty and total_cost_basis > 0:
        total_pl_dollars = total_asset_value - total_cost_basis
        total_pl_percent = (total_pl_dollars / total_cost_basis) * 100
        col3.metric("Total Unrealized P/L", f"${total_pl_dollars:,.2f}", f"{total_pl_percent:.2f}%")
    else:
        col3.metric("Total Unrealized P/L", "$0.00")

    col4.metric("Leverage Ratio", f"{leverage_ratio:.2f}x",
                delta="Warning: High Leverage!" if leverage_ratio > 2.0 else "Healthy",
                delta_color="inverse" if leverage_ratio > 2.0 else "normal")

    st.markdown("---")

    if not df_portfolio.empty:
        col_table, col_chart = st.columns([3, 2])

        with col_table:
            st.subheader("Holdings Detail")
            display_df = df_portfolio.drop(columns=['Custom Yield', 'Auto Yield (%)', 'Effective Exposure']).copy()
            for col in ['Avg Price', 'Current Price', 'Total Value', 'Total Cost', 'P/L ($)']:
                display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
            display_df['P/L (%)'] = display_df['P/L (%)'].apply(lambda x: f"{x:.2f}%")
            display_df['Expected Yield (%)'] = display_df['Expected Yield (%)'].apply(lambda x: f"{x:.2f}%")
            display_df['Leverage'] = display_df['Leverage'].apply(lambda x: f"{x}x")

            # Using updated width standard for Streamlit
            st.dataframe(display_df, width="stretch", hide_index=True)

        with col_chart:
            st.subheader("Asset Allocation")
            fig = px.pie(df_portfolio, values='Total Value', names='Ticker', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

            # Using updated width standard for Streamlit
            st.plotly_chart(fig, width="stretch")
    else:
        st.info("Please enter your holdings in the sidebar to see your portfolio analysis.")

with tab2:
    st.header("Macro-Economic Indicators (1-Year Trend)")

    with st.spinner("Fetching macro indicators from Yahoo Finance..."):
        macro_hist, macro_current = fetch_macro_data()

    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)


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

    st.markdown("---")

    if macro_hist:
        chart_col1, chart_col2 = st.columns(2)

        # S&P 500 Chart
        if "S&P 500" in macro_hist and not macro_hist["S&P 500"].empty:
            fig_sp = px.line(x=macro_hist["S&P 500"].index, y=macro_hist["S&P 500"].values, title="S&P 500 Index")
            fig_sp.update_xaxes(title="Date")
            fig_sp.update_yaxes(title="Price")
            chart_col1.plotly_chart(fig_sp, width="stretch")

        # VIX Chart
        if "VIX" in macro_hist and not macro_hist["VIX"].empty:
            fig_vix = px.line(x=macro_hist["VIX"].index, y=macro_hist["VIX"].values, title="VIX (Market Fear Index)")
            fig_vix.update_traces(line_color='red')
            fig_vix.update_xaxes(title="Date")
            fig_vix.update_yaxes(title="Points")
            chart_col2.plotly_chart(fig_vix, width="stretch")

        # US 10-Year Chart
        if "US 10-Year Yield" in macro_hist and not macro_hist["US 10-Year Yield"].empty:
            fig_tnx = px.line(x=macro_hist["US 10-Year Yield"].index, y=macro_hist["US 10-Year Yield"].values,
                              title="US 10-Year Treasury Yield (%)")
            fig_tnx.update_traces(line_color='green')
            fig_tnx.update_xaxes(title="Date")
            fig_tnx.update_yaxes(title="Yield (%)")
            chart_col1.plotly_chart(fig_tnx, width="stretch")

        # USD Index & Brent Crude
        if "USD Index" in macro_hist and not macro_hist["USD Index"].empty:
            fig_usd = px.line(x=macro_hist["USD Index"].index, y=macro_hist["USD Index"].values,
                              title="US Dollar Index (DXY)")
            fig_usd.update_traces(line_color='purple')
            fig_usd.update_xaxes(title="Date")
            fig_usd.update_yaxes(title="Index Value")
            chart_col2.plotly_chart(fig_usd, width="stretch")

with tab3:
    st.header("Future Portfolio Growth Estimator")
    st.markdown(
        "Project your equity growth over time. Each holding grows at its **individual Expected Yield** (automatically calculated from 1-year historical returns unless overridden).")

    g_col1, g_col2 = st.columns(2)
    years_to_project = g_col1.slider("Years to Project", min_value=1, max_value=30, value=10, step=1)
    annual_contribution = g_col2.number_input("Additional Annual Contribution ($)", min_value=0.0, value=12000.0,
                                              step=1000.0)

    if total_asset_value > 0:
        weighted_avg_cagr = (df_portfolio['Expected Yield (%)'] * df_portfolio['Total Value']).sum() / total_asset_value
        st.info(
            f"💡 **Projection Engine:** Individual holdings grow at their specific yields. Your unallocated cash (new contributions minus margin interest) is assumed to grow at your portfolio's current weighted average yield of **{weighted_avg_cagr:.2f}%**.")

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
                projected_equity[i] = 0  # Margin Wipeout Scenario

        df_projection = pd.DataFrame({
            "Year": [datetime.now().year + y for y in years],
            "Total Assets": projected_assets,
            "Net Equity": projected_equity,
            "Margin Debt": projected_debt
        })

        fig_proj = go.Figure()
        fig_proj.add_trace(go.Bar(x=df_projection["Year"], y=df_projection["Net Equity"], name="Net Equity",
                                  marker_color='rgb(55, 83, 109)'))
        fig_proj.add_trace(go.Bar(x=df_projection["Year"], y=df_projection["Margin Debt"], name="Margin Debt",
                                  marker_color='rgb(204, 51, 51)'))

        fig_proj.update_layout(
            title="Portfolio Composition Over Time (Individual Yield Models)",
            barmode='stack',
            xaxis_title="Year",
            yaxis_title="USD Value ($)",
            hovermode="x unified"
        )
        st.plotly_chart(fig_proj, width="stretch")

        st.success(
            f"📈 After **{years_to_project} years**, contributing **${annual_contribution:,.0f}** yearly, your Net Equity is estimated to be **${projected_equity[-1]:,.2f}**.")
    else:
        st.warning("Your total asset value is 0. Add holdings in the sidebar to see projections.")