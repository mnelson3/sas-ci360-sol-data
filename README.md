# SAS Customer Intelligence 360

## SAS 360 SOLUTIONS - Data Module

This repository provides Python interfaces for SAS Customer Intelligence 360 Data Management and Marketing Data APIs.

### Overview

The Data module enables programmatic access to CI360's data management capabilities, including audience data, customer profiles, and marketing data operations.

### Features

- Marketing Data API integration
- Audience management
- Data import/export operations
- Customer profile management
- Data validation and processing

### Prerequisites

- Python 3.8+
- Access to SAS Customer Intelligence 360 environment
- Required dependencies (see requirements.txt)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/sas-ci360-sol-data.git
   cd sas-ci360-sol-data
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Getting Started

```python
from sasci360soldata.base import CI360DataBase, CI360DataConfig

# Initialize with your CI360 credentials
config = CI360DataConfig(
    host="your-ci360-host",
    secret_key="your-secret-key",
    tenant_id="your-tenant-id"
)
data_client = CI360DataBase(config)

# Use the client for data operations
customers = data_client.get_customers()
```

### Solutions Code

The data module provides:

1. **Data Management**: Core data operations and API calls
2. **Audience Operations**: Create, update, and manage marketing audiences
3. **Profile Management**: Customer profile data handling
4. **Import/Export**: Data transfer utilities

### Troubleshooting

- Verify API credentials and endpoints
- Check network connectivity to CI360
- Review API response logs for errors

## 🛠️ Developer/Implementation Guide

This section provides comprehensive guidance for developers implementing data management solutions with SAS CI360.

### Architecture Overview

The SAS CI360 Data module follows a layered architecture designed for robust customer data management:

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Module                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Customer    │ │ Audience    │ │ Data I/O    │           │
│  │ Management  │ │ Operations  │ │ Operations  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ REST API    │ │ JWT Auth    │ │ Async I/O   │           │
│  │ Client      │ │ & Security  │ │ Operations  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

#### Core Components

1. **Customer Management Layer**
   - `CI360DataBase`: Core client class for customer data operations
   - Customer CRUD operations (Create, Read, Update, Delete)
   - Profile data management and enrichment
   - Customer segmentation and targeting

2. **Audience Operations Layer**
   - Audience creation and management
   - Segment-based operations
   - Audience analytics and reporting
   - Dynamic audience updates

3. **Data I/O Operations Layer**
   - Data import/export functionality
   - Bulk data processing
   - Data validation and transformation
   - ETL pipeline integration

### Configuration Management

#### Environment Variables
```bash
export SAS_CI360_SECRET_KEY="your-secret-key"
export SAS_CI360_TENANT_ID="your-tenant-id"
```

#### Configuration Class
```python
from sasci360soldata.base import CI360DataConfig

config = CI360DataConfig(
    algorithm="HS256",
    api_base="/marketingData",
    encoding="utf-8",
    host="your-ci360-host.sas.com",
    secret_key="your-secret-key",
    tenant_id="your-tenant-id"
)
```

### API Integration Patterns

#### Customer Data Operations
```python
from sasci360soldata.base import CI360DataBase

# Initialize client
client = CI360DataBase()

# Get all customers
customers = client.get_customers()
print(f"Found {len(customers)} customers")

# Create new customer
customer_data = {
    'firstName': 'John',
    'lastName': 'Doe',
    'email': 'john.doe@example.com',
    'attributes': {
        'loyalty_tier': 'gold',
        'signup_date': '2024-01-15'
    }
}
result = client.create_customer(customer_data)
print(f"Created customer: {result['id']}")
```

#### Asynchronous Operations
```python
import asyncio
from sasci360soldata.base import CI360DataBase

async def manage_customer_data():
    client = CI360DataBase()

    # Get customer asynchronously
    customer = await client.get_customer_async('customer-123')
    print(f"Customer: {customer['firstName']} {customer['lastName']}")

    # Update customer data
    update_data = {
        'attributes': {
            'last_login': '2024-01-15T10:30:00Z',
            'purchase_count': 15
        }
    }
    result = await client.update_customer_async('customer-123', update_data)
    print(f"Updated customer: {result['id']}")

# Run async operations
asyncio.run(manage_customer_data())
```

#### Audience Management
```python
# Create marketing audience
audience_data = {
    'name': 'High-Value Customers',
    'description': 'Customers with >$1000 lifetime value',
    'criteria': {
        'lifetime_value': {'gt': 1000},
        'last_purchase': {'within': '90 days'}
    },
    'size': 5000
}

audience = client.create_audience(audience_data)
print(f"Created audience: {audience['id']}")

# Get audience segments
segments = client.get_segments(audience_id=audience['id'])
for segment in segments:
    print(f"Segment: {segment['name']} - Size: {segment['count']}")
```

### Error Handling

#### Exception Types
```python
from sasci360soldata.base import (
    CI360DataBase,
    CI360DataError,
    CI360DataAuthError,
    CI360DataValidationError
)

try:
    client = CI360DataBase()
    customers = client.get_customers()
except CI360DataAuthError as e:
    print(f"Authentication failed: {e}")
    # Handle auth issues (token refresh, credentials)
except CI360DataValidationError as e:
    print(f"Validation error: {e}")
    # Handle input validation issues
except CI360DataError as e:
    print(f"API error: {e}")
    # Handle general API errors
```

#### Bulk Operation Error Handling
```python
def process_customers_batch(client, customer_batch):
    successful = []
    failed = []

    for customer_data in customer_batch:
        try:
            result = client.create_customer(customer_data)
            successful.append(result)
        except CI360DataValidationError as e:
            failed.append({
                'data': customer_data,
                'error': str(e)
            })
        except Exception as e:
            failed.append({
                'data': customer_data,
                'error': f"Unexpected error: {str(e)}"
            })

    return successful, failed
```

### Testing Approaches

#### Unit Testing
```python
import unittest
from unittest.mock import Mock, patch
from sasci360soldata.base import CI360DataBase

class TestDataOperations(unittest.TestCase):
    def setUp(self):
        self.client = CI360DataBase()
        self.mock_response = Mock()
        self.mock_response.json.return_value = {'id': '123', 'status': 'success'}

    @patch('requests.Session.request')
    def test_get_customers(self, mock_request):
        mock_request.return_value = self.mock_response

        result = self.client.get_customers()
        self.assertEqual(result['status'], 'success')
        mock_request.assert_called_once()

    @patch('sasci360soldata.base.CI360DataBase._generate_token')
    def test_authentication(self, mock_generate):
        mock_generate.return_value = 'mock-jwt-token'

        headers = self.client.get_auth_headers()
        self.assertIn('Authorization', headers)
        self.assertEqual(headers['Authorization'], 'Bearer mock-jwt-token')
```

#### Integration Testing
```python
import pytest
from sasci360soldata.base import CI360DataBase

@pytest.fixture
def data_client():
    return CI360DataBase()

@pytest.mark.integration
def test_customer_lifecycle(data_client):
    # Test complete customer lifecycle
    customer_data = {
        'firstName': 'Test',
        'lastName': 'User',
        'email': 'test@example.com'
    }

    # Create
    created = data_client.create_customer(customer_data)
    customer_id = created['id']

    # Read
    retrieved = data_client.get_customer(customer_id)
    assert retrieved['email'] == 'test@example.com'

    # Update
    updated_data = customer_data.copy()
    updated_data['firstName'] = 'Updated'
    updated = data_client.update_customer(customer_id, updated_data)
    assert updated['firstName'] == 'Updated'

    # Delete
    deleted = data_client.delete_customer(customer_id)
    assert deleted is True
```

### Performance Considerations

#### Batch Processing
```python
# Process customers in batches for better performance
def process_customers_batch_async(client, customer_list, batch_size=100):
    async def process_batch(batch):
        tasks = [client.create_customer_async(customer) for customer in batch]
        return await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for i in range(0, len(customer_list), batch_size):
        batch = customer_list[i:i + batch_size]
        batch_results = asyncio.run(process_batch(batch))
        results.extend(batch_results)

    return results
```

#### Connection Optimization
```python
# Configure session for high-throughput operations
client._session.mount('https://', requests.adapters.HTTPAdapter(
    pool_connections=20,
    pool_maxsize=40,
    max_retries=5,
    pool_block=False
))
```

#### Data Caching
```python
from cachetools import TTLCache

class CachedDataClient(CI360DataBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._customer_cache = TTLCache(maxsize=5000, ttl=600)  # 10 minute TTL

    def get_customer(self, customer_id: str):
        if customer_id in self._customer_cache:
            return self._customer_cache[customer_id]

        customer = super().get_customer(customer_id)
        self._customer_cache[customer_id] = customer
        return customer
```

### Data Privacy and Compliance

1. **PII Handling**: Implement proper PII masking and encryption
2. **GDPR Compliance**: Support right to erasure and data portability
3. **Audit Logging**: Track all data access and modifications
4. **Data Retention**: Implement automated data cleanup policies
5. **Access Control**: Role-based access to sensitive customer data

### Contributing

We welcome your contributions! Please read [CONTRIBUTING](CONTRIBUTING.md) for details on how to submit contributions to this project.

### License

This project is licensed under the [Nelson Grey LLC Community License 1.0](LICENSE).

- **Free for individuals, education, and research**: use, modify, and distribute this software for non-commercial purposes
- **Commercial evaluation**: evaluate the software for a possible commercial use, free of charge
- **Commercial production use**: requires a commercial license from Nelson Grey LLC
- **Automatic conversion**: on December 13, 2029, this automatically converts to the Apache License 2.0

For commercial licensing inquiries, contact support@nelsongrey.com.

### Additional Resources

For more information, see [Marketing Data API](https://go.documentation.sas.com/doc/en/cintcdc/production.a/cintapis/rest-mkt-data.htm).
