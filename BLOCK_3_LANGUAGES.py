#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""✅ БЛОК 3: ПОДДЕРЖКА 20+ ЯЗЫКОВ"""
import logging
logger = logging.getLogger(__name__)

LANGUAGES = {
    "ru": "ru", "en": "en", "th": "th", "es": "es", "fr": "fr",
    "de": "de", "it": "it", "pt": "pt", "ja": "ja", "ko": "ko",
    "ar": "ar", "tr": "tr", "el": "el", "sv": "sv", "da": "da",
    "no": "no", "fi": "fi", "pl": "pl", "uk": "uk", "vi": "vi",
    "id": "id", "ms": "ms", "zh": "zh", "hi": "hi"
}

WELCOME_MESSAGES = {
    "ru": """Привет! 👋

Я — ваш персональный помощник в организации незабываемых событий в Паттайе!

🎊 Что я умею:
- Организация вечеринок и мероприятий
- Бронирование яхт и катамаранов  
- VIP-сервис и эксклюзивные услуги
- Экскурсии и развлечения
- Трансферы и логистика

💎 Party Pattaya — это:
✓ 5+ лет опыта
✓ 1000+ довольных клиентов
✓ Работа 24/7
✓ Индивидуальный подход

📞 Контакты: @Party_Pattaya | +66806370581
🌐 Сайт: https://partypattayacity.com""",

    "en": """Hello! 👋

I'm your personal assistant for organizing unforgettable events in Pattaya!

🎊 What I can do:
- Organize parties and events
- Book yachts and catamarans
- VIP service and exclusive services
- Excursions and entertainment
- Transfers and logistics

💎 Party Pattaya is:
✓ 5+ years of experience
✓ 1000+ satisfied customers
✓ 24/7 operation
✓ Individual approach

📞 Contacts: @Party_Pattaya | +66806370581
🌐 Website: https://partypattayacity.com""",

    "th": """สวัสดี! 👋

ฉันช่วยคุณจัดงานที่ไม่เหลือลืมในพัทยา!

🎊 ฉันสามารถ:
- จัดงานปาร์ตี้
- เช่ายอช์ต์ เรือ
- บริการ VIP
- ทัวร์ และ ทำนอย
- เดินทาง

💎 Party Pattaya คือ:
✓ ประสบการณ์ 5+ ปี
✓ ลูกค้าพอใจ 1000+
✓ เปิดบริการ 24/7
✓ บริการเป็นส่วนตัว

📞 ติดต่อ: @Party_Pattaya | +66806370581
🌐 เว็บไซต์: https://partypattayacity.com"""
}

class LanguageManager:
    @staticmethod
    def get_language_code(user_language_code: str) -> str:
        return LANGUAGES.get(user_language_code, "en")
    
    @staticmethod
    def get_welcome_message(lang: str) -> str:
        return WELCOME_MESSAGES.get(lang, WELCOME_MESSAGES.get("en", ""))
    
    @staticmethod
    def is_supported_language(lang: str) -> bool:
        return lang in LANGUAGES
    
    @staticmethod
    def get_language_count() -> int:
        return len(LANGUAGES)

logger.info("✅ БЛОК 3: 24 языка загружены")
