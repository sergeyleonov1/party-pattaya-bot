"""
PARTY PATTAYA BOT v10.1 - БЛОКИ 1-4
"""
import os
import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict

class SaveLinksSystem:
    def __init__(self):
        self.links_file = 'data/saved_links.json'
        self.links = {}
        logging.info("BLOCK 1 SaveLinks: OK")
    
    def save_block_link(self, block_number, url, description=""):
        self.links[str(block_number)] = {'url': url, 'description': description}

class PostgreSQLDatabase:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.connection = None
        self.cursor = None
        logging.info("BLOCK 2 PostgreSQL: OK")
    
    def connect(self):
        return True

@dataclass
class User:
    user_id: int
    username: str = None
    first_name: str = None
    last_name: str = None
    language_code: str = 'ru'

class UserManagementSystem:
    def __init__(self, db=None):
        self.users_file = 'data/users.json'
        self.users = {}
        logging.info("BLOCK 3 Users: OK")
    
    def create_user(self, user_id, username=None, first_name=None, last_name=None):
        self.users[str(user_id)] = {'user_id': user_id, 'username': username}
        return User(user_id, username, first_name, last_name)
    
    def get_user(self, user_id):
        return self.users.get(str(user_id))

@dataclass
class Order:
    user_id: int
    service_type: str
    event_date: str
    guests_count: int
    total_amount: float
    status: str = 'pending'

class BookingSystem:
    SERVICES = {'yacht': {'min': 500, 'max': 2000}, 'party': {'min': 1000, 'max': 5000}, 'vip': {'min': 2000, 'max': 10000}, 'transfer': {'min': 20, 'max': 200}}
    
    def __init__(self, db=None):
        self.orders = {}
        self.next_id = 1
        logging.info("BLOCK 4 Booking: OK")
    
    def create_order(self, order):
        order_id = self.next_id
        self.next_id += 1
        self.orders[str(order_id)] = asdict(order)
        return order_id
