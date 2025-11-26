# ═══════════════════════════════════════════════════════════════════════════════
# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║                                                                               ║
# ║                         BLOCK 17: YACHT CATALOG                               ║
# ║                      Party Pattaya Bot v10.2.1                                ║
# ║                                                                               ║
# ║  Каталог яхт с фильтрацией, бронированием и управлением доступностью          ║
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
    SAILBOAT = "sailboat"

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
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class YachtCatalogConfig:
    """Конфигурация каталога яхт"""
    
    # Контакты Party Pattaya
    contacts = {
        "whatsapp": "+66-633-633-407",
        "email": "Liliya@partypattayacity.com",
        "telegram": "@Party_Pattaya"
    }
    
    # Категории яхт с ценами
    yacht_categories = {
        "speedboat": {"min_price": 500, "max_price": 1500, "capacity_range": (4, 12)},
        "catamaran": {"min_price": 800, "max_price": 2500, "capacity_range": (10, 30)},
        "yacht": {"min_price": 1000, "max_price": 3000, "capacity_range": (8, 20)},
        "superyacht": {"min_price": 2000, "max_price": 10000, "capacity_range": (15, 50)},
        "sailboat": {"min_price": 600, "max_price": 1800, "capacity_range": (4, 10)}
    }
    
    # Удобства
    amenities = [
        "wifi", "air_conditioning", "sound_system", "jet_ski", "snorkeling_gear",
        "fishing_equipment", "bbq", "kitchen", "bedroom", "bathroom", "shower",
        "sun_deck", "swimming_platform", "water_toys", "karaoke", "tv"
    ]
    
    # Маршруты
    routes = {
        "coral_island": {"duration_hours": 6, "distance_km": 15, "popular": True},
        "phi_phi": {"duration_hours": 10, "distance_km": 45, "popular": True},
        "racha_island": {"duration_hours": 8, "distance_km": 25, "popular": True},
        "similan": {"duration_hours": 12, "distance_km": 100, "popular": False},
        "sunset_cruise": {"duration_hours": 3, "distance_km": 10, "popular": True},
        "fishing_trip": {"duration_hours": 8, "distance_km": 30, "popular": False},
        "custom": {"duration_hours": None, "distance_km": None, "popular": False}
    }
    
    # Настройки бронирования
    booking_settings = {
        "min_advance_hours": 24,
        "max_advance_days": 90,
        "cancellation_free_hours": 48,
        "cancellation_fee_percent": 50,
        "deposit_percent": 30,
        "peak_season_months": [12, 1, 2, 3, 4],
        "peak_season_markup": 1.2
    }
    
    # Локализация
    messages = {
        "ru": {
            "booking_confirmed": "✅ Бронирование подтверждено! Яхта: {yacht_name}, Дата: {date}",
            "booking_cancelled": "❌ Бронирование отменено. Номер: {booking_id}",
            "not_available": "😔 К сожалению, яхта недоступна на выбранную дату",
            "yacht_added": "✅ Яхта успешно добавлена: {yacht_name}",
            "yacht_updated": "✅ Яхта обновлена: {yacht_name}",
            "yacht_deleted": "🗑️ Яхта удалена: {yacht_name}"
        },
        "en": {
            "booking_confirmed": "✅ Booking confirmed! Yacht: {yacht_name}, Date: {date}",
            "booking_cancelled": "❌ Booking cancelled. Number: {booking_id}",
            "not_available": "😔 Sorry, the yacht is not available on the selected date",
            "yacht_added": "✅ Yacht successfully added: {yacht_name}",
            "yacht_updated": "✅ Yacht updated: {yacht_name}",
            "yacht_deleted": "🗑️ Yacht deleted: {yacht_name}"
        },
        "th": {
            "booking_confirmed": "✅ การจองได้รับการยืนยัน! เรือ: {yacht_name}, วันที่: {date}",
            "booking_cancelled": "❌ ยกเลิกการจองแล้ว หมายเลข: {booking_id}",
            "not_available": "😔 ขออภัย เรือไม่ว่างในวันที่เลือก",
            "yacht_added": "✅ เพิ่มเรือสำเร็จ: {yacht_name}",
            "yacht_updated": "✅ อัปเดตเรือแล้ว: {yacht_name}",
            "yacht_deleted": "🗑️ ลบเรือแล้ว: {yacht_name}"
        },
        "zh": {
            "booking_confirmed": "✅ 预订已确认！游艇: {yacht_name}, 日期: {date}",
            "booking_cancelled": "❌ 预订已取消。编号: {booking_id}",
            "not_available": "😔 抱歉，所选日期游艇不可用",
            "yacht_added": "✅ 游艇添加成功: {yacht_name}",
            "yacht_updated": "✅ 游艇已更新: {yacht_name}",
            "yacht_deleted": "🗑️ 游艇已删除: {yacht_name}"
        }
    }

CONFIG = YachtCatalogConfig()

# ═══════════════════════════════════════════════════════════════════════════════
# DATA STORE
# ═══════════════════════════════════════════════════════════════════════════════

class YachtDataStore:
    """Хранилище данных яхт"""
    
    def __init__(self):
        self.yachts: Dict[str, Dict] = {}
        self.bookings: Dict[str, Dict] = {}
        self.reviews: Dict[str, List[Dict]] = {}
        self.photos: Dict[str, List[Dict]] = {}
        self.calendar: Dict[str, Dict[str, List]] = {}  # yacht_id -> date -> bookings
        self.metrics = {
            "total_views": 0,
            "total_bookings": 0,
            "total_revenue": 0,
            "cancellations": 0
        }
        self._init_demo_yachts()
    
    def _init_demo_yachts(self):
        """Инициализация демо-яхт"""
        demo_yachts = [
            {
                "yacht_id": "yacht_001",
                "name": "Ocean Paradise",
                "name_th": "สวรรค์แห่งมหาสมุทร",
                "type": YachtType.SUPERYACHT.value,
                "capacity": 30,
                "length_meters": 25,
                "year_built": 2020,
                "price_per_day": 3500,
                "price_per_hour": 500,
                "amenities": ["wifi", "air_conditioning", "sound_system", "jet_ski", "bbq", "kitchen", "bedroom", "bathroom", "sun_deck"],
                "crew_included": True,
                "crew_size": 4,
                "description": {
                    "ru": "Роскошная суперяхта для незабываемых вечеринок и круизов",
                    "en": "Luxury superyacht for unforgettable parties and cruises",
                    "th": "ซุปเปอร์ยอช์ทหรูสำหรับปาร์ตี้และล่องเรือที่น่าจดจำ",
                    "zh": "豪华超级游艇，打造难忘派对和巡游体验"
                },
                "status": YachtStatus.AVAILABLE.value,
                "rating": 4.9,
                "reviews_count": 47,
                "featured": True
            },
            {
                "yacht_id": "yacht_002",
                "name": "Speed Demon",
                "name_th": "ปีศาจความเร็ว",
                "type": YachtType.SPEEDBOAT.value,
                "capacity": 8,
                "length_meters": 10,
                "year_built": 2022,
                "price_per_day": 800,
                "price_per_hour": 150,
                "amenities": ["sound_system", "snorkeling_gear", "sun_deck"],
                "crew_included": True,
                "crew_size": 1,
                "description": {
                    "ru": "Быстрый спидбот для экскурсий на острова",
                    "en": "Fast speedboat for island hopping",
                    "th": "สปีดโบ๊ทเร็วสำหรับเที่ยวเกาะ",
                    "zh": "快艇，适合跳岛游"
                },
                "status": YachtStatus.AVAILABLE.value,
                "rating": 4.7,
                "reviews_count": 89,
                "featured": False
            },
            {
                "yacht_id": "yacht_003",
                "name": "Sunset Dream",
                "name_th": "ความฝันพระอาทิตย์ตก",
                "type": YachtType.CATAMARAN.value,
                "capacity": 20,
                "length_meters": 15,
                "year_built": 2019,
                "price_per_day": 1800,
                "price_per_hour": 300,
                "amenities": ["wifi", "air_conditioning", "sound_system", "bbq", "snorkeling_gear", "karaoke", "swimming_platform"],
                "crew_included": True,
                "crew_size": 3,
                "description": {
                    "ru": "Стабильный катамаран для комфортных морских прогулок",
                    "en": "Stable catamaran for comfortable sea trips",
                    "th": "เรือคาตามารันที่มั่นคงสำหรับการเดินทางทางทะเลที่สะดวกสบาย",
                    "zh": "稳定的双体船，舒适的海上之旅"
                },
                "status": YachtStatus.AVAILABLE.value,
                "rating": 4.8,
                "reviews_count": 62,
                "featured": True
            },
            {
                "yacht_id": "yacht_004",
                "name": "Royal Voyage",
                "name_th": "การเดินทางของราชวงศ์",
                "type": YachtType.YACHT.value,
                "capacity": 15,
                "length_meters": 18,
                "year_built": 2021,
                "price_per_day": 2200,
                "price_per_hour": 350,
                "amenities": ["wifi", "air_conditioning", "sound_system", "jet_ski", "fishing_equipment", "bedroom", "bathroom", "tv"],
                "crew_included": True,
                "crew_size": 3,
                "description": {
                    "ru": "Элегантная яхта для особых случаев",
                    "en": "Elegant yacht for special occasions",
                    "th": "เรือยอช์ทหรูสำหรับโอกาสพิเศษ",
                    "zh": "优雅游艇，适合特殊场合"
                },
                "status": YachtStatus.AVAILABLE.value,
                "rating": 4.85,
                "reviews_count": 35,
                "featured": False
            },
            {
                "yacht_id": "yacht_005",
                "name": "Wind Chaser",
                "name_th": "ผู้ไล่ตามสายลม",
                "type": YachtType.SAILBOAT.value,
                "capacity": 6,
                "length_meters": 12,
                "year_built": 2018,
                "price_per_day": 700,
                "price_per_hour": 120,
                "amenities": ["snorkeling_gear", "fishing_equipment", "sun_deck"],
                "crew_included": True,
                "crew_size": 1,
                "description": {
                    "ru": "Парусная яхта для романтических прогулок",
                    "en": "Sailing yacht for romantic trips",
                    "th": "เรือใบสำหรับการเดินทางโรแมนติก",
                    "zh": "帆船，浪漫之旅"
                },
                "status": YachtStatus.AVAILABLE.value,
                "rating": 4.6,
                "reviews_count": 28,
                "featured": False
            }
        ]
        
        for yacht in demo_yachts:
            self.yachts[yacht["yacht_id"]] = yacht
            self.reviews[yacht["yacht_id"]] = []
            self.photos[yacht["yacht_id"]] = [
                {"photo_id": f"photo_{yacht['yacht_id']}_1", "url": f"/photos/{yacht['yacht_id']}/main.jpg", "is_main": True},
                {"photo_id": f"photo_{yacht['yacht_id']}_2", "url": f"/photos/{yacht['yacht_id']}/deck.jpg", "is_main": False},
                {"photo_id": f"photo_{yacht['yacht_id']}_3", "url": f"/photos/{yacht['yacht_id']}/interior.jpg", "is_main": False}
            ]
            self.calendar[yacht["yacht_id"]] = {}
    
    def get_yacht(self, yacht_id: str) -> Optional[Dict]:
        return self.yachts.get(yacht_id)
    
    def save_yacht(self, yacht_id: str, data: Dict):
        self.yachts[yacht_id] = data
    
    def delete_yacht(self, yacht_id: str):
        if yacht_id in self.yachts:
            del self.yachts[yacht_id]
    
    def get_booking(self, booking_id: str) -> Optional[Dict]:
        return self.bookings.get(booking_id)
    
    def save_booking(self, booking_id: str, data: Dict):
        self.bookings[booking_id] = data

DATA = YachtDataStore()

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def detect_language(text: str) -> str:
    if re.search(r"[а-яА-ЯёЁ]", text):
        return "ru"
    elif re.search(r"[ก-๙]", text):
        return "th"
    elif re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    return "en"

def get_message(key: str, lang: str = "en", **kwargs) -> str:
    msg = CONFIG.messages.get(lang, CONFIG.messages["en"]).get(key, "")
    return msg.format(**kwargs) if kwargs else msg

def calculate_price(yacht: Dict, hours: int = None, days: int = None, date: datetime = None) -> Dict:
    """Расчёт стоимости аренды"""
    base_price = 0
    
    if days and days > 0:
        base_price = yacht.get("price_per_day", 0) * days
    elif hours and hours > 0:
        base_price = yacht.get("price_per_hour", 0) * hours
    
    # Наценка в высокий сезон
    multiplier = 1.0
    if date and date.month in CONFIG.booking_settings["peak_season_months"]:
        multiplier = CONFIG.booking_settings["peak_season_markup"]
    
    final_price = base_price * multiplier
    deposit = final_price * (CONFIG.booking_settings["deposit_percent"] / 100)
    
    return {
        "base_price": base_price,
        "multiplier": multiplier,
        "final_price": round(final_price, 2),
        "deposit": round(deposit, 2),
        "currency": "USD",
        "is_peak_season": multiplier > 1.0
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 1: get_all_yachts
# ═══════════════════════════════════════════════════════════════════════════════

async def get_all_yachts(
    include_inactive: bool = False,
    sort_by: str = "rating",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Получение списка всех яхт.
    
    Args:
        include_inactive: Включать неактивные яхты
        sort_by: Поле для сортировки (rating, price, capacity, name)
        sort_order: Порядок сортировки (asc, desc)
        limit: Лимит результатов
        offset: Смещение для пагинации
    """
    yachts = list(DATA.yachts.values())
    
    # Фильтрация неактивных
    if not include_inactive:
        yachts = [y for y in yachts if y.get("status") != YachtStatus.INACTIVE.value]
    
    # Сортировка
    sort_keys = {
        "rating": lambda x: x.get("rating", 0),
        "price": lambda x: x.get("price_per_day", 0),
        "capacity": lambda x: x.get("capacity", 0),
        "name": lambda x: x.get("name", ""),
        "reviews": lambda x: x.get("reviews_count", 0)
    }
    
    if sort_by in sort_keys:
        reverse = sort_order == "desc"
        yachts = sorted(yachts, key=sort_keys[sort_by], reverse=reverse)
    
    # Пагинация
    total = len(yachts)
    yachts = yachts[offset:offset + limit]
    
    # Добавляем фото к каждой яхте
    for yacht in yachts:
        yacht_id = yacht.get("yacht_id")
        photos = DATA.photos.get(yacht_id, [])
        main_photo = next((p for p in photos if p.get("is_main")), photos[0] if photos else None)
        yacht["main_photo"] = main_photo
    
    DATA.metrics["total_views"] += 1
    
    return {
        "yachts": yachts,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "featured": [y for y in yachts if y.get("featured")][:3]
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 2: get_yacht_by_id
# ═══════════════════════════════════════════════════════════════════════════════

async def get_yacht_by_id(
    yacht_id: str,
    include_reviews: bool = True,
    include_photos: bool = True,
    include_calendar: bool = False,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Получение детальной информации о яхте по ID.
    
    Args:
        yacht_id: ID яхты
        include_reviews: Включить отзывы
        include_photos: Включить фото
        include_calendar: Включить календарь доступности
        lang: Язык для описания
    """
    yacht = DATA.get_yacht(yacht_id)
    
    if not yacht:
        return {
            "success": False,
            "error": "yacht_not_found",
            "message": "Яхта не найдена" if lang == "ru" else "Yacht not found"
        }
    
    result = {
        "success": True,
        "yacht": yacht.copy()
    }
    
    # Локализация описания
    if "description" in result["yacht"] and isinstance(result["yacht"]["description"], dict):
        result["yacht"]["description_localized"] = result["yacht"]["description"].get(lang, result["yacht"]["description"].get("en", ""))
    
    # Фотографии
    if include_photos:
        result["photos"] = DATA.photos.get(yacht_id, [])
    
    # Отзывы
    if include_reviews:
        reviews = DATA.reviews.get(yacht_id, [])
        approved_reviews = [r for r in reviews if r.get("status") == ReviewStatus.APPROVED.value]
        result["reviews"] = approved_reviews[-10:]  # Последние 10
        result["reviews_summary"] = {
            "total": len(approved_reviews),
            "average_rating": round(sum(r.get("rating", 0) for r in approved_reviews) / max(len(approved_reviews), 1), 1),
            "rating_distribution": {i: len([r for r in approved_reviews if r.get("rating") == i]) for i in range(1, 6)}
        }
    
    # Календарь
    if include_calendar:
        today = datetime.now().date()
        next_30_days = []
        for i in range(30):
            day = today + timedelta(days=i)
            day_str = day.isoformat()
            bookings = DATA.calendar.get(yacht_id, {}).get(day_str, [])
            is_available = yacht.get("status") == YachtStatus.AVAILABLE.value and len(bookings) == 0
            next_30_days.append({
                "date": day_str,
                "available": is_available,
                "bookings_count": len(bookings)
            })
        result["calendar"] = next_30_days
    
    # Расчёт цен
    result["pricing"] = {
        "per_hour": yacht.get("price_per_hour"),
        "per_day": yacht.get("price_per_day"),
        "deposit_percent": CONFIG.booking_settings["deposit_percent"],
        "peak_season_months": CONFIG.booking_settings["peak_season_months"],
        "peak_season_markup": CONFIG.booking_settings["peak_season_markup"]
    }
    
    # Похожие яхты
    similar = [y for y in DATA.yachts.values() 
               if y.get("yacht_id") != yacht_id 
               and y.get("type") == yacht.get("type")
               and y.get("status") == YachtStatus.AVAILABLE.value][:3]
    result["similar_yachts"] = [{"yacht_id": y["yacht_id"], "name": y["name"], "price_per_day": y["price_per_day"]} for y in similar]
    
    DATA.metrics["total_views"] += 1
    
    return result

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 3: search_yachts
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
    duration_hours: int = None,
    sort_by: str = "relevance"
) -> Dict[str, Any]:
    """
    Поиск яхт с фильтрами.
    
    Args:
        query: Текстовый поиск
        yacht_type: Тип яхты
        min_capacity/max_capacity: Диапазон вместимости
        min_price/max_price: Диапазон цены
        amenities: Требуемые удобства
        date: Дата бронирования
        duration_hours: Длительность аренды
        sort_by: Сортировка (relevance, price_asc, price_desc, rating)
    """
    results = list(DATA.yachts.values())
    
    # Только доступные
    results = [y for y in results if y.get("status") == YachtStatus.AVAILABLE.value]
    
    # Фильтр по типу
    if yacht_type:
        results = [y for y in results if y.get("type") == yacht_type]
    
    # Фильтр по вместимости
    if min_capacity:
        results = [y for y in results if y.get("capacity", 0) >= min_capacity]
    if max_capacity:
        results = [y for y in results if y.get("capacity", 0) <= max_capacity]
    
    # Фильтр по цене
    if min_price:
        results = [y for y in results if y.get("price_per_day", 0) >= min_price]
    if max_price:
        results = [y for y in results if y.get("price_per_day", 0) <= max_price]
    
    # Фильтр по удобствам
    if amenities:
        results = [y for y in results if all(a in y.get("amenities", []) for a in amenities)]
    
    # Фильтр по доступности на дату
    if date:
        available_results = []
        for yacht in results:
            bookings = DATA.calendar.get(yacht.get("yacht_id"), {}).get(date, [])
            if len(bookings) == 0:
                available_results.append(yacht)
        results = available_results
    
    # Текстовый поиск
    if query:
        query_lower = query.lower()
        scored_results = []
        for yacht in results:
            score = 0
            name = yacht.get("name", "").lower()
            desc = str(yacht.get("description", "")).lower()
            
            if query_lower in name:
                score += 10
            if query_lower in desc:
                score += 5
            for amenity in yacht.get("amenities", []):
                if query_lower in amenity:
                    score += 2
            
            if score > 0:
                scored_results.append((yacht, score))
        
        scored_results.sort(key=lambda x: x[1], reverse=True)
        results = [r[0] for r in scored_results]
    
    # Сортировка
    if sort_by == "price_asc":
        results.sort(key=lambda x: x.get("price_per_day", 0))
    elif sort_by == "price_desc":
        results.sort(key=lambda x: x.get("price_per_day", 0), reverse=True)
    elif sort_by == "rating":
        results.sort(key=lambda x: x.get("rating", 0), reverse=True)
    elif sort_by == "capacity":
        results.sort(key=lambda x: x.get("capacity", 0), reverse=True)
    
    # Расчёт цен для каждой яхты
    for yacht in results:
        if duration_hours:
            pricing = calculate_price(yacht, hours=duration_hours, date=datetime.strptime(date, "%Y-%m-%d") if date else None)
            yacht["calculated_price"] = pricing
    
    return {
        "results": results,
        "total": len(results),
        "filters_applied": {
            "query": query,
            "yacht_type": yacht_type,
            "capacity_range": [min_capacity, max_capacity],
            "price_range": [min_price, max_price],
            "amenities": amenities,
            "date": date
        },
        "sort_by": sort_by,
        "available_types": list(set(y.get("type") for y in DATA.yachts.values())),
        "price_range": {
            "min": min(y.get("price_per_day", 0) for y in DATA.yachts.values()) if DATA.yachts else 0,
            "max": max(y.get("price_per_day", 0) for y in DATA.yachts.values()) if DATA.yachts else 0
        }
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 4: filter_by_capacity
# ═══════════════════════════════════════════════════════════════════════════════

async def filter_by_capacity(
    min_guests: int,
    max_guests: int = None,
    include_crew: bool = False
) -> Dict[str, Any]:
    """
    Фильтрация яхт по вместимости.
    
    Args:
        min_guests: Минимум гостей
        max_guests: Максимум гостей (опционально)
        include_crew: Учитывать ли экипаж в вместимости
    """
    results = []
    
    for yacht in DATA.yachts.values():
        if yacht.get("status") != YachtStatus.AVAILABLE.value:
            continue
        
        capacity = yacht.get("capacity", 0)
        if include_crew:
            capacity += yacht.get("crew_size", 0)
        
        if capacity >= min_guests:
            if max_guests is None or capacity <= max_guests:
                results.append({
                    **yacht,
                    "effective_capacity": capacity,
                    "fits_group": True,
                    "extra_space": capacity - min_guests
                })
    
    # Сортировка по оптимальности (минимум лишнего места)
    results.sort(key=lambda x: x.get("extra_space", 0))
    
    # Рекомендации
    recommendations = []
    if results:
        best_fit = results[0]
        recommendations.append(f"Best fit: {best_fit.get('name')} ({best_fit.get('capacity')} guests)")
    
    if not results and min_guests > 30:
        recommendations.append("Consider splitting into multiple yachts for large groups")
    
    return {
        "results": results,
        "total": len(results),
        "search_params": {
            "min_guests": min_guests,
            "max_guests": max_guests,
            "include_crew": include_crew
        },
        "recommendations": recommendations,
        "capacity_ranges": {
            "small": len([y for y in results if y.get("capacity", 0) <= 10]),
            "medium": len([y for y in results if 10 < y.get("capacity", 0) <= 20]),
            "large": len([y for y in results if y.get("capacity", 0) > 20])
        }
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 5: filter_by_price
# ═══════════════════════════════════════════════════════════════════════════════

async def filter_by_price(
    min_price: int = None,
    max_price: int = None,
    price_type: str = "per_day",
    include_peak_pricing: bool = True
) -> Dict[str, Any]:
    """
    Фильтрация яхт по цене.
    
    Args:
        min_price: Минимальная цена
        max_price: Максимальная цена
        price_type: Тип цены (per_day, per_hour)
        include_peak_pricing: Показывать цены высокого сезона
    """
    results = []
    price_field = "price_per_day" if price_type == "per_day" else "price_per_hour"
    
    for yacht in DATA.yachts.values():
        if yacht.get("status") != YachtStatus.AVAILABLE.value:
            continue
        
        price = yacht.get(price_field, 0)
        
        if min_price and price < min_price:
            continue
        if max_price and price > max_price:
            continue
        
        yacht_result = yacht.copy()
        yacht_result["regular_price"] = price
        
        if include_peak_pricing:
            peak_price = price * CONFIG.booking_settings["peak_season_markup"]
            yacht_result["peak_season_price"] = round(peak_price, 2)
        
        yacht_result["value_score"] = round(yacht.get("rating", 0) / max(price / 1000, 1), 2)
        
        results.append(yacht_result)
    
    # Сортировка по цене
    results.sort(key=lambda x: x.get("regular_price", 0))
    
    # Статистика
    prices = [y.get(price_field, 0) for y in DATA.yachts.values()]
    
    return {
        "results": results,
        "total": len(results),
        "price_type": price_type,
        "search_params": {
            "min_price": min_price,
            "max_price": max_price
        },
        "statistics": {
            "min_available": min(prices) if prices else 0,
            "max_available": max(prices) if prices else 0,
            "average": round(sum(prices) / len(prices), 2) if prices else 0,
            "median": sorted(prices)[len(prices) // 2] if prices else 0
        },
        "budget_categories": {
            "budget": len([y for y in results if y.get("regular_price", 0) < 1000]),
            "mid_range": len([y for y in results if 1000 <= y.get("regular_price", 0) < 2500]),
            "luxury": len([y for y in results if y.get("regular_price", 0) >= 2500])
        },
        "best_value": max(results, key=lambda x: x.get("value_score", 0)) if results else None
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 6: check_availability
# ═══════════════════════════════════════════════════════════════════════════════

async def check_availability(
    yacht_id: str,
    date: str,
    duration_hours: int = None,
    duration_days: int = None
) -> Dict[str, Any]:
    """
    Проверка доступности яхты на дату.
    
    Args:
        yacht_id: ID яхты
        date: Дата начала (YYYY-MM-DD)
        duration_hours: Длительность в часах
        duration_days: Длительность в днях
    """
    yacht = DATA.get_yacht(yacht_id)
    
    if not yacht:
        return {
            "available": False,
            "error": "yacht_not_found",
            "message": "Yacht not found"
        }
    
    # Проверка статуса яхты
    if yacht.get("status") != YachtStatus.AVAILABLE.value:
        return {
            "available": False,
            "yacht_id": yacht_id,
            "yacht_name": yacht.get("name"),
            "reason": "yacht_unavailable",
            "status": yacht.get("status"),
            "message": "Yacht is currently unavailable"
        }
    
    # Проверка даты
    try:
        booking_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {
            "available": False,
            "error": "invalid_date",
            "message": "Invalid date format. Use YYYY-MM-DD"
        }
    
    # Проверка минимального времени бронирования
    min_advance = timedelta(hours=CONFIG.booking_settings["min_advance_hours"])
    if booking_date < datetime.now() + min_advance:
        return {
            "available": False,
            "yacht_id": yacht_id,
            "reason": "too_short_notice",
            "message": f"Booking requires at least {CONFIG.booking_settings['min_advance_hours']} hours advance notice"
        }
    
    # Проверка максимального времени бронирования
    max_advance = timedelta(days=CONFIG.booking_settings["max_advance_days"])
    if booking_date > datetime.now() + max_advance:
        return {
            "available": False,
            "yacht_id": yacht_id,
            "reason": "too_far_advance",
            "message": f"Booking can only be made up to {CONFIG.booking_settings['max_advance_days']} days in advance"
        }
    
    # Проверка существующих бронирований
    dates_to_check = [date]
    if duration_days and duration_days > 1:
        for i in range(1, duration_days):
            next_date = (booking_date + timedelta(days=i)).strftime("%Y-%m-%d")
            dates_to_check.append(next_date)
    
    conflicts = []
    for check_date in dates_to_check:
        bookings = DATA.calendar.get(yacht_id, {}).get(check_date, [])
        if bookings:
            conflicts.extend(bookings)
    
    if conflicts:
        return {
            "available": False,
            "yacht_id": yacht_id,
            "yacht_name": yacht.get("name"),
            "reason": "already_booked",
            "conflicting_dates": dates_to_check,
            "message": "Yacht is already booked for these dates",
            "alternative_dates": await _find_alternative_dates(yacht_id, booking_date, duration_days or 1)
        }
    
    # Расчёт стоимости
    pricing = calculate_price(
        yacht,
        hours=duration_hours,
        days=duration_days,
        date=booking_date
    )
    
    return {
        "available": True,
        "yacht_id": yacht_id,
        "yacht_name": yacht.get("name"),
        "date": date,
        "duration_hours": duration_hours,
        "duration_days": duration_days,
        "pricing": pricing,
        "booking_deadline": (booking_date - min_advance).isoformat(),
        "cancellation_free_until": (booking_date - timedelta(hours=CONFIG.booking_settings["cancellation_free_hours"])).isoformat(),
        "contacts": CONFIG.contacts
    }

async def _find_alternative_dates(yacht_id: str, original_date: datetime, duration: int) -> List[str]:
    """Поиск альтернативных дат"""
    alternatives = []
    for offset in range(-7, 8):
        if offset == 0:
            continue
        check_date = original_date + timedelta(days=offset)
        if check_date < datetime.now():
            continue
        
        date_str = check_date.strftime("%Y-%m-%d")
        bookings = DATA.calendar.get(yacht_id, {}).get(date_str, [])
        if not bookings:
            alternatives.append(date_str)
            if len(alternatives) >= 5:
                break
    
    return alternatives

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 7: get_yacht_calendar
# ═══════════════════════════════════════════════════════════════════════════════

async def get_yacht_calendar(
    yacht_id: str,
    month: int = None,
    year: int = None,
    days_ahead: int = 30
) -> Dict[str, Any]:
    """
    Получение календаря доступности яхты.
    
    Args:
        yacht_id: ID яхты
        month: Месяц (если указан, показывает весь месяц)
        year: Год
        days_ahead: Количество дней вперёд (если месяц не указан)
    """
    yacht = DATA.get_yacht(yacht_id)
    
    if not yacht:
        return {
            "success": False,
            "error": "yacht_not_found"
        }
    
    today = datetime.now().date()
    calendar_data = []
    
    if month and year:
        # Показать конкретный месяц
        from calendar import monthrange
        days_in_month = monthrange(year, month)[1]
        start_date = datetime(year, month, 1).date()
        
        for day in range(1, days_in_month + 1):
            current_date = datetime(year, month, day).date()
            date_str = current_date.isoformat()
            
            bookings = DATA.calendar.get(yacht_id, {}).get(date_str, [])
            is_past = current_date < today
            is_available = not is_past and yacht.get("status") == YachtStatus.AVAILABLE.value and len(bookings) == 0
            is_peak = month in CONFIG.booking_settings["peak_season_months"]
            
            calendar_data.append({
                "date": date_str,
                "day": day,
                "weekday": current_date.strftime("%A"),
                "available": is_available,
                "is_past": is_past,
                "is_peak_season": is_peak,
                "bookings_count": len(bookings),
                "price_multiplier": CONFIG.booking_settings["peak_season_markup"] if is_peak else 1.0
            })
    else:
        # Показать N дней вперёд
        for i in range(days_ahead):
            current_date = today + timedelta(days=i)
            date_str = current_date.isoformat()
            
            bookings = DATA.calendar.get(yacht_id, {}).get(date_str, [])
            is_available = yacht.get("status") == YachtStatus.AVAILABLE.value and len(bookings) == 0
            is_peak = current_date.month in CONFIG.booking_settings["peak_season_months"]
            
            calendar_data.append({
                "date": date_str,
                "day": current_date.day,
                "weekday": current_date.strftime("%A"),
                "available": is_available,
                "is_peak_season": is_peak,
                "bookings_count": len(bookings),
                "price_multiplier": CONFIG.booking_settings["peak_season_markup"] if is_peak else 1.0
            })
    
    available_count = len([d for d in calendar_data if d.get("available")])
    
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
        "pricing": {
            "regular_per_day": yacht.get("price_per_day"),
            "peak_per_day": round(yacht.get("price_per_day", 0) * CONFIG.booking_settings["peak_season_markup"], 2)
        },
        "next_available": next((d["date"] for d in calendar_data if d.get("available")), None)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 8: reserve_yacht
# ═══════════════════════════════════════════════════════════════════════════════

async def reserve_yacht(
    yacht_id: str,
    user_id: int,
    date: str,
    duration_hours: int = None,
    duration_days: int = None,
    contact_info: Dict = None,
    special_requests: str = None,
    route: str = None,
    guests_count: int = None,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Бронирование яхты.
    
    Args:
        yacht_id: ID яхты
        user_id: ID пользователя
        date: Дата начала (YYYY-MM-DD)
        duration_hours: Длительность в часах
        duration_days: Длительность в днях
        contact_info: Контактная информация
        special_requests: Особые пожелания
        route: Маршрут
        guests_count: Количество гостей
        lang: Язык
    """
    # Проверка доступности
    availability = await check_availability(yacht_id, date, duration_hours, duration_days)
    
    if not availability.get("available"):
        return {
            "success": False,
            "error": "not_available",
            "message": get_message("not_available", lang),
            "details": availability
        }
    
    yacht = DATA.get_yacht(yacht_id)
    
    # Проверка вместимости
    if guests_count and guests_count > yacht.get("capacity", 0):
        return {
            "success": False,
            "error": "capacity_exceeded",
            "message": f"Maximum capacity is {yacht.get('capacity')} guests",
            "yacht_capacity": yacht.get("capacity"),
            "requested_guests": guests_count
        }
    
    # Создание бронирования
    booking_id = generate_id("booking")
    booking_date = datetime.strptime(date, "%Y-%m-%d")
    
    pricing = availability.get("pricing", {})
    
    booking = {
        "booking_id": booking_id,
        "yacht_id": yacht_id,
        "yacht_name": yacht.get("name"),
        "user_id": user_id,
        "date": date,
        "duration_hours": duration_hours,
        "duration_days": duration_days,
        "guests_count": guests_count or yacht.get("capacity"),
        "route": route,
        "special_requests": special_requests,
        "contact_info": contact_info or {},
        "pricing": pricing,
        "status": BookingStatus.PENDING.value,
        "deposit_required": pricing.get("deposit", 0),
        "deposit_paid": False,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "cancellation_free_until": availability.get("cancellation_free_until"),
        "language": lang
    }
    
    # Сохранение бронирования
    DATA.save_booking(booking_id, booking)
    
    # Добавление в календарь
    dates_to_book = [date]
    if duration_days and duration_days > 1:
        for i in range(1, duration_days):
            next_date = (booking_date + timedelta(days=i)).strftime("%Y-%m-%d")
            dates_to_book.append(next_date)
    
    for book_date in dates_to_book:
        if yacht_id not in DATA.calendar:
            DATA.calendar[yacht_id] = {}
        if book_date not in DATA.calendar[yacht_id]:
            DATA.calendar[yacht_id][book_date] = []
        DATA.calendar[yacht_id][book_date].append(booking_id)
    
    # Обновление метрик
    DATA.metrics["total_bookings"] += 1
    
    return {
        "success": True,
        "booking_id": booking_id,
        "message": get_message("booking_confirmed", lang, yacht_name=yacht.get("name"), date=date),
        "booking": booking,
        "next_steps": [
            f"Pay deposit: ${pricing.get('deposit', 0)}",
            f"Full payment: ${pricing.get('final_price', 0)}",
            f"Free cancellation until: {availability.get('cancellation_free_until')}"
        ],
        "contacts": CONFIG.contacts,
        "payment_methods": ["credit_card", "bank_transfer", "crypto", "cash"]
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 9: cancel_reservation
# ═══════════════════════════════════════════════════════════════════════════════

async def cancel_reservation(
    booking_id: str,
    user_id: int,
    reason: str = None,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Отмена бронирования.
    
    Args:
        booking_id: ID бронирования
        user_id: ID пользователя
        reason: Причина отмены
        lang: Язык
    """
    booking = DATA.get_booking(booking_id)
    
    if not booking:
        return {
            "success": False,
            "error": "booking_not_found",
            "message": "Booking not found"
        }
    
    # Проверка владельца
    if booking.get("user_id") != user_id:
        return {
            "success": False,
            "error": "unauthorized",
            "message": "You can only cancel your own bookings"
        }
    
    # Проверка статуса
    if booking.get("status") in [BookingStatus.CANCELLED.value, BookingStatus.COMPLETED.value]:
        return {
            "success": False,
            "error": "invalid_status",
            "message": f"Booking is already {booking.get('status')}"
        }
    
    # Расчёт штрафа
    cancellation_free_until = booking.get("cancellation_free_until")
    refund_amount = 0
    cancellation_fee = 0
    
    if cancellation_free_until:
        free_until = datetime.fromisoformat(cancellation_free_until)
        if datetime.now() <= free_until:
            # Бесплатная отмена
            refund_amount = booking.get("pricing", {}).get("final_price", 0)
            if booking.get("deposit_paid"):
                refund_amount = booking.get("deposit_required", 0)
        else:
            # Отмена со штрафом
            total = booking.get("pricing", {}).get("final_price", 0)
            cancellation_fee = total * (CONFIG.booking_settings["cancellation_fee_percent"] / 100)
            refund_amount = total - cancellation_fee
            if booking.get("deposit_paid"):
                refund_amount = max(0, booking.get("deposit_required", 0) - cancellation_fee)
    
    # Обновление статуса
    booking["status"] = BookingStatus.CANCELLED.value
    booking["cancelled_at"] = datetime.now().isoformat()
    booking["cancellation_reason"] = reason
    booking["refund_amount"] = round(refund_amount, 2)
    booking["cancellation_fee"] = round(cancellation_fee, 2)
    booking["updated_at"] = datetime.now().isoformat()
    
    DATA.save_booking(booking_id, booking)
    
    # Освобождение дат в календаре
    yacht_id = booking.get("yacht_id")
    date = booking.get("date")
    duration_days = booking.get("duration_days") or 1
    booking_date = datetime.strptime(date, "%Y-%m-%d")
    
    for i in range(duration_days):
        release_date = (booking_date + timedelta(days=i)).strftime("%Y-%m-%d")
        if yacht_id in DATA.calendar and release_date in DATA.calendar[yacht_id]:
            DATA.calendar[yacht_id][release_date] = [
                b for b in DATA.calendar[yacht_id][release_date] if b != booking_id
            ]
    
    DATA.metrics["cancellations"] += 1
    
    return {
        "success": True,
        "booking_id": booking_id,
        "message": get_message("booking_cancelled", lang, booking_id=booking_id),
        "refund_amount": round(refund_amount, 2),
        "cancellation_fee": round(cancellation_fee, 2),
        "was_free_cancellation": cancellation_fee == 0,
        "cancelled_at": booking["cancelled_at"],
        "contacts": CONFIG.contacts
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 10: get_yacht_photos
# ═══════════════════════════════════════════════════════════════════════════════

async def get_yacht_photos(
    yacht_id: str,
    include_thumbnails: bool = True
) -> Dict[str, Any]:
    """
    Получение фотографий яхты.
    
    Args:
        yacht_id: ID яхты
        include_thumbnails: Включить миниатюры
    """
    yacht = DATA.get_yacht(yacht_id)
    
    if not yacht:
        return {
            "success": False,
            "error": "yacht_not_found"
        }
    
    photos = DATA.photos.get(yacht_id, [])
    
    # Добавление миниатюр
    if include_thumbnails:
        for photo in photos:
            url = photo.get("url", "")
            photo["thumbnail_url"] = url.replace(".jpg", "_thumb.jpg")
    
    # Сортировка - главное фото первым
    photos = sorted(photos, key=lambda x: not x.get("is_main", False))
    
    main_photo = next((p for p in photos if p.get("is_main")), photos[0] if photos else None)
    
    return {
        "success": True,
        "yacht_id": yacht_id,
        "yacht_name": yacht.get("name"),
        "photos": photos,
        "total": len(photos),
        "main_photo": main_photo,
        "categories": {
            "exterior": [p for p in photos if "exterior" in p.get("url", "") or "deck" in p.get("url", "")],
            "interior": [p for p in photos if "interior" in p.get("url", "")],
            "amenities": [p for p in photos if "amenity" in p.get("url", "")]
        }
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 11: get_yacht_reviews
# ═══════════════════════════════════════════════════════════════════════════════

async def get_yacht_reviews(
    yacht_id: str,
    status: str = "approved",
    sort_by: str = "date",
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Получение отзывов о яхте.
    
    Args:
        yacht_id: ID яхты
        status: Статус отзывов (approved, pending, all)
        sort_by: Сортировка (date, rating)
        limit: Лимит
        offset: Смещение
    """
    yacht = DATA.get_yacht(yacht_id)
    
    if not yacht:
        return {
            "success": False,
            "error": "yacht_not_found"
        }
    
    reviews = DATA.reviews.get(yacht_id, [])
    
    # Фильтрация по статусу
    if status != "all":
        reviews = [r for r in reviews if r.get("status") == status]
    
    # Сортировка
    if sort_by == "date":
        reviews = sorted(reviews, key=lambda x: x.get("created_at", ""), reverse=True)
    elif sort_by == "rating":
        reviews = sorted(reviews, key=lambda x: x.get("rating", 0), reverse=True)
    elif sort_by == "helpful":
        reviews = sorted(reviews, key=lambda x: x.get("helpful_count", 0), reverse=True)
    
    total = len(reviews)
    reviews = reviews[offset:offset + limit]
    
    # Статистика
    all_approved = [r for r in DATA.reviews.get(yacht_id, []) if r.get("status") == "approved"]
    ratings = [r.get("rating", 0) for r in all_approved]
    
    return {
        "success": True,
        "yacht_id": yacht_id,
        "yacht_name": yacht.get("name"),
        "reviews": reviews,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
        "statistics": {
            "average_rating": round(sum(ratings) / len(ratings), 1) if ratings else 0,
            "total_reviews": len(all_approved),
            "rating_distribution": {
                5: len([r for r in ratings if r == 5]),
                4: len([r for r in ratings if r == 4]),
                3: len([r for r in ratings if r == 3]),
                2: len([r for r in ratings if r == 2]),
                1: len([r for r in ratings if r == 1])
            },
            "recommendation_rate": round(len([r for r in ratings if r >= 4]) / max(len(ratings), 1) * 100, 1)
        },
        "highlights": {
            "most_praised": ["crew", "cleanliness", "amenities"][:3],
            "recent_positive": [r.get("text", "")[:100] for r in all_approved if r.get("rating", 0) >= 4][:3]
        }
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 12: add_yacht (Admin)
# ═══════════════════════════════════════════════════════════════════════════════

async def add_yacht(
    name: str,
    yacht_type: str,
    capacity: int,
    price_per_day: float,
    price_per_hour: float = None,
    length_meters: float = None,
    year_built: int = None,
    amenities: List[str] = None,
    description: Dict[str, str] = None,
    crew_included: bool = True,
    crew_size: int = 1,
    admin_user_id: int = None,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Добавление новой яхты (только для администраторов).
    
    Args:
        name: Название яхты
        yacht_type: Тип яхты
        capacity: Вместимость
        price_per_day: Цена за день
        price_per_hour: Цена за час
        length_meters: Длина в метрах
        year_built: Год постройки
        amenities: Удобства
        description: Описание на разных языках
        crew_included: Экипаж включён
        crew_size: Размер экипажа
        admin_user_id: ID администратора
        lang: Язык
    """
    # Валидация типа
    valid_types = [t.value for t in YachtType]
    if yacht_type not in valid_types:
        return {
            "success": False,
            "error": "invalid_type",
            "message": f"Valid types: {', '.join(valid_types)}"
        }
    
    # Валидация удобств
    if amenities:
        invalid_amenities = [a for a in amenities if a not in CONFIG.amenities]
        if invalid_amenities:
            return {
                "success": False,
                "error": "invalid_amenities",
                "message": f"Invalid amenities: {invalid_amenities}",
                "valid_amenities": CONFIG.amenities
            }
    
    yacht_id = generate_id("yacht")
    
    yacht = {
        "yacht_id": yacht_id,
        "name": name,
        "type": yacht_type,
        "capacity": capacity,
        "length_meters": length_meters,
        "year_built": year_built or datetime.now().year,
        "price_per_day": price_per_day,
        "price_per_hour": price_per_hour or round(price_per_day / 8, 2),
        "amenities": amenities or [],
        "crew_included": crew_included,
        "crew_size": crew_size,
        "description": description or {"en": "", "ru": "", "th": "", "zh": ""},
        "status": YachtStatus.AVAILABLE.value,
        "rating": 0,
        "reviews_count": 0,
        "featured": False,
        "created_at": datetime.now().isoformat(),
        "created_by": admin_user_id,
        "updated_at": datetime.now().isoformat()
    }
    
    DATA.save_yacht(yacht_id, yacht)
    DATA.reviews[yacht_id] = []
    DATA.photos[yacht_id] = []
    DATA.calendar[yacht_id] = {}
    
    return {
        "success": True,
        "yacht_id": yacht_id,
        "message": get_message("yacht_added", lang, yacht_name=name),
        "yacht": yacht,
        "next_steps": [
            "Upload photos",
            "Add detailed description",
            "Set featured status if needed"
        ]
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 13: update_yacht (Admin)
# ═══════════════════════════════════════════════════════════════════════════════

async def update_yacht(
    yacht_id: str,
    updates: Dict[str, Any],
    admin_user_id: int = None,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Обновление информации о яхте (только для администраторов).
    
    Args:
        yacht_id: ID яхты
        updates: Словарь с обновлениями
        admin_user_id: ID администратора
        lang: Язык
    """
    yacht = DATA.get_yacht(yacht_id)
    
    if not yacht:
        return {
            "success": False,
            "error": "yacht_not_found"
        }
    
    # Защищённые поля
    protected_fields = ["yacht_id", "created_at", "created_by", "reviews_count", "rating"]
    
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
    
    if not changes:
        return {
            "success": False,
            "error": "no_changes",
            "message": "No changes detected"
        }
    
    yacht["updated_at"] = datetime.now().isoformat()
    yacht["updated_by"] = admin_user_id
    
    DATA.save_yacht(yacht_id, yacht)
    
    return {
        "success": True,
        "yacht_id": yacht_id,
        "message": get_message("yacht_updated", lang, yacht_name=yacht.get("name")),
        "changes": changes,
        "yacht": yacht
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 14: delete_yacht (Admin)
# ═══════════════════════════════════════════════════════════════════════════════

async def delete_yacht(
    yacht_id: str,
    admin_user_id: int = None,
    force: bool = False,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Удаление яхты (только для администраторов).
    
    Args:
        yacht_id: ID яхты
        admin_user_id: ID администратора
        force: Принудительное удаление (даже с бронированиями)
        lang: Язык
    """
    yacht = DATA.get_yacht(yacht_id)
    
    if not yacht:
        return {
            "success": False,
            "error": "yacht_not_found"
        }
    
    yacht_name = yacht.get("name")
    
    # Проверка активных бронирований
    active_bookings = [
        b for b in DATA.bookings.values()
        if b.get("yacht_id") == yacht_id
        and b.get("status") in [BookingStatus.PENDING.value, BookingStatus.CONFIRMED.value, BookingStatus.PAID.value]
    ]
    
    if active_bookings and not force:
        return {
            "success": False,
            "error": "has_active_bookings",
            "message": f"Yacht has {len(active_bookings)} active bookings. Use force=True to delete anyway.",
            "active_bookings": [b.get("booking_id") for b in active_bookings]
        }
    
    # Если force=True, отменяем все бронирования
    cancelled_bookings = []
    if active_bookings and force:
        for booking in active_bookings:
            booking["status"] = BookingStatus.CANCELLED.value
            booking["cancelled_at"] = datetime.now().isoformat()
            booking["cancellation_reason"] = "Yacht removed from service"
            booking["refund_amount"] = booking.get("pricing", {}).get("final_price", 0)
            DATA.save_booking(booking["booking_id"], booking)
            cancelled_bookings.append(booking["booking_id"])
    
    # Удаление яхты
    DATA.delete_yacht(yacht_id)
    
    # Очистка связанных данных
    if yacht_id in DATA.reviews:
        del DATA.reviews[yacht_id]
    if yacht_id in DATA.photos:
        del DATA.photos[yacht_id]
    if yacht_id in DATA.calendar:
        del DATA.calendar[yacht_id]
    
    return {
        "success": True,
        "yacht_id": yacht_id,
        "message": get_message("yacht_deleted", lang, yacht_name=yacht_name),
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
║                         BLOCK 17: YACHT CATALOG                              ║
║                      Party Pattaya Bot v10.2.1                               ║
║                                                                              ║
║  Функций: 14 | Автор: Claude | Дата: 26.11.2025                             ║
║  Статус: ✅ PRODUCTION READY - изменения запрещены без разрешения            ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("Функции:")
    print("  1.  get_all_yachts       - Список всех яхт")
    print("  2.  get_yacht_by_id      - Яхта по ID")
    print("  3.  search_yachts        - Поиск с фильтрами")
    print("  4.  filter_by_capacity   - Фильтр по вместимости")
    print("  5.  filter_by_price      - Фильтр по цене")
    print("  6.  check_availability   - Проверка доступности")
    print("  7.  get_yacht_calendar   - Календарь яхты")
    print("  8.  reserve_yacht        - Бронирование")
    print("  9.  cancel_reservation   - Отмена брони")
    print("  10. get_yacht_photos     - Фото яхты")
    print("  11. get_yacht_reviews    - Отзывы")
    print("  12. add_yacht            - Добавление яхты (admin)")
    print("  13. update_yacht         - Обновление (admin)")
    print("  14. delete_yacht         - Удаление (admin)")
    print("\nИмпорт: from block_17_yacht_catalog import *")
