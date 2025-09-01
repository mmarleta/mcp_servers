import redis
import json
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class TokenService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    def store_tokens(self, seller_id: str, tokens: Dict[str, Any]) -> bool:
        """Store tokens for a seller in Redis"""
        try:
            key = f"tray_tokens:{seller_id}"
            self.redis_client.setex(
                key,
                30 * 24 * 60 * 60,  # 30 days
                json.dumps(tokens)
            )
            return True
        except Exception as e:
            logger.error(f"Error storing tokens for seller {seller_id}: {str(e)}")
            return False
    
    def get_tokens(self, seller_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve tokens for a seller from Redis"""
        try:
            key = f"tray_tokens:{seller_id}"
            tokens_json = self.redis_client.get(key)
            if tokens_json:
                return json.loads(tokens_json)
            return None
        except Exception as e:
            logger.error(f"Error retrieving tokens for seller {seller_id}: {str(e)}")
            return None
    
    def delete_tokens(self, seller_id: str) -> bool:
        """Delete tokens for a seller from Redis"""
        try:
            key = f"tray_tokens:{seller_id}"
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting tokens for seller {seller_id}: {str(e)}")
            return False
    
    def refresh_token_exists(self, seller_id: str) -> bool:
        """Check if refresh token exists for a seller"""
        try:
            tokens = self.get_tokens(seller_id)
            return tokens is not None and "refresh_token" in tokens
        except Exception as e:
            logger.error(f"Error checking refresh token for seller {seller_id}: {str(e)}")
            return False
