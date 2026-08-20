# tests/test_human_review_flow.py

from unittest.mock import MagicMock

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from deal_gate.graph import build_graph


class TestHumanReviewFlow:
    def test_human_review_interrupt_and_resume(self, monkeypatch):
        # Mock da LLM para análise
        fake_analysis_response = MagicMock()
        fake_analysis_response.content = "Fake analysis summary"

        # Mock da LLM para memo final
        fake_memo_response = MagicMock()
        fake_memo_response.content = "Fake investment memo"

        fake_llm = MagicMock()
        fake_llm.invoke.side_effect = [
            fake_analysis_response,
            fake_memo_response,
        ]

        monkeypatch.setattr(
            "deal_gate.nodes.llm",
            fake_llm,
        )

        # Checkpointer isolado para o teste
        graph = build_graph(
            checkpointer=InMemorySaver()
        )

        deal = {
            "deal_id": "test-human-review-22",
            "name": "Test Deal",
            "asset_type": "apartment",
            "purchase_price": 1_000_000,
            "noi": 50_000,
        }

        config = {
            "configurable": {
                "thread_id": deal["deal_id"]
            }
        }

        # ACT 1 — começa o workflow
        response = graph.invoke(
            deal,
            config=config,
        )

        # ASSERT 1 — deve ter parado no interrupt
        assert "__interrupt__" in response
        assert response["status"] == "human_review"
        assert response["cap_rate"] == 0.05
        assert response["analysis_summary"] == "Fake analysis summary"

        # ACT 2 — humano aprova
        resumed_response = graph.invoke(
            Command(
                resume={
                    "human_decision": "approved",
                    "human_reason": "Acceptable return for the asset profile.",
                }
            ),
            config=config,
        )

        # ASSERT 2 — workflow terminou
        assert resumed_response["status"] == "approved"
        assert resumed_response["human_decision"] == "approved"
        assert resumed_response["human_reason"] == (
            "Acceptable return for the asset profile."
        )
        assert resumed_response["investment_memo"] == "Fake investment memo"

        # análise + memo
        assert fake_llm.invoke.call_count == 2