"""
Token 预算管理器
控制上下文大小，防止超出模型限制
"""

import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BudgetConfig:
    """预算配置"""
    total_tokens: int = 128000  # 总 token 限制
    system_rules: float = 0.05  # 5% 系统规则
    cards: float = 0.15         # 15% 角色/世界观卡片
    canon: float = 0.10         # 10% 事实表
    summaries: float = 0.20     # 20% 前文摘要
    current_draft: float = 0.30 # 30% 当前草稿
    output_reserve: float = 0.20 # 20% 输出预留


class TokenBudgeter:
    """Token 预算管理器"""

    def __init__(self, config: Optional[BudgetConfig] = None):
        self.config = config or BudgetConfig()

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的 token 数
        简单估算：中文约 1.5 字符/token，英文约 4 字符/token
        """
        if not text:
            return 0

        # 分离中文和英文
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - chinese_chars

        # 估算 token 数
        chinese_tokens = chinese_chars / 1.5
        other_tokens = other_chars / 4

        return int(chinese_tokens + other_tokens)

    def get_budget(self, category: str) -> int:
        """获取某个类别的 token 预算"""
        ratios = {
            "system_rules": self.config.system_rules,
            "cards": self.config.cards,
            "canon": self.config.canon,
            "summaries": self.config.summaries,
            "current_draft": self.config.current_draft,
            "output_reserve": self.config.output_reserve,
        }

        ratio = ratios.get(category, 0.1)
        return int(self.config.total_tokens * ratio)

    def allocate_context(
        self,
        context: Dict[str, Any],
        priorities: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        根据预算分配上下文

        Args:
            context: 原始上下文字典
            priorities: 优先级顺序，默认 ["characters", "style", "rules", "facts", "summaries", "world"]

        Returns:
            裁剪后的上下文
        """
        if priorities is None:
            priorities = ["characters", "style", "rules", "facts", "summaries", "world"]

        # 计算各部分预算
        cards_budget = self.get_budget("cards")
        canon_budget = self.get_budget("canon")
        summaries_budget = self.get_budget("summaries")

        allocated = {
            "characters": [],
            "world": [],
            "style": context.get("style"),
            "rules": context.get("rules"),
            "facts": [],
            "summaries": []
        }

        current_tokens = {
            "cards": 0,
            "canon": 0,
            "summaries": 0
        }

        # 按优先级分配
        for category in priorities:
            if category == "characters":
                for char in context.get("characters", []):
                    char_text = self._serialize_character(char)
                    char_tokens = self.estimate_tokens(char_text)
                    if current_tokens["cards"] + char_tokens <= cards_budget:
                        allocated["characters"].append(char)
                        current_tokens["cards"] += char_tokens
                    else:
                        logger.debug(f"角色 {char.name} 被裁剪（超出预算）")
                        break

            elif category == "world":
                for world in context.get("world", []):
                    world_text = self._serialize_world(world)
                    world_tokens = self.estimate_tokens(world_text)
                    if current_tokens["cards"] + world_tokens <= cards_budget:
                        allocated["world"].append(world)
                        current_tokens["cards"] += world_tokens
                    else:
                        logger.debug(f"世界观 {world.name} 被裁剪（超出预算）")
                        break

            elif category == "style":
                # 文风卡通常很小，直接包含
                pass

            elif category == "rules":
                # 规则卡通常很小，直接包含
                pass

            elif category == "facts":
                for fact in context.get("facts", []):
                    fact_text = fact.statement
                    fact_tokens = self.estimate_tokens(fact_text)
                    if current_tokens["canon"] + fact_tokens <= canon_budget:
                        allocated["facts"].append(fact)
                        current_tokens["canon"] += fact_tokens
                    else:
                        logger.debug("事实被裁剪（超出预算）")
                        break

            elif category == "summaries":
                for summary in context.get("summaries", []):
                    summary_text = summary.summary
                    summary_tokens = self.estimate_tokens(summary_text)
                    if current_tokens["summaries"] + summary_tokens <= summaries_budget:
                        allocated["summaries"].append(summary)
                        current_tokens["summaries"] += summary_tokens
                    else:
                        logger.debug(f"摘要 {summary.chapter} 被裁剪（超出预算）")
                        break

        # 记录分配情况
        logger.info(
            f"Token 分配: cards={current_tokens['cards']}/{cards_budget}, "
            f"canon={current_tokens['canon']}/{canon_budget}, "
            f"summaries={current_tokens['summaries']}/{summaries_budget}"
        )

        return allocated

    def _serialize_character(self, char) -> str:
        """序列化角色卡为文本"""
        parts = [char.name, char.identity]
        if char.personality:
            parts.append(",".join(char.personality))
        if char.speech_pattern:
            parts.append(char.speech_pattern)
        return " ".join(parts)

    def _serialize_world(self, world) -> str:
        """序列化世界观卡为文本"""
        return f"{world.name} {world.description}"

    def check_budget(self, text: str, category: str) -> bool:
        """检查文本是否在预算内"""
        tokens = self.estimate_tokens(text)
        budget = self.get_budget(category)
        return tokens <= budget

    def truncate_to_budget(self, text: str, category: str) -> str:
        """将文本裁剪到预算内"""
        budget = self.get_budget(category)
        tokens = self.estimate_tokens(text)

        if tokens <= budget:
            return text

        # 按比例裁剪
        ratio = budget / tokens
        target_len = int(len(text) * ratio * 0.95)  # 留5%余量

        truncated = text[:target_len]
        logger.warning(f"文本被裁剪: {tokens} -> ~{budget} tokens")

        return truncated + "\n...(内容已裁剪)"


# 全局实例
_budgeter: Optional[TokenBudgeter] = None


def get_budgeter() -> TokenBudgeter:
    """获取全局预算管理器"""
    global _budgeter
    if _budgeter is None:
        _budgeter = TokenBudgeter()
    return _budgeter
