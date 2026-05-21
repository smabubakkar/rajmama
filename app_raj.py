# app.py

import streamlit as st
import pandas as pd
import yfinance as yf
from io import BytesIO
import time

st.set_page_config(
    page_title="Intraday High Low Finder",
    layout="wide"
)

st.title("📈 Intraday High / Low Finder (IST)")

st.write("""
Features:
- Day High
- Day Low
- High Time (IST)
- Low Time (IST)
- Day of Week
- Excel Download
""")

# =========================================
# CACHE DOWNLOADS
# =========================================

@st.cache_data(show_spinner=False)
def fetch_stock_data(symbol, start_date, end_date):

    df = yf.download(
        symbol,
        start=start_date,
        end=end_date + pd.Timedelta(days=1),
        interval="5m",
        progress=False,
        auto_adjust=False,
        threads=False
    )

    return df


# =========================================
# INPUTS
# =========================================

stock_input = st.text_area(
    "Enter Stock Codes (comma separated)",
    placeholder="RELIANCE.NS, TCS.NS, INFY.NS",
    height=120
)

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input("Start Date")

with col2:
    end_date = st.date_input("End Date")

# =========================================
# BUTTON
# =========================================

if st.button("Fetch Data"):

    if not stock_input.strip():
        st.warning("Please enter stock symbols.")
        st.stop()

    # Yahoo limitation warning
    days_diff = (end_date - start_date).days

    if days_diff > 60:
        st.warning(
            "Yahoo Finance intraday data works best within 60 days. "
            "Larger ranges may fail or get rate-limited."
        )

    stock_list = [
        s.strip().upper()
        for s in stock_input.split(",")
        if s.strip()
    ]

    final_rows = []

    progress = st.progress(0)

    for stock_index, symbol in enumerate(stock_list):

        try:

            # =========================================
            # SMALL DELAY TO AVOID RATE LIMIT
            # =========================================

            time.sleep(1)

            # =========================================
            # DOWNLOAD DATA
            # =========================================

            df = fetch_stock_data(
                symbol,
                start_date,
                end_date
            )

            if df.empty:
                st.warning(f"No data found for {symbol}")
                continue

            # =========================================
            # FIX MULTI INDEX
            # =========================================

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df.reset_index(inplace=True)

            # =========================================
            # DATETIME COLUMN
            # =========================================

            if "Datetime" in df.columns:
                df.rename(
                    columns={"Datetime": "DateTime"},
                    inplace=True
                )

            # =========================================
            # UTC → IST
            # =========================================

            df["DateTime"] = pd.to_datetime(
                df["DateTime"],
                utc=True
            )

            df["DateTime"] = df["DateTime"].dt.tz_convert(
                "Asia/Kolkata"
            )

            # =========================================
            # EXTRACT DATE/TIME
            # =========================================

            df["Date"] = df["DateTime"].dt.date

            df["Time"] = df["DateTime"].dt.strftime(
                "%H:%M"
            )

            df["Day"] = df["DateTime"].dt.day_name()

            # =========================================
            # GROUP BY DATE
            # =========================================

            grouped = df.groupby("Date")

            for date, day_df in grouped:

                high_value = round(
                    float(day_df["High"].max()),
                    2
                )

                low_value = round(
                    float(day_df["Low"].min()),
                    2
                )

                high_row = day_df.loc[
                    day_df["High"].idxmax()
                ]

                low_row = day_df.loc[
                    day_df["Low"].idxmin()
                ]

                open_price = round(
                    float(day_df.iloc[0]["Open"]),
                    2
                )

                close_price = round(
                    float(day_df.iloc[-1]["Close"]),
                    2
                )

                final_rows.append({

                    "Stock": symbol,

                    "Date": str(date),

                    "Day": high_row["Day"],

                    "Open": open_price,

                    "Day High": high_value,
                    "High Time (IST)": high_row["Time"],

                    "Day Low": low_value,
                    "Low Time (IST)": low_row["Time"],

                    "Close": close_price
                })

        except Exception as e:

            st.error(f"{symbol} -> {str(e)}")

        progress.progress(
            (stock_index + 1) / len(stock_list)
        )

    # =========================================
    # FINAL OUTPUT
    # =========================================

    if final_rows:

        result_df = pd.DataFrame(final_rows)

        result_df.sort_values(
            by=["Stock", "Date"],
            inplace=True
        )

        st.success("Completed!")

        st.dataframe(
            result_df,
            use_container_width=True,
            height=700
        )

        # =========================================
        # EXCEL EXPORT
        # =========================================

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            result_df.to_excel(
                writer,
                index=False,
                sheet_name="Intraday_High_Low"
            )

        output.seek(0)

        st.download_button(
            label="📥 Download Excel",
            data=output,
            file_name="intraday_high_low_ist.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("No data found.")