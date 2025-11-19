#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""✅ БЛОК 7: ОБРАБОТКА ТЕКСТА (NLP)"""
import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)

class TextProcessor:
    """БЛОК 7: NLP обработка текста"""
    
    SERVICE_KEYWORDS = {
        "yacht": ["яхта", "катамаран", "лодка", "yacht", "boat"],
        "party": ["вечеринка", "праздник", "party", "celebration"],
        "vip": ["vip", "эксклюзив", "premium", "exclusive"],
        "excursion": ["экскурсия", "тур", "tour", "excursion"],
        "transfer": ["трансфер", "такси", "transfer", "taxi"]
    }
    
    POSITIVE_WORDS = ["спасибо", "отлично", "круто", "супер", "thanks", "great", "awesome"]
    NEGATIVE_WORDS = ["ужасно", "плохо", "нет", "bad", "terrible", "no", "horrible"]
    QUESTION_WORDS = ["как", "что", "когда", "где", "почему", "how", "what", "when", "where", "why"]
    
    @staticmethod
    def clean_text(text: str) -> str:
        text = text.strip().lower()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        logger.info("✅ БЛОК 7: Извлечение ключевых слов")
        text = TextProcessor.clean_text(text)
        keywords = []
        for service, words in TextProcessor.SERVICE_KEYWORDS.items():
            for word in words:
                if word in text:
                    keywords.append(service)
                    break
        return keywords
    
    @staticmethod
    def detect_sentiment(text: str) -> str:
        logger.info("✅ БЛОК 7: Анализ тональности")
        text = TextProcessor.clean_text(text)
        positive_count = sum(1 for word in TextProcessor.POSITIVE_WORDS if word in text)
        negative_count = sum(1 for word in TextProcessor.NEGATIVE_WORDS if word in text)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        return "neutral"
    
    @staticmethod
    def is_question(text: str) -> bool:
        logger.info("✅ БЛОК 7: Анализ типа сообщения")
        text = TextProcessor.clean_text(text)
        for word in TextProcessor.QUESTION_WORDS:
            if word in text:
                return True
        return text.endswith("?")
    
    @staticmethod
    def extract_entities(text: str) -> Dict[str, List[str]]:
        logger.info("✅ БЛОК 7: NLP извлечение сущностей")
        return {
            "services": TextProcessor.extract_keywords(text),
            "sentiments": [TextProcessor.detect_sentiment(text)],
            "numbers": re.findall(r'\d+', text)
        }
    
    @staticmethod
    def preprocess_message(text: str) -> Dict:
        logger.info("✅ БЛОК 7: Предварительная обработка (NLP)")
        return {
            "original": text,
            "cleaned": TextProcessor.clean_text(text),
            "is_question": TextProcessor.is_question(text),
            "sentiment": TextProcessor.detect_sentiment(text),
            "entities": TextProcessor.extract_entities(text),
            "keywords": TextProcessor.extract_keywords(text),
            "length": len(text),
            "word_count": len(text.split())
        }
    
    @staticmethod
    def detect_language(text: str) -> str:
        logger.info("✅ БЛОК 7: Определение языка")
        text = text.lower()
        if re.search(r'[а-яёА-ЯЁ]', text):
            return "ru"
        elif re.search(r'[\u0E00-\u0E7F]', text):
            return "th"
        elif re.search(r'[\u4E00-\u9FFF]', text):
            return "zh"
        return "en"
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        logger.info("✅ БЛОК 7: Токенизация")
        text = TextProcessor.clean_text(text)
        return text.split()

logger.info("✅ БЛОК 7: NLP обработка текста загружена")
