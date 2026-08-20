from .state import DealState
from langgraph.types import interrupt
from langchain_core.messages import SystemMessage, HumanMessage

from .llm import llm
from .agents.deal_analyzer import deal_analyzer_system_prompt, deal_analyzer_user_prompt, deal_investiment_committee_system_prompt, deal_investiment_committee_user_prompt

def prepare_deal(state: DealState):
  return {
    "status": "pending"
  }

def validate_deal(state: DealState):
  required_fields = (
    "deal_id",
    "name",
    "asset_type",
    "purchase_price",
    "noi",
  )

  for field in required_fields:
    value = state.get(field)

    if value is None or str(value).strip() == "":
      return {
        "status": "invalid"
      }

  purchase_price = state.get("purchase_price")
  noi = state.get("noi")

  if purchase_price <= 0 or noi <= 0:
    return {
      "status": "invalid"
    }

  return {
    "status": "valid"
  }

def analyze_deal(state: DealState):
  noi = state.get("noi")
  purchase_price = state.get("purchase_price")

  cap_rate = noi / purchase_price
  status = None;
  if cap_rate >= 0.08:
    status = "approved"
  elif cap_rate < 0.05:
    status = "rejected"
  else:
    status = "human_review" 

  return {
    "status": status,
    "cap_rate": cap_rate
  }

def sumarize_analysis(state: DealState):
  system_prompt = deal_analyzer_system_prompt()
  user_prompt = deal_analyzer_user_prompt(state)

  response = llm.invoke([
    SystemMessage(content=system_prompt),
    HumanMessage(content=(
      "This deal could not be automatically approved or rejected "
      "by the deterministic policy rules. "
      "Analyze the deal for a human reviewer using only the provided "
      "deal data and fictional investment policy. "
      "Do not make the final approval decision.\n\n"
      f"{user_prompt}"
    ))
  ])

  return {
    "analysis_summary": response.content
  }

def notify_deal_pending_to_review(state: DealState):
  deal_id = state.get("deal_id")
  print(f"\n\n============ \n\tNotification: Deal with ID {deal_id} is pending review.n\n\n")
  return state

def human_review(state: DealState):
  human_response = interrupt(state)
  human_decision = human_response.get("human_decision")
  human_reason = human_response.get("human_reason")

  # validate the decision
  if human_decision not in ("approved", "rejected"):
    print(f"Invalid decision: {human_decision}. Please enter 'approved' or 'rejected'.")
    human_response = interrupt(state)
    return

  return {
    "status": human_decision,
    "human_reason": human_reason,
    "human_decision": human_decision,
  }

def write_investment_memo(state: DealState):
  response = llm.invoke([
    SystemMessage(content=deal_investiment_committee_system_prompt()),
    HumanMessage(content=deal_investiment_committee_user_prompt(state))
  ])

  return {
    "investment_memo": response.content
  }