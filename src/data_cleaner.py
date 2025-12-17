import json
import re
import os

def clean_number(text):
    """Chuyển chuỗi (ví dụ: '9 tỷ', '102,27') thành số (9.0, 102.27)"""
    if not text: return None
    # Tìm tất cả các số, dấu chấm và dấu phẩy
    match = re.search(r"([\d.,]+)", str(text))
    if match:
        num_str = match.group(1)
        # Nếu có dấu chấm và sau đó là 3 chữ số (vd: 1.020), coi là dấu ngàn -> xóa bỏ
        if '.' in num_str and num_str.count('.') >= 1 and len(num_str.split('.')[-1]) == 3:
             num_str = num_str.replace('.', '')
             
        # Chuyển dấu phẩy thành dấu chấm thập phân (vd: 102,27 -> 102.27)
        num_str = num_str.replace(',', '.')
        try:
            return float(num_str)
        except:
            return None
    return None

def process_data(input_file, output_file):
    try:
        # Kiểm tra file có tồn tại không
        if not os.path.exists(input_file):
            print(f" Không tìm thấy file tại: {input_file}")
            return

        with open(input_file, 'r', encoding='utf-8') as f:
            raw_content = f.read().strip()
            
        # --- SỬA LỖI QUAN TRỌNG Ở ĐÂY ---
        # Dùng Regex để tìm pattern: Dấu đóng } -> khoảng trắng/xuống dòng bất kỳ -> Dấu mở {
        # Và thay thế bằng: }, {
        fixed_content = re.sub(r'\}\s*\{', '}, {', raw_content)
        
        # Đóng gói vào trong mảng [] nếu chưa có
        if not fixed_content.startswith('['):
            fixed_content = f"[{fixed_content}]"
            
        try:
            data = json.loads(fixed_content)
        except json.JSONDecodeError as err:
            print(f" Lỗi format JSON: {err}")
            # In ra một đoạn xung quanh vị trí lỗi để debug nếu cần
            start = max(0, err.pos - 20)
            end = min(len(fixed_content), err.pos + 20)
            print(f"Vị trí lỗi: ...{fixed_content[start:end]}...")
            return

        cleaned_data = []

        # Xử lý từng tin đăng
        for item in data:
            new_item = item.copy()

            # 1. Tách địa chỉ
            addr = item.get("address", "")
            parts = [p.strip() for p in addr.split(',')]
            if len(parts) >= 4:
                new_item["city"] = parts[-1]
                new_item["district"] = parts[-2]
                new_item["ward"] = parts[-3]
                new_item["street"] = ", ".join(parts[:-3])
            else:
                new_item["city"] = parts[-1] if parts else ""
                new_item["district"] = ""
                new_item["ward"] = ""
                new_item["street"] = parts[0] if parts else ""

            # 2. Làm sạch số liệu
            new_item["price"] = clean_number(item.get("price"))
            new_item["price_per_spm"] = clean_number(item.get("price_per_spm"))
            new_item["area"] = clean_number(item.get("area"))

            # 3. Làm sạch thông số (Spec)
            if "spec" in item:
                spec = item["spec"]
                new_spec = spec.copy() 
                for key in ["bedroom", "bathroom", "num_floor", "front_width", "road_width"]:
                    if key in spec:
                        new_spec[key] = clean_number(spec.get(key))
                new_item["spec"] = new_spec

            # 4. Xử lý ngày giờ
            scraped_at = item.get("scraped_at", "")
            if "T" in scraped_at:
                new_item["scraped_at"] = scraped_at.replace("T", " ").split(".")[0]

            cleaned_data.append(new_item)

        # Xuất file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
            
        print(f" Xử lý thành công! File mới tại: {output_file}")

    except Exception as e:
        print(f" Có lỗi không mong muốn: {e}")

if __name__ == "__main__":
    # Tự động lấy đường dẫn chính xác của file nằm cùng thư mục src
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(current_dir, 'batdongsan_detail.json')
    output_path = os.path.join(current_dir, 'cleaned_data.json')
    
    process_data(input_path, output_path)