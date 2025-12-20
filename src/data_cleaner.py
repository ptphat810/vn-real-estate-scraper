import json
import re
import os

# --- CÁC HÀM HỖ TRỢ LÀM SẠCH DỮ LIỆU ---

def clean_price(text):
    """
    Chuyển '9 tỷ' -> 9000000000, '800 triệu' -> 800000000
    Trả về số nguyên (Int) hoặc None
    """
    if not text: return None
    text_lower = str(text).lower()
    
    # Lấy phần số: thay dấu phẩy thành chấm để xử lý thập phân (vd: 9,5 tỷ -> 9.5)
    match = re.search(r"([\d.,]+)", text_lower)
    if not match: return None
    
    num_str = match.group(1).replace(',', '.')
    try:
        val = float(num_str)
    except ValueError:
        return None

    # Nhân theo đơn vị
    if 'tỷ' in text_lower:
        val *= 1_000_000_000
    elif 'triệu' in text_lower:
        val *= 1_000_000
    elif 'nghìn' in text_lower or 'ngàn' in text_lower:
        val *= 1_000
        
    return int(val)

def clean_int(text):
    """Chuyển '6.0' hoặc '6' thành số nguyên 6"""
    if not text: return None
    # Lấy số đầu tiên tìm thấy
    match = re.search(r"([\d.,]+)", str(text))
    if match:
        num_str = match.group(1).replace(',', '.')
        try:
            # Float trước rồi mới int để xử lý trường hợp "6.0"
            return int(float(num_str))
        except:
            return None
    return None

def clean_date(text):
    """Chuyển '26/12/2025' thành '2025-12-26' (Format YYYY-MM-DD)"""
    if not text: return ""
    # Tìm pattern dd/mm/yyyy
    match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", str(text))
    if match:
        d, m, y = match.groups()
        # Trả về chuẩn YYYY-MM-DD (Chuẩn quốc tế dễ so sánh)
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}" 
    return text

# --- HÀM XỬ LÝ CHÍNH ---

def process_data(input_file):
    """
    Đọc file, sửa lỗi JSON, làm sạch dữ liệu.
    RETURN: Danh sách (List) data đã làm sạch.
    """
    # 1. Kiểm tra file
    if not os.path.exists(input_file):
        print(f"Không tìm thấy file tại: {input_file}")
        return []

    with open(input_file, 'r', encoding='utf-8') as f:
        raw_content = f.read().strip()
        
    # 2. Sửa lỗi JSON hỏng (} { -> }, {)
    fixed_content = re.sub(r'\}\s*\{', '}, {', raw_content)
    
    if not fixed_content.startswith('['):
        fixed_content = f"[{fixed_content}]"
        
    try:
        data = json.loads(fixed_content)
    except json.JSONDecodeError as err:
        print(f"Lỗi format JSON: {err}")
        return []

    cleaned_data = []

    # 3. Duyệt và làm sạch từng dòng
    for item in data:
        new_item = item.copy()

        # ---  Address Object ---
        addr_str = item.get("address", "")
        parts = [p.strip() for p in addr_str.split(',')]
        
        # tách địa chỉ 
        addr_obj = {
            "City": "",
            "District": "",
            "Ward": "",
            "Street": ""
        }
        
        if len(parts) >= 1: addr_obj["City"] = parts[-1]
        if len(parts) >= 2: addr_obj["District"] = parts[-2]
        if len(parts) >= 3: addr_obj["Ward"] = parts[-3]
        if len(parts) >= 4: addr_obj["Street"] = ", ".join(parts[:-3])
        elif len(parts) > 0: addr_obj["Street"] = parts[0] # Fallback nếu địa chỉ ngắn
            
        new_item["address"] = addr_obj # Gán đè lại object mới

        # Price thành Int (full số)
        new_item["price"] = clean_price(item.get("price"))
        
        # Các cột Int 
        # Xử lý các trường nằm ngay bên ngoài
        for field in ["area"]:
            new_item[field] = clean_int(item.get(field))

        # Tính price_per_spm 
        p = new_item["price"]
        a = new_item["area"]

        if p is not None and a is not None and a > 0:
            # Tính chia và làm tròn 2 số
            new_item["price_per_spm"] = round(p / a, 2)
        else:
            new_item["price_per_spm"] = None

        # Xử lý các trường nằm trong 'spec'
        if "spec" in item and isinstance(item["spec"], dict):
            new_spec = item["spec"].copy()
            for key in ["bedroom", "bathroom", "num_floor", "front_width", "road_width"]:
                if key in new_spec:
                    new_spec[key] = clean_int(new_spec.get(key))
            new_item["spec"] = new_spec

        # Date Format (YY/MM/DD)
        new_item["date_posted"] = clean_date(item.get("date_posted"))
        new_item["date_expired"] = clean_date(item.get("date_expired"))

        # Xử lý scraped_at
        scraped_at = item.get("scraped_at", "")
        if "T" in scraped_at:
            new_item["scraped_at"] = scraped_at.replace("T", " ").split(".")[0]

        cleaned_data.append(new_item)

    return cleaned_data

# ---Test thử---
#if __name__ == "__main__":
#    current_dir = os.path.dirname(os.path.abspath(__file__))
#    input_path = os.path.join(current_dir, 'batdongsan_detail.json')
#    output_path = os.path.join(current_dir, 'cleaned_data.json')
    
    # Gọi hàm xử lý và nhận lại data
#    result_data = process_data(input_path)
    
#    if result_data:
        # Ghi ra file tại đây (bên ngoài hàm xử lý)
#        with open(output_path, 'w', encoding='utf-8') as f:
#            json.dump(result_data, f, ensure_ascii=False, indent=4)
#        print(f"Xử lý thành công {len(result_data)} tin! File mới tại: {output_path}")
#    else:
#        print("Không có dữ liệu để ghi.")