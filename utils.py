import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import re
import dateparser
from word2number import w2n

DB_FILE = "database.db"

_CATEGORY_KEYWORDS = {
    "Groceries": ["grocery", "super", "mart", "bigbasket"],
    "Dining": ["restaurant", "dine", "cafe", "coffee", "dominos", "mc", "kfc", "pizza"],
    "Transport": ["uber", "ola", "taxi", "train", "bus", "metro", "petrol"],
    "Rent": ["rent", "landlord", "housing"],
    "Utilities": ["electric", "water", "bill", "gas", "utility"],
    "Entertainment": ["netflix", "prime", "movie", "theater", "spotify"],
    "Health": ["pharm", "clinic", "hospital", "dental", "doctor"],
    "Shopping": ["amazon", "flipkart", "myntra", "store"],
    "Subscriptions": ["subscription", "membership"],
    "Education": ["college", "university", "course", "udemy", "coursera"],
    "Insurance": ["insurance", "premium"],
    "Taxes": ["tax", "gst"],
    "Transfers": ["transfer", "neft", "imps", "rtgs", "upi", "paytm", "phonepe"]
}

def extract_amount(text):
    match = re.search(r"(\d+(\.\d+)?)", text)
    if match:
        return float(match.group())
    else:
        # Try to convert words to numbers
        try:
            return float(w2n.word_to_num(text))
        except:
            return None

def extract_category(text):
    text =text.lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        for w in keywords:
            if w.lower() in text: 
                return category
    return "Uncategorized"

def extract_date(text):
    text = text.lower().strip()
    if "day before yesterday" in text:
        return (datetime.now() - timedelta(days=2)).date()
    
    if "yesterday" in text:
        return (datetime.now() - timedelta(days=1)).date()
    
    if "tomorrow" in text:
        return (datetime.now() + timedelta(days=1)).date()
    
    if "lastweek" in text:
        return (datetime.now() - timedelta(days=7)).date()
    
    if "lastmonth" in text:
        return (datetime.now() - timedelta(days=30)).date()
    
    cleaned = re.sub(r"(on|at|the|of|in)\s+", "", text).strip()
    
    parsed = dateparser.parse(cleaned)
    if parsed is None:
        try:

            match = re.search(r"\b(\d{1,2}(?:st|nd|rd|th)?[\s./-]+[a-zA-Z]+[\s./-]+\d{2,4})\b",
                text,
                flags=re.IGNORECASE)
            if match:
                parsed = dateparser.parse(match.group())
        
        except re.error:
            parsed = None
    
    if parsed is None:
        try:
            match = re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text)
            if match:
                parsed = dateparser.parse(match.group())
        except re.error:
            parsed = None
    
    return parsed.date() if parsed else datetime.now().date()

def parse_voice_transaction(text):
    text = text.lower()

    amount = extract_amount(text)
    category = extract_category(text)
    date = extract_date(text)

    ttype = "Income" if any(k in text.lower() for k in ["salary", "credited", "income", "earned", "received", "got"]) else "Expense"

    return {
        "amount" : amount,
        "category": category,
        "date": date,
        "type": ttype
    }

def default_categories():
    return list(_CATEGORY_KEYWORDS.keys()) + ["Uncategorized"]

def categorize_description(text: str) -> str:
    if not isinstance(text, str) or text.strip() == "":
        return "Uncategorized"

    txt = text.lower()

    for cat, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in txt for kw in keywords):
            return cat
        
    return "Uncategorized"

#Database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
             CREATE TABLE IF NOT EXISTS transactions(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              Date TEXT,
              Description TEXT,
              Category TEXT,
              Amount REAL,
              Type TEXT
              )
    """)
    conn.commit()
    conn.close()

def insert_transactions(date, description, category, amount, ttype):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(""" 
        INSERT INTO transactions (Date, Description, Category, Amount, Type)
        VALUES(?, ?, ?, ?, ?)
    """,(str(date), description, category, amount, ttype))
    conn.commit()
    conn.close()

def reset_db():
    import os
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    init_db()

def get_all_transactions():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    return df

#CSV Upload
def parse_upload(uploaded_file):
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.lower()

    # Auto-detect column names
    mapping = {}
    for col in df.columns:
        low = col.lower()
        if "date" in low:
            mapping[col] = "Date"
        elif "desc" in low:
            mapping[col] = "Description"
        elif "amount" in low or "value" in low:
            mapping[col] = "Amount"
        elif "type" in low or "income" in low or "expense" in low:
            mapping[col] = "Type"
        else:
            mapping[col] = col

    df = df.rename(columns=mapping)

    # Required columns
    if not all(c in df.columns for c in ["Date", "Description", "Amount"]):
        raise ValueError("CSV must include: Date, Description, Amount")

    # Clean columns
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").fillna(method="ffill")
    df["Amount"] = (df["Amount"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.extract(r"([-+]?\d*\.?\d+)")[0]
        .astype(float)
        .fillna(0.0)
    )

    # Detect Type if missing
    if "Type" not in df.columns:
        df["Type"] = df["Amount"].apply(lambda x: "Income" if x >= 0 else "Expense")

    else:
        df["Type"] = df["Type"].astype(str).str.strip().str.title()
        df.loc[~df["Type"].isin(["Income", "Expense"]), "Type"] = "Expense"
    
    df["Category"] = df["Description"].apply(categorize_description)

    return df[["Date", "Description", "Category", "Amount", "Type"]]


def style_money(x):
    try:
        return "₹{:,.2f}".format(float(x))
    except:
        return str(x)