import os
from typing import List, Optional
from .logger import logger

RULES_PATH = "config/black-rules.txt"

class ContentModerator:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ContentModerator, cls).__new__(cls)
            cls._instance.rules = []
            cls._instance.load_rules()
        return cls._instance

    def load_rules(self):
        """加载敏感词规则"""
        if not os.path.exists(RULES_PATH):
            logger.warning(f"Sensitive words file not found: {RULES_PATH}")
            return

        try:
            with open(RULES_PATH, 'r', encoding='utf-8') as f:
                # 读取非空行，去除首尾空格
                self.rules = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(self.rules)} sensitive word rules.")
        except Exception as e:
            logger.error(f"Failed to load sensitive words: {e}")

    def check_text(self, text: str) -> Optional[str]:
        """
        检查文本是否包含敏感词 (模糊匹配/子字符串匹配)
        
        Args:
            text: 待检查的文本
            
        Returns:
            str: 匹配到的第一个敏感词，如果没有则返回 None
        """
        if not text:
            return None
            
        text_lower = text.lower()
        for rule in self.rules:
            # 简单的子字符串匹配
            if rule.lower() in text_lower:
                return rule
        return None

# 全局实例
moderator = ContentModerator()
