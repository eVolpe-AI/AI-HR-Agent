from langgraph.checkpoint import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agent_graph.nodes.gear_manager import gear_manager
from agent_graph.nodes.intent_retrival import intent_retrival
from agent_graph.nodes.llm_call import llm_call
from agent_graph.nodes.output_parser import output_parser
from agent_graph.nodes.tool_permit import tool_permit
from agent_state.state import GraphState


def should_continue(state) -> str:
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"


def check_user_decision(state) -> str:
    decision = state["tool_accept"]
    if decision:
        return "consent"
    else:
        return "decline"


def check_intent(state) -> str:
    return "continue"


def check_message_type(state) -> str:
    print(state["tool_accept"])
    if state["tool_accept"]:
        return "confirmation"
    else:
        return "default"


def create_graph(tools):
    graph = StateGraph(GraphState)

    graph.add_node("llm_node", llm_call)
    graph.add_node("tool_node", ToolNode(tools))
    graph.add_node("tool_controller_node", tool_permit)
    graph.add_node("intent_retrival_node", intent_retrival)
    graph.add_node("gear_manager_node", gear_manager)
    graph.add_node("output_parsing_node", output_parser)

    graph.add_conditional_edges(
        START,
        check_message_type,
        {"default": "intent_retrival_node", "confirmation": "tool_node"},
    )
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
        {"consent": "tool_node", "decline": "output_parsing_node"},
    )
    graph.add_edge("tool_node", "llm_node")
    graph.add_edge("output_parsing_node", END)

    return graph


def compile_workflow(graph):
    memory = MemorySaver()
    workflow = graph.compile(checkpointer=memory)

    return workflow
