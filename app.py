import urllib.parse
import pandas as pd
import plotly.graph_objects as _plotly_go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

from engine import MarketEngine
from reports import ReportGenerator

# --- إعداد الصفحة القياسي وتجاوب الشاشة ---
st.set_page_config(
    page_title="منصة التحليل المالي المفتوحة",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# --- 1. إعداد وحفظ التفضيلات المحلية (Local Preferences Setup) ---
if "default_karat" not in st.session_state:
    st.session_state["default_karat"] = "عيار 21 (الأنشُر - الافتراضي)"

if "default_iqd_rate" not in st.session_state:
    st.session_state["default_iqd_rate"] = 1480.0

# --- 2. تحسينات تجاوب الواجهة والتصميم المالي الاحترافي (Advanced Responsive CSS) ---
st.markdown("""
<style>
    /* خلفية متدرجة حديثة طابع مالي داكن */
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #161b22 100%);
        color: #e6edf3;
    }

    /* تقليل الهوامش الشاشات الصغيرة */
    .main .block-container {
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }

    /* ضبط اتجاه النصوص للعناوين والفقرات */
    .main h1, .main h2, .main h3, .main p, .main div {
        text-align: right;
    }

    /* كروت المؤشرات بتأثير الزجاج الضبابي Glassmorphism */
    [data-testid="stMetric"] {
        background: rgba(22, 27, 34, 0.65) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 12px 8px !important;
        text-align: center !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 210, 106, 0.4) !important;
    }

    [data-testid="stMetricValue"] {
        font-size: clamp(1.0rem, 2.5vw, 1.3rem) !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        justify-content: center !important;
        text-align: center !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: clamp(0.72rem, 1.8vw, 0.88rem) !important;
        color: #8b949e !important;
        font-weight: bold !important;
        justify-content: center !important;
        text-align: center !important;
    }

    /* شريط النظرة العامة السريع (Market Overview Bar) */
    .ticker-bar {
        background: rgba(13, 17, 23, 0.85);
        border: 1px solid rgba(48, 54, 61, 0.8);
        border-radius: 12px;
        padding: 12px 20px;
        margin-bottom: 25px;
        display: flex;
        justify-content: space-around;
        align-items: center;
        flex-wrap: wrap;
        gap: 15px;
        direction: rtl;
    }

    .ticker-item {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.92rem;
        font-weight: 600;
    }

    .badge-up {
        background-color: rgba(46, 213, 115, 0.2);
        color: #2ed573;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: bold;
    }

    .badge-down {
        background-color: rgba(255, 71, 87, 0.2);
        color: #ff4757;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: bold;
    }

    /* أزرار المشاركة والمظهر */
    .share-container {
        display: flex;
        gap: 10px;
        justify-content: center;
        align-items: center;
    }

    .share-btn-wa, .share-btn-tg {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        color: white;
        text-align: center;
    }

    .share-btn-wa { background-color: #25D366; }
    .share-btn-tg { background-color: #0088cc; }

    /* شبكة الكروت للموبايل */
    @media (max-width: 768px) {
        .main [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 10px !important;
            direction: rtl !important;
        }
        .main [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# --- دالة عرض الشريط المالي اللحظي في الأعلى (المعدلة) ---
@st.cache_data(ttl=300)
def render_market_overview_bar():
    """عرض شريط نظرة عامة سريعة للأسواق العالمية في أعلى لوحة التحكم"""
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

                if pct_change >= 0:
                    badge_class = "badge-up"
                    arrow = "▲"
                else:
                    badge_class = "badge-down"
                    arrow = "▼"

                item_str = f'<div class="ticker-item"><span><b>{label}:</b> ${last_price:,.2f}</span><span class="{badge_class}">{arrow} {abs(pct_change):.2f}%</span></div>'
                items_html_list.append(item_str)
        except Exception:
            continue

    if items_html_list:
        full_bar_html = f'<div class="ticker-bar">{"".join(items_html_list)}</div>'
        st.markdown(full_bar_html, unsafe_allow_html=True)


st.title("📈 المنصة المالية للتحليل الفني والشامل")
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
        "ميتا": "META", "فيسبوك": "META", "meta": "META",
        "علي بابا": "BABA", "alibaba": "BABA",
        "نتفليكس": "NFLX", "netflix": "NFLX"
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
        "إيثريوم": "ETH-USD", "اثريوم": "ETH-USD", "ethereum": "ETH-USD", "eth": "ETH-USD",
        "سولانا": "SOL-USD", "solana": "SOL-USD", "sol": "SOL-USD",
        "بينانس": "BNB-USD", "binance": "BNB-USD", "bnb": "BNB-USD",
        "ريبل": "XRP-USD", "ripple": "XRP-USD", "xrp": "XRP-USD",
        "دوجكوين": "DOGE-USD", "dogecoin": "DOGE-USD", "doge": "DOGE-USD",
        "كاردانو": "ADA-USD", "cardano": "ADA-USD", "ada": "ADA-USD",
        "يورو": "EURUSD=X", "euro": "EURUSD=X",
        "باوند": "GBPUSD=X", "pound": "GBPUSD=X",
        "ين": "JPY=X", "yen": "JPY=X"
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
st.sidebar.header("⚙️ إعدادات البحث والتحليل")

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

        current_index = karat_options.index(st.session_state["default_karat"]) if st.session_state[
                                                                                      "default_karat"] in karat_options else 0

        gold_karat = st.sidebar.selectbox(
            "👑 اختر عيار الذهب المفضّل:",
            karat_options,
            index=current_index
        )
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

# --- التحكم بالفريم الزمني والفترة الزمنية تلقائياً ---
timeframe_choice = st.sidebar.selectbox(
    "⏱️ الفريم الزمني (Timeframe):",
    ["ساعاتي (1H)", "يومي (1D)", "أسبوعي (1W)"],
    index=1
)

if timeframe_choice == "ساعاتي (1H)":
    selected_interval = "1h"
    time_period = "1mo"
elif timeframe_choice == "أسبوعي (1W)":
    selected_interval = "1wk"
    time_period = st.sidebar.selectbox("الفترة الزمنية:", ["1y", "2y", "5y"], index=1)
else:
    selected_interval = "1d"
    time_period = st.sidebar.selectbox("الفترة الزمنية:", ["1m", "3m", "6m", "1y", "2y"], index=3)

st.sidebar.markdown("---")

if selected_symbol == "GC=F":
    st.sidebar.subheader("💰 حاسبة الذهب المحلية (IQD)")
    iqd_rate = st.sidebar.number_input(
        "سعر صرف USD/IQD:",
        value=st.session_state["default_iqd_rate"],
        step=10.0
    )
    st.session_state["default_iqd_rate"] = iqd_rate
    user_mithqal = st.sidebar.number_input("عدد المثاقيل لديك:", value=1.0, min_value=0.1, step=0.5)
else:
    st.sidebar.subheader("💼 حاسبة الاستثمار الشخصي")
    user_quantity = st.sidebar.number_input("عدد الأسهم/الوحدات المملوكة:", value=1.0, min_value=0.01, step=0.1)

# --- جلب البيانات مع دعم الفريم والتخزين المؤقت ---
data = MarketEngine.get_market_data(selected_symbol, period=time_period, interval=selected_interval)

if data is None or data.empty:
    st.error(f"❌ لم يتم العثور على بيانات لـ ({selected_label}). يرجى التأكد من كتابة الاسم بصورة صحيحة.")
    st.stop()

latest_row = data.iloc[-1]
signal_label, rsi_status = MarketEngine.get_signal(latest_row)

st.sidebar.info(f"📍 الرمز الفعلي: **{selected_symbol}** | الفريم: **{timeframe_choice}**")

# --- العرض والتفاصيل ---
col_sig1, col_sig2, col_sig3, col_sig4 = st.columns(4)
col_sig1.metric("السعر الحالي", f"${latest_row['Close']:,.2f}")
col_sig2.metric("مؤشر RSI", f"{latest_row['RSI']:.1f}")
col_sig3.metric("حالة RSI", rsi_status)
col_sig4.metric("التوصية الحالية", signal_label)

# --- إظهار تنبيهات كشف نماذج الشموع اليابانية التلقائي ---
detected_patterns = MarketEngine.detect_candlestick_patterns(data)
if detected_patterns:
    for pattern in detected_patterns:
        st.info(f"🔍 **تنبيه نموذج فني مكتشف:** {pattern}")

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

    st.subheader(f"🧈 التحليل السعري للذهب — (عيار {selected_karat_name})")

    g_col1, g_col2, g_col3 = st.columns(3)
    g_col1.metric(f"سعر المثقال عيار {selected_karat_name} (IQD)", f"{mithqal_iqd:,.0f} د.ع")
    g_col2.metric(f"سعر الجرام عيار {selected_karat_name} (IQD)", f"{gram_iqd:,.0f} د.ع")
    g_col3.metric(f"قيمة ممتلكاتك ({user_mithqal} مثقال)", f"{total_val_iqd:,.0f} د.ع")
    st.markdown("---")

    share_text = (
        f"🏆 *تقرير الذهب اليوم (عيار {selected_karat_name})*\n"
        f"💵 السعر العالمي للأونصة: ${latest_row['Close']:,.2f}\n"
        f"🇮🇶 سعر المثقال: {mithqal_iqd:,.0f} د.ع\n"
        f"📊 المؤشر الفني: {signal_label}\n"
        f"تطبيق التحليل المالي الذكي 📈"
    )
else:
    st.subheader(f"📊 ملخص القيمة الاستثمارية لـ ({selected_label})")
    total_asset_val = latest_row['Close'] * user_quantity
    c1, c2 = st.columns(2)
    c1.metric("الكمية المملوكة", f"{user_quantity} وحدة/سهم")
    c2.metric("القيمة الإجمالية بالدولار", f"${total_asset_val:,.2f}")
    st.markdown("---")

    share_text = (
        f"📈 *تقرير سوق المال: ({selected_label})*\n"
        f"💵 السعر الحالي: ${latest_row['Close']:,.2f}\n"
        f"🎯 التوصية الفنية: {signal_label}\n"
        f"📉 مؤشر RSI: {latest_row['RSI']:.1f} ({rsi_status})\n"
        f"تطبيق التحليل المالي الذكي 📈"
    )

# --- الرسوم البيانية التفاعلية والمتقدمة ---
st.subheader(f"📊 التحليل الفني المتقدم: {selected_label} ({selected_symbol}) - فريم [{timeframe_choice}]")

tab_main, tab_oscillators, tab_advanced = st.tabs([
    "📈 السعر، بولنجر و VWAP / السيولة",
    "⚡ مؤشرات RSI & MACD",
    "🎯 Stochastic & قوة الاتجاه (ADX)"
])

# === التبويب الأول: رسم السعر الرئيسي + VWAP + Volume ===
with tab_main:
    has_volume = 'Volume' in data.columns and (data['Volume'] > 0).any()

    if has_volume:
        fig_main = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f"السعر ومتوسط VWAP ({selected_symbol})", "حجم التداول (Volume)")
        )
    else:
        fig_main = make_subplots(rows=1, cols=1, subplot_titles=(f"السعر ونطاقات بولنجر ({selected_symbol})",))

    # 1. رسم السعر ونطاقات بولنجر
    fig_main.add_trace(
        _plotly_go.Scatter(x=data.index, y=data['Close'], name='السعر', line=dict(color='#1f77b4', width=2)), row=1,
        col=1)
    fig_main.add_trace(
        _plotly_go.Scatter(x=data.index, y=data['BB_Upper'], name='Upper Band', line=dict(color='gray', dash='dash')),
        row=1, col=1)
    fig_main.add_trace(
        _plotly_go.Scatter(x=data.index, y=data['BB_Lower'], name='Lower Band', line=dict(color='gray', dash='dash')),
        row=1, col=1)

    # 2. خط VWAP البرتقالي
    if 'VWAP' in data.columns:
        fig_main.add_trace(_plotly_go.Scatter(x=data.index, y=data['VWAP'], name='VWAP (متوسط السيولة)',
                                              line=dict(color='#ff9f43', width=1.5, dash='dot')), row=1, col=1)

    # 3. أعمدة Volume
    if has_volume:
        vol_colors = ['#2ed573' if c >= o else '#ff4757' for c, o in zip(data['Close'], data['Open'])]
        fig_main.add_trace(_plotly_go.Bar(x=data.index, y=data['Volume'], name='Volume', marker_color=vol_colors),
                           row=2, col=1)

    fig_main.update_layout(height=550, showlegend=True, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_main, use_container_width=True, config={"responsive": True})

# === التبويب الثاني: مؤشرا RSI & MACD ===
with tab_oscillators:
    fig_osc = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("مؤشر القوة النسبية (RSI)", "مؤشر الماكد (MACD)")
    )

    fig_osc.add_trace(_plotly_go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='#9467bd')), row=1,
                      col=1)
    fig_osc.add_hline(y=70, line_dash="dot", line_color="red", row=1, col=1)
    fig_osc.add_hline(y=30, line_dash="dot", line_color="green", row=1, col=1)

    fig_osc.add_trace(_plotly_go.Scatter(x=data.index, y=data['MACD'], name='MACD', line=dict(color='#ff7f0e')), row=2,
                      col=1)
    fig_osc.add_trace(
        _plotly_go.Scatter(x=data.index, y=data['Signal_Line'], name='Signal', line=dict(color='#2ca02c')), row=2,
        col=1)
    fig_osc.add_trace(_plotly_go.Bar(x=data.index, y=data['MACD_Hist'], name='Histogram'), row=2, col=1)

    fig_osc.update_layout(height=500, showlegend=True, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_osc, use_container_width=True, config={"responsive": True})

# === التبويب الثالث: Stochastic & ADX ===
with tab_advanced:
    fig_adv = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("المذبذب العشوائي (Stochastic Oscillator %K & %D)", "مؤشر قوة الاتجاه (ADX)")
    )

    if 'Stoch_K' in data.columns:
        fig_adv.add_trace(
            _plotly_go.Scatter(x=data.index, y=data['Stoch_K'], name='%K Line', line=dict(color='#00d2d3')), row=1,
            col=1)
        fig_adv.add_trace(_plotly_go.Scatter(x=data.index, y=data['Stoch_D'], name='%D Line',
                                             line=dict(color='#ff9f43', dash='dash')), row=1, col=1)
        fig_adv.add_hline(y=80, line_dash="dot", line_color="red", row=1, col=1)
        fig_adv.add_hline(y=20, line_dash="dot", line_color="green", row=1, col=1)

    if 'ADX' in data.columns:
        fig_adv.add_trace(_plotly_go.Scatter(x=data.index, y=data['ADX'], name='ADX Trend Strength',
                                             line=dict(color='#54a0ff', width=2)), row=2, col=1)
        fig_adv.add_hline(y=25, line_dash="dot", line_color="yellow", row=2, col=1, annotation_text="اتجاه قَوِي (>25)")

    fig_adv.update_layout(height=500, showlegend=True, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_adv, use_container_width=True, config={"responsive": True})

# --- التقارير والتصدير والمشاركة ---
st.subheader("📥 تصدير البيانات والمشاركة المباشرة")
exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 1])

with exp_col1:
    excel_data = ReportGenerator.convert_df_to_excel(data)
    st.download_button(
        label=f"📊 تحميل Excel",
        data=excel_data,
        file_name=f"{selected_symbol}_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with exp_col2:
    word_doc = ReportGenerator.generate_rsi_word_doc()
    st.download_button(
        label="📝 تحميل دليل (Word)",
        data=word_doc,
        file_name="دليل_المؤشرات_الفنية.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

# ترميز النص للمشاركة
encoded_text = urllib.parse.quote(share_text)
wa_url = f"https://api.whatsapp.com/send?text={encoded_text}"
tg_url = f"https://t.me/share/url?url=&text={encoded_text}"

with exp_col3:
    st.markdown(
        f'''
        <div class="share-container">
            <a href="{wa_url}" target="_blank" class="share-btn-wa">💬 واتساب</a>
            <a href="{tg_url}" target="_blank" class="share-btn-tg">✈️ تليجرام</a>
        </div>
        ''',
        unsafe_allow_html=True
    )