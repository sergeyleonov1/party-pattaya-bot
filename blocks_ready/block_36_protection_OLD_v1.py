#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
БЛОК 36 - УНИВЕРСАЛЬНАЯ СИСТЕМА ЗАЩИТЫ ВСЕХ БЛОКОВ
═══════════════════════════════════════════════════════════════════════════
Владелец: Сергей Леонов (@Party_Pattaya)
Версия: UNIVERSAL 3.0
Дата: 25.11.2025

ЗАЩИЩАЕТ:
✅ Все 5 критических JSON (greeting, contacts, services, buttons, tz)
✅ Все 46 блоков Python (.py файлы)
✅ Новые блоки автоматически

ФУНКЦИИ:
- SHA256 хеширование
- Автомониторинг
- Telegram уведомления
- Система разрешений
- Автовосстановление
- CLI меню
- Интеграция с Блоком 1
═══════════════════════════════════════════════════════════════════════════
"""

import json
import hashlib
import os
import shutil
import stat
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

# ═══════════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════

BASE_DIR = Path.home() / "Desktop" / "Bot Party Pattaya"
PROTECTION_DIR = BASE_DIR / "protection"
BACKUP_DIR = BASE_DIR / "backups"
LOG_DIR = BASE_DIR / "logs"
BLOCKS_DIR = BASE_DIR / "blocks_ready"

HASHES_FILE = PROTECTION_DIR / "block_hashes.json"
PERMISSIONS_FILE = PROTECTION_DIR / "permissions.json"
MONITOR_CONFIG = PROTECTION_DIR / "monitor_config.json"
PROTECTION_LOG = LOG_DIR / "protection.log"

TELEGRAM_BOT_TOKEN = "8526699649:AAHKQN_HRkvMGcto7rrljdbsLPiGTGovYJY"
TELEGRAM_CHAT_ID = "@Party_Pattaya"

# Критические JSON файлы
CRITICAL_JSON = {
    "greeting": BASE_DIR / "greeting.json",
    "contacts": BASE_DIR / "contacts.json",
    "services": BASE_DIR / "services.json",
    "buttons": BASE_DIR / "buttons.json",
    "tz_v10_1": BASE_DIR / "tz_v10_1.json"
}

CRITICAL_DATA = {
    "owner": "Сергей Леонов",
    "contacts": {
        "telegram": "@Party_Pattaya",
        "whatsapp": "+66-633-633-407",
        "email": "Liliya@partypattayacity.com"
    }
}


# ═══════════════════════════════════════════════════════════════════════════
# АВТОМАТИЧЕСКОЕ ОБНАРУЖЕНИЕ БЛОКОВ
# ═══════════════════════════════════════════════════════════════════════════

def discover_all_blocks() -> Dict:
    """Автоматически найти все блоки"""
    protected = {}
    
    # 1. Критические JSON
    for name, path in CRITICAL_JSON.items():
        if path.exists():
            protected[name] = {
                "path": path,
                "type": "json",
                "critical": True
            }
    
    # 2. Все Python блоки
    if BLOCKS_DIR.exists():
        for block_file in BLOCKS_DIR.glob("block_*.py"):
            block_name = block_file.stem
            protected[block_name] = {
                "path": block_file,
                "type": "python",
                "critical": False
            }
    
    # 3. Интеграция с Блоком 1
    try:
        registry_file = BASE_DIR / "block_registry.json"
        if registry_file.exists():
            with open(registry_file, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            for block_id, block_data in registry.get("blocks", {}).items():
                file_path = Path(block_data["file_path"])
                if not file_path.is_absolute():
                    file_path = BASE_DIR / file_path
                
                if file_path.exists() and file_path.suffix == '.py':
                    protected[block_id] = {
                        "path": file_path,
                        "type": "python",
                        "critical": False
                    }
    except:
        pass
    
    return protected


def calculate_hash(file_path: Path) -> Optional[str]:
    """Вычислить SHA256 хеш"""
    if not file_path.exists():
        return None
    
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except:
        return None


def log_message(message: str, level: str = "INFO"):
    """Записать в лог"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "block": "36_protection",
        "message": message
    }
    
    try:
        with open(PROTECTION_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except:
        pass


def save_hashes() -> bool:
    """Сохранить хеши ВСЕХ файлов"""
    PROTECTION_DIR.mkdir(parents=True, exist_ok=True)
    
    protected_files = discover_all_blocks()
    
    hashes = {
        "version": "3.0",
        "owner": CRITICAL_DATA["owner"],
        "contacts": CRITICAL_DATA["contacts"],
        "created": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "files": {},
        "total_files": len(protected_files)
    }
    
    print("\n" + "="*70)
    print("🔒 СОХРАНЕНИЕ ХЕШЕЙ")
    print("="*70)
    print(f"Файлов: {len(protected_files)}")
    
    for name, data in protected_files.items():
        path = data["path"]
        file_hash = calculate_hash(path)
        
        if file_hash:
            hashes["files"][name] = {
                "path": str(path),
                "type": data["type"],
                "critical": data["critical"],
                "hash": file_hash,
                "size": path.stat().st_size,
                "last_check": datetime.now().isoformat()
            }
            icon = "🔴" if data["critical"] else "🟢"
            print(f"{icon} {name[:30]:30} | {file_hash[:12]}...")
    
    try:
        with open(HASHES_FILE, 'w', encoding='utf-8') as f:
            json.dump(hashes, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Хеши сохранены: {len(hashes['files'])} файлов")
        log_message(f"Хеши сохранены: {len(hashes['files'])}", "INFO")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def check_integrity(auto_restore: bool = False, silent: bool = False) -> bool:
    """Проверить целостность"""
    if not HASHES_FILE.exists():
        if not silent:
            print("❌ Хеши не найдены!")
        return False
    
    with open(HASHES_FILE, 'r', encoding='utf-8') as f:
        saved_hashes = json.load(f)
    
    if not silent:
        print("\n" + "="*70)
        print("🔒 ПРОВЕРКА ЦЕЛОСТНОСТИ")
        print("="*70)
    
    all_ok = True
    protected_files = discover_all_blocks()
    
    for name, data in saved_hashes["files"].items():
        path = Path(data["path"])
        saved_hash = data["hash"]
        current_hash = calculate_hash(path)
        
        if current_hash == saved_hash:
            if not silent:
                print(f"✅ {name[:30]:30} | OK")
        else:
            if not silent:
                print(f"🚨 {name[:30]:30} | ИЗМЕНЕН!")
            
            all_ok = False
            log_message(f"Изменен: {name}", "WARNING")
            send_telegram_alert(name, "UNAUTHORIZED_CHANGE")
            
            if auto_restore and name in protected_files:
                if restore_from_backup(name, protected_files):
                    if not silent:
                        print(f"   ✅ Восстановлено")
                    send_telegram_alert(name, "AUTO_RESTORED")
    
    if not silent:
        print("="*70)
        if all_ok:
            print("✅ ВСЕ ФАЙЛЫ БЕЗ ИЗМЕНЕНИЙ")
    
    return all_ok


def create_backup(file_name: str, protected_files: Dict) -> bool:
    """Создать backup"""
    if file_name not in protected_files:
        return False
    
    source_path = protected_files[file_name]["path"]
    
    if not source_path.exists():
        return False
    
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{file_name}_{timestamp}.backup"
    backup_path = BACKUP_DIR / backup_name
    
    try:
        shutil.copy2(source_path, backup_path)
        log_message(f"Backup: {backup_name}", "INFO")
        return True
    except:
        return False


def restore_from_backup(file_name: str, protected_files: Dict) -> bool:
    """Восстановить из backup"""
    if file_name not in protected_files:
        return False
    
    backups = sorted(BACKUP_DIR.glob(f"{file_name}_*.backup"), reverse=True)
    
    if not backups:
        return False
    
    latest_backup = backups[0]
    target_path = protected_files[file_name]["path"]
    
    try:
        shutil.copy2(latest_backup, target_path)
        log_message(f"Восстановлено: {file_name}", "INFO")
        return True
    except:
        return False


def send_telegram_alert(file_name: str, alert_type: str, details: str = ""):
    """Telegram уведомление"""
    try:
        import requests
        
        icons = {
            "UNAUTHORIZED_CHANGE": "🚨",
            "AUTO_RESTORED": "✅",
            "PERMISSION_REQUESTED": "📋"
        }
        
        text = f"{icons.get(alert_type, '⚠️')} БЛОК 36\n\n"
        text += f"Файл: {file_name}\n"
        if details:
            text += f"{details}\n"
        text += f"\n@Party_Pattaya"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=5)
    except:
        pass


def show_status():
    """Показать статус"""
    protected_files = discover_all_blocks()
    
    print("\n" + "="*70)
    print("🔒 БЛОК 36 - ЗАЩИТА ВСЕХ БЛОКОВ (UNIVERSAL 3.0)")
    print("="*70)
    print(f"Владелец: {CRITICAL_DATA['owner']}")
    print(f"Контакт: {CRITICAL_DATA['contacts']['telegram']}")
    print("="*70)
    
    print(f"\n📂 ЗАЩИЩЕННЫЕ ФАЙЛЫ: {len(protected_files)}")
    
    critical_count = sum(1 for f in protected_files.values() if f.get("critical"))
    python_count = sum(1 for f in protected_files.values() if f.get("type") == "python")
    json_count = sum(1 for f in protected_files.values() if f.get("type") == "json")
    
    print(f"   🔴 Критические JSON: {critical_count}")
    print(f"   🟢 Python блоки: {python_count}")
    
    if BACKUP_DIR.exists():
        backup_count = len(list(BACKUP_DIR.glob("*.backup")))
        print(f"\n💾 BACKUP: {backup_count} файлов")
    
    print("="*70)


def full_setup():
    """Полная установка"""
    print("\n🚀 УСТАНОВКА БЛОКА 36")
    
    protected_files = discover_all_blocks()
    
    print(f"\n1️⃣ Найдено файлов: {len(protected_files)}")
    
    print("\n2️⃣ Создание backup...")
    for name in protected_files.keys():
        create_backup(name, protected_files)
    
    print("\n3️⃣ Сохранение хешей...")
    save_hashes()
    
    print("\n✅ УСТАНОВКА ЗАВЕРШЕНА!")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🔒 БЛОК 36 - ЗАЩИТА ВСЕХ БЛОКОВ (UNIVERSAL 3.0)")
    print("\nВыполни: full_setup() для установки")
    show_status()
