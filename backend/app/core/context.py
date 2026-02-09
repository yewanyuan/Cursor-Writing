"""
上下文选择器
根据章节目标筛选最相关的信息
使用 TF-IDF 进行相似度检索
"""

import asyncio
import logging
import re
import math
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
from dataclasses import dataclass

from app.storage import CardStorage, CanonStorage, DraftStorage
from app.core.budgeter import get_budgeter
from app.utils.helpers import estimate_tokens

logger = logging.getLogger(__name__)


@dataclass
class ScoredItem:
    """带评分的条目"""
    item: Any
    score: float
    text: str


class TextSimilarity:
    """文本相似度计算器（基于 TF-IDF）"""

    # 中文停用词
    STOPWORDS = {
        "的", "了", "和", "是", "就", "都", "而", "及", "与", "着",
        "或", "一个", "没有", "我们", "你们", "他们", "它们", "这个",
        "那个", "这些", "那些", "自己", "什么", "这样", "那样", "如何",
        "可以", "因为", "所以", "但是", "然后", "如果", "虽然", "不过",
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "shall",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "under", "again", "further", "then", "once",
    }

    def __init__(self):
        self._idf_cache: Dict[str, float] = {}
        self._doc_count = 0

    def tokenize(self, text: str) -> List[str]:
        """分词"""
        if not text:
            return []

        # 中文按字符分割，英文按空格分割
        tokens = []

        # 提取中文词（简单的 n-gram）
        chinese_text = re.findall(r'[\u4e00-\u9fff]+', text)
        for segment in chinese_text:
            # 使用 bigram
            for i in range(len(segment)):
                if i + 2 <= len(segment):
                    tokens.append(segment[i:i+2])
                tokens.append(segment[i])

        # 提取英文词
        english_words = re.findall(r'[a-zA-Z]+', text.lower())
        tokens.extend(english_words)

        # 过滤停用词和短词
        tokens = [t for t in tokens if t not in self.STOPWORDS and len(t) > 1]

        return tokens

    def compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """计算词频 (TF)"""
        if not tokens:
            return {}

        counter = Counter(tokens)
        total = len(tokens)
        return {word: count / total for word, count in counter.items()}

    def compute_idf(self, documents: List[List[str]]) -> Dict[str, float]:
        """计算逆文档频率 (IDF)"""
        doc_count = len(documents)
        if doc_count == 0:
            return {}

        # 统计每个词在多少文档中出现
        word_doc_count: Dict[str, int] = Counter()
        for doc_tokens in documents:
            unique_tokens = set(doc_tokens)
            for token in unique_tokens:
                word_doc_count[token] += 1

        # 计算 IDF
        idf = {}
        for word, count in word_doc_count.items():
            idf[word] = math.log(doc_count / (1 + count)) + 1

        return idf

    def compute_tfidf(self, tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
        """计算 TF-IDF 向量"""
        tf = self.compute_tf(tokens)
        return {word: tf_val * idf.get(word, 1.0) for word, tf_val in tf.items()}

    def cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2:
            return 0.0

        # 计算点积
        dot_product = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in set(vec1) | set(vec2))

        # 计算模
        norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def rank_by_similarity(
        self,
        query: str,
        documents: List[Tuple[Any, str]],
        top_k: int = 10
    ) -> List[ScoredItem]:
        """
        根据相似度对文档排序

        Args:
            query: 查询文本
            documents: [(item, text), ...] 文档列表
            top_k: 返回前 k 个结果

        Returns:
            按相似度降序排列的 ScoredItem 列表
        """
        if not query or not documents:
            return [ScoredItem(item=item, score=0.0, text=text) for item, text in documents[:top_k]]

        # 分词
        query_tokens = self.tokenize(query)
        doc_tokens_list = [self.tokenize(text) for _, text in documents]

        # 计算 IDF
        all_docs = [query_tokens] + doc_tokens_list
        idf = self.compute_idf(all_docs)

        # 计算查询的 TF-IDF
        query_tfidf = self.compute_tfidf(query_tokens, idf)

        # 计算每个文档的相似度
        results = []
        for (item, text), doc_tokens in zip(documents, doc_tokens_list):
            doc_tfidf = self.compute_tfidf(doc_tokens, idf)
            similarity = self.cosine_similarity(query_tfidf, doc_tfidf)
            results.append(ScoredItem(item=item, score=similarity, text=text))

        # 按相似度降序排序
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:top_k]


class ContextSelector:
    """上下文选择器"""

    def __init__(
        self,
        card_storage: CardStorage,
        canon_storage: CanonStorage,
        draft_storage: DraftStorage
    ):
        self.cards = card_storage
        self.canon = canon_storage
        self.drafts = draft_storage
        self.similarity = TextSimilarity()
        self.budgeter = get_budgeter()

    async def select_for_writing(
        self,
        project_id: str,
        chapter: str,
        chapter_goal: str,
        characters: List[str] = None
    ) -> Dict[str, Any]:
        """
        为写作选择上下文

        使用 TF-IDF 相似度返回与章节目标最相关的信息
        """
        context = {
            "characters": [],
            "world": [],
            "style": None,
            "rules": None,
            "facts": [],
            "summaries": []
        }

        # 并行获取所有基础数据
        char_names_task = None
        if not characters:
            char_names_task = self.cards.list_characters(project_id)

        world_names_task = self.cards.list_world_cards(project_id)
        style_task = self.cards.get_style(project_id)
        rules_task = self.cards.get_rules(project_id)
        facts_task = self.canon.get_facts(project_id)
        summaries_task = self.drafts.get_previous_summaries(project_id, chapter, limit=20)

        # 并行执行所有任务
        tasks = [world_names_task, style_task, rules_task, facts_task, summaries_task]
        if char_names_task:
            tasks.append(char_names_task)

        results = await asyncio.gather(*tasks)

        world_names = results[0]
        context["style"] = results[1]
        context["rules"] = results[2]
        all_facts = results[3]
        all_summaries = results[4]
        char_names = results[5] if char_names_task else characters

        # 并行获取角色卡和世界观卡详情
        char_card_tasks = [
            self.cards.get_character(project_id, name)
            for name in char_names
        ]
        world_card_tasks = [
            self.cards.get_world_card(project_id, name)
            for name in world_names
        ]

        all_card_results = await asyncio.gather(*char_card_tasks, *world_card_tasks)

        char_cards = [c for c in all_card_results[:len(char_card_tasks)] if c]
        world_cards = [c for c in all_card_results[len(char_card_tasks):] if c]

        # 1. 角色卡 - 按相关性选择
        if char_cards and chapter_goal:
            char_docs = [(card, f"{card.name} {card.identity} {' '.join(card.personality)} {card.speech_pattern}")
                        for card in char_cards]
            ranked_chars = self.similarity.rank_by_similarity(chapter_goal, char_docs, top_k=10)
            context["characters"] = [item.item for item in ranked_chars if item.score > 0.05]
            # 至少保留指定的角色
            if characters:
                for card in char_cards:
                    if card.name in characters and card not in context["characters"]:
                        context["characters"].append(card)
        else:
            context["characters"] = char_cards[:10]

        # 2. 世界观卡 - 使用相似度排序
        if world_cards and chapter_goal:
            world_docs = [(card, f"{card.name} {card.category} {card.description}")
                         for card in world_cards]
            ranked_world = self.similarity.rank_by_similarity(chapter_goal, world_docs, top_k=5)
            context["world"] = [item.item for item in ranked_world if item.score > 0.03]

        # 如果没匹配到，至少取前3个
        if not context["world"] and world_cards:
            context["world"] = world_cards[:3]

        # 4. 事实 - 使用 token 预算动态分配，而非硬编码数量
        if all_facts:
            # 按优先级排序：critical > normal > minor，然后按时间倒序
            priority_order = {"critical": 0, "normal": 1, "minor": 2}
            sorted_facts = sorted(
                all_facts,
                key=lambda f: (priority_order.get(f.importance, 1), -all_facts.index(f))
            )

            # 使用 token 预算选取事实（预算 2000 tokens）
            fact_token_budget = 2000
            selected_facts = []
            used_tokens = 0

            for fact in sorted_facts:
                fact_tokens = estimate_tokens(fact.statement)
                if used_tokens + fact_tokens > fact_token_budget:
                    break
                selected_facts.append(fact)
                used_tokens += fact_tokens

            # 如果按优先级选取的太少，补充最近的事实
            if len(selected_facts) < 5 and len(all_facts) > len(selected_facts):
                remaining_budget = fact_token_budget - used_tokens
                recent_facts = [f for f in all_facts[-10:] if f not in selected_facts]
                for fact in recent_facts:
                    fact_tokens = estimate_tokens(fact.statement)
                    if used_tokens + fact_tokens > fact_token_budget:
                        break
                    selected_facts.append(fact)
                    used_tokens += fact_tokens

            # 对较早的事实按相关性排序（如果有章节目标）
            if chapter_goal and len(selected_facts) > 5:
                fact_docs = [(f, f.statement) for f in selected_facts]
                ranked_facts = self.similarity.rank_by_similarity(chapter_goal, fact_docs, top_k=len(selected_facts))
                context["facts"] = [item.item for item in ranked_facts]
            else:
                context["facts"] = selected_facts

        # 5. 前文摘要 - 使用相似度 + 距离衰减
        if all_summaries:
            if chapter_goal:
                summary_docs = [(s, s.summary) for s in all_summaries]
                ranked_summaries = self.similarity.rank_by_similarity(chapter_goal, summary_docs, top_k=5)

                # 结合相关性和距离（最近的摘要权重更高）
                for i, item in enumerate(ranked_summaries):
                    # 找到原始位置，计算距离权重
                    orig_idx = next((j for j, s in enumerate(all_summaries) if s.chapter == item.item.chapter), len(all_summaries))
                    distance_weight = 1.0 / (1 + orig_idx * 0.2)  # 距离越近权重越高
                    item.score = item.score * 0.7 + distance_weight * 0.3  # 70% 相关性 + 30% 距离

                ranked_summaries.sort(key=lambda x: x.score, reverse=True)
                context["summaries"] = [item.item for item in ranked_summaries[:5]]
            else:
                context["summaries"] = all_summaries[:5]

        # 6. 应用 Token 预算裁剪
        context = self.budgeter.allocate_context(context)

        logger.info(
            f"上下文选择: {len(context['characters'])} 角色, "
            f"{len(context['world'])} 世界观, "
            f"{len(context['facts'])} 事实, "
            f"{len(context['summaries'])} 摘要"
        )

        return context

    def format_context(self, context: Dict[str, Any]) -> str:
        """将上下文格式化为文本"""
        parts = []

        # 角色
        if context["characters"]:
            parts.append("=== 角色 ===")
            for c in context["characters"]:
                parts.append(f"【{c.name}】{c.identity}")
                if c.personality:
                    parts.append(f"  性格: {', '.join(c.personality[:3])}")
                if c.speech_pattern:
                    parts.append(f"  说话风格: {c.speech_pattern}")

        # 世界观
        if context["world"]:
            parts.append("\n=== 世界观 ===")
            for w in context["world"]:
                parts.append(f"【{w.name}】{w.description[:100]}")

        # 文风
        if context["style"]:
            parts.append("\n=== 文风 ===")
            s = context["style"]
            parts.append(f"叙事距离: {s.narrative_distance}, 节奏: {s.pacing}")
            if s.sentence_style:
                parts.append(f"句式: {s.sentence_style}")

        # 规则
        if context["rules"]:
            r = context["rules"]
            if r.donts:
                parts.append("\n=== 禁止事项 ===")
                for d in r.donts[:5]:
                    parts.append(f"- {d}")

        # 事实
        if context["facts"]:
            parts.append("\n=== 已知事实 ===")
            for f in context["facts"][-10:]:
                parts.append(f"- {f.statement}")

        # 前文摘要
        if context["summaries"]:
            parts.append("\n=== 前文摘要 ===")
            for s in context["summaries"]:
                parts.append(f"【{s.chapter}】{s.summary}")

        return "\n".join(parts)
