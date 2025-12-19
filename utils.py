import pytesseract
import cv2
import re
import os
from datetime import datetime

# ======================================================
# CẤU HÌNH TESSERACT
# ======================================================
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

def process_receipt(image_path):
    # 1. Đọc ảnh và tiền xử lý
    img = cv2.imread(image_path)
    if img is None:
        return {"amount": 0, "date": "", "note": "Không thể đọc được file ảnh"}

    # Chuyển xám và tăng độ tương phản để đọc số rõ hơn
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    
    # 2. Chạy OCR
    custom_config = r'--oem 3 --psm 6'
    try:
        text = pytesseract.image_to_string(gray, lang='vie', config=custom_config)
    except:
        text = pytesseract.image_to_string(gray, lang='eng', config=custom_config)

    # 3. Trích xuất số tiền (Cải tiến logic)
    # Tìm các dãy số có định dạng tiền tệ phổ biến
    raw_numbers = re.findall(r'\d+(?:[.,]\d+)*', text)
    valid_amounts = []
    
    for num in raw_numbers:
        # Loại bỏ dấu ngăn cách
        clean_num = num.replace('.', '').replace(',', '')
        
        # CHỐNG QUÉT NHẦM MÃ VẠCH: 
        # 1. Số phải là chữ số và độ dài phải từ 4 đến 8 ký tự (1.000đ đến 99.000.000đ)
        # 2. Loại bỏ các chuỗi số dài như mã vạch WinMart (thường 13 số)
        if clean_num.isdigit() and 4 <= len(clean_num) <= 8:
            val = int(clean_num)
            # Giới hạn số tiền hóa đơn lẻ thường dưới 5 triệu để an toàn
            if 1000 <= val <= 5000000:
                valid_amounts.append(val)
    
    # CHIẾN THUẬT: Lấy số tiền xuất hiện cuối cùng trong danh sách
    # Vì từ khóa "Thanh toán" hoặc "Tổng cộng" và số tiền của nó luôn ở cuối biên lai
    if valid_amounts:
        # Ưu tiên các số nằm ở 20% cuối của văn bản OCR được
        total = valid_amounts[-1] 
    else:
        total = 0
    
    # 4. Trích xuất ngày tháng
    date_pattern = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
    date_match = re.search(date_pattern, text)
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    final_date = today_str

    if date_match:
        day, month, year = date_match.groups()
        try:
            # Chuẩn hóa về YYYY-MM-DD
            final_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass

    # 5. Ghi chú
    note = "Quét tự động từ hóa đơn"
    text_upper = text.upper()
    if any(x in text_upper for x in ["WINMART", "COOP", "BHX", "SIÊU THỊ"]):
        note = "Đi chợ/Siêu thị (Quét AI)"
    elif any(x in text_upper for x in ["COFFEE", "HIGHLANDS", "PHÚC LONG", "TRÀ SỮA"]):
        note = "Ăn uống (Quét AI)"

    return {
        "amount": total,
        "date": final_date,
        "note": note
    }