"""
Analytics Package
=================

Graph analytics modules for fraud detection, AML compliance, and UBO discovery.

Modules:
- ubo_discovery: Ultimate Beneficial Owner discovery through ownership chains
"""

from .ubo_discovery import UBODiscovery, UBOResult, discover_ubos, OwnershipType, OwnershipLink

__all__ = [
    'UBODiscovery',
    'UBOResult', 
    'discover_ubos',
    'OwnershipType',
    'OwnershipLink'
]
