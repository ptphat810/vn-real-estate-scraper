from pymongo import MongoClient
import re # Thư viện xử lý biểu thức chính quy (tìm kiếm chuỗi)

# 1. Kết nối đến MongoDB
# Nếu dùng Cloud, bạn thay chuỗi kết nối này bằng URI trong file .env của bạn
client = MongoClient('mongodb://localhost:27017/') 
db = client['batdongsanvn']  # Tên database Bất động sản
col = db['properties_post']  # Tên collection chứa tin đăng


# 1. Lấy tất cả tin đang "Bán"
print("1. Danh sách tin Bán (lấy 2 tin đầu):")
for doc in col.find({"transaction_type": "sale"}).limit(2):
    print(f" - {doc.get('title')}")

# 2. Lấy tất cả tin đang "Cho thuê"
print("\n2. Danh sách tin Cho thuê (lấy 2 tin đầu):")
for doc in col.find({"transaction_type": "rent"}).limit(2):
    print(f" {doc.get('title')}")

# 3. Lấy tin theo loại "Căn hộ chung cư" (Apartment)
print("\n3. Các tin rao bán/thuê Căn hộ:")
count_apt = col.count_documents({"property_category": "Apartment"})
print(f"Tìm thấy {count_apt} tin căn hộ.")

# 4. Lấy tin theo loại "Đất nền" (Land Plot)
print("\n4. Các tin rao bán Đất nền:")
count_land = col.count_documents({"property_category": "Land Plot"})
print(f"Tìm thấy {count_land} tin đất nền.")

# 5. Tìm nhà tại Quận 7 
print("\n5. Các tin tại Quận 7:")
query_q7 = {"address": {"$regex": "Quận 7", "$options": "i"}}
for doc in col.find(query_q7).limit(2):
    print(f"{doc.get('address')}")

# 6. Tìm nhà tại Hà Nội
print("\n6. Số lượng tin tại Hà Nội:")
count_hn = col.count_documents({"address": {"$regex": "Hà Nội", "$options": "i"}})
print(f" {count_hn} tin.")

# 7. Tìm các tin thuộc dự án Vinhomes (Tìm trong title hoặc project_info)
print("\n7. Các tin liên quan đến Vinhomes:")
query_vin = {
    "$or": [
        {"title": {"$regex": "Vinhomes", "$options": "i"}},
        {"project_info.name": {"$regex": "Vinhomes", "$options": "i"}}
    ]
}
for doc in col.find(query_vin).limit(2):
    print(f"{doc.get('title')}")

# 8. Tìm nhà có đúng 2 phòng ngủ
print("\n8. Nhà có 2 phòng ngủ:")
# Lưu ý: Dữ liệu của bạn lưu là chuỗi "2 phòng"
count_2pn = col.count_documents({"spec.bedroom": "2 phòng"})
print(f"{count_2pn}")

# 9. Tìm nhà có từ 3 phòng ngủ trở lên (Dùng Regex bắt số 3,4,5...)
print("\n9. Nhà có từ 3 phòng ngủ trở lên:")
query_3pn = {"spec.bedroom": {"$regex": "^[3-9] phòng"}}
for doc in col.find(query_3pn).limit(2):
    print(f"{doc.get('title')} ({doc.get('spec', {}).get('bedroom')})")

# 10. Tìm nhà có Sổ đỏ / Sổ hồng
print("\n10. Nhà có giấy tờ pháp lý rõ ràng (Sổ đỏ/hồng):")
count_legal = col.count_documents({"spec.legal": {"$regex": "Sổ đỏ|Sổ hồng", "$options": "i"}})
print(f"{count_legal}")

# 11. Tìm nhà có hướng ban công Đông Nam
print("\n11. Nhà hướng ban công Đông Nam:")
count_dongnam = col.count_documents({"spec.balcony_direction": "Đông - Nam"})
print(f"{count_dongnam}")

# 12. Tìm tin có giá "Thỏa thuận"
print("\n12. Tin có giá Thỏa thuận:")
count_deal = col.count_documents({"price": "Thỏa thuận"})
print(f"Có {count_deal} tin.")

# 13. Lọc đa điều kiện: Cho thuê + Căn hộ + Quận Bình Thạnh
print("\n13. Căn hộ cho thuê tại Bình Thạnh:")
query_complex = {
    "transaction_type": "rent",
    "property_category": "Apartment",
    "address": {"$regex": "Bình Thạnh", "$options": "i"}
}
for doc in col.find(query_complex).limit(2):
    print(doc.get('title'))

# 14. Chỉ lấy các trường cần thiết (Projection)
print("\n14. Lấy dữ liệu rút gọn (Chỉ Tiêu đề & Giá):")
projection = {
    "_id": 0,
    "title": 1,
    "price": 1
}
for doc in col.find({"transaction_type": "sale"}, projection).limit(2):
    print({doc})

# 15. Thống kê số lượng tin theo từng Loại hình BĐS (Aggregation)
print("\n15. Thống kê số lượng tin theo loại hình:")
pipeline = [
    {
        "$group": {
            "_id": "$property_category", # Gom nhóm theo loại BĐS
            "total_posts": {"$sum": 1}   # Đếm tổng số tin
        }
    },
    {"$sort": {"total_posts": -1}}       # Sắp xếp giảm dần
]
results = col.aggregate(pipeline)
for group in results:
    category = group['_id'] if group['_id'] else "Không xác định"
    print(f"{category}: {group['total_posts']} ")

# Đóng kết nối
client.close()