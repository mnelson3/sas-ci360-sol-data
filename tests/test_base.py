#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for SAS CI360 Data Module

Comprehensive test suite for the CI360DataBase class and its APIs.
"""

import asyncio
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from sasci360soldata.base import CI360DataBase, CI360DataConfig, CI360DataError


class TestCI360DataConfig(unittest.TestCase):
    """Test cases for CI360DataConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CI360DataConfig()
        self.assertEqual(config.algorithm, "HS256")
        self.assertEqual(config.api_base, "/marketingData")
        self.assertEqual(config.encoding, "utf-8")
        self.assertIsNone(config.host)
        self.assertIsNone(config.secret_key)
        self.assertIsNone(config.tenant_id)
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.retry_backoff, 0.5)
        self.assertTrue(config.enable_compression)

    def test_custom_config(self):
        """Test custom configuration values."""
        config = CI360DataConfig(
            host="https://api.example.com",
            secret_key="test-secret",
            tenant_id="test-tenant",
            timeout=60,
            max_retries=5
        )
        self.assertEqual(config.host, "https://api.example.com")
        self.assertEqual(config.secret_key, "test-secret")
        self.assertEqual(config.tenant_id, "test-tenant")
        self.assertEqual(config.timeout, 60)
        self.assertEqual(config.max_retries, 5)


class TestCI360DataBase(unittest.TestCase):
    """Test cases for CI360DataBase class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = CI360DataConfig(
            host="https://api.example.com",
            secret_key="test-secret-key",
            tenant_id="test-tenant-id"
        )

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    def test_initialization_success(self, mock_encryption_class, mock_session_class):
        """Test successful initialization."""
        mock_encryption = Mock()
        mock_encryption.generate_jwt.return_value = "test-token"
        mock_encryption_class.return_value = mock_encryption

        mock_session = Mock()
        mock_session_class.return_value = mock_session

        client = CI360DataBase(self.config)

        self.assertEqual(client.config, self.config)
        self.assertEqual(client.token, "test-token")
        mock_encryption_class.assert_called_once()
        mock_session_class.assert_called_once()

    def test_initialization_missing_config(self):
        """Test initialization with missing required config."""
        incomplete_config = CI360DataConfig(host="https://api.example.com")
        with self.assertRaises(CI360DataError):
            CI360DataBase(incomplete_config)

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    def test_get_auth_headers(self, mock_encryption_class, mock_session_class):
        """Test authentication headers generation."""
        mock_encryption = Mock()
        mock_encryption.generate_jwt.return_value = "test-jwt-token"
        mock_encryption_class.return_value = mock_encryption

        client = CI360DataBase(self.config)
        headers = client.get_auth_headers()

        expected_headers = {
            "Authorization": "Bearer test-jwt-token",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Tenant-ID": "test-tenant-id"
        }
        self.assertEqual(headers, expected_headers)

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase.validate_connection_async')
    def test_validate_connection_async_success(self, mock_validate, mock_encryption_class, mock_session_class):
        """Test successful async connection validation."""
        mock_validate.return_value = True

        client = CI360DataBase(self.config)
        result = asyncio.run(client.validate_connection_async())

        self.assertTrue(result)
        mock_validate.assert_called_once()

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase.validate_connection_async')
    def test_validate_connection_async_failure(self, mock_validate, mock_encryption_class, mock_session_class):
        """Test failed async connection validation."""
        mock_validate.return_value = False

        client = CI360DataBase(self.config)
        result = asyncio.run(client.validate_connection_async())

        self.assertFalse(result)

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_get_customers_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async customer retrieval."""
        mock_request.return_value = {"customers": [], "total": 0}

        client = CI360DataBase(self.config)
        result = asyncio.run(client.get_customers_async(limit=10, offset=5))

        self.assertEqual(result, {"customers": [], "total": 0})
        mock_request.assert_called_once_with(
            "GET", "/customers",
            params={"limit": 10, "offset": 5}
        )

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_get_customer_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async single customer retrieval."""
        mock_request.return_value = {"id": "123", "name": "John Doe"}

        client = CI360DataBase(self.config)
        result = asyncio.run(client.get_customer_async("123"))

        self.assertEqual(result, {"id": "123", "name": "John Doe"})
        mock_request.assert_called_once_with("GET", "/customers/123")

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_create_customer_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async customer creation."""
        customer_data = {"name": "John Doe", "email": "john@example.com"}
        mock_request.return_value = {"id": "123", **customer_data}

        client = CI360DataBase(self.config)
        result = asyncio.run(client.create_customer_async(customer_data))

        self.assertEqual(result, {"id": "123", **customer_data})
        mock_request.assert_called_once_with("POST", "/customers", data=customer_data)

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_update_customer_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async customer update."""
        update_data = {"name": "Jane Doe"}
        mock_request.return_value = {"id": "123", "name": "Jane Doe", "email": "john@example.com"}

        client = CI360DataBase(self.config)
        result = asyncio.run(client.update_customer_async("123", update_data))

        self.assertEqual(result["name"], "Jane Doe")
        mock_request.assert_called_once_with("PUT", "/customers/123", data=update_data)

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_delete_customer_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async customer deletion."""
        mock_request.return_value = None

        client = CI360DataBase(self.config)
        result = asyncio.run(client.delete_customer_async("123"))

        self.assertTrue(result)
        mock_request.assert_called_once_with("DELETE", "/customers/123")

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_get_segments_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async segment retrieval."""
        mock_request.return_value = {"segments": [], "total": 0}

        client = CI360DataBase(self.config)
        result = asyncio.run(client.get_segments_async(limit=20, offset=10))

        self.assertEqual(result, {"segments": [], "total": 0})
        mock_request.assert_called_once_with(
            "GET", "/segments",
            params={"limit": 20, "offset": 10}
        )

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_create_segment_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async segment creation."""
        segment_data = {"name": "High Value Customers", "criteria": {"totalSpent": {"gt": 1000}}}
        mock_request.return_value = {"id": "seg-123", **segment_data}

        client = CI360DataBase(self.config)
        result = asyncio.run(client.create_segment_async(segment_data))

        self.assertEqual(result["name"], "High Value Customers")
        mock_request.assert_called_once_with("POST", "/segments", data=segment_data)

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_import_data_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async data import."""
        data = [{"name": "John", "email": "john@test.com"}]
        mock_request.return_value = {"imported": 1, "failed": 0, "jobId": "import-123"}

        client = CI360DataBase(self.config)
        result = asyncio.run(client.import_data_async(data, "customers"))

        self.assertEqual(result["imported"], 1)
        expected_payload = {"data": data, "dataType": "customers"}
        mock_request.assert_called_once_with("POST", "/import", data=expected_payload)

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_export_data_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async data export."""
        mock_request.return_value = {"exportId": "exp-123", "status": "processing"}

        client = CI360DataBase(self.config)
        result = asyncio.run(client.export_data_async("customers", {"segmentId": "seg-123"}, "json"))

        self.assertEqual(result["status"], "processing")
        expected_params = {"dataType": "customers", "format": "json", "segmentId": "seg-123"}
        mock_request.assert_called_once_with("GET", "/export", params=expected_params)

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_validate_data_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async data validation."""
        data = [{"name": "John", "email": "invalid-email"}]
        mock_request.return_value = {"valid": False, "errors": ["Invalid email format"]}

        client = CI360DataBase(self.config)
        result = asyncio.run(client.validate_data_async(data, "customers"))

        self.assertFalse(result["valid"])
        self.assertIn("Invalid email format", result["errors"])

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_get_schema_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async schema retrieval."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        mock_request.return_value = schema

        client = CI360DataBase(self.config)
        result = asyncio.run(client.get_schema_async("customers"))

        self.assertEqual(result, schema)
        mock_request.assert_called_once_with("GET", "/schema", params={"dataType": "customers"})

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_update_schema_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async schema update."""
        new_schema = {"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}
        mock_request.return_value = new_schema

        client = CI360DataBase(self.config)
        result = asyncio.run(client.update_schema_async("customers", new_schema))

        self.assertEqual(result, new_schema)
        expected_payload = {"dataType": "customers", "schema": new_schema}
        mock_request.assert_called_once_with("PUT", "/schema", data=expected_payload)

    # Synchronous method tests

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_get_customers_sync(self, mock_request, mock_encryption_class, mock_session_class):
        """Test synchronous customer retrieval."""
        mock_request.return_value = {"customers": [], "total": 0}

        client = CI360DataBase(self.config)
        result = client.get_customers(limit=10, offset=5)

        self.assertEqual(result, {"customers": [], "total": 0})

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_create_customer_sync(self, mock_request, mock_encryption_class, mock_session_class):
        """Test synchronous customer creation."""
        customer_data = {"name": "John Doe", "email": "john@example.com"}
        mock_request.return_value = {"id": "123", **customer_data}

        client = CI360DataBase(self.config)
        result = client.create_customer(customer_data)

        self.assertEqual(result["name"], "John Doe")

    # Context manager tests

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase.validate_connection')
    def test_context_manager_sync(self, mock_validate, mock_encryption_class, mock_session_class):
        """Test synchronous context manager."""
        mock_validate.return_value = True
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        client = CI360DataBase(self.config)

        with client as ctx:
            self.assertEqual(ctx, client)

        mock_session.close.assert_called_once()

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase.validate_connection_async')
    def test_context_manager_async(self, mock_validate, mock_encryption_class, mock_session_class):
        """Test asynchronous context manager."""
        mock_validate.return_value = True
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        client = CI360DataBase(self.config)

        async def test_async_context():
            async with client as ctx:
                self.assertEqual(ctx, client)
            mock_session.close.assert_called_once()

        asyncio.run(test_async_context())


class TestCI360DataErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = CI360DataConfig(
            host="https://api.example.com",
            secret_key="test-secret-key",
            tenant_id="test-tenant-id"
        )

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_connection_error_handling(self, mock_request, mock_encryption_class, mock_session_class):
        """Test connection error handling."""
        from sasci360soldata.base import CI360DataConnectionError
        mock_request.side_effect = CI360DataConnectionError("Connection failed")

        client = CI360DataBase(self.config)

        with self.assertRaises(CI360DataConnectionError):
            asyncio.run(client.get_customers_async())

    @patch('sasci360soldata.base.requests.Session')
    @patch('sasci360soldata.base.Encryption')
    @patch('sasci360soldata.base.CI360DataBase._make_request_async')
    def test_auth_error_handling(self, mock_request, mock_encryption_class, mock_session_class):
        """Test authentication error handling."""
        from sasci360soldata.base import CI360DataAuthError
        mock_request.side_effect = CI360DataAuthError("Authentication failed")

        client = CI360DataBase(self.config)

        with self.assertRaises(CI360DataAuthError):
            asyncio.run(client.get_customers_async())


if __name__ == '__main__':
    unittest.main()