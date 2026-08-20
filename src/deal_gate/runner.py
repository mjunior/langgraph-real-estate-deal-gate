from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from .state import DealState
from .graph import build_graph
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver # type: ignore

db_path = "deals.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)


def run(my_deal: DealState):
  graph = build_graph(checkpointer=memory)
  config: RunnableConfig = { "configurable": { "thread_id": my_deal["deal_id"] } }
  snapshot = graph.get_state(config)

  response = "";
  if snapshot.values:
    if not snapshot.next:
      return snapshot.values
    else:
      response = graph.invoke(None, config=config)
  else:
    response = graph.invoke(my_deal, config=config)

  return response

def resume_review(
    deal_id: str,
    human_decision: str,
    human_reason: str,
):
    graph = build_graph(checkpointer=memory)

    config = {
        "configurable": {
            "thread_id": deal_id
        }
    }

    return graph.invoke(
        Command(
            resume={
                "human_decision": human_decision,
                "human_reason": human_reason,
            }
        ),
        config=config,
    )