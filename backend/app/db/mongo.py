from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from backend.app.config import settings
from backend.app.core.logger import logger


class MongoDBManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls):
        """Establish asynchronous MongoDB connection and create required collection indices."""
        try:
            logger.info(f"Connecting to MongoDB at {settings.MONGO_URI} (Database: {settings.MONGO_DB_NAME})...")
            cls.client = AsyncIOMotorClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000
            )
            cls.db = cls.client[settings.MONGO_DB_NAME]

            # Verify connection with ping
            await cls.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB.")

            # Ensure collections and indexes are provisioned
            await cls._init_indexes()
        except Exception as e:
            logger.warning(f"MongoDB connection or ping warning: {e}. Client endpoints will attempt re-connection.")

    @classmethod
    async def _init_indexes(cls):
        """Set up unique and search indexes on the clients collection."""
        if cls.db is None:
            return
        try:
            clients_col = cls.db["clients"]
            # Unique index on email
            await clients_col.create_index("email", unique=True, name="idx_client_email_unique")
            # Text index for search on name, company, and address
            await clients_col.create_index(
                [("name", "text"), ("company", "text"), ("address", "text")],
                name="idx_client_text_search"
            )
            # Standard index on creation timestamp
            await clients_col.create_index("created_at", name="idx_client_created_at")
            logger.info("MongoDB client collection indices initialized.")
        except Exception as e:
            logger.warning(f"Failed to initialize MongoDB indices: {e}")

    @classmethod
    async def disconnect(cls):
        """Cleanly close MongoDB connection."""
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("MongoDB connection closed.")

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        if cls.db is None:
            if cls.client is None:
                cls.client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=3000)
            cls.db = cls.client[settings.MONGO_DB_NAME]
        return cls.db

    @classmethod
    def get_collection(cls, collection_name: str = "clients") -> AsyncIOMotorCollection:
        return cls.get_database()[collection_name]


async def get_clients_collection() -> AsyncIOMotorCollection:
    """FastAPI dependency for accessing the clients collection."""
    return MongoDBManager.get_collection("clients")
