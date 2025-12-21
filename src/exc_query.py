from mongo_client import MongoDBClient
from posts_queries import (
    get_all_posts,
    get_latest_posts,
    get_posts_by_city,
    get_posts_price_less_than,
    count_posts
)

db = MongoDBClient()
col = db.col

print("Tổng số tin:", count_posts(col))

hn_posts = get_posts_by_city(col, "Hà Nội")
print("Số tin Hà Nội:", len(hn_posts))

cheap_posts = get_posts_price_less_than(col, 5_000_000_000)
print("Nhà < 5 tỷ:", len(cheap_posts))

latest = get_latest_posts(col, 5)
print("Tin mới nhất:", latest[0])

db.close()
