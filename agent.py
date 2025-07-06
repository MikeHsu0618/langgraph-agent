import asyncio
import os
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.chat_models import init_chat_model
from typing import Dict, List, Any

# 載入 .env 文件
load_dotenv()

# Author: Grafana 可觀測性診斷專家 - 基於 LangGraph + MCP

# 使用 LangGraph 推薦方式定義大模型
# 選項 1: 使用 Gemini（從 .env 讀取 API key）
# llm = init_chat_model(
#     model="gemini-2.5-flash",
#     model_provider="google_genai",
#     temperature=0,
#     api_key=os.getenv("GOOGLE_API_KEY"),  # 從 .env 文件讀取
# )

# 選項 2: 使用 OpenAI（從 .env 讀取 API key）
llm = init_chat_model(
    model="gpt-4o-mini",
    model_provider="openai",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),  # 從 .env 文件讀取
)

# 選項 3: 使用本地 Ollama（如果你有安裝）
# llm = init_chat_model(
#     model="llama3.2",
#     model_provider="ollama",
#     temperature=0,
#     base_url="http://localhost:11434",
# )

# 選項 4: 使用有效的 DeepSeek API key
# llm = init_chat_model(
#     model="deepseek-v3",
#     model_provider="openai",
#     temperature=0,
#     base_url="https://nangeai.top/v1",
#     api_key="your-valid-api-key-here"  # 請替換為有效的 API key
# )


# 解析消息列表
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


# 保存狀態圖的可視化表示
def save_graph_visualization(graph, filename: str = "grafana_agent_graph.png") -> None:
    """保存狀態圖的可視化表示。

    Args:
        graph: 狀態圖實例。
        filename: 保存文件路徑。
    """
    # 嘗試執行以下代碼塊
    try:
        # 以二進制寫模式打開文件
        with open(filename, "wb") as f:
            # 將狀態圖轉換為 Mermaid 格式的 PNG 並寫入文件
            f.write(graph.get_graph().draw_mermaid_png())
        # 記錄保存成功的日誌
        print(f"Grafana Agent 圖形可視化已保存為 {filename}")
    # 捕獲 IO 錯誤
    except IOError as e:
        # 記錄警告日誌
        print(f"保存圖形可視化失敗: {e}")


# 定義並運行 Grafana 可觀測性診斷專家 Agent
async def run_grafana_agent():
    # 實例化 MCP Server 客戶端
    client = MultiServerMCPClient({
        # Grafana MCP Server - 連接到你的本地 Grafana MCP 服務
        "grafana-mcp": {
            "url": os.getenv("GRAFANA_MCP_URL", "http://localhost:8001/sse"),  # 從 .env 讀取，有預設值
            "transport": "sse",
        }
    })

    # 從 MCP Server 中獲取可提供使用的全部工具
    all_tools = await client.get_tools()
    print(f"🔧 所有可用的 Grafana 工具: {[tool.name for tool in all_tools]}\n")

    # 定義你想要的工具列表
    desired_tools = [
        'list_loki_label_names',
        'list_loki_label_values',
        'query_loki_stats',
        'search_dashboards',
        'get_dashboard_by_uid',
        'update_dashboard',
        'get_dashboard_panel_queries',
        'list_datasources',
        'get_datasource_by_uid',
        'get_datasource_by_name',
        'query_prometheus',
        'list_prometheus_metric_metadata',
        'list_prometheus_metric_names',
        'list_prometheus_label_names',
        'list_prometheus_label_values',
        'query_loki_logs',
    ]

    # 過濾工具，只保留你想要的
    tools = [tool for tool in all_tools if tool.name in desired_tools]
    print(f"🎯 已選擇的工具: {[tool.name for tool in tools]}")
    print(f"📊 工具數量: {len(tools)}/{len(all_tools)}\n")

    # 基於內存存儲的 short-term
    checkpointer = InMemorySaver()

    # 定義系統消息，指導如何使用工具
    system_message = SystemMessage(content=(
        """你是首席 Grafana 可觀測性診斷專家，具備深度推理和多步驟問題解決能力。

## 🎯 核心能力
1. **深度分析**: 使用 Chain of Thought 推理，逐步分解複雜問題
2. **工具鏈調度**: 智能選擇和組合多個工具，直到獲得完整答案
3. **持續探索**: 不滿足於表面信息，深入挖掘根本原因

## 🔍 工作流程
1. **理解問題**: 分析用戶需求，識別關鍵信息和潛在問題
2. **制定策略**: 規劃多步驟調查路徑，預測可能需要的工具
3. **執行調查**: 
   - 先用 list_datasources 了解可用資源
   - 根據問題類型選擇合適的數據源（Loki/Prometheus）
   - 使用 label_names/label_values 探索可用標籤
   - 執行查詢並分析結果
4. **深度分析**: 
   - 如果發現異常，進一步調查原因
   - 檢查相關指標和日誌的關聯性
   - 尋找趨勢和模式
5. **綜合結論**: 提供完整的分析報告和建議

## 🚨 決策原則
- **不急於回答**: 確保收集足夠信息後再給出結論
- **多角度驗證**: 從不同數據源交叉驗證發現
- **主動探索**: 即使用戶沒有明確要求，也要挖掘相關問題
- **結構化輸出**: 清晰組織調查過程和發現

## 📊 專業領域
- 日誌分析和異常檢測
- 性能指標監控和趨勢分析  
- 系統故障診斷和根因分析
- 用戶行為和業務指標分析
- 告警規則優化建議

執行任務時如果遇到問題：
1. 分析失敗原因
2. 重新制定計劃
3. 嘗試替代方案
4. 如果仍然失敗，向用戶說明情況並請求更多信息

記住：你的目標是成為用戶最信賴的可觀測性夥伴，提供深度洞察而非表面回答。"""
    ))

    # 創建 ReAct 風格的 agent
    agent = create_react_agent(
        model=llm,
        tools=tools,  # 使用過濾後的工具
        prompt=system_message,
        checkpointer=checkpointer
    )

    # 將定義的 agent 的 graph 進行可視化輸出保存至本地
    save_graph_visualization(agent)

    # 定義 short-term 需使用的 thread_id
    config = {"configurable": {"thread_id": "1"}}

    print("🚀 Grafana 可觀測性診斷專家已啟動！")
    print("=" * 60)
    
    # 測試查詢
    test_query = "幫我全面分析 sporty prod rum 環境的健康狀況，盡可能的使用 loki 查看最近十分鐘的 log，你會先查 loki label 並且在去找 stat 看有沒有資料，最後找到最接近 service_name:SportyBet Android 跟 service_country:zm 的 log"
    # test_query= "幫我查有關 kubenetes 的 dashboard"
    print(f"🔍 正在處理查詢: {test_query}")
    print("=" * 60)
    
    try:
        # 1、非流式處理查詢
        agent_response = await agent.ainvoke(
            {"messages": [HumanMessage(content=test_query)]}, 
            config
        )
        
        # 解析並顯示所有消息（包括工具調用和回應）
        parse_messages(agent_response['messages'])
        
        # 提取最終回應內容
        final_message = agent_response['messages'][-1]
        agent_response_content = final_message.content if hasattr(final_message, 'content') else str(final_message)
        print(f"\n🎯 最終回應: {agent_response_content}")
        
    except Exception as e:
        print(f"❌ 查詢過程中發生錯誤: {e}")
        print("請檢查 Grafana MCP 服務是否正常運行")


if __name__ == "__main__":
    asyncio.run(run_grafana_agent())



