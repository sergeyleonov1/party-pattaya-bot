"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    БЛОК 36: UNIVERSAL PROTECTION SYSTEM                       ║
║                         Party Pattaya Bot v10.2                               ║
║                                                                               ║
║  Полная система защиты блоков от несанкционированных изменений                ║
║  23 функции: 10 базовых + 13 расширенных по ТЗ                               ║
║                                                                               ║
║  Автор: Сергей Леонов                                                        ║
║  Дата: 26.11.2025                                                            ║
║  Статус: ✅ ЗАЩИЩЕН - изменения запрещены без разрешения                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import hashlib
import json
import os
import stat
import shutil
import asyncio
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import fcntl  # Для блокировки файлов на Unix

# ============================================================================
#                              КОНФИГУРАЦИЯ
# ============================================================================

class ProtectionLevel(Enum):
    """Уровни защиты блоков"""
    NONE = 0        # Без защиты
    LOW = 1         # Только логирование
    MEDIUM = 2      # Логирование + алерты
    HIGH = 3        # Логирование + алерты + блокировка
    CRITICAL = 4    # Полная защита + автооткат

@dataclass
class ProtectionConfig:
    """Конфигурация системы защиты"""
    # Пути
    base_dir: Path = Path(".")
    blocks_dir: Path = Path("blocks_ready")
    backups_dir: Path = Path("backups")
    logs_dir: Path = Path("logs")
    hashes_file: Path = Path("protection_hashes.json")
    
    # Telegram
    bot_token: str = ""
    admin_id: int = 359364877
    
    # Настройки
    auto_backup: bool = True
    auto_restore: bool = False
    alert_on_change: bool = True
    default_level: ProtectionLevel = ProtectionLevel.HIGH
    
    # Защищенные блоки
    protected_blocks: List[int] = field(default_factory=lambda: [1, 36])

# Глобальная конфигурация
CONFIG = ProtectionConfig()

# Хранилище данных защиты
PROTECTION_DATA: Dict[str, Any] = {
    "hashes": {},
    "locks": {},
    "readonly": set(),
    "events": [],
    "protected": set()
}

# Логгер
logger = logging.getLogger("block_36_protection")
logger.setLevel(logging.INFO)

# ============================================================================
#                      ЧАСТЬ 1: БАЗОВЫЕ ФУНКЦИИ (существующие)
# ============================================================================

def discover_all_blocks() -> Dict[str, Path]:
    """
    Обнаружение всех блоков в проекте
    
    Returns:
        Dict с именами блоков и путями к файлам
    """
    blocks = {}
    
    # Поиск в blocks_ready/
    blocks_dir = CONFIG.blocks_dir
    if blocks_dir.exists():
        for file in blocks_dir.glob("block_*.py"):
            block_name = file.stem
            blocks[block_name] = file
    
    # Поиск в modules/
    modules_dir = Path("modules")
    if modules_dir.exists():
        for file in modules_dir.glob("*.py"):
            if "block" in file.name.lower():
                blocks[file.stem] = file
    
    # Поиск в корне
    for file in Path(".").glob("block_*.py"):
        if file.stem not in blocks:
            blocks[file.stem] = file
    
    log_message(f"Обнаружено {len(blocks)} блоков", "INFO")
    return blocks


def calculate_hash(file_path: Path) -> Optional[str]:
    """
    Расчет SHA256 хеша файла
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        SHA256 хеш или None при ошибке
    """
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            return hashlib.sha256(content).hexdigest()
    except Exception as e:
        log_message(f"Ошибка расчета хеша {file_path}: {e}", "ERROR")
        return None


def log_message(message: str, level: str = "INFO"):
    """
    Логирование сообщений
    
    Args:
        message: Текст сообщения
        level: Уровень (INFO, WARNING, ERROR, CRITICAL)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    
    # Вывод в консоль
    print(log_entry)
    
    # Запись в файл
    try:
        CONFIG.logs_dir.mkdir(exist_ok=True)
        log_file = CONFIG.logs_dir / "protection.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"Ошибка записи лога: {e}")
    
    # Сохранение в память
    PROTECTION_DATA["events"].append({
        "timestamp": timestamp,
        "level": level,
        "message": message
    })


def save_hashes() -> bool:
    """
    Сохранение хешей всех защищенных файлов
    
    Returns:
        True при успехе
    """
    try:
        blocks = discover_all_blocks()
        hashes = {}
        
        for name, path in blocks.items():
            file_hash = calculate_hash(path)
            if file_hash:
                hashes[name] = {
                    "path": str(path),
                    "hash": file_hash,
                    "size": path.stat().st_size,
                    "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                    "protected_at": datetime.now().isoformat()
                }
        
        # Сохранение в JSON
        with open(CONFIG.hashes_file, 'w', encoding='utf-8') as f:
            json.dump(hashes, f, indent=2, ensure_ascii=False)
        
        PROTECTION_DATA["hashes"] = hashes
        log_message(f"Сохранено {len(hashes)} хешей в {CONFIG.hashes_file}", "INFO")
        return True
        
    except Exception as e:
        log_message(f"Ошибка сохранения хешей: {e}", "ERROR")
        return False


def check_integrity(auto_restore: bool = False, silent: bool = False) -> bool:
    """
    Проверка целостности всех защищенных файлов
    
    Args:
        auto_restore: Автоматически восстанавливать при изменениях
        silent: Не выводить сообщения
        
    Returns:
        True если все файлы в порядке
    """
    try:
        if not CONFIG.hashes_file.exists():
            if not silent:
                log_message("Файл хешей не найден, создаю...", "WARNING")
            save_hashes()
            return True
        
        with open(CONFIG.hashes_file, 'r', encoding='utf-8') as f:
            saved_hashes = json.load(f)
        
        all_ok = True
        modified_files = []
        
        for name, data in saved_hashes.items():
            file_path = Path(data["path"])
            
            if not file_path.exists():
                if not silent:
                    log_message(f"⚠️ Файл удален: {name}", "WARNING")
                modified_files.append((name, "DELETED", file_path))
                all_ok = False
                continue
            
            current_hash = calculate_hash(file_path)
            if current_hash != data["hash"]:
                if not silent:
                    log_message(f"🔴 ИЗМЕНЕН: {name}", "CRITICAL")
                modified_files.append((name, "MODIFIED", file_path))
                all_ok = False
                
                # Алерт
                if CONFIG.alert_on_change:
                    send_telegram_alert(name, "MODIFIED", f"Хеш изменился")
        
        if all_ok and not silent:
            log_message("✅ Все файлы в порядке", "INFO")
        
        # Автовосстановление
        if not all_ok and auto_restore:
            for name, status, path in modified_files:
                if status == "MODIFIED":
                    restore_from_backup(name, saved_hashes)
        
        return all_ok
        
    except Exception as e:
        log_message(f"Ошибка проверки целостности: {e}", "ERROR")
        return False


def create_backup(file_name: str, protected_files: Dict = None) -> bool:
    """
    Создание резервной копии файла
    
    Args:
        file_name: Имя блока
        protected_files: Словарь защищенных файлов
        
    Returns:
        True при успехе
    """
    try:
        if protected_files is None:
            protected_files = PROTECTION_DATA.get("hashes", {})
        
        if file_name not in protected_files:
            log_message(f"Файл {file_name} не найден в защищенных", "WARNING")
            return False
        
        source_path = Path(protected_files[file_name]["path"])
        if not source_path.exists():
            log_message(f"Исходный файл не существует: {source_path}", "ERROR")
            return False
        
        # Создание директории бекапов
        CONFIG.backups_dir.mkdir(exist_ok=True)
        
        # Имя бекапа с временной меткой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_name}_{timestamp}.py.bak"
        backup_path = CONFIG.backups_dir / backup_name
        
        # Копирование
        shutil.copy2(source_path, backup_path)
        
        log_message(f"✅ Бекап создан: {backup_path}", "INFO")
        return True
        
    except Exception as e:
        log_message(f"Ошибка создания бекапа: {e}", "ERROR")
        return False


def restore_from_backup(file_name: str, protected_files: Dict = None) -> bool:
    """
    Восстановление файла из последнего бекапа
    
    Args:
        file_name: Имя блока
        protected_files: Словарь защищенных файлов
        
    Returns:
        True при успехе
    """
    try:
        if protected_files is None:
            protected_files = PROTECTION_DATA.get("hashes", {})
        
        if file_name not in protected_files:
            log_message(f"Файл {file_name} не найден", "ERROR")
            return False
        
        # Поиск последнего бекапа
        backups = list(CONFIG.backups_dir.glob(f"{file_name}_*.py.bak"))
        if not backups:
            log_message(f"Бекапы для {file_name} не найдены", "ERROR")
            return False
        
        # Сортировка по дате (последний первым)
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_backup = backups[0]
        
        # Восстановление
        target_path = Path(protected_files[file_name]["path"])
        shutil.copy2(latest_backup, target_path)
        
        log_message(f"✅ Восстановлено из {latest_backup}", "INFO")
        
        # Пересчет хеша
        save_hashes()
        
        return True
        
    except Exception as e:
        log_message(f"Ошибка восстановления: {e}", "ERROR")
        return False


def send_telegram_alert(file_name: str, alert_type: str, details: str = ""):
    """
    Отправка алерта в Telegram
    
    Args:
        file_name: Имя файла
        alert_type: Тип алерта (MODIFIED, DELETED, BREACH)
        details: Дополнительные детали
    """
    try:
        import requests
        
        if not CONFIG.bot_token:
            log_message("Telegram токен не настроен", "WARNING")
            return
        
        emoji_map = {
            "MODIFIED": "🔴",
            "DELETED": "⚠️",
            "BREACH": "🚨",
            "INFO": "ℹ️"
        }
        
        emoji = emoji_map.get(alert_type, "📢")
        
        message = f"""
{emoji} **PROTECTION ALERT**

📁 Файл: `{file_name}`
🔔 Тип: {alert_type}
📝 Детали: {details}
🕐 Время: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        url = f"https://api.telegram.org/bot{CONFIG.bot_token}/sendMessage"
        payload = {
            "chat_id": CONFIG.admin_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            log_message(f"Алерт отправлен: {alert_type}", "INFO")
        else:
            log_message(f"Ошибка отправки алерта: {response.text}", "ERROR")
            
    except Exception as e:
        log_message(f"Ошибка Telegram: {e}", "ERROR")


def show_status():
    """Отображение статуса защиты всех блоков"""
    print("\n" + "="*60)
    print("         СТАТУС СИСТЕМЫ ЗАЩИТЫ БЛОКОВ")
    print("="*60)
    
    blocks = discover_all_blocks()
    
    # Загрузка сохраненных хешей
    saved_hashes = {}
    if CONFIG.hashes_file.exists():
        with open(CONFIG.hashes_file, 'r', encoding='utf-8') as f:
            saved_hashes = json.load(f)
    
    print(f"\n{'Блок':<30} {'Размер':<12} {'Статус':<15}")
    print("-"*60)
    
    for name, path in sorted(blocks.items()):
        size = f"{path.stat().st_size / 1024:.1f} KB"
        
        if name in saved_hashes:
            current_hash = calculate_hash(path)
            if current_hash == saved_hashes[name]["hash"]:
                status = "✅ Защищен"
            else:
                status = "🔴 ИЗМЕНЕН!"
        else:
            status = "⚪ Не защищен"
        
        # Проверка блокировки
        if name in PROTECTION_DATA["locks"]:
            status += " 🔒"
        
        # Проверка readonly
        if str(path) in PROTECTION_DATA["readonly"]:
            status += " [RO]"
        
        print(f"{name:<30} {size:<12} {status:<15}")
    
    print("-"*60)
    print(f"Всего блоков: {len(blocks)}")
    print(f"Защищено: {len(saved_hashes)}")
    print(f"Заблокировано: {len(PROTECTION_DATA['locks'])}")
    print("="*60 + "\n")


def full_setup():
    """Полная настройка системы защиты"""
    print("\n🔧 НАСТРОЙКА СИСТЕМЫ ЗАЩИТЫ БЛОКОВ\n")
    
    # 1. Создание директорий
    CONFIG.backups_dir.mkdir(exist_ok=True)
    CONFIG.logs_dir.mkdir(exist_ok=True)
    print("✅ Директории созданы")
    
    # 2. Обнаружение блоков
    blocks = discover_all_blocks()
    print(f"✅ Обнаружено {len(blocks)} блоков")
    
    # 3. Создание бекапов
    for name in blocks:
        create_backup(name, {name: {"path": str(blocks[name])}})
    print("✅ Бекапы созданы")
    
    # 4. Сохранение хешей
    save_hashes()
    print("✅ Хеши сохранены")
    
    # 5. Показать статус
    show_status()
    
    print("\n🎉 Система защиты настроена!\n")


# ============================================================================
#                    ЧАСТЬ 2: РАСШИРЕННЫЕ ФУНКЦИИ ПО ТЗ
# ============================================================================

async def protect_block(block_id: int, level: ProtectionLevel = None) -> Dict[str, Any]:
    """
    Защита блока от изменений
    
    Args:
        block_id: ID блока (1-46)
        level: Уровень защиты
        
    Returns:
        Dict с результатом операции
    """
    if level is None:
        level = CONFIG.default_level
    
    block_name = f"block_{block_id:02d}"
    blocks = discover_all_blocks()
    
    # Поиск блока
    block_path = None
    for name, path in blocks.items():
        if f"block_{block_id:02d}" in name or f"block_{block_id}_" in name:
            block_path = path
            block_name = name
            break
    
    if not block_path:
        return {
            "success": False,
            "error": f"Блок {block_id} не найден",
            "block_id": block_id
        }
    
    try:
        # Расчет хеша
        file_hash = calculate_hash(block_path)
        
        # Сохранение в защищенные
        PROTECTION_DATA["protected"].add(block_name)
        PROTECTION_DATA["hashes"][block_name] = {
            "path": str(block_path),
            "hash": file_hash,
            "level": level.value,
            "protected_at": datetime.now().isoformat(),
            "size": block_path.stat().st_size
        }
        
        # Создание бекапа
        if CONFIG.auto_backup:
            create_backup(block_name, PROTECTION_DATA["hashes"])
        
        # Установка readonly для HIGH и CRITICAL
        if level in [ProtectionLevel.HIGH, ProtectionLevel.CRITICAL]:
            await set_readonly(str(block_path), True)
        
        # Логирование
        log_protection_event(block_name, "PROTECTED", f"Уровень: {level.name}")
        
        # Сохранение хешей
        save_hashes()
        
        return {
            "success": True,
            "block_id": block_id,
            "block_name": block_name,
            "hash": file_hash,
            "level": level.name,
            "path": str(block_path)
        }
        
    except Exception as e:
        log_message(f"Ошибка защиты блока {block_id}: {e}", "ERROR")
        return {
            "success": False,
            "error": str(e),
            "block_id": block_id
        }


async def unprotect_block(block_id: int, admin_confirm: bool = False) -> Dict[str, Any]:
    """
    Снятие защиты с блока (только для админа)
    
    Args:
        block_id: ID блока
        admin_confirm: Подтверждение админа
        
    Returns:
        Dict с результатом
    """
    if not admin_confirm:
        return {
            "success": False,
            "error": "Требуется подтверждение админа (admin_confirm=True)",
            "block_id": block_id
        }
    
    block_name = f"block_{block_id:02d}"
    
    # Поиск в защищенных
    found_name = None
    for name in PROTECTION_DATA["protected"]:
        if f"block_{block_id:02d}" in name or f"block_{block_id}_" in name:
            found_name = name
            break
    
    if not found_name:
        return {
            "success": False,
            "error": f"Блок {block_id} не защищен",
            "block_id": block_id
        }
    
    try:
        # Получение пути
        block_data = PROTECTION_DATA["hashes"].get(found_name, {})
        block_path = block_data.get("path", "")
        
        # Снятие readonly
        if block_path:
            await set_readonly(block_path, False)
        
        # Удаление из защищенных
        PROTECTION_DATA["protected"].discard(found_name)
        
        # Удаление блокировки
        if found_name in PROTECTION_DATA["locks"]:
            del PROTECTION_DATA["locks"][found_name]
        
        # Логирование
        log_protection_event(found_name, "UNPROTECTED", "Снята защита админом")
        
        return {
            "success": True,
            "block_id": block_id,
            "block_name": found_name,
            "message": "Защита снята"
        }
        
    except Exception as e:
        log_message(f"Ошибка снятия защиты: {e}", "ERROR")
        return {
            "success": False,
            "error": str(e),
            "block_id": block_id
        }


async def verify_protection(block_id: int = None) -> Dict[str, Any]:
    """
    Проверка статуса защиты блока или всех блоков
    
    Args:
        block_id: ID блока (None = все блоки)
        
    Returns:
        Dict со статусом защиты
    """
    results = {}
    
    if block_id is not None:
        # Проверка конкретного блока
        block_name = f"block_{block_id:02d}"
        found = False
        
        for name in PROTECTION_DATA["hashes"]:
            if f"block_{block_id:02d}" in name or f"block_{block_id}_" in name:
                block_name = name
                found = True
                break
        
        if not found:
            return {
                "block_id": block_id,
                "protected": False,
                "status": "NOT_FOUND"
            }
        
        block_data = PROTECTION_DATA["hashes"].get(block_name, {})
        block_path = Path(block_data.get("path", ""))
        
        # Проверка существования
        if not block_path.exists():
            return {
                "block_id": block_id,
                "block_name": block_name,
                "protected": True,
                "status": "FILE_MISSING",
                "integrity": False
            }
        
        # Проверка хеша
        current_hash = calculate_hash(block_path)
        saved_hash = block_data.get("hash", "")
        
        return {
            "block_id": block_id,
            "block_name": block_name,
            "protected": block_name in PROTECTION_DATA["protected"],
            "locked": block_name in PROTECTION_DATA["locks"],
            "readonly": str(block_path) in PROTECTION_DATA["readonly"],
            "integrity": current_hash == saved_hash,
            "status": "OK" if current_hash == saved_hash else "MODIFIED",
            "level": block_data.get("level", 0),
            "protected_at": block_data.get("protected_at", "")
        }
    
    else:
        # Проверка всех блоков
        for name, data in PROTECTION_DATA["hashes"].items():
            block_path = Path(data.get("path", ""))
            
            if block_path.exists():
                current_hash = calculate_hash(block_path)
                saved_hash = data.get("hash", "")
                status = "OK" if current_hash == saved_hash else "MODIFIED"
            else:
                status = "FILE_MISSING"
            
            results[name] = {
                "protected": name in PROTECTION_DATA["protected"],
                "locked": name in PROTECTION_DATA["locks"],
                "integrity": status == "OK",
                "status": status
            }
        
        return {
            "total": len(results),
            "protected": sum(1 for v in results.values() if v["protected"]),
            "ok": sum(1 for v in results.values() if v["status"] == "OK"),
            "modified": sum(1 for v in results.values() if v["status"] == "MODIFIED"),
            "missing": sum(1 for v in results.values() if v["status"] == "FILE_MISSING"),
            "blocks": results
        }


async def check_modification(file_path: str) -> Dict[str, Any]:
    """
    Проверка файла на изменения
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        Dict с информацией об изменениях
    """
    path = Path(file_path)
    
    if not path.exists():
        return {
            "exists": False,
            "modified": True,
            "status": "FILE_MISSING"
        }
    
    # Поиск в защищенных
    block_name = None
    saved_data = None
    
    for name, data in PROTECTION_DATA["hashes"].items():
        if data.get("path") == str(path) or path.name in name:
            block_name = name
            saved_data = data
            break
    
    if not saved_data:
        return {
            "exists": True,
            "protected": False,
            "status": "NOT_PROTECTED"
        }
    
    # Сравнение хешей
    current_hash = calculate_hash(path)
    saved_hash = saved_data.get("hash", "")
    
    # Сравнение размеров
    current_size = path.stat().st_size
    saved_size = saved_data.get("size", 0)
    
    # Сравнение времени модификации
    current_mtime = datetime.fromtimestamp(path.stat().st_mtime)
    saved_mtime = datetime.fromisoformat(saved_data.get("modified", datetime.now().isoformat()))
    
    is_modified = current_hash != saved_hash
    
    result = {
        "exists": True,
        "protected": True,
        "block_name": block_name,
        "modified": is_modified,
        "status": "MODIFIED" if is_modified else "OK",
        "current_hash": current_hash,
        "saved_hash": saved_hash,
        "size_changed": current_size != saved_size,
        "current_size": current_size,
        "saved_size": saved_size,
        "time_changed": current_mtime > saved_mtime
    }
    
    # Алерт при изменении
    if is_modified and CONFIG.alert_on_change:
        await alert_on_breach(block_name, "MODIFICATION_DETECTED", result)
    
    return result


async def detect_tampering(deep_scan: bool = False) -> Dict[str, Any]:
    """
    Детекция попыток взлома/изменения защищенных файлов
    
    Args:
        deep_scan: Глубокое сканирование (проверка бекапов)
        
    Returns:
        Dict с результатами сканирования
    """
    tampering_detected = []
    warnings = []
    
    # Проверка всех защищенных файлов
    for name, data in PROTECTION_DATA["hashes"].items():
        file_path = Path(data.get("path", ""))
        
        # 1. Проверка существования
        if not file_path.exists():
            tampering_detected.append({
                "block": name,
                "type": "FILE_DELETED",
                "severity": "CRITICAL"
            })
            continue
        
        # 2. Проверка хеша
        current_hash = calculate_hash(file_path)
        if current_hash != data.get("hash"):
            tampering_detected.append({
                "block": name,
                "type": "HASH_MISMATCH",
                "severity": "HIGH",
                "expected": data.get("hash")[:16] + "...",
                "actual": current_hash[:16] + "..."
            })
        
        # 3. Проверка прав доступа
        if str(file_path) in PROTECTION_DATA["readonly"]:
            file_mode = file_path.stat().st_mode
            if file_mode & stat.S_IWUSR:  # Если запись разрешена
                warnings.append({
                    "block": name,
                    "type": "READONLY_BYPASSED",
                    "severity": "MEDIUM"
                })
        
        # 4. Глубокое сканирование
        if deep_scan:
            # Проверка бекапов
            backups = list(CONFIG.backups_dir.glob(f"{name}_*.py.bak"))
            if not backups:
                warnings.append({
                    "block": name,
                    "type": "NO_BACKUP",
                    "severity": "LOW"
                })
    
    # Результат
    result = {
        "scan_time": datetime.now().isoformat(),
        "deep_scan": deep_scan,
        "tampering_detected": len(tampering_detected) > 0,
        "tampering_count": len(tampering_detected),
        "warnings_count": len(warnings),
        "tampering": tampering_detected,
        "warnings": warnings,
        "status": "COMPROMISED" if tampering_detected else "SECURE"
    }
    
    # Логирование
    if tampering_detected:
        log_message(f"🚨 ОБНАРУЖЕН ВЗЛОМ! {len(tampering_detected)} нарушений", "CRITICAL")
        for t in tampering_detected:
            await alert_on_breach(t["block"], t["type"], t)
    
    return result


async def lock_file(file_path: str, timeout: int = 0) -> Dict[str, Any]:
    """
    Блокировка файла от изменений
    
    Args:
        file_path: Путь к файлу
        timeout: Таймаут блокировки в секундах (0 = бессрочно)
        
    Returns:
        Dict с результатом
    """
    path = Path(file_path)
    
    if not path.exists():
        return {
            "success": False,
            "error": "Файл не существует"
        }
    
    try:
        # Получение имени блока
        block_name = path.stem
        
        # Проверка существующей блокировки
        if block_name in PROTECTION_DATA["locks"]:
            return {
                "success": False,
                "error": "Файл уже заблокирован",
                "locked_at": PROTECTION_DATA["locks"][block_name]["locked_at"]
            }
        
        # Создание блокировки
        lock_data = {
            "path": str(path),
            "locked_at": datetime.now().isoformat(),
            "timeout": timeout,
            "expires_at": (datetime.now().isoformat() if timeout == 0 
                         else (datetime.now().timestamp() + timeout))
        }
        
        PROTECTION_DATA["locks"][block_name] = lock_data
        
        # Установка readonly
        await set_readonly(str(path), True)
        
        log_protection_event(block_name, "LOCKED", f"Timeout: {timeout}s")
        
        return {
            "success": True,
            "block_name": block_name,
            "locked_at": lock_data["locked_at"],
            "timeout": timeout
        }
        
    except Exception as e:
        log_message(f"Ошибка блокировки: {e}", "ERROR")
        return {
            "success": False,
            "error": str(e)
        }


async def unlock_file(file_path: str, force: bool = False) -> Dict[str, Any]:
    """
    Разблокировка файла
    
    Args:
        file_path: Путь к файлу
        force: Принудительная разблокировка
        
    Returns:
        Dict с результатом
    """
    path = Path(file_path)
    block_name = path.stem
    
    if block_name not in PROTECTION_DATA["locks"]:
        return {
            "success": False,
            "error": "Файл не заблокирован"
        }
    
    try:
        lock_data = PROTECTION_DATA["locks"][block_name]
        
        # Проверка таймаута
        if not force and lock_data["timeout"] > 0:
            if datetime.now().timestamp() < lock_data["expires_at"]:
                return {
                    "success": False,
                    "error": "Блокировка еще не истекла",
                    "expires_at": datetime.fromtimestamp(lock_data["expires_at"]).isoformat()
                }
        
        # Снятие блокировки
        del PROTECTION_DATA["locks"][block_name]
        
        # Снятие readonly
        await set_readonly(str(path), False)
        
        log_protection_event(block_name, "UNLOCKED", f"Force: {force}")
        
        return {
            "success": True,
            "block_name": block_name,
            "unlocked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        log_message(f"Ошибка разблокировки: {e}", "ERROR")
        return {
            "success": False,
            "error": str(e)
        }


async def set_readonly(file_path: str, readonly: bool = True) -> Dict[str, Any]:
    """
    Установка/снятие атрибута только для чтения
    
    Args:
        file_path: Путь к файлу
        readonly: True = только чтение, False = разрешить запись
        
    Returns:
        Dict с результатом
    """
    path = Path(file_path)
    
    if not path.exists():
        return {
            "success": False,
            "error": "Файл не существует"
        }
    
    try:
        current_mode = path.stat().st_mode
        
        if readonly:
            # Убираем права на запись
            new_mode = current_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH
            PROTECTION_DATA["readonly"].add(str(path))
        else:
            # Добавляем права на запись владельцу
            new_mode = current_mode | stat.S_IWUSR
            PROTECTION_DATA["readonly"].discard(str(path))
        
        os.chmod(path, new_mode)
        
        return {
            "success": True,
            "path": str(path),
            "readonly": readonly,
            "mode": oct(new_mode)
        }
        
    except Exception as e:
        log_message(f"Ошибка установки readonly: {e}", "ERROR")
        return {
            "success": False,
            "error": str(e)
        }


def create_protection_hash(data: Any, algorithm: str = "sha256") -> str:
    """
    Создание хеша для защиты данных
    
    Args:
        data: Данные для хеширования (строка, байты, dict)
        algorithm: Алгоритм хеширования (sha256, sha512, md5)
        
    Returns:
        Хеш-строка
    """
    # Преобразование данных в байты
    if isinstance(data, dict):
        data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
    elif isinstance(data, str):
        data_bytes = data.encode('utf-8')
    elif isinstance(data, bytes):
        data_bytes = data
    else:
        data_bytes = str(data).encode('utf-8')
    
    # Выбор алгоритма
    if algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "sha512":
        hasher = hashlib.sha512()
    elif algorithm == "md5":
        hasher = hashlib.md5()
    else:
        hasher = hashlib.sha256()
    
    hasher.update(data_bytes)
    return hasher.hexdigest()


def verify_hash(data: Any, expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Проверка соответствия хеша данных
    
    Args:
        data: Данные для проверки
        expected_hash: Ожидаемый хеш
        algorithm: Алгоритм хеширования
        
    Returns:
        True если хеши совпадают
    """
    actual_hash = create_protection_hash(data, algorithm)
    return actual_hash == expected_hash


def log_protection_event(
    block_name: str,
    event_type: str,
    details: str = "",
    severity: str = "INFO"
):
    """
    Логирование события защиты
    
    Args:
        block_name: Имя блока
        event_type: Тип события (PROTECTED, UNPROTECTED, MODIFIED, etc.)
        details: Дополнительные детали
        severity: Уровень важности
    """
    event = {
        "timestamp": datetime.now().isoformat(),
        "block": block_name,
        "type": event_type,
        "details": details,
        "severity": severity
    }
    
    PROTECTION_DATA["events"].append(event)
    
    # Форматирование сообщения
    emoji_map = {
        "PROTECTED": "🛡️",
        "UNPROTECTED": "🔓",
        "MODIFIED": "📝",
        "LOCKED": "🔒",
        "UNLOCKED": "🔑",
        "BREACH": "🚨",
        "RESTORED": "♻️"
    }
    
    emoji = emoji_map.get(event_type, "📋")
    message = f"{emoji} [{event_type}] {block_name}: {details}"
    
    log_message(message, severity)
    
    # Запись в отдельный файл событий
    try:
        events_file = CONFIG.logs_dir / "protection_events.json"
        
        existing_events = []
        if events_file.exists():
            with open(events_file, 'r', encoding='utf-8') as f:
                existing_events = json.load(f)
        
        existing_events.append(event)
        
        # Ограничение размера (последние 1000 событий)
        if len(existing_events) > 1000:
            existing_events = existing_events[-1000:]
        
        with open(events_file, 'w', encoding='utf-8') as f:
            json.dump(existing_events, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        log_message(f"Ошибка записи события: {e}", "ERROR")


async def alert_on_breach(
    block_name: str,
    breach_type: str,
    details: Dict[str, Any] = None
) -> bool:
    """
    Алерт при нарушении безопасности
    
    Args:
        block_name: Имя блока
        breach_type: Тип нарушения
        details: Детали нарушения
        
    Returns:
        True если алерт отправлен
    """
    # Логирование
    log_protection_event(block_name, "BREACH", f"{breach_type}: {details}", "CRITICAL")
    
    # Формирование сообщения
    details_str = json.dumps(details, indent=2, ensure_ascii=False) if details else ""
    
    # Отправка в Telegram
    send_telegram_alert(block_name, "BREACH", f"{breach_type}\n{details_str}")
    
    # Автоматические действия при CRITICAL
    block_data = PROTECTION_DATA["hashes"].get(block_name, {})
    level = block_data.get("level", 0)
    
    if level >= ProtectionLevel.CRITICAL.value:
        # Автоматический откат
        log_message(f"Автооткат для {block_name} (уровень CRITICAL)", "WARNING")
        await rollback_changes(block_name)
    
    return True


async def rollback_changes(block_name: str, backup_index: int = 0) -> Dict[str, Any]:
    """
    Откат изменений блока к предыдущей версии
    
    Args:
        block_name: Имя блока
        backup_index: Индекс бекапа (0 = последний)
        
    Returns:
        Dict с результатом
    """
    try:
        # Поиск бекапов
        backups = list(CONFIG.backups_dir.glob(f"{block_name}_*.py.bak"))
        
        if not backups:
            return {
                "success": False,
                "error": f"Бекапы для {block_name} не найдены"
            }
        
        # Сортировка (последний первым)
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if backup_index >= len(backups):
            return {
                "success": False,
                "error": f"Бекап с индексом {backup_index} не найден"
            }
        
        selected_backup = backups[backup_index]
        
        # Получение пути к оригиналу
        block_data = PROTECTION_DATA["hashes"].get(block_name)
        if not block_data:
            # Поиск по имени
            blocks = discover_all_blocks()
            for name, path in blocks.items():
                if block_name in name:
                    target_path = path
                    break
            else:
                return {
                    "success": False,
                    "error": f"Файл блока {block_name} не найден"
                }
        else:
            target_path = Path(block_data["path"])
        
        # Снятие readonly если установлен
        if str(target_path) in PROTECTION_DATA["readonly"]:
            await set_readonly(str(target_path), False)
        
        # Создание бекапа текущего состояния перед откатом
        if target_path.exists():
            pre_rollback_backup = CONFIG.backups_dir / f"{block_name}_pre_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py.bak"
            shutil.copy2(target_path, pre_rollback_backup)
        
        # Восстановление
        shutil.copy2(selected_backup, target_path)
        
        # Пересчет хеша
        new_hash = calculate_hash(target_path)
        if block_name in PROTECTION_DATA["hashes"]:
            PROTECTION_DATA["hashes"][block_name]["hash"] = new_hash
            PROTECTION_DATA["hashes"][block_name]["modified"] = datetime.now().isoformat()
        
        # Восстановление readonly
        if block_name in PROTECTION_DATA["protected"]:
            await set_readonly(str(target_path), True)
        
        # Сохранение хешей
        save_hashes()
        
        # Логирование
        log_protection_event(block_name, "RESTORED", f"Из бекапа: {selected_backup.name}")
        
        return {
            "success": True,
            "block_name": block_name,
            "restored_from": str(selected_backup),
            "new_hash": new_hash,
            "rollback_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        log_message(f"Ошибка отката: {e}", "ERROR")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
#                         ДОПОЛНИТЕЛЬНЫЕ УТИЛИТЫ
# ============================================================================

async def protect_all_critical_blocks():
    """Защита всех критических блоков (1, 36)"""
    results = []
    
    for block_id in CONFIG.protected_blocks:
        result = await protect_block(block_id, ProtectionLevel.CRITICAL)
        results.append(result)
        
    return results


async def run_security_check() -> Dict[str, Any]:
    """Полная проверка безопасности"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # 1. Проверка целостности
    integrity_ok = check_integrity(silent=True)
    results["checks"]["integrity"] = {
        "status": "PASS" if integrity_ok else "FAIL",
        "description": "Проверка хешей файлов"
    }
    
    # 2. Детекция взлома
    tampering = await detect_tampering(deep_scan=True)
    results["checks"]["tampering"] = {
        "status": "PASS" if not tampering["tampering_detected"] else "FAIL",
        "description": "Детекция несанкционированных изменений",
        "details": tampering
    }
    
    # 3. Проверка бекапов
    backups_ok = CONFIG.backups_dir.exists() and any(CONFIG.backups_dir.iterdir())
    results["checks"]["backups"] = {
        "status": "PASS" if backups_ok else "WARN",
        "description": "Наличие резервных копий"
    }
    
    # Общий статус
    all_pass = all(
        c["status"] == "PASS" 
        for c in results["checks"].values()
    )
    results["overall_status"] = "SECURE" if all_pass else "ATTENTION_REQUIRED"
    
    return results


def get_protection_stats() -> Dict[str, Any]:
    """Получение статистики защиты"""
    return {
        "total_protected": len(PROTECTION_DATA["protected"]),
        "total_locked": len(PROTECTION_DATA["locks"]),
        "total_readonly": len(PROTECTION_DATA["readonly"]),
        "total_events": len(PROTECTION_DATA["events"]),
        "hashes_saved": len(PROTECTION_DATA["hashes"]),
        "backups_dir": str(CONFIG.backups_dir),
        "logs_dir": str(CONFIG.logs_dir)
    }


# ============================================================================
#                              MAIN / CLI
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    БЛОК 36: UNIVERSAL PROTECTION SYSTEM                       ║
║                         Party Pattaya Bot v10.2                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "setup":
            full_setup()
        elif command == "status":
            show_status()
        elif command == "check":
            check_integrity()
        elif command == "protect":
            if len(sys.argv) > 2:
                block_id = int(sys.argv[2])
                asyncio.run(protect_block(block_id))
            else:
                print("Укажите ID блока: python block_36_protection.py protect 1")
        elif command == "scan":
            result = asyncio.run(detect_tampering(deep_scan=True))
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"Неизвестная команда: {command}")
            print("Доступные команды: setup, status, check, protect <id>, scan")
    else:
        # Интерактивный режим
        print("Команды:")
        print("  1. Полная настройка")
        print("  2. Показать статус")
        print("  3. Проверить целостность")
        print("  4. Сканировать на взлом")
        print("  5. Выход")
        print()
        
        choice = input("Выберите действие (1-5): ").strip()
        
        if choice == "1":
            full_setup()
        elif choice == "2":
            show_status()
        elif choice == "3":
            check_integrity()
        elif choice == "4":
            result = asyncio.run(detect_tampering(deep_scan=True))
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif choice == "5":
            print("Выход")
        else:
            print("Неверный выбор")
