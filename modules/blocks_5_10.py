"""
PARTY PATTAYA BOT v10.1 - БЛОКИ 5-10
"""
import os
import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import requests

class GoogleCalendarIntegration:
    def __init__(self):
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        logging.info("BLOCK 5 Calendar: OK")
    
    def create_event(self, title, start, end):
        return f"event_{datetime.now().timestamp()}"
    
    def check_availability(self, start, end):
        return True

class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class PaymentSystem:
    def __init__(self):
        self.payments = {}
        logging.info("BLOCK 6 Payments: OK")
    
    def create_payment(self, amount, currency, order_id):
        payment_id = f"pay_{datetime.now().timestamp()}"
        self.payments[payment_id] = {'amount': amount, 'currency': currency, 'order_id': order_id}
        return payment_id

class NotificationSystem:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN', '')
        logging.info("BLOCK 7 Notifications: OK")
    
    def send_telegram(self, user_id, message):
        if not self.bot_token:
            return False
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            requests.post(url, json={'chat_id': user_id, 'text': message, 'parse_mode': 'HTML'}, timeout=10)
            return True
        except:
            return False

@dataclass
class Service:
    service_id: int
    name: str
    category: str
    price_min: float
    price_max: float
    max_guests: int

class ServiceCatalog:
    def __init__(self):
        self.services = {
            1: Service(1, "Yacht Sunset", "yacht", 500, 1200, 20),
            2: Service(2, "Yacht Premium", "yacht", 1200, 2000, 50),
            3: Service(3, "Beach Party", "party", 1000, 3000, 100),
            4: Service(4, "VIP Club", "party", 3000, 5000, 200),
            5: Service(5, "VIP Concierge", "vip", 2000, 5000, 10),
            6: Service(6, "VIP Elite", "vip", 5000, 10000, 30),
            7: Service(7, "Airport Transfer", "transfer", 20, 50, 4),
            8: Service(8, "VIP Transfer", "transfer", 100, 200, 6)
        }
        logging.info("BLOCK 8 Services: OK")
    
    def get_service(self, service_id):
        return self.services.get(service_id)
    
    def get_by_category(self, category):
        return [s for s in self.services.values() if s.category == category]

class InstagramGallery:
    def __init__(self):
        self.username = 'party_pattaya_city'
        self.posts = {}
        logging.info("BLOCK 9 Instagram: OK")
    
    def get_latest_posts(self, limit=12):
        return list(self.posts.values())[:limit]

class ReviewSystem:
    def __init__(self):
        self.reviews = {}
        self.next_id = 1
        logging.info("BLOCK 10 Reviews: OK")
    
    def create_review(self, user_id, service_id, rating, comment):
        review_id = self.next_id
        self.next_id += 1
        self.reviews[review_id] = {'user_id': user_id, 'service_id': service_id, 'rating': rating, 'comment': comment}
        return review_id
    
    def get_average_rating(self, service_id):
        service_reviews = [r for r in self.reviews.values() if r['service_id'] == service_id]
        if not service_reviews:
            return 0.0
        return sum(r['rating'] for r in service_reviews) / len(service_reviews)
