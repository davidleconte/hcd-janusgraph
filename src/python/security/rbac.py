"""
Enhanced Role-Based Access Control (RBAC) Module

Provides comprehensive RBAC with hierarchical roles, permissions,
resource-level access control, and dynamic policy evaluation.
"""

import logging
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


class Permission(Enum):
    """System permissions."""
    # Read permissions
    READ = "read"
    READ_OWN = "read_own"
    READ_ALL = "read_all"
    
    # Write permissions
    WRITE = "write"
    WRITE_OWN = "write_own"
    WRITE_ALL = "write_all"
    
    # Delete permissions
    DELETE = "delete"
    DELETE_OWN = "delete_own"
    DELETE_ALL = "delete_all"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_PERMISSIONS = "manage_permissions"
    MANAGE_SCHEMA = "manage_schema"
    
    # Query permissions
    QUERY = "query"
    QUERY_ADVANCED = "query_advanced"
    QUERY_ADMIN = "query_admin"
    
    # System permissions
    VIEW_LOGS = "view_logs"
    VIEW_METRICS = "view_metrics"
    MANAGE_SYSTEM = "manage_system"
    
    # Deployment permissions
    DEPLOY_DEV = "deploy_dev"
    DEPLOY_STAGING = "deploy_staging"
    DEPLOY_PRODUCTION = "deploy_production"
    
    # Audit permissions
    VIEW_AUDIT_LOGS = "view_audit_logs"
    EXPORT_DATA = "export_data"


class ResourceType(Enum):
    """Resource types for access control."""
    VERTEX = "vertex"
    EDGE = "edge"
    GRAPH = "graph"
    SCHEMA = "schema"
    USER = "user"
    ROLE = "role"
    SYSTEM = "system"
    AUDIT_LOG = "audit_log"


@dataclass
class Role:
    """Role definition with permissions and hierarchy."""
    name: str
    description: str
    permissions: Set[Permission] = field(default_factory=set)
    inherits_from: List[str] = field(default_factory=list)
    resource_restrictions: Dict[ResourceType, List[str]] = field(default_factory=dict)
    conditions: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_permission(self, permission: Permission):
        """Add permission to role."""
        self.permissions.add(permission)
        self.updated_at = datetime.now(timezone.utc)
    
    def remove_permission(self, permission: Permission):
        """Remove permission from role."""
        self.permissions.discard(permission)
        self.updated_at = datetime.now(timezone.utc)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has permission."""
        return permission in self.permissions


@dataclass
class User:
    """User with roles and attributes."""
    user_id: str
    username: str
    email: str
    roles: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    mfa_enabled: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    
    def add_role(self, role_name: str):
        """Add role to user."""
        if role_name not in self.roles:
            self.roles.append(role_name)
    
    def remove_role(self, role_name: str):
        """Remove role from user."""
        if role_name in self.roles:
            self.roles.remove(role_name)
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has role."""
        return role_name in self.roles


@dataclass
class AccessRequest:
    """Access control request."""
    user: User
    resource_type: ResourceType
    resource_id: Optional[str]
    action: Permission
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AccessDecision:
    """Access control decision."""
    allowed: bool
    reason: str
    evaluated_policies: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RBACManager:
    """Manages role-based access control."""
    
    def __init__(self):
        """Initialize RBAC manager."""
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}
        self._initialize_default_roles()
        logger.info("RBAC Manager initialized")
    
    def _initialize_default_roles(self):
        """Initialize default system roles."""
        # Admin role - full access
        admin = Role(
            name="admin",
            description="System administrator with full access",
            permissions={
                Permission.READ_ALL,
                Permission.WRITE_ALL,
                Permission.DELETE_ALL,
                Permission.MANAGE_USERS,
                Permission.MANAGE_ROLES,
                Permission.MANAGE_PERMISSIONS,
                Permission.MANAGE_SCHEMA,
                Permission.QUERY_ADMIN,
                Permission.VIEW_LOGS,
                Permission.VIEW_METRICS,
                Permission.MANAGE_SYSTEM,
                Permission.DEPLOY_PRODUCTION,
                Permission.VIEW_AUDIT_LOGS,
                Permission.EXPORT_DATA
            }
        )
        
        # Developer role
        developer = Role(
            name="developer",
            description="Developer with read/write access",
            permissions={
                Permission.READ_ALL,
                Permission.WRITE_ALL,
                Permission.DELETE_OWN,
                Permission.QUERY_ADVANCED,
                Permission.VIEW_LOGS,
                Permission.VIEW_METRICS,
                Permission.DEPLOY_DEV,
                Permission.DEPLOY_STAGING
            }
        )
        
        # Analyst role
        analyst = Role(
            name="analyst",
            description="Data analyst with read and query access",
            permissions={
                Permission.READ_ALL,
                Permission.QUERY,
                Permission.QUERY_ADVANCED,
                Permission.VIEW_METRICS,
                Permission.EXPORT_DATA
            }
        )
        
        # User role
        user = Role(
            name="user",
            description="Standard user with limited access",
            permissions={
                Permission.READ_OWN,
                Permission.WRITE_OWN,
                Permission.DELETE_OWN,
                Permission.QUERY
            }
        )
        
        # Auditor role
        auditor = Role(
            name="auditor",
            description="Auditor with read-only access to audit logs",
            permissions={
                Permission.READ_ALL,
                Permission.VIEW_AUDIT_LOGS,
                Permission.VIEW_LOGS,
                Permission.VIEW_METRICS
            }
        )
        
        # Register roles
        self.register_role(admin)
        self.register_role(developer)
        self.register_role(analyst)
        self.register_role(user)
        self.register_role(auditor)
        
        logger.info("Default roles initialized")
    
    def register_role(self, role: Role):
        """
        Register a new role.
        
        Args:
            role: Role to register
        """
        self.roles[role.name] = role
        logger.info("Role registered: %s", role.name)
    
    def get_role(self, role_name: str) -> Optional[Role]:
        """
        Get role by name.
        
        Args:
            role_name: Name of role
        
        Returns:
            Role object or None
        """
        return self.roles.get(role_name)
    
    def register_user(self, user: User):
        """
        Register a new user.
        
        Args:
            user: User to register
        """
        self.users[user.user_id] = user
        logger.info("User registered: %s", user.user_id)
    
    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User identifier
        
        Returns:
            User object or None
        """
        return self.users.get(user_id)
    
    def assign_role(self, user_id: str, role_name: str):
        """
        Assign role to user.
        
        Args:
            user_id: User identifier
            role_name: Role name
        """
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        role = self.get_role(role_name)
        if not role:
            raise ValueError(f"Role not found: {role_name}")
        
        user.add_role(role_name)
        logger.info("Role %s assigned to user %s", role_name, user_id)
    
    def revoke_role(self, user_id: str, role_name: str):
        """
        Revoke role from user.
        
        Args:
            user_id: User identifier
            role_name: Role name
        """
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        user.remove_role(role_name)
        logger.info("Role %s revoked from user %s", role_name, user_id)
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """
        Get all permissions for a user (including inherited).
        
        Args:
            user_id: User identifier
        
        Returns:
            Set of permissions
        """
        user = self.get_user(user_id)
        if not user:
            return set()
        
        permissions = set()
        
        for role_name in user.roles:
            role = self.get_role(role_name)
            if role:
                # Add direct permissions
                permissions.update(role.permissions)
                
                # Add inherited permissions
                permissions.update(self._get_inherited_permissions(role))
        
        return permissions
    
    def _get_inherited_permissions(self, role: Role) -> Set[Permission]:
        """
        Get inherited permissions from parent roles.
        
        Args:
            role: Role to get inherited permissions for
        
        Returns:
            Set of inherited permissions
        """
        inherited = set()
        
        for parent_name in role.inherits_from:
            parent = self.get_role(parent_name)
            if parent:
                inherited.update(parent.permissions)
                inherited.update(self._get_inherited_permissions(parent))
        
        return inherited
    
    def check_permission(
        self,
        user_id: str,
        permission: Permission,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[str] = None
    ) -> bool:
        """
        Check if user has permission.
        
        Args:
            user_id: User identifier
            permission: Permission to check
            resource_type: Optional resource type
            resource_id: Optional resource identifier
        
        Returns:
            True if user has permission, False otherwise
        """
        user = self.get_user(user_id)
        if not user:
            logger.warning("Permission check failed: user not found %s", user_id)
            return False
        
        user_permissions = self.get_user_permissions(user_id)
        
        # Check if user has the permission
        if permission not in user_permissions:
            logger.debug("User %s does not have permission %s", user_id, permission.value)
            return False
        
        # Check resource-level restrictions
        if resource_type and resource_id:
            if not self._check_resource_access(user, resource_type, resource_id):
                logger.debug("User %s denied access to resource %s:%s", user_id, resource_type.value, resource_id)
                return False
        
        logger.debug("User %s granted permission %s", user_id, permission.value)
        return True
    
    def _check_resource_access(
        self,
        user: User,
        resource_type: ResourceType,
        resource_id: str
    ) -> bool:
        """
        Check resource-level access restrictions.
        
        Args:
            user: User object
            resource_type: Resource type
            resource_id: Resource identifier
        
        Returns:
            True if access allowed, False otherwise
        """
        # Check each role's resource restrictions
        for role_name in user.roles:
            role = self.get_role(role_name)
            if not role:
                continue
            
            # If role has no restrictions for this resource type, allow
            if resource_type not in role.resource_restrictions:
                return True
            
            # Check if resource is in allowed list
            allowed_resources = role.resource_restrictions[resource_type]
            if '*' in allowed_resources or resource_id in allowed_resources:
                return True
        
        return False
    
    def evaluate_access(self, request: AccessRequest) -> AccessDecision:
        """
        Evaluate access request with detailed decision.
        
        Args:
            request: Access request
        
        Returns:
            Access decision
        """
        evaluated_policies = []
        
        # Check if user exists
        if not self.get_user(request.user.user_id):
            return AccessDecision(
                allowed=False,
                reason="User not found",
                evaluated_policies=evaluated_policies
            )
        
        # Check permission
        has_permission = self.check_permission(
            request.user.user_id,
            request.action,
            request.resource_type,
            request.resource_id
        )
        
        evaluated_policies.append(f"permission_check:{request.action.value}")
        
        if not has_permission:
            return AccessDecision(
                allowed=False,
                reason=f"User lacks permission: {request.action.value}",
                evaluated_policies=evaluated_policies
            )
        
        # Check context-based conditions
        if not self._evaluate_conditions(request):
            return AccessDecision(
                allowed=False,
                reason="Context conditions not met",
                evaluated_policies=evaluated_policies
            )
        
        evaluated_policies.append("context_check:passed")
        
        return AccessDecision(
            allowed=True,
            reason="Access granted",
            evaluated_policies=evaluated_policies
        )
    
    def _evaluate_conditions(self, request: AccessRequest) -> bool:
        """
        Evaluate context-based conditions.
        
        Args:
            request: Access request
        
        Returns:
            True if conditions met, False otherwise
        """
        # Example conditions:
        # - Time-based access
        # - IP-based access
        # - MFA requirement
        # - Resource ownership
        
        # Check MFA requirement for sensitive operations
        sensitive_permissions = {
            Permission.DELETE_ALL,
            Permission.MANAGE_USERS,
            Permission.MANAGE_SYSTEM,
            Permission.DEPLOY_PRODUCTION
        }
        
        if request.action in sensitive_permissions:
            if not request.user.mfa_enabled:
                logger.warning("MFA required for %s", request.action.value)
                return False
            
            if not request.context.get('mfa_verified', False):
                logger.warning("MFA not verified for %s", request.action.value)
                return False
        
        # Check time-based restrictions
        if 'allowed_hours' in request.context:
            current_hour = datetime.now(timezone.utc).hour
            allowed_hours = request.context['allowed_hours']
            if current_hour not in allowed_hours:
                logger.warning("Access denied: outside allowed hours")
                return False
        
        # Check IP-based restrictions
        if 'allowed_ips' in request.context:
            client_ip = request.context.get('client_ip')
            allowed_ips = request.context['allowed_ips']
            if client_ip not in allowed_ips:
                logger.warning("Access denied: IP not allowed %s", client_ip)
                return False
        
        return True
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """
        Get list of roles for user.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of role names
        """
        user = self.get_user(user_id)
        return user.roles if user else []
    
    def export_policy(self) -> str:
        """
        Export RBAC policy as JSON.
        
        Returns:
            JSON string of policy
        """
        policy = {
            'roles': {
                name: {
                    'description': role.description,
                    'permissions': [p.value for p in role.permissions],
                    'inherits_from': role.inherits_from
                }
                for name, role in self.roles.items()
            },
            'users': {
                user_id: {
                    'username': user.username,
                    'email': user.email,
                    'roles': user.roles,
                    'mfa_enabled': user.mfa_enabled
                }
                for user_id, user in self.users.items()
            }
        }
        
        return json.dumps(policy, indent=2)
    
    def import_policy(self, policy_json: str):
        """
        Import RBAC policy from JSON.
        
        Args:
            policy_json: JSON string of policy
        """
        policy = json.loads(policy_json)
        
        # Import roles
        for role_name, role_data in policy.get('roles', {}).items():
            role = Role(
                name=role_name,
                description=role_data['description'],
                permissions={Permission(p) for p in role_data['permissions']},
                inherits_from=role_data.get('inherits_from', [])
            )
            self.register_role(role)
        
        # Import users
        for user_id, user_data in policy.get('users', {}).items():
            user = User(
                user_id=user_id,
                username=user_data['username'],
                email=user_data['email'],
                roles=user_data['roles'],
                mfa_enabled=user_data.get('mfa_enabled', False)
            )
            self.register_user(user)
        
        logger.info("RBAC policy imported successfully")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize RBAC manager
    rbac = RBACManager()
    
    # Create and register user
    user = User(
        user_id="user123",
        username="john_doe",
        email="john@example.com",
        mfa_enabled=True
    )
    rbac.register_user(user)
    
    # Assign roles
    rbac.assign_role("user123", "developer")
    
    # Check permissions
    can_read = rbac.check_permission("user123", Permission.READ_ALL)
    can_deploy_prod = rbac.check_permission("user123", Permission.DEPLOY_PRODUCTION)
    
    print(f"Can read: {can_read}")
    print(f"Can deploy to production: {can_deploy_prod}")
    
    # Evaluate access request
    request = AccessRequest(
        user=user,
        resource_type=ResourceType.VERTEX,
        resource_id="vertex123",
        action=Permission.WRITE_ALL,
        context={'mfa_verified': True}
    )
    
    decision = rbac.evaluate_access(request)
    print(f"Access decision: {decision.allowed} - {decision.reason}")
    
    # Export policy
    policy_json = rbac.export_policy()
    print(f"Policy exported: {len(policy_json)} bytes")

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
