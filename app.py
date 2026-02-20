import streamlit as st
import os
from dotenv import load_dotenv
import bcrypt
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import json
import uuid
import base64

# Load environment variables
load_dotenv()

# Data storage using JSON files
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.json")

def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return []

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4, default=str)

# Initialize data
users = load_data(USERS_FILE)
transactions = load_data(TRANSACTIONS_FILE)

# Helper functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def register_user(name, email, password):
    global users
    if any(u['email'] == email for u in users):
        return False, "Email already exists!"
    hashed = hash_password(password)
    user = {
        "id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "password": base64.b64encode(hashed).decode('utf-8')
    }
    users.append(user)
    save_data(USERS_FILE, users)
    return True, "Registration successful!"

def login_user(email, password):
    global users
    for user in users:
        if user['email'] == email:
            hashed_bytes = base64.b64decode(user['password'])
            if check_password(password, hashed_bytes):
                return True, user
    return False, "Invalid email or password"

def add_transaction(user_id, amount, type_, category, reference, description, date):
    global transactions
    trans = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "amount": amount,
        "type": type_,
        "category": category,
        "reference": reference,
        "description": description,
        "date": date.isoformat()
    }
    transactions.append(trans)
    save_data(TRANSACTIONS_FILE, transactions)
    return True, "Transaction added successfully!"

def get_transactions(user_id, frequency="7", start_date=None, end_date=None, type_filter="all"):
    global transactions
    trans = [t for t in transactions if t['user_id'] == user_id]
    
    if type_filter != "all":
        trans = [t for t in trans if t['type'] == type_filter]
    
    if frequency != "custom":
        days = int(frequency)
        cutoff = datetime.now() - timedelta(days=days)
        trans = [t for t in trans if datetime.fromisoformat(t['date']) >= cutoff]
    else:
        if start_date and end_date:
            trans = [t for t in trans if start_date <= datetime.fromisoformat(t['date']).date() <= end_date]
    
    return sorted(trans, key=lambda x: x['date'], reverse=True)

def delete_transaction(trans_id):
    global transactions
    transactions = [t for t in transactions if t['id'] != trans_id]
    save_data(TRANSACTIONS_FILE, transactions)
    return True, "Transaction deleted!"

def update_transaction(trans_id, updates):
    global transactions
    for t in transactions:
        if t['id'] == trans_id:
            t.update(updates)
            save_data(TRANSACTIONS_FILE, transactions)
            return True, "Transaction updated!"
    return False, "Transaction not found"

# Helper functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# Streamlit app
st.set_page_config(page_title="Expense Management System", layout="wide")

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# Sidebar navigation
if st.session_state.logged_in:
    st.sidebar.title(f"Welcome, {st.session_state.user['name']}!")
    page = st.sidebar.radio("Navigation", ["Dashboard", "Add Transaction", "Analytics", "Logout"])
    if page == "Logout":
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.page = "login"
        st.rerun()
else:
    page = "login"

# Main content
if not st.session_state.logged_in:
    st.title("Expense Management System")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.header("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            success, result = login_user(email, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.user = result
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error(result)
    
    with tab2:
        st.header("Register")
        name = st.text_input("Name", key="reg_name")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_password")
        if st.button("Register"):
            success, message = register_user(name, email, password)
            if success:
                st.success(message)
            else:
                st.error(message)

else:
    if page == "Dashboard":
        st.title("Dashboard")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            frequency = st.selectbox("Frequency", ["7", "30", "365", "custom"], key="freq")
        with col2:
            type_filter = st.selectbox("Type", ["all", "income", "expense"], key="type_filt")
        with col3:
            if frequency == "custom":
                date_range = st.date_input("Date Range", [], key="date_range")
                start_date = date_range[0] if len(date_range) > 0 else None
                end_date = date_range[1] if len(date_range) > 1 else None
            else:
                start_date = None
                end_date = None
        
        # Get transactions
        trans = get_transactions(st.session_state.user["id"], frequency, start_date, end_date, type_filter)
        
        if trans:
            df = pd.DataFrame(trans)
            df["date"] = pd.to_datetime(df["date"])
            df = df.drop(columns=["id", "user_id"])
            st.dataframe(df)
            
            # Edit/Delete
            selected = st.selectbox("Select transaction to edit/delete", df.index, format_func=lambda x: f"{df.iloc[x]['description']} - {df.iloc[x]['amount']}")
            if selected is not None:
                trans_id = trans[selected]["id"]
                if st.button("Delete"):
                    success, msg = delete_transaction(trans_id)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                
                st.subheader("Edit Transaction")
                with st.form("edit_form"):
                    amount = st.number_input("Amount", value=df.iloc[selected]["amount"])
                    type_ = st.selectbox("Type", ["income", "expense"], index=0 if df.iloc[selected]["type"] == "income" else 1)
                    category = st.text_input("Category", value=df.iloc[selected]["category"])
                    reference = st.text_input("Reference", value=df.iloc[selected]["reference"])
                    description = st.text_input("Description", value=df.iloc[selected]["description"])
                    date = st.date_input("Date", value=df.iloc[selected]["date"].date())
                    if st.form_submit_button("Update"):
                        updates = {
                            "amount": amount,
                            "type": type_,
                            "category": category,
                            "reference": reference,
                            "description": description,
                            "date": datetime.combine(date, datetime.min.time())
                        }
                        success, msg = update_transaction(trans_id, updates)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
        else:
            st.info("No transactions found.")
    
    elif page == "Add Transaction":
        st.title("Add Transaction")
        with st.form("add_form"):
            amount = st.number_input("Amount")
            type_ = st.selectbox("Type", ["income", "expense"])
            category = st.text_input("Category")
            reference = st.text_input("Reference")
            description = st.text_input("Description")
            date = st.date_input("Date")
            if st.form_submit_button("Add Transaction"):
                success, msg = add_transaction(
                    st.session_state.user["id"],
                    amount,
                    type_,
                    category,
                    reference,
                    description,
                    datetime.combine(date, datetime.min.time())
                )
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
    
    elif page == "Analytics":
        st.title("Analytics")
        
        trans = get_transactions(st.session_state.user["id"])
        if trans:
            df = pd.DataFrame(trans)
            df["date"] = pd.to_datetime(df["date"])
            
            # Summary
            total_income = df[df["type"] == "income"]["amount"].sum()
            total_expense = df[df["type"] == "expense"]["amount"].sum()
            balance = total_income - total_expense
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Income", f"${total_income:.2f}")
            col2.metric("Total Expense", f"${total_expense:.2f}")
            col3.metric("Balance", f"${balance:.2f}")
            
            # Charts
            expense_df = df[df["type"] == "expense"]
            if not expense_df.empty:
                # Category pie chart
                category_sum = expense_df.groupby("category")["amount"].sum().reset_index()
                fig1 = px.pie(category_sum, values="amount", names="category", title="Expenses by Category")
                st.plotly_chart(fig1)
                
                # Time series
                df["month"] = df["date"].dt.to_period("M").astype(str)
                monthly_sum = df.groupby(["month", "type"])["amount"].sum().reset_index()
                fig2 = px.bar(monthly_sum, x="month", y="amount", color="type", title="Monthly Income vs Expense")
                st.plotly_chart(fig2)
        else:
            st.info("No data for analytics.")