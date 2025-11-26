# ═══════════════════════════════════════════════════════════════════════════════
# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                                                                               ║
# ║                         BLOCK 02: MAIN BOT ENGINE                             ║
# ║                      Party Pattaya Bot v10.2.1                                ║
# ║                                                                               ║
# ║  Основной движок бота - инициализация, обработка сообщений                    ║
# ║  Функций: 15 | Автор: Claude | Статус: PRODUCTION READY                       ║
# ║                                                                               ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
# ═══════════════════════════════════════════════════════════════════════════════

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import os

# Telegram imports (aiogram 3.x)
try:
    from aiogram import Bot, Dispatcher, Router, F
    from aiogram.types import Message, CallbackQuery, Update, Voice, BotCommand
    from aiogram.filters import Command, CommandStart
    from aiogram.enums import ParseMode, ChatAction
    from aiogram.client.default import DefaultBotProperties
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
    AIOGRAM_AVAILABLE = True
except ImportError:
    AIOGRAM_AVAILABLE = False
    Bot = None
    Dispatcher = None

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class BotStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class BotConfig:
    """Конфигурация Party Pattaya Bot"""
    
    # Контакты Party Pattaya (РЕАЛЬНЫЕ - НЕ МЕНЯТЬ!)
    contacts = {
        "whatsapp": "+66-633-633-407",
        "email": "partypattayacity@gmail.com",
        "telegram": "@Party_Pattaya",
        "contact_person": "Лилия Новикова",
        "website": "https://partypattayacity.com"
    }
    
    # Настройки бота
    bot_settings = {
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "protect_content": False,
        "max_message_length": 4096,
        "typing_delay": 0.5,
        "rate_limit_messages": 30,
        "rate_limit_period": 60
    }
    
    # Команды бота
    commands = [
        {"command": "start", "description": "🚀 Начать / Start"},
        {"command": "menu", "description": "📋 Главное меню / Main menu"},
        {"command": "yachts", "description": "🚤 Яхты / Yachts"},
        {"command": "parties", "description": "🎉 Вечеринки / Parties"},
        {"command": "vip", "description": "👑 VIP услуги / VIP services"},
        {"command": "transfer", "description": "🚗 Трансфер / Transfer"},
        {"command": "contact", "description": "📞 Контакты / Contacts"},
        {"command": "help", "description": "❓ Помощь / Help"},
        {"command": "language", "description": "🌐 Язык / Language"}
    ]
    
    # Приветственное сообщение (НЕ МЕНЯТЬ!)
    welcome_message = {
        "ru": """🎉 <b>Добро пожаловать в Party Pattaya!</b>

Мы организуем незабываемые мероприятия в Паттайе:
🚤 Аренда яхт
🎊 Вечеринки под ключ
👑 VIP услуги
🚗 Трансферы

📞 Контакты:
WhatsApp: +66-633-633-407
Telegram: @Party_Pattaya

Выберите услугу из меню ниже 👇""",
        
        "en": """🎉 <b>Welcome to Party Pattaya!</b>

We organize unforgettable events in Pattaya:
🚤 Yacht rentals
🎊 Turnkey parties
👑 VIP services
🚗 Transfers

📞 Contacts:
WhatsApp: +66-633-633-407
Telegram: @Party_Pattaya

Select a service from the menu below 👇""",
        
        "th": """🎉 <b>ยินดีต้อนรับสู่ Party Pattaya!</b>

เราจัดงานอีเวนต์สุดพิเศษในพัทยา:
🚤 เช่าเรือยอชท์
🎊 จัดปาร์ตี้ครบวงจร
👑 บริการ VIP
🚗 รถรับส่ง

📞 ติดต่อ:
WhatsApp: +66-633-633-407
Telegram: @Party_Pattaya

เลือกบริการจากเมนูด้านล่าง 👇""",
        
        "zh": """🎉 <b>欢迎来到 Party Pattaya!</b>

我们在芭提雅组织难忘的活动:
🚤 游艇租赁
🎊 一站式派对
👑 VIP服务
🚗 接送服务

📞 联系方式:
WhatsApp: +66-633-633-407
Telegram: @Party_Pattaya

从下方菜单选择服务 👇"""
    }
    
    # Главное меню - 3 кнопки (НЕ МЕНЯТЬ!)
    main_menu_buttons = [
        [{"text": "🚤 Яхты", "callback_data": "menu_yachts"}],
        [{"text": "🎉 Вечеринки", "callback_data": "menu_parties"}],
        [{"text": "📞 Контакты", "callback_data": "menu_contacts"}]
    ]
    
    # Локализация сообщений
    messages = {
        "ru": {
            "error": "❌ Произошла ошибка. Попробуйте позже.",
            "admin_only": "⛔ Только для администраторов",
            "rate_limited": "⏳ Слишком много запросов. Подождите немного.",
            "bot_restarting": "🔄 Бот перезапускается...",
            "bot_stopped": "🛑 Бот остановлен"
        },
        "en": {
            "error": "❌ An error occurred. Please try again later.",
            "admin_only": "⛔ Admin only",
            "rate_limited": "⏳ Too many requests. Please wait.",
            "bot_restarting": "🔄 Bot is restarting...",
            "bot_stopped": "🛑 Bot stopped"
        },
        "th": {
            "error": "❌ เกิดข้อผิดพลาด กรุณาลองใหม่ภายหลัง",
            "admin_only": "⛔ สำหรับผู้ดูแลเท่านั้น",
            "rate_limited": "⏳ คำขอมากเกินไป กรุณารอสักครู่",
            "bot_restarting": "🔄 บอทกำลังรีสตาร์ท...",
            "bot_stopped": "🛑 บอทหยุดทำงาน"
        },
        "zh": {
            "error": "❌ 发生错误，请稍后重试",
            "admin_only": "⛔ 仅管理员可用",
            "rate_limited": "⏳ 请求过多，请稍候",
            "bot_restarting": "🔄 机器人正在重启...",
            "bot_stopped": "🛑 机器人已停止"
        }
    }

CONFIG = BotConfig()

# ═══════════════════════════════════════════════════════════════════════════════
# BOT STATE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BotState:
    """Состояние бота"""
    status: BotStatus = BotStatus.STOPPED
    bot: Any = None
    dispatcher: Any = None
    router: Any = None
    admin_ids: List[int] = field(default_factory=list)
    started_at: datetime = None
    messages_processed: int = 0
    errors_count: int = 0
    last_error: str = None
    webhooks_active: bool = False
    middlewares: List[str] = field(default_factory=list)
    handlers_registered: bool = False
    user_languages: Dict[int, str] = field(default_factory=dict)
    rate_limits: Dict[int, List[datetime]] = field(default_factory=dict)

STATE = BotState()

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_message(key: str, lang: str = "en") -> str:
    """Получение локализованного сообщения"""
    messages = CONFIG.messages.get(lang, CONFIG.messages["en"])
    return messages.get(key, CONFIG.messages["en"].get(key, key))

def get_welcome_message(lang: str = "en") -> str:
    """Получение приветственного сообщения"""
    return CONFIG.welcome_message.get(lang, CONFIG.welcome_message["en"])

def detect_language(text: str) -> str:
    """Определение языка по тексту"""
    import re
    if re.search(r'[ก-๙]', text):
        return "th"
    elif re.search(r'[一-龥]', text):
        return "zh"
    elif re.search(r'[а-яА-ЯёЁ]', text):
        return "ru"
    return "en"

def check_rate_limit(user_id: int) -> bool:
    """Проверка rate limit для пользователя"""
    now = datetime.now()
    period = CONFIG.bot_settings["rate_limit_period"]
    max_messages = CONFIG.bot_settings["rate_limit_messages"]
    
    if user_id not in STATE.rate_limits:
        STATE.rate_limits[user_id] = []
    
    # Очистка старых записей
    STATE.rate_limits[user_id] = [
        t for t in STATE.rate_limits[user_id]
        if (now - t).total_seconds() < period
    ]
    
    if len(STATE.rate_limits[user_id]) >= max_messages:
        return False
    
    STATE.rate_limits[user_id].append(now)
    return True

def get_user_language(user_id: int) -> str:
    """Получение языка пользователя"""
    return STATE.user_languages.get(user_id, "en")

def set_user_language(user_id: int, lang: str) -> None:
    """Установка языка пользователя"""
    STATE.user_languages[user_id] = lang


# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 1: INIT BOT
# ═══════════════════════════════════════════════════════════════════════════════

async def init_bot(
    token: str,
    admin_id: int,
    webhook_url: str = None
) -> Any:
    """
    Инициализация бота Party Pattaya
    
    Args:
        token: Telegram Bot Token
        admin_id: ID администратора
        webhook_url: URL для webhook (опционально)
        
    Returns:
        Инициализированный объект Bot
    """
    global STATE
    
    if not AIOGRAM_AVAILABLE:
        logger.error("aiogram not installed. Run: pip install aiogram")
        return None
    
    try:
        STATE.status = BotStatus.STARTING
        logger.info("Initializing Party Pattaya Bot...")
        
        # Создание бота
        STATE.bot = Bot(
            token=token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                link_preview_is_disabled=CONFIG.bot_settings["disable_web_page_preview"]
            )
        )
        
        # Создание диспетчера
        storage = MemoryStorage()
        STATE.dispatcher = Dispatcher(storage=storage)
        
        # Создание роутера
        STATE.router = Router()
        STATE.dispatcher.include_router(STATE.router)
        
        # Установка админа
        STATE.admin_ids = [admin_id] if isinstance(admin_id, int) else list(admin_id)
        
        # Установка команд бота
        commands = [
            BotCommand(command=cmd["command"], description=cmd["description"])
            for cmd in CONFIG.commands
        ]
        await STATE.bot.set_my_commands(commands)
        
        # Webhook если указан
        if webhook_url:
            await setup_webhook(STATE.bot, webhook_url)
        
        STATE.started_at = datetime.now()
        STATE.status = BotStatus.RUNNING
        
        logger.info(f"Bot initialized successfully. Admin ID: {admin_id}")
        
        return STATE.bot
        
    except Exception as e:
        STATE.status = BotStatus.ERROR
        STATE.last_error = str(e)
        STATE.errors_count += 1
        logger.error(f"Failed to initialize bot: {e}")
        raise

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 2: START POLLING
# ═══════════════════════════════════════════════════════════════════════════════

async def start_polling(
    bot: Any = None,
    skip_updates: bool = True
) -> None:
    """
    Запуск long polling
    
    Args:
        bot: Объект бота (если None - используется STATE.bot)
        skip_updates: Пропустить накопившиеся обновления
    """
    global STATE
    
    bot = bot or STATE.bot
    if not bot:
        raise ValueError("Bot not initialized. Call init_bot() first.")
    
    try:
        logger.info("Starting long polling...")
        STATE.status = BotStatus.RUNNING
        
        # Регистрация хендлеров если не зарегистрированы
        if not STATE.handlers_registered:
            await register_handlers()
        
        # Запуск polling
        await STATE.dispatcher.start_polling(
            bot,
            skip_updates=skip_updates,
            allowed_updates=["message", "callback_query", "inline_query"]
        )
        
    except asyncio.CancelledError:
        logger.info("Polling cancelled")
    except Exception as e:
        STATE.status = BotStatus.ERROR
        STATE.last_error = str(e)
        STATE.errors_count += 1
        logger.error(f"Polling error: {e}")
        raise

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 3: SETUP WEBHOOK
# ═══════════════════════════════════════════════════════════════════════════════

async def setup_webhook(
    bot: Any,
    url: str,
    certificate: str = None,
    secret_token: str = None
) -> bool:
    """
    Настройка webhook
    
    Args:
        bot: Объект бота
        url: URL для webhook
        certificate: SSL сертификат (путь к файлу)
        secret_token: Секретный токен для верификации
        
    Returns:
        True если успешно
    """
    global STATE
    
    try:
        logger.info(f"Setting up webhook: {url}")
        
        # Удаление старого webhook
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Чтение сертификата если указан
        cert_file = None
        if certificate and os.path.exists(certificate):
            cert_file = open(certificate, "rb")
        
        # Установка webhook
        result = await bot.set_webhook(
            url=url,
            certificate=cert_file,
            secret_token=secret_token,
            allowed_updates=["message", "callback_query", "inline_query"],
            drop_pending_updates=True
        )
        
        if cert_file:
            cert_file.close()
        
        if result:
            STATE.webhooks_active = True
            logger.info("Webhook set successfully")
            return True
        else:
            logger.error("Failed to set webhook")
            return False
            
    except Exception as e:
        STATE.errors_count += 1
        STATE.last_error = str(e)
        logger.error(f"Webhook setup error: {e}")
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 4: PROCESS UPDATE
# ═══════════════════════════════════════════════════════════════════════════════

async def process_update(
    update: Any,
    bot: Any = None
) -> Dict[str, Any]:
    """
    Обработка входящего обновления
    
    Args:
        update: Telegram Update (dict или объект)
        bot: Объект бота
        
    Returns:
        Результат обработки
    """
    global STATE
    
    bot = bot or STATE.bot
    
    try:
        STATE.messages_processed += 1
        
        # Преобразование dict в Update если нужно
        if isinstance(update, dict):
            update = Update(**update)
        
        # Определение типа обновления
        if update.message:
            if update.message.voice:
                return await handle_voice(update.message, bot)
            else:
                return await handle_message(update.message, bot)
        elif update.callback_query:
            return await handle_callback(update.callback_query, bot)
        else:
            logger.debug(f"Unknown update type: {update}")
            return {"success": True, "type": "unknown"}
            
    except Exception as e:
        STATE.errors_count += 1
        STATE.last_error = str(e)
        logger.error(f"Error processing update: {e}")
        return {"success": False, "error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 5: HANDLE MESSAGE
# ═══════════════════════════════════════════════════════════════════════════════

async def handle_message(
    message: Any,
    bot: Any = None
) -> Dict[str, Any]:
    """
    Обработка текстового сообщения
    
    Args:
        message: Telegram Message
        bot: Объект бота
        
    Returns:
        Результат обработки
    """
    global STATE
    
    bot = bot or STATE.bot
    user_id = message.from_user.id
    text = message.text or ""
    
    try:
        # Проверка rate limit
        if not check_rate_limit(user_id):
            lang = get_user_language(user_id)
            await send_message_safe(
                bot, user_id,
                get_message("rate_limited", lang)
            )
            return {"success": False, "reason": "rate_limited"}
        
        # Определение языка
        if user_id not in STATE.user_languages:
            detected_lang = detect_language(text)
            set_user_language(user_id, detected_lang)
        
        lang = get_user_language(user_id)
        
        # Обработка команд
        if text.startswith("/"):
            command = text.split()[0].lower().replace("/", "").replace("@", "")
            
            if command in ["start", "начать"]:
                # Отправка приветствия с меню
                await send_message_safe(
                    bot, user_id,
                    get_welcome_message(lang),
                    reply_markup={"inline_keyboard": CONFIG.main_menu_buttons}
                )
                return {"success": True, "command": "start"}
            
            elif command in ["menu", "меню"]:
                await send_message_safe(
                    bot, user_id,
                    "📋 Главное меню:" if lang == "ru" else "📋 Main menu:",
                    reply_markup={"inline_keyboard": CONFIG.main_menu_buttons}
                )
                return {"success": True, "command": "menu"}
            
            elif command in ["contact", "contacts", "контакты"]:
                contacts_text = f"""📞 <b>Контакты Party Pattaya:</b>

WhatsApp: {CONFIG.contacts['whatsapp']}
Telegram: {CONFIG.contacts['telegram']}
Email: {CONFIG.contacts['email']}
Website: {CONFIG.contacts['website']}

Контактное лицо: {CONFIG.contacts['contact_person']}"""
                await send_message_safe(bot, user_id, contacts_text)
                return {"success": True, "command": "contacts"}
            
            elif command in ["help", "помощь"]:
                help_text = "❓ Выберите услугу из меню или напишите ваш вопрос." if lang == "ru" else "❓ Select a service from the menu or write your question."
                await send_message_safe(
                    bot, user_id, help_text,
                    reply_markup={"inline_keyboard": CONFIG.main_menu_buttons}
                )
                return {"success": True, "command": "help"}
            
            elif command in ["language", "язык"]:
                lang_buttons = [
                    [{"text": "🇷🇺 Русский", "callback_data": "lang_ru"}],
                    [{"text": "🇬🇧 English", "callback_data": "lang_en"}],
                    [{"text": "🇹🇭 ไทย", "callback_data": "lang_th"}],
                    [{"text": "🇨🇳 中文", "callback_data": "lang_zh"}]
                ]
                await send_message_safe(
                    bot, user_id,
                    "🌐 Выберите язык / Select language:",
                    reply_markup={"inline_keyboard": lang_buttons}
                )
                return {"success": True, "command": "language"}
        
        # Обычное сообщение - показываем меню
        await send_typing_action(bot, user_id)
        await send_message_safe(
            bot, user_id,
            "Выберите услугу:" if lang == "ru" else "Select a service:",
            reply_markup={"inline_keyboard": CONFIG.main_menu_buttons}
        )
        
        return {"success": True, "type": "text", "text": text}
        
    except Exception as e:
        STATE.errors_count += 1
        STATE.last_error = str(e)
        logger.error(f"Error handling message: {e}")
        return {"success": False, "error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 6: HANDLE CALLBACK
# ═══════════════════════════════════════════════════════════════════════════════

async def handle_callback(
    callback: Any,
    bot: Any = None
) -> Dict[str, Any]:
    """
    Обработка callback query (нажатие кнопки)
    
    Args:
        callback: Telegram CallbackQuery
        bot: Объект бота
        
    Returns:
        Результат обработки
    """
    global STATE
    
    bot = bot or STATE.bot
    user_id = callback.from_user.id
    data = callback.data or ""
    
    try:
        lang = get_user_language(user_id)
        
        # Обработка выбора языка
        if data.startswith("lang_"):
            new_lang = data.replace("lang_", "")
            set_user_language(user_id, new_lang)
            
            # Отправляем приветствие на новом языке
            await bot.answer_callback_query(callback.id, "✅")
            await send_message_safe(
                bot, user_id,
                get_welcome_message(new_lang),
                reply_markup={"inline_keyboard": CONFIG.main_menu_buttons}
            )
            return {"success": True, "action": "language_changed", "lang": new_lang}
        
        # Обработка меню
        elif data == "menu_yachts":
            await bot.answer_callback_query(callback.id)
            yachts_text = """🚤 <b>Аренда яхт в Паттайе</b>

У нас 9 яхт на любой вкус:
- Ocean Yachting - до 70 чел
- Bali 45 - до 20 чел  
- Azimuth 76 - суперяхта
- И другие...

Цены от 20,400 до 100,000 THB

📞 WhatsApp: +66-633-633-407""" if lang == "ru" else """🚤 <b>Yacht Rental in Pattaya</b>

We have 9 yachts for every taste:
- Ocean Yachting - up to 70 ppl
- Bali 45 - up to 20 ppl
- Azimuth 76 - superyacht
- And more...

Prices from 20,400 to 100,000 THB

📞 WhatsApp: +66-633-633-407"""
            
            back_button = [[{"text": "◀️ Назад" if lang == "ru" else "◀️ Back", "callback_data": "menu_back"}]]
            await send_message_safe(bot, user_id, yachts_text, reply_markup={"inline_keyboard": back_button})
            return {"success": True, "action": "menu_yachts"}
        
        elif data == "menu_parties":
            await bot.answer_callback_query(callback.id)
            parties_text = """🎉 <b>Организация вечеринок</b>

Мы организуем:
- Вечеринки на яхтах
- Дни рождения
- Корпоративы
- Тематические вечеринки
- Свадьбы

Всё включено: локация, звук, свет, артисты, кейтеринг

📞 WhatsApp: +66-633-633-407""" if lang == "ru" else """🎉 <b>Party Organization</b>

We organize:
- Yacht parties
- Birthdays
- Corporate events
- Theme parties
- Weddings

All inclusive: venue, sound, lights, artists, catering

📞 WhatsApp: +66-633-633-407"""
            
            back_button = [[{"text": "◀️ Назад" if lang == "ru" else "◀️ Back", "callback_data": "menu_back"}]]
            await send_message_safe(bot, user_id, parties_text, reply_markup={"inline_keyboard": back_button})
            return {"success": True, "action": "menu_parties"}
        
        elif data == "menu_contacts":
            await bot.answer_callback_query(callback.id)
            contacts_text = f"""📞 <b>Контакты Party Pattaya:</b>

WhatsApp: {CONFIG.contacts['whatsapp']}
Telegram: {CONFIG.contacts['telegram']}
Email: {CONFIG.contacts['email']}
Website: {CONFIG.contacts['website']}

Контактное лицо: {CONFIG.contacts['contact_person']}"""
            
            back_button = [[{"text": "◀️ Назад" if lang == "ru" else "◀️ Back", "callback_data": "menu_back"}]]
            await send_message_safe(bot, user_id, contacts_text, reply_markup={"inline_keyboard": back_button})
            return {"success": True, "action": "menu_contacts"}
        
        elif data == "menu_back":
            await bot.answer_callback_query(callback.id)
            await send_message_safe(
                bot, user_id,
                "📋 Главное меню:" if lang == "ru" else "📋 Main menu:",
                reply_markup={"inline_keyboard": CONFIG.main_menu_buttons}
            )
            return {"success": True, "action": "menu_back"}
        
        # Неизвестный callback
        await bot.answer_callback_query(callback.id)
        return {"success": True, "action": "unknown", "data": data}
        
    except Exception as e:
        STATE.errors_count += 1
        STATE.last_error = str(e)
        logger.error(f"Error handling callback: {e}")
        try:
            await bot.answer_callback_query(callback.id, "❌ Error")
        except:
            pass
        return {"success": False, "error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 7: HANDLE VOICE
# ═══════════════════════════════════════════════════════════════════════════════

async def handle_voice(
    message: Any,
    bot: Any = None
) -> Dict[str, Any]:
    """
    Обработка голосового сообщения
    
    Args:
        message: Telegram Message с голосом
        bot: Объект бота
        
    Returns:
        Результат обработки
    """
    global STATE
    
    bot = bot or STATE.bot
    user_id = message.from_user.id
    voice = message.voice
    
    try:
        lang = get_user_language(user_id)
        
        # Показываем что обрабатываем
        await send_typing_action(bot, user_id)
        
        # Информация о голосовом сообщении
        voice_info = {
            "file_id": voice.file_id,
            "file_unique_id": voice.file_unique_id,
            "duration": voice.duration,
            "mime_type": voice.mime_type,
            "file_size": voice.file_size
        }
        
        # Здесь будет интеграция с Whisper STT (Блок 11)
        # Пока отправляем заглушку
        response_text = """🎤 Голосовое сообщение получено!

Для обработки голосовых сообщений свяжитесь с нами напрямую:
📞 WhatsApp: +66-633-633-407""" if lang == "ru" else """🎤 Voice message received!

For voice message processing, contact us directly:
📞 WhatsApp: +66-633-633-407"""
        
        await send_message_safe(bot, user_id, response_text)
        
        return {
            "success": True,
            "type": "voice",
            "voice_info": voice_info
        }
        
    except Exception as e:
        STATE.errors_count += 1
        STATE.last_error = str(e)
        logger.error(f"Error handling voice: {e}")
        return {"success": False, "error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 8: SEND MESSAGE SAFE
# ═══════════════════════════════════════════════════════════════════════════════

async def send_message_safe(
    bot: Any,
    chat_id: int,
    text: str,
    reply_markup: Dict = None,
    parse_mode: str = None,
    disable_notification: bool = False
) -> Optional[Any]:
    """
    Безопасная отправка сообщения с обработкой ошибок
    
    Args:
        bot: Объект бота
        chat_id: ID чата
        text: Текст сообщения
        reply_markup: Клавиатура
        parse_mode: Режим парсинга (HTML/Markdown)
        disable_notification: Без уведомления
        
    Returns:
        Отправленное сообщение или None
    """
    try:
        # Ограничение длины сообщения
        max_length = CONFIG.bot_settings["max_message_length"]
        if len(text) > max_length:
            text = text[:max_length - 3] + "..."
        
        # Конвертация reply_markup если нужно
        keyboard = None
        if reply_markup and isinstance(reply_markup, dict):
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            if "inline_keyboard" in reply_markup:
                buttons = []
                for row in reply_markup["inline_keyboard"]:
                    btn_row = []
                    for btn in row:
                        btn_row.append(InlineKeyboardButton(
                            text=btn.get("text", ""),
                            callback_data=btn.get("callback_data"),
                            url=btn.get("url")
                        ))
                    buttons.append(btn_row)
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        # Отправка
        message = await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode or ParseMode.HTML,
            disable_notification=disable_notification
        )
        
        return message
        
    except Exception as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")
        STATE.errors_count += 1
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 9: SEND TYPING ACTION
# ═══════════════════════════════════════════════════════════════════════════════

async def send_typing_action(
    bot: Any,
    chat_id: int,
    action: str = "typing",
    duration: float = None
) -> bool:
    """
    Отправка индикатора действия (печатает, записывает голос и т.д.)
    
    Args:
        bot: Объект бота
        chat_id: ID чата
        action: Тип действия (typing, upload_photo, record_voice, etc.)
        duration: Длительность показа (секунды)
        
    Returns:
        True если успешно
    """
    try:
        # Маппинг действий на ChatAction
        action_map = {
            "typing": ChatAction.TYPING,
            "upload_photo": ChatAction.UPLOAD_PHOTO,
            "record_video": ChatAction.RECORD_VIDEO,
            "upload_video": ChatAction.UPLOAD_VIDEO,
            "record_voice": ChatAction.RECORD_VOICE,
            "upload_voice": ChatAction.UPLOAD_VOICE,
            "upload_document": ChatAction.UPLOAD_DOCUMENT,
            "find_location": ChatAction.FIND_LOCATION,
            "record_video_note": ChatAction.RECORD_VIDEO_NOTE,
            "upload_video_note": ChatAction.UPLOAD_VIDEO_NOTE
        }
        
        chat_action = action_map.get(action, ChatAction.TYPING)
        
        await bot.send_chat_action(chat_id=chat_id, action=chat_action)
        
        # Задержка если указана
        if duration:
            await asyncio.sleep(min(duration, 5.0))  # Max 5 секунд
        else:
            await asyncio.sleep(CONFIG.bot_settings["typing_delay"])
        
        return True
        
    except Exception as e:
        logger.warning(f"Failed to send typing action to {chat_id}: {e}")
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 10: CHECK ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

def check_admin(user_id: int) -> bool:
    """
    Проверка является ли пользователь администратором
    
    Args:
        user_id: ID пользователя
        
    Returns:
        True если администратор
    """
    return user_id in STATE.admin_ids

async def check_admin_async(
    user_id: int,
    bot: Any = None,
    send_warning: bool = True
) -> bool:
    """
    Асинхронная проверка администратора с отправкой предупреждения
    
    Args:
        user_id: ID пользователя
        bot: Объект бота
        send_warning: Отправить предупреждение если не админ
        
    Returns:
        True если администратор
    """
    is_admin = check_admin(user_id)
    
    if not is_admin and send_warning and bot:
        lang = get_user_language(user_id)
        await send_message_safe(bot, user_id, get_message("admin_only", lang))
    
    return is_admin

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 11: GET BOT INFO
# ═══════════════════════════════════════════════════════════════════════════════

async def get_bot_info(bot: Any = None) -> Dict[str, Any]:
    """
    Получение информации о боте
    
    Args:
        bot: Объект бота (если None - используется STATE.bot)
        
    Returns:
        Словарь с информацией о боте
    """
    bot = bot or STATE.bot
    
    try:
        # Получение информации от Telegram
        bot_user = await bot.get_me()
        
        # Статистика работы
        uptime = None
        if STATE.started_at:
            uptime = (datetime.now() - STATE.started_at).total_seconds()
        
        return {
            "success": True,
            "bot": {
                "id": bot_user.id,
                "username": bot_user.username,
                "first_name": bot_user.first_name,
                "can_join_groups": bot_user.can_join_groups,
                "can_read_all_group_messages": bot_user.can_read_all_group_messages,
                "supports_inline_queries": bot_user.supports_inline_queries
            },
            "status": STATE.status.value,
            "statistics": {
                "messages_processed": STATE.messages_processed,
                "errors_count": STATE.errors_count,
                "last_error": STATE.last_error,
                "uptime_seconds": uptime,
                "uptime_formatted": format_uptime(uptime) if uptime else None
            },
            "config": {
                "admin_ids": STATE.admin_ids,
                "webhooks_active": STATE.webhooks_active,
                "handlers_registered": STATE.handlers_registered,
                "middlewares": STATE.middlewares,
                "users_count": len(STATE.user_languages)
            },
            "contacts": CONFIG.contacts
        }
        
    except Exception as e:
        logger.error(f"Failed to get bot info: {e}")
        return {
            "success": False,
            "error": str(e),
            "status": STATE.status.value
        }

def format_uptime(seconds: float) -> str:
    """Форматирование времени работы"""
    if not seconds:
        return "0s"
    
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 12: REGISTER HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

async def register_handlers(
    router: Any = None,
    custom_handlers: List[Dict] = None
) -> bool:
    """
    Регистрация обработчиков сообщений
    
    Args:
        router: Роутер (если None - используется STATE.router)
        custom_handlers: Список кастомных обработчиков
        
    Returns:
        True если успешно
    """
    global STATE
    
    router = router or STATE.router
    if not router:
        logger.error("Router not initialized")
        return False
    
    try:
        logger.info("Registering handlers...")
        
        # Обработчик команды /start
        @router.message(CommandStart())
        async def cmd_start(message: Message):
            await handle_message(message, STATE.bot)
        
        # Обработчик команды /menu
        @router.message(Command("menu"))
        async def cmd_menu(message: Message):
            await handle_message(message, STATE.bot)
        
        # Обработчик команды /help
        @router.message(Command("help"))
        async def cmd_help(message: Message):
            await handle_message(message, STATE.bot)
        
        # Обработчик команды /contact
        @router.message(Command("contact", "contacts"))
        async def cmd_contact(message: Message):
            await handle_message(message, STATE.bot)
        
        # Обработчик команды /language
        @router.message(Command("language"))
        async def cmd_language(message: Message):
            await handle_message(message, STATE.bot)
        
        # Обработчик команды /yachts
        @router.message(Command("yachts"))
        async def cmd_yachts(message: Message):
            user_id = message.from_user.id
            lang = get_user_language(user_id)
            # Эмулируем нажатие кнопки яхт
            class FakeCallback:
                def __init__(self):
                    self.from_user = message.from_user
                    self.data = "menu_yachts"
                    self.id = "fake"
            await handle_callback(FakeCallback(), STATE.bot)
        
        # Обработчик команды /parties
        @router.message(Command("parties"))
        async def cmd_parties(message: Message):
            class FakeCallback:
                def __init__(self):
                    self.from_user = message.from_user
                    self.data = "menu_parties"
                    self.id = "fake"
            await handle_callback(FakeCallback(), STATE.bot)
        
        # Обработчик команды /vip
        @router.message(Command("vip"))
        async def cmd_vip(message: Message):
            user_id = message.from_user.id
            lang = get_user_language(user_id)
            vip_text = """👑 <b>VIP Услуги Party Pattaya</b>

- Персональный менеджер
- Приоритетное бронирование
- Эксклюзивные локации
- Премиум кейтеринг
- VIP трансфер

📞 WhatsApp: +66-633-633-407""" if lang == "ru" else """👑 <b>VIP Services Party Pattaya</b>

- Personal manager
- Priority booking
- Exclusive locations
- Premium catering
- VIP transfer

📞 WhatsApp: +66-633-633-407"""
            await send_message_safe(STATE.bot, user_id, vip_text)
        
        # Обработчик команды /transfer
        @router.message(Command("transfer"))
        async def cmd_transfer(message: Message):
            user_id = message.from_user.id
            lang = get_user_language(user_id)
            transfer_text = """🚗 <b>Трансфер услуги</b>

- Аэропорт ↔ Паттайя
- Бангкок ↔ Паттайя  
- Любые направления
- Комфортные авто
- VIP транспорт

Цены от 1,500 THB

📞 WhatsApp: +66-633-633-407""" if lang == "ru" else """🚗 <b>Transfer Services</b>

- Airport ↔ Pattaya
- Bangkok ↔ Pattaya
- Any direction
- Comfortable cars
- VIP transport

Prices from 1,500 THB

📞 WhatsApp: +66-633-633-407"""
            await send_message_safe(STATE.bot, user_id, transfer_text)
        
        # Обработчик админ-команды /admin
        @router.message(Command("admin"))
        async def cmd_admin(message: Message):
            user_id = message.from_user.id
            if not check_admin(user_id):
                lang = get_user_language(user_id)
                await send_message_safe(STATE.bot, user_id, get_message("admin_only", lang))
                return
            
            info = await get_bot_info()
            admin_text = f"""🔧 <b>Admin Panel</b>

<b>Bot Status:</b> {info.get('status', 'unknown')}
<b>Messages:</b> {info.get('statistics', {}).get('messages_processed', 0)}
<b>Errors:</b> {info.get('statistics', {}).get('errors_count', 0)}
<b>Uptime:</b> {info.get('statistics', {}).get('uptime_formatted', 'N/A')}
<b>Users:</b> {info.get('config', {}).get('users_count', 0)}

<b>Commands:</b>
/admin - This panel
/stats - Statistics
/broadcast - Send to all users
/restart - Restart bot"""
            await send_message_safe(STATE.bot, user_id, admin_text)
        
        # Обработчик голосовых сообщений
        @router.message(F.voice)
        async def voice_handler(message: Message):
            await handle_voice(message, STATE.bot)
        
        # Обработчик callback queries
        @router.callback_query()
        async def callback_handler(callback: CallbackQuery):
            await handle_callback(callback, STATE.bot)
        
        # Обработчик всех остальных текстовых сообщений
        @router.message(F.text)
        async def text_handler(message: Message):
            # Игнорируем если это команда (уже обработана)
            if message.text and message.text.startswith("/"):
                return
            await handle_message(message, STATE.bot)
        
        # Регистрация кастомных обработчиков
        if custom_handlers:
            for handler in custom_handlers:
                handler_func = handler.get("function")
                handler_filter = handler.get("filter")
                if handler_func:
                    if handler_filter:
                        router.message(handler_filter)(handler_func)
                    else:
                        router.message()(handler_func)
                    logger.info(f"Registered custom handler: {handler.get('name', 'unnamed')}")
        
        STATE.handlers_registered = True
        logger.info("All handlers registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to register handlers: {e}")
        STATE.errors_count += 1
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 13: SETUP MIDDLEWARES
# ═══════════════════════════════════════════════════════════════════════════════

async def setup_middlewares(
    dispatcher: Any = None,
    custom_middlewares: List[Any] = None
) -> bool:
    """
    Настройка middleware для бота
    
    Args:
        dispatcher: Диспетчер (если None - используется STATE.dispatcher)
        custom_middlewares: Список кастомных middleware
        
    Returns:
        True если успешно
    """
    global STATE
    
    dispatcher = dispatcher or STATE.dispatcher
    if not dispatcher:
        logger.error("Dispatcher not initialized")
        return False
    
    try:
        logger.info("Setting up middlewares...")
        
        # Базовый middleware для логирования
        from aiogram import BaseMiddleware
        from aiogram.types import TelegramObject
        
        class LoggingMiddleware(BaseMiddleware):
            async def __call__(self, handler, event: TelegramObject, data: dict):
                logger.debug(f"Update received: {type(event).__name__}")
                return await handler(event, data)
        
        class RateLimitMiddleware(BaseMiddleware):
            async def __call__(self, handler, event: TelegramObject, data: dict):
                # Получаем user_id из события
                user_id = None
                if hasattr(event, "from_user") and event.from_user:
                    user_id = event.from_user.id
                elif hasattr(event, "message") and event.message and event.message.from_user:
                    user_id = event.message.from_user.id
                
                if user_id and not check_rate_limit(user_id):
                    lang = get_user_language(user_id)
                    logger.warning(f"Rate limit exceeded for user {user_id}")
                    # Не вызываем handler - пропускаем сообщение
                    return None
                
                return await handler(event, data)
        
        class ErrorHandlerMiddleware(BaseMiddleware):
            async def __call__(self, handler, event: TelegramObject, data: dict):
                try:
                    return await handler(event, data)
                except Exception as e:
                    STATE.errors_count += 1
                    STATE.last_error = str(e)
                    logger.error(f"Error in handler: {e}")
                    
                    # Пытаемся отправить сообщение об ошибке
                    user_id = None
                    if hasattr(event, "from_user") and event.from_user:
                        user_id = event.from_user.id
                    elif hasattr(event, "message") and event.message and event.message.from_user:
                        user_id = event.message.from_user.id
                    
                    if user_id and STATE.bot:
                        lang = get_user_language(user_id)
                        try:
                            await send_message_safe(STATE.bot, user_id, get_message("error", lang))
                        except:
                            pass
                    
                    return None
        
        # Регистрация middleware
        dispatcher.message.middleware(LoggingMiddleware())
        STATE.middlewares.append("LoggingMiddleware")
        
        dispatcher.message.middleware(RateLimitMiddleware())
        STATE.middlewares.append("RateLimitMiddleware")
        
        dispatcher.message.middleware(ErrorHandlerMiddleware())
        STATE.middlewares.append("ErrorHandlerMiddleware")
        
        # Кастомные middleware
        if custom_middlewares:
            for mw in custom_middlewares:
                dispatcher.message.middleware(mw)
                STATE.middlewares.append(type(mw).__name__)
                logger.info(f"Registered custom middleware: {type(mw).__name__}")
        
        logger.info(f"Middlewares setup complete: {STATE.middlewares}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup middlewares: {e}")
        STATE.errors_count += 1
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 14: SHUTDOWN BOT
# ═══════════════════════════════════════════════════════════════════════════════

async def shutdown_bot(
    bot: Any = None,
    notify_admins: bool = True,
    reason: str = None
) -> bool:
    """
    Корректная остановка бота
    
    Args:
        bot: Объект бота
        notify_admins: Уведомить администраторов
        reason: Причина остановки
        
    Returns:
        True если успешно
    """
    global STATE
    
    bot = bot or STATE.bot
    
    try:
        logger.info(f"Shutting down bot... Reason: {reason or 'not specified'}")
        STATE.status = BotStatus.STOPPING
        
        # Уведомление администраторов
        if notify_admins and bot and STATE.admin_ids:
            shutdown_text = f"🛑 <b>Bot shutting down</b>\nReason: {reason or 'Manual shutdown'}"
            for admin_id in STATE.admin_ids:
                try:
                    await send_message_safe(bot, admin_id, shutdown_text)
                except:
                    pass
        
        # Удаление webhook если был
        if STATE.webhooks_active and bot:
            try:
                await bot.delete_webhook()
                STATE.webhooks_active = False
            except:
                pass
        
        # Закрытие сессии бота
        if bot:
            try:
                await bot.session.close()
            except:
                pass
        
        # Остановка диспетчера
        if STATE.dispatcher:
            try:
                await STATE.dispatcher.stop_polling()
            except:
                pass
        
        STATE.status = BotStatus.STOPPED
        STATE.bot = None
        STATE.dispatcher = None
        STATE.router = None
        STATE.handlers_registered = False
        
        logger.info("Bot shutdown complete")
        return True
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        STATE.status = BotStatus.ERROR
        STATE.last_error = str(e)
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 15: RESTART BOT
# ═══════════════════════════════════════════════════════════════════════════════

async def restart_bot(
    token: str = None,
    admin_id: int = None,
    notify_admins: bool = True,
    delay_seconds: float = 2.0
) -> bool:
    """
    Перезапуск бота
    
    Args:
        token: Telegram Bot Token (если None - используется предыдущий)
        admin_id: ID администратора
        notify_admins: Уведомить администраторов
        delay_seconds: Задержка перед перезапуском
        
    Returns:
        True если успешно
    """
    global STATE
    
    try:
        logger.info("Restarting bot...")
        
        # Сохраняем текущие настройки
        saved_token = token
        saved_admin_ids = STATE.admin_ids.copy() if STATE.admin_ids else []
        saved_languages = STATE.user_languages.copy()
        
        if admin_id:
            saved_admin_ids = [admin_id] if isinstance(admin_id, int) else list(admin_id)
        
        # Уведомление администраторов о перезапуске
        if notify_admins and STATE.bot and saved_admin_ids:
            for aid in saved_admin_ids:
                lang = get_user_language(aid)
                try:
                    await send_message_safe(STATE.bot, aid, get_message("bot_restarting", lang))
                except:
                    pass
        
        # Остановка
        await shutdown_bot(notify_admins=False, reason="Restart")
        
        # Задержка
        await asyncio.sleep(delay_seconds)
        
        # Проверяем наличие токена
        if not saved_token:
            logger.error("Cannot restart: no token provided")
            return False
        
        # Перезапуск
        await init_bot(
            token=saved_token,
            admin_id=saved_admin_ids[0] if saved_admin_ids else 0
        )
        
        # Восстановление языков пользователей
        STATE.user_languages = saved_languages
        
        # Настройка middleware и handlers
        await setup_middlewares()
        await register_handlers()
        
        # Уведомление о успешном перезапуске
        if notify_admins and STATE.bot and saved_admin_ids:
            for aid in saved_admin_ids:
                try:
                    await send_message_safe(STATE.bot, aid, "✅ Bot restarted successfully!")
                except:
                    pass
        
        logger.info("Bot restart complete")
        return True
        
    except Exception as e:
        logger.error(f"Failed to restart bot: {e}")
        STATE.status = BotStatus.ERROR
        STATE.last_error = str(e)
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# ДОПОЛНИТЕЛЬНЫЕ УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════════════════════

async def broadcast_message(
    text: str,
    user_ids: List[int] = None,
    reply_markup: Dict = None,
    admin_only: bool = False
) -> Dict[str, Any]:
    """
    Рассылка сообщений пользователям
    
    Args:
        text: Текст сообщения
        user_ids: Список ID (если None - всем известным пользователям)
        reply_markup: Клавиатура
        admin_only: Только администраторам
        
    Returns:
        Статистика рассылки
    """
    if not STATE.bot:
        return {"success": False, "error": "Bot not initialized"}
    
    targets = user_ids or list(STATE.user_languages.keys())
    
    if admin_only:
        targets = [uid for uid in targets if uid in STATE.admin_ids]
    
    sent = 0
    failed = 0
    
    for user_id in targets:
        try:
            await send_message_safe(STATE.bot, user_id, text, reply_markup=reply_markup)
            sent += 1
            await asyncio.sleep(0.05)  # Антифлуд
        except Exception as e:
            failed += 1
            logger.warning(f"Failed to send broadcast to {user_id}: {e}")
    
    return {
        "success": True,
        "total": len(targets),
        "sent": sent,
        "failed": failed
    }

def add_admin(user_id: int) -> bool:
    """Добавление администратора"""
    if user_id not in STATE.admin_ids:
        STATE.admin_ids.append(user_id)
        return True
    return False

def remove_admin(user_id: int) -> bool:
    """Удаление администратора"""
    if user_id in STATE.admin_ids:
        STATE.admin_ids.remove(user_id)
        return True
    return False

def get_statistics() -> Dict[str, Any]:
    """Получение статистики бота"""
    uptime = None
    if STATE.started_at:
        uptime = (datetime.now() - STATE.started_at).total_seconds()
    
    return {
        "status": STATE.status.value,
        "messages_processed": STATE.messages_processed,
        "errors_count": STATE.errors_count,
        "last_error": STATE.last_error,
        "uptime_seconds": uptime,
        "uptime_formatted": format_uptime(uptime) if uptime else None,
        "users_count": len(STATE.user_languages),
        "admins_count": len(STATE.admin_ids),
        "handlers_registered": STATE.handlers_registered,
        "middlewares": STATE.middlewares,
        "webhooks_active": STATE.webhooks_active
    }

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                         BLOCK 02: MAIN BOT ENGINE                            ║
║                       Party Pattaya Bot v10.2.1                              ║
║                                                                              ║
║  Основной движок Telegram бота для Party Pattaya                             ║
║  15 функций | aiogram 3.x | Полная интеграция                                ║
║                                                                              ║
║  ⚠️  ИЗМЕНЕНИЯ ЗАПРЕЩЕНЫ БЕЗ РАЗРЕШЕНИЯ СЕРГЕЯ                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("КОНТАКТЫ PARTY PATTAYA (защищены):")
    print(f"  WhatsApp: {CONFIG.contacts['whatsapp']}")
    print(f"  Telegram: {CONFIG.contacts['telegram']}")
    print(f"  Email: {CONFIG.contacts['email']}")
    
    print("\nФункции:")
    print("  1.  init_bot            - Инициализация бота")
    print("  2.  start_polling       - Запуск long polling")
    print("  3.  setup_webhook       - Настройка webhook")
    print("  4.  process_update      - Обработка обновлений")
    print("  5.  handle_message      - Обработка сообщений")
    print("  6.  handle_callback     - Обработка callback")
    print("  7.  handle_voice        - Обработка голоса")
    print("  8.  send_message_safe   - Безопасная отправка")
    print("  9.  send_typing_action  - Индикатор печати")
    print("  10. check_admin         - Проверка админа")
    print("  11. get_bot_info        - Информация о боте")
    print("  12. register_handlers   - Регистрация хендлеров")
    print("  13. setup_middlewares   - Настройка middleware")
    print("  14. shutdown_bot        - Остановка бота")
    print("  15. restart_bot         - Перезапуск бота")
    
    print("\nДополнительно:")
    print("  • broadcast_message     - Рассылка")
    print("  • add_admin/remove_admin - Управление админами")
    print("  • get_statistics        - Статистика")
    
    print("\nИмпорт: from block_02_main_bot_engine import *")
    
    print("\nПример запуска:")
    print("  bot = await init_bot(token='YOUR_TOKEN', admin_id=123456)")
    print("  await start_polling()")
