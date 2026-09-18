#!/usr/bin/env python3
# Business Source License 1.1
#
# Parameters
#
# Licensor:             Nelson Grey LLC
# Licensed Work:        SAS CI360 Data Solution
# Additional Use Grant: None
# Change Date:          2029-12-13
# Change License:       Apache License 2.0
#
# Terms
#
# The Licensor hereby grants you the right to copy, modify, create derivative
# works, redistribute, and make non-production use of the Licensed Work. The
# Licensor may make an Additional Use Grant, above, permitting limited
# production use.
#
# Effective on the Change Date, or the fourth anniversary of the first publicly
# available distribution of a specific version of the Licensed Work under this
# License, whichever comes first, the Licensor hereby grants you rights under
# the terms of the Change License, and the rights granted in the paragraph
# above terminate.
#
# If your use of the Licensed Work does not comply with the requirements
# currently in effect as described in this License, you must purchase a
# commercial license from the Licensor, its affiliated entities, or authorized
# resellers, or you must refrain from using the Licensed Work.
#
# All copies of the original and modified Licensed Work, and derivative works
# of the Licensed Work, are subject to this License. This License applies
# separately for each version of the Licensed Work and the Change Date may vary
# for each version of the Licensed Work released by Licensor.
#
# You must conspicuously display this License on each original or modified copy
# of the Licensed Work. If you receive the Licensed Work in original or
# modified form from a third party, the terms and conditions set forth in this
# License apply to your use of that work.
#
# Any use of the Licensed Work in violation of this License will automatically
# terminate your rights under this License for the current and all other
# versions of the Licensed Work.
#
# This License does not grant you any right in any trademark or logo of
# Licensor or its affiliates (provided that you may use a trademark or logo of
# Licensor as expressly required by this License).
#
# TO THE EXTENT PERMITTED BY APPLICABLE LAW, THE LICENSED WORK IS PROVIDED ON
# AN "AS IS" BASIS. LICENSOR HEREBY DISCLAIMS ALL WARRANTIES AND CONDITIONS,
# EXPRESS OR IMPLIED, INCLUDING (WITHOUT LIMITATION) WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, AND
# TITLE.
#
# MariaDB hereby grants you permission to use this License's text to license
# your works, and to refer to it using the trademark "Business Source License",
# as long as you comply with the Covenants of Licensor below.
#
# Covenants of Licensor
#
# In consideration of the right to use this License's text and the "Business
# Source License" name and trademark, Licensor covenants to MariaDB, a Delaware
# corporation, for the benefit of MariaDB and any other party that has
# contributed to the Licensed Work, to use best efforts to provide the Change
# License on the Change Date for each version of the Licensed Work, and to
# designate the Change License as "Apache License 2.0" or a later version of
# the Apache License.

#
# Copyright (c) 2025 Nelson Grey LLC
# Author: Nelson Grey LLC
#
# Licensed under the Business Source License 1.1 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# https://github.com/mnelson3/sas-ci360-sol-data/blob/main/LICENSE
#
# -*- coding: utf-8 -*-
"""
SAS CI360 Data Module Base Class

Provides foundational functionality for SAS Customer Intelligence 360
data operations, including connection management, authentication, and
data processing capabilities.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from sasci360apicore.encryption import Encryption
except ImportError:  # pragma: no cover - optional dependency, only needed at runtime
    Encryption = None


@dataclass
class CI360DataConfig:
    """Configuration for CI360 Data operations."""

    algorithm: str = "HS256"
    api_base: str = "/marketingData"
    encoding: str = "utf-8"
    host: Optional[str] = None
    secret_key: Optional[str] = None
    tenant_id: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_backoff: float = 0.5
    enable_compression: bool = True


class CI360DataError(Exception):
    """Base exception for CI360 Data operations."""
    pass


class CI360DataAuthError(CI360DataError):
    """Authentication-related errors."""
    pass


class CI360DataConnectionError(CI360DataError):
    """Connection and network-related errors."""
    pass


class CI360DataValidationError(CI360DataError):
    """Data validation errors."""
    pass


class CI360DataBase:
    """
    Base class for SAS CI360 Data operations.

    Provides authentication, connection management, and common functionality
    for data-related API interactions with async support and robust error handling.
    """

    def __init__(self, config: Optional[CI360DataConfig] = None) -> None:
        """
        Initialize the CI360 Data base client.

        Args:
            config: Configuration object for CI360 Data operations

        Raises:
            CI360DataValidationError: If required configuration is missing
        """
        self.config = config or CI360DataConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Validate configuration
        self._validate_config()

        # Initialize HTTP session with retry strategy
        self.session = self._create_session()

        # Generate authentication token
        self.token = self._generate_token()

        # Connection state
        self._connected = False

        self.logger.info("CI360 Data Base initialized successfully")

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        required_fields = ['host', 'secret_key', 'tenant_id']
        missing = [field for field in required_fields if not getattr(self.config, field)]

        if missing:
            raise CI360DataValidationError(f"Missing required configuration: {', '.join(missing)}")

        # Validate algorithm
        supported_algorithms = ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
        if self.config.algorithm not in supported_algorithms:
            raise CI360DataValidationError(f"Unsupported algorithm: {self.config.algorithm}")

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _generate_token(self) -> str:
        """Generate JWT authentication token."""
        if Encryption is None:
            raise CI360DataAuthError(
                "sasci360apicore is required to generate authentication tokens"
            )

        try:
            encryption = Encryption(
                algorithm=self.config.algorithm,
                encoding=self.config.encoding
            )

            return encryption.generate_jwt(
                tenant_id=self.config.tenant_id,
                secret_key=self.config.secret_key
            )
        except Exception as e:
            raise CI360DataAuthError(f"Failed to generate authentication token: {e}")

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.

        Returns:
            Dict[str, str]: Headers dictionary with authorization token
        """
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Tenant-ID": str(self.config.tenant_id)
        }

    async def validate_connection_async(self) -> bool:
        """
        Asynchronously validate connection to CI360 service.

        Returns:
            bool: True if connection is valid
        """
        try:
            # Basic health check endpoint; config.host is validated non-None in __init__
            assert self.config.host is not None
            health_url = urljoin(self.config.host, "/health")
            headers = self.get_auth_headers()

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(
                    health_url,
                    headers=headers,
                    timeout=self.config.timeout
                )
            )

            self._connected = response.status_code == 200
            return self._connected

        except Exception as e:
            self.logger.error(f"Connection validation failed: {e}")
            self._connected = False
            return False

    def validate_connection(self) -> bool:
        """
        Validate connection to CI360 service.

        Returns:
            bool: True if connection is valid
        """
        try:
            # Run async validation in sync context
            return asyncio.run(self.validate_connection_async())
        except Exception as e:
            self.logger.error(f"Sync connection validation failed: {e}")
            return False

    async def _make_request_async(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make asynchronous HTTP request to CI360 API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Dict[str, Any]: Response data

        Raises:
            CI360DataConnectionError: For network/connection errors
            CI360DataAuthError: For authentication errors
        """
        if not self._connected:
            await self.validate_connection_async()
            if not self._connected:
                raise CI360DataConnectionError("No active connection to CI360 service")

        assert self.config.host is not None  # validated non-None in __init__
        url = urljoin(self.config.host + self.config.api_base, endpoint.lstrip('/'))
        headers = self.get_auth_headers()

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=self.config.timeout
                )
            )

            response.raise_for_status()
            return response.json() if response.content else {}

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise CI360DataAuthError(f"Authentication failed: {e}")
            elif response.status_code >= 500:
                raise CI360DataConnectionError(f"Server error: {e}")
            else:
                raise CI360DataError(f"API request failed: {e}")
        except requests.exceptions.RequestException as e:
            raise CI360DataConnectionError(f"Network error: {e}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make synchronous HTTP request to CI360 API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Dict[str, Any]: Response data
        """
        try:
            return asyncio.run(self._make_request_async(method, endpoint, data, params))
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            raise

    # Customer Data Management APIs

    async def get_customers_async(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve customer data asynchronously.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            filters: Optional filters for customer data

        Returns:
            Dict containing customer data and metadata
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        if filters:
            params.update(filters)

        return await self._make_request_async("GET", "/customers", params=params)

    def get_customers(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Retrieve customer data synchronously."""
        params = {
            "limit": limit,
            "offset": offset
        }
        if filters:
            params.update(filters)

        return self._make_request("GET", "/customers", params=params)

    async def get_customer_async(self, customer_id: str) -> Dict[str, Any]:
        """
        Retrieve specific customer data asynchronously.

        Args:
            customer_id: Unique customer identifier

        Returns:
            Dict containing customer data
        """
        return await self._make_request_async("GET", f"/customers/{customer_id}")

    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Retrieve specific customer data synchronously."""
        return self._make_request("GET", f"/customers/{customer_id}")

    async def create_customer_async(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new customer record asynchronously.

        Args:
            customer_data: Customer data to create

        Returns:
            Dict containing created customer data
        """
        return await self._make_request_async("POST", "/customers", data=customer_data)

    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new customer record synchronously."""
        return self._make_request("POST", "/customers", data=customer_data)

    async def update_customer_async(self, customer_id: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update customer record asynchronously.

        Args:
            customer_id: Unique customer identifier
            customer_data: Updated customer data

        Returns:
            Dict containing updated customer data
        """
        return await self._make_request_async("PUT", f"/customers/{customer_id}", data=customer_data)

    def update_customer(self, customer_id: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer record synchronously."""
        return self._make_request("PUT", f"/customers/{customer_id}", data=customer_data)

    async def delete_customer_async(self, customer_id: str) -> bool:
        """
        Delete customer record asynchronously.

        Args:
            customer_id: Unique customer identifier

        Returns:
            True if deletion successful
        """
        await self._make_request_async("DELETE", f"/customers/{customer_id}")
        return True

    def delete_customer(self, customer_id: str) -> bool:
        """Delete customer record synchronously."""
        self._make_request("DELETE", f"/customers/{customer_id}")
        return True

    # Segment Management APIs

    async def get_segments_async(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve customer segments asynchronously.

        Args:
            limit: Maximum number of segments to return
            offset: Number of segments to skip
            filters: Optional filters for segments

        Returns:
            Dict containing segment data and metadata
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        if filters:
            params.update(filters)

        return await self._make_request_async("GET", "/segments", params=params)

    def get_segments(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Retrieve customer segments synchronously."""
        params = {
            "limit": limit,
            "offset": offset
        }
        if filters:
            params.update(filters)

        return self._make_request("GET", "/segments", params=params)

    async def get_segment_async(self, segment_id: str) -> Dict[str, Any]:
        """
        Retrieve specific segment data asynchronously.

        Args:
            segment_id: Unique segment identifier

        Returns:
            Dict containing segment data
        """
        return await self._make_request_async("GET", f"/segments/{segment_id}")

    def get_segment(self, segment_id: str) -> Dict[str, Any]:
        """Retrieve specific segment data synchronously."""
        return self._make_request("GET", f"/segments/{segment_id}")

    async def create_segment_async(self, segment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new customer segment asynchronously.

        Args:
            segment_data: Segment definition data

        Returns:
            Dict containing created segment data
        """
        return await self._make_request_async("POST", "/segments", data=segment_data)

    def create_segment(self, segment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new customer segment synchronously."""
        return self._make_request("POST", "/segments", data=segment_data)

    async def update_segment_async(self, segment_id: str, segment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update segment definition asynchronously.

        Args:
            segment_id: Unique segment identifier
            segment_data: Updated segment data

        Returns:
            Dict containing updated segment data
        """
        return await self._make_request_async("PUT", f"/segments/{segment_id}", data=segment_data)

    def update_segment(self, segment_id: str, segment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update segment definition synchronously."""
        return self._make_request("PUT", f"/segments/{segment_id}", data=segment_data)

    async def delete_segment_async(self, segment_id: str) -> bool:
        """
        Delete customer segment asynchronously.

        Args:
            segment_id: Unique segment identifier

        Returns:
            True if deletion successful
        """
        await self._make_request_async("DELETE", f"/segments/{segment_id}")
        return True

    def delete_segment(self, segment_id: str) -> bool:
        """Delete customer segment synchronously."""
        self._make_request("DELETE", f"/segments/{segment_id}")
        return True

    # Data Import/Export APIs

    async def import_data_async(self, data: List[Dict[str, Any]], data_type: str = "customers") -> Dict[str, Any]:
        """
        Import bulk data asynchronously.

        Args:
            data: List of data records to import
            data_type: Type of data being imported (customers, events, etc.)

        Returns:
            Dict containing import results and status
        """
        payload = {
            "data": data,
            "dataType": data_type
        }
        return await self._make_request_async("POST", "/import", data=payload)

    def import_data(self, data: List[Dict[str, Any]], data_type: str = "customers") -> Dict[str, Any]:
        """Import bulk data synchronously."""
        payload = {
            "data": data,
            "dataType": data_type
        }
        return self._make_request("POST", "/import", data=payload)

    async def export_data_async(
        self,
        data_type: str = "customers",
        filters: Optional[Dict[str, Any]] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export data asynchronously.

        Args:
            data_type: Type of data to export
            filters: Optional filters for export
            format: Export format (json, csv, etc.)

        Returns:
            Dict containing export data or job status
        """
        params = {
            "dataType": data_type,
            "format": format
        }
        if filters:
            params.update(filters)

        return await self._make_request_async("GET", "/export", params=params)

    def export_data(
        self,
        data_type: str = "customers",
        filters: Optional[Dict[str, Any]] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export data synchronously."""
        params = {
            "dataType": data_type,
            "format": format
        }
        if filters:
            params.update(filters)

        return self._make_request("GET", "/export", params=params)

    # Data Validation APIs

    async def validate_data_async(self, data: List[Dict[str, Any]], data_type: str = "customers") -> Dict[str, Any]:
        """
        Validate data records asynchronously.

        Args:
            data: List of data records to validate
            data_type: Type of data being validated

        Returns:
            Dict containing validation results
        """
        payload = {
            "data": data,
            "dataType": data_type
        }
        return await self._make_request_async("POST", "/validate", data=payload)

    def validate_data(self, data: List[Dict[str, Any]], data_type: str = "customers") -> Dict[str, Any]:
        """Validate data records synchronously."""
        payload = {
            "data": data,
            "dataType": data_type
        }
        return self._make_request("POST", "/validate", data=payload)

    # Schema Management APIs

    async def get_schema_async(self, data_type: str = "customers") -> Dict[str, Any]:
        """
        Retrieve data schema asynchronously.

        Args:
            data_type: Type of data schema to retrieve

        Returns:
            Dict containing schema definition
        """
        params = {"dataType": data_type}
        return await self._make_request_async("GET", "/schema", params=params)

    def get_schema(self, data_type: str = "customers") -> Dict[str, Any]:
        """Retrieve data schema synchronously."""
        params = {"dataType": data_type}
        return self._make_request("GET", "/schema", params=params)

    async def update_schema_async(self, data_type: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update data schema asynchronously.

        Args:
            data_type: Type of data schema to update
            schema: New schema definition

        Returns:
            Dict containing updated schema
        """
        payload = {
            "dataType": data_type,
            "schema": schema
        }
        return await self._make_request_async("PUT", "/schema", data=payload)

    def update_schema(self, data_type: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Update data schema synchronously."""
        payload = {
            "dataType": data_type,
            "schema": schema
        }
        return self._make_request("PUT", "/schema", data=payload)

    def __enter__(self):
        """Context manager entry."""
        if not self.validate_connection():
            raise CI360DataConnectionError("Failed to establish connection")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        if not await self.validate_connection_async():
            raise CI360DataConnectionError("Failed to establish connection")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.session.close()
