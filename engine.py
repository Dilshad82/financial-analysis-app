import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


class MarketEngine:

    @staticmethod
    @st.cache_data(ttl=180)  # وقت الكاش 3 دقائق
    def get_market_data(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """جلب البيانات المالية بناءً على الفترة والفريم الزمني المحدد"""
        # تم إضافة interval=interval هنا 👇
        df = yf.download(ticker, period=period, interval=interval, progress=False)

        if df.empty:
            return df

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna(subset=['Close']).copy()

        # --- المؤشرات الأساسية والمتقدمة ---
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        std = df['Close'].rolling(window=20).std()
        df['BB_Middle'] = df['SMA_20']
        df['BB_Upper'] = df['BB_Middle'] + (std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (std * 2)

        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = np.where(loss == 0, 100, gain / np.where(loss == 0, 1, loss))
        df['RSI'] = 100 - (100 / (1 + rs))
        df['RSI'] = df['RSI'].fillna(50)

        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal_Line']

        # VWAP
        if 'Volume' in df.columns and (df['Volume'] > 0).any():
            typical_price = (df['High'] + df['Low'] + df['Close']) / 3
            df['VWAP'] = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
        else:
            df['VWAP'] = df['Close']

        # Stochastic
        low_14 = df['Low'].rolling(window=14).min()
        high_14 = df['High'].rolling(window=14).max()
        stoch_range = high_14 - low_14
        df['Stoch_K'] = np.where(stoch_range == 0, 50, 100 * ((df['Close'] - low_14) / stoch_range))
        df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()

        # ADX
        up_move = df['High'].diff()
        down_move = -df['Low'].diff()
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        tr = pd.concat(
            [df['High'] - df['Low'], (df['High'] - df['Close'].shift()).abs(), (df['Low'] - df['Close'].shift()).abs()],
            axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        atr_safe = np.where(atr == 0, 1, atr)
        plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(14).mean() / atr_safe)
        minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(14).mean() / atr_safe)
        di_sum = np.where((plus_di + minus_di) == 0, 1, plus_di + minus_di)
        df['ADX'] = pd.Series(100 * (abs(plus_di - minus_di) / di_sum), index=df.index).rolling(14).mean().fillna(20)

        return df

    @staticmethod
    def detect_candlestick_patterns(df: pd.DataFrame) -> list:
        """خوارزمية الكشف التلقائي عن نماذج الشموع اليابانية للشمعة الأخيرة"""
        if len(df) < 2:
            return []

        patterns = []
        curr = df.iloc[-1]
        prev = df.iloc[-2]

        body = abs(curr['Close'] - curr['Open'])
        candle_range = curr['High'] - curr['Low']

        if candle_range == 0:
            return []

        lower_shadow = min(curr['Open'], curr['Close']) - curr['Low']
        upper_shadow = curr['High'] - max(curr['Open'], curr['Close'])

        # 1. نموذج الدوجي (Doji)
        if body <= (candle_range * 0.1):
            patterns.append("🕯️ شمعة دوجي (تردد وحيرة في الاتجاه)")

        # 2. نموذج المطرقة (Hammer - ارتداد صاعد)
        elif lower_shadow >= (2 * body) and upper_shadow <= (0.2 * body):
            patterns.append("🔨 شمعة مطرقة (إشارة ارتداد صاعد)")

        # 3. نموذج الشمعة الابتلاعية الشرائية (Bullish Engulfing)
        elif prev['Close'] < prev['Open'] and curr['Close'] > curr['Open']:
            if curr['Close'] > prev['Open'] and curr['Open'] < prev['Close']:
                patterns.append("🟢 شمعة ابتلاعية شرائية (قوة شراء قوية)")

        # 4. نموذج الشمعة الابتلاعية البيعية (Bearish Engulfing)
        elif prev['Close'] > prev['Open'] and curr['Close'] < curr['Open']:
            if curr['Open'] > prev['Close'] and curr['Close'] < prev['Open']:
                patterns.append("🔴 شمعة ابتلاعية بيعية (ضغوط بيع قوية)")

        return patterns

    @staticmethod
    def get_signal(row) -> tuple:
        rsi = row['RSI']
        price = row['Close']
        sma = row['SMA_20']
        adx = row.get('ADX', 20)
        stoch_k = row.get('Stoch_K', 50)

        if rsi >= 70:
            rsi_status = "غالٍ جداً 🔴"
        elif rsi <= 30:
            rsi_status = "رخيص جداً 🟢"
        else:
            rsi_status = "سعر طبيعي ⚪"

        trend_strong = adx > 25

        if price > sma and rsi < 50 and stoch_k < 30:
            signal_label = "🟢 فرصة شراء قوية" if trend_strong else "🟢 فرصة شراء"
        elif price < sma and rsi > 55 and stoch_k > 70:
            signal_label = "🔴 فرصة بيع قوية" if trend_strong else "🔴 فرصة بيع"
        else:
            signal_label = "⚪ راقب فقط"

        return signal_label, rsi_status

    @staticmethod
    def calculate_gold_units(usd_price: float, karat: int = 21, iqd_rate: float = 1480.0) -> dict:
        gram_24_usd = usd_price / 31.1034768
        karat_factor = karat / 24.0
        gram_usd = gram_24_usd * karat_factor
        mithqal_usd = gram_usd * 5.0
        return {
            "gram_usd": gram_usd,
            "mithqal_usd": mithqal_usd,
            "gram_iqd": gram_usd * iqd_rate,
            "mithqal_iqd": mithqal_usd * iqd_rate
        }