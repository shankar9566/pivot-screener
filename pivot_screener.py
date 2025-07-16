import yfinance as yf
import pandas as pd
import streamlit as st

st.set_page_config(page_title="F&O Breakout Screener", layout="wide")
st.title("📊 CPR + Camarilla Breakout Screener – NSE F&O Stocks")

# === Hardcoded F&O symbols === (Replace with full list if needed)
fo_stocks = pd.read_csv("fo_stocks.csv")["Symbol"].tolist() # Replace with full list or CSV loader

threshold = st.slider("CPR Width % Threshold", 0.1, 2.0, 0.5, 0.1)

@st.cache_data
def download_and_screen(symbol):
    try:
        df = yf.download(symbol, period="7d", interval="1d", progress=False)
        if df.empty or len(df) < 2:
            return None

        df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

        df['PP'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['BC'] = (df['High'] + df['Low']) / 2
        df['TC'] = (2 * df['PP']) - df['BC']
        df['CPR_Width%'] = abs(df['TC'] - df['BC']) / df['Close'] * 100

        range_ = df['High'] - df['Low']
        df['H4'] = df['Close'] + (range_ * 1.1 / 2)
        df['L4'] = df['Close'] - (range_ * 1.1 / 2)

        df['StrongBullBreak'] = (df['CPR_Width%'] < threshold) & (df['Close'] > df['TC']) & (df['Close'] > df['H4'])
        df['StrongBearBreak'] = (df['CPR_Width%'] < threshold) & (df['Close'] < df['BC']) & (df['Close'] < df['L4'])

        return df.iloc[-1]
    except Exception as e:
        return None

# === Screen all F&O stocks ===
results = []
progress = st.progress(0)
total = len(fo_stocks)

for i, sym in enumerate(fo_stocks):
    row = download_and_screen(sym)
    if row is not None:
        if row['StrongBullBreak']:
            results.append([sym, "Strong Bull Break", round(row['CPR_Width%'], 2)])
        elif row['StrongBearBreak']:
            results.append([sym, "Strong Bear Break", round(row['CPR_Width%'], 2)])
    progress.progress((i+1)/total)

# === Output Results ===
if results:
    df_out = pd.DataFrame(results, columns=["Symbol", "Signal", "CPR Width %"])
    st.success(f"✅ {len(df_out)} breakout(s) found")
    st.dataframe(df_out)
    st.download_button("📥 Download CSV", df_out.to_csv(index=False), "CPR_Screener_Output.csv", "text/csv")
else:
    st.warning("No breakout signals found today.")
