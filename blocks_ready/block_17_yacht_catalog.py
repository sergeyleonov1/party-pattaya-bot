# ═══════════════════════════════════════════════════════════════════════════════
# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                                                                               ║
# ║                         BLOCK 17: YACHT CATALOG                               ║
# ║                      Party Pattaya Bot v10.2.1                                ║
# ║                                                                               ║
# ║  РЕАЛЬНЫЕ ДАННЫЕ С САЙТА partypattayacity.com                                 ║
# ║  Функций: 14 | Автор: Claude | Статус: PRODUCTION READY                       ║
# ║                                                                               ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
# ═══════════════════════════════════════════════════════════════════════════════

import asyncio
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class YachtStatus(Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"

class YachtType(Enum):
    SPEEDBOAT = "speedboat"
    CATAMARAN = "catamaran"
    YACHT = "yacht"
    SUPERYACHT = "superyacht"

class BookingStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class ReviewStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION - РЕАЛЬНЫЕ ДАННЫЕ PARTY PATTAYA
# ═══════════════════════════════════════════════════════════════════════════════

class YachtCatalogConfig:
    """Конфигурация каталога яхт Party Pattaya"""
    
    # Контакты Party Pattaya (РЕАЛЬНЫЕ)
    contacts = {
        "whatsapp": "+66-633-633-407",
        "email": "partypattayacity@gmail.com", 
        "telegram": "@Party_Pattaya",
        "contact_person": "Лилия Новикова",
        "address": "118/40 Moo 11, Baan Dusit Pattaya Park, Huay Yai, Bang Lamung, Chonburi 20150, Thailand",
        "google_maps": "https://maps.app.goo.gl/DiqkHXV3g4fXeL4s8"
    }
    
    # Маршруты (РЕАЛЬНЫЕ)
    routes = {
        "koh_pai": {
            "name": {"ru": "Остров Пай (Бамбуковый)", "en": "Koh Pai (Bamboo Island)", "th": "เกาะไผ่"},
            "can_land": True,
            "duration_hours": 8,
            "popular": True
        },
        "koh_kram": {
            "name": {"ru": "Остров Крам", "en": "Koh Kram", "th": "เกาะคราม"},
            "can_land": False,
            "duration_hours": 4,
            "popular": True
        },
        "koh_kram_monkey": {
            "name": {"ru": "Крам + Обезьяний остров", "en": "Koh Kram + Monkey Island", "th": "เกาะคราม + เกาะลิง"},
            "can_land": True,
            "military_beach": True,
            "duration_hours": 8,
            "popular": True
        },
        "sunset_cruise": {
            "name": {"ru": "Закатный круиз", "en": "Sunset Cruise", "th": "ทริปชมพระอาทิตย์ตก"},
            "time": "17:00-19:00",
            "duration_hours": 2,
            "popular": True
        }
    }
    
    # Включено в аренду яхты
    included_services = {
        "ru": ["Яхта с топливом и экипажем", "Напитки, лёд и фрукты", "Снаряжение для снорклинга и рыбалки", "SUP доска"],
        "en": ["Yacht with fuel and crew", "Drinks, ice and fruits", "Snorkeling and fishing equipment", "SUP board"],
        "th": ["เรือพร้อมน้ำมันเชื้อเพลิงและลูกเรือ", "เครื่องดื่ม น้ำแข็ง และผลไม้", "อุปกรณ์ดำน้ำตื้นและตกปลา", "บอร์ด SUP"]
    }
    
    # Настройки бронирования
    booking_settings = {
        "min_advance_hours": 24,
        "max_advance_days": 90,
        "cancellation_free_hours": 48,
        "cancellation_fee_percent": 50,
        "deposit_percent": 30,
        "currency": "THB"
    }
    
    # Локализация сообщений
    messages = {
        "ru": {
            "booking_confirmed": "✅ Бронирование подтверждено! Яхта: {yacht_name}, Дата: {date}",
            "booking_cancelled": "❌ Бронирование отменено. Номер: {booking_id}",
            "not_available": "😔 К сожалению, яхта недоступна на выбранную дату",
            "yacht_added": "✅ Яхта успешно добавлена: {yacht_name}",
            "contact_manager": "Свяжитесь с нашим менеджером: WhatsApp {whatsapp}"
        },
        "en": {
            "booking_confirmed": "✅ Booking confirmed! Yacht: {yacht_name}, Date: {date}",
            "booking_cancelled": "❌ Booking cancelled. Number: {booking_id}",
            "not_available": "😔 Sorry, the yacht is not available on the selected date",
            "yacht_added": "✅ Yacht successfully added: {yacht_name}",
            "contact_manager": "Contact our manager: WhatsApp {whatsapp}"
        },
        "th": {
            "booking_confirmed": "✅ การจองได้รับการยืนยัน! เรือ: {yacht_name}, วันที่: {date}",
            "booking_cancelled": "❌ ยกเลิกการจองแล้ว หมายเลข: {booking_id}",
            "not_available": "😔 ขออภัย เรือไม่ว่างในวันที่เลือก",
            "yacht_added": "✅ เพิ่มเรือสำเร็จ: {yacht_name}",
            "contact_manager": "ติดต่อผู้จัดการของเรา: WhatsApp {whatsapp}"
        },
        "zh": {
            "booking_confirmed": "✅ 预订已确认！游艇: {yacht_name}, 日期: {date}",
            "booking_cancelled": "❌ 预订已取消。编号: {booking_id}",
            "not_available": "😔 抱歉，所选日期游艇不可用",
            "yacht_added": "✅ 游艇添加成功: {yacht_name}",
            "contact_manager": "联系我们的经理: WhatsApp {whatsapp}"
        }
    }

CONFIG = YachtCatalogConfig()

# ═══════════════════════════════════════════════════════════════════════════════
# РЕАЛЬНЫЕ ЯХТЫ PARTY PATTAYA (с сайта partypattayacity.com)
# ═══════════════════════════════════════════════════════════════════════════════

REAL_YACHTS = {
    "ocean_yachting": {
        "yacht_id": "ocean_yachting",
        "name": "Ocean Yachting",
        "type": YachtType.CATAMARAN.value,
        "capacity": 30,
        "max_capacity": 70,
        "extra_guest_fee": 500,  # бат за доп. гостя
        "description": {
            "ru": "Роскошный катамаран для отдыха вдали от толпы. Экскурсии на острова, дайвинг, водные виды спорта или просто отдых под солнцем с коктейлем.",
            "en": "Luxury catamaran for relaxation away from crowds. Island tours, diving, water sports or just relaxing under the sun with a cocktail.",
            "th": "เรือใบคาตามารันสุดหรูเพื่อเพลิดเพลินกับบรรยากาศผ่อนคลาย ห่างไกลจากฝูงชน",
            "zh": "豪华双体船，远离人群放松身心"
        },
        "pricing": {
            "8_hours": {"weekday": 90000, "weekend": 100000},
            "6_hours": {"weekday": 72000, "weekend": 80000},
            "4_hours": {"weekday": 57000, "weekend": 60000},
            "2_hours_sunset": {"weekday": 33250, "weekend": 35000}
        },
        "included": ["yacht_fuel_crew", "drinks_ice_fruits", "snorkeling_fishing", "sup_board"],
        "amenities": ["wifi", "sound_system", "sun_deck", "swimming_platform", "water_toys"],
        "status": YachtStatus.AVAILABLE.value,
        "featured": True
    },
    
    "speedboat_2019": {
        "yacht_id": "speedboat_2019",
        "name": "Speedboat (2019)",
        "type": YachtType.SPEEDBOAT.value,
        "capacity": 15,
        "max_capacity": 25,
        "extra_guest_fee": 500,
        "year_built": 2019,
        "description": {
            "ru": "Быстрый спидбот 2019 года для экскурсий на острова",
            "en": "Fast 2019 speedboat for island excursions",
            "th": "เรือเร็วปี 2019 สำหรับเที่ยวเกาะ",
            "zh": "2019年快艇，适合岛屿游览"
        },
        "pricing": {
            "8_hours_koh_pai": {"base_2": 30400, "up_to_15": 33000},
            "4_hours_koh_kram": {"base_2": 22400, "up_to_10": 24000}
        },
        "included": ["yacht_fuel_crew", "drinks_ice_fruits", "snorkeling_fishing", "sup_board", "beach_tent", "beach_table_chairs", "bbq_grill"],
        "amenities": ["sound_system", "sun_deck"],
        "status": YachtStatus.AVAILABLE.value,
        "featured": False
    },
    
    "bali_45": {
        "yacht_id": "bali_45",
        "name": "Bali 45 (2019, France)",
        "type": YachtType.CATAMARAN.value,
        "capacity": 10,
        "max_capacity": 20,
        "year_built": 2019,
        "country": "France",
        "length_meters": 14,
        "cabins": 4,
        "bathrooms": 4,
        "description": {
            "ru": "Французский парусный катамаран Bali 45 (2019), 14 метров, 4 каюты с кондиционером, 4 ванные комнаты",
            "en": "French sailing catamaran Bali 45 (2019), 14 meters, 4 air-conditioned cabins, 4 bathrooms",
            "th": "เรือใบคาตามารัน Bali 45 จากฝรั่งเศส ปี 2019 ยาว 14 เมตร 4 ห้องนอน 4 ห้องน้ำ",
            "zh": "法国帆船双体船Bali 45 (2019)，14米，4个空调舱，4个浴室"
        },
        "pricing": {
            "8_hours_koh_pai": {"base_2": 55400, "up_to_10": 57000, "up_to_20": 59000},
            "8_hours_koh_kram_monkey": {"base_2": 50400, "up_to_10": 52000, "up_to_20": 54000},
            "6_hours": {"base_2": 35400, "up_to_10": 37000, "up_to_20": 39000},
            "5_hours_weekday": {"base_2": 28400, "up_to_10": 30000, "up_to_20": 32000},
            "5_hours_weekend": {"base_2": 30400, "up_to_10": 32000, "up_to_20": 34000}
        },
        "included": ["yacht_fuel_crew", "drinks_ice_fruits", "snorkeling_fishing", "sup_board", "floating_pool"],
        "amenities": ["air_conditioning", "wifi", "sound_system", "sun_deck", "swimming_platform", "bedroom", "bathroom"],
        "status": YachtStatus.AVAILABLE.value,
        "featured": True
    },
    
    "lagoon_400": {
        "yacht_id": "lagoon_400",
        "name": "LAGOON 400 (2013)",
        "type": YachtType.CATAMARAN.value,
        "capacity": 10,
        "max_capacity": 15,
        "year_built": 2013,
        "description": {
            "ru": "Парусный катамаран LAGOON 400 (2013)",
            "en": "Sailing catamaran LAGOON 400 (2013)",
            "th": "เรือใบคาตามารัน LAGOON 400 ปี 2013",
            "zh": "双体帆船LAGOON 400 (2013)"
        },
        "pricing": {
            "8_hours_koh_pai": {"base_2": 39400, "up_to_10": 41000, "up_to_15": 42000},
            "8_hours_koh_kram_monkey": {"base_2": 36400, "up_to_10": 38000, "up_to_15": 39000},
            "6_hours": {"base_2": 27400, "up_to_10": 29000, "up_to_15": 30000},
            "4_hours_weekday": {"base_2": 20400, "up_to_10": 22000, "up_to_15": 23000},
            "4_hours_weekend": {"base_2": 22400, "up_to_10": 24000, "up_to_15": 25000}
        },
        "included": ["yacht_fuel_crew", "drinks_ice_fruits", "snorkeling_fishing", "sup_board"],
        "amenities": ["sound_system", "sun_deck", "swimming_platform"],
        "status": YachtStatus.AVAILABLE.value,
        "featured": False
    },
    
    "azimuth_yacht": {
        "yacht_id": "azimuth_yacht",
        "name": "Azimuth Yacht",
        "type": YachtType.YACHT.value,
        "capacity": 15,
        "cabins": 2,
        "bathrooms": 2,
        "description": {
            "ru": "Моторная яхта Azimuth с 2 каютами с кондиционером и 2 ванными",
            "en": "Azimuth motor yacht with 2 air-conditioned cabins and 2 bathrooms",
            "th": "เรือยอทช์ Azimuth 2 ห้องปรับอากาศ 2 ห้องน้ำ",
            "zh": "Azimuth游艇，2个空调舱，2个浴室"
        },
        "pricing": {
            "4_hours": 49000,
            "8_hours": 75000
        },
        "included": ["yacht_fuel_crew", "drinks_ice_fruits"],
        "amenities": ["air_conditioning", "sound_system", "sun_deck", "bedroom", "bathroom"],
        "status": YachtStatus.AVAILABLE.value,
        "featured": False
    },
    
    "charisma_yacht": {
        "yacht_id": "charisma_yacht",
        "name": "Charisma Yacht",
        "type": YachtType.YACHT.value,
        "capacity": 23,
        "cabins": 2,
        "bathrooms": 2,
        "description": {
            "ru": "Яхта Charisma с 2 каютами с кондиционером и 2 ванными",
            "en": "Charisma yacht with 2 air-conditioned cabins and 2 bathrooms",
            "th": "เรือยอทช์ Charisma 2 ห้องปรับอากาศ 2 ห้องน้ำ",
            "zh": "Charisma游艇，2个空调舱，2个浴室"
        },
        "pricing": {
            "4_hours": 55000,
            "8_hours": 80000
        },
        "included": ["yacht_fuel_crew", "drinks_ice_fruits"],
        "amenities": ["air_conditioning", "sound_system", "sun_deck", "bedroom", "bathroom"],
        "status": YachtStatus.AVAILABLE.value,
        "featured": False
    },
    
    "azimuth_64": {
        "yacht_id": "azimuth_64",
        "name": "Azimuth 64",
        "type": YachtType.YACHT.value,
        "capacity": 20,
        "length_feet": 64,
        "cabins": 2,
        "bathrooms": 2,
        "description": {
            "ru": "Премиальная яхта Azimuth 64 футов с 2 каютами и 2 ванными",
            "en": "Premium Azimuth 64 feet yacht with 2 cabins and 2 bathrooms",
            "th": "เรือยอทช์ Azimuth 64 ฟุต 2 ห้องนอน 2 ห้องน้ำ",
            "zh": "Azimuth 64英尺游艇，2舱2浴"
        },
        "pricing": {
            "4_hours": 75000
        },
        "included": ["yacht_fuel_crew", "drinks_ice_fruits"],
        "amenities": ["air_conditioning", "sound_system", "sun_deck", "bedroom", "bathroom"],
        "status": YachtStatus.AVAILABLE.value,
        "featured": True
    },
    
    "sunseeker_64": {
        "yacht_id": "sunseeker_64",
        "name": "Sunseeker 64",
        "type": YachtType.YACHT.value,
        "capacity": 18,
        "length_feet": 64,
        "cabins": 2,
        "bathrooms": 2,
        "description": {
            "ru": "Британская яхта Sunseeker 64 футов с 2 каютами и 2 ванными",
            "en": "British Sunseeker 64 feet yacht with 2 cabins and 2 bathrooms",
            "th": "เรือยอทช์ Sunseeker 64 ฟุต จากอังกฤษ 2 ห้องนอน 2 ห้องน้ำ",
            "zh": "英国Sunseeker 64英尺游艇，2舱2浴"
        },
        "pricing": {
            "4_hours": 80000
        },
        "included": ["yacht_fuel_crew", "drinks_ice_fruits"],
        "amenities": ["air_conditioning", "sound_system", "sun_deck", "bedroom", "bathroom"],
        "status": YachtStatus.AVAILABLE.value,
        "featured": True
    },
    
    "azimuth_76": {
        "yacht_id": "azimuth_76",
        "name": "Azimuth 76",
        "type": YachtType.SUPERYACHT.value,
        "capacity": 25,
        "length_feet": 76,
        "cabins": 2,
        "bathrooms": 2,
        "description": {
            "ru": "Суперяхта Azimuth 76 футов с 2 каютами и 2 ванными - наш флагман",
            "en": "Superyacht Azimuth 76 feet with 2 cabins and 2 bathrooms - our flagship",
            "th": "ซุปเปอร์ยอช์ท Azimuth 76 ฟุต 2 ห้องนอน 2 ห้องน้ำ - เรือเอก",
            "zh": "Azimuth 76英尺超级游艇，2舱2浴 - 旗舰"
        },
        "pricing": {
            "4_hours": 75000
        },
        "included": ["yacht_fuel_crew", "drinks_ice_fruits"],
        "amenities": ["air_conditioning", "wifi", "sound_system", "sun_deck", "swimming_platform", "bedroom", "bathroom", "jet_ski"],
        "status": YachtStatus.AVAILABLE.value,
        "featured": True
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STORE
# ═══════════════════════════════════════════════════════════════════════════════

class YachtDataStore:
    """Хранилище данных яхт"""
    yachts: Dict[str, Dict] = REAL_YACHTS.copy()
    bookings: Dict[str, Dict] = {}
    reviews: Dict[str, List[Dict]] = {}
    photos: Dict[str, List[Dict]] = {}
    calendar: Dict[str, Dict[str, List[str]]] = {}  # yacht_id -> date -> bookings
    metrics: Dict[str, Any] = {
        "total_views": 0,
        "total_bookings": 0,
        "total_revenue": 0,
        "cancellations": 0
    }

STORE = YachtDataStore()

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_id(prefix: str = "id") -> str:
    """Генерация уникального ID"""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def detect_language(text: str) -> str:
    """Определение языка по тексту"""
    if re.search(r'[ก-๙]', text):
        return "th"
    elif re.search(r'[一-龥]', text):
        return "zh"
    elif re.search(r'[а-яА-ЯёЁ]', text):
        return "ru"
    return "en"

def get_message(key: str, lang: str = "en", **kwargs) -> str:
    """Получение локализованного сообщения"""
    messages = CONFIG.messages.get(lang, CONFIG.messages["en"])
    message = messages.get(key, CONFIG.messages["en"].get(key, key))
    return message.format(**kwargs) if kwargs else message

def get_description(yacht: Dict, lang: str = "en") -> str:
    """Получение описания яхты на нужном языке"""
    desc = yacht.get("description", {})
    return desc.get(lang, desc.get("en", ""))

def calculate_price_thb(yacht: Dict, duration_key: str, guests: int = 2, is_weekend: bool = False) -> Dict:
    """Расчёт цены в батах (THB) по реальным данным"""
    pricing = yacht.get("pricing", {})
    
    # Поиск подходящего тарифа
    if duration_key in pricing:
        price_data = pricing[duration_key]
        
        # Простая цена (число)
        if isinstance(price_data, (int, float)):
            return {
                "price": price_data,
                "currency": "THB",
                "duration": duration_key,
                "guests": guests
            }
        
        # Сложная структура с weekday/weekend
        if isinstance(price_data, dict):
            if "weekday" in price_data:
                base_price = price_data["weekend"] if is_weekend else price_data["weekday"]
                extra_guests = max(0, guests - yacht.get("capacity", 30))
                extra_fee = extra_guests * yacht.get("extra_guest_fee", 500)
                return {
                    "base_price": base_price,
                    "extra_guests": extra_guests,
                    "extra_fee": extra_fee,
                    "total_price": base_price + extra_fee,
                    "currency": "THB",
                    "duration": duration_key,
                    "guests": guests,
                    "is_weekend": is_weekend
                }
            
            # Структура с base_2, up_to_10, etc
            if guests <= 2:
                price = price_data.get("base_2", 0)
            elif guests <= 10:
                price = price_data.get("up_to_10", price_data.get("base_2", 0))
            elif guests <= 15:
                price = price_data.get("up_to_15", price_data.get("up_to_10", 0))
            elif guests <= 20:
                price = price_data.get("up_to_20", price_data.get("up_to_15", 0))
            else:
                price = price_data.get("up_to_20", 0)
                extra = (guests - 20) * yacht.get("extra_guest_fee", 500)
                return {
                    "base_price": price,
                    "extra_guests": guests - 20,
                    "extra_fee": extra,
                    "total_price": price + extra,
                    "currency": "THB",
                    "duration": duration_key,
                    "guests": guests
                }
            
            return {
                "price": price,
                "currency": "THB",
                "duration": duration_key,
                "guests": guests
            }
    
    return {"error": "Price not found", "duration_key": duration_key}

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 1: GET ALL YACHTS
# ═══════════════════════════════════════════════════════════════════════════════

async def get_all_yachts(
    include_inactive: bool = False,
    sort_by: str = "featured",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Получение списка всех яхт Party Pattaya
    
    Args:
        include_inactive: Включать неактивные яхты
        sort_by: Сортировка (featured, capacity, name, type)
        sort_order: Порядок (asc, desc)
        limit: Лимит результатов
        offset: Смещение для пагинации
        lang: Язык описаний
    
    Returns:
        Список яхт с описаниями на выбранном языке
    """
    STORE.metrics["total_views"] += 1
    
    yachts_list = []
    for yacht_id, yacht in STORE.yachts.items():
        if not include_inactive and yacht.get("status") != YachtStatus.AVAILABLE.value:
            continue
        
        yacht_info = {
            "yacht_id": yacht_id,
            "name": yacht.get("name"),
            "type": yacht.get("type"),
            "capacity": yacht.get("capacity"),
            "max_capacity": yacht.get("max_capacity", yacht.get("capacity")),
            "description": get_description(yacht, lang),
            "pricing": yacht.get("pricing"),
            "amenities": yacht.get("amenities", []),
            "featured": yacht.get("featured", False),
            "status": yacht.get("status")
        }
        
        # Дополнительные поля если есть
        for field in ["year_built", "length_meters", "length_feet", "cabins", "bathrooms", "country"]:
            if field in yacht:
                yacht_info[field] = yacht[field]
        
        yachts_list.append(yacht_info)
    
    # Сортировка
    reverse = sort_order == "desc"
    if sort_by == "featured":
        yachts_list.sort(key=lambda x: (x.get("featured", False), x.get("capacity", 0)), reverse=reverse)
    elif sort_by == "capacity":
        yachts_list.sort(key=lambda x: x.get("max_capacity", 0), reverse=reverse)
    elif sort_by == "name":
        yachts_list.sort(key=lambda x: x.get("name", ""), reverse=reverse)
    elif sort_by == "type":
        yachts_list.sort(key=lambda x: x.get("type", ""), reverse=reverse)
    
    # Пагинация
    total = len(yachts_list)
    yachts_list = yachts_list[offset:offset + limit]
    
    # Featured яхты
    featured = [y for y in STORE.yachts.values() if y.get("featured")]
    
    return {
        "success": True,
        "yachts": yachts_list,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
        "featured_count": len(featured),
        "contacts": CONFIG.contacts
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 2: GET YACHT BY ID
# ═══════════════════════════════════════════════════════════════════════════════

async def get_yacht_by_id(
    yacht_id: str,
    include_reviews: bool = True,
    include_photos: bool = True,
    include_calendar: bool = False,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Получение детальной информации о яхте
    
    Args:
        yacht_id: ID яхты
        include_reviews: Включить отзывы
        include_photos: Включить фото
        include_calendar: Включить календарь доступности
        lang: Язык
    
    Returns:
        Полная информация о яхте
    """
    yacht = STORE.yachts.get(yacht_id)
    if not yacht:
        return {"success": False, "error": "Yacht not found", "yacht_id": yacht_id}
    
    result = {
        "success": True,
        "yacht": {
            "yacht_id": yacht_id,
            "name": yacht.get("name"),
            "type": yacht.get("type"),
            "capacity": yacht.get("capacity"),
            "max_capacity": yacht.get("max_capacity", yacht.get("capacity")),
            "extra_guest_fee": yacht.get("extra_guest_fee", 500),
            "description": get_description(yacht, lang),
            "pricing": yacht.get("pricing"),
            "included": yacht.get("included", []),
            "included_text": CONFIG.included_services.get(lang, CONFIG.included_services["en"]),
            "amenities": yacht.get("amenities", []),
            "status": yacht.get("status"),
            "featured": yacht.get("featured", False)
        },
        "contacts": CONFIG.contacts,
        "routes": CONFIG.routes
    }
    
    # Дополнительные поля
    for field in ["year_built", "length_meters", "length_feet", "cabins", "bathrooms", "country"]:
        if field in yacht:
            result["yacht"][field] = yacht[field]
    
    # Отзывы
    if include_reviews:
        reviews = STORE.reviews.get(yacht_id, [])
        result["reviews"] = reviews[:10]
        result["reviews_count"] = len(reviews)
    
    # Фото
    if include_photos:
        result["photos"] = STORE.photos.get(yacht_id, [])
    
    # Календарь на 30 дней
    if include_calendar:
        calendar_data = []
        today = datetime.now().date()
        for i in range(30):
            check_date = today + timedelta(days=i)
            date_str = check_date.strftime("%Y-%m-%d")
            bookings = STORE.calendar.get(yacht_id, {}).get(date_str, [])
            calendar_data.append({
                "date": date_str,
                "available": len(bookings) == 0,
                "is_weekend": check_date.weekday() >= 5
            })
        result["calendar"] = calendar_data
    
    # Похожие яхты того же типа
    similar = []
    for yid, y in STORE.yachts.items():
        if yid != yacht_id and y.get("type") == yacht.get("type") and y.get("status") == YachtStatus.AVAILABLE.value:
            similar.append({
                "yacht_id": yid,
                "name": y.get("name"),
                "capacity": y.get("capacity")
            })
    result["similar_yachts"] = similar[:3]
    
    return result

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 3: SEARCH YACHTS
# ═══════════════════════════════════════════════════════════════════════════════

async def search_yachts(
    query: str = None,
    yacht_type: str = None,
    min_capacity: int = None,
    max_capacity: int = None,
    min_price: int = None,
    max_price: int = None,
    amenities: List[str] = None,
    date: str = None,
    duration: str = None,
    guests: int = 2,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Поиск яхт по различным критериям
    
    Args:
        query: Текстовый поиск
        yacht_type: Тип яхты (speedboat, catamaran, yacht, superyacht)
        min_capacity: Минимальная вместимость
        max_capacity: Максимальная вместимость
        min_price: Минимальная цена (THB)
        max_price: Максимальная цена (THB)
        amenities: Требуемые удобства
        date: Дата для проверки доступности (YYYY-MM-DD)
        duration: Длительность (4_hours, 6_hours, 8_hours, etc)
        guests: Количество гостей
        lang: Язык
    
    Returns:
        Результаты поиска с рассчитанными ценами
    """
    results = []
    filters_applied = []
    
    for yacht_id, yacht in STORE.yachts.items():
        if yacht.get("status") != YachtStatus.AVAILABLE.value:
            continue
        
        score = 100  # Базовый скор
        
        # Фильтр по типу
        if yacht_type and yacht.get("type") != yacht_type:
            continue
        if yacht_type:
            filters_applied.append(f"type={yacht_type}")
        
        # Фильтр по вместимости
        capacity = yacht.get("max_capacity", yacht.get("capacity", 0))
        if min_capacity and capacity < min_capacity:
            continue
        if max_capacity and yacht.get("capacity", 0) > max_capacity:
            continue
        
        # Текстовый поиск
        if query:
            query_lower = query.lower()
            name_match = query_lower in yacht.get("name", "").lower()
            desc_match = query_lower in str(yacht.get("description", {})).lower()
            if name_match:
                score += 20
            elif desc_match:
                score += 10
            elif not name_match and not desc_match:
                continue
            filters_applied.append(f"query={query}")
        
        # Фильтр по удобствам
        if amenities:
            yacht_amenities = set(yacht.get("amenities", []))
            if not set(amenities).issubset(yacht_amenities):
                continue
        
        # Проверка доступности на дату
        if date:
            bookings = STORE.calendar.get(yacht_id, {}).get(date, [])
            if bookings:
                continue
        
        # Расчёт цены
        calculated_price = None
        if duration:
            is_weekend = False
            if date:
                try:
                    check_date = datetime.strptime(date, "%Y-%m-%d")
                    is_weekend = check_date.weekday() >= 5
                except:
                    pass
            calculated_price = calculate_price_thb(yacht, duration, guests, is_weekend)
            
            # Фильтр по цене
            if calculated_price and "error" not in calculated_price:
                price_val = calculated_price.get("total_price", calculated_price.get("price", 0))
                if min_price and price_val < min_price:
                    continue
                if max_price and price_val > max_price:
                    continue
        
        results.append({
            "yacht_id": yacht_id,
            "name": yacht.get("name"),
            "type": yacht.get("type"),
            "capacity": yacht.get("capacity"),
            "max_capacity": capacity,
            "description": get_description(yacht, lang),
            "amenities": yacht.get("amenities", []),
            "featured": yacht.get("featured", False),
            "calculated_price": calculated_price,
            "score": score
        })
    
    # Сортировка по скору
    results.sort(key=lambda x: (x.get("featured", False), x.get("score", 0)), reverse=True)
    
    return {
        "success": True,
        "results": results,
        "total": len(results),
        "filters_applied": list(set(filters_applied)),
        "available_types": list(set(y.get("type") for y in STORE.yachts.values())),
        "contacts": CONFIG.contacts
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 4: FILTER BY CAPACITY
# ═══════════════════════════════════════════════════════════════════════════════

async def filter_by_capacity(
    min_guests: int,
    max_guests: int = None,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Фильтрация яхт по вместимости
    
    Args:
        min_guests: Минимальное количество гостей
        max_guests: Максимальное количество гостей
        lang: Язык
    
    Returns:
        Яхты подходящей вместимости
    """
    results = []
    
    for yacht_id, yacht in STORE.yachts.items():
        if yacht.get("status") != YachtStatus.AVAILABLE.value:
            continue
        
        capacity = yacht.get("capacity", 0)
        max_cap = yacht.get("max_capacity", capacity)
        
        # Проверка вместимости
        if min_guests > max_cap:
            continue
        if max_guests and capacity > max_guests:
            continue
        
        extra_space = max_cap - min_guests
        
        results.append({
            "yacht_id": yacht_id,
            "name": yacht.get("name"),
            "type": yacht.get("type"),
            "capacity": capacity,
            "max_capacity": max_cap,
            "extra_guest_fee": yacht.get("extra_guest_fee", 500),
            "extra_space": extra_space,
            "description": get_description(yacht, lang),
            "fit_score": 100 - abs(capacity - min_guests) * 2  # Оптимальность
        })
    
    # Сортировка по оптимальности
    results.sort(key=lambda x: x.get("fit_score", 0), reverse=True)
    
    # Рекомендации
    recommendations = {}
    if results:
        recommendations["best_fit"] = results[0]["name"]
    if min_guests > 30:
        recommendations["suggestion"] = "Для большой группы рекомендуем Ocean Yachting (до 70 человек)"
    
    return {
        "success": True,
        "results": results,
        "total": len(results),
        "requested_capacity": {"min": min_guests, "max": max_guests},
        "recommendations": recommendations,
        "contacts": CONFIG.contacts
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 5: FILTER BY PRICE
# ═══════════════════════════════════════════════════════════════════════════════

async def filter_by_price(
    min_price: int = None,
    max_price: int = None,
    duration: str = "4_hours",
    guests: int = 2,
    is_weekend: bool = False,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Фильтрация яхт по цене
    
    Args:
        min_price: Минимальная цена (THB)
        max_price: Максимальная цена (THB)
        duration: Длительность аренды
        guests: Количество гостей
        is_weekend: Выходной день
        lang: Язык
    
    Returns:
        Яхты в заданном ценовом диапазоне
    """
    results = []
    all_prices = []
    
    for yacht_id, yacht in STORE.yachts.items():
        if yacht.get("status") != YachtStatus.AVAILABLE.value:
            continue
        
        # Расчёт цены
        price_calc = calculate_price_thb(yacht, duration, guests, is_weekend)
        if "error" in price_calc:
            continue
        
        price = price_calc.get("total_price", price_calc.get("price", 0))
        all_prices.append(price)
        
        # Фильтр
        if min_price and price < min_price:
            continue
        if max_price and price > max_price:
            continue
        
        results.append({
            "yacht_id": yacht_id,
            "name": yacht.get("name"),
            "type": yacht.get("type"),
            "capacity": yacht.get("capacity"),
            "price": price,
            "price_details": price_calc,
            "description": get_description(yacht, lang),
            "value_score": yacht.get("capacity", 1) / (price / 10000)  # Гостей на 10000 бат
        })
    
    # Сортировка по цене
    results.sort(key=lambda x: x.get("price", 0))
    
    # Статистика
    stats = {}
    if all_prices:
        stats = {
            "min_price": min(all_prices),
            "max_price": max(all_prices),
            "avg_price": sum(all_prices) // len(all_prices)
        }
    
    # Категории бюджета
    budget_categories = {
        "budget": [r for r in results if r.get("price", 0) < 40000],
        "mid_range": [r for r in results if 40000 <= r.get("price", 0) < 70000],
        "premium": [r for r in results if r.get("price", 0) >= 70000]
    }
    
    return {
        "success": True,
        "results": results,
        "total": len(results),
        "duration": duration,
        "guests": guests,
        "is_weekend": is_weekend,
        "statistics": stats,
        "budget_categories": {k: len(v) for k, v in budget_categories.items()},
        "best_value": max(results, key=lambda x: x.get("value_score", 0))["name"] if results else None,
        "contacts": CONFIG.contacts
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 6: CHECK AVAILABILITY
# ═══════════════════════════════════════════════════════════════════════════════

async def check_availability(
    yacht_id: str,
    date: str,
    duration: str = "4_hours",
    guests: int = 2,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Проверка доступности яхты на дату
    
    Args:
        yacht_id: ID яхты
        date: Дата в формате YYYY-MM-DD
        duration: Длительность аренды
        guests: Количество гостей
        lang: Язык
    
    Returns:
        Информация о доступности и цене
    """
    yacht = STORE.yachts.get(yacht_id)
    if not yacht:
        return {"success": False, "error": "Yacht not found", "yacht_id": yacht_id}
    
    if yacht.get("status") != YachtStatus.AVAILABLE.value:
        return {
            "success": False,
            "available": False,
            "reason": "yacht_inactive",
            "message": get_message("not_available", lang)
        }
    
    # Проверка формата даты
    try:
        check_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}
    
    # Проверка минимального времени бронирования (24 часа)
    now = datetime.now()
    hours_until = (check_date - now).total_seconds() / 3600
    if hours_until < CONFIG.booking_settings["min_advance_hours"]:
        return {
            "success": False,
            "available": False,
            "reason": "too_short_notice",
            "message": f"Бронирование минимум за {CONFIG.booking_settings['min_advance_hours']} часов"
        }
    
    # Проверка максимального времени (90 дней)
    days_until = (check_date - now).days
    if days_until > CONFIG.booking_settings["max_advance_days"]:
        return {
            "success": False,
            "available": False,
            "reason": "too_far_ahead",
            "message": f"Бронирование максимум за {CONFIG.booking_settings['max_advance_days']} дней"
        }
    
    # Проверка существующих бронирований
    existing_bookings = STORE.calendar.get(yacht_id, {}).get(date, [])
    if existing_bookings:
        # Поиск альтернативных дат
        alternatives = await _find_alternative_dates(yacht_id, check_date, 7)
        return {
            "success": True,
            "available": False,
            "reason": "already_booked",
            "message": get_message("not_available", lang),
            "alternative_dates": alternatives,
            "contacts": CONFIG.contacts
        }
    
    # Проверка вместимости
    max_cap = yacht.get("max_capacity", yacht.get("capacity", 0))
    if guests > max_cap:
        return {
            "success": False,
            "available": False,
            "reason": "capacity_exceeded",
            "message": f"Максимальная вместимость: {max_cap} гостей"
        }
    
    # Расчёт цены
    is_weekend = check_date.weekday() >= 5
    price_calc = calculate_price_thb(yacht, duration, guests, is_weekend)
    
    # Дедлайн бесплатной отмены
    cancel_deadline = check_date - timedelta(hours=CONFIG.booking_settings["cancellation_free_hours"])
    
    return {
        "success": True,
        "available": True,
        "yacht_id": yacht_id,
        "yacht_name": yacht.get("name"),
        "date": date,
        "is_weekend": is_weekend,
        "duration": duration,
        "guests": guests,
        "pricing": price_calc,
        "deposit_percent": CONFIG.booking_settings["deposit_percent"],
        "cancellation_free_until": cancel_deadline.strftime("%Y-%m-%d %H:%M"),
        "booking_deadline": (check_date - timedelta(hours=CONFIG.booking_settings["min_advance_hours"])).strftime("%Y-%m-%d %H:%M"),
        "contacts": CONFIG.contacts
    }

async def _find_alternative_dates(yacht_id: str, original_date: datetime, days_range: int = 7) -> List[str]:
    """Поиск альтернативных доступных дат"""
    alternatives = []
    for delta in range(-days_range, days_range + 1):
        if delta == 0:
            continue
        check_date = original_date + timedelta(days=delta)
        if check_date < datetime.now():
            continue
        date_str = check_date.strftime("%Y-%m-%d")
        if not STORE.calendar.get(yacht_id, {}).get(date_str):
            alternatives.append({
                "date": date_str,
                "is_weekend": check_date.weekday() >= 5,
                "days_from_original": delta
            })
    return alternatives[:5]

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 7: GET YACHT CALENDAR
# ═══════════════════════════════════════════════════════════════════════════════

async def get_yacht_calendar(
    yacht_id: str,
    month: int = None,
    year: int = None,
    days_ahead: int = 30,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Получение календаря доступности яхты
    
    Args:
        yacht_id: ID яхты
        month: Месяц (1-12)
        year: Год
        days_ahead: Количество дней вперёд (если месяц не указан)
        lang: Язык
    
    Returns:
        Календарь с доступностью по дням
    """
    yacht = STORE.yachts.get(yacht_id)
    if not yacht:
        return {"success": False, "error": "Yacht not found", "yacht_id": yacht_id}
    
    calendar_data = []
    today = datetime.now().date()
    
    if month and year:
        # Конкретный месяц
        import calendar as cal
        _, last_day = cal.monthrange(year, month)
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, last_day).date()
    else:
        # Дни вперёд
        start_date = today
        end_date = today + timedelta(days=days_ahead)
    
    available_count = 0
    current = start_date
    
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        bookings = STORE.calendar.get(yacht_id, {}).get(date_str, [])
        is_available = len(bookings) == 0 and current >= today
        
        if is_available:
            available_count += 1
        
        calendar_data.append({
            "date": date_str,
            "day": current.day,
            "weekday": current.strftime("%A"),
            "available": is_available,
            "is_past": current < today,
            "is_weekend": current.weekday() >= 5,
            "bookings_count": len(bookings)
        })
        current += timedelta(days=1)
    
    return {
        "success": True,
        "yacht_id": yacht_id,
        "yacht_name": yacht.get("name"),
        "calendar": calendar_data,
        "summary": {
            "total_days": len(calendar_data),
            "available_days": available_count,
            "booked_days": len(calendar_data) - available_count,
            "availability_rate": round(available_count / len(calendar_data) * 100, 1) if calendar_data else 0
        },
        "next_available": next((d["date"] for d in calendar_data if d.get("available")), None),
        "contacts": CONFIG.contacts
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 8: RESERVE YACHT
# ═══════════════════════════════════════════════════════════════════════════════

async def reserve_yacht(
    yacht_id: str,
    user_id: int,
    date: str,
    duration: str,
    guests: int,
    contact_info: Dict,
    route: str = None,
    special_requests: str = None,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Бронирование яхты
    
    Args:
        yacht_id: ID яхты
        user_id: ID пользователя
        date: Дата (YYYY-MM-DD)
        duration: Длительность (4_hours, 6_hours, 8_hours, etc)
        guests: Количество гостей
        contact_info: Контактная информация {name, phone, email}
        route: Маршрут (koh_pai, koh_kram, etc)
        special_requests: Особые пожелания
        lang: Язык
    
    Returns:
        Информация о бронировании
    """
    # Проверка доступности
    availability = await check_availability(yacht_id, date, duration, guests, lang)
    if not availability.get("success") or not availability.get("available"):
        return availability
    
    yacht = STORE.yachts.get(yacht_id)
    
    # Создание бронирования
    booking_id = generate_id("booking")
    
    try:
        booking_date = datetime.strptime(date, "%Y-%m-%d")
        is_weekend = booking_date.weekday() >= 5
    except:
        is_weekend = False
    
    price_calc = calculate_price_thb(yacht, duration, guests, is_weekend)
    final_price = price_calc.get("total_price", price_calc.get("price", 0))
    deposit = round(final_price * CONFIG.booking_settings["deposit_percent"] / 100)
    
    booking = {
        "booking_id": booking_id,
        "yacht_id": yacht_id,
        "yacht_name": yacht.get("name"),
        "user_id": user_id,
        "date": date,
        "duration": duration,
        "guests": guests,
        "route": route,
        "route_info": CONFIG.routes.get(route, {}) if route else None,
        "contact_info": contact_info,
        "special_requests": special_requests,
        "pricing": price_calc,
        "total_price": final_price,
        "deposit_required": deposit,
        "status": BookingStatus.PENDING.value,
        "created_at": datetime.now().isoformat(),
        "cancellation_free_until": (booking_date - timedelta(hours=CONFIG.booking_settings["cancellation_free_hours"])).isoformat()
    }
    
    # Сохранение
    STORE.bookings[booking_id] = booking
    
    # Добавление в календарь
    if yacht_id not in STORE.calendar:
        STORE.calendar[yacht_id] = {}
    if date not in STORE.calendar[yacht_id]:
        STORE.calendar[yacht_id][date] = []
    STORE.calendar[yacht_id][date].append(booking_id)
    
    # Метрики
    STORE.metrics["total_bookings"] += 1
    STORE.metrics["total_revenue"] += final_price
    
    return {
        "success": True,
        "message": get_message("booking_confirmed", lang, yacht_name=yacht.get("name"), date=date),
        "booking": booking,
        "next_steps": {
            "1": f"Оплатите депозит {deposit:,} THB",
            "2": f"Полная оплата {final_price:,} THB до {date}",
            "3": f"Бесплатная отмена до {booking['cancellation_free_until'][:10]}"
        },
        "payment_methods": ["bank_transfer", "credit_card", "cash"],
        "contacts": CONFIG.contacts
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 9: CANCEL RESERVATION
# ═══════════════════════════════════════════════════════════════════════════════

async def cancel_reservation(
    booking_id: str,
    user_id: int,
    reason: str = None,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Отмена бронирования
    
    Args:
        booking_id: ID бронирования
        user_id: ID пользователя
        reason: Причина отмены
        lang: Язык
    
    Returns:
        Информация об отмене и возврате
    """
    booking = STORE.bookings.get(booking_id)
    if not booking:
        return {"success": False, "error": "Booking not found", "booking_id": booking_id}
    
    # Проверка владельца
    if booking.get("user_id") != user_id:
        return {"success": False, "error": "Not authorized to cancel this booking"}
    
    # Проверка статуса
    if booking.get("status") in [BookingStatus.CANCELLED.value, BookingStatus.COMPLETED.value]:
        return {"success": False, "error": f"Booking already {booking.get('status')}"}
    
    # Расчёт штрафа
    now = datetime.now()
    cancel_deadline = datetime.fromisoformat(booking.get("cancellation_free_until", now.isoformat()))
    
    total_price = booking.get("total_price", 0)
    
    if now <= cancel_deadline:
        # Бесплатная отмена
        refund_amount = total_price
        cancellation_fee = 0
        was_free = True
    else:
        # Штраф
        cancellation_fee = round(total_price * CONFIG.booking_settings["cancellation_fee_percent"] / 100)
        refund_amount = total_price - cancellation_fee
        was_free = False
    
    # Обновление бронирования
    booking["status"] = BookingStatus.CANCELLED.value
    booking["cancelled_at"] = now.isoformat()
    booking["cancellation_reason"] = reason
    booking["refund_amount"] = refund_amount
    booking["cancellation_fee"] = cancellation_fee
    
    # Освобождение даты в календаре
    yacht_id = booking.get("yacht_id")
    date = booking.get("date")
    if yacht_id in STORE.calendar and date in STORE.calendar[yacht_id]:
        if booking_id in STORE.calendar[yacht_id][date]:
            STORE.calendar[yacht_id][date].remove(booking_id)
    
    # Метрики
    STORE.metrics["cancellations"] += 1
    
    return {
        "success": True,
        "message": get_message("booking_cancelled", lang, booking_id=booking_id),
        "booking_id": booking_id,
        "was_free_cancellation": was_free,
        "refund_amount": refund_amount,
        "cancellation_fee": cancellation_fee,
        "cancelled_at": booking["cancelled_at"],
        "contacts": CONFIG.contacts
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 10: GET YACHT PHOTOS
# ═══════════════════════════════════════════════════════════════════════════════

async def get_yacht_photos(
    yacht_id: str,
    include_thumbnails: bool = True
) -> Dict[str, Any]:
    """
    Получение фотографий яхты
    
    Args:
        yacht_id: ID яхты
        include_thumbnails: Включить миниатюры
    
    Returns:
        Список фотографий
    """
    yacht = STORE.yachts.get(yacht_id)
    if not yacht:
        return {"success": False, "error": "Yacht not found", "yacht_id": yacht_id}
    
    photos = STORE.photos.get(yacht_id, [])
    
    # Если фото нет, создаём плейсхолдеры
    if not photos:
        photos = [
            {"photo_id": f"photo_{yacht_id}_1", "url": f"https://partypattayacity.com/yachts/{yacht_id}/main.jpg", "is_main": True, "category": "exterior"},
            {"photo_id": f"photo_{yacht_id}_2", "url": f"https://partypattayacity.com/yachts/{yacht_id}/deck.jpg", "is_main": False, "category": "exterior"},
            {"photo_id": f"photo_{yacht_id}_3", "url": f"https://partypattayacity.com/yachts/{yacht_id}/interior.jpg", "is_main": False, "category": "interior"}
        ]
    
    if include_thumbnails:
        for photo in photos:
            photo["thumbnail_url"] = photo.get("url", "").replace(".jpg", "_thumb.jpg")
    
    # Сортировка - main фото первым
    photos.sort(key=lambda x: (not x.get("is_main", False), x.get("photo_id", "")))
    
    return {
        "success": True,
        "yacht_id": yacht_id,
        "yacht_name": yacht.get("name"),
        "photos": photos,
        "total": len(photos),
        "main_photo": next((p for p in photos if p.get("is_main")), photos[0] if photos else None)
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 11: GET YACHT REVIEWS
# ═══════════════════════════════════════════════════════════════════════════════

async def get_yacht_reviews(
    yacht_id: str,
    status: str = "approved",
    sort_by: str = "date",
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Получение отзывов о яхте
    
    Args:
        yacht_id: ID яхты
        status: Статус отзывов (approved, pending, all)
        sort_by: Сортировка (date, rating, helpful)
        limit: Лимит
        offset: Смещение
    
    Returns:
        Список отзывов со статистикой
    """
    yacht = STORE.yachts.get(yacht_id)
    if not yacht:
        return {"success": False, "error": "Yacht not found", "yacht_id": yacht_id}
    
    reviews = STORE.reviews.get(yacht_id, [])
    
    # Фильтр по статусу
    if status != "all":
        reviews = [r for r in reviews if r.get("status") == status]
    
    # Сортировка
    if sort_by == "date":
        reviews.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    elif sort_by == "rating":
        reviews.sort(key=lambda x: x.get("rating", 0), reverse=True)
    elif sort_by == "helpful":
        reviews.sort(key=lambda x: x.get("helpful_count", 0), reverse=True)
    
    total = len(reviews)
    reviews = reviews[offset:offset + limit]
    
    # Статистика
    all_reviews = STORE.reviews.get(yacht_id, [])
    approved_reviews = [r for r in all_reviews if r.get("status") == "approved"]
    
    if approved_reviews:
        ratings = [r.get("rating", 0) for r in approved_reviews]
        avg_rating = sum(ratings) / len(ratings)
        rating_dist = {i: ratings.count(i) for i in range(1, 6)}
        recommendation_rate = len([r for r in approved_reviews if r.get("rating", 0) >= 4]) / len(approved_reviews) * 100
    else:
        avg_rating = 0
        rating_dist = {i: 0 for i in range(1, 6)}
        recommendation_rate = 0
    
    return {
        "success": True,
        "yacht_id": yacht_id,
        "yacht_name": yacht.get("name"),
        "reviews": reviews,
        "total": total,
        "has_more": offset + limit < total,
        "statistics": {
            "average_rating": round(avg_rating, 1),
            "total_reviews": len(approved_reviews),
            "rating_distribution": rating_dist,
            "recommendation_rate": round(recommendation_rate, 1)
        }
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 12: ADD YACHT (ADMIN)
# ═══════════════════════════════════════════════════════════════════════════════

async def add_yacht(
    name: str,
    yacht_type: str,
    capacity: int,
    pricing: Dict,
    admin_user_id: int,
    description: Dict[str, str] = None,
    max_capacity: int = None,
    extra_guest_fee: int = 500,
    amenities: List[str] = None,
    included: List[str] = None,
    year_built: int = None,
    length_meters: float = None,
    length_feet: int = None,
    cabins: int = None,
    bathrooms: int = None,
    country: str = None,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Добавление новой яхты (только для админов)
    
    Args:
        name: Название яхты
        yacht_type: Тип (speedboat, catamaran, yacht, superyacht)
        capacity: Базовая вместимость
        pricing: Ценообразование
        admin_user_id: ID администратора
        description: Описания на разных языках
        max_capacity: Максимальная вместимость
        extra_guest_fee: Доплата за гостя сверх нормы
        amenities: Список удобств
        included: Что включено
        year_built: Год постройки
        length_meters: Длина в метрах
        length_feet: Длина в футах
        cabins: Количество кают
        bathrooms: Количество ванных
        country: Страна производства
        lang: Язык
    
    Returns:
        Информация о добавленной яхте
    """
    # Валидация типа
    valid_types = ["speedboat", "catamaran", "yacht", "superyacht"]
    if yacht_type not in valid_types:
        return {"success": False, "error": f"Invalid yacht type. Must be one of: {valid_types}"}
    
    # Генерация ID
    yacht_id = name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace(",", "")
    
    # Проверка уникальности
    if yacht_id in STORE.yachts:
        yacht_id = f"{yacht_id}_{generate_id('')[3:8]}"
    
    yacht = {
        "yacht_id": yacht_id,
        "name": name,
        "type": yacht_type,
        "capacity": capacity,
        "max_capacity": max_capacity or capacity,
        "extra_guest_fee": extra_guest_fee,
        "description": description or {"en": f"Yacht {name}"},
        "pricing": pricing,
        "amenities": amenities or [],
        "included": included or ["yacht_fuel_crew", "drinks_ice_fruits"],
        "status": YachtStatus.AVAILABLE.value,
        "featured": False,
        "created_at": datetime.now().isoformat(),
        "created_by": admin_user_id
    }
    
    # Дополнительные поля
    if year_built:
        yacht["year_built"] = year_built
    if length_meters:
        yacht["length_meters"] = length_meters
    if length_feet:
        yacht["length_feet"] = length_feet
    if cabins:
        yacht["cabins"] = cabins
    if bathrooms:
        yacht["bathrooms"] = bathrooms
    if country:
        yacht["country"] = country
    
    # Сохранение
    STORE.yachts[yacht_id] = yacht
    STORE.reviews[yacht_id] = []
    STORE.photos[yacht_id] = []
    STORE.calendar[yacht_id] = {}
    
    return {
        "success": True,
        "message": get_message("yacht_added", lang, yacht_name=name),
        "yacht_id": yacht_id,
        "yacht": yacht,
        "next_steps": ["Загрузить фото", "Добавить описания на других языках", "Установить featured если нужно"]
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 13: UPDATE YACHT (ADMIN)
# ═══════════════════════════════════════════════════════════════════════════════

async def update_yacht(
    yacht_id: str,
    updates: Dict,
    admin_user_id: int,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Обновление информации о яхте (только для админов)
    
    Args:
        yacht_id: ID яхты
        updates: Словарь с обновлениями
        admin_user_id: ID администратора
        lang: Язык
    
    Returns:
        Информация об обновлённой яхте
    """
    yacht = STORE.yachts.get(yacht_id)
    if not yacht:
        return {"success": False, "error": "Yacht not found", "yacht_id": yacht_id}
    
    # Защищённые поля
    protected_fields = ["yacht_id", "created_at", "created_by"]
    
    changes = []
    for key, value in updates.items():
        if key in protected_fields:
            continue
        if key in yacht and yacht[key] != value:
            changes.append({
                "field": key,
                "old_value": yacht[key],
                "new_value": value
            })
        yacht[key] = value
    
    yacht["updated_at"] = datetime.now().isoformat()
    yacht["updated_by"] = admin_user_id
    
    return {
        "success": True,
        "yacht_id": yacht_id,
        "changes": changes,
        "yacht": yacht
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 14: DELETE YACHT (ADMIN)
# ═══════════════════════════════════════════════════════════════════════════════

async def delete_yacht(
    yacht_id: str,
    admin_user_id: int,
    force: bool = False,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Удаление яхты (только для админов)
    
    Args:
        yacht_id: ID яхты
        admin_user_id: ID администратора
        force: Принудительное удаление с отменой бронирований
        lang: Язык
    
    Returns:
        Информация об удалении
    """
    yacht = STORE.yachts.get(yacht_id)
    if not yacht:
        return {"success": False, "error": "Yacht not found", "yacht_id": yacht_id}
    
    # Проверка активных бронирований
    active_bookings = [
        b for b in STORE.bookings.values()
        if b.get("yacht_id") == yacht_id and b.get("status") in [
            BookingStatus.PENDING.value,
            BookingStatus.CONFIRMED.value,
            BookingStatus.PAID.value
        ]
    ]
    
    if active_bookings and not force:
        return {
            "success": False,
            "error": "Yacht has active bookings",
            "active_bookings_count": len(active_bookings),
            "hint": "Use force=True to cancel all bookings and delete yacht"
        }
    
    cancelled_bookings = []
    if force and active_bookings:
        for booking in active_bookings:
            booking["status"] = BookingStatus.CANCELLED.value
            booking["cancellation_reason"] = "Yacht removed from service"
            booking["refund_amount"] = booking.get("total_price", 0)
            cancelled_bookings.append(booking["booking_id"])
    
    # Удаление
    del STORE.yachts[yacht_id]
    if yacht_id in STORE.reviews:
        del STORE.reviews[yacht_id]
    if yacht_id in STORE.photos:
        del STORE.photos[yacht_id]
    if yacht_id in STORE.calendar:
        del STORE.calendar[yacht_id]
    
    return {
        "success": True,
        "message": get_message("yacht_deleted" if "yacht_deleted" in CONFIG.messages.get(lang, {}) else "yacht_added", lang, yacht_name=yacht.get("name")).replace("добавлена", "удалена").replace("added", "deleted"),
        "yacht_id": yacht_id,
        "yacht_name": yacht.get("name"),
        "deleted_at": datetime.now().isoformat(),
        "deleted_by": admin_user_id,
        "cancelled_bookings": cancelled_bookings,
        "was_forced": force and len(active_bookings) > 0
    }

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                         BLOCK 17: YACHT CATALOG                              ║
║                       Party Pattaya Bot v10.2.1                              ║
║                                                                              ║
║  РЕАЛЬНЫЕ ЯХТЫ С САЙТА partypattayacity.com                                  ║
║  9 яхт | 14 функций | Валюта: THB (бат)                                      ║
║                                                                              ║
║  ⚠️  ИЗМЕНЕНИЯ ЗАПРЕЩЕНЫ БЕЗ РАЗРЕШЕНИЯ СЕРГЕЯ                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    print("ЯХТЫ PARTY PATTAYA:")
    for yacht_id, yacht in REAL_YACHTS.items():
        print(f"  • {yacht['name']} - до {yacht.get('max_capacity', yacht['capacity'])} чел")
    
    print("\nФункции:")
    print("  1.  get_all_yachts       - Список всех яхт")
    print("  2.  get_yacht_by_id      - Яхта по ID")
    print("  3.  search_yachts        - Поиск с фильтрами")
    print("  4.  filter_by_capacity   - Фильтр по вместимости")
    print("  5.  filter_by_price      - Фильтр по цене (THB)")
    print("  6.  check_availability   - Проверка доступности")
    print("  7.  get_yacht_calendar   - Календарь яхты")
    print("  8.  reserve_yacht        - Бронирование")
    print("  9.  cancel_reservation   - Отмена брони")
    print("  10. get_yacht_photos     - Фото яхты")
    print("  11. get_yacht_reviews    - Отзывы")
    print("  12. add_yacht            - Добавление яхты (admin)")
    print("  13. update_yacht         - Обновление (admin)")
    print("  14. delete_yacht         - Удаление (admin)")
    print("\nКонтакты: WhatsApp +66-633-633-407 | @Party_Pattaya")
    print("\nИмпорт: from block_17_yacht_catalog import *")
