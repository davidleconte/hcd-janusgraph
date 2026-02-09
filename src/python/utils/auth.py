"""
Authentication Utilities
Shared authentication helpers for consistent credential handling

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Created: 2026-01-28
Phase: Week 1 Remediation - Security Hardening
"""

import os
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def get_credentials(
    username: Optional[str] = None,
    password: Optional[str] = None,
    username_env_var: str = 'USERNAME',
    password_env_var: str = 'PASSWORD',
    service_name: str = 'Service'
) -> Tuple[str, str]:
    """
    Get authentication credentials from parameters or environment variables.
    
    This function provides a consistent way to handle authentication across
    different clients (JanusGraph, OpenSearch, etc.).
    
    Args:
        username: Username (if None, reads from environment)
        password: Password (if None, reads from environment)
        username_env_var: Environment variable name for username
        password_env_var: Environment variable name for password
        service_name: Service name for error messages
    
    Returns:
        Tuple of (username, password)
    
    Raises:
        ValueError: If credentials are not provided
    
    Example:
        >>> username, password = get_credentials(
        ...     username_env_var='JANUSGRAPH_USERNAME',
        ...     password_env_var='JANUSGRAPH_PASSWORD',
        ...     service_name='JanusGraph'
        ... )
    """
    # Get credentials from environment if not provided
    if not username:
        username = os.getenv(username_env_var)
    if not password:
        password = os.getenv(password_env_var)
    
    # Require authentication
    if not username or not password:
        raise ValueError(
            f"{service_name} authentication required: username and password must be provided. "
            f"Set {username_env_var} and {password_env_var} environment variables "
            f"or pass credentials to constructor."
        )
    
    logger.debug(
        "%s authentication configured for user: %s",
        service_name,
        username
    )
    
    return username, password


def validate_ssl_config(
    use_ssl: bool,
    verify_certs: bool,
    ca_certs: Optional[str] = None
) -> None:
    """
    Validate SSL/TLS configuration and log warnings.
    
    Args:
        use_ssl: Whether SSL is enabled
        verify_certs: Whether to verify certificates
        ca_certs: Path to CA certificate bundle
    
    Raises:
        ValueError: If configuration is invalid
    """
    if not use_ssl and verify_certs:
        raise ValueError(
            "Cannot verify certificates when SSL is disabled. "
            "Set use_ssl=True or verify_certs=False."
        )
    
    if use_ssl and not verify_certs:
        logger.warning(
            "SSL certificate verification disabled. "
            "This is not recommended for production environments."
        )
    
    if ca_certs and not use_ssl:
        logger.warning(
            "CA certificates provided but SSL is disabled. "
            "CA certificates will be ignored."
        )


__all__ = [
    'get_credentials',
    'validate_ssl_config',
]
