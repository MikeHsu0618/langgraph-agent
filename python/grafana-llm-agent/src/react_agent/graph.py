"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import UTC, datetime
from typing import Dict, List, Literal, cast
import asyncio
import logging

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from react_agent.configuration import Configuration
from react_agent.state import InputState, State
from react_agent.tools import get_all_tools, TOOLS, parse_messages
from react_agent.utils import load_chat_model

# 設置日誌
logger = logging.getLogger(__name__)

# 全局變量來存儲動態工具
_dynamic_tools = None
_compiled_graph = None


async def get_dynamic_tools():
    """Get dynamically loaded tools including MCP tools."""
    global _dynamic_tools
    if _dynamic_tools is None:
        try:
            _dynamic_tools = await get_all_tools()
            logger.info(f"動態載入工具: {[tool.name if hasattr(tool, 'name') else str(tool) for tool in _dynamic_tools]}")
        except Exception as e:
            logger.error(f"無法載入動態工具: {e}")
            _dynamic_tools = TOOLS  # 回退到靜態工具
    return _dynamic_tools


# Define the function that calls the model
async def call_model(state: State) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.

    Returns:
        dict: A dictionary containing the model's response message.
    """
    configuration = Configuration.from_context()

    # 獲取動態工具
    tools = await get_dynamic_tools()
    
    # Initialize the model with tool binding. Change the model or add more tools here.
    model = load_chat_model(configuration.model).bind_tools(tools)

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = configuration.system_prompt.format(
        system_time=datetime.now(tz=UTC).isoformat()
    )

    # Get the model's response
    response = cast(
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": system_message}, *state.messages]
        ),
    )

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="抱歉，我在指定的步驟數內無法找到答案。請提供更多信息或簡化問題。",
                )
            ]
        }

    # Return the model's response as a list to be added to existing messages
    return {"messages": [response]}


def route_model_output(state: State) -> Literal["__end__", "tools"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "tools").
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return "__end__"
    # Otherwise we execute the requested actions
    return "tools"


async def create_graph():
    """Create the graph with dynamic tools."""
    global _compiled_graph
    if _compiled_graph is None:
        # 獲取動態工具
        tools = await get_dynamic_tools()
        
        # Define a new graph
        builder = StateGraph(State, input=InputState, config_schema=Configuration)

        # Define the two nodes we will cycle between
        builder.add_node(call_model)
        builder.add_node("tools", ToolNode(tools))

        # Set the entrypoint as `call_model`
        builder.add_edge("__start__", "call_model")

        # Add a conditional edge to determine the next step after `call_model`
        builder.add_conditional_edges(
            "call_model",
            route_model_output,
        )

        # Add a normal edge from `tools` to `call_model`
        builder.add_edge("tools", "call_model")

        # Compile the builder into an executable graph
        # Note: In LangGraph Platform, persistence is handled automatically
        _compiled_graph = builder.compile(name="Grafana LLM Agent")
        
        logger.info("圖結構已成功編譯")
    
    return _compiled_graph


def save_graph_visualization(graph, filename: str = "grafana_agent_graph.png") -> None:
    """保存狀態圖的可視化表示。

    Args:
        graph: 狀態圖實例。
        filename: 保存文件路徑。
    """
    try:
        with open(filename, "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
        logger.info(f"Grafana Agent 圖形可視化已保存為 {filename}")
    except Exception as e:
        logger.warning(f"保存圖形可視化失敗: {e}")


# 為了兼容性，我們提供一個同步的 graph 對象
# 但實際使用時應該使用 create_graph() 函數
async def get_graph():
    """Get the compiled graph."""
    return await create_graph()


# 創建一個包裝函數用於向後兼容
def create_sync_graph():
    """Create graph synchronously (for compatibility)."""
    return asyncio.run(create_graph())


# 為了兼容現有的測試，我們提供一個預設的 graph 對象
# 但在生產環境中建議使用 get_graph() 函數
try:
    graph = create_sync_graph()
except Exception as e:
    logger.error(f"無法創建同步圖: {e}")
    # 回退到簡單的圖結構
    builder = StateGraph(State, input=InputState, config_schema=Configuration)
    builder.add_node(call_model)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge("__start__", "call_model")
    builder.add_conditional_edges("call_model", route_model_output)
    builder.add_edge("tools", "call_model")
    # Note: In LangGraph Platform, persistence is handled automatically
    graph = builder.compile(name="Grafana LLM Agent (Fallback)")
