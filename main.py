"""
PARTY PATTAYA BOT v10.1 FINAL
Владелец: Сергей Леонов
Telegram: @Party_Pattaya
"""
import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

CONTACTS = {
    'phone': '+66633633407',
    'email': 'infopartypattayacity@gmail.com',
    'website': 'https://partypattayacity.com',
    'telegram': '@Party_Pattaya',
    'instagram': 'party_pattaya_city'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Услуги", callback_data='services')],
        [InlineKeyboardButton("📞 Контакты", callback_data='contacts')]
    ]
    await update.message.reply_text(
        "🎉 Добро пожаловать в Party Pattaya!\n\n"
        "🎤 Удерживайте кнопку микрофона до конца записи\n\n"
        "Выберите раздел:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'services':
        keyboard = [
            [InlineKeyboardButton("🛥 Яхты ($500-2000)", callback_data='yacht')],
            [InlineKeyboardButton("🎉 Вечеринки ($1000-5000)", callback_data='party')],
            [InlineKeyboardButton("👑 VIP ($2000-10000)", callback_data='vip')],
            [InlineKeyboardButton("🚗 Трансферы ($20-200)", callback_data='transfer')],
            [InlineKeyboardButton("⬅️ Вернуться", callback_data='back')]
        ]
        await query.edit_message_text("📋 Наши услуги:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == 'contacts':
        text = f"""📞 КОНТАКТЫ Party Pattaya:

📱 WhatsApp/Viber: {CONTACTS['phone']}
📧 Email: {CONTACTS['email']}
🌐 Сайт: {CONTACTS['website']}
💬 Telegram: {CONTACTS['telegram']}
📸 Instagram: {CONTACTS['instagram']}"""
        keyboard = [[InlineKeyboardButton("⬅️ Вернуться", callback_data='back')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == 'back':
        keyboard = [
            [InlineKeyboardButton("📋 Услуги", callback_data='services')],
            [InlineKeyboardButton("📞 Контакты", callback_data='contacts')]
        ]
        await query.edit_message_text(
            "🎉 Добро пожаловать в Party Pattaya!\n\nВыберите раздел:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data in ['yacht', 'party', 'vip', 'transfer']:
        keyboard = [[InlineKeyboardButton("⬅️ Вернуться", callback_data='services')]]
        await query.edit_message_text(
            f"Вы выбрали: {query.data}\n\nСвяжитесь с нами: {CONTACTS['phone']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    logging.info("Party Pattaya Bot v10.1 запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
