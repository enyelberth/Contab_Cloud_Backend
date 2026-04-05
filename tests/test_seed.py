from app.access import service as access_service
from app.auth.dependencies import _has_permission_in_role
from seed import DEMO_USERS, ROLE_PERMISSIONS, get_seed_permission_slugs


def test_seed_permissions_cover_router_permissions():
    expected = {
        "companies.view",
        "companies.create",
        "companies.delete",
        "company.roles.manage",
        "users.view",
        "users.create",
        "users.update",
        "users.delete",
        "users.assign_permissions",
        "products.view",
        "products.create",
        "products.update",
        "products.delete",
    }

    assert expected.issubset(get_seed_permission_slugs())


def test_seed_role_permissions_only_use_known_permissions():
    known_permissions = get_seed_permission_slugs()

    for permission_slugs in ROLE_PERMISSIONS.values():
        assert set(permission_slugs).issubset(known_permissions)


def test_demo_users_reference_seeded_roles():
    known_roles = set(ROLE_PERMISSIONS)

    for user in DEMO_USERS:
        tenant_role = user["tenant_role"]
        assert tenant_role in known_roles


def test_get_user_permissions_query_no_longer_depends_on_missing_deleted_at(monkeypatch):
    db = object()

    def fake_fetch_one(_db, query, params=None):
        assert "p.deleted_at" not in query
        if "FROM global.user_tenants ut" in query:
            return {"role_id": "role-1", "role_name": "tenant_admin"}
        return None

    def fake_fetch_all(_db, query, params=None):
        assert "p.deleted_at" not in query
        return [{"id": "perm-1", "name": "Ver usuarios", "slug": "users.view"}]

    monkeypatch.setattr(access_service, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(access_service, "fetch_all", fake_fetch_all)

    result = access_service.get_user_permissions(db, user_id="user-1", company_id="tenant-1")

    assert result["permissions"][0]["slug"] == "users.view"


def test_has_permission_in_role_query_no_longer_depends_on_missing_deleted_at(monkeypatch):
    captured = {}

    def fake_fetch_one(_db, query, params=None):
        captured["query"] = query
        return {"ok": 1}

    monkeypatch.setattr("app.auth.dependencies.fetch_one", fake_fetch_one)

    assert _has_permission_in_role(object(), "role-1", "users.view") is True
    assert "p.deleted_at" not in captured["query"]
