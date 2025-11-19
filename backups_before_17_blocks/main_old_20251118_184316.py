#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, logging, asyncio, io
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from openai import OpenAI
from langdetect import detect, LangDetectException
from dotenv import load_dotenv

# 🔒 БЛОК 17: СИСТЕМА ЗАЩИТЫ И ВОССТАНОВЛЕНИЯ
from block_17_protection import initialize_block_17, get_protection_system


# ═══════════════════════════════════════════════════════════════════════════════
# 🔒 БЛОК 17: СИСТЕМА ЗАЩИТЫ И ВОССТАНОВЛЕНИЯ
# ═══════════════════════════════════════════════════════════════════════════════
from block_17_protection import initialize_block_17, get_protection_system


load_dotenv()

TELEGRAM_TOKEN = "8439387127:AAFF4OGp6BBtCSKXMYMMuGkgy67ymtYQ74E"
OPENAI_API_KEY = "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"
ADMIN_ID = 359364877

openai_client = OpenAI(api_key=OPENAI_API_KEY)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TELEGRAM_LANGUAGE_MAP = {
    "ru": "ru", "en": "en", "es": "es", "fr": "fr", "de": "de", 
    "it": "it", "pt": "pt", "ja": "ja", "ko": "ko", "th": "th",
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

📱 Общение с AI:
💬 Напишите вопрос или удерживая кнопку микрофона до конца сообщения

📞 Готовы помочь! Какое событие вы планируете?""",
    
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

📱 Chat with AI:
💬 Type a question or hold the microphone button until the end of the message

📞 Ready to help! What event are you planning?""",

    "th": """สวัสดี! 👋

ฉันช่วยคุณจัดงานที่ไม่เหลือลืมในพัทยา!

🎊 ฉันสามารถ:
- จัดงาน ปาร์ตี้
- เช่ายอชต์ เรือ
- บริการ VIP
- ทัวร์
- เดินทาง

💎 Party Pattaya:
✓ 5+ ปี ที่พัทยา
✓ 1000+ ลูกค้าพอใจ
✓ เปิด 24/7
✓ บริการส่วนตัว

📱 คุยกับ AI:
💬 พิมพ์คำถามหรือกดปุ่มไมค์จนจบ

📞 พร้อมช่วย!""",
}

WELCOME_VOICE = {
    "ru": "Привет! Я ваш помощник Party Pattaya. Я помогу вам организовать незабываемое событие в Паттайе. Вы можете со мной писать вопросы или общаться голосом. Какое событие вы планируете?",
    "en": "Hello! I'm your Party Pattaya assistant. I'll help you organize an unforgettable event in Pattaya. You can write questions to me or communicate by voice. What event are you planning?",
    "th": "สวัสดี ฉันช่วยคุณจัดงาน ฉันจะช่วยให้คุณจัดงานที่ไม่เหลือลืม บนพัทยา",
}

SERVICES_TEXT = {
    "ru": """🎉 НАШИ УСЛУГИ

🔥 СПЕЦПРЕДЛОЖЕНИЯ:
- Скидка 10% на первый заказ
- Бесплатная консультация
- Организация мероприятий "под ключ"

💎 ПОЧЕМУ МЫ?
✓ 5+ лет опыта в Паттайе
✓ 1000+ довольных клиентов
✓ Работаем 24/7 без выходных
✓ Индивидуальный подход к каждому
✓ Гарантия качества

🏝 ЛОКАЦИИ И ЯХТЫ:
- Виллы с бассейном
- Яхты и катера
- Частный остров
- Крыши отелей

🎪 КОНЦЕРТЫ И СОБЫТИЯ:
- Организация концертов
- Здание в аренду
- Звуковое оборудование JBL
- Световое оборудование
- Видео панели
- Сцены

🎤 АРТИСТЫ:
- DJ (диджеи)
- Вокалисты и певцы
- Музыканты
- Танцоры и шоу
- Фокусники

🎨 ДЕКОР:
- Праздничные декорации
- Световое оформление
- Тематическое оформление
- Флористика

🍽 КЕЙТЕРИНГ И БАР:
- Выездной кейтеринг
- Организация бара
- Коктейльные карты
- Меню на любой вкус

🎥 ФОТО/ВИДЕО СЪЁМКА:
- Профессиональная фотосъёмка
- Видеосъёмка мероприятия
- Монтаж и обработка

💎 VIP-СЕРВИСЫ:
- Полёт на вертолёте
- Полёт на самолёте
- Аренда спортивных авто
- VIP-трансферы

📞 Позвоните: +66633633407
💬 WhatsApp: https://wa.me/66633633407""",
    
    "en": """🎉 OUR SERVICES

🔥 SPECIAL OFFERS:
- 10% discount on first order
- Free consultation
- Full-service event organization

💎 WHY US?
✓ 5+ years of experience in Pattaya
✓ 1000+ satisfied customers
✓ Open 24/7 without days off
✓ Individual approach to everyone
✓ Quality guarantee

🏝 LOCATIONS AND YACHTS:
- Villas with pool
- Yachts and boats
- Private island
- Hotel rooftops

🎪 CONCERTS AND EVENTS:
- Concert organization
- Building rental
- JBL sound equipment
- Lighting equipment
- Video panels
- Stages

🎤 ARTISTS:
- DJs
- Vocalists and singers
- Musicians
- Dancers and shows
- Magicians

🎨 DECORATION:
- Holiday decorations
- Lighting design
- Themed decorations
- Florals

🍽 CATERING AND BAR:
- Catering service
- Bar organization
- Cocktail menus
- Any taste menu

🎥 PHOTO/VIDEO SHOOTING:
- Professional photography
- Event videography
- Editing and processing

💎 VIP SERVICES:
- Helicopter flights
- Airplane flights
- Sports car rental
- VIP transfers

📞 Call: +66633633407
💬 WhatsApp: https://wa.me/66633633407""",

    "th": """🎉 บริการของเรา

🏝 สถานที่และยอชต์:
- วิลล่า
- ยอชต์
- เกาะส่วนตัว
- หลังคาโรงแรม

🎪 คอนเสิร์ตและอีเวนต์:
- จัดคอนเสิร์ต
- เช่าอาคาร
- อุปกรณ์เสียง

🎤 ศิลปิน:
- ดีเจ
- นักร้อง
- นักเต้น

📞 โทร: +66633633407""",
}

SERVICES_VOICE = {
    "ru": "Мы предлагаем организацию вечеринок, бронирование яхт и катеров, VIP сервис. Все услуги на высшем уровне. Работаем 24/7 для вас.",
    "en": "We offer party organization, yacht and boat rental, VIP service. All services at the highest level. We work 24/7 for you.",
    "th": "เราจัดงาน เช่ายอชต์ บริการ VIP คุณภาพสูง เปิด 24/7",
}

CONTACTS_TEXT = {
    "ru": """📞 КОНТАКТЫ PARTY PATTAYA

🏢 АДРЕС:
118/40, Moo 11, Baan Dusit Pattaya Park
Huayyai, Chonburi, Bang Lamung, 20150 Thailand

📱 МОБИЛЬНЫЙ:
+66633633407 (WhatsApp, Viber, Call)

📧 EMAIL:
infopartypattayacity@gmail.com
partypattayacity@gmail.com

🌐 ГЛАВНЫЙ САЙТ:
https://partypattayacity.com

🎥 СОЦИАЛЬНЫЕ СЕТИ:

📺 YouTube: @party_pattaya
https://youtube.com/@party_pattaya?si=mpfWJZmzq2bGozbp

🎵 TikTok: @events_pattaya
https://www.tiktok.com/@events_pattaya?_t=ZS-8ziYqK7l9d6&_r=1

💬 Telegram: @Party_Pattaya
https://t.me/Party_Pattaya

📱 Line:
https://line.me/ti/p/yNV6RFgTKQ

📸 Instagram: party_pattaya_city
https://www.instagram.com/party_pattaya_city?igsh=MWd6Y2E5ajlsdGl4dA%3D%3D&utm_source=qr

👥 Facebook: Party Pattaya City
https://www.facebook.com/share/19gz2ijhzk/?mibextid=wwXIfr

🗺 КАРТЫ:
Яндекс карты: https://yandex.com/maps/-/CLB2BD2w
Google Maps: https://maps.app.goo.gl/DiqkHXV3g4fXeL4s8?g_st=ipc

📋 РЕКВИЗИТЫ:
TAX-ID: 0205566048577""",

    "en": """📞 PARTY PATTAYA CONTACTS

🏢 ADDRESS:
118/40, Moo 11, Baan Dusit Pattaya Park
Huayyai, Chonburi, Bang Lamung, 20150 Thailand

📱 MOBILE:
+66633633407 (WhatsApp, Viber, Call)

📧 EMAIL:
infopartypattayacity@gmail.com
partypattayacity@gmail.com

🌐 MAIN WEBSITE:
https://partypattayacity.com

🎥 SOCIAL MEDIA:

📺 YouTube: @party_pattaya
https://youtube.com/@party_pattaya?si=mpfWJZmzq2bGozbp

🎵 TikTok: @events_pattaya
https://www.tiktok.com/@events_pattaya?_t=ZS-8ziYqK7l9d6&_r=1

💬 Telegram: @Party_Pattaya
https://t.me/Party_Pattaya

📱 Line:
https://line.me/ti/p/yNV6RFgTKQ

📸 Instagram: party_pattaya_city
https://www.instagram.com/party_pattaya_city?igsh=MWd6Y2E5ajlsdGl4dA%3D%3D&utm_source=qr

👥 Facebook: Party Pattaya City
https://www.facebook.com/share/19gz2ijhzk/?mibextid=wwXIfr

🗺 MAPS:
Yandex Maps: https://yandex.com/maps/-/CLB2BD2w
Google Maps: https://maps.app.goo.gl/DiqkHXV3g4fXeL4s8?g_st=ipc

📋 DETAILS:
TAX-ID: 0205566048577""",

    "th": """📞 ติดต่อเรา

📱 มือถือ: +66633633407
💬 Telegram: @Party_Pattaya
📸 Instagram: party_pattaya_city
🌐 เว็บ: https://partypattayacity.com
📧 Email: infopartypattayacity@gmail.com""",
}

LANGUAGE_PROMPTS = {
    "ru": "Ты помощник Party Pattaya в Паттайе. Помогай клиентам бронировать яхты, организовать события, VIP услуги. Отвечай только на русском. Информацию бери с сайта partypattayacity.com",
    "en": "You are Party Pattaya City assistant in Pattaya. Help book yachts, organize events, VIP services. Answer ONLY in English. Get information from partypattayacity.com",
    "th": "คุณเป็นผู้ช่วย Party Pattaya ที่พัทยา ช่วยจองยอชต์ จัดงาน ตอบเป็นภาษาไทย เป็นมืออาชีพ",
}

class PartyPattayaBotV2:
    def __init__(self):
        logger.info("🚀 Bot v2.0 инициализация...")
        self.app = Application.builder().token(TELEGRAM_TOKEN).build()

    def get_telegram_language(self, telegram_lang_code: str) -> str:
        if not telegram_lang_code:
            return "en"
        base_lang = telegram_lang_code.split("-")[0].lower()
        return TELEGRAM_LANGUAGE_MAP.get(base_lang, "en")

    def detect_language(self, text: str) -> str:
        if not text or len(text) < 2:
            return "en"
        try:
            detected = detect(text)
            return detected if detected in LANGUAGE_PROMPTS else "en"
        except:
            return "en"

    async def send_voice(self, chat_id, voice_data):
        try:
            await self.app.bot.send_voice(chat_id=chat_id, voice=voice_data)
            logger.info(f"✅ Voice sent: {len(voice_data)} bytes")
            return True
        except Exception as e:
            logger.error(f"❌ Send voice error: {e}")
            return False

    async def send_message(self, chat_id, text, **kwargs):
        try:
            await self.app.bot.send_message(chat_id=chat_id, text=text, **kwargs)
            return True
        except Exception as e:
            logger.error(f"❌ Send message error: {e}")
            return False

    async def create_voice(self, text: str):
        try:
            logger.info(f"🎤 TTS: {text[:50]}")
            response = openai_client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=text,
            )
            logger.info(f"✅ TTS created: {len(response.content)} bytes")
            return response.content
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
            return None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        telegram_lang = self.get_telegram_language(user.language_code)
        context.user_data["language"] = telegram_lang
        logger.info(f"👤 User {user.id} | Lang: {telegram_lang}")
        welcome = WELCOME_MESSAGES.get(telegram_lang, WELCOME_MESSAGES["en"])
        button_texts = {
            "ru": ["🎉 Услуги", "📞 Контакты"],
            "en": ["🎉 Services", "📞 Contacts"],
            "th": ["🎉 บริการ", "📞 ติดต่อ"],
        }.get(telegram_lang, ["🎉 Services", "📞 Contacts"])
        keyboard = [[
            InlineKeyboardButton(button_texts[0], callback_data="services"),
            InlineKeyboardButton(button_texts[1], callback_data="contacts"),
        ]]
        await self.send_message(update.effective_chat.id, welcome, reply_markup=InlineKeyboardMarkup(keyboard))
        logger.info("✅ Welcome TEXT sent")
        voice_text = WELCOME_VOICE.get(telegram_lang, WELCOME_VOICE["en"])
        voice_data = await self.create_voice(voice_text)
        if voice_data:
            await self.send_voice(update.effective_chat.id, voice_data)
            logger.info(f"✅ Welcome VOICE sent")

    async def button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        lang = context.user_data.get("language", "en")
        chat_id = query.message.chat_id
        back_text = {
            "ru": "🔙 Вернуться",
            "en": "🔙 Back",
            "th": "🔙 กลับ",
        }.get(lang, "🔙 Back")
        back_btn = InlineKeyboardButton(back_text, callback_data="back")
        if query.data == "services":
            await query.edit_message_text(SERVICES_TEXT.get(lang, SERVICES_TEXT["en"]), reply_markup=InlineKeyboardMarkup([[back_btn]]))
            logger.info("✅ Services TEXT sent")
            voice_text = SERVICES_VOICE.get(lang, SERVICES_VOICE["en"])
            voice_data = await self.create_voice(voice_text)
            if voice_data:
                await self.send_voice(chat_id, voice_data)
                logger.info(f"✅ Services VOICE sent")
        elif query.data == "contacts":
            await query.edit_message_text(CONTACTS_TEXT.get(lang, CONTACTS_TEXT["en"]), reply_markup=InlineKeyboardMarkup([[back_btn]]))
            logger.info("✅ Contacts TEXT sent")
        elif query.data == "back":
            welcome = WELCOME_MESSAGES.get(lang)
            button_texts = {
                "ru": ["🎉 Услуги", "📞 Контакты"],
                "en": ["🎉 Services", "📞 Contacts"],
                "th": ["🎉 บริการ", "📞 ติดต่อ"],
            }.get(lang, ["🎉 Services", "📞 Contacts"])
            keyboard = [[
                InlineKeyboardButton(button_texts[0], callback_data="services"),
                InlineKeyboardButton(button_texts[1], callback_data="contacts"),
            ]]
            await query.edit_message_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard))

    async def text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        message_lang = self.detect_language(text)
        context.user_data["session_language"] = message_lang
        await update.message.chat.send_action("typing")
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": LANGUAGE_PROMPTS.get(message_lang, LANGUAGE_PROMPTS["en"])},
                    {"role": "user", "content": text}
                ],
                max_tokens=500,
                temperature=0.7,
            )
            ai_response = response.choices[0].message.content
            await self.send_message(update.effective_chat.id, ai_response)
            logger.info(f"✅ AI TEXT sent")
        except Exception as e:
            logger.error(f"❌ Text error: {e}")

    async def voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        logger.info(f"🎤 Voice from {user_id}")
        try:
            await update.message.chat.send_action("record_audio")
            file = await context.bot.get_file(update.message.voice.file_id)
            voice_buffer = io.BytesIO()
            await file.download_to_memory(out=voice_buffer)
            voice_buffer.seek(0)
            logger.info(f"✅ Voice downloaded: {len(voice_buffer.getvalue())} bytes")
            await update.message.chat.send_action("typing")
            try:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=("voice.ogg", voice_buffer, "audio/ogg"),
                )
                text = transcript.text
                logger.info(f"🎤 Recognized: {text}")
            except Exception as e:
                logger.error(f"❌ Transcription error: {e}")
                await self.send_message(chat_id, f"❌ Error: {str(e)}")
                return
            detected_lang = self.detect_language(text)
            transcription_msg = f"🎤 *Вы сказали:*\n_{text}_" if detected_lang == "ru" else f"🎤 *You said:*\n_{text}_"
            await self.send_message(chat_id, transcription_msg)
            logger.info("✅ Transcription SENT")
            await update.message.chat.send_action("typing")
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": LANGUAGE_PROMPTS.get(detected_lang, LANGUAGE_PROMPTS["en"])},
                    {"role": "user", "content": text}
                ],
                max_tokens=500,
                temperature=0.7,
            )
            ai_response = response.choices[0].message.content
            logger.info(f"🤖 AI: {ai_response[:100]}")
            await self.send_message(chat_id, ai_response)
            logger.info("✅ AI TEXT sent")
            voice_data = await self.create_voice(ai_response[:1000])
            if voice_data:
                await self.send_voice(chat_id, voice_data)
                logger.info("✅ AI VOICE sent")
        except Exception as e:
            logger.error(f"❌ VOICE ERROR: {e}")
            await self.send_message(chat_id, f"❌ Error: {str(e)}")

    
    async def initialize_protection(self):
        """Инициализировать БЛОК 17 при запуске бота"""
        try:
            logger.info("🔒 БЛОК 17: Инициализация системы защиты...")
            protection = await initialize_block_17("main.py")
            if protection:
                logger.info("✅ БЛОК 17: Система защиты активирована")
                return True
            else:
                logger.warning("⚠️  БЛОК 17: Некоторые блоки требуют проверки")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка БЛОКА 17: {e}")
            return False

    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CallbackQueryHandler(self.button_click))
        self.app.add_handler(MessageHandler(filters.VOICE, self.voice_message))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_message))
        logger.info("✅ Handlers ready")

    def run(self):
        print("\n" + "="*80)
        print("🚀 PARTY PATTAYA BOT v2.0 - ВСЕ 16 БЛОКОВ + БЛОК 17 (ЗАЩИТА)")
        print("="*80 + "\n")
        
        self.setup_handlers()
        try:
            logger.info("🟢 БОТ ЗАПУСКАЕТСЯ...")
            self.app.run_polling(allowed_updates=Update.ALL_TYPES)
        except KeyboardInterrupt:
            logger.info("🔴 Бот остановлен")

if __name__ == "__main__":
    bot = PartyPattayaBotV2()
    bot.run()
