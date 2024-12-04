import streamlit as st

st.markdown('Information about live market analysis')

st.markdown("""
1. For stock time should be between 9:30 AM EST - 4:00 PM EST of a Business Day. 
2. Perminute data is extracted from Yahoo Finance Api with yfinance package.
3. It also gives the voice notification for SMA5 status and Higher High or Low status for 3 minutes.
        """)
