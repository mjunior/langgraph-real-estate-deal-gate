from langgraph.graph import START, END, StateGraph
from .state import DealState
from .nodes import prepare_deal, validate_deal, analyze_deal, human_review, notify_deal_pending_to_review, sumarize_analysis, write_investment_memo

def route_deal_is_valid(state: DealState):
  if state.get("status") == "valid":
    return "analyze_deal"
  else:
    return END

def route_deal_analysis_result(state: DealState):
  status = state.get("status")
  if status == "approved":
    return "write_investment_memo"
  elif status == "rejected":
    return END
  elif status == "human_review":
    return "sumarize_analysis"
  else:
    raise ValueError(f"Unexpected status: {status}")

def build_graph(checkpointer=None):
  state_graph = StateGraph(DealState)
  state_graph.add_node("prepare_deal", prepare_deal)
  state_graph.add_node("validate_deal", validate_deal)
  state_graph.add_node("analyze_deal", analyze_deal)
  state_graph.add_node("sumarize_analysis", sumarize_analysis)
  state_graph.add_node("human_review", human_review)  
  state_graph.add_node("notify_reviewer", notify_deal_pending_to_review)
  state_graph.add_node("write_investment_memo", write_investment_memo)

  state_graph.add_edge(START, "prepare_deal")
  state_graph.add_edge("prepare_deal", "validate_deal")
  state_graph.add_conditional_edges("validate_deal", route_deal_is_valid)
  state_graph.add_conditional_edges("analyze_deal", route_deal_analysis_result)
  state_graph.add_edge("sumarize_analysis", "notify_reviewer")
  state_graph.add_edge("notify_reviewer", "human_review")
  state_graph.add_edge("human_review", "write_investment_memo")
  state_graph.add_edge("write_investment_memo", END)

  return state_graph.compile(checkpointer=checkpointer)
