import httpx
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class TrayAPIClient:
    """API client for interacting with Tray's REST API"""
    
    def __init__(self, access_token: str, api_address: str):
        self.access_token = access_token
        self.api_address = api_address
        self.base_url = api_address.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, params: Dict = None, json_data: Dict = None):
        """Make an HTTP request to the Tray API"""
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params["access_token"] = self.access_token
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"HTTP error {e} for {method} {url}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error {e} for {method} {url}")
                raise
    
    # Products API
    async def list_products(self, limit: int = 30, page: int = 1):
        """List products from the store"""
        params = {"limit": limit, "page": page}
        return await self._make_request("GET", "/products", params)
    
    async def get_product(self, product_id: str):
        """Get a specific product by ID"""
        return await self._make_request("GET", f"/products/{product_id}")
    
    async def create_product(self, product_data: Dict[str, Any]):
        """Create a new product"""
        return await self._make_request("POST", "/products", json_data=product_data)
    
    async def update_product(self, product_id: str, product_data: Dict[str, Any]):
        """Update an existing product"""
        return await self._make_request("PUT", f"/products/{product_id}", json_data=product_data)
    
    async def delete_product(self, product_id: str):
        """Delete a product"""
        return await self._make_request("DELETE", f"/products/{product_id}")
    
    # Orders API
    async def list_orders(self, limit: int = 30, page: int = 1):
        """List orders from the store"""
        params = {"limit": limit, "page": page}
        return await self._make_request("GET", "/orders", params)
    
    async def get_order(self, order_id: str):
        """Get a specific order by ID"""
        return await self._make_request("GET", f"/orders/{order_id}")
    
    async def update_order(self, order_id: str, order_data: Dict[str, Any]):
        """Update an existing order"""
        return await self._make_request("PUT", f"/orders/{order_id}", json_data=order_data)
    
    async def cancel_order(self, order_id: str):
        """Cancel an order"""
        return await self._make_request("PUT", f"/orders/{order_id}/cancel")
    
    # Customers API
    async def list_customers(self, limit: int = 30, page: int = 1):
        """List customers from the store"""
        params = {"limit": limit, "page": page}
        return await self._make_request("GET", "/customers", params)
    
    async def get_customer(self, customer_id: str):
        """Get a specific customer by ID"""
        return await self._make_request("GET", f"/customers/{customer_id}")
    
    async def create_customer(self, customer_data: Dict[str, Any]):
        """Create a new customer"""
        return await self._make_request("POST", "/customers", json_data=customer_data)
    
    async def update_customer(self, customer_id: str, customer_data: Dict[str, Any]):
        """Update an existing customer"""
        return await self._make_request("PUT", f"/customers/{customer_id}", json_data=customer_data)
    
    async def delete_customer(self, customer_id: str):
        """Delete a customer"""
        return await self._make_request("DELETE", f"/customers/{customer_id}")
    
    # Categories API
    async def list_categories(self):
        """List all categories"""
        return await self._make_request("GET", "/categories")
    
    async def get_category(self, category_id: str):
        """Get a specific category by ID"""
        return await self._make_request("GET", f"/categories/{category_id}")
    
    # Store Info API
    async def get_store_info(self):
        """Get store information"""
        return await self._make_request("GET", "/store")
