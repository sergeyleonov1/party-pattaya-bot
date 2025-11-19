import logging
import json
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MonitoringLogger:
    """БЛОК 14: Система мониторинга и логирования"""
    
    def __init__(self):
        self.logs = []
        self.metrics = {}
        logger.info("✅ БЛОК 14: Monitoring & Logging инициализирован")
    
    def log_user_action(self, user_id: int, action: str, details: Dict[str, Any]):
        """Логировать действие пользователя"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "details": details
        }
        self.logs.append(log_entry)
        logger.info(f"👤 User {user_id}: {action}")
    
    def log_error(self, error_type: str, error_msg: str, user_id: int = None):
        """Логировать ошибки"""
        error_log = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_msg": error_msg,
            "user_id": user_id
        }
        self.logs.append(error_log)
        logger.error(f"❌ {error_type}: {error_msg}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику"""
        return {
            "total_logs": len(self.logs),
            "total_errors": len([l for l in self.logs if "error_type" in l]),
            "last_log": self.logs[-1] if self.logs else None
        }
    
    def export_logs(self, filename: str = "bot_logs.json"):
        """Экспортировать логи в JSON"""
        with open(filename, 'w') as f:
            json.dump(self.logs, f, indent=2)
        logger.info(f"✅ Логи экспортированы в {filename}")

