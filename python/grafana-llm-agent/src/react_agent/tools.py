"""This module provides Grafana MCP tools and search functionality.

It includes both Tavily search (as backup) and comprehensive Grafana MCP tools
for observability diagnostics.
"""

from typing import Any, Callable, List, Optional, cast
import asyncio
import logging

from langgraph.types import Command, interrupt

from langchain_tavily import TavilySearch  # type: ignore[import-not-found]
from langchain_mcp_adapters.client import MultiServerMCPClient

from react_agent.configuration import Configuration

# 設置日誌
logger = logging.getLogger(__name__)

# 全局 MCP 客戶端和工具緩存
_mcp_client: Optional[MultiServerMCPClient] = None
_mcp_tools: Optional[List[Callable[..., Any]]] = None


async def search(query: str) -> Optional[dict[str, Any]]:
    """Search for general web results using Tavily.

    This function performs a search using the Tavily search engine, which is designed
    to provide comprehensive, accurate, and trusted results. It's particularly useful
    for answering questions about current events.
    """
    configuration = Configuration.from_context()
    wrapped = TavilySearch(max_results=configuration.max_search_results)
    return cast(dict[str, Any], await wrapped.ainvoke({"query": query}))

def think(thought: str) -> Optional[dict[str, Any]]:
    """Use the tool to think about something.
           This is perfect to start your workflow.
           It will not obtain new information or take any actions, but just append the thought to the log and return the result.
           Use it when complex reasoning or some cache memory or a scratchpad is needed.


           :param thought: A thought to think about and log.
           :return: The full log of thoughts and the new thought.
    """
    return thought

def incrementCounterWithConfirm(reason: str, amount: int) -> dict[str, Any]:
    """
    增加計數器，並且需要使用者確認
    使用 LangGraph 的 interrupt 機制來暫停執行，等待用戶確認
    :param reason: 使用者想要增加的原因
    :param amount: 使用者想要增加多少
    :return: 包含執行結果的字典
    """
    # 使用 interrupt 暫停執行，並提供確認信息給前端
    user_input = interrupt({
        "tool_name": "incrementCounterWithConfirm",
        "action": "increment_counter",
        "reason": reason,
        "amount": amount,
        "message": f"請確認是否要增加計數器 {amount} 次？原因：{reason}",
        "ui_action": "show_counter_increment_dialog",
        "requires_confirmation": True
    })
    print(user_input)
    if user_input == "yes":
        return {
            "success": True,
            "action": "increment_counter",
            "amount": amount,
            "reason": reason,
            "user_input": user_input,
            "message": f"計數器已成功增加 {amount} 次"
        }
    else:
        return {
            "success": False,
            "action": "cancelled",
            "user_input": user_input,
            "reason": user_input.get("reason", "用戶取消操作") if user_input else "用戶取消操作",
            "message": "計數器增加操作已取消"
        }

async def get_mcp_client() -> MultiServerMCPClient:
    """Get or create the MCP client."""
    global _mcp_client
    if _mcp_client is None:
        configuration = Configuration.from_context()
        _mcp_client = MultiServerMCPClient({
            "grafana-mcp": {
                "url": configuration.grafana_mcp_url,
                "transport": "sse",
            }
        })
    return _mcp_client


async def get_mcp_tools() -> List[Callable[..., Any]]:
    """Get the filtered MCP tools."""
    global _mcp_tools
    if _mcp_tools is None:
        try:
            configuration = Configuration.from_context()
            client = await get_mcp_client()
            
            # 從 MCP Server 中獲取所有工具
            all_tools = await client.get_tools()
            logger.info(f"所有可用的 Grafana 工具: {[tool.name for tool in all_tools]}")
            
            # 過濾工具，只保留配置中指定的工具
            _mcp_tools = [tool for tool in all_tools if tool.name in configuration.grafana_tools]
            logger.info(f"已選擇的工具: {[tool.name for tool in _mcp_tools]}")
            logger.info(f"工具數量: {len(_mcp_tools)}/{len(all_tools)}")
            
        except Exception as e:
            logger.error(f"無法獲取 MCP 工具: {e}")
            _mcp_tools = []
    
    return _mcp_tools


async def get_all_tools() -> List[Callable[..., Any]]:
    """Get all available tools (both MCP and search)."""
    mcp_tools = await get_mcp_tools()
    return [search, think, incrementCounterWithConfirm] + mcp_tools


def parse_messages(messages: List[Any]) -> None:
    """
    解析消息列表，打印 HumanMessage、AIMessage 和 ToolMessage 的詳細信息

    Args:
        messages: 包含消息的列表，每個消息是一個對象
    """
    print("\n🔍 === 詳細消息解析 ===")
    for idx, msg in enumerate(messages, 1):
        print(f"\n📝 消息 {idx}: {msg.__class__.__name__}")
        print("-" * 40)
        
        # 獲取消息類型
        msg_type = msg.__class__.__name__
        
        # 提取消息內容
        content = getattr(msg, 'content', '')
        if content:
            print(f"💬 內容: {content}")
        
        # 處理 HumanMessage
        if msg_type == 'HumanMessage':
            print("👤 用戶輸入")
            
        # 處理 AIMessage 的工具調用
        elif msg_type == 'AIMessage':
            print("🤖 AI 回應")
            tool_calls = getattr(msg, 'tool_calls', [])
            if tool_calls:
                print("🔧 工具調用:")
                for i, tool_call in enumerate(tool_calls, 1):
                    print(f"  {i}. 工具名稱: {tool_call.get('name', 'Unknown')}")
                    print(f"     工具參數: {tool_call.get('args', {})}")
                    print(f"     調用 ID: {tool_call.get('id', 'Unknown')}")
            
            # 處理 additional_kwargs 中的工具調用（舊格式）
            additional_kwargs = getattr(msg, 'additional_kwargs', {})
            if additional_kwargs.get('tool_calls'):
                print("🔧 工具調用 (舊格式):")
                for i, tool_call in enumerate(additional_kwargs['tool_calls'], 1):
                    print(f"  {i}. 函數名稱: {tool_call.get('function', {}).get('name', 'Unknown')}")
                    print(f"     函數參數: {tool_call.get('function', {}).get('arguments', '{}')}")
                    print(f"     調用 ID: {tool_call.get('id', 'Unknown')}")
        
        # 處理 ToolMessage
        elif msg_type == 'ToolMessage':
            print("🛠️ 工具執行結果")
            tool_name = getattr(msg, 'name', 'Unknown')
            tool_call_id = getattr(msg, 'tool_call_id', 'Unknown')
            print(f"🔧 工具名稱: {tool_name}")
            print(f"🆔 工具調用 ID: {tool_call_id}")
            
            # 嘗試解析 JSON 格式的工具結果
            try:
                import json
                if content:
                    parsed_content = json.loads(content)
                    if isinstance(parsed_content, list) and len(parsed_content) > 0:
                        print(f"📊 結果數量: {len(parsed_content)} 項")
                        print(f"📋 結果預覽: {str(parsed_content)[:200]}...")
                    else:
                        print(f"📊 結果: {str(parsed_content)[:200]}...")
            except:
                print(f"📊 原始結果: {content[:200]}...")
        
        print()  # 空行分隔


# 為了兼容性，我們需要在模組級別提供 TOOLS
# 但由於 MCP 工具需要異步初始化，我們提供一個空列表作為佔位符
TOOLS: List[Callable[..., Any]] = [search, think, incrementCounterWithConfirm]
