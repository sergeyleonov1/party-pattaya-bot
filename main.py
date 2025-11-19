#!/usr/bin/env python3
import os, logging, io
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[logging.FileHandler('bot.log', encoding='utf-8'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

WELCOME = """Привет! 👋

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

📱 Общение с AI: Напишите вопрос или удерживая кнопку микрофона
📞 Контакты: @Party_Pattaya | +66633633407
🌐 Сайт: https://partypattayacity.com"""

SERVICES = {"yacht": {"name": "🛥️ Аренда яхты", "price": "\$500-2000"}, "party": {"name": "🎊 Организация вечеринки", "price": "\$1000-5000"}, "vip": {"name": "💎 VIP сервис", "price": "\$2000-10000"}, "tour": {"name": "🗺️ Экскурсия", "price": "\$50-500"}, "transfer": {"name": "🚗 Трансфер", "price": "\$20-200"}}

user_profiles = {}
user_history = {}

class Bot:
    def __init__(self):
        logger.info("✅ БЛОК 1: Инициализация Bot v7.0")
        self.app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in user_profiles:
            user_profiles[user_id] = {"username": update.effective_user.username}
        keyboard = [[InlineKeyboardButton("🎊 Услуги", callback_data="services"), InlineKeyboardButton("📞 Контакты", callback_data="contacts")], [InlineKeyboardButton("📋 Заказать", callback_data="order")]]
        await update.message.reply_text(WELCOME, reply_markup=InlineKeyboardMarkup(keyboard))
        logger.info(f"✅ БЛОК 2: {update.effective_user.username}")
    
    async def button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data == "services":
            text = "🎊 УСЛУГИ:\n\n"
            for s in SERVICES.values():
                text += f"{s['name']}\n{s['price']}\n\n"
            await query.edit_message_text(text=text)
        elif query.data == "contacts":
            await query.edit_message_text(text="📞 КОНТАКТЫ\n\nWhatsApp: +66633633407\nTelegram: @Party_Pattaya\nEmail: infopartypattayacity@gmail.com\nСайт: Partypattayacity.com\n\n📍 118/40, Moo 11, Baan Dusit Pattaya Park, Huayyai, Chonburi, 20150\nTAX-ID: 0205566048577\n\n📺 YouTube: https://youtube.com/@party_pattaya\nTikTok: https://www.tiktok.com/@events_pattaya\nTelegram: https://t.me/Party_Pattaya\nLine: https://line.me/ti/p/yNV6RFgTKQ\nInstagram: https://www.instagram.com/party_pattaya_city\nFacebook: https://www.facebook.com/share/19gz2ijhzk/")
        elif query.data == "order":
            await query.edit_message_text(text="📋 ЗАКАЗ\n\nНапишите:\n- Услуга\n- Дата\n- Гостей\n- Бюджет\n\n+66633633407\n@Party_Pattaya")
    
    async def text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.message.text
        try:
            response = openai_client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "system", "content": "Помощник Party Pattaya. ТОЛЬКО сайт Partypattayacity.com"}, {"role": "user", "content": msg}], max_tokens=500)
            await update.message.reply_text(response.choices[0].message.content)
        except Exception as e:
            logger.warning("⚠️ НЕ ОТВЕЧАЮ")
    
    async def voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            voice = update.message.voice
            file = await context.bot.get_file(voice.file_id)
            audio = await file.download_as_bytearray()
            audio_file = io.BytesIO(audio)
            audio_file.name = "voice.ogg"
            transcript = openai_client.audio.transcriptions.create(model="whisper-1", file=audio_file)
            text = transcript.text
            response = openai_client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "system", "content": "Помощник Party Pattaya"}, {"role": "user", "content": text}], max_tokens=500)
            await update.message.reply_text(f"🎙️ {text}\n\n{response.choices[0].message.content}")
        except Exception as e:
            logger.warning("⚠️ НЕ ОТВЕЧАЮ - ошибка голоса")
    
    def run(self):
        logger.info("✅ PARTY PATTAYA BOT v7.0 - ВСЕ 17 БЛОКОВ")
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CallbackQueryHandler(self.button_click))
        self.app.add_handler(MessageHandler(filters.VOICE, self.voice_message))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_message))
        logger.info("🟢 БОТ ЗАПУСКАЕТСЯ...")
        self.app.run_polling()

if __name__ == "__main__":
    Bot().run()
