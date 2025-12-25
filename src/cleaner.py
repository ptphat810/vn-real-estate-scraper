import json
import re
import os

# --- 1. CÁC HÀM HỖ TRỢ LÀM SẠCH DỮ LIỆU (Dùng chung) ---

def clean_price(text):
    if not text: return None
    text_lower = str(text).lower()
    match = re.search(r"([\d.,]+)", text_lower)
    if not match: return None
    
    num_str = match.group(1).replace(',', '.')
    try:
        val = float(num_str)
    except:
        return None

    if 'tỷ' in text_lower:
        val *= 1_000_000_000
    elif 'triệu' in text_lower:
        val *= 1_000_000
    elif 'nghìn' in text_lower or 'ngàn' in text_lower:
        val *= 1_000
    return int(val)

def clean_int(text):
    if not text: return None
    match = re.search(r"([\d.,]+)", str(text))
    if match:
        num_str = match.group(1).replace(',', '.')
        try:
            return int(float(num_str))
        except: return None
    return None

def clean_date(text):
    if not text: return ""
    match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", str(text))
    if match:
        d, m, y = match.groups()
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}" 
    return text

def clean_address(addr_str):
    parts = [p.strip() for p in addr_str.split(',')]
    addr_obj = {"City": "", "District": "", "Ward": "", "Street": ""}
    if len(parts) >= 1: addr_obj["City"] = parts[-1]
    if len(parts) >= 2: addr_obj["District"] = parts[-2]
    if len(parts) >= 3: addr_obj["Ward"] = parts[-3]
    if len(parts) >= 4: addr_obj["Street"] = ", ".join(parts[:-3])
    elif len(parts) > 0: addr_obj["Street"] = parts[0]
    return addr_obj

# --- 2. HÀM XỬ LÝ CHUNG (Common Logic) ---

def base_clean(item):
    """Làm sạch các trường mà cả tin Thuê và Bán đều có"""
    new_item = item.copy()
    new_item["address"] = clean_address(item.get("address", ""))
    new_item["area"] = clean_int(item.get("area"))
    new_item["date_posted"] = clean_date(item.get("date_posted"))
    new_item["date_expired"] = clean_date(item.get("date_expired"))
    
    # Làm sạch Spec chung
    if "spec" in item and isinstance(item["spec"], dict):
        new_spec = item["spec"].copy()
        for key in ["bedroom", "bathroom", "num_floor", "front_width", "road_width"]:
            if key in new_spec:
                new_spec[key] = clean_int(new_spec.get(key))
        new_item["spec"] = new_spec
        
    return new_item

# --- 3. TÁCH BIỆT LOGIC THUÊ VÀ BÁN ---

def process_rent_item(item):
    """Xử lý đặc thù cho bất động sản cho thuê"""
    cleaned = base_clean(item)
    # Thuê: Giá thường là theo tháng
    cleaned["price_monthly"] = clean_price(item.get("price"))
    # Tính đơn giá thuê mỗi m2
    if cleaned["price_monthly"] and cleaned["area"]:
        cleaned["rent_per_m2"] = round(cleaned["price_monthly"] / cleaned["area"], 2)
    return cleaned

def process_sale_item(item):
    """Xử lý đặc thù cho bất động sản mua bán"""
    cleaned = base_clean(item)
    # Bán: Xử lý tổng giá và giá/m2 từ chuỗi có sẵn (price_per_spm)
    cleaned["price_total"] = clean_price(item.get("price"))
    
    # Ưu tiên lấy price_per_spm từ raw data nếu có, nếu không thì tự tính
    raw_ppp = item.get("price_per_spm")
    if raw_ppp:
        cleaned["price_per_m2"] = clean_price(raw_ppp)
    elif cleaned["price_total"] and cleaned["area"]:
        cleaned["price_per_m2"] = round(cleaned["price_total"] / cleaned["area"], 2)
    
    # Bán: Thêm thông tin pháp lý (thường chỉ tin bán mới có)
    if "spec" in cleaned and "legal" in item.get("spec", {}):
        cleaned["legal_status"] = item["spec"]["legal"]
        
    return cleaned

# --- 4. HÀM ĐIỀU PHỐI CHÍNH ---

def main_process(input_file):
    if not os.path.exists(input_file): return []

    with open(input_file, 'r', encoding='utf-8') as f:
        try:
            # Sửa lỗi JSON nếu cần và load
            content = f.read().strip()
            fixed_content = re.sub(r'\}\s*\{', '}, {', content)
            if not fixed_content.startswith('['): fixed_content = f"[{fixed_content}]"
            data = json.loads(fixed_content)
        except Exception as e:
            print(f"Lỗi đọc file: {e}")
            return []

    final_results = []
    for item in data:
        # Tự động nhận diện loại giao dịch để gọi hàm tương ứng
        trans_type = item.get("transaction_type", "").lower()
        
        if "rent" in trans_type or "thue" in trans_type:
            final_results.append(process_rent_item(item))
        else:
            # Mặc định xử lý như tin bán (sale)
            final_results.append(process_sale_item(item))
            
    return final_results




# --- ĐOẠN CODE TEST CHỨC NĂNG ---

if __name__ == "__main__":
    # Danh sách các file thực tế bạn đã gửi
    test_files = [
        './data/raw/rent_20251222.json',
        './data/raw/bds_20251223.json'
    ]
    
    for file_name in test_files:
        print(f"\n--- ĐANG TEST FILE: {file_name} ---")
        
        # Gọi hàm xử lý chính (main_process đã viết ở bước trước)
        results = main_process(file_name)
        
        if results:
            print(f"✅ Đã xử lý thành công {len(results)} dòng dữ liệu.")
            
            # In ra 1 ví dụ để kiểm tra độ chính xác
            sample = results[0]
            print("\nVí dụ kết quả dòng đầu tiên:")
            print(f"- Tiêu đề: {sample.get('title')[:50]}...")
            print(f"- Địa chỉ đã tách: {sample.get('address')}")
            
            # Kiểm tra logic tách biệt Thuê/Bán
            if "price_monthly" in sample:
                print(f"- Loại: THUÊ")
                print(f"- Giá thuê: {sample.get('price_monthly'):,} VNĐ/tháng")
            else:
                print(f"- Loại: BÁN")
                print(f"- Tổng giá: {sample.get('price_total'):,} VNĐ")
                print(f"- Giá/m2: {sample.get('price_per_m2'):,} VNĐ")
                
            print(f"- Diện tích: {sample.get('area')} m2")
            print(f"- Ngày đăng: {sample.get('date_posted')}")
        else:
            print(f"❌ File {file_name} không có dữ liệu hoặc lỗi format.")