from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import json
from datetime import datetime

# ======================================================
# 1. CẤU HÌNH VÀ KHỞI TẠO FLASK
# ======================================================
app = Flask(__name__)
app.secret_key = 'super_secret_key_for_loopmind_app' 

# Hàm tiện ích VND (giữ nguyên)
def vnd(x):
    """Định dạng tiền tệ Việt Nam đồng (để dùng trong template)"""
    return f"{abs(x):,.0f}".replace(",", ".")

app.jinja_env.globals.update(vnd=vnd)
# Thêm datetime vào globals để sử dụng trong HTML cho input type="date"
app.jinja_env.globals.update(datetime=datetime) 


# ======================================================
# 2. DỮ LIỆU CÓ THỂ SỬA ĐỔI (Dùng biến toàn cục)
# ======================================================

# DataFrames sẽ được sửa đổi
global TRANSACTIONS_DATA
global DEBT_LOAN_DATA

# Dữ liệu mẫu cho Thu Chi
TRANSACTIONS_DATA = pd.DataFrame({
    'NGÀY': ['2025-12-15', '2025-12-14', '2025-12-13', '2025-12-12', '2025-12-11'],
    'MÔ TẢ': ['Lương tháng 12', 'Thanh toán tiền nhà', 'Mua hàng trên Tiki', 'Tiền bán hàng online', 'Chi phí đi lại'],
    'SỐ TIỀN': [35_000_000, -8_000_000, -1_500_000, 2_000_000, -500_000],
    'DANH MỤC': ['Thu nhập', 'Nhà ở', 'Mua sắm', 'Thu nhập', 'Vận chuyển'],
    'QUỸ (JAR)': ['Tiêu dùng', 'Nhu cầu', 'Nhu cầu', 'Tiêu dùng', 'Nhu cầu']
})
TRANSACTIONS_DATA['NGÀY'] = pd.to_datetime(TRANSACTIONS_DATA['NGÀY'])

# Dữ liệu mẫu cho Vay Nợ
DEBT_LOAN_DATA = pd.DataFrame({
    'NGÀY BẮT ĐẦU': ['2025-11-01', '2025-12-05'],
    'ĐỐI TƯỢNG': ['Ngân hàng A', 'Bạn B'],
    'LOẠI': ['VAY NỢ', 'CHO VAY'],
    'TỔNG TIỀN': [50_000_000, 15_000_000],
    'ĐÃ THANH TOÁN': [10_000_000, 0],
    'CÒN LẠI': [40_000_000, 15_000_000],
})


# ======================================================
# 3. ROUTES HIỂN THỊ (GET)
# ======================================================

@app.route('/')
@app.route('/dashboard')
def dashboard():
    # Tính toán KPI động
    income_kpi = TRANSACTIONS_DATA[TRANSACTIONS_DATA['SỐ TIỀN'] > 0]['SỐ TIỀN'].sum()
    expense_kpi = TRANSACTIONS_DATA[TRANSACTIONS_DATA['SỐ TIỀN'] < 0]['SỐ TIỀN'].sum() * -1
    balance_kpi = TRANSACTIONS_DATA['SỐ TIỀN'].sum()
    
    KPI_DATA = {
        "income": income_kpi,
        "expense": expense_kpi,
        "balance": balance_kpi,
        "saving_pct": 26.2, 
        "category_data": {"Ăn uống": 7000, "Nhà ở": 5000, "Vận chuyển": 3500, "Giáo dục": 4000, "Giải trí": 3000, "Khác": 3300},
        "jar_data": {"Nhu cầu": 13000, "Giáo dục": 5000, "Tiết kiệm": 7800},
    }
    
    category_labels = list(KPI_DATA['category_data'].keys())
    category_values = list(KPI_DATA['category_data'].values())
    jar_labels = list(KPI_DATA['jar_data'].keys())
    jar_values = list(KPI_DATA['jar_data'].values())

    context = {
        'page': 'dashboard',
        'kpi_data': KPI_DATA,
        'category_labels_json': json.dumps(category_labels),
        'category_values_json': json.dumps(category_values),
        'jar_labels_json': json.dumps(jar_labels),
        'jar_values_json': json.dumps(jar_values),
    }
    return render_template('dashboard.html', **context)


@app.route('/thu-chi')
def thu_chi():
    global TRANSACTIONS_DATA
    total_income = TRANSACTIONS_DATA[TRANSACTIONS_DATA['SỐ TIỀN'] > 0]['SỐ TIỀN'].sum()
    total_expense = TRANSACTIONS_DATA[TRANSACTIONS_DATA['SỐ TIỀN'] < 0]['SỐ TIỀN'].sum()
    balance = total_income + total_expense
    
    context = {
        'page': 'thu_chi',
        'income': total_income,
        'expense': abs(total_expense),
        'balance': balance,
        # Sắp xếp và chuyển đổi dữ liệu thành list of dicts cho Jinja
        'transactions': TRANSACTIONS_DATA.sort_values(by='NGÀY', ascending=False).to_dict('records')
    }
    # ĐÃ SỬA LỖI TemplateNotFound: Gọi đúng template income_expense.html
    return render_template('income_expense.html', **context)


@app.route('/vay-no')
def vay_no():
    global DEBT_LOAN_DATA
    total_loan = DEBT_LOAN_DATA[DEBT_LOAN_DATA['LOẠI'] == 'CHO VAY']['CÒN LẠI'].sum()
    total_debt = DEBT_LOAN_DATA[DEBT_LOAN_DATA['LOẠI'] == 'VAY NỢ']['CÒN LẠI'].sum()
    net_balance = total_loan - total_debt
    
    context = {
        'page': 'vay_no',
        'total_loan': total_loan,
        'total_debt': total_debt,
        'net_balance': net_balance,
        'debt_loan_items': DEBT_LOAN_DATA.to_dict('records')
    }
    return render_template('debt_loan.html', **context)


# ======================================================
# 4. FORM HANDLERS (ĐÃ IMPLEMENT LOGIC)
# ======================================================

@app.route('/add-transaction', methods=['POST'])
def add_transaction():
    global TRANSACTIONS_DATA
    if request.method == 'POST':
        # Lấy dữ liệu từ Form
        amount = int(request.form['amount'])
        description = request.form['description']
        category = request.form['category']
        date = request.form['date']
        type = request.form['transaction_type'] 
        
        # Xử lý dấu của số tiền
        final_amount = amount if type == 'income' else -amount
        
        # Tạo dòng DataFrame mới
        new_transaction = pd.DataFrame([{
            'NGÀY': date,
            'MÔ TẢ': description,
            'DANH MỤC': category,
            'SỐ TIỀN': final_amount,
            'QUỸ (JAR)': 'N/A' # Cần thêm input JAR vào form HTML
        }])
        
        # Thêm vào DataFrame toàn cục
        TRANSACTIONS_DATA = pd.concat([TRANSACTIONS_DATA, new_transaction], ignore_index=True)
        TRANSACTIONS_DATA['NGÀY'] = pd.to_datetime(TRANSACTIONS_DATA['NGÀY'])
        
        # Chuyển hướng về trang Thu Chi
        return redirect(url_for('thu_chi'))
    
    return redirect(url_for('thu_chi'))


@app.route('/add-debt-loan', methods=['POST'])
def add_debt_loan():
    global DEBT_LOAN_DATA
    if request.method == 'POST':
        # Lấy dữ liệu từ Form
        loan_type = request.form['loan_type'] # 'loan-out' (Cho Vay) hoặc 'loan-in' (Vay Nợ)
        related_person = request.form['related_person']
        amount = int(request.form['amount'])
        amount_paid = int(request.form.get('amount_paid', 0) or 0)
        description = request.form['description']
        date = request.form['date']

        # Tính toán giá trị còn lại
        remaining = amount - amount_paid
        
        # Xác định trạng thái
        if remaining <= 0:
            status = 'ĐÃ KẾT THÚC'
            remaining = 0
        else:
            status = 'CHƯA TRẢ' if loan_type == 'loan-out' else 'ĐANG NỢ'
            
        # Tạo dòng DataFrame mới
        new_row = pd.DataFrame([{
            'NGÀY BẮT ĐẦU': date,
            'ĐỐI TƯỢNG': related_person,
            'LOẠI': 'CHO VAY' if loan_type == 'loan-out' else 'VAY NỢ',
            'TỔNG TIỀN': amount, 
            'ĐÃ THANH TOÁN': amount_paid,
            'CÒN LẠI': remaining,
            'TRẠNG THÁI': status
        }])

        # Thêm vào DataFrame toàn cục
        DEBT_LOAN_DATA = pd.concat([DEBT_LOAN_DATA, new_row], ignore_index=True)

        return redirect(url_for('vay_no'))
    
    return redirect(url_for('vay_no'))


# ======================================================
# 5. CHẠY ỨNG DỤNG
# ======================================================
if __name__ == '__main__':
    app.run(debug=True)