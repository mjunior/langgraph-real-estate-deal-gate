from uuid import uuid4

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, Static

from .runner import resume_review, run
from .state import DealState


class DealGateApp(App):
    CSS = """
    #form {
        height: 1fr;
    }

    #review {
        display: none;
        height: auto;
    }

    #review_actions {
        height: auto;
    }
    """

    deal_id: str | None = None

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="form"):
            yield Label("Real Estate Deal Gate")

            yield Label("Deal name")
            yield Input(
                placeholder="My Deal",
                id="deal_name",
            )

            yield Label("Asset type")
            yield Input(
                value="apartment",
                id="asset_type",
            )

            yield Label("Purchase price")
            yield Input(
                placeholder="1000000",
                id="purchase_price",
                type="number",
            )

            yield Label("NOI")
            yield Input(
                placeholder="50000",
                id="noi",
                type="number",
            )

            yield Button(
                "Analyze Deal",
                id="analyze_button",
                variant="primary",
            )

            yield Static("", id="result")

            with Vertical(id="review"):
                yield Label("Human review")
                yield Static("", id="analysis_summary")
                yield Label("Decision reason")
                yield Input(
                    placeholder="Explain the decision",
                    id="human_reason",
                )
                with Horizontal(id="review_actions"):
                    yield Button(
                        "Approve",
                        id="approve_button",
                        variant="success",
                    )
                    yield Button(
                        "Reject",
                        id="reject_button",
                        variant="error",
                    )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "analyze_button":
            self.analyze_deal()
        elif event.button.id == "approve_button":
            self.submit_review("approved")
        elif event.button.id == "reject_button":
            self.submit_review("rejected")

    def analyze_deal(self) -> None:
        result = self.query_one("#result", Static)

        try:
            purchase_price = float(
                self.query_one("#purchase_price", Input).value
            )
            noi = float(self.query_one("#noi", Input).value)
        except ValueError:
            result.update("Purchase price and NOI must be valid numbers.")
            return

        name = self.query_one("#deal_name", Input).value
        asset_type = self.query_one("#asset_type", Input).value

        if not name.strip() or not asset_type.strip():
            result.update("Deal name and asset type are required.")
            return

        self.deal_id = str(uuid4())
        deal: DealState = {
            "deal_id": self.deal_id,
            "name": name,
            "asset_type": asset_type,
            "purchase_price": purchase_price,
            "noi": noi,
        }

        self.query_one("#review", Vertical).display = False
        self.query_one("#analyze_button", Button).disabled = True
        result.update("Analyzing deal...")
        self.run_analysis(deal)

    @work(thread=True, exclusive=True)
    def run_analysis(self, deal: DealState) -> None:
        try:
            response = run(deal)
        except Exception as error:
            self.call_from_thread(self.show_error, error)
            return

        self.call_from_thread(self.show_analysis, response)

    def show_analysis(self, response: DealState) -> None:
        self.query_one("#analyze_button", Button).disabled = False

        if response.get("status") == "human_review":
            cap_rate = response.get("cap_rate", 0)
            self.query_one("#result", Static).update(
                f"Human review required\nCap rate: {cap_rate:.2%}"
            )
            self.query_one("#analysis_summary", Static).update(
                response.get("analysis_summary", "")
            )
            self.query_one("#review", Vertical).display = True
            reason_input = self.query_one("#human_reason", Input)
            self.call_after_refresh(reason_input.focus)
            return

        self.show_final_result(response)

    def submit_review(self, decision: str) -> None:
        if self.deal_id is None:
            self.query_one("#result", Static).update(
                "Analyze a deal before submitting a review."
            )
            return

        reason = self.query_one("#human_reason", Input).value.strip()
        if not reason:
            self.query_one("#result", Static).update(
                "A decision reason is required."
            )
            return

        self.set_review_buttons_disabled(True)
        self.query_one("#result", Static).update("Submitting review...")
        self.run_review(self.deal_id, decision, reason)

    @work(thread=True, exclusive=True)
    def run_review(self, deal_id: str, decision: str, reason: str) -> None:
        try:
            response = resume_review(deal_id, decision, reason)
        except Exception as error:
            self.call_from_thread(self.show_error, error)
            return

        self.call_from_thread(self.show_final_result, response)

    def show_final_result(self, response: DealState) -> None:
        status = response.get("status", "unknown")
        memo = response.get("investment_memo")
        content = f"Decision: {status}"
        if memo:
            content += f"\n\nInvestment memo\n{memo}"

        self.query_one("#result", Static).update(content)
        self.query_one("#review", Vertical).display = False
        self.set_review_buttons_disabled(False)

    def show_error(self, error: Exception) -> None:
        self.query_one("#result", Static).update(f"Error: {error}")
        self.query_one("#analyze_button", Button).disabled = False
        self.set_review_buttons_disabled(False)

    def set_review_buttons_disabled(self, disabled: bool) -> None:
        self.query_one("#approve_button", Button).disabled = disabled
        self.query_one("#reject_button", Button).disabled = disabled


if __name__ == "__main__":
    DealGateApp().run()