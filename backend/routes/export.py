from flask import Blueprint, jsonify, Response, request
import csv
import io
import json
from ..models import Transaction, Category, Budget
from ..extensions import db

export_bp = Blueprint('export', __name__)

@export_bp.route('/csv', methods=['GET'])
def export_csv():
    # Export all transactions
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['ID', 'Date', 'Type', 'Category', 'Description', 'Amount'])
    
    for t in transactions:
        writer.writerow([
            t.id, 
            t.date, 
            t.type, 
            t.category.name if t.category else 'Unknown', 
            t.description, 
            t.amount
        ])
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=transactions.csv"}
    )

@export_bp.route('/json', methods=['GET'])
def export_json():
    # Export full database state
    transactions = [t.to_dict() for t in Transaction.query.all()]
    categories = [c.to_dict() for c in Category.query.all()]
    budgets = [b.to_dict() for b in Budget.query.all()]
    
    data = {
        'transactions': transactions,
        'categories': categories,
        'budgets': budgets
    }
    
    return Response(
        json.dumps(data, indent=2),
        mimetype="application/json",
        headers={"Content-disposition": "attachment; filename=backup.json"}
    )

from fpdf import FPDF
from datetime import datetime
from sqlalchemy import func

@export_bp.route('/pdf', methods=['GET'])
def export_pdf():
    # Get month/year from query params or default to current
    today = datetime.now()
    try:
        month = int(request.args.get('month', today.month))
        year = int(request.args.get('year', today.year))
    except ValueError:
        month = today.month
        year = today.year

    # Fetch Data
    # 1. Transactions
    transactions = Transaction.query.filter(
        db.extract('month', Transaction.date) == month,
        db.extract('year', Transaction.date) == year
    ).order_by(Transaction.date).all()

    # 2. Budgets & Spending
    budgets = Budget.query.filter_by(month=month, year=year).all()
    budget_data = []
    for b in budgets:
        spent = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.category_id == b.category_id,
            Transaction.type == 'expense',
            db.extract('month', Transaction.date) == month,
            db.extract('year', Transaction.date) == year
        ).scalar() or 0.0
        budget_data.append({
            'category': b.category.name,
            'limit': b.monthly_limit,
            'spent': spent,
            'remaining': b.monthly_limit - spent
        })

    # 3. Totals
    total_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.type == 'income',
        db.extract('month', Transaction.date) == month,
        db.extract('year', Transaction.date) == year
    ).scalar() or 0.0
    
    total_expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.type == 'expense',
        db.extract('month', Transaction.date) == month,
        db.extract('year', Transaction.date) == year
    ).scalar() or 0.0

    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, f"Monthly Financial Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 12)
    month_name = datetime(year, month, 1).strftime('%B %Y')
    pdf.cell(0, 10, f"Period: {month_name}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)

    # Summary Section
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Financial Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    
    pdf.cell(100, 10, f"Total Income: {total_income:.2f} EUR", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(100, 10, f"Total Expenses: {total_expense:.2f} EUR", new_x="LMARGIN", new_y="NEXT")
    savings = total_income - total_expense
    pdf.set_text_color(0, 150, 0) if savings >= 0 else pdf.set_text_color(200, 0, 0)
    pdf.cell(100, 10, f"Net Savings: {savings:.2f} EUR", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)

    # Budget Overview
    if budget_data:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Budget Performance", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 10)
        # Table Header
        col_w = [50, 40, 40, 40]
        pdf.cell(col_w[0], 10, "Category", border=1)
        pdf.cell(col_w[1], 10, "Limit", border=1, align="R")
        pdf.cell(col_w[2], 10, "Spent", border=1, align="R")
        pdf.cell(col_w[3], 10, "Remaining", border=1, align="R")
        pdf.ln()
        
        pdf.set_font("Helvetica", "", 10)
        for b in budget_data:
            pdf.cell(col_w[0], 10, str(b['category']), border=1)
            pdf.cell(col_w[1], 10, f"{b['limit']:.2f}", border=1, align="R")
            pdf.cell(col_w[2], 10, f"{b['spent']:.2f}", border=1, align="R")
            
            # Color for remaining
            if b['remaining'] < 0:
                pdf.set_text_color(200, 0, 0)
            else:
                pdf.set_text_color(0, 150, 0)
            pdf.cell(col_w[3], 10, f"{b['remaining']:.2f}", border=1, align="R")
            pdf.set_text_color(0, 0, 0)
            pdf.ln()
        pdf.ln(10)

    # Transaction List
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Detailed Transactions", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 9)
    
    # Table Header
    # Date, Type, Category, Description, Amount
    cols = [25, 20, 35, 80, 25]
    pdf.cell(cols[0], 8, "Date", border=1)
    pdf.cell(cols[1], 8, "Type", border=1)
    pdf.cell(cols[2], 8, "Category", border=1)
    pdf.cell(cols[3], 8, "Description", border=1)
    pdf.cell(cols[4], 8, "Amount", border=1, align="R")
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 9)
    for t in transactions:
        pdf.cell(cols[0], 8, str(t.date.strftime('%Y-%m-%d')), border=1)
        pdf.cell(cols[1], 8, t.type.upper(), border=1)
        pdf.cell(cols[2], 8, t.category.name if t.category else "-", border=1)
        
        # Truncate description if too long
        desc = t.description if len(t.description) < 40 else t.description[:37] + "..."
        pdf.cell(cols[3], 8, desc, border=1)
        
        if t.type == 'income':
            pdf.set_text_color(0, 150, 0)
        else:
             pdf.set_text_color(0, 0, 0)
        
        pdf.cell(cols[4], 8, f"{t.amount:.2f}", border=1, align="R")
        pdf.set_text_color(0, 0, 0)
        pdf.ln()

    # Output
    pdf_bytes = bytes(pdf.output())
    response = Response(pdf_bytes, mimetype='application/pdf')
    response.headers['Content-Disposition'] = f'attachment; filename=report_{year}_{month:02d}.pdf'
    return response
