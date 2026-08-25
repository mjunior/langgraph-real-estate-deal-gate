import asyncio

from textual.containers import Vertical
from textual.widgets import Input, Static

from deal_gate.tui import DealGateApp


def test_analyze_and_approve_human_review(monkeypatch):
    resumed_with = {}

    def fake_run(deal):
        return {
            **deal,
            "status": "human_review",
            "cap_rate": 0.05,
            "analysis_summary": "\n".join(
                f"Review detail {line}." for line in range(30)
            ),
            "__interrupt__": (),
        }

    def fake_resume_review(deal_id, decision, reason):
        resumed_with.update(
            deal_id=deal_id,
            decision=decision,
            reason=reason,
        )
        return {
            "deal_id": deal_id,
            "name": "Test Deal",
            "asset_type": "apartment",
            "purchase_price": 1_000_000,
            "noi": 50_000,
            "status": decision,
            "human_decision": decision,
            "human_reason": reason,
            "investment_memo": "Fake investment memo",
        }

    monkeypatch.setattr("deal_gate.tui.run", fake_run)
    monkeypatch.setattr("deal_gate.tui.resume_review", fake_resume_review)

    async def exercise_app():
        app = DealGateApp()
        async with app.run_test(size=(80, 24)) as pilot:
            app.query_one("#deal_name", Input).value = "Test Deal"
            app.query_one("#purchase_price", Input).value = "1000000"
            app.query_one("#noi", Input).value = "50000"

            await pilot.click("#analyze_button")
            await pilot.pause()

            assert app.query_one("#review", Vertical).display
            assert "Review detail 0." in str(
                app.query_one("#analysis_summary", Static).render()
            )
            reason_input = app.query_one("#human_reason", Input)
            assert app.focused is reason_input
            assert reason_input.region.bottom <= app.screen.size.height

            reason_input.value = "Acceptable return."
            await pilot.click("#approve_button")
            await pilot.pause()

            assert not app.query_one("#review", Vertical).display
            result = app.query_one("#result", Static)
            assert "Decision: approved" in str(result.render())
            assert 0 <= result.region.y < app.screen.size.height
            assert result.region.bottom <= app.screen.size.height
            assert resumed_with == {
                "deal_id": app.deal_id,
                "decision": "approved",
                "reason": "Acceptable return.",
            }

    asyncio.run(exercise_app())