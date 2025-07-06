#!/usr/bin/env python3
"""
Grafana LLM Agent 執行腳本
基於 LangGraph 框架的 Grafana 可觀測性診斷專家
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from react_agent.graph import get_graph, save_graph_visualization
from react_agent.tools import parse_messages

# 載入環境變數
load_dotenv()

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_grafana_agent():
    """運行 Grafana 可觀測性診斷專家 Agent"""
    
    print("🚀 正在初始化 Grafana LLM Agent...")
    print("=" * 60)
    
    try:
        # 獲取編譯後的圖
        graph = await get_graph()
        
        # 保存圖形可視化
        save_graph_visualization(graph)
        
        print("✅ Grafana 可觀測性診斷專家已成功啟動！")
        print("=" * 60)
        
        # 配置對話線程
        config = {"configurable": {"thread_id": "1"}}
        
        # 測試查詢範例
        test_queries = [
            "幫我全面分析 sporty prod rum 環境的健康狀況，盡可能使用 loki 查看最近十分鐘的 log",
            "查看有關 kubernetes 的 dashboard",
            "列出所有可用的數據源",
            "分析最近的錯誤日誌模式"
        ]
        
        # 選擇要執行的查詢
        selected_query = test_queries[0]
        print(f"🔍 正在處理查詢: {selected_query}")
        print("=" * 60)
        
        # 執行查詢
        agent_response = await graph.ainvoke(
            {"messages": [HumanMessage(content=selected_query)]}, 
            config
        )
        
        # 解析並顯示所有消息
        print("\n📋 完整對話記錄:")
        parse_messages(agent_response['messages'])
        
        # 提取最終回應
        final_message = agent_response['messages'][-1]
        final_content = final_message.content if hasattr(final_message, 'content') else str(final_message)
        
        print(f"\n🎯 最終回應:")
        print("=" * 60)
        print(final_content)
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 執行過程中發生錯誤: {e}")
        print(f"❌ 錯誤詳情: {e}")
        print("\n💡 可能的解決方案:")
        print("1. 確保 Grafana MCP 服務正在運行")
        print("2. 檢查 .env 文件中的 API 金鑰")
        print("3. 確認 GRAFANA_MCP_URL 設定正確")


async def interactive_mode():
    """互動式模式"""
    print("🎯 Grafana Agent 互動式模式")
    print("輸入 'quit' 或 'exit' 退出")
    print("=" * 60)
    
    try:
        graph = await get_graph()
        config = {"configurable": {"thread_id": "interactive"}}
        
        while True:
            user_input = input("\n🔍 您的問題: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再見！")
                break
            
            if not user_input:
                continue
            
            try:
                print(f"\n⏳ 正在處理: {user_input}")
                print("-" * 40)
                
                result = await graph.ainvoke(
                    {"messages": [HumanMessage(content=user_input)]},
                    config
                )
                
                # 顯示最終回應
                final_message = result['messages'][-1]
                final_content = final_message.content if hasattr(final_message, 'content') else str(final_message)
                
                print(f"🤖 Agent 回應: {final_content}")
                
            except Exception as e:
                print(f"❌ 處理過程中發生錯誤: {e}")
                
    except Exception as e:
        logger.error(f"❌ 初始化失敗: {e}")
        print(f"❌ 無法啟動互動模式: {e}")


def main():
    """主函數"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_mode())
    else:
        asyncio.run(run_grafana_agent())


if __name__ == "__main__":
    main() 