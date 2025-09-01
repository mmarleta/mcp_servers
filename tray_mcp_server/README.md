# Tray MCP Server

A FastAPI-based Model Context Protocol (MCP) server for integrating with the Tray e-commerce platform.

## Features

- OAuth2 authentication with Tray
- Webhook handling for real-time notifications
- REST API client for Tray's endpoints
- Secure token management
- Docker support
- Health checks

## Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- Tray developer account and application credentials

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd tray-mcp-server
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

Create a `.env` file based on `.env.example` and configure the following variables:

- `SECRET_KEY`: A secure secret key for JWT token signing
- `TRAY_CONSUMER_KEY`: Your Tray application consumer key
- `TRAY_CONSUMER_SECRET`: Your Tray application consumer secret

## Running the Application

### Local Development

```bash
uvicorn app.main:app --reload
```

The server will be available at `http://localhost:8000`.

### With Docker

```bash
docker-compose up --build
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/v1/auth/tray/auth-url` - Generate Tray authentication URL
- `POST /api/v1/auth/tray/token` - Exchange authorization code for access token
- `GET /api/v1/auth/tray/refresh-token` - Refresh access token
- `POST /api/v1/webhooks/tray/webhook` - Handle Tray webhook notifications
- `GET /api/v1/webhooks/tray/webhook` - Webhook verification endpoint

## Tray Integration Flow

1. **Application Registration**: Register your application with Tray to obtain consumer key and secret
2. **Authentication**: Use OAuth2 authorization code flow to obtain access tokens
3. **API Usage**: Use the access tokens to make authenticated requests to Tray APIs
4. **Webhooks**: Configure webhook URL in Tray to receive real-time notifications

## Webhook Handling

The server listens for webhook notifications from Tray at `/api/v1/webhooks/tray/webhook`. Supported events include:

- Order creation/update/cancellation

## Using the Tray API Endpoints

After successfully authenticating with Tray and obtaining access tokens, you can use the following endpoints to interact with the Tray API. All endpoints require authentication via the `Authorization` header with a valid JWT token.

### Products

- `GET /api/v1/tray/products?seller_id={store_host}` - List products
- `GET /api/v1/tray/products/{product_id}?seller_id={store_host}` - Get a specific product
- `POST /api/v1/tray/products?seller_id={store_host}` - Create a new product
- `PUT /api/v1/tray/products/{product_id}?seller_id={store_host}` - Update an existing product
- `DELETE /api/v1/tray/products/{product_id}?seller_id={store_host}` - Delete a product

### Orders

- `GET /api/v1/tray/orders?seller_id={store_host}` - List orders
- `GET /api/v1/tray/orders/{order_id}?seller_id={store_host}` - Get a specific order
- `PUT /api/v1/tray/orders/{order_id}?seller_id={store_host}` - Update an existing order
- `PUT /api/v1/tray/orders/{order_id}/cancel?seller_id={store_host}` - Cancel an order

### Customers

- `GET /api/v1/tray/customers?seller_id={store_host}` - List customers
- `GET /api/v1/tray/customers/{customer_id}?seller_id={store_host}` - Get a specific customer
- `POST /api/v1/tray/customers?seller_id={store_host}` - Create a new customer
- `PUT /api/v1/tray/customers/{customer_id}?seller_id={store_host}` - Update an existing customer
- `DELETE /api/v1/tray/customers/{customer_id}?seller_id={store_host}` - Delete a customer

### Categories

- `GET /api/v1/tray/categories?seller_id={store_host}` - List all categories
- `GET /api/v1/tray/categories/{category_id}?seller_id={store_host}` - Get a specific category

### Store Information

- `GET /api/v1/tray/store?seller_id={store_host}` - Get store information

### Authentication

All endpoints require a valid JWT token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

The `seller_id` parameter corresponds to the `store_host` used during the authentication process.
- Product creation/update/deletion
- Customer creation/update/deletion
- Stock updates

## Tray API Client

The server includes a client for interacting with Tray's REST APIs:

- Products management
- Orders management
- Customers management
- Categories
- Store information

## License

This project is licensed under the MIT License.
