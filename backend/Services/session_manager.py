# backend/Services/session_manager.py
"""
Session Manager for Conversational Editing & History

Manages persistent conversations with:
- MongoDB storage for component models and history
- Snapshot-based versioning
- User-based retrieval
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
from db.database import Database

class SessionManager:
    """
    Manages persistent conversation sessions using MongoDB.
    
    Architecture:
    - 'conversations' collection: Metadata & sidebar info
    - 'conversation_versions' collection: Full snapshots of each step
    """
    
    def __init__(self):
        """Initialize session manager wrapper."""
        from datetime import timedelta
        self.session_timeout = timedelta(hours=2) # Compatibility with main.py
        print("✅ SessionManager (Persistent) initialized")
    
    def __len__(self) -> int:
        """Compatibility with main.py startup check."""
        return 0 # We don't track in-memory count anymore

    def cleanup_expired_sessions(self):
        """No-op: MongoDB handles persistence now."""
        pass
    
    async def create_session(self, component_model: dict, user_id: str, title: str = "New Project", web_preview: dict = None, react_native_code: dict = None) -> str:
        """
        Create a new persistent conversation.
        """
        db = Database.get_db()
        conversation_id = str(uuid.uuid4())
        
        # 1. Create Conversation Metadata
        conversation = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "title": title,
            "screen_type": component_model.get("design_strategy", {}).get("screen_type", "general"),
            "last_modified": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "latest_version": 1,
            "total_tokens": 0
        }
        await db.conversations.insert_one(conversation)
        
        # 2. Store First Version Snapshot
        version_snapshot = {
            "version_id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "version_num": 1,
            "data": {
                "component_model": component_model,
                "web_preview": web_preview,
                "react_native_code": react_native_code
            },
            "message_history": [], # Initial generation has no history yet
            "created_at": datetime.utcnow()
        }
        await db.conversation_versions.insert_one(version_snapshot)
        
        print(f"✅ Created persistent conversation {conversation_id} for user {user_id}")
        return conversation_id
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get the latest version of a conversation.
        """
        db = Database.get_db()
        
        # Fetch metadata
        conversation = await db.conversations.find_one({"conversation_id": session_id})
        if not conversation:
            return None
            
        # Fetch latest version
        latest_version = await db.conversation_versions.find_one(
            {"conversation_id": session_id},
            sort=[("version_num", -1)]
        )
        
        if not latest_version:
            return None
            
        # Format for return (mimicking old session structure but from DB)
        return {
            "session_id": session_id,
            "user_id": conversation["user_id"],
            "component_model": latest_version["data"]["component_model"],
            "web_preview": latest_version["data"].get("web_preview"),
            "react_native_code": latest_version["data"].get("react_native_code"),
            "conversation_history": latest_version["message_history"],
            "created_at": conversation["created_at"],
            "last_activity": conversation["last_modified"],
            "edit_count": latest_version["version_num"] - 1,
            "total_tokens_used": conversation.get("total_tokens", 0),
            "metadata": {
                "screens": len(latest_version["data"]["component_model"].get("screens", [])),
                "screen_type": conversation["screen_type"]
            }
        }

    async def update_session(
        self,
        session_id: str,
        new_component_model: dict,
        user_message: str,
        assistant_response: str,
        tokens_used: int = 0,
        web_preview: dict = None,
        react_native_code: dict = None
    ) -> bool:
        """
        Add a new version snapshot to the conversation.
        """
        db = Database.get_db()
        
        # 1. Get current conversation to find next version number
        conversation = await db.conversations.find_one({"conversation_id": session_id})
        if not conversation:
            return False
            
        next_version = conversation.get("latest_version", 0) + 1
        
        # 2. Get previous message history
        prev_version = await db.conversation_versions.find_one(
            {"conversation_id": session_id},
            sort=[("version_num", -1)]
        )
        
        current_history = prev_version["message_history"] if prev_version else []
        
        # 3. Append new messages
        new_messages = [
            {"role": "user", "content": user_message, "timestamp": datetime.utcnow().isoformat()},
            {"role": "assistant", "content": assistant_response, "timestamp": datetime.utcnow().isoformat()}
        ]
        updated_history = current_history + new_messages
        
        # Limit history size
        if len(updated_history) > 20:
            updated_history = updated_history[-20:]
            
        # 4. Save New Version Snapshot
        new_snapshot = {
            "version_id": str(uuid.uuid4()),
            "conversation_id": session_id,
            "version_num": next_version,
            "data": {
                "component_model": new_component_model,
                "web_preview": web_preview,
                "react_native_code": react_native_code
            },
            "message_history": updated_history,
            "created_at": datetime.utcnow()
        }
        await db.conversation_versions.insert_one(new_snapshot)
        
        # 5. Update Conversation Metadata
        await db.conversations.update_one(
            {"conversation_id": session_id},
            {
                "$set": {
                    "last_modified": datetime.utcnow(),
                    "latest_version": next_version
                },
                "$inc": {
                    "total_tokens": tokens_used
                }
            }
        )
        
        print(f"✅ Version {next_version} saved for conversation {session_id}")
        return True

    async def get_user_sessions(self, user_id: str) -> List[Dict]:
        """
        Get all conversations for a user (for sidebar).
        """
        db = Database.get_db()
        cursor = db.conversations.find({"user_id": user_id}).sort("last_modified", -1)
        
        results = []
        async for doc in cursor:
            results.append({
                "conversation_id": doc["conversation_id"],
                "title": doc.get("title", "New Project"),
                "screen_type": doc.get("screen_type", "general"),
                "last_modified": doc["last_modified"].isoformat(),
                "created_at": doc["created_at"].isoformat(),
                "version_count": doc.get("latest_version", 1)
            })
        return results

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a conversation and all its versions.
        """
        db = Database.get_db()
        await db.conversations.delete_one({"conversation_id": session_id})
        await db.conversation_versions.delete_many({"conversation_id": session_id})
        print(f"🗑️ Deleted conversation history for {session_id}")
        return True

    async def update_session_title(self, session_id: str, new_title: str) -> bool:
        """
        Update the title of a conversation.
        """
        db = Database.get_db()
        result = await db.conversations.update_one(
            {"conversation_id": session_id},
            {"$set": {"title": new_title, "last_modified": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def get_conversation_history(self, session_id: str, last_n_exchanges: int = 3) -> List[Dict]:
        """
        Get recent message history.
        """
        session = await self.get_session(session_id)
        if not session:
            return []
        
        history = session["conversation_history"]
        num_messages = last_n_exchanges * 2
        return history[-num_messages:] if len(history) > num_messages else history

# Global instance
session_manager = SessionManager()

# Async Helper wrappers
async def create_editing_session(component_model: dict, user_id: str, title: str = "New Project", web_preview: dict = None, react_native_code: dict = None) -> str:
    return await session_manager.create_session(component_model, user_id, title, web_preview, react_native_code)

async def get_editing_session(session_id: str) -> Optional[Dict]:
    return await session_manager.get_session(session_id)
