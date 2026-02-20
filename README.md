# Expense Management System (Python Version)

A full-stack expense tracking application built with Python and Streamlit.

## Features
- User registration and login with secure password hashing
- Add, edit, delete transactions (income/expense)
- Filter transactions by frequency, date range, and type
- Analytics dashboard with charts (expenses by category, monthly trends)
- Balance calculation
- Data stored locally in JSON files (no database required)

## Requirements
- Python 3.8+
- Virtual environment (already set up)

## Installation
The virtual environment is configured, and packages are installed.

## Running the App
Run the following command:
```
C:/Users/banth/OneDrive/Documents/Expense-Management-System-main/.venv/Scripts/python.exe -m streamlit run app.py
```

The app will be available at http://localhost:8501

## Data Storage
- User data: `data/users.json`
- Transaction data: `data/transactions.json`
- Data persists between sessions

## Security
- Passwords are hashed using bcrypt.
- User emails are unique.