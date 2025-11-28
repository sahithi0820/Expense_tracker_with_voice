# Expense_tracker_with_voice
A **Streamlit web app** to track your income and expenses. This app supports **adding transactions via text, CSV upload, and voice input**. It visualizes your spending and helps manage personal finances easily.

## **Features**

1. **Add Transaction Manually**
   - Add transactions with **date, description, category, amount, and type** (Expense/Income).
   - Categories are auto-detected from your description if left as "Uncategorized".

2. **Upload CSV**
   - Upload CSV files with columns like `Date`, `Description`, `Amount`, and optionally `Type`.
   - The app automatically cleans the data and categorizes transactions.

3. **Voice Transaction Input**
   - Speak your transaction and let the app parse it into **Amount, Date, Category, Type, and Description**.
   - Example inputs:
     - `"Spent 500 on groceries yesterday"`
     - `"Received 10000 salary on 20 November 2025"`
   - Supports **relative dates** like "yesterday", "day before yesterday", "last week", etc.
   - Categories are detected from keywords; unknown categories default to "Uncategorized".
   - After parsing, you can **preview** and **confirm** before saving.

4. **Dashboard**
   - View **total income, total expense, and net savings**.
   - See **category-wise expense pie chart**.

5. **View All Transactions**
   - Browse all your transactions in a table.

6. **Reset Database**
   - Helps to reset database and start fresh.

---

## **Setup Instructions**

### 1. Clone the repository:

git clone <repo_url>
cd <repo_folder>

### Create a Python virtual environment (recommended):

python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate # Linux/macOS

### Install dependencies:

pip install -r requirements.txt

### Run the Streamlit app:

streamlit run app.py

### Open the link provided by Streamlit in your browser to start using the app.

## Notes

Voice Input: Requires a microphone and pyaudio. Make sure your system allows access to the mic.

Data Storage: Transactions are stored locally in database.db.

If you share the app via Streamlit Cloud, each user will have a separate session, so their uploads will not be shared with others.

Category Detection: Uses predefined keywords for auto-categorization.

Date Recognition: Supports explicit dates like 20 November 2025 or relative dates like yesterday.
