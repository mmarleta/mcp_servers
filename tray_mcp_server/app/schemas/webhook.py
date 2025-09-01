from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class WebhookEventBase(BaseModel):
    seller_id: str
    scope_name: str
    scope_id: str
    action: str
    app_code: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class WebhookEventCreate(WebhookEventBase):
    pass

class WebhookEventUpdate(WebhookEventBase):
    status: Optional[str] = None
    processed_at: Optional[datetime] = None

class WebhookEventInDBBase(WebhookEventBase):
    id: int
    created_at: datetime
    processed_at: Optional[datetime] = None
    status: str
    
    class Config:
        from_attributes = True

class WebhookEvent(WebhookEventInDBBase):
    pass

class WebhookEventInDB(WebhookEventInDBBase):
    pass
