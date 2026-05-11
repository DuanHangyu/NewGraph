"""
QA 会话持久化
复用 ProjectManager 的 JSON 文件存储模式
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from ..config import Config


class QASessionManager:
    """QA 会话管理器 — JSON 文件持久化"""

    SESSIONS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'qa_sessions')

    @classmethod
    def _ensure_dir(cls):
        os.makedirs(cls.SESSIONS_DIR, exist_ok=True)

    @classmethod
    def _session_path(cls, session_id: str) -> str:
        return os.path.join(cls.SESSIONS_DIR, f"{session_id}.json")

    @classmethod
    def create_session(cls, project_id: str) -> dict[str, Any]:
        """创建新会话"""
        cls._ensure_dir()
        session_id = f"qa_{uuid.uuid4().hex[:12]}"
        session = {
            "session_id": session_id,
            "project_id": project_id,
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(cls._session_path(session_id), 'w', encoding='utf-8') as f:
            json.dump(session, f, ensure_ascii=False, indent=2)
        return session

    @classmethod
    def get_session(cls, session_id: str) -> dict[str, Any] | None:
        """获取会话"""
        path = cls._session_path(session_id)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def add_message(cls, session_id: str, message: dict[str, Any]) -> dict[str, Any] | None:
        """添加消息到会话"""
        session = cls.get_session(session_id)
        if session is None:
            return None

        message["id"] = f"msg_{uuid.uuid4().hex[:8]}"
        message["timestamp"] = datetime.now(timezone.utc).isoformat()
        session["messages"].append(message)

        with open(cls._session_path(session_id), 'w', encoding='utf-8') as f:
            json.dump(session, f, ensure_ascii=False, indent=2)

        return session

    @classmethod
    def clear_session(cls, session_id: str) -> bool:
        """清空会话消息"""
        session = cls.get_session(session_id)
        if session is None:
            return False

        session["messages"] = []
        with open(cls._session_path(session_id), 'w', encoding='utf-8') as f:
            json.dump(session, f, ensure_ascii=False, indent=2)

        return True
