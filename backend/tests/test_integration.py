from fastapi.testclient import TestClient

from app.main import app
from app.store import WATCHLIST

client = TestClient(app)


def setup_function() -> None:
    WATCHLIST.clear()


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_funds_list_and_sort() -> None:
    resp = client.get("/api/v1/funds", params={"risk_profile": "均衡", "page": 1, "page_size": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert data["total"] >= 3
    assert len(data["items"]) == 3
    assert data["items"][0]["final_score"] >= data["items"][1]["final_score"]


def test_funds_list_sort_by_fee_asc() -> None:
    resp = client.get(
        "/api/v1/funds",
        params={"risk_profile": "均衡", "sort_by": "fee", "sort_order": "asc", "page": 1, "page_size": 6},
    )
    assert resp.status_code == 200
    names = [item["name"] for item in resp.json()["items"]]
    assert names[0] == "稳健纯债A"


def test_funds_pagination_page_2_differs_from_page_1() -> None:
    page1 = client.get("/api/v1/funds", params={"risk_profile": "均衡", "page": 1, "page_size": 2})
    page2 = client.get("/api/v1/funds", params={"risk_profile": "均衡", "page": 2, "page_size": 2})

    assert page1.status_code == 200
    assert page2.status_code == 200

    codes1 = [item["code"] for item in page1.json()["items"]]
    codes2 = [item["code"] for item in page2.json()["items"]]
    assert codes1
    assert codes2
    assert codes1 != codes2


def test_funds_pagination_invalid_page_rejected() -> None:
    resp = client.get("/api/v1/funds", params={"risk_profile": "均衡", "page": 0, "page_size": 10})
    assert resp.status_code == 422


def test_funds_pagination_invalid_page_size_rejected() -> None:
    resp = client.get("/api/v1/funds", params={"risk_profile": "均衡", "page": 1, "page_size": 101})
    assert resp.status_code == 422


def test_fund_detail_not_found() -> None:
    resp = client.get("/api/v1/funds/UNKNOWN")
    assert resp.status_code == 404


def test_compare_happy_path() -> None:
    resp = client.get(
        "/api/v1/compare",
        params=[("codes", "510300"), ("codes", "005827"), ("risk_profile", "均衡")],
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload) == 2


def test_compare_invalid_size() -> None:
    resp = client.get("/api/v1/compare", params=[("codes", "510300")])
    assert resp.status_code == 422


def test_watchlist_flow_with_alerts() -> None:
    create = client.post("/api/v1/watchlist", json={"code": "512480"})
    assert create.status_code == 200

    listed = client.get("/api/v1/watchlist")
    assert listed.status_code == 200
    payload = listed.json()
    assert len(payload) == 1
    assert "alerts" in payload[0]

    delete = client.delete("/api/v1/watchlist/512480")
    assert delete.status_code == 200
    assert client.get("/api/v1/watchlist").json() == []


def test_policy_timestamp_validation_api() -> None:
    payload = {
        "policy_id": "P-001",
        "published_at": "2026-03-01T09:00:00Z",
        "effective_from": "2026-03-02T09:00:00Z",
        "observed_at": "2026-03-03T09:00:00Z",
    }
    resp = client.post("/api/v1/policy/validate-timestamps", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["policy_id"] == "P-001"
    assert data["valid"] is True
    assert data["errors"] == []
