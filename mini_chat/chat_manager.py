"""
Chat Manager module for handling Telegram chat operations
"""

import logging
from typing import Optional, List, Dict
from telethon import TelegramClient
from telethon.tl.types import Message, Dialog

logger = logging.getLogger(__name__)

class ChatManager:
    def __init__(self, client: TelegramClient):
        self.client = client
        self._active_chats: Dict[int, Dialog] = {}
        
    async def get_recent_chats(self, limit: int = 10) -> List[Dialog]:
        """Get recent chat dialogs"""
        try:
            dialogs = await self.client.get_dialogs(limit=limit)
            return dialogs
        except Exception as e:
            logger.error(f"Error fetching recent chats: {e}")
            return []
            
    async def send_message(self, chat_id: int, message: str) -> Optional[Message]:
        """Send a message to a specific chat"""
        try:
            return await self.client.send_message(chat_id, message)
        except Exception as e:
            logger.error(f"Error sending message to {chat_id}: {e}")
            return None
            
    async def get_chat_history(self, chat_id: int, limit: int = 50) -> List[Message]:
        """Get message history from a chat"""
        try:
            messages = await self.client.get_messages(chat_id, limit=limit)
            return messages
        except Exception as e:
            logger.error(f"Error fetching chat history for {chat_id}: {e}")
            return [] 