from typing import Literal, TypedDict, NotRequired

class DealState(TypedDict):
  deal_id: str
  name: str
  asset_type: str
  purchase_price: float
  noi: float
  cap_rate: NotRequired[float]
  analysis_summary: NotRequired[str]
  human_decision: NotRequired[Literal["approved", "rejected"]]
  human_reason: NotRequired[str]
  investment_memo: NotRequired[str]
  status: NotRequired[Literal[
    "pending",
    "valid",
    "invalid",
    "approved",
    "rejected",
    "human_review"
  ]] # <- analyze node set it