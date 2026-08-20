from deal_gate.state import DealState
from deal_gate.nodes import analyze_deal


def test_analyze_deal_auto_approved():
  state: DealState = {
    "deal_id": "test-1",
    "name": "Test Deal",
    "asset_type": "apartment",
    "purchase_price": 1_000_000,
    "noi": 90_000,
  }

  result = analyze_deal(state)

  assert result["cap_rate"] == 0.09
  assert result["status"] == "approved"


def test_analyze_deal_auto_rejected():
  state: DealState = {
    "deal_id": "test-1",
    "name": "Test Deal",
    "asset_type": "apartment",
    "purchase_price": 1_000_000,
    "noi": 10_000,
  }

  result = analyze_deal(state)

  assert result["cap_rate"] == 0.01
  assert result["status"] == "rejected"

def test_routes_mid_cap_rate_to_human_review():
    state = {
        "deal_id": "test-3",
        "name": "Test Deal",
        "asset_type": "apartment",
        "purchase_price": 1_000_000,
        "noi": 50_000,
    }

    result = analyze_deal(state)

    assert result["cap_rate"] == 0.05
    assert result["status"] == "human_review"