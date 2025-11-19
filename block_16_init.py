"""
ИНИЦИАЛИЗАЦИЯ И ИНТЕГРАЦИЯ БЛОКА 16
Этот файл подключает БЛОК 16 к основному боту
"""

import asyncio
import logging
from block_16_seo import SEOSearchEngineIntegrationBlock16, create_integrated_block, integration_layer

logger = logging.getLogger(__name__)

# Глобальный экземпляр БЛОКА 16
block_16_instance = None

async def initialize_block_16():
    """
    Инициализация БЛОКА 16 при запуске бота
    """
    global block_16_instance
    
    try:
        logger.info("🚀 Инициализация БЛОКА 16...")
        
        # 1. Создаем экземпляр БЛОКА 16
        block_16_instance = SEOSearchEngineIntegrationBlock16(
            telegram_admin_id="@Sergey080637"
        )
        
        logger.info("✅ БЛОК 16 инициализирован")
        
        # 2. Настраиваем локальную геоптимизацию
        block_16_instance.setup_local_geo_optimization()
        logger.info("✅ Локальная геоптимизация настроена (Pattaya + 30km)")
        
        # 3. Оптимизируем Google My Business
        gmb = block_16_instance.optimize_google_my_business()
        logger.info("✅ Google My Business подготовлен")
        
        # 4. Запускаем расписание ежедневных отчетов (08:00 UTC+7)
        asyncio.create_task(block_16_instance.schedule_daily_ai_learning())
        logger.info("✅ Ежедневные отчеты запланированы (08:00 UTC+7)")
        
        return block_16_instance
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БЛОКА 16: {e}")
        raise

def link_other_blocks_to_block_16(block_handlers):
    """
    Линкует все другие блоки (1-15) к БЛОКУ 16
    
    Использование:
        link_other_blocks_to_block_16({
            "БЛОК_1": block_1_instance,
            "БЛОК_2": telegram_handler,
            # ... и т.д. для всех 15 блоков
        })
    """
    global block_16_instance
    
    if not block_16_instance:
        logger.error("❌ БЛОК 16 не инициализирован!")
        return False
    
    try:
        # Линкуем все блоки к БЛОКУ 16
        for block_name, block_instance in block_handlers.items():
            if block_instance is None:
                logger.warning(f"⚠️  {block_name} не инициализирован, пропускаем")
                continue
            
            # Динамически вызываем метод линкования
            method_name = f"link_{block_name.lower()}"
            if hasattr(block_16_instance, method_name):
                getattr(block_16_instance, method_name)(block_instance)
                logger.info(f"✅ {block_name} линкован к БЛОКУ 16")
        
        logger.info(f"✅ Все доступные блоки линкованы к БЛОКУ 16")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка линкования блоков: {e}")
        return False

def get_block_16():
    """Получить глобальный экземпляр БЛОКА 16"""
    return block_16_instance

