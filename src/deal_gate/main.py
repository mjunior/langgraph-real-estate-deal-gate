from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from .state import DealState
from .graph import build_graph
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver # type: ignore

db_path = "deals.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)


def main():
  graph = build_graph(checkpointer=memory)
  my_deal: DealState = {
    "deal_id": "47",
    "name": "My Deal",
    "asset_type": "apartment",
    "purchase_price": 1_000_000,
    "noi": 50_000,
  }

  config: RunnableConfig = { "configurable": { "thread_id": my_deal["deal_id"] } }
  snapshot = graph.get_state(config)

  response = "";
  if snapshot.values:
    if snapshot.values.get("status") == "approved" or snapshot.values.get("status") == "rejected":
      print(f"Deal {my_deal['deal_id']} has already been processed with status: {snapshot.values.get('status')}")
      history = graph.get_state_history(config)
      print("State history:")
      for entry in history:
        print(f" - {entry.created_at}: {entry.values.get('status')}")

    else:
      response = graph.invoke(None, config=config)
  else:
    response = graph.invoke(my_deal, config=config)

  if "__interrupt__" in response:
    human_decision = input("Please enter your decision (approved/rejected): ").strip().lower()
    human_reason = input("Please provide a reason for your decision: ").strip()

    if human_decision not in ("approved", "rejected"):
      print("Invalid decision. Deal remains waiting for human review.")
      return

    if not human_reason:
      print("Reason is required. Deal remains waiting for human review.")
      return

    response = graph.invoke(
    Command(resume={
        "human_decision": human_decision,
        "human_reason": human_reason
      }),
      config=config,
    )

  if (response):
    print("Final response:", response.get('analysis_summary'))
    print("======")
    print("Memo: ", response.get('investment_memo'))

if __name__ == "__main__":
  main()
