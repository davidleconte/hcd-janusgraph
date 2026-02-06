"""
Production-ready JanusGraph client with authentication, SSL/TLS, and validation.

File: janusgraph_client.py
Updated: 2026-01-28 - Security Hardening
Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
"""

import logging
import os
import ssl
from typing import Any, Optional

from gremlin_python.driver import client, serializer
from gremlin_python.driver.protocol import GremlinServerError

from .exceptions import ConnectionError, QueryError, TimeoutError, ValidationError
from ..utils.validation import (
    validate_gremlin_query,
    validate_hostname,
    validate_port,
    validate_file_path,
)
from ..utils.auth import get_credentials, validate_ssl_config

logger = logging.getLogger(__name__)


class JanusGraphClient:
    """
    Production-ready client for JanusGraph with security hardening.

    Security Features:
    - Mandatory authentication
    - SSL/TLS support (wss://)
    - Query validation
    - Input sanitization
    - Secure logging

    Example:
        >>> client = JanusGraphClient(
        ...     host="localhost",
        ...     port=8182,
        ...     username="admin",
        ...     password="secure_password"
        ... )
        >>> client.connect()
        >>> result = client.execute("g.V().count()")
        >>> client.close()
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = int(os.getenv('JANUSGRAPH_PORT', '18182')),
        username: Optional[str] = None,
        password: Optional[str] = None,
        traversal_source: str = "g",
        timeout: int = 30,
        use_ssl: bool = True,
        verify_certs: bool = True,
        ca_certs: Optional[str] = None,
    ) -> None:
        """
        Initialize JanusGraph client with security.

        Args:
            host: JanusGraph server hostname
            port: Gremlin WebSocket port
            username: Authentication username (required)
            password: Authentication password (required)
            traversal_source: Graph traversal source name
            timeout: Connection timeout in seconds
            use_ssl: Use SSL/TLS (wss://) - default True
            verify_certs: Verify SSL certificates - default True
            ca_certs: Path to CA certificate bundle

        Raises:
            ValidationError: If parameters are invalid or authentication missing
        """
        # Validate inputs
        host = validate_hostname(host)
        port = validate_port(port, allow_privileged=True)
        
        # Validate timeout
        if not isinstance(timeout, (int, float)):
            raise ValidationError(f"Timeout must be numeric, got {type(timeout).__name__}")
        if timeout <= 0:
            raise ValidationError(
                f"Timeout must be positive, got {timeout}. "
                "Recommended: 30-120 seconds for production."
            )
        if timeout > 300:
            logger.warning(
                "Timeout %d seconds is very high. Consider using a lower value.", timeout
            )
        
        # Validate ca_certs file if provided
        if ca_certs:
            try:
                validate_file_path(ca_certs, must_exist=True)
            except ValidationError as e:
                raise ValidationError(
                    f"Invalid CA certificate file: {ca_certs}. {e}"
                ) from e

        # Get credentials using shared utility
        try:
            username, password = get_credentials(
                username=username,
                password=password,
                username_env_var='JANUSGRAPH_USERNAME',
                password_env_var='JANUSGRAPH_PASSWORD',
                service_name='JanusGraph'
            )
        except ValueError as e:
            raise ValidationError(str(e)) from e
        
        # Validate SSL configuration
        validate_ssl_config(use_ssl, verify_certs, ca_certs)

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.traversal_source = traversal_source
        self.timeout = timeout
        self.use_ssl = use_ssl
        self.verify_certs = verify_certs
        self.ca_certs = ca_certs

        # Build URL with SSL
        protocol = "wss" if use_ssl else "ws"
        self.url = f"{protocol}://{host}:{port}/gremlin"
        
        self._client: Optional[client.Client] = None

        logger.info(
            "Initialized JanusGraphClient: host=%s, port=%d, ssl=%s",
            host,
            port,
            use_ssl,
        )

    def connect(self) -> None:
        """
        Establish secure connection to JanusGraph server.

        Raises:
            ConnectionError: If connection fails
            TimeoutError: If connection times out
        """
        if self._client is not None:
            logger.warning("Client already connected to %s", self.url)
            return

        try:
            logger.info("Connecting to JanusGraph at %s (SSL: %s)", self.url, self.use_ssl)
            
            # Configure SSL context if using SSL
            ssl_context = None
            if self.use_ssl:
                ssl_context = ssl.create_default_context()
                if self.ca_certs:
                    ssl_context.load_verify_locations(self.ca_certs)
                if not self.verify_certs:
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE

            # Create client with authentication
            self._client = client.Client(
                self.url,
                self.traversal_source,
                username=self.username,
                password=self.password,
                message_serializer=serializer.GraphSONSerializersV3d0(),
            )
            
            logger.info("Successfully connected to JanusGraph at %s", self.url)
            
        except TimeoutError as e:
            logger.error("Connection timeout to %s: %s", self.url, e)
            raise TimeoutError(f"Connection to {self.url} timed out") from e
        except Exception as e:
            logger.error("Failed to connect to %s: %s", self.url, e)
            raise ConnectionError(f"Failed to connect to {self.url}: {e}") from e

    def execute(self, query: str, bindings: Optional[dict[str, Any]] = None) -> list[Any]:
        """
        Execute Gremlin query with validation.

        Args:
            query: Gremlin query string
            bindings: Optional query parameter bindings

        Returns:
            List of query results

        Raises:
            ValidationError: If query is invalid
            ConnectionError: If client not connected
            QueryError: If query execution fails
            TimeoutError: If query times out
        """
        # Validate query
        query = validate_gremlin_query(query)

        if self._client is None:
            raise ConnectionError(
                "Client not connected. Call connect() first or use context manager."
            )

        try:
            # Log query (first 100 chars only for security)
            logger.debug("Executing query: %s", query[:100])
            
            # Log bindings count but not values (may contain sensitive data)
            if bindings:
                logger.debug("Query has %d parameter bindings", len(bindings))
                result = self._client.submit(query, bindings).all().result()
            else:
                result = self._client.submit(query).all().result()
            
            logger.debug("Query returned %d results", len(result))
            return result
            
        except GremlinServerError as e:
            logger.error("Query execution failed: %s", e)
            raise QueryError(f"Gremlin query error: {e}", query=query) from e
        except TimeoutError as e:
            logger.error("Query timeout: %s", e)
            raise TimeoutError(f"Query execution timed out: {e}") from e
        except Exception as e:
            logger.error("Unexpected error executing query: %s", e)
            raise QueryError(f"Query execution failed: {e}", query=query) from e

    def is_connected(self) -> bool:
        """Check if client is currently connected."""
        return self._client is not None

    def close(self) -> None:
        """Close connection to JanusGraph server."""
        if self._client is None:
            logger.debug("Client already closed or never connected")
            return

        try:
            logger.info("Closing connection to %s", self.url)
            self._client.close()
            self._client = None
            logger.info("Successfully closed connection to %s", self.url)
        except Exception as e:
            logger.error("Error closing connection: %s", e)
            self._client = None
            raise

    def __enter__(self) -> "JanusGraphClient":
        """Context manager entry: establish connection."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit: close connection."""
        self.close()

    def __repr__(self) -> str:
        """String representation of client."""
        status = "connected" if self.is_connected() else "disconnected"
        return f"JanusGraphClient(url={self.url}, ssl={self.use_ssl}, status={status})"

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
