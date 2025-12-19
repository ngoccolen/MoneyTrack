from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
from datetime import datetime
from utils import process_receipt # Đảm bảo file utils.py vẫn ở cùng thư mục
import os 
import re
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote_plus

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_loopmind_app'

# ======================================================
# 1. CẤU HÌNH MYSQL & MODELS
# ======================================================
# Mã hóa mật khẩu có ký tự đặc biệt @
password = quote_plus('loveSKZ143@')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{password}@localhost/money_track_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))
    jar = db.Column(db.String(50), default='Nhu cầu')

class Debt(db.Model):
    __tablename__ = 'debts'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    target = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    paid_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(50))

# Khởi tạo bảng
with app.app_context():
    db.create_all()

# ======================================================
# 2. UTILS & FILTERS
# ======================================================
def vnd(x):
    if x is None: return "0"
    return f"{abs(x):,.0f}".replace(",", ".")

@app.template_filter('format_date')
def format_date(value):
    if value is None: return ""
    return value.strftime('%d/%m/%Y')

app.jinja_env.globals.update(vnd=vnd, datetime=datetime)
app.jinja_env.filters['format_date'] = format_date

# ======================================================
# 3. ROUTES HIỂN THỊ
# ======================================================

@app.route('/')
@app.route('/dashboard')
def dashboard():
    txs = Transaction.query.all()

    income = sum(t.amount for t in txs if t.amount > 0)
    expense = sum(abs(t.amount) for t in txs if t.amount < 0)

    acc = Account.query.first()
    base_balance = acc.balance if acc else 0

    balance = base_balance + income - expense
    saving_pct = (balance / income * 100) if income > 0 else 0

    kpi_data = {
        "income": income,
        "expense": expense,
        "balance": balance,
        "saving_pct": saving_pct,
        "base_balance": base_balance
    }

    return render_template(
        'dashboard.html',
        page='dashboard',
        kpi_data=kpi_data,
        account=acc,
        category_labels_json=json.dumps(["Ăn uống", "Nhà ở", "Khác"]),
        category_values_json=json.dumps([expense, 0, 0])
    )


@app.route('/thu-chi')
def thu_chi():
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    cat = request.args.get('category_filter')

    query = Transaction.query
    if start: query = query.filter(Transaction.date >= start)
    if end: query = query.filter(Transaction.date <= end)
    if cat and cat != 'all': query = query.filter(Transaction.category == cat)

    transactions = query.order_by(Transaction.date.desc()).all()
    income = sum(t.amount for t in transactions if t.amount > 0)
    expense = sum(t.amount for t in transactions if t.amount < 0)
    
    return render_template('income_expense.html', transactions=transactions, income=income, 
                           expense=abs(expense), balance=income + expense, page='thu_chi')

@app.route('/vay-no')
def vay_no():
    debts = Debt.query.all()
    t_loan = sum(d.total_amount - d.paid_amount for d in debts if d.type == 'CHO VAY')
    t_debt = sum(d.total_amount - d.paid_amount for d in debts if d.type == 'VAY NỢ')
    return render_template('debt_loan.html', page='vay_no', total_loan=t_loan, total_debt=t_debt, 
                           net_balance=t_loan - t_debt, debt_loans=debts)

@app.route('/scan')
def scan_page():
    return render_template('scan.html', page='scan')

# ======================================================
# 4. API & XỬ LÝ DỮ LIỆU
# ======================================================

@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    data = request.json
    user_msg = data.get('message', '').lower()
    match = re.search(r'(\d+(?:\.\d+)?)\s*(k|tr|triệu|đ|vnd)?', user_msg)
    
    if match:
        val_str = match.group(1).replace('.', '')
        val = float(val_str)
        unit = match.group(2)
        if unit == 'k': val *= 1000
        elif unit in ['tr', 'triệu']: val *= 1000000
        amount = int(val)
        desc = user_msg.replace(match.group(0), '').strip().capitalize() or "Chi tiêu AI"
        cat = "Ăn uống" if any(x in desc.lower() for x in ['ăn', 'uống', 'cafe']) else "Khác"

        try:
            new_tx = Transaction(date=datetime.now().date(), description=desc, amount=-amount, category=cat)
            db.session.add(new_tx)
            db.session.commit()
            return {"status": "success", "reply": f"✅ Ghi nhận: **{desc}** -{vnd(amount)}đ vào MySQL."}
        except:
            db.session.rollback()
            return {"status": "error", "reply": "Lỗi lưu Database!"}
    return {"status": "error", "reply": "Nhập ví dụ: 'ăn sáng 30k'"}

@app.route('/api/scan-receipt', methods=['POST'])
def scan_receipt():
    if 'file' not in request.files: return jsonify({"error": "No file"}), 400
    file = request.files['file']
    path = os.path.join("static/uploads", file.filename)
    file.save(path)
    result = process_receipt(path) # Gọi từ utils.py
    return jsonify(result)

@app.route('/add-debt-loan', methods=['POST'])
def add_debt_loan():
    # Lấy dữ liệu từ form trong debt_loan.html
    l_type_raw = request.form['loan_type'] # 'loan-out' hoặc 'loan-in'
    l_type = 'CHO VAY' if l_type_raw == 'loan-out' else 'VAY NỢ'
    
    amount = float(request.form['amount'])
    paid = float(request.form.get('amount_paid', 0) or 0)
    
    # Tạo bản ghi mới trong MySQL
    new_debt = Debt(
        date=request.form['date'],
        target=request.form['related_person'],
        type=l_type,
        total_amount=amount,
        paid_amount=paid,
        status='Đã hoàn thành' if paid >= amount else 'Chưa trả'
    )
    
    db.session.add(new_debt)
    db.session.commit()
    return redirect(url_for('vay_no'))

# Route để xóa khoản nợ (nếu cần)
@app.route('/delete-debt/<int:id>')
def delete_debt(id):
    d = Debt.query.get(id)
    if d:
        db.session.delete(d)
        db.session.commit()
    return redirect(url_for('vay_no'))

@app.route('/add-transaction', methods=['POST'])
def add_transaction():
    amount = float(request.form['amount'])
    final_amount = amount if request.form['transaction_type'] == 'income' else -amount
    new_tx = Transaction(date=request.form['date'], description=request.form['description'], 
                         amount=final_amount, category=request.form['category'])
    db.session.add(new_tx)
    db.session.commit()
    return redirect(url_for('thu_chi'))

@app.route('/delete-transaction/<int:id>')
def delete_transaction(id):
    tx = Transaction.query.get(id)
    if tx:
        db.session.delete(tx)
        db.session.commit()
    return redirect(url_for('thu_chi'))

# Thêm Model này vào app.py
class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0)
    icon = db.Column(db.String(10))

# Route để cập nhật nhanh số dư ban đầu
@app.route('/update-balance', methods=['POST'])
def update_balance():
    new_balance = float(request.form.get('balance', 0))
    # Giả sử chúng ta cập nhật cho ví đầu tiên (Ví chính)
    acc = Account.query.first()
    if not acc:
        acc = Account(name="Ví chính", balance=new_balance)
        db.session.add(acc)
    else:
        acc.balance = new_balance
    db.session.commit()
    return redirect(url_for('dashboard'))
if __name__ == '__main__':
    if not os.path.exists('static/uploads'): os.makedirs('static/uploads')
    app.run(debug=True)