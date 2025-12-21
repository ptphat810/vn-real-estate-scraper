"""Module truy vấn tin đăng từ MongoDB"""

def get_all_posts(col):
    """Lấy toàn bộ tin"""
    return list(col.find({}, {"_id": 0}))


def get_latest_posts(col, limit=10):
    """Lấy tin mới nhất"""
    return list(
        col.find({}, {"_id": 0})
           .sort("scraped_at", -1)
           .limit(limit)
    )


def get_posts_by_city(col, city):
    """Lấy tin theo thành phố"""
    return list(
        col.find(
            {"address.City": city},
            {"_id": 0}
        )
    )


def get_posts_price_less_than(col, max_price):
    """Lấy tin có giá < max_price"""
    return list(
        col.find(
            {"price": {"$lt": max_price}},
            {"_id": 0}
        )
    )


def count_posts(col):
    """Đếm số lượng tin"""
    return col.count_documents({})
