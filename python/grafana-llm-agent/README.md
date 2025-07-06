# Grafana LLM Agent - 基於 LangGraph 的可觀測性診斷專家

[![CI](https://github.com/langchain-ai/react-agent/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/langchain-ai/react-agent/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/langchain-ai/react-agent/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/langchain-ai/react-agent/actions/workflows/integration-tests.yml)
[![Open in - LangGraph Studio](https://img.shields.io/badge/Open_in-LangGraph_Studio-00324d.svg?logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4NS4zMzMiIGhlaWdodD0iODUuMzMzIiB2ZXJzaW9uPSIxLjAiIHZpZXdCb3g9IjAgMCA2NCA2NCI+PHBhdGggZD0iTTEzIDcuOGMtNi4zIDMuMS03LjEgNi4zLTYuOCAyNS43LjQgMjQuNi4zIDI0LjUgMjUuOSAyNC41QzU3LjUgNTggNTggNTcuNSA1OCAzMi4zIDU4IDcuMyA1Ni43IDYgMzIgNmMtMTIuOCAwLTE2LjEuMy0xOSAxLjhtMzcuNiAxNi42YzIuOCAyLjggMy40IDQuMiAzLjQgNy42cy0uNiA0LjgtMy40IDcuNkw0Ny4yIDQzSDE2LjhsLTMuNC0zLjRjLTQuOC00LjgtNC44LTEwLjQgMC0xNS4ybDMuNC0zLjRoMzAuNHoiLz48cGF0aCBkPSJNMTguOSAyNS42Yy0xLjEgMS4zLTEgMS43LjQgMi41LjkuNiAxLjcgMS44IDEuNyAyLjcgMCAxIC43IDIuOCAxLjYgNC4xIDEuNCAxLjkgMS40IDIuNS4zIDMuMi0xIC42LS42LjkgMS40LjkgMS41IDAgMi43LS41IDIuNy0xIDAtLjYgMS4xLS44IDIuNi0uNGwyLjYuNy0xLjgtMi45Yy01LjktOS4zLTkuNC0xMi4zLTExLjUtOS44TTM5IDI2YzAgMS4xLS45IDIuNS0yIDMuMi0yLjQgMS41LTIuNiAzLjQtLjUgNC4yLjguMyAyIDEuNyAyLjUgMy4xLjYgMS41IDEuNCAyLjMgMiAyIDEuNS0uOSAxLjItMy41LS40LTMuNS0yLjEgMC0yLjgtMi44LS44LTMuMyAxLjYtLjQgMS42LS41IDAtLjYtMS4xLS4xLTEuNS0uNi0xLjItMS42LjctMS43IDMuMy0yLjEgMy41LS41LjEuNS4yIDEuNi4zIDIuMiAwIC43LjkgMS40IDEuOSAxLjYgMi4xLjQgMi4zLTIuMyAyLTMuMi0uOC0uMy0yLTEuNy0yLjUtMy4xLTEuMS0zLTMtMy4zLTMtLjUiLz48L3N2Zz4=)](https://langgraph-studio.vercel.app/templates/open?githubUrl=https://github.com/langchain-ai/react-agent)

這個專案是基於 LangGraph 框架的 Grafana 可觀測性診斷專家，整合了 MCP (Model Context Protocol) 來提供強大的 Grafana 工具集成。

![Graph view in LangGraph studio UI](./static/studio_ui.png)

## 🎯 功能特色

這個 Grafana LLM Agent 具備以下核心功能：

1. **深度分析**: 使用 Chain of Thought 推理，逐步分解複雜問題
2. **多步驟工具調度**: 智能選擇和組合多個 Grafana 工具
3. **持續探索**: 不滿足於表面信息，深入挖掘根本原因
4. **專業領域知識**: 
   - 日誌分析和異常檢測
   - 性能指標監控和趨勢分析
   - 系統故障診斷和根因分析
   - 用戶行為和業務指標分析

## 🚀 快速開始

### 1. 環境設置

創建 `.env` 文件並設置必要的環境變數：

```env
# LLM API 金鑰（任選其一）
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Tavily 搜索 API Key（可選）
TAVILY_API_KEY=your_tavily_api_key_here

# Grafana MCP 服務器 URL
GRAFANA_MCP_URL=http://localhost:8001/sse

# LangSmith 追蹤（可選）
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_TRACING=true
```

### 2. 安裝依賴

```bash
cd python/grafana-llm-agent
pip install -e .
```

### 3. 啟動 Grafana MCP 服務

確保你的 Grafana MCP 服務正在運行（通常在 `http://localhost:8001/sse`）。

### 4. 運行 Agent

有多種方式來運行 agent：

#### 使用自定義執行腳本
```bash
# 單次查詢模式
python run_grafana_agent.py

# 互動式模式
python run_grafana_agent.py interactive
```

#### 使用 LangGraph Studio（推薦）
```bash
# 安裝 LangGraph CLI
pip install -U langgraph-cli

# 啟動 Studio
langgraph dev

# 訪問 http://localhost:8123
```

#### 使用標準 LangGraph 方式
```python
import asyncio
from react_agent.graph import get_graph
from langchain_core.messages import HumanMessage

async def main():
    graph = await get_graph()
    result = await graph.ainvoke({
        "messages": [HumanMessage(content="列出所有可用的數據源")]
    })
    print(result['messages'][-1].content)

asyncio.run(main())
```

## 🔧 可用工具

Agent 集成了以下 Grafana MCP 工具：

### Loki 工具
- `list_loki_label_names` - 列出 Loki 標籤名稱
- `list_loki_label_values` - 列出標籤值
- `query_loki_stats` - 查詢 Loki 統計信息
- `query_loki_logs` - 查詢 Loki 日誌

### Prometheus 工具
- `query_prometheus` - 查詢 Prometheus 指標
- `list_prometheus_metric_names` - 列出指標名稱
- `list_prometheus_label_names` - 列出標籤名稱
- `list_prometheus_label_values` - 列出標籤值
- `list_prometheus_metric_metadata` - 列出指標元數據

### Dashboard 工具
- `search_dashboards` - 搜索儀表板
- `get_dashboard_by_uid` - 根據 UID 獲取儀表板
- `update_dashboard` - 更新儀表板
- `get_dashboard_panel_queries` - 獲取面板查詢

### 數據源工具
- `list_datasources` - 列出數據源
- `get_datasource_by_uid` - 根據 UID 獲取數據源
- `get_datasource_by_name` - 根據名稱獲取數據源

## 🏗️ 架構說明

### 移植實現過程

我們將原始的 `agent.py` 成功移植到 LangGraph 框架，具體步驟如下：

1. **依賴管理** (`pyproject.toml`)
   - 添加 `langchain-mcp-adapters` 和 `google-generativeai`
   - 保持與原 LangGraph 模板的兼容性

2. **配置模組** (`configuration.py`)
   - 添加 `grafana_mcp_url` 配置
   - 添加 `grafana_tools` 工具列表配置
   - 保持 LangGraph 配置架構

3. **系統提示** (`prompts.py`)
   - 移植專業的 Grafana 診斷專家提示詞
   - 保持 LangGraph 的提示格式

4. **工具集成** (`tools.py`)
   - 集成 MCP 客戶端和工具管理
   - 保留原有的 Tavily 搜索功能
   - 添加動態工具載入功能
   - 集成消息解析功能

5. **圖結構** (`graph.py`)
   - 實現動態工具載入
   - 添加內存檢查點
   - 保持 ReAct 架構
   - 添加圖形可視化功能

6. **執行腳本** (`run_grafana_agent.py`)
   - 提供單次查詢和互動模式
   - 集成完整的錯誤處理
   - 保持與原始功能的兼容性

### 關鍵技術特點

- **異步優先**: 全面使用異步操作以提高性能
- **動態工具載入**: 支持運行時動態載入 MCP 工具
- **錯誤恢復**: 完整的錯誤處理和回退機制
- **可觀測性**: 詳細的日誌記錄和消息解析
- **配置靈活**: 支持多種 LLM 提供商和配置選項

## 🔍 使用範例

```python
# 查詢範例
test_queries = [
    "幫我全面分析 sporty prod rum 環境的健康狀況，使用 loki 查看最近十分鐘的 log",
    "查看有關 kubernetes 的 dashboard",
    "列出所有可用的數據源",
    "分析最近的錯誤日誌模式"
]
```

## 🛠️ 開發

### 運行測試

```bash
# 單元測試
pytest tests/unit_tests/ -v

# 集成測試
pytest tests/integration_tests/ -v

# 所有測試
pytest tests/ -v
```

### 代碼格式化

```bash
# 格式化代碼
make format

# 代碼檢查
make lint
```

## 📁 專案結構

```
python/grafana-llm-agent/
├── src/react_agent/
│   ├── __init__.py
│   ├── configuration.py    # 配置管理
│   ├── graph.py           # 主要圖結構
│   ├── prompts.py         # 系統提示詞
│   ├── state.py           # 狀態管理
│   ├── tools.py           # 工具集成
│   └── utils.py           # 工具函數
├── tests/                 # 測試文件
├── run_grafana_agent.py   # 執行腳本
├── pyproject.toml        # 專案配置
└── README.md             # 說明文件
```

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 許可證

MIT License - 詳見 [LICENSE](LICENSE) 文件。

---

## 🎯 下一步計劃

1. **增強工具集成**: 添加更多 Grafana API 支持
2. **優化性能**: 改進工具調用效率
3. **擴展功能**: 添加告警和通知功能
4. **改進 UI**: 開發更好的用戶界面
5. **文檔完善**: 添加更多使用案例和教程