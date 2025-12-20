from pymongo import MongoClient, errors


class MongoDBClient:
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017")
        self.db = self.client["real_estate"]
        self.col = self.db["posts"]
        self.col.create_index("post_id", unique=True)

    def insert_post(self, data: dict) -> bool:
        try:
            self.col.insert_one(data)
            return True
        except errors.DuplicateKeyError:
            return False

if __name__ == "__main__":
    pass