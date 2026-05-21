# app.py

import streamlit as st
import pandas as pd
import yfinance as yf
from io import BytesIO

st.set_page_config(
    page_title="Intraday High Low Finder",
    layout="wide"
)

st.title("📈 Intraday High / Low Time Finder (IST)")

st.write("""
Get:
- Day High
- Day Low
- High Time (IST)
- Low Time (IST)

for multiple stocks.
""")

# =====================================
# INPUTS
# =====================================

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

# =====================================
# BUTTON
# =====================================

if st.button("Fetch Data"):

    if not stock_input.strip():
        st.warning("Please enter stock symbols.")
        st.stop()

    stock_list = [
        s.strip().upper()
        for s in stock_input.split(",")
        if s.strip()
    ]

    final_rows = []

    progress = st.progress(0)

    for stock_index, symbol in enumerate(stock_list):

        try:

            # =====================================
            # DOWNLOAD 5 MIN DATA
            # =====================================

            df = yf.download(
                symbol,
                start=start_date,
                end=end_date + pd.Timedelta(days=1),
                interval="5m",
                progress=False,
                auto_adjust=False
            )

            if df.empty:
                continue

            # =====================================
            # FIX MULTI INDEX
            # =====================================

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df.reset_index(inplace=True)

            # =====================================
            # RENAME DATETIME COLUMN
            # =====================================

            if "Datetime" in df.columns:
                df.rename(
                    columns={"Datetime": "DateTime"},
                    inplace=True
                )

            # =====================================
            # CONVERT TO IST
            # =====================================

            df["DateTime"] = pd.to_datetime(
                df["DateTime"],
                utc=True
            )

            df["DateTime"] = df["DateTime"].dt.tz_convert(
                "Asia/Kolkata"
            )

            # =====================================
            # EXTRACT DATE + TIME
            # =====================================

            df["Date"] = df["DateTime"].dt.date

            df["Time"] = df["DateTime"].dt.strftime(
                "%H:%M"
            )

            # =====================================
            # GROUP BY DATE
            # =====================================

            grouped = df.groupby("Date")

            for date, day_df in grouped:

                # Day High
                high_value = round(
                    float(day_df["High"].max()),
                    2
                )

                # Day Low
                low_value = round(
                    float(day_df["Low"].min()),
                    2
                )

                # High Row
                high_row = day_df.loc[
                    day_df["High"].idxmax()
                ]

                # Low Row
                low_row = day_df.loc[
                    day_df["Low"].idxmin()
                ]

                # Open / Close
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

                    "Day High": high_value,
                    "High Time (IST)": high_row["Time"],

                    "Day Low": low_value,
                    "Low Time (IST)": low_row["Time"],

                    "Open": open_price,
                    "Close": close_price
                })

        except Exception as e:

            st.error(f"{symbol} -> {str(e)}")

        progress.progress(
            (stock_index + 1) / len(stock_list)
        )

    # =====================================
    # FINAL OUTPUT
    # =====================================

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

        # =====================================
        # EXCEL EXPORT
        # =====================================

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