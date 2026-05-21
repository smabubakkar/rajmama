# app.py

import streamlit as st
import pandas as pd
import yfinance as yf
from io import BytesIO

st.set_page_config(
    page_title="Daily Stock High Low Export",
    layout="wide"
)

st.title("📈 Daily Stock High / Low Export")

st.write("""
Enter stock symbols separated by commas.

Examples:
- RELIANCE.NS, TCS.NS, INFY.NS
- AAPL, MSFT, TSLA
""")

# =========================
# INPUTS
# =========================

stock_input = st.text_area(
    "Enter Stock Codes",
    height=120,
    placeholder="RELIANCE.NS, TCS.NS, INFY.NS"
)

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input("Start Date")

with col2:
    end_date = st.date_input("End Date")

# =========================
# BUTTON
# =========================

if st.button("Fetch Daily Data"):

    if not stock_input.strip():
        st.warning("Please enter stock symbols.")
        st.stop()

    stock_list = [
        stock.strip().upper()
        for stock in stock_input.split(",")
        if stock.strip()
    ]

    all_data = []

    progress_bar = st.progress(0)

    for idx, symbol in enumerate(stock_list):

        try:

            df = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=False
            )

            if df.empty:
                continue

            # Handle multi-index columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Reset index so Date becomes column
            df.reset_index(inplace=True)

            # Keep only required columns
            df = df[[
                "Date",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            ]]

            # Add stock column
            df["Stock"] = symbol

            # Reorder columns
            df = df[[
                "Stock",
                "Date",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            ]]

            # Round prices
            for col in ["Open", "High", "Low", "Close"]:
                df[col] = df[col].round(2)

            all_data.append(df)

        except Exception as e:
            st.error(f"{symbol} -> {str(e)}")

        progress_bar.progress((idx + 1) / len(stock_list))

    # =========================
    # FINAL OUTPUT
    # =========================

    if all_data:

        final_df = pd.concat(all_data, ignore_index=True)

        final_df["Date"] = pd.to_datetime(
            final_df["Date"]
        ).dt.strftime("%Y-%m-%d")

        st.success("Data fetched successfully!")

        st.dataframe(
            final_df,
            use_container_width=True,
            height=600
        )

        # =========================
        # EXCEL DOWNLOAD
        # =========================

        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            final_df.to_excel(
                writer,
                index=False,
                sheet_name="Daily_High_Low"
            )

        output.seek(0)

        st.download_button(
            label="📥 Download Excel",
            data=output,
            file_name="daily_stock_high_low.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("No data found.")