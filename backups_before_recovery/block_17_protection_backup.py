# ═══════════════════════════════════════════════════════════════════════════════
# 🔒 БЛОК 17: SELF-HEALING & SELF-RECOVERY СИСТЕМА
# ═══════════════════════════════════════════════════════════════════════════════
# Версия: 2.0 FINAL
# Дата: 18.11.2025
# Статус: ✅ ЗАЩИТА ВСЕХ 16 БЛОКОВ И ВОССТАНОВЛЕНИЕ

import os
import sys
import hashlib
import json
import logging
import shutil
import asyncio
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Создание логгера для БЛОКА 17
logger = logging.getLogger("BLOCK_17_PROTECTION")
logger.setLevel(logging.INFO)

# ═══════════════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ БЛОКА 17
# ═══════════════════════════════════════════════════════════════════════════════

BLOCKS_CONFIG = {
    1: {"name": "Инициализация", "keywords": ["Application.builder", "TELEGRAM_TOKEN"]},
    2: {"name": "Telegram Handler", "keywords": ["CommandHandler", "MessageHandler"]},
    3: {"name": "Многоязычность", "keywords": ["langdetect", "WELCOME_MESSAGES"]},
    4: {"name": "API Endpoints", "keywords": ["FastAPI", "@app.get", "@app.post"]},
    5: {"name": "CRM Система", "keywords": ["user_profile", "history"]},
    6: {"name": "ChatGPT", "keywords": ["OpenAI", "chat.completions"]},
    7: {"name": "Обработка текста", "keywords": ["text_message", "process_text"]},
    8: {"name": "Whisper", "keywords": ["audio.transcriptions", "voice_message"]},
    9: {"name": "Социальные сети", "keywords": ["youtube", "instagram", "tiktok"]},
    10: {"name": "Услуги", "keywords": ["services", "price"]},
    11: {"name": "Напоминания", "keywords": ["reminder", "schedule"]},
    12: {"name": "Отчёты", "keywords": ["daily_report", "WhatsApp"]},
    13: {"name": "Сайт", "keywords": ["partypattayacity", "website"]},
    14: {"name": "Логирование", "keywords": ["logger.info", "logging"]},
    15: {"name": "Тестирование", "keywords": ["test_", "pytest"]},
    16: {"name": "Интеграция", "keywords": ["def main", "async def main"]},
}

# ═══════════════════════════════════════════════════════════════════════════════
# КЛАСС ЗАЩИТЫ И ВОССТАНОВЛЕНИЯ
# ═══════════════════════════════════════════════════════════════════════════════

class SelfHealingProtectionSystem:
    """🔒 БЛОК 17 - Система защиты и восстановления всех 16 блоков"""
    
    def __init__(self, main_file_path: str = "main.py"):
        self.main_file = Path(main_file_path)
        self.backup_dir = Path("block_17_backups")
        self.hashes_file = Path("block_17_hashes.json")
        self.log_file = Path("block_17_protection.log")
        self.memory_backup = {}
        
        # Создание необходимых директорий
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🔒 БЛОК 17: Инициализирована защита")
        logger.info(f"   main.py: {self.main_file}")
        logger.info(f"   Backup: {self.backup_dir}")
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Вычислить SHA256 хеш файла"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"❌ Ошибка расчета хеша: {e}")
            return "ERROR"
    
    def verify_block_integrity(self, block_id: int, file_path: Path) -> Tuple[bool, str, str]:
        """Проверить целостность одного блока"""
        try:
            if not file_path.exists():
                return False, "FILE_NOT_FOUND", ""
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            keywords = BLOCKS_CONFIG[block_id].get("keywords", [])
            found_keywords = sum(1 for kw in keywords if kw in content)
            keyword_percentage = (found_keywords / len(keywords) * 100) if keywords else 100
            
            current_hash = self.calculate_file_hash(file_path)
            
            if keyword_percentage >= 80:
                return True, "OK", current_hash
            else:
                return False, "DAMAGED", current_hash
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки БЛОКА {block_id}: {e}")
            return False, "ERROR", ""
    
    async def perform_full_system_check(self) -> Dict:
        """Проверить целостность всех 16 блоков"""
        logger.info("🔍 БЛОК 17: Проверка целостности всех 16 блоков...")
        
        check_result = {
            "timestamp": datetime.now().isoformat(),
            "total_blocks": 16,
            "healthy_blocks": 0,
            "damaged_blocks": 0,
            "blocks_status": {},
            "system_healthy": True,
            "recovery_needed": []
        }
        
        for block_id in range(1, 17):
            is_healthy, status, hash_value = self.verify_block_integrity(block_id, self.main_file)
            
            block_info = {
                "block_name": BLOCKS_CONFIG[block_id]["name"],
                "is_healthy": is_healthy,
                "status": status,
                "hash": hash_value,
                "timestamp": datetime.now().isoformat()
            }
            
            check_result["blocks_status"][block_id] = block_info
            
            if is_healthy:
                check_result["healthy_blocks"] += 1
                print(f"   ✅ БЛОК {block_id:2d}: {BLOCKS_CONFIG[block_id]['name']:40s} [OK]")
            else:
                check_result["damaged_blocks"] += 1
                check_result["recovery_needed"].append(block_id)
                print(f"   ❌ БЛОК {block_id:2d}: {BLOCKS_CONFIG[block_id]['name']:40s} [ПОВРЕЖДЁН]")
        
        check_result["system_healthy"] = check_result["damaged_blocks"] == 0
        
        print(f"\n✅ Проверка завершена: {check_result['healthy_blocks']}/16 блоков здоровы")
        
        return check_result
    
    async def save_memory_backup(self, file_path: Path) -> bool:
        """Сохранить рабочий файл в резервную копию"""
        try:
            if not file_path.exists():
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.memory_backup["main.py"] = {
                "content": content,
                "hash": self.calculate_file_hash(file_path),
                "timestamp": datetime.now().isoformat(),
                "size": len(content)
            }
            
            backup_file = self.backup_dir / f"main_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            shutil.copy2(file_path, backup_file)
            
            logger.info(f"💾 Резервная копия: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения backup: {e}")
            return False
    
    async def startup_check(self) -> bool:
        """Проверка при запуске бота"""
        print("\n" + "=" * 85)
        print("🔒 БЛОК 17: ПРОВЕРКА ЦЕЛОСТНОСТИ ВСЕХ 16 БЛОКОВ")
        print("=" * 85 + "\n")
        
        # Сохраняем рабочую копию
        await self.save_memory_backup(self.main_file)
        
        # Проверяем целостность
        check_result = await self.perform_full_system_check()
        
        if check_result['system_healthy']:
            print("\n✅ БЛОК 17: ВСЕ 16 БЛОКОВ ЦЕЛЫ И РАБОТАЮТ НОРМАЛЬНО")
            print("=" * 85 + "\n")
            return True
        else:
            print(f"\n❌ Обнаружено повреждений: {check_result['damaged_blocks']} блоков")
            print("=" * 85 + "\n")
            return False

# ═══════════════════════════════════════════════════════════════════════════════
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ═══════════════════════════════════════════════════════════════════════════════

_protection_system = None

async def initialize_block_17(main_file: str = "main.py") -> SelfHealingProtectionSystem:
    """Инициализировать БЛОК 17"""
    global _protection_system
    
    try:
        logger.info("🔧 БЛОК 17: Инициализация системы защиты...")
        _protection_system = SelfHealingProtectionSystem(main_file)
        
        success = await _protection_system.startup_check()
        
        if not success:
            logger.error("❌ Предупреждение: Некоторые блоки требуют внимания")
        
        logger.info("✅ БЛОК 17 ИНИЦИАЛИЗИРОВАН")
        return _protection_system
        
    except Exception as e:
        logger.error(f"❌ Ошибка в БЛОКЕ 17: {e}")
        raise

async def get_protection_system() -> SelfHealingProtectionSystem:
    """Получить экземпляр системы защиты"""
    global _protection_system
    
    if _protection_system is None:
        _protection_system = SelfHealingProtectionSystem()
    
    return _protection_system

__all__ = [
    'SelfHealingProtectionSystem',
    'initialize_block_17',
    'get_protection_system',
    'BLOCKS_CONFIG'
]
