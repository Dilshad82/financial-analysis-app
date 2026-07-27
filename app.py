import urllib.parse
import pandas as pd
import plotly.graph_objects as _plotly_go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

from engine import MarketEngine
from reports import ReportGenerator

# --- إعداد الصفحة القياسي ---
st.set_page_config(
    page_title="منصة التحليل المالي المفتوحة",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="collapsed"
)

# --- 1. إعداد وحفظ التفضيلات المحلية ---
if "default_karat" not in st.session_state:
    st.session_state["default_karat"] = "عيار 21 (الأنشُر - الافتراضي)"

if "default_iqd_rate" not in st.session_state:
    st.session_state["default_iqd_rate"] = 1480.0

# --- 2. تحسينات التجاوب الشاملة للموبايل والشاشات الصغرى ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #161b22 100%);
        color: #e6edf3;
    }

    /* ضبط الحواف العامة */
    .main .block-container {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        padding-top: 0.8rem !important;
        padding-bottom: 2rem !important;
    }

    /* تعديل حجم العنوان الرئيسي ليكون مناسباً للموبايل */
    .main h1 {
        font-size: clamp(1.3rem, 4vw, 2.2rem) !important;
        text-align: center !important;
        margin-bottom: 15px !important;
        white-space: nowrap !important;
    }

    /* شريط الأسواق المباشرة العلوي المتجاوب */
    .ticker-bar {
        background: rgba(13, 17, 23, 0.85);
        border: 1px solid rgba(48, 54, 61, 0.8);
        border-radius: 12px;
        padding: 8px 12px;
        margin-bottom: 15px;
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
        justify-content: space-around;
        align-items: center;
        gap: 8px;
        direction: rtl;
    }

    .ticker-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: clamp(0.75rem, 2.5vw, 0.9rem);
        font-weight: 600;
    }

    .badge-up {
        background-color: rgba(46, 213, 115, 0.2);
        color: #2ed573;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
    }

    .badge-down {
        background-color: rgba(255, 71, 87, 0.2);
        color: #ff4757;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
    }

    /* تصميم بطاقات المؤشرات (stMetric) */
    [data-testid="stMetric"] {
        background: rgba(22, 27, 34, 0.65) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 8px 4px !important;
        text-align: center !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    }

    [data-testid="stMetricValue"] {
        font-size: clamp(0.95rem, 3.5vw, 1.3rem) !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        justify-content: center !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: clamp(0.7rem, 2.5vw, 0.85rem) !important;
        color: #8b949e !important;
        font-weight: 600 !important;
        justify-content: center !important;
    }

    /* إجبار شبكة الكروت (st.columns) على العرض كصفين بجانب بعض في الموبايل */
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 8px !important;
            direction: rtl !important;
        }
        div[data-testid="column"] {
            width: 100% !important;
            min-width: 0 !important;
        }
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# --- دالة عرض الشريط المالي اللحظي ---
@st.cache_data(ttl=300)
def render_market_overview_bar():
    tickers = {
        "🧈 الذهب": "GC=F",
        "🛢️ النفط": "CL=F",
        "🪙 بيتكوين": "BTC-USD"
    }

    items_html_list = []
    for label, symbol in tickers.items():
        try:
            df = yf.download(symbol, period="5d", interval="1d", progress=False)
            if not df.empty and len(df) >= 2:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                last_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]
                pct_change = ((last_price - prev_price) / prev_price) * 100

                badge_class = "badge-up" if pct_change >= 0 else "badge-down"
                arrow = "▲" if pct_change >= 0 else "▼"

                item_str = f'<div class="ticker-item"><span><b>{label}:</b> ${last_price:,.2f}</span><span class="{badge_class}">{arrow} {abs(pct_change):.2f}%</span></div>'
                items_html_list.append(item_str)
        except Exception:
            continue

    if items_html_list:
        full_bar_html = f'<div class="ticker-bar">{"".join(items_html_list)}</div>'
        st.markdown(full_bar_html, unsafe_allow_html=True)


st.title("📈 المنصة المالية للتحليل الفني")
render_market_overview_bar()


# --- الدوال المساعدة ---
def resolve_company_symbol(query: str) -> str:
    query_clean = query.strip().lower()
    companies_mapping = {
        "أبل": "AAPL", "ابل": "AAPL", "apple": "AAPL",
        "مايكروسوفت": "MSFT", "microsoft": "MSFT",
        "تسلا": "TSLA", "تسيلا": "TSLA", "tesla": "TSLA",
        "إنفيديا": "NVDA", "انفيديا": "NVDA", "nvidia": "NVDA",
        "أمازون": "AMZN", "امازون": "AMZN", "amazon": "AMZN",
        "جوجل": "GOOGL", "قوقل": "GOOGL", "google": "GOOGL",
        "ميتا": "META", "فيسبوك": "META", "meta": "META"
    }
    if query_clean in companies_mapping:
        return companies_mapping[query_clean]
    try:
        search_results = yf.Search(query, max_results=1).quotes
        if search_results and "symbol" in search_results[0]:
            return search_results[0]["symbol"]
    except Exception:
        pass
    return query.strip().upper()


def resolve_currency_symbol(query: str) -> str:
    query_clean = query.strip().lower()
    currencies_mapping = {
        "بتكوين": "BTC-USD", "بيتكوين": "BTC-USD", "bitcoin": "BTC-USD", "btc": "BTC-USD",
        "إيثريوم": "ETH-USD", "اثريوم": "ETH-USD", "ethereum": "ETH-USD",
        "سولانا": "SOL-USD", "solana": "SOL-USD",
        "ريبل": "XRP-USD", "ripple": "XRP-USD",
        "يورو": "EURUSD=X", "باوند": "GBPUSD=X"
    }
    if query_clean in currencies_mapping:
        return currencies_mapping[query_clean]
    try:
        search_results = yf.Search(query, max_results=1).quotes
        if search_results and "symbol" in search_results[0]:
            return search_results[0]["symbol"]
    except Exception:
        pass
    return query.strip().upper()


# --- الشريط الجانبي ---
st.sidebar.header("⚙️ إعدادات البحث")

asset_category = st.sidebar.radio(
    "اختر فئة التحليل:",
    ["🏢 شركات وأسهم عالمية", "🪙 عملات (رقمية وأجنبية)", "🧈 الذهب والمعادن"]
)

st.sidebar.markdown("---")

selected_symbol = ""
selected_label = ""
karat_value = 21
selected_karat_name = "21"

if asset_category == "🏢 شركات وأسهم عالمية":
    company_input = st.sidebar.text_input("أدخل اسم الشركة أو الرمز:", value="أبل")
    selected_symbol = resolve_company_symbol(company_input)
    selected_label = company_input

elif asset_category == "🪙 عملات (رقمية وأجنبية)":
    currency_input = st.sidebar.text_input("أدخل اسم العملة أو الرمز:", value="بيتكوين")
    selected_symbol = resolve_currency_symbol(currency_input)
    selected_label = currency_input

else:
    metal_choice = st.sidebar.selectbox("اختر المعدن:", ["عقود الذهب (Gold)", "عقود الفضة (Silver)"])
    if "فضة" in metal_choice or "Silver" in metal_choice:
        selected_symbol = "SI=F"
        selected_label = "الفضة"
    else:
        selected_symbol = "GC=F"
        selected_label = "الذهب"

        karat_options = [
            "عيار 21 (الأنشُر - الافتراضي)",
            "عيار 24 (الذهب الخالص)",
            "عيار 18 (المطعّم)"
        ]

        current_index = karat_options.index(st.session_state["default_karat"]) if st.session_state["default_karat"] in karat_options else 0

        gold_karat = st.sidebar.selectbox("👑 اختر عيار الذهب المفضّل:", karat_options, index=current_index)
        st.session_state["default_karat"] = gold_karat

        if "24" in gold_karat:
            karat_value = 24
            selected_karat_name = "24"
        elif "18" in gold_karat:
            karat_value = 18
            selected_karat_name = "18"
        else:
            karat_value = 21
            selected_karat_name = "21"

timeframe_choice = st.sidebar.selectbox("⏱️ الفريم الزمني:", ["ساعاتي (1H)", "يومي (1D)", "أسبوعي (1W)"], index=1)

if timeframe_choice == "ساعاتي (1H)":
    selected_interval = "1h"
    time_period = "1mo"
elif timeframe_choice == "أسبوعي (1W)":
    selected_interval = "1wk"
    time_period = st.sidebar.selectbox("الفترة الزمنية:", ["1y", "2y", "5y"], index=1)
else:
    selected_interval = "1d"
    time_period = st.sidebar.selectbox("الفترة الزمنية:", ["1m", "3m", "6m", "1y", "2y"], index=3)

if selected_symbol == "GC=F":
    st.sidebar.subheader("💰 حاسبة الذهب (IQD)")
    iqd_rate = st.sidebar.number_input("سعر صرف USD/IQD:", value=st.session_state["default_iqd_rate"], step=10.0)
    st.session_state["default_iqd_rate"] = iqd_rate
    user_mithqal = st.sidebar.number_input("عدد المثاقيل:", value=1.0, min_value=0.1, step=0.5)
else:
    st.sidebar.subheader("💼 حاسبة الاستثمار")
    user_quantity = st.sidebar.number_input("عدد الأسهم/الوحدات:", value=1.0, min_value=0.01, step=0.1)

# --- جلب البيانات ---
data = MarketEngine.get_market_data(selected_symbol, period=time_period, interval=selected_interval)

if data is None or data.empty:
    st.error(f"❌ لم يتم العثور على بيانات لـ ({selected_label}).")
    st.stop()

latest_row = data.iloc[-1]
signal_label, rsi_status = MarketEngine.get_signal(latest_row)

# --- كروت المؤشرات الأساسية ---
col_sig1, col_sig2, col_sig3, col_sig4 = st.columns(4)
col_sig1.metric("السعر الحالي", f"${latest_row['Close']:,.2f}")
col_sig2.metric("مؤشر RSI", f"{latest_row['RSI']:.1f}")
col_sig3.metric("حالة RSI", rsi_status)
col_sig4.metric("التوصية", signal_label)

detected_patterns = MarketEngine.detect_candlestick_patterns(data)
if detected_patterns:
    for pattern in detected_patterns:
        st.info(f"🔍 **نموذج فني:** {pattern}")

st.markdown("---")

share_text = ""

if selected_symbol == "GC=F":
    gold_info = MarketEngine.calculate_gold_units(
        usd_price=latest_row['Close'],
        karat=karat_value,
        iqd_rate=iqd_rate
    )

    mithqal_iqd = gold_info['mithqal_iqd']
    gram_iqd = gold_info['gram_iqd']
    total_val_iqd = mithqal_iqd * user_mithqal

    st.subheader(f"🧈 الذهب — عيار {selected_karat_name}")

    g_col1, g_col2, g_col3 = st.columns(3)
    g_col1.metric(f"المثقال ({selected_karat_name})", f"{mithqal_iqd:,.0f} د.ع")
    g_col2.metric(f"الجرام ({selected_karat_name})", f"{gram_iqd:,.0f} د.ع")
    g_col3.metric(f"قيمة ممتلكاتك", f"{total_val_iqd:,.0f} د.ع")
    st.markdown("---")

    share_text = f"🏆 تقرير الذهب (عيار {selected_karat_name}): الأونصة ${latest_row['Close']:,.2f} | المثقال {mithqal_iqd:,.0f} د.ع"
else:
    st.subheader(f"📊 قيمة الاستثمار: {selected_label}")
    total_asset_val = latest_row['Close'] * user_quantity
    c1, c2 = st.columns(2)
    c1.metric("الكمية", f"{user_quantity}")
    c2.metric("القيمة الإجمالية", f"${total_asset_val:,.2f}")
    st.markdown("---")

    share_text = f"📈 تقرير {selected_label}: ${latest_row['Close']:,.2f} | التوصية: {signal_label}"

# --- الرسوم البيانية ---
st.subheader(f"📊 الرسم البياني ({timeframe_choice})")

tab_main, tab_oscillators, tab_advanced = st.tabs(["📈 السعر و Volume", "⚡ RSI & MACD", "🎯 Stoch & ADX"])

with tab_main:
    has_volume = 'Volume' in data.columns and (data['Volume'] > 0).any()
    if has_volume:
        fig_main = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    else:
        fig_main = make_subplots(rows=1, cols=1)

    fig_main.add_trace(_plotly_go.Scatter(x=data.index, y=data['Close'], name='السعر', line=dict(color='#1f77b4', width=2)), row=1, col=1)
    fig_main.add_trace(_plotly_go.Scatter(x=data.index, y=data['BB_Upper'], name='Upper', line=dict(color='gray', dash='dash')), row=1, col=1)
    fig_main.add_trace(_plotly_go.Scatter(x=data.index, y=data['BB_Lower'], name='Lower', line=dict(color='gray', dash='dash')), row=1, col=1)

    if 'VWAP' in data.columns:
        fig_main.add_trace(_plotly_go.Scatter(x=data.index, y=data['VWAP'], name='VWAP', line=dict(color='#ff9f43', width=1.5, dash='dot')), row=1, col=1)

    if has_volume:
        vol_colors = ['#2ed573' if c >= o else '#ff4757' for c, o in zip(data['Close'], data['Open'])]
        fig_main.add_trace(_plotly_go.Bar(x=data.index, y=data['Volume'], name='Volume', marker_color=vol_colors), row=2, col=1)

    fig_main.update_layout(height=420, showlegend=False, margin=dict(l=5, r=5, t=10, b=10))
    st.plotly_chart(fig_main, use_container_width=True, config={"responsive": True})

with tab_oscillators:
    fig_osc = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08)
    fig_osc.add_trace(_plotly_go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='#9467bd')), row=1, col=1)
    fig_osc.add_hline(y=70, line_dash="dot", line_color="red", row=1, col=1)
    fig_osc.add_hline(y=30, line_dash="dot", line_color="green", row=1, col=1)

    fig_osc.add_trace(_plotly_go.Scatter(x=data.index, y=data['MACD'], name='MACD', line=dict(color='#ff7f0e')), row=2, col=1)
    fig_osc.add_trace(_plotly_go.Scatter(x=data.index, y=data['Signal_Line'], name='Signal', line=dict(color='#2ca02c')), row=2, col=1)
    fig_osc.add_trace(_plotly_go.Bar(x=data.index, y=data['MACD_Hist'], name='Hist'), row=2, col=1)

    fig_osc.update_layout(height=400, showlegend=False, margin=dict(l=5, r=5, t=10, b=10))
    st.plotly_chart(fig_osc, use_container_width=True, config={"responsive": True})

with tab_advanced:
    fig_adv = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08)
    if 'Stoch_K' in data.columns:
        fig_adv.add_trace(_plotly_go.Scatter(x=data.index, y=data['Stoch_K'], name='%K', line=dict(color='#00d2d3')), row=1, col=1)
        fig_adv.add_trace(_plotly_go.Scatter(x=data.index, y=data['Stoch_D'], name='%D', line=dict(color='#ff9f43', dash='dash')), row=1, col=1)

    if 'ADX' in data.columns:
        fig_adv.add_trace(_plotly_go.Scatter(x=data.index, y=data['ADX'], name='ADX', line=dict(color='#54a0ff', width=2)), row=2, col=1)

    fig_adv.update_layout(height=400, showlegend=False, margin=dict(l=5, r=5, t=10, b=10))
    st.plotly_chart(fig_adv, use_container_width=True, config={"responsive": True})

# --- التصدير والمشاركة ---
st.subheader("📥 التصدير والمشاركة")
exp_col1, exp_col2 = st.columns(2)

with exp_col1:
    excel_data = ReportGenerator.convert_df_to_excel(data)
    st.download_button("📊 Excel", data=excel_data, file_name=f"{selected_symbol}.xlsx", use_container_width=True)

with exp_col2:
    word_doc = ReportGenerator.generate_rsi_word_doc()
    st.download_button("📝 دليل (Word)", data=word_doc, file_name="دليل_المؤشرات.docx", use_container_width=True)