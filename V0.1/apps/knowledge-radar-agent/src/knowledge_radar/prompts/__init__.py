"""
Knowledge Radar Prompts

YAML Prompt 模板集合
"""

from typing import Dict, Any
import yaml
from pathlib import Path


PROMPTS_DIR = Path(__file__).parent


def load_prompt(prompt_name: str) -> Dict[str, Any]:
    """
    加载 prompt 模板
    
    Args:
        prompt_name: prompt 文件名（不含 .yaml 后缀）
    
    Returns:
        prompt 字典
    """
    prompt_path = PROMPTS_DIR / f"{prompt_name}.yaml"
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def format_user_prompt(prompt_name: str, **kwargs) -> str:
    """
    格式化用户提示
    
    Args:
        prompt_name: prompt 文件名
        **kwargs: 填充变量
    
    Returns:
        格式化后的用户提示
    """
    prompt = load_prompt(prompt_name)
    template = prompt.get("user_prompt_template", "")
    return template.format(**kwargs)


__all__ = ["load_prompt", "format_user_prompt", "PROMPTS_DIR"]
