from app.access import service


class DummyDB:
    pass


def test_get_user_permissions_uses_membership_role(monkeypatch):
    db = DummyDB()

    def fake_fetch_one(_db, query, params=None):
        if "FROM company_memberships" in query:
            return {"role_id": 10, "role_name": "ADMIN_EMPRESA"}
        return None

    def fake_fetch_all(_db, query, params=None):
        if "FROM role_permissions" in query:
            return [{"id": 1, "name": "Ver usuarios", "slug": "users.view"}]
        return []

    monkeypatch.setattr(service, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(service, "fetch_all", fake_fetch_all)

    result = service.get_user_permissions(db, user_id=5, company_id=7)

    assert result["role_id"] == 10
    assert result["role_name"] == "ADMIN_EMPRESA"
    assert len(result["permissions"]) == 1
    assert result["permissions"][0]["slug"] == "users.view"
