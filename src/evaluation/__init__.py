"""Shared evaluation API used by scripts, tests and notebooks."""
from .core import load_tasks, load_agent_module, evaluate_deterministic, evaluate_agents, repository_root
from .metrics import summarize_audit, family_summary
