import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import base64
from st_audiorec import st_audiorec
from utils import (init_db, insert_transactions, get_all_transactions, categorize_description, parse_upload, style_money,default_categories, parse_voice_transaction)

#For voice input
import speech_recognition as sr
import dateparser
import re
import sounddevice as sd
from scipy.io.wavfile import write
import tempfile


st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="wide", initial_sidebar_state="expanded")

#Header
st.markdown("""
            <h1 style='text-align:center; color:#4CAF50;'>💰 Personal Finance & Expense Tracker</h1>
            <p style='text-align:center; font-size:18px;'>
            Track expenses, upload CSVs, visualize spending, and manage your money better.
            </p><br>
        """, unsafe_allow_html=True)

init_db()

#Sidebar

st.sidebar.header("🔧 Options")
menu = st.sidebar.radio("Select", ["➕ Add Transaction", "📤 Upload CSV", "🎤 Add via Voice", "📊 Dashboard", "📁 View All"])

if st.sidebar.button("🗑 Reset Database"):
    from utils import reset_db
    reset_db()
    st.sidebar.success("Database reset! Starting fresh.")


# ADD TRANSACTION 
if menu == "➕ Add Transaction":
    st.subheader("Add New Transaction")

    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date", datetime.date.today())
        desc = st.text_input("Description")
        amount = st.number_input("Amount (₹)", min_value=0.00, step=0.5)
    with col2:
        ttype = st.selectbox("Type", ["Expense", "Income"])
        category = st.selectbox("Category", default_categories())

    if st.button("Add"):
        final_category = category
        if category == "Uncategorized":
            final_category = categorize_description(desc)

        insert_transactions(date, desc, final_category, amount, ttype)
        st.success("Transaction added successfully!")

# UPLOAD CSV 
elif menu == "📤 Upload CSV":
    st.subheader("Upload CSV")

    uploaded_file = st.file_uploader("Choose CSV File", type=["csv"])
    if uploaded_file:
        try:
            new_data = parse_upload(uploaded_file)
            for _, row in new_data.iterrows():
                insert_transactions(row["Date"], row["Description"], row["Category"], row["Amount"], row["Type"])
            st.success("CSV uploaded and saved successfully!")

        except Exception as e:
            st.error(str(e))

#Voice Input
elif menu == "🎤 Add via Voice":
    st.subheader("Add Transaction via Voice")
    st.info("Click 'Record Transaction' and speak your transaction. Example: 'Spent 500 on groceries yesterday' or 'Received 10000 salary today")

    from st_audiorec import st_audiorec  # browser recorder

    audio_bytes = st_audiorec()  # returns raw audio bytes automatically

    if audio_bytes is not None:
        st.success("Audio captured! Converting to text...")

        import speech_recognition as sr

        r = sr.Recognizer()
        import io

        audio_file = io.BytesIO(audio_bytes)
        #Recognize speech
        r = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio = r.record(source)

        try:
            text = r.recognize_google(audio)
            st.success(f"You said: {text}")

            parsed = parse_voice_transaction(text)

            amount = parsed["amount"]
            date = parsed["date"]
            category = parsed["category"]
            ttype = parsed["type"]
            desc = text
            
            st.write("### Parsed Transaction")
            st.write(f"- **Amount:** ₹{amount}")
            st.write(f"- **Date:** {date}")
            st.write(f"- **Type:** {ttype}")
            st.write(f"- **Category:** {category}")

            if st.button("✔ Save Transaction"):
                insert_transactions(date, desc, category, amount, ttype)
                st.success("Transaction added successfully!")
                
        except Exception as e:
            st.error("Could not recognize audio:" + str(e))

#Dashboard
elif menu == "📊 Dashboard":
    df = get_all_transactions()
    if df.empty:
        st.warning("No transactions yet. Add or upload to see dashboard.")
    else:
        st.subheader("📊 Financial Dashboard")

        # Summary cards
        col1, col2, col3 = st.columns(3)

        total_income = df[df["Type"] == "Income"]["Amount"].sum()
        total_expense = df[df["Type"] == "Expense"]["Amount"].sum()
        net_savings = total_income - total_expense

        col1.metric("Total Income", style_money(total_income))
        col2.metric("Total Expense", style_money(total_expense))
        col3.metric("Net Savings", style_money(net_savings))

        # Charts
        st.write("### 📌 Category-wise Spending")

        category_expense = df[df["Type"] == "Expense"].groupby("Category")["Amount"].sum()
        if not category_expense.empty:
            fig = px.pie(
            names=category_expense.index,
            values=category_expense.values,
            title="Expense by Category",
        )
        st.plotly_chart(fig, use_container_width=True)

# VIEW ALL 
elif menu == "📁 View All":
    df = get_all_transactions()
    st.subheader("All Transactions")

    if df.empty:
        st.info("No data available.")
    else:
        st.dataframe(df)

st.markdown("---")
st.markdown("Built with ❤️")