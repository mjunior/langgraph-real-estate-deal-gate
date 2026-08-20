from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from .state import DealState
from .graph import build_graph
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver # type: ignore
from .runner import run, resume_review
db_path = "deals.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)


def main():
  my_deal: DealState = {
    "deal_id": "427331",
    "name": "My Deal",
    "asset_type": "apartment",
    "purchase_price": 1_000_000,
    "noi": 50_000,
  }

  response = run(my_deal)

  if "__interrupt__" in response:
    human_decision = input("Please enter your decision (approved/rejected): ").strip().lower()
    human_reason = input("Please provide a reason for your decision: ").strip()

    if human_decision not in ("approved", "rejected"):
      print("Invalid decision. Deal remains waiting for human review.")
      return

    if not human_reason:
      print("Reason is required. Deal remains waiting for human review.")
      return

    response = resume_review(my_deal["deal_id"], human_decision, human_reason)

  if (response):
    print("Final response:", response.get('analysis_summary'))
    print("======")
    print("Memo: ", response.get('investment_memo'))

if __name__ == "__main__":
  main()
