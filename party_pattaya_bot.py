#!/usr/bin/env python3
import os, sys, logging, asyncio, io, json, hashlib, threading, re, pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# ЛОГИРОВАНИЕ
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# ═══════════════════════════════════════════════════════════════════════════

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "359364877"))
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://party_user:party_password@localhost:5432/party_pattaya_bot")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://party_user:party_password@localhost:27017/?authSource=admin")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

logger.info("🚀 PARTY PATTAYA BOT v8.1 WITH DETAILED LOGGING")
logger.info(f"TELEGRAM_TOKEN: {'SET' if TELEGRAM_TOKEN else 'NOT SET'}")
logger.info(f"OPENAI_API_KEY: {'SET' if OPENAI_API_KEY else 'NOT SET'}")
logger.info(f"DATABASE_URL: {POSTGRES_URL}")
logger.info(f"MONGODB_URL: {MONGODB_URL}")
logger.info(f"REDIS_URL: {REDIS_URL}")

# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════

try:
    from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, JSON, text
    from sqlalchemy.orm import sessionmaker, Session, declarative_base
    from sqlalchemy.pool import NullPool
    SQLALCHEMY_AVAILABLE = True
    logger.info("✅ SQLAlchemy imported successfully")
    Base = declarative_base()
except Exception as e:
    SQLALCHEMY_AVAILABLE = False
    Base = None
    logger.error(f"❌ SQLAlchemy import failed: {type(e).__name__}: {e}")

try:
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
    logger.info("✅ PyMongo imported successfully")
except Exception as e:
    PYMONGO_AVAILABLE = False
    logger.error(f"❌ PyMongo import failed: {type(e).__name__}: {e}")

try:
    import redis
    REDIS_AVAILABLE = True
    logger.info("✅ Redis imported successfully")
except Exception as e:
    REDIS_AVAILABLE = False
    logger.error(f"❌ Redis import failed: {type(e).__name__}: {e}")

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    FASTAPI_AVAILABLE = True
    logger.info("✅ FastAPI imported successfully")
except:
    FASTAPI_AVAILABLE = False
    logger.warning("⚠️ FastAPI not available")

# ═══════════════════════════════════════════════════════════════════════════
# SQLALCHEMY MODELS
# ═══════════════════════════════════════════════════════════════════════════

if SQLALCHEMY_AVAILABLE and Base:
    logger.info("📝 Defining SQLAlchemy models...")
    
    class UserProfile(Base):
        __tablename__ = "user_profiles"
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, unique=True, index=True)
        name = Column(String(255))
        username = Column(String(255))
        language = Column(String(10))
        created_at = Column(DateTime, default=datetime.utcnow)
        interactions = Column(Integer, default=0)

    class Reminder(Base):
        __tablename__ = "reminders"
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, index=True)
        event_type = Column(String(255))
        event_date = Column(String(255))
        event_time = Column(String(255))
        user_name = Column(String(255))
        status = Column(String(50), default="pending")

    class Payment(Base):
        __tablename__ = "payments"
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, index=True)
        amount = Column(Float)
        method = Column(String(50))
        status = Column(String(50), default="completed")
    
    logger.info("✅ Models defined successfully")

# ═══════════════════════════════════════════════════════════════════════════
# POSTGRESQL MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class PostgreSQLManager:
    def __init__(self):
        try:
            logger.info("=" * 80)
            logger.info("🔗 POSTGRESQL MANAGER INITIALIZATION")
            logger.info("=" * 80)
            logger.info(f"URL: {POSTGRES_URL}")
            
            if not SQLALCHEMY_AVAILABLE:
                logger.error("❌ SQLAlchemy not available")
                self.available = False
                return
            
            logger.info("📦 Creating SQLAlchemy engine...")
            self.engine = create_engine(
                POSTGRES_URL,
                poolclass=NullPool,
                echo=False,
                connect_args={"connect_timeout": 10}
            )
            
            logger.info("🔍 Testing connection...")
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info(f"✅ Connection test successful: {result.fetchone()}")
            
            logger.info("📊 Creating tables...")
            Base.metadata.create_all(self.engine)
            logger.info("✅ Tables created successfully")
            
            self.SessionLocal = sessionmaker(bind=self.engine)
            logger.info("✅ PostgreSQL Manager initialized successfully")
            self.available = True
            
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ POSTGRESQL ERROR: {type(e).__name__}")
            logger.error(f"Message: {str(e)}")
            logger.error("=" * 80)
            self.available = False
    
    def save_user_profile(self, user_id: int, profile_data: Dict) -> bool:
        try:
            if not self.available:
                logger.warning("PostgreSQL not available")
                return False
            
            logger.debug(f"Saving profile for user {user_id}")
            session = self.SessionLocal()
            user = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if user:
                logger.debug(f"User {user_id} exists, updating...")
                user.interactions = profile_data.get("interactions", 0)
            else:
                logger.debug(f"User {user_id} not found, creating...")
                user = UserProfile(
                    user_id=user_id,
                    name=profile_data.get("name"),
                    username=profile_data.get("username"),
                    language=profile_data.get("language"),
                    interactions=profile_data.get("interactions", 0)
                )
                session.add(user)
            
            session.commit()
            session.close()
            logger.info(f"✅ Profile {user_id} saved to PostgreSQL")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving profile: {type(e).__name__}: {e}")
            return False

# ═══════════════════════════════════════════════════════════════════════════
# MONGODB MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class MongoDBManager:
    def __init__(self):
        try:
            logger.info("=" * 80)
            logger.info("🔗 MONGODB MANAGER INITIALIZATION")
            logger.info("=" * 80)
            logger.info(f"URL: {MONGODB_URL}")
            
            logger.info("📦 Creating MongoDB client...")
            self.client = MongoClient(
                MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=10000
            )
            
            logger.info("🔍 Testing connection...")
            self.client.server_info()
            logger.info("✅ Connection test successful")
            
            self.db = self.client["party_pattaya_bot"]
            self.messages_collection = self.db["user_messages"]
            self.analytics_collection = self.db["analytics"]
            
            logger.info("✅ MongoDB Manager initialized successfully")
            self.available = True
            
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ MONGODB ERROR: {type(e).__name__}")
            logger.error(f"Message: {str(e)}")
            logger.error("=" * 80)
            self.available = False
    
    def save_message(self, user_id: int, message: str, message_type: str = "text") -> bool:
        try:
            if not self.available:
                logger.warning("MongoDB not available")
                return False
            
            logger.debug(f"Saving message from user {user_id}")
            self.messages_collection.insert_one({
                "user_id": user_id,
                "message": message,
                "message_type": message_type,
                "timestamp": datetime.utcnow()
            })
            logger.info(f"✅ Message from {user_id} saved to MongoDB")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving message: {type(e).__name__}: {e}")
            return False

# ═══════════════════════════════════════════════════════════════════════════
# REDIS MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class RedisManager:
    def __init__(self):
        try:
            logger.info("=" * 80)
            logger.info("🔗 REDIS MANAGER INITIALIZATION")
            logger.info("=" * 80)
            logger.info(f"URL: {REDIS_URL}")
            
            logger.info("📦 Creating Redis client...")
            self.redis = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=10,
                socket_timeout=10
            )
            
            logger.info("🔍 Testing connection...")
            pong = self.redis.ping()
            logger.info(f"✅ Connection test successful: {pong}")
            
            logger.info("✅ Redis Manager initialized successfully")
            self.available = True
            
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ REDIS ERROR: {type(e).__name__}")
            logger.error(f"Message: {str(e)}")
            logger.error("=" * 80)
            self.available = False
    
    def set_session(self, user_id: int, session_data: Dict, ttl: int = 3600) -> bool:
        try:
            if not self.available:
                logger.warning("Redis not available")
                return False
            
            logger.debug(f"Saving session for user {user_id}")
            key = f"session:{user_id}"
            self.redis.setex(key, ttl, json.dumps(session_data))
            logger.info(f"✅ Session {user_id} saved to Redis")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving session: {type(e).__name__}: {e}")
            return False

# ═══════════════════════════════════════════════════════════════════════════
# ИНИЦИАЛИЗАЦИЯ МЕНЕДЖЕРОВ БД
# ═══════════════════════════════════════════════════════════════════════════

logger.info("\n" + "=" * 80)
logger.info("INITIALIZING DATABASE MANAGERS")
logger.info("=" * 80 + "\n")

postgres_manager = PostgreSQLManager() if SQLALCHEMY_AVAILABLE else None
mongodb_manager = MongoDBManager() if PYMONGO_AVAILABLE else None
redis_manager = RedisManager() if REDIS_AVAILABLE else None

# ═══════════════════════════════════════════════════════════════════════════
# TELEGRAM CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

LANGUAGES_FULL = {
    "ru": "Русский", "en": "English", "es": "Español", "fr": "Français", "de": "Deutsch",
    "it": "Italiano", "pt": "Português", "ja": "日本語", "ko": "한국어", "th": "ไทย"
}

WELCOME_MESSAGES = {
    "ru": "Привет! 👋\nЯ помощник Party Pattaya City!",
    "en": "Hello! 👋\nI'm Party Pattaya City assistant!"
}

SERVICES = {
    "yacht": "🛥️ Аренда яхты - $500-2000",
    "party": "🎊 Организация вечеринки - $1000-5000",
    "vip": "💎 VIP сервис - $2000-10000"
}

user_profiles = {}
user_history = {}

# ═══════════════════════════════════════════════════════════════════════════
# CODE PROTECTION
# ═══════════════════════════════════════════════════════════════════════════

class CodeProtection:
    PROTECTED_FILE = "/Users/polina4/Desktop/Bot Party Pattaya/party_pattaya_bot.py"
    HASH_FILE = "/Users/polina4/Desktop/Bot Party Pattaya/.bot_hash"
    
    @staticmethod
    def calculate_hash(file_path: str) -> str:
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return ""
    
    @staticmethod
    def save_hash():
        try:
            current_hash = CodeProtection.calculate_hash(CodeProtection.PROTECTED_FILE)
            with open(CodeProtection.HASH_FILE, 'w') as f:
                f.write(current_hash)
            logger.info(f"✅ SHA256 сохранен")
            return True
        except:
            return False
    
    @staticmethod
    def verify_integrity() -> bool:
        try:
            if not os.path.exists(CodeProtection.HASH_FILE):
                CodeProtection.save_hash()
                return True
            with open(CodeProtection.HASH_FILE, 'r') as f:
                stored_hash = f.read().strip()
            current_hash = CodeProtection.calculate_hash(CodeProtection.PROTECTED_FILE)
            if stored_hash != current_hash:
                logger.error(f"❌ КОД ИЗМЕНЕН БЕЗ РАЗРЕШЕНИЯ!")
                return False
            logger.info(f"✅ Целостность подтверждена")
            return True
        except:
            return False

# ═══════════════════════════════════════════════════════════════════════════
# BOT CLASS
# ═══════════════════════════════════════════════════════════════════════════

class PartyPattayaBot:
    def __init__(self):
        logger.info("✅ Инициализация бота")
        if not CodeProtection.verify_integrity():
            sys.exit(1)
        self.app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        logger.info(f"👤 User {user_id} started bot")
        
        if user_id not in user_profiles:
            user_profiles[user_id] = {
                "name": user.first_name,
                "username": user.username,
                "language": user.language_code or "en"
            }
            logger.debug(f"Creating new profile for {user_id}")
            
            if postgres_manager and postgres_manager.available:
                logger.debug(f"Saving to PostgreSQL...")
                postgres_manager.save_user_profile(user_id, user_profiles[user_id])
            
            if redis_manager and redis_manager.available:
                logger.debug(f"Saving to Redis...")
                redis_manager.set_session(user_id, user_profiles[user_id])
        
        lang = user.language_code if user.language_code in WELCOME_MESSAGES else "en"
        keyboard = [[InlineKeyboardButton("🎊 Услуги", callback_data="services")]]
        await update.message.reply_text(WELCOME_MESSAGES.get(lang), reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("/start /help /databases")
    
    async def databases_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = f"""🗄️ СТАТУС БАЗ ДАННЫХ:
PostgreSQL: {'✅ CONNECTED' if postgres_manager and postgres_manager.available else '❌ NOT CONNECTED'}
MongoDB: {'✅ CONNECTED' if mongodb_manager and mongodb_manager.available else '❌ NOT CONNECTED'}
Redis: {'✅ CONNECTED' if redis_manager and redis_manager.available else '❌ NOT CONNECTED'}"""
        await update.message.reply_text(text)
    
    async def button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data == "services":
            text = "🎊 УСЛУГИ:\n\n" + "\n".join(SERVICES.values())
            await query.edit_message_text(text)
    
    async def text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text
        logger.info(f"📝 Message from {user_id}: {text[:50]}")
        
        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append(text)
        
        if mongodb_manager and mongodb_manager.available:
            mongodb_manager.save_message(user_id, text)
    
    def setup_handlers(self):
        logger.info("🔧 Setting up handlers...")
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("databases", self.databases_command))
        self.app.add_handler(CallbackQueryHandler(self.button_click))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_message))
        logger.info("✅ Handlers setup complete")
    
    def run(self):
        logger.info("\n" + "=" * 80)
        logger.info("✅ PARTY PATTAYA BOT v8.1 STARTING")
        logger.info("=" * 80)
        logger.info("🗄️ DATABASE STATUS:")
        logger.info(f"   PostgreSQL: {'✅' if postgres_manager and postgres_manager.available else '❌'}")
        logger.info(f"   MongoDB: {'✅' if mongodb_manager and mongodb_manager.available else '❌'}")
        logger.info(f"   Redis: {'✅' if redis_manager and redis_manager.available else '❌'}")
        logger.info("=" * 80 + "\n")
        self.setup_handlers()
        logger.info("✅ БОТ РАБОТАЕТ")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    CodeProtection.save_hash()
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        bot = PartyPattayaBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {type(e).__name__}: {e}")
        sys.exit(1)
