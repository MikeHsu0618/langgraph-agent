"""Define the configurable parameters for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Annotated, List
import os

from langchain_core.runnables import ensure_config
from langgraph.config import get_config

from react_agent import prompts


@dataclass(kw_only=True)
class Configuration:
    """The configuration for the agent."""

    system_prompt: str = field(
        default=prompts.SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt to use for the agent's interactions. "
            "This prompt sets the context and behavior for the agent."
        },
    )

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-4o-mini",
        metadata={
            "description": "The name of the language model to use for the agent's main interactions. "
            "Should be in the form: provider/model-name."
        },
    )

    max_search_results: int = field(
        default=10,
        metadata={
            "description": "The maximum number of search results to return for each search query."
        },
    )

    # Grafana MCP 相關配置
    grafana_mcp_url: str = field(
        default_factory=lambda: os.getenv("GRAFANA_MCP_URL", "http://localhost:8001/sse"),
        metadata={
            "description": "The URL of the Grafana MCP server."
        },
    )

    grafana_tools: List[str] = field(
        default_factory=lambda: [
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
        ],
        metadata={
            "description": "List of Grafana MCP tools to use."
        },
    )

    @classmethod
    def from_context(cls) -> Configuration:
        """Create a Configuration instance from a RunnableConfig object."""
        try:
            config = get_config()
        except RuntimeError:
            config = None
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})
