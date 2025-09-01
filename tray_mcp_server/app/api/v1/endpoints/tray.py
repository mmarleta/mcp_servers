from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from app.services.tray_service import TrayService
from app.auth.oauth2 import get_current_user

router = APIRouter()
tray_service = TrayService()

# Request/Response Models
class ProductCreate(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    

class CustomerCreate(BaseModel):
    name: str
    email: str
    

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

# Products Endpoints
@router.get("/products")
async def list_products(seller_id: str, limit: int = 30, page: int = 1, current_user: dict = Depends(get_current_user)):
    """List products from the store"""
    try:
        result = await tray_service.list_products(seller_id, limit, page)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list products: {str(e)}")

@router.get("/products/{product_id}")
async def get_product(seller_id: str, product_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific product by ID"""
    try:
        result = await tray_service.get_product(seller_id, product_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")

@router.post("/products")
async def create_product(seller_id: str, product: ProductCreate, current_user: dict = Depends(get_current_user)):
    """Create a new product"""
    try:
        result = await tray_service.create_product(seller_id, product.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

@router.put("/products/{product_id}")
async def update_product(seller_id: str, product_id: str, product: ProductUpdate, current_user: dict = Depends(get_current_user)):
    """Update an existing product"""
    try:
        result = await tray_service.update_product(seller_id, product_id, product.dict(exclude_unset=True))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")

@router.delete("/products/{product_id}")
async def delete_product(seller_id: str, product_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a product"""
    try:
        result = await tray_service.delete_product(seller_id, product_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")

# Orders Endpoints
@router.get("/orders")
async def list_orders(seller_id: str, limit: int = 30, page: int = 1, current_user: dict = Depends(get_current_user)):
    """List orders from the store"""
    try:
        result = await tray_service.list_orders(seller_id, limit, page)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list orders: {str(e)}")

@router.get("/orders/{order_id}")
async def get_order(seller_id: str, order_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific order by ID"""
    try:
        result = await tray_service.get_order(seller_id, order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get order: {str(e)}")

@router.put("/orders/{order_id}")
async def update_order(seller_id: str, order_id: str, order: OrderUpdate, current_user: dict = Depends(get_current_user)):
    """Update an existing order"""
    try:
        result = await tray_service.update_order(seller_id, order_id, order.dict(exclude_unset=True))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update order: {str(e)}")

@router.put("/orders/{order_id}/cancel")
async def cancel_order(seller_id: str, order_id: str, current_user: dict = Depends(get_current_user)):
    """Cancel an order"""
    try:
        result = await tray_service.cancel_order(seller_id, order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel order: {str(e)}")

# Customers Endpoints
@router.get("/customers")
async def list_customers(seller_id: str, limit: int = 30, page: int = 1, current_user: dict = Depends(get_current_user)):
    """List customers from the store"""
    try:
        result = await tray_service.list_customers(seller_id, limit, page)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list customers: {str(e)}")

@router.get("/customers/{customer_id}")
async def get_customer(seller_id: str, customer_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific customer by ID"""
    try:
        result = await tray_service.get_customer(seller_id, customer_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer: {str(e)}")

@router.post("/customers")
async def create_customer(seller_id: str, customer: CustomerCreate, current_user: dict = Depends(get_current_user)):
    """Create a new customer"""
    try:
        result = await tray_service.create_customer(seller_id, customer.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create customer: {str(e)}")

@router.put("/customers/{customer_id}")
async def update_customer(seller_id: str, customer_id: str, customer: CustomerUpdate, current_user: dict = Depends(get_current_user)):
    """Update an existing customer"""
    try:
        result = await tray_service.update_customer(seller_id, customer_id, customer.dict(exclude_unset=True))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update customer: {str(e)}")

@router.delete("/customers/{customer_id}")
async def delete_customer(seller_id: str, customer_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a customer"""
    try:
        result = await tray_service.delete_customer(seller_id, customer_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete customer: {str(e)}")

# Categories Endpoints
@router.get("/categories")
async def list_categories(seller_id: str, current_user: dict = Depends(get_current_user)):
    """List all categories"""
    try:
        result = await tray_service.list_categories(seller_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list categories: {str(e)}")

@router.get("/categories/{category_id}")
async def get_category(seller_id: str, category_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific category by ID"""
    try:
        result = await tray_service.get_category(seller_id, category_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get category: {str(e)}")

# Store Info Endpoint
@router.get("/store")
async def get_store_info(seller_id: str, current_user: dict = Depends(get_current_user)):
    """Get store information"""
    try:
        result = await tray_service.get_store_info(seller_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get store info: {str(e)}")
