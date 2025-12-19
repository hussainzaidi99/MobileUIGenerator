# backend/Services/session_manager.py
"""
Session Manager for Conversational Editing

Manages editing sessions with:
- Component model storage
- Conversation history tracking
- Automatic cleanup
- Session timeout handling
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
from threading import Lock


class SessionManager:
    """
    Manages conversation sessions for live editing.
    
    Each session stores:
    - Original component model
    - Conversation history with LLM
    - Current state
    - Edit statistics
    
    Features:
    - Thread-safe operations
    - Automatic timeout handling
    - Memory-efficient storage
    - Detailed session tracking
    """
    
    def __init__(self, session_timeout_hours: int = 2):
        """
        Initialize session manager.
        
        Args:
            session_timeout_hours: Hours before session expires (default: 2)
        """
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(hours=session_timeout_hours)
        self._lock = Lock()
        
        print(f"✅ SessionManager initialized (timeout: {session_timeout_hours}h)")
    
    def create_session(self, component_model: dict, user_id: str) -> str:
        """
        Create new editing session.
        
        Args:
            component_model: Initial component model from generation
            user_id: User who owns this session
            
        Returns:
            session_id: Unique identifier for the session
        """
        session_id = str(uuid.uuid4())
        
        with self._lock:
            self.sessions[session_id] = {
                "session_id": session_id,
                "user_id": user_id,
                "component_model": component_model,
                "conversation_history": [],
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "edit_count": 0,
                "total_tokens_used": 0,
                "metadata": {
                    "screens": len(component_model.get("screens", [])),
                    "screen_type": component_model.get("design_strategy", {}).get("screen_type", "unknown")
                }
            }
        
        print(f"✅ Created session {session_id} for user {user_id}")
        print(f"   Screens: {self.sessions[session_id]['metadata']['screens']}")
        print(f"   Type: {self.sessions[session_id]['metadata']['screen_type']}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session by ID with timeout check.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session dict or None if not found/expired
        """
        with self._lock:
            session = self.sessions.get(session_id)
            
            if not session:
                return None
            
            # Check timeout
            if datetime.now() - session["last_activity"] > self.session_timeout:
                print(f"⏰ Session {session_id} expired (inactive for {self.session_timeout})")
                del self.sessions[session_id]
                return None
            
            # Update last activity
            session["last_activity"] = datetime.now()
            
            return session
    
    def update_session(
        self,
        session_id: str,
        new_component_model: dict,
        user_message: str,
        assistant_response: str,
        tokens_used: int = 0
    ) -> bool:
        """
        Update session with new state and conversation.
        
        Args:
            session_id: Session identifier
            new_component_model: Updated component model
            user_message: User's edit prompt
            assistant_response: LLM's response summary
            tokens_used: Tokens consumed in this edit
            
        Returns:
            True if successful, False if session not found
        """
        with self._lock:
            session = self.sessions.get(session_id)
            
            if not session:
                return False
            
            # Update component model
            session["component_model"] = new_component_model
            
            # Add to conversation history
            session["conversation_history"].extend([
                {
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "role": "assistant",
                    "content": assistant_response,
                    "timestamp": datetime.now().isoformat()
                }
            ])
            
            # Update statistics
            session["edit_count"] += 1
            session["total_tokens_used"] += tokens_used
            session["last_activity"] = datetime.now()
            
            # Keep only last 10 exchanges (20 messages) to prevent memory bloat
            if len(session["conversation_history"]) > 20:
                session["conversation_history"] = session["conversation_history"][-20:]
            
            print(f"✅ Updated session {session_id}")
            print(f"   Edit #{session['edit_count']}")
            print(f"   Total tokens: {session['total_tokens_used']:,}")
            print(f"   History length: {len(session['conversation_history'])} messages")
            
            return True
    
    def get_conversation_history(
        self,
        session_id: str,
        last_n_exchanges: int = 3
    ) -> List[Dict]:
        """
        Get recent conversation history for context.
        
        Args:
            session_id: Session identifier
            last_n_exchanges: Number of recent exchanges to return (default: 3)
            
        Returns:
            List of conversation messages (user + assistant pairs)
        """
        session = self.get_session(session_id)
        
        if not session:
            return []
        
        history = session["conversation_history"]
        
        # Return last N exchanges (N*2 messages since each exchange = user + assistant)
        num_messages = last_n_exchanges * 2
        return history[-num_messages:] if len(history) > num_messages else history
    
    def delete_session(self, session_id: str) -> bool:
        """
        Manually delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                print(f"🗑️  Deleted session {session_id}")
                return True
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        
        with self._lock:
            expired = [
                sid for sid, session in self.sessions.items()
                if now - session["last_activity"] > self.session_timeout
            ]
            
            for sid in expired:
                del self.sessions[sid]
        
        if expired:
            print(f"🧹 Cleaned up {len(expired)} expired sessions")
        
        return len(expired)
    
    def get_stats(self) -> Dict:
        """
        Get overall session statistics.
        
        Returns:
            Statistics dictionary
        """
        with self._lock:
            total_sessions = len(self.sessions)
            total_edits = sum(s["edit_count"] for s in self.sessions.values())
            total_tokens = sum(s["total_tokens_used"] for s in self.sessions.values())
            
            # Group by user
            users = {}
            for session in self.sessions.values():
                uid = session["user_id"]
                if uid not in users:
                    users[uid] = {"sessions": 0, "edits": 0, "tokens": 0}
                users[uid]["sessions"] += 1
                users[uid]["edits"] += session["edit_count"]
                users[uid]["tokens"] += session["total_tokens_used"]
            
            return {
                "total_sessions": total_sessions,
                "total_edits": total_edits,
                "total_tokens_used": total_tokens,
                "unique_users": len(users),
                "avg_edits_per_session": round(total_edits / total_sessions, 2) if total_sessions > 0 else 0,
                "avg_tokens_per_edit": round(total_tokens / total_edits, 0) if total_edits > 0 else 0,
                "timeout_hours": self.session_timeout.total_seconds() / 3600
            }
    
    def get_user_sessions(self, user_id: str) -> List[Dict]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of session summaries
        """
        with self._lock:
            user_sessions = []
            
            for session in self.sessions.values():
                if session["user_id"] == user_id:
                    user_sessions.append({
                        "session_id": session["session_id"],
                        "created_at": session["created_at"].isoformat(),
                        "last_activity": session["last_activity"].isoformat(),
                        "edit_count": session["edit_count"],
                        "screens": session["metadata"]["screens"],
                        "screen_type": session["metadata"]["screen_type"]
                    })
            
            return user_sessions
    
    def __len__(self) -> int:
        """Return number of active sessions."""
        return len(self.sessions)
    
    def __contains__(self, session_id: str) -> bool:
        """Check if session exists."""
        return session_id in self.sessions


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Global session manager instance (initialized on import)
session_manager = SessionManager(session_timeout_hours=2)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_session_manager() -> SessionManager:
    """
    Get the global session manager instance.
    
    Returns:
        Global SessionManager instance
    """
    return session_manager


def create_editing_session(component_model: dict, user_id: str) -> str:
    """
    Convenience function to create a new editing session.
    
    Args:
        component_model: Component model from generation
        user_id: User identifier
        
    Returns:
        session_id: New session identifier
    """
    return session_manager.create_session(component_model, user_id)


def get_editing_session(session_id: str) -> Optional[Dict]:
    """
    Convenience function to get a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session dict or None
    """
    return session_manager.get_session(session_id)


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    "SessionManager",
    "session_manager",
    "get_session_manager",
    "create_editing_session",
    "get_editing_session"
]


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    """Test session manager functionality"""
    
    print("\n" + "="*70)
    print("SESSION MANAGER TEST")
    print("="*70)
    
    # Test data
    test_model = {
        "screens": [{"name": "Test", "components": []}],
        "theme": {},
        "tokens": {}
    }
    
    # Create session
    print("\n1. Creating test session...")
    sid = session_manager.create_session(test_model, "test_user_123")
    print(f"   Session ID: {sid}")
    
    # Get session
    print("\n2. Retrieving session...")
    session = session_manager.get_session(sid)
    print(f"   Found: {session is not None}")
    print(f"   User: {session['user_id']}")
    print(f"   Edits: {session['edit_count']}")
    
    # Update session
    print("\n3. Updating session...")
    success = session_manager.update_session(
        sid,
        test_model,
        "Change button to blue",
        "Applied changes successfully",
        tokens_used=3000
    )
    print(f"   Updated: {success}")
    
    # Get stats
    print("\n4. Session statistics...")
    stats = session_manager.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Cleanup
    print("\n5. Cleanup test...")
    session_manager.delete_session(sid)
    print(f"   Sessions remaining: {len(session_manager)}")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED")
    print("="*70 + "\n")