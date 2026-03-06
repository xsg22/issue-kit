"""AI 助手适配层，支持不同编程助手的命令格式。"""

from .registry import AGENT_REGISTRY, get_agent_config

__all__ = ["AGENT_REGISTRY", "get_agent_config"]
