from typing import TypedDict

from langgraph.checkpoint import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agent_graph.nodes.gear_manager import gear_manager
from agent_graph.nodes.intent_retrival import intent_retrival
from agent_graph.nodes.llm_call import llm_call
from agent_graph.nodes.output_parser import output_parser
from agent_graph.nodes.tool_permit import tool_permit
from agent_state.state import GraphState


class ConfigSchema(TypedDict):
    system_prompt: str


def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"


def check_user_decision(state):
    decision = state["tool_accept"]
    if decision == 1:
        return "consent"
    else:
        return "decline"


# TODO:
def check_intent(state):
    return "continue"


def check_another_prompt(state):
    if state["continue_conversation"]:
        return "continue"
    else:
        return "end"


def create_graph(tools):
    graph = StateGraph(GraphState, ConfigSchema)

    graph.add_node("llm_node", llm_call)
    graph.add_node("tool_node", ToolNode(tools))
    graph.add_node("tool_controller_node", tool_permit)
    graph.add_node("intent_retrival_node", intent_retrival)
    graph.add_node("gear_manager_node", gear_manager)
    graph.add_node("output_parsing_node", output_parser)

    graph.add_edge(START, "intent_retrival_node")
    graph.add_conditional_edges(
        "intent_retrival_node",
        check_intent,
        {"continue": "gear_manager_node", "end": "output_parsing_node"},
    )
    graph.add_edge("gear_manager_node", "llm_node")
    graph.add_conditional_edges(
        "llm_node",
        should_continue,
        {"continue": "tool_controller_node", "end": "output_parsing_node"},
    )
    graph.add_conditional_edges(
        "tool_controller_node",
        check_user_decision,
        {"consent": "tool_node", "decline": "llm_node"},
    )
    graph.add_edge("tool_node", "llm_node")
    graph.add_conditional_edges(
        "output_parsing_node",
        check_another_prompt,
        {"continue": "intent_retrival_node", "end": END},
    )

    return graph


def compile_workflow(graph):
    memory = MemorySaver()
    workflow = graph.compile(checkpointer=memory)

    return workflow
