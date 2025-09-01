from fastapi import APIRouter, HTTPException, Request, status, BackgroundTasks
from typing import Dict, Any
import logging
from app.services.webhook_service import process_webhook_notification

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/tray/webhook")
async def tray_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle incoming webhook notifications from Tray"""
    try:
        # Get the form data from the webhook
        form_data = await request.form()
        payload = dict(form_data)
        
        logger.info(f"Received webhook notification: {payload}")
        
        # Process the webhook in the background
        background_tasks.add_task(process_webhook_notification, payload)
        
        # Return success response
        return {"status": "success", "message": "Webhook received"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )

@router.get("/tray/webhook")
async def tray_webhook_get(request: Request):
    """Handle GET requests to webhook endpoint (for verification)"""
    query_params = dict(request.query_params)
    logger.info(f"Received webhook GET request with params: {query_params}")
    return {"status": "success", "message": "Webhook endpoint is active"}

# Additional webhook endpoints for specific event types can be added here
