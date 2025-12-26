import os
from pymongo import MongoClient, errors
from dotenv import load_dotenv
from utils import get_logger

load_dotenv()
logger = get_logger("mongodb")


class MongoDBClient:
    def __init__(self):
        user = os.getenv("MONGO_USER")
        pw = os.getenv("MONGO_PASS")
        cluster = os.getenv("MONGO_CLUSTER")
        db_name = os.getenv("MONGO_DB")
        col_name = os.getenv("MONGO_COLLECTION")
        uri = f"mongodb+srv://{user}:{pw}@{cluster}/?retryWrites=true&w=majority"

        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.client.server_info()
            self.db = self.client[db_name]
            self.col = self.db[col_name]
            self.col.create_index(
                [("post_id", 1), ("transaction_type", 1)],
                unique=True
            )
            logger.info(f"Connected to Atlas: DB [{db_name}] | Collection [{col_name}]")

        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise

    def check_duplicated(self, post_id, transaction_type):
        try:
            query = {"post_id": str(post_id), "transaction_type": transaction_type}
            result = self.col.find_one(query, {"_id": 1})
            return result is not None

        except Exception as e:
            logger.error(f"Duplicate check error: {e}")
            return False


    def find_post(self, query):
        try:
            result = self.col.find_one(query)
            return result

        except Exception as e:
            logger.error(f"Find one error: {e}")
            return None


    def find_many_posts(self, query, limit=0):
        try:
            result = list(self.col.find(query).limit(limit))
            return result

        except Exception as e:
            logger.error(f"Find many error: {e}")
            return []


    def insert_post(self, data: dict):
        try:
            result = self.col.insert_one(data)
            return result.inserted_id

        except errors.DuplicateKeyError:
            return None

        except Exception as e:
            logger.error(f"Insert one error: {e}")
            return None


    def insert_many_posts(self, data_list: list) -> int:
        if not data_list:
            return 0
        try:
            result = self.col.insert_many(data_list, ordered=False)
            return len(result.inserted_ids)

        except errors.BulkWriteError as bwe:
            return bwe.details.get('nInserted', 0)

        except Exception as e:
            logger.error(f"Bulk insert error: {e}")
            return 0

    def update_post(self, query, update_data):
        try:
            result = self.col.update_one(query, {"$set": update_data})
            return result.modified_count

        except Exception as e:
            logger.error(f"Update one error: {e}")
            return 0


    def update_many_posts(self, query, update_data):
        try:
            result = self.col.update_many(query, {"$set": update_data})
            return result.modified_count

        except Exception as e:
            logger.error(f"Update many error: {e}")
            return 0

    def delete_post(self, query):
        try:
            result = self.col.delete_one(query)
            return result.deleted_count

        except Exception as e:
            logger.error(f"Delete one error: {e}")
            return 0

    def delete_many_posts(self, query):
        try:
            result = self.col.delete_many(query)
            return result.deleted_count

        except Exception as e:
            logger.error(f"Delete many error: {e}")
            return 0


    def close(self):
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("MongoDB connection closed.")