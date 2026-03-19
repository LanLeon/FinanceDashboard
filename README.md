# Finance Tracker

A personal finance tracker for managing transactions, budgets, and expense analytics – built with **Flask** (Backend) and **Vue.js** (Frontend).

---

## 1. Installation

### Prerequisites
- Python 3.8+
- pip (Standard package manager for Python)

### Steps
1. **Open project directory**: Navigate in your terminal to the project directory containing this README.
   ```bash
   cd path/to/Programmierprojekt
   ```
2. **Set up virtual environment (recommended)**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Initialize database** (optional, if not already present):
   ```bash
   python -m backend.init_db
   ```
   *Tip: Use `python -m backend.seed_data` to load sample data into the database.*

---

## 2. Usage

### Start Application
Start the backend server (which simultaneously serves the frontend):
```bash
python -m backend.app
```
Now open your web browser and go to the address `http://127.0.0.1:5000`.

### Main Features
- **Dashboard**: Get an overview of your income and expenses, visualized by charts.
- **Manage Transactions**: Use the form on the left side to enter new income and expenses. Make sure to select an appropriate category.
- **Manage Categories**: You can create new categories with individual colors and icons to better structure your expenses.
- **Set Budgets**: Set monthly limits for categories to keep track of your expenses.

---

## 3. Maintenance
- **Database Backup**: The entire database is stored in the file `backend/finance_tracker.db`. To create a backup, simply copy this file to a safe location.
- **Troubleshooting**: If the server does not start, check whether port 5000 is already in use by another application.

---

## Project Structure

```text
Programmierprojekt/
├── backend/
│   ├── app.py          # Flask App & Entry Point
│   ├── models.py       # Database models
│   ├── extensions.py   # SQLAlchemy instance
│   └── routes/
│       ├── transactions.py
│       ├── categories.py
│       ├── budgets.py
│       ├── analytics.py
│       └── export.py
├── frontend/
│   └── index.html      # Vue.js Frontend (CDN-based)
├── requirements.txt    # Python dependencies
└── README.md
```