import httpx
import logging
import os
from typing import Dict, Any, Optional
from app.services.token_service import TokenService
from app.core.config import settings

logger = logging.getLogger(__name__)

class TrayService:
    def __init__(self):
        self.token_service = TokenService()
    
    async def _make_request(self, seller_id: str, method: str, endpoint: str, params: Dict = None, json_data: Dict = None):
        """Make an authenticated request to the Tray API"""
        # 🧪 MODO DE DESENVOLVIMENTO - Retorna dados mockados
        dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
        
        # Get stored tokens
        tokens = self.token_service.get_tokens(seller_id)
        if not tokens or "access_token" not in tokens:
            if dev_mode or seller_id.startswith("dev_"):
                print(f"🧪 DEV MODE: Returning mock data for {method} {endpoint}")
                return self._get_mock_response(method, endpoint, params, json_data)
            raise Exception("No access token found for seller")
        
        access_token = tokens["access_token"]
        api_address = tokens.get("api_address", settings.TRAY_API_BASE_URL)
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Prepare URL
        url = f"{api_address}{endpoint}"
        params = params or {}
        
        # Make request
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # If it's a 401, try to refresh the token
                if e.response.status_code == 401:
                    logger.info(f"Token expired for seller {seller_id}, attempting refresh")
                    refreshed = await self._refresh_token(seller_id)
                    if refreshed:
                        # Retry the request with new token
                        return await self._make_request(seller_id, method, endpoint, params, json_data)
                logger.error(f"HTTP error {e} for {method} {url}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error {e} for {method} {url}")
                raise
    
    async def _refresh_token(self, seller_id: str) -> bool:
        """Refresh the access token for a seller"""
        try:
            # Get stored tokens
            stored_tokens = self.token_service.get_tokens(seller_id)
            if not stored_tokens or "refresh_token" not in stored_tokens:
                logger.error(f"No refresh token found for seller {seller_id}")
                return False
            
            refresh_token = stored_tokens["refresh_token"]
            api_address = stored_tokens.get("api_address", settings.TRAY_API_BASE_URL)
            
            # Make refresh request
            refresh_url = f"{api_address}/auth?refresh_token={refresh_token}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(refresh_url)
                response.raise_for_status()
                token_data = response.json()
                
                # Update stored tokens
                self.token_service.store_tokens(
                    seller_id,
                    {
                        "access_token": token_data["access_token"],
                        "refresh_token": token_data["refresh_token"],
                        "expires_in": token_data.get("expires_in", 3600),
                        "token_type": token_data.get("token_type", "Bearer"),
                        "api_address": api_address
                    }
                )
                
                logger.info(f"Successfully refreshed token for seller {seller_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to refresh token for seller {seller_id}: {str(e)}")
            return False
    
    # Products API
    async def list_products(self, seller_id: str, limit: int = 30, page: int = 1):
        """List products from the store"""
        params = {"limit": limit, "page": page}
        return await self._make_request(seller_id, "GET", "/products", params)
    
    async def get_product(self, seller_id: str, product_id: str):
        """Get a specific product by ID"""
        return await self._make_request(seller_id, "GET", f"/products/{product_id}")
    
    async def create_product(self, seller_id: str, product_data: Dict[str, Any]):
        """Create a new product"""
        return await self._make_request(seller_id, "POST", "/products", json_data=product_data)
    
    async def update_product(self, seller_id: str, product_id: str, product_data: Dict[str, Any]):
        """Update an existing product"""
        return await self._make_request(seller_id, "PUT", f"/products/{product_id}", json_data=product_data)
    
    async def delete_product(self, seller_id: str, product_id: str):
        """Delete a product"""
        return await self._make_request(seller_id, "DELETE", f"/products/{product_id}")
    
    # Orders API
    async def list_orders(self, seller_id: str, limit: int = 30, page: int = 1):
        """List orders from the store"""
        params = {"limit": limit, "page": page}
        return await self._make_request(seller_id, "GET", "/orders", params)
    
    async def get_order(self, seller_id: str, order_id: str):
        """Get a specific order by ID"""
        return await self._make_request(seller_id, "GET", f"/orders/{order_id}")
    
    async def update_order(self, seller_id: str, order_id: str, order_data: Dict[str, Any]):
        """Update an existing order"""
        return await self._make_request(seller_id, "PUT", f"/orders/{order_id}", json_data=order_data)
    
    async def cancel_order(self, seller_id: str, order_id: str):
        """Cancel an order"""
        return await self._make_request(seller_id, "PUT", f"/orders/{order_id}/cancel")
    
    # Customers API
    async def list_customers(self, seller_id: str, limit: int = 30, page: int = 1):
        """List customers from the store"""
        params = {"limit": limit, "page": page}
        return await self._make_request(seller_id, "GET", "/customers", params)
    
    async def get_customer(self, seller_id: str, customer_id: str):
        """Get a specific customer by ID"""
        return await self._make_request(seller_id, "GET", f"/customers/{customer_id}")
    
    async def create_customer(self, seller_id: str, customer_data: Dict[str, Any]):
        """Create a new customer"""
        return await self._make_request(seller_id, "POST", "/customers", json_data=customer_data)
    
    async def update_customer(self, seller_id: str, customer_id: str, customer_data: Dict[str, Any]):
        """Update an existing customer"""
        return await self._make_request(seller_id, "PUT", f"/customers/{customer_id}", json_data=customer_data)
    
    async def delete_customer(self, seller_id: str, customer_id: str):
        """Delete a customer"""
        return await self._make_request(seller_id, "DELETE", f"/customers/{customer_id}")
    
    # Categories API
    async def list_categories(self, seller_id: str):
        """List all categories"""
        return await self._make_request(seller_id, "GET", "/categories")
    
    async def get_category(self, seller_id: str, category_id: str):
        """Get a specific category by ID"""
        return await self._make_request(seller_id, "GET", f"/categories/{category_id}")
    
    # Store Info API
    async def get_store_info(self, seller_id: str):
        """Get store information"""
        return await self._make_request(seller_id, "GET", "/store")
    
    def _get_mock_response(self, method: str, endpoint: str, params: Dict = None, json_data: Dict = None):
        """🧪 Retorna dados mockados para desenvolvimento"""
        import random
        from datetime import datetime
        
        # Produtos
        if "/products" in endpoint and method == "GET":
            if endpoint.endswith("/products"):
                return {
                    "products": [
                        {
                            "id": 1,
                            "name": "Produto de Teste 1",
                            "price": 99.99,
                            "description": "Descrição do produto de teste 1",
                            "category_id": 1,
                            "stock": 50,
                            "active": True,
                            "created_at": "2024-01-01T10:00:00Z"
                        },
                        {
                            "id": 2,
                            "name": "Produto de Teste 2",
                            "price": 149.99,
                            "description": "Descrição do produto de teste 2",
                            "category_id": 2,
                            "stock": 25,
                            "active": True,
                            "created_at": "2024-01-02T11:00:00Z"
                        }
                    ],
                    "total": 2,
                    "page": 1,
                    "limit": 30
                }
            else:
                product_id = endpoint.split("/")[-1]
                return {
                    "id": int(product_id),
                    "name": f"Produto {product_id}",
                    "price": random.uniform(10.0, 500.0),
                    "description": f"Descrição do produto {product_id}",
                    "category_id": random.randint(1, 5),
                    "stock": random.randint(0, 100),
                    "active": True,
                    "created_at": "2024-01-01T10:00:00Z"
                }
        
        # Criação de produto
        elif "/products" in endpoint and method == "POST":
            return {
                "id": random.randint(100, 999),
                "name": json_data.get("name", "Novo Produto"),
                "price": json_data.get("price", 0.0),
                "description": json_data.get("description", ""),
                "category_id": 1,
                "stock": 0,
                "active": True,
                "created_at": datetime.now().isoformat() + "Z"
            }
        
        # Atualização de produto
        elif "/products" in endpoint and method == "PUT":
            product_id = endpoint.split("/")[-1]
            return {
                "id": int(product_id),
                "name": json_data.get("name", f"Produto Atualizado {product_id}"),
                "price": json_data.get("price", 99.99),
                "description": json_data.get("description", "Produto atualizado"),
                "category_id": 1,
                "stock": 10,
                "active": True,
                "updated_at": datetime.now().isoformat() + "Z"
            }
        
        # Pedidos
        elif "/orders" in endpoint and method == "GET":
            if endpoint.endswith("/orders"):
                return {
                    "orders": [
                        {
                            "id": 1001,
                            "status": "pending",
                            "total": 199.98,
                            "customer_id": 1,
                            "customer_name": "João Silva",
                            "customer_email": "joao@example.com",
                            "items": [
                                {"product_id": 1, "quantity": 2, "price": 99.99}
                            ],
                            "created_at": "2024-01-01T12:00:00Z"
                        },
                        {
                            "id": 1002,
                            "status": "completed",
                            "total": 149.99,
                            "customer_id": 2,
                            "customer_name": "Maria Santos",
                            "customer_email": "maria@example.com",
                            "items": [
                                {"product_id": 2, "quantity": 1, "price": 149.99}
                            ],
                            "created_at": "2024-01-02T14:00:00Z"
                        }
                    ],
                    "total": 2,
                    "page": 1,
                    "limit": 30
                }
            else:
                order_id = endpoint.split("/")[-1]
                return {
                    "id": int(order_id),
                    "status": "pending",
                    "total": random.uniform(50.0, 1000.0),
                    "customer_id": random.randint(1, 100),
                    "customer_name": "Cliente Teste",
                    "customer_email": "cliente@example.com",
                    "items": [
                        {"product_id": 1, "quantity": 1, "price": 99.99}
                    ],
                    "created_at": "2024-01-01T12:00:00Z"
                }
        
        # Clientes
        elif "/customers" in endpoint and method == "GET":
            if endpoint.endswith("/customers"):
                return {
                    "customers": [
                        {
                            "id": 1,
                            "name": "João Silva",
                            "email": "joao@example.com",
                            "phone": "(11) 99999-9999",
                            "created_at": "2024-01-01T10:00:00Z"
                        },
                        {
                            "id": 2,
                            "name": "Maria Santos",
                            "email": "maria@example.com",
                            "phone": "(11) 88888-8888",
                            "created_at": "2024-01-02T11:00:00Z"
                        }
                    ],
                    "total": 2,
                    "page": 1,
                    "limit": 30
                }
            else:
                customer_id = endpoint.split("/")[-1]
                return {
                    "id": int(customer_id),
                    "name": f"Cliente {customer_id}",
                    "email": f"cliente{customer_id}@example.com",
                    "phone": "(11) 99999-9999",
                    "created_at": "2024-01-01T10:00:00Z"
                }
        
        # Categorias
        elif "/categories" in endpoint and method == "GET":
            if endpoint.endswith("/categories"):
                return {
                    "categories": [
                        {"id": 1, "name": "Eletrônicos", "description": "Produtos eletrônicos"},
                        {"id": 2, "name": "Roupas", "description": "Vestuário em geral"},
                        {"id": 3, "name": "Casa", "description": "Produtos para casa"},
                        {"id": 4, "name": "Esportes", "description": "Artigos esportivos"},
                        {"id": 5, "name": "Livros", "description": "Livros e literatura"}
                    ],
                    "total": 5
                }
            else:
                category_id = endpoint.split("/")[-1]
                return {
                    "id": int(category_id),
                    "name": f"Categoria {category_id}",
                    "description": f"Descrição da categoria {category_id}"
                }
        
        # Informações da loja
        elif "/store" in endpoint and method == "GET":
            return {
                "id": 1,
                "name": "Loja de Teste MCP",
                "description": "Loja de desenvolvimento para testes do MCP Server",
                "email": "contato@lojateste.com",
                "phone": "(11) 99999-9999",
                "address": {
                    "street": "Rua de Teste, 123",
                    "city": "São Paulo",
                    "state": "SP",
                    "zipcode": "01234-567",
                    "country": "Brasil"
                },
                "settings": {
                    "currency": "BRL",
                    "timezone": "America/Sao_Paulo",
                    "language": "pt-BR"
                },
                "created_at": "2024-01-01T00:00:00Z"
            }
        
        # Resposta padrão
        else:
            return {
                "message": f"Mock response for {method} {endpoint}",
                "data": json_data or {},
                "params": params or {},
                "timestamp": datetime.now().isoformat() + "Z",
                "dev_mode": True
            }
