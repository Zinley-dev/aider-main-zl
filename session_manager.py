import time
import threading
import uuid
from typing import Dict, Any, Optional

class SessionManager:
    """
    Quản lý các session Aider cho REST API
    Bao gồm tự động cleanup các session hết hạn
    """
    
    def __init__(self, timeout: int = 3600):  # 1 giờ timeout mặc định
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.timeout = timeout
        self.lock = threading.Lock()
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy session theo ID và cập nhật last_activity
        """
        with self.lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session["last_activity"] = time.time()
                return session
            return None
    
    def create_session(self, coder, io) -> str:
        """
        Tạo session mới với coder và io instance
        Trả về session_id
        """
        with self.lock:
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = {
                "coder": coder,
                "io": io,
                "last_activity": time.time(),
                "created_at": time.time()
            }
            return session_id
    
    def delete_session(self, session_id: str) -> bool:
        """
        Xóa session theo ID
        Trả về True nếu thành công, False nếu không tìm thấy
        """
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False
    
    def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Lấy danh sách tất cả session (không bao gồm coder/io objects)
        """
        with self.lock:
            sessions_info = {}
            for session_id, session in self.sessions.items():
                sessions_info[session_id] = {
                    "last_activity": session["last_activity"],
                    "created_at": session["created_at"],
                    "age_seconds": time.time() - session["created_at"]
                }
            return sessions_info
    
    def get_session_count(self) -> int:
        """
        Lấy số lượng session hiện tại
        """
        with self.lock:
            return len(self.sessions)
    
    def _cleanup_loop(self):
        """
        Vòng lặp cleanup chạy trong background thread
        """
        while True:
            time.sleep(60)  # Kiểm tra mỗi phút
            self._cleanup_expired_sessions()
    
    def _cleanup_expired_sessions(self):
        """
        Xóa các session đã hết hạn
        """
        current_time = time.time()
        with self.lock:
            expired_sessions = [
                session_id for session_id, session in self.sessions.items()
                if current_time - session["last_activity"] > self.timeout
            ]
            
            for session_id in expired_sessions:
                print(f"Cleaning up expired session: {session_id}")
                del self.sessions[session_id]
            
            if expired_sessions:
                print(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def force_cleanup(self):
        """
        Buộc cleanup tất cả session hết hạn ngay lập tức
        """
        self._cleanup_expired_sessions()
    
    def update_session_activity(self, session_id: str) -> bool:
        """
        Cập nhật thời gian hoạt động cuối của session
        """
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id]["last_activity"] = time.time()
                return True
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin về session (không bao gồm coder/io objects)
        """
        with self.lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                return {
                    "session_id": session_id,
                    "last_activity": session["last_activity"],
                    "created_at": session["created_at"],
                    "age_seconds": time.time() - session["created_at"],
                    "time_until_expiry": self.timeout - (time.time() - session["last_activity"])
                }
            return None 