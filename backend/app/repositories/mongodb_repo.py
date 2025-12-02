"""
MongoDB Repository
Handles all MongoDB database operations.
Implements Repository pattern for clean data access.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
import logging

from app.config import settings
from app.models.user import User, UserCreate
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document

logger = logging.getLogger(__name__)


class MongoDBRepository:
    """
    MongoDB repository for handling all database operations.
    Uses Motor for async MongoDB operations.
    """
    
    def __init__(self):
        """Initialize MongoDB connection."""
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """Establish connection to MongoDB."""
        try:
            # Connection with extended timeout for Windows SSL
            self.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=30000,  # 30 seconds for Windows SSL
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                tlsAllowInvalidCertificates=True  # Required for Windows SSL with Python 3.11
            )
            self.db = self.client[settings.mongodb_db_name]
            
            # Test connection with retry
            logger.info("Connecting to MongoDB Atlas...")
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            # Create indexes
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self):
        """Create database indexes for optimal query performance."""
        try:
            # User indexes
            await self.db[settings.mongodb_auth_collection].create_index("email", unique=True)
            await self.db[settings.mongodb_auth_collection].create_index("role")
            
            # Chat session indexes
            await self.db[settings.mongodb_chat_collection].create_index("user_id")
            await self.db[settings.mongodb_chat_collection].create_index("created_at")
            await self.db[settings.mongodb_chat_collection].create_index(
                [("user_id", 1), ("created_at", -1)]
            )
            
            # Document indexes
            await self.db.documents.create_index("uploaded_by")
            await self.db.documents.create_index("document_type")
            await self.db.documents.create_index("status")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    # ==================== User Operations ====================
    
    async def create_user(self, user: UserCreate, hashed_password: str) -> User:
        """
        Create a new user in the database.
        
        Args:
            user: User creation data
            hashed_password: Hashed password
            
        Returns:
            Created user object
        """
        user_dict = {
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None
        }
        
        result = await self.db[settings.mongodb_auth_collection].insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)
        
        return User(**user_dict)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve user by email address.
        
        Args:
            email: User email
            
        Returns:
            User object if found, None otherwise
        """
        user_dict = await self.db[settings.mongodb_auth_collection].find_one({"email": email})
        
        if user_dict:
            user_dict["_id"] = str(user_dict["_id"])
            return User(**user_dict)
        
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            user_dict = await self.db[settings.mongodb_auth_collection].find_one(
                {"_id": ObjectId(user_id)}
            )
            
            if user_dict:
                user_dict["_id"] = str(user_dict["_id"])
                return User(**user_dict)
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
        
        return None
    
    async def update_last_login(self, user_id: str):
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User ID
        """
        await self.db[settings.mongodb_auth_collection].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login": datetime.utcnow()}}
        )
    
    # ==================== Chat Operations ====================
    
    async def create_chat_session(self, user_id: str, title: str = "New Conversation") -> ChatSession:
        """
        Create a new chat session.
        
        Args:
            user_id: Owner user ID
            title: Session title
            
        Returns:
            Created chat session
        """
        session_dict = {
            "user_id": user_id,
            "title": title,
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_archived": False,
            "tags": []
        }
        
        result = await self.db[settings.mongodb_chat_collection].insert_one(session_dict)
        # Convert MongoDB _id to id for the model
        session_dict["id"] = str(result.inserted_id)
        # Remove _id to avoid Pydantic validation error
        if "_id" in session_dict:
            del session_dict["_id"]
        
        return ChatSession(**session_dict)
    
    async def get_chat_session(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        """
        Retrieve a chat session.
        
        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            
        Returns:
            Chat session if found and authorized, None otherwise
        """
        try:
            session_dict = await self.db[settings.mongodb_chat_collection].find_one({
                "_id": ObjectId(session_id),
                "user_id": user_id
            })
            
            if session_dict:
                # Convert MongoDB _id to id for the model
                session_dict["id"] = str(session_dict["_id"])
                del session_dict["_id"]
                return ChatSession(**session_dict)
            
        except Exception as e:
            logger.error(f"Error getting chat session: {e}")
        
        return None
    
    async def add_message_to_session(
        self,
        session_id: str,
        user_id: str,
        message: ChatMessage
    ) -> bool:
        """
        Add a message to a chat session.
        
        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            message: Message to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            message_dict = message.model_dump()
            
            result = await self.db[settings.mongodb_chat_collection].update_one(
                {"_id": ObjectId(session_id), "user_id": user_id},
                {
                    "$push": {"messages": message_dict},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error adding message to session: {e}")
            return False
    
    async def get_user_chat_sessions(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        include_archived: bool = False
    ) -> List[ChatSession]:
        """
        Get all chat sessions for a user.
        
        Args:
            user_id: User ID
            skip: Number of sessions to skip (pagination)
            limit: Maximum number of sessions to return
            include_archived: Whether to include archived sessions
            
        Returns:
            List of chat sessions
        """
        query = {"user_id": user_id}
        if not include_archived:
            query["is_archived"] = False
        
        cursor = self.db[settings.mongodb_chat_collection].find(query).sort(
            "updated_at", -1
        ).skip(skip).limit(limit)
        
        sessions = []
        async for session_dict in cursor:
            # Convert MongoDB _id to id for the model
            session_dict["id"] = str(session_dict["_id"])
            del session_dict["_id"]
            sessions.append(ChatSession(**session_dict))
        
        return sessions
    
    async def update_session_title(self, session_id: str, user_id: str, title: str) -> bool:
        """
        Update chat session title.
        
        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            title: New title
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db[settings.mongodb_chat_collection].update_one(
                {"_id": ObjectId(session_id), "user_id": user_id},
                {"$set": {"title": title, "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating session title: {e}")
            return False
    
    async def archive_session(self, session_id: str, user_id: str) -> bool:
        """
        Archive a chat session.
        
        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db[settings.mongodb_chat_collection].update_one(
                {"_id": ObjectId(session_id), "user_id": user_id},
                {"$set": {"is_archived": True, "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error archiving session: {e}")
            return False
    
    # ==================== Document Operations ====================
    
    async def create_document(self, document: Document) -> Document:
        """
        Create a document record.
        
        Args:
            document: Document object
            
        Returns:
            Created document with ID
        """
        doc_dict = document.model_dump(exclude={"id"})
        result = await self.db.documents.insert_one(doc_dict)
        document.id = str(result.inserted_id)
        
        return document
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """
        Retrieve a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        try:
            doc_dict = await self.db.documents.find_one({"_id": ObjectId(document_id)})
            
            if doc_dict:
                doc_dict["_id"] = str(doc_dict["_id"])
                return Document(**doc_dict)
            
        except Exception as e:
            logger.error(f"Error getting document: {e}")
        
        return None
    
    async def update_document_status(
        self,
        document_id: str,
        status: str,
        error: Optional[str] = None
    ) -> bool:
        """
        Update document processing status.
        
        Args:
            document_id: Document ID
            status: New status
            error: Error message if failed
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_dict = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if status == "processing":
                update_dict["processing_started_at"] = datetime.utcnow()
            elif status == "completed":
                update_dict["processing_completed_at"] = datetime.utcnow()
            elif status == "failed" and error:
                update_dict["processing_error"] = error
            
            result = await self.db.documents.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": update_dict}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating document status: {e}")
            return False
    
    async def get_user_documents(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Document]:
        """
        Get documents uploaded by a user.
        
        Args:
            user_id: User ID
            skip: Number to skip (pagination)
            limit: Maximum number to return
            
        Returns:
            List of documents
        """
        cursor = self.db.documents.find({"uploaded_by": user_id}).sort(
            "uploaded_at", -1
        ).skip(skip).limit(limit)
        
        documents = []
        async for doc_dict in cursor:
            doc_dict["_id"] = str(doc_dict["_id"])
            documents.append(Document(**doc_dict))
        
        return documents
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the database.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db.documents.delete_one({"_id": ObjectId(document_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False


# Global repository instance
_mongodb_repo = None


async def get_mongodb_repo() -> MongoDBRepository:
    """
    Get or create the global MongoDB repository instance.
    Dependency injection function for FastAPI.
    """
    global _mongodb_repo
    if _mongodb_repo is None:
        _mongodb_repo = MongoDBRepository()
        await _mongodb_repo.connect()
    return _mongodb_repo

