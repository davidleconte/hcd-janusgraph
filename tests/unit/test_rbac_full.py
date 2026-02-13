"""Comprehensive tests for src.python.security.rbac — targets 42% → 90%+."""
import json
import pytest

from src.python.security.rbac import (
    Permission,
    ResourceType,
    Role,
    User,
    AccessRequest,
    AccessDecision,
    RBACManager,
)


class TestPermissionEnum:
    def test_all_values(self):
        assert Permission.READ.value == "read"
        assert Permission.MANAGE_SYSTEM.value == "manage_system"
        assert Permission.DEPLOY_PRODUCTION.value == "deploy_production"
        assert Permission.EXPORT_DATA.value == "export_data"


class TestResourceTypeEnum:
    def test_all_values(self):
        assert ResourceType.VERTEX.value == "vertex"
        assert ResourceType.AUDIT_LOG.value == "audit_log"


class TestRole:
    def test_add_remove_permission(self):
        r = Role(name="test", description="test role")
        r.add_permission(Permission.READ)
        assert r.has_permission(Permission.READ)
        r.remove_permission(Permission.READ)
        assert not r.has_permission(Permission.READ)

    def test_remove_nonexistent_permission(self):
        r = Role(name="test", description="test role")
        r.remove_permission(Permission.READ)

    def test_updated_at_changes(self):
        r = Role(name="test", description="test role")
        t1 = r.updated_at
        r.add_permission(Permission.READ)
        assert r.updated_at >= t1


class TestUser:
    def test_add_remove_role(self):
        u = User(user_id="u1", username="alice", email="a@b.com")
        u.add_role("admin")
        assert u.has_role("admin")
        u.add_role("admin")
        assert u.roles.count("admin") == 1
        u.remove_role("admin")
        assert not u.has_role("admin")

    def test_remove_nonexistent_role(self):
        u = User(user_id="u1", username="alice", email="a@b.com")
        u.remove_role("nope")


class TestRBACManager:
    def setup_method(self):
        self.mgr = RBACManager()

    def test_default_roles(self):
        assert self.mgr.get_role("admin") is not None
        assert self.mgr.get_role("developer") is not None
        assert self.mgr.get_role("analyst") is not None
        assert self.mgr.get_role("user") is not None
        assert self.mgr.get_role("auditor") is not None

    def test_register_and_get_user(self):
        u = User(user_id="u1", username="alice", email="a@b.com")
        self.mgr.register_user(u)
        assert self.mgr.get_user("u1") is u
        assert self.mgr.get_user("nope") is None

    def test_assign_role(self):
        u = User(user_id="u1", username="alice", email="a@b.com")
        self.mgr.register_user(u)
        self.mgr.assign_role("u1", "admin")
        assert "admin" in u.roles

    def test_assign_role_user_not_found(self):
        with pytest.raises(ValueError, match="User not found"):
            self.mgr.assign_role("nope", "admin")

    def test_assign_role_role_not_found(self):
        u = User(user_id="u1", username="alice", email="a@b.com")
        self.mgr.register_user(u)
        with pytest.raises(ValueError, match="Role not found"):
            self.mgr.assign_role("u1", "nonexistent")

    def test_revoke_role(self):
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["admin"])
        self.mgr.register_user(u)
        self.mgr.revoke_role("u1", "admin")
        assert "admin" not in u.roles

    def test_revoke_role_user_not_found(self):
        with pytest.raises(ValueError, match="User not found"):
            self.mgr.revoke_role("nope", "admin")

    def test_get_user_permissions(self):
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["admin"])
        self.mgr.register_user(u)
        perms = self.mgr.get_user_permissions("u1")
        assert Permission.MANAGE_SYSTEM in perms

    def test_get_user_permissions_unknown(self):
        assert self.mgr.get_user_permissions("nope") == set()

    def test_inherited_permissions(self):
        parent = Role(name="parent", description="p", permissions={Permission.READ})
        child = Role(name="child", description="c", inherits_from=["parent"])
        self.mgr.register_role(parent)
        self.mgr.register_role(child)
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["child"])
        self.mgr.register_user(u)
        perms = self.mgr.get_user_permissions("u1")
        assert Permission.READ in perms

    def test_check_permission_true(self):
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["admin"])
        self.mgr.register_user(u)
        assert self.mgr.check_permission("u1", Permission.MANAGE_SYSTEM)

    def test_check_permission_false(self):
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["user"])
        self.mgr.register_user(u)
        assert not self.mgr.check_permission("u1", Permission.MANAGE_SYSTEM)

    def test_check_permission_unknown_user(self):
        assert not self.mgr.check_permission("nope", Permission.READ)

    def test_check_permission_with_resource(self):
        role = Role(
            name="restricted",
            description="r",
            permissions={Permission.READ},
            resource_restrictions={ResourceType.VERTEX: ["v-1"]},
        )
        self.mgr.register_role(role)
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["restricted"])
        self.mgr.register_user(u)
        assert self.mgr.check_permission("u1", Permission.READ, ResourceType.VERTEX, "v-1")
        assert not self.mgr.check_permission("u1", Permission.READ, ResourceType.VERTEX, "v-2")

    def test_check_permission_wildcard_resource(self):
        role = Role(
            name="wildcard",
            description="w",
            permissions={Permission.READ},
            resource_restrictions={ResourceType.VERTEX: ["*"]},
        )
        self.mgr.register_role(role)
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["wildcard"])
        self.mgr.register_user(u)
        assert self.mgr.check_permission("u1", Permission.READ, ResourceType.VERTEX, "anything")

    def test_evaluate_access_granted(self):
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["analyst"])
        self.mgr.register_user(u)
        req = AccessRequest(user=u, resource_type=ResourceType.VERTEX, resource_id="v-1", action=Permission.READ_ALL)
        decision = self.mgr.evaluate_access(req)
        assert decision.allowed
        assert "Access granted" in decision.reason

    def test_evaluate_access_user_not_found(self):
        u = User(user_id="ghost", username="ghost", email="g@b.com")
        req = AccessRequest(user=u, resource_type=ResourceType.VERTEX, resource_id="v-1", action=Permission.READ)
        decision = self.mgr.evaluate_access(req)
        assert not decision.allowed
        assert "User not found" in decision.reason

    def test_evaluate_access_denied(self):
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["user"])
        self.mgr.register_user(u)
        req = AccessRequest(user=u, resource_type=ResourceType.SYSTEM, resource_id=None, action=Permission.MANAGE_SYSTEM)
        decision = self.mgr.evaluate_access(req)
        assert not decision.allowed

    def test_evaluate_access_mfa_required(self):
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["admin"], mfa_enabled=False)
        self.mgr.register_user(u)
        req = AccessRequest(
            user=u,
            resource_type=ResourceType.SYSTEM,
            resource_id=None,
            action=Permission.MANAGE_SYSTEM,
        )
        decision = self.mgr.evaluate_access(req)
        assert not decision.allowed
        assert "conditions" in decision.reason.lower() or "Context" in decision.reason

    def test_evaluate_access_mfa_verified(self):
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["admin"], mfa_enabled=True)
        self.mgr.register_user(u)
        req = AccessRequest(
            user=u,
            resource_type=ResourceType.SYSTEM,
            resource_id=None,
            action=Permission.MANAGE_SYSTEM,
            context={"mfa_verified": True},
        )
        decision = self.mgr.evaluate_access(req)
        assert decision.allowed

    def test_evaluate_conditions_ip_restriction(self):
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["analyst"])
        self.mgr.register_user(u)
        req = AccessRequest(
            user=u,
            resource_type=ResourceType.VERTEX,
            resource_id="v-1",
            action=Permission.READ_ALL,
            context={"allowed_ips": ["10.0.0.1"], "client_ip": "192.168.1.1"},
        )
        decision = self.mgr.evaluate_access(req)
        assert not decision.allowed

    def test_evaluate_conditions_hours_restriction(self):
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["analyst"])
        self.mgr.register_user(u)
        req = AccessRequest(
            user=u,
            resource_type=ResourceType.VERTEX,
            resource_id="v-1",
            action=Permission.READ_ALL,
            context={"allowed_hours": []},
        )
        decision = self.mgr.evaluate_access(req)
        assert not decision.allowed

    def test_get_user_roles(self):
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["admin", "developer"])
        self.mgr.register_user(u)
        assert self.mgr.get_user_roles("u1") == ["admin", "developer"]
        assert self.mgr.get_user_roles("nope") == []

    def test_export_import_policy(self):
        u = User(user_id="u1", username="alice", email="a@b.com", roles=["admin"])
        self.mgr.register_user(u)
        policy_json = self.mgr.export_policy()
        policy = json.loads(policy_json)
        assert "admin" in policy["roles"]
        assert "u1" in policy["users"]

        new_mgr = RBACManager()
        new_mgr.import_policy(policy_json)
        assert new_mgr.get_user("u1") is not None
        assert new_mgr.get_role("admin") is not None
