# app.py

import streamlit as st
import pandas as pd
import yfinance as yf
from io import BytesIO

st.set_page_config(
    page_title="Intraday High Low Finder",
    layout="wide"
)

st.title("📈 Intraday High / Low Time Finder")

stock_input = st.text_area(
    "Enter Stock Codes (comma separated)",
    placeholder="RELIANCE.NS, TCS.NS"
)

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input("Start Date")

with col2:
    end_date = st.date_input("End Date")

if st.button("Fetch Data"):

    stock_list = [
        s.strip().upper()
        for s in stock_input.split(",")
        if s.strip()
    ]

    final_rows = []

    progress = st.progress(0)

    for stock_index, symbol in enumerate(stock_list):

        try:

            # 5-minute data
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

            # Fix MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df.reset_index(inplace=True)

            # Rename Datetime column
            if "Datetime" in df.columns:
                df.rename(columns={"Datetime": "DateTime"}, inplace=True)

            df["DateTime"] = pd.to_datetime(df["DateTime"])

            # Extract Date + Time
            df["Date"] = df["DateTime"].dt.date
            df["Time"] = df["DateTime"].dt.strftime("%H:%M")

            grouped = df.groupby("Date")

            for date, day_df in grouped:

                high_value = round(day_df["High"].max(), 2)
                low_value = round(day_df["Low"].min(), 2)

                high_row = day_df.loc[
                    day_df["High"].idxmax()
                ]

                low_row = day_df.loc[
                    day_df["Low"].idxmin()
                ]

                final_rows.append({
                    "Stock": symbol,
                    "Date": str(date),

                    "Day High": high_value,
                    "High Time": high_row["Time"],

                    "Day Low": low_value,
                    "Low Time": low_row["Time"],

                    "Open": round(float(day_df.iloc[0]["Open"]), 2),
                    "Close": round(float(day_df.iloc[-1]["Close"]), 2),
                })

        except Exception as e:
            st.error(f"{symbol} -> {str(e)}")

        progress.progress((stock_index + 1) / len(stock_list))

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

        # Excel Export
        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            result_df.to_excel(
                writer,
                index=False,
                sheet_name="Intraday_High_Low"
            )

        output.seek(0)

        st.download_button(
            label="📥 Download Excel",
            data=output,
            file_name="intraday_high_low.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("No data found.")