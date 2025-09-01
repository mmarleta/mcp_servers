from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(String, index=True)
    scope_name = Column(String, index=True)
    scope_id = Column(String, index=True)
    action = Column(String)
    app_code = Column(String)
    payload = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    status = Column(String, default="pending")  # pending, processed, failed
    
    def __repr__(self):
        return f"<WebhookEvent(scope={self.scope_name}, action={self.action}, id={self.scope_id})>"
