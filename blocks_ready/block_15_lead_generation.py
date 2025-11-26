"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    БЛОК 15: LEAD GENERATION AGENT - FULL                      ║
║                         Party Pattaya Bot v10.2.1                             ║
║                                                                               ║
║  Полная система генерации и квалификации лидов                               ║
║  10 функций по ТЗ | Автор: Сергей Леонов | Дата: 26.11.2025                  ║
║  Статус: ✅ ГОТОВ - изменения запрещены без разрешения                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import asyncio, json, re, uuid, hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger("block_15")

# === ENUMS ===
class LeadSource(Enum):
    TELEGRAM = "telegram"
    WEBSITE = "website"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    WHATSAPP = "whatsapp"
    REFERRAL = "referral"
    ORGANIC = "organic"
    GOOGLE_ADS = "google_ads"
    FACEBOOK_ADS = "facebook_ads"
    TIKTOK = "tiktok"

class LeadStatus(Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    NURTURING = "nurturing"

class LeadTemperature(Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"

class QualificationLevel(Enum):
    UNQUALIFIED = "unqualified"
    MQL = "mql"  # Marketing Qualified Lead
    SQL = "sql"  # Sales Qualified Lead
    PQL = "pql"  # Product Qualified Lead

# === CONFIG ===
@dataclass
class LeadGenConfig:
    admin_id: int = 359364877
    admin_telegram: str = "@Party_Pattaya"
    admin_whatsapp: str = "+66-633-633-407"
    admin_email: str = "Liliya@partypattayacity.com"
    company_name: str = "Party Pattaya"
    qualification_threshold: int = 60
    hot_lead_threshold: int = 80
    warm_lead_threshold: int = 50
    mql_threshold: int = 40
    sql_threshold: int = 70
    max_leads_per_agent: int = 50
    nurture_sequence_days: int = 30
    scoring_weights: Dict = field(default_factory=lambda: {
        "budget_match": 25,
        "timeline_urgency": 20,
        "group_size": 15,
        "engagement_level": 15,
        "source_quality": 10,
        "repeat_customer": 10,
        "referral_bonus": 5
    })
    source_quality_scores: Dict = field(default_factory=lambda: {
        "referral": 90,
        "organic": 75,
        "telegram": 80,
        "whatsapp": 85,
        "website": 70,
        "instagram": 65,
        "facebook": 60,
        "google_ads": 55,
        "facebook_ads": 50,
        "tiktok": 45
    })
    agents: List[Dict] = field(default_factory=lambda: [
        {"id": "agent_1", "name": "Лилия", "specialization": ["yacht", "vip"], "capacity": 50, "current_load": 0},
        {"id": "agent_2", "name": "Менеджер 2", "specialization": ["party", "transfer"], "capacity": 50, "current_load": 0},
        {"id": "agent_3", "name": "Менеджер 3", "specialization": ["all"], "capacity": 30, "current_load": 0}
    ])

CONFIG = LeadGenConfig()

# === DATA STORE ===
class LeadDataStore:
    def __init__(self):
        self.leads: Dict[str, Dict] = {}
        self.campaigns: Dict[str, Dict] = {}
        self.lead_magnets: Dict[str, Dict] = {}
        self.ab_tests: Dict[str, Dict] = {}
        self.nurture_sequences: Dict[str, List[Dict]] = {
            "default": [
                {"day": 1, "type": "welcome", "template": "welcome_email"},
                {"day": 3, "type": "value", "template": "service_overview"},
                {"day": 7, "type": "social_proof", "template": "testimonials"},
                {"day": 14, "type": "offer", "template": "special_discount"},
                {"day": 21, "type": "urgency", "template": "limited_time"},
                {"day": 30, "type": "final", "template": "last_chance"}
            ],
            "vip": [
                {"day": 0, "type": "personal_call", "template": "vip_welcome"},
                {"day": 1, "type": "concierge", "template": "vip_services"},
                {"day": 3, "type": "exclusive", "template": "vip_exclusive_offer"}
            ],
            "reactivation": [
                {"day": 1, "type": "reconnect", "template": "we_miss_you"},
                {"day": 7, "type": "special", "template": "comeback_offer"},
                {"day": 14, "type": "final", "template": "last_chance_return"}
            ]
        }
        self.sources_stats: Dict[str, Dict] = {s.value: {"total": 0, "qualified": 0, "converted": 0, "revenue": 0} for s in LeadSource}
        self.funnel_stats: Dict[str, int] = {s.value: 0 for s in LeadStatus}
        self.metrics: Dict = {
            "total_leads": 0,
            "qualified_leads": 0,
            "converted": 0,
            "revenue": 0,
            "avg_score": 0,
            "conversion_rate": 0,
            "avg_conversion_time_hours": 0
        }

    def get_lead(self, lead_id: str) -> Optional[Dict]:
        return self.leads.get(lead_id)

    def save_lead(self, lead: Dict) -> str:
        lead_id = lead.get("lead_id") or str(uuid.uuid4())[:8]
        lead["lead_id"] = lead_id
        lead["updated_at"] = datetime.now().isoformat()
        self.leads[lead_id] = lead
        return lead_id

DATA = LeadDataStore()

# === HELPER FUNCTIONS ===
def generate_lead_id() -> str:
    return f"L{datetime.now().strftime('%y%m%d')}{str(uuid.uuid4())[:6].upper()}"

def detect_language(text: str) -> str:
    if len(re.findall(r"[а-яА-ЯёЁ]", text)) / max(len(text), 1) > 0.3:
        return "ru"
    if len(re.findall(r"[\u0E00-\u0E7F]", text)) / max(len(text), 1) > 0.3:
        return "th"
    if len(re.findall(r"[\u4e00-\u9fff]", text)) / max(len(text), 1) > 0.3:
        return "zh"
    return "en"

def extract_contact_type(contact_info: Dict) -> str:
    if contact_info.get("telegram"):
        return "telegram"
    if contact_info.get("whatsapp"):
        return "whatsapp"
    if contact_info.get("email"):
        return "email"
    if contact_info.get("phone"):
        return "phone"
    return "unknown"

# === FUNCTION 1: CAPTURE_LEAD ===
async def capture_lead(source: str, contact_info: Dict, initial_message: str = None, utm_params: Dict = None) -> Dict[str, Any]:
    """Захват лида с детальной информацией об источнике"""
    lead_id = generate_lead_id()
    
    lang = detect_language(initial_message) if initial_message else "en"
    contact_type = extract_contact_type(contact_info)
    
    source_quality = CONFIG.source_quality_scores.get(source, 50)
    initial_score = source_quality // 2
    
    initial_temperature = "hot" if source in ["referral", "whatsapp"] else "warm" if source in ["telegram", "organic"] else "cold"
    
    lead = {
        "lead_id": lead_id,
        "source": source,
        "contact_info": contact_info,
        "contact_type": contact_type,
        "initial_message": initial_message,
        "language": lang,
        "utm_params": utm_params or {},
        "status": LeadStatus.NEW.value,
        "temperature": initial_temperature,
        "score": initial_score,
        "qualification_level": QualificationLevel.UNQUALIFIED.value,
        "assigned_agent": None,
        "tags": [],
        "notes": [],
        "interactions": [{"type": "captured", "timestamp": datetime.now().isoformat(), "details": f"Source: {source}"}],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "conversion_data": None
    }
    
    DATA.save_lead(lead)
    DATA.metrics["total_leads"] += 1
    DATA.sources_stats[source]["total"] = DATA.sources_stats.get(source, {}).get("total", 0) + 1
    DATA.funnel_stats[LeadStatus.NEW.value] += 1
    
    campaign_id = utm_params.get("campaign") if utm_params else None
    if campaign_id and campaign_id in DATA.campaigns:
        DATA.campaigns[campaign_id]["leads_captured"] = DATA.campaigns[campaign_id].get("leads_captured", 0) + 1
    
    logger.info(f"Lead captured: {lead_id} from {source}")
    
    return {
        "lead_id": lead_id,
        "source": source,
        "initial_score": initial_score,
        "temperature": initial_temperature,
        "status": LeadStatus.NEW.value,
        "language": lang,
        "contact_type": contact_type,
        "next_action": "qualify" if initial_temperature == "hot" else "nurture",
        "recommended_response_time": "< 5 min" if initial_temperature == "hot" else "< 1 hour",
        "captured_at": datetime.now().isoformat()
    }


# === FUNCTION 2: QUALIFY_LEAD ===
async def qualify_lead(lead_id: str, qualification_data: Dict) -> Dict[str, Any]:
    """Квалификация лида по BANT критериям"""
    lead = DATA.get_lead(lead_id)
    if not lead:
        return {"error": "Lead not found", "lead_id": lead_id}
    
    # BANT: Budget, Authority, Need, Timeline
    budget = qualification_data.get("budget", 0)
    has_authority = qualification_data.get("has_authority", False)
    need_level = qualification_data.get("need_level", "low")  # low, medium, high
    timeline = qualification_data.get("timeline", "undefined")  # immediate, this_week, this_month, quarter, undefined
    group_size = qualification_data.get("group_size", 1)
    service_interest = qualification_data.get("service_interest", [])
    
    # Scoring по критериям
    scores = {"budget": 0, "authority": 0, "need": 0, "timeline": 0, "group": 0, "service": 0}
    
    # Budget scoring
    if budget >= 5000:
        scores["budget"] = 25
    elif budget >= 2000:
        scores["budget"] = 20
    elif budget >= 1000:
        scores["budget"] = 15
    elif budget >= 500:
        scores["budget"] = 10
    elif budget > 0:
        scores["budget"] = 5
    
    # Authority scoring
    scores["authority"] = 15 if has_authority else 5
    
    # Need scoring
    need_scores = {"high": 20, "medium": 12, "low": 5}
    scores["need"] = need_scores.get(need_level, 5)
    
    # Timeline scoring
    timeline_scores = {"immediate": 20, "this_week": 15, "this_month": 10, "quarter": 5, "undefined": 2}
    scores["timeline"] = timeline_scores.get(timeline, 2)
    
    # Group size scoring
    if group_size >= 20:
        scores["group"] = 15
    elif group_size >= 10:
        scores["group"] = 10
    elif group_size >= 5:
        scores["group"] = 5
    
    # Service interest scoring
    high_value_services = ["yacht_vip", "vip_club", "beach_party"]
    if any(s in service_interest for s in high_value_services):
        scores["service"] = 10
    elif service_interest:
        scores["service"] = 5
    
    total_score = sum(scores.values())
    
    # Determine qualification level
    if total_score >= CONFIG.sql_threshold:
        qual_level = QualificationLevel.SQL.value
        lead["status"] = LeadStatus.QUALIFIED.value
    elif total_score >= CONFIG.mql_threshold:
        qual_level = QualificationLevel.MQL.value
        lead["status"] = LeadStatus.CONTACTED.value
    else:
        qual_level = QualificationLevel.UNQUALIFIED.value
    
    # Determine temperature
    if total_score >= CONFIG.hot_lead_threshold:
        temperature = LeadTemperature.HOT.value
    elif total_score >= CONFIG.warm_lead_threshold:
        temperature = LeadTemperature.WARM.value
    else:
        temperature = LeadTemperature.COLD.value
    
    # Update lead
    lead["score"] = total_score
    lead["temperature"] = temperature
    lead["qualification_level"] = qual_level
    lead["qualification_data"] = {
        "budget": budget,
        "has_authority": has_authority,
        "need_level": need_level,
        "timeline": timeline,
        "group_size": group_size,
        "service_interest": service_interest,
        "scores_breakdown": scores,
        "qualified_at": datetime.now().isoformat()
    }
    lead["interactions"].append({
        "type": "qualified",
        "timestamp": datetime.now().isoformat(),
        "details": f"Score: {total_score}, Level: {qual_level}"
    })
    
    DATA.save_lead(lead)
    
    if qual_level in [QualificationLevel.SQL.value, QualificationLevel.MQL.value]:
        DATA.metrics["qualified_leads"] += 1
        DATA.sources_stats[lead["source"]]["qualified"] += 1
    
    # Determine next action
    next_actions = {
        QualificationLevel.SQL.value: "assign_to_sales",
        QualificationLevel.MQL.value: "nurture_with_content",
        QualificationLevel.UNQUALIFIED.value: "add_to_drip_campaign"
    }
    
    return {
        "lead_id": lead_id,
        "total_score": total_score,
        "qualification_level": qual_level,
        "temperature": temperature,
        "scores_breakdown": scores,
        "bant_analysis": {
            "budget_adequate": budget >= 500,
            "has_authority": has_authority,
            "need_confirmed": need_level in ["medium", "high"],
            "timeline_defined": timeline != "undefined"
        },
        "status": lead["status"],
        "next_action": next_actions.get(qual_level, "review"),
        "priority": "high" if qual_level == QualificationLevel.SQL.value else "medium" if qual_level == QualificationLevel.MQL.value else "low",
        "qualified_at": datetime.now().isoformat()
    }

# === FUNCTION 3: SCORE_LEAD ===
async def score_lead(lead_id: str, scoring_factors: Dict = None) -> Dict[str, Any]:
    """Динамический скоринг лида с учетом множества факторов"""
    lead = DATA.get_lead(lead_id)
    if not lead:
        return {"error": "Lead not found", "lead_id": lead_id}
    
    factors = scoring_factors or {}
    weights = CONFIG.scoring_weights
    
    scores = {}
    max_possible = 0
    
    # 1. Budget match (0-25)
    budget = factors.get("budget", lead.get("qualification_data", {}).get("budget", 0))
    if budget >= 5000:
        scores["budget_match"] = 25
    elif budget >= 2000:
        scores["budget_match"] = 20
    elif budget >= 1000:
        scores["budget_match"] = 15
    elif budget >= 500:
        scores["budget_match"] = 10
    else:
        scores["budget_match"] = budget // 100
    max_possible += weights["budget_match"]
    
    # 2. Timeline urgency (0-20)
    timeline = factors.get("timeline", lead.get("qualification_data", {}).get("timeline", "undefined"))
    timeline_scores = {"immediate": 20, "this_week": 16, "this_month": 12, "quarter": 6, "undefined": 2}
    scores["timeline_urgency"] = timeline_scores.get(timeline, 2)
    max_possible += weights["timeline_urgency"]
    
    # 3. Group size (0-15)
    group_size = factors.get("group_size", lead.get("qualification_data", {}).get("group_size", 1))
    if group_size >= 50:
        scores["group_size"] = 15
    elif group_size >= 20:
        scores["group_size"] = 12
    elif group_size >= 10:
        scores["group_size"] = 8
    elif group_size >= 5:
        scores["group_size"] = 5
    else:
        scores["group_size"] = 2
    max_possible += weights["group_size"]
    
    # 4. Engagement level (0-15)
    interactions = len(lead.get("interactions", []))
    response_rate = factors.get("response_rate", 0.5)
    engagement_score = min(15, interactions * 2 + int(response_rate * 10))
    scores["engagement_level"] = engagement_score
    max_possible += weights["engagement_level"]
    
    # 5. Source quality (0-10)
    source = lead.get("source", "unknown")
    source_quality = CONFIG.source_quality_scores.get(source, 50)
    scores["source_quality"] = int(source_quality / 10)
    max_possible += weights["source_quality"]
    
    # 6. Repeat customer bonus (0-10)
    is_repeat = factors.get("is_repeat_customer", False)
    previous_orders = factors.get("previous_orders", 0)
    if is_repeat:
        scores["repeat_customer"] = min(10, 5 + previous_orders)
    else:
        scores["repeat_customer"] = 0
    max_possible += weights["repeat_customer"]
    
    # 7. Referral bonus (0-5)
    is_referral = lead.get("source") == "referral" or factors.get("is_referral", False)
    scores["referral_bonus"] = 5 if is_referral else 0
    max_possible += weights["referral_bonus"]
    
    # Calculate total
    total_score = sum(scores.values())
    normalized_score = int((total_score / max_possible) * 100) if max_possible > 0 else 0
    
    # Update temperature based on score
    if normalized_score >= CONFIG.hot_lead_threshold:
        temperature = LeadTemperature.HOT.value
    elif normalized_score >= CONFIG.warm_lead_threshold:
        temperature = LeadTemperature.WARM.value
    else:
        temperature = LeadTemperature.COLD.value
    
    # Score change tracking
    previous_score = lead.get("score", 0)
    score_change = normalized_score - previous_score
    
    # Update lead
    lead["score"] = normalized_score
    lead["temperature"] = temperature
    lead["scoring_history"] = lead.get("scoring_history", [])
    lead["scoring_history"].append({
        "score": normalized_score,
        "factors": scores,
        "timestamp": datetime.now().isoformat()
    })
    
    DATA.save_lead(lead)
    
    # Update metrics
    all_scores = [l.get("score", 0) for l in DATA.leads.values()]
    DATA.metrics["avg_score"] = sum(all_scores) / len(all_scores) if all_scores else 0
    
    return {
        "lead_id": lead_id,
        "total_score": normalized_score,
        "raw_score": total_score,
        "max_possible": max_possible,
        "temperature": temperature,
        "factors_breakdown": scores,
        "score_change": score_change,
        "trend": "up" if score_change > 0 else "down" if score_change < 0 else "stable",
        "percentile": f"Top {100 - normalized_score}%" if normalized_score > 50 else f"Bottom {normalized_score}%",
        "recommendations": [
            "Priority follow-up" if normalized_score >= 80 else "Standard nurture",
            "Assign to senior agent" if normalized_score >= 70 else "Auto-nurture sequence"
        ],
        "scored_at": datetime.now().isoformat()
    }

# === FUNCTION 4: ASSIGN_LEAD ===
async def assign_lead(lead_id: str, assignment_rules: Dict = None) -> Dict[str, Any]:
    """Назначение лида агенту по специализации и загрузке"""
    lead = DATA.get_lead(lead_id)
    if not lead:
        return {"error": "Lead not found", "lead_id": lead_id}
    
    rules = assignment_rules or {}
    force_agent = rules.get("force_agent")
    preferred_specialization = rules.get("specialization")
    priority = rules.get("priority", "normal")
    
    agents = CONFIG.agents.copy()
    
    # If force assignment
    if force_agent:
        agent = next((a for a in agents if a["id"] == force_agent), None)
        if agent:
            lead["assigned_agent"] = agent["id"]
            lead["assignment"] = {
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "assigned_at": datetime.now().isoformat(),
                "method": "forced",
                "priority": priority
            }
            DATA.save_lead(lead)
            return {
                "lead_id": lead_id,
                "assigned_to": agent["id"],
                "agent_name": agent["name"],
                "method": "forced",
                "success": True
            }
    
    # Determine required specialization from lead data
    service_interest = lead.get("qualification_data", {}).get("service_interest", [])
    if not preferred_specialization:
        if any("yacht" in s or "vip" in s for s in service_interest):
            preferred_specialization = "yacht"
        elif any("party" in s for s in service_interest):
            preferred_specialization = "party"
        elif any("transfer" in s for s in service_interest):
            preferred_specialization = "transfer"
    
    # Score agents
    agent_scores = []
    for agent in agents:
        score = 0
        
        # Capacity check
        capacity_ratio = agent["current_load"] / agent["capacity"]
        if capacity_ratio >= 1:
            continue  # Skip full agents
        score += int((1 - capacity_ratio) * 40)  # Up to 40 points for availability
        
        # Specialization match
        specs = agent["specialization"]
        if "all" in specs:
            score += 20
        elif preferred_specialization and preferred_specialization in specs:
            score += 30
        elif preferred_specialization:
            score += 5
        
        # Priority bonus for hot leads
        if priority == "high" and lead.get("temperature") == "hot":
            if agent["current_load"] < agent["capacity"] * 0.5:
                score += 20
        
        agent_scores.append({"agent": agent, "score": score})
    
    if not agent_scores:
        return {
            "lead_id": lead_id,
            "assigned_to": None,
            "error": "No available agents",
            "recommendation": "Add to queue or expand team",
            "success": False
        }
    
    # Select best agent
    agent_scores.sort(key=lambda x: x["score"], reverse=True)
    best_agent = agent_scores[0]["agent"]
    
    # Update lead
    lead["assigned_agent"] = best_agent["id"]
    lead["status"] = LeadStatus.CONTACTED.value if lead["status"] == LeadStatus.NEW.value else lead["status"]
    lead["assignment"] = {
        "agent_id": best_agent["id"],
        "agent_name": best_agent["name"],
        "assigned_at": datetime.now().isoformat(),
        "method": "auto",
        "priority": priority,
        "match_score": agent_scores[0]["score"]
    }
    lead["interactions"].append({
        "type": "assigned",
        "timestamp": datetime.now().isoformat(),
        "details": f"Assigned to {best_agent['name']}"
    })
    
    DATA.save_lead(lead)
    
    # Update agent load (in real system this would be in agent store)
    for a in CONFIG.agents:
        if a["id"] == best_agent["id"]:
            a["current_load"] += 1
            break
    
    return {
        "lead_id": lead_id,
        "assigned_to": best_agent["id"],
        "agent_name": best_agent["name"],
        "specialization": best_agent["specialization"],
        "method": "auto",
        "match_score": agent_scores[0]["score"],
        "agent_current_load": best_agent["current_load"] + 1,
        "agent_capacity": best_agent["capacity"],
        "priority": priority,
        "next_action": "Contact within 5 minutes" if priority == "high" else "Contact within 1 hour",
        "success": True,
        "assigned_at": datetime.now().isoformat()
    }

# === FUNCTION 5: NURTURE_LEAD ===
async def nurture_lead(lead_id: str, nurture_sequence: str = "default", custom_content: Dict = None) -> Dict[str, Any]:
    """Nurture sequences для разных сегментов лидов"""
    lead = DATA.get_lead(lead_id)
    if not lead:
        return {"error": "Lead not found", "lead_id": lead_id}
    
    sequence = DATA.nurture_sequences.get(nurture_sequence, DATA.nurture_sequences["default"])
    lang = lead.get("language", "en")
    
    # Templates for different languages
    templates = {
        "welcome_email": {
            "ru": "🎉 Добро пожаловать в Party Pattaya! Мы рады видеть вас. Готовы организовать незабываемый отдых!",
            "en": "🎉 Welcome to Party Pattaya! We are glad to see you. Ready to organize an unforgettable vacation!",
            "th": "🎉 ยินดีต้อนรับสู่ Party Pattaya! เรายินดีที่ได้พบคุณ",
            "zh": "🎉 欢迎来到Party Pattaya！我们很高兴见到您。"
        },
        "service_overview": {
            "ru": "🛥 Наши услуги: Яхты от $500, Вечеринки от $1000, VIP от $2000, Трансферы от $20. Что вас интересует?",
            "en": "🛥 Our services: Yachts from $500, Parties from $1000, VIP from $2000, Transfers from $20. What interests you?",
            "th": "🛥 บริการของเรา: เรือยอช์ท $500, ปาร์ตี้ $1000, VIP $2000, รถรับส่ง $20",
            "zh": "🛥 我们的服务：游艇$500起，派对$1000起，VIP $2000起，接送$20起"
        },
        "testimonials": {
            "ru": "⭐ 500+ довольных клиентов! Рейтинг 4.8/5. Читайте отзывы наших гостей.",
            "en": "⭐ 500+ happy customers! Rating 4.8/5. Read our guest reviews.",
            "th": "⭐ ลูกค้ามากกว่า 500 คน! คะแนน 4.8/5",
            "zh": "⭐ 500多位满意客户！评分4.8/5"
        },
        "special_discount": {
            "ru": "🎁 Специально для вас: скидка 15% на первый заказ! Код: WELCOME15",
            "en": "🎁 Special for you: 15% off your first order! Code: WELCOME15",
            "th": "🎁 พิเศษสำหรับคุณ: ส่วนลด 15%! รหัส: WELCOME15",
            "zh": "🎁 特别优惠：首单85折！代码：WELCOME15"
        },
        "limited_time": {
            "ru": "⏰ Ограниченное предложение! Скидка 20% действует только 48 часов!",
            "en": "⏰ Limited offer! 20% discount valid for 48 hours only!",
            "th": "⏰ ข้อเสนอจำกัด! ส่วนลด 20% เฉพาะ 48 ชั่วโมง!",
            "zh": "⏰ 限时优惠！8折仅限48小时！"
        },
        "last_chance": {
            "ru": "🔥 Последний шанс! Ваша скидка истекает сегодня. Не упустите!",
            "en": "🔥 Last chance! Your discount expires today. Don\'t miss out!",
            "th": "🔥 โอกาสสุดท้าย! ส่วนลดของคุณหมดอายุวันนี้!",
            "zh": "🔥 最后机会！您的折扣今天到期！"
        },
        "vip_welcome": {
            "ru": "👑 VIP Приветствие! Ваш персональный менеджер свяжется с вами в течение часа.",
            "en": "👑 VIP Welcome! Your personal manager will contact you within an hour.",
            "th": "👑 ยินดีต้อนรับ VIP! ผู้จัดการส่วนตัวจะติดต่อคุณภายในหนึ่งชั่วโมง",
            "zh": "👑 VIP欢迎！您的专属经理将在一小时内联系您。"
        },
        "we_miss_you": {
            "ru": "💫 Мы скучаем! Давно не виделись. Специальное предложение для вас внутри.",
            "en": "💫 We miss you! It\'s been a while. Special offer inside for you.",
            "th": "💫 เราคิดถึงคุณ! ข้อเสนอพิเศษสำหรับคุณ",
            "zh": "💫 我们想念您！好久不见。特别优惠等着您。"
        },
        "comeback_offer": {
            "ru": "🎁 Возвращайтесь! Скидка 25% на следующий заказ. Мы ждём вас!",
            "en": "🎁 Come back! 25% off your next order. We are waiting for you!",
            "th": "🎁 กลับมาเถอะ! ส่วนลด 25% สำหรับคำสั่งซื้อถัดไป",
            "zh": "🎁 回来吧！下单享75折优惠！"
        }
    }
    
    # Build nurture schedule
    scheduled_messages = []
    start_date = datetime.now()
    
    for step in sequence:
        template_key = step.get("template", "welcome_email")
        template = templates.get(template_key, {})
        message_text = custom_content.get(template_key) if custom_content else None
        message_text = message_text or template.get(lang, template.get("en", ""))
        
        send_date = start_date + timedelta(days=step["day"])
        
        scheduled_messages.append({
            "day": step["day"],
            "type": step["type"],
            "template": template_key,
            "message": message_text,
            "scheduled_at": send_date.isoformat(),
            "status": "scheduled"
        })
    
    # Update lead
    lead["nurture_sequence"] = nurture_sequence
    lead["nurture_schedule"] = scheduled_messages
    lead["nurture_started_at"] = datetime.now().isoformat()
    lead["status"] = LeadStatus.NURTURING.value if lead["status"] == LeadStatus.NEW.value else lead["status"]
    lead["interactions"].append({
        "type": "nurture_started",
        "timestamp": datetime.now().isoformat(),
        "details": f"Sequence: {nurture_sequence}, Messages: {len(scheduled_messages)}"
    })
    
    DATA.save_lead(lead)
    
    return {
        "lead_id": lead_id,
        "sequence": nurture_sequence,
        "total_messages": len(scheduled_messages),
        "duration_days": sequence[-1]["day"] if sequence else 0,
        "language": lang,
        "scheduled_messages": scheduled_messages,
        "first_message": scheduled_messages[0] if scheduled_messages else None,
        "status": "active",
        "started_at": datetime.now().isoformat()
    }


# === FUNCTION 6: TRACK_LEAD_SOURCE ===
async def track_lead_source(source: str, campaign_id: str = None, metrics: Dict = None) -> Dict[str, Any]:
    """Детальная аналитика по источникам лидов"""
    
    # Initialize or update campaign
    if campaign_id:
        if campaign_id not in DATA.campaigns:
            DATA.campaigns[campaign_id] = {
                "campaign_id": campaign_id,
                "source": source,
                "created_at": datetime.now().isoformat(),
                "leads_captured": 0,
                "leads_qualified": 0,
                "leads_converted": 0,
                "revenue": 0,
                "spend": metrics.get("spend", 0) if metrics else 0,
                "impressions": 0,
                "clicks": 0
            }
        
        if metrics:
            camp = DATA.campaigns[campaign_id]
            camp["impressions"] += metrics.get("impressions", 0)
            camp["clicks"] += metrics.get("clicks", 0)
            camp["spend"] += metrics.get("spend", 0)
    
    # Get source statistics
    source_stats = DATA.sources_stats.get(source, {"total": 0, "qualified": 0, "converted": 0, "revenue": 0})
    
    # Calculate rates
    total = source_stats["total"] or 1
    qualification_rate = source_stats["qualified"] / total
    conversion_rate = source_stats["converted"] / total
    avg_value = source_stats["revenue"] / max(source_stats["converted"], 1)
    
    # Get leads from this source
    source_leads = [l for l in DATA.leads.values() if l.get("source") == source]
    
    # Calculate time metrics
    conversion_times = []
    for lead in source_leads:
        if lead.get("conversion_data") and lead.get("created_at"):
            try:
                created = datetime.fromisoformat(lead["created_at"])
                converted = datetime.fromisoformat(lead["conversion_data"].get("converted_at", ""))
                conversion_times.append((converted - created).total_seconds() / 3600)
            except:
                pass
    
    avg_conversion_time = sum(conversion_times) / len(conversion_times) if conversion_times else None
    
    # Source quality assessment
    source_quality = CONFIG.source_quality_scores.get(source, 50)
    quality_label = "Excellent" if source_quality >= 80 else "Good" if source_quality >= 60 else "Average" if source_quality >= 40 else "Poor"
    
    # Campaign performance if exists
    campaign_data = None
    if campaign_id and campaign_id in DATA.campaigns:
        camp = DATA.campaigns[campaign_id]
        ctr = camp["clicks"] / max(camp["impressions"], 1)
        cpl = camp["spend"] / max(camp["leads_captured"], 1)
        cpa = camp["spend"] / max(camp["leads_converted"], 1)
        roi = (camp["revenue"] - camp["spend"]) / max(camp["spend"], 1) * 100
        
        campaign_data = {
            "campaign_id": campaign_id,
            "impressions": camp["impressions"],
            "clicks": camp["clicks"],
            "ctr": round(ctr * 100, 2),
            "leads": camp["leads_captured"],
            "conversions": camp["leads_converted"],
            "spend": camp["spend"],
            "revenue": camp["revenue"],
            "cpl": round(cpl, 2),
            "cpa": round(cpa, 2),
            "roi": round(roi, 1)
        }
    
    return {
        "source": source,
        "source_quality": source_quality,
        "quality_label": quality_label,
        "statistics": {
            "total_leads": source_stats["total"],
            "qualified_leads": source_stats["qualified"],
            "converted_leads": source_stats["converted"],
            "total_revenue": source_stats["revenue"],
            "qualification_rate": round(qualification_rate * 100, 1),
            "conversion_rate": round(conversion_rate * 100, 1),
            "avg_deal_value": round(avg_value, 2),
            "avg_conversion_time_hours": round(avg_conversion_time, 1) if avg_conversion_time else None
        },
        "campaign": campaign_data,
        "recommendations": [
            f"Increase budget - high ROI" if campaign_data and campaign_data.get("roi", 0) > 100 else "Optimize targeting",
            f"Good source quality ({quality_label})" if source_quality >= 60 else "Consider alternative sources"
        ],
        "tracked_at": datetime.now().isoformat()
    }

# === FUNCTION 7: CREATE_LEAD_MAGNET ===
async def create_lead_magnet(magnet_type: str, content: Dict, target_audience: Dict = None) -> Dict[str, Any]:
    """Создание лид-магнитов разных типов"""
    
    magnet_templates = {
        "ebook": {
            "title_template": "Ultimate Guide to {topic}",
            "format": "pdf",
            "avg_conversion": 15,
            "best_for": ["education", "b2b"]
        },
        "discount": {
            "title_template": "{percent}% Off Your First {service}",
            "format": "code",
            "avg_conversion": 25,
            "best_for": ["immediate_purchase", "price_sensitive"]
        },
        "checklist": {
            "title_template": "{topic} Checklist",
            "format": "pdf",
            "avg_conversion": 20,
            "best_for": ["planning", "organization"]
        },
        "consultation": {
            "title_template": "Free {duration} Consultation",
            "format": "booking",
            "avg_conversion": 30,
            "best_for": ["high_value", "complex_services"]
        },
        "quiz": {
            "title_template": "Which {service} is Right for You?",
            "format": "interactive",
            "avg_conversion": 35,
            "best_for": ["engagement", "segmentation"]
        },
        "video": {
            "title_template": "Exclusive {topic} Video",
            "format": "video",
            "avg_conversion": 18,
            "best_for": ["demonstration", "trust_building"]
        },
        "webinar": {
            "title_template": "Live: {topic} Masterclass",
            "format": "live_event",
            "avg_conversion": 40,
            "best_for": ["high_engagement", "b2b"]
        }
    }
    
    template = magnet_templates.get(magnet_type, magnet_templates["discount"])
    
    # Generate magnet
    magnet_id = f"LM{datetime.now().strftime('%y%m%d')}{str(uuid.uuid4())[:4].upper()}"
    
    title = content.get("title") or template["title_template"].format(
        topic=content.get("topic", "Pattaya Events"),
        percent=content.get("percent", 15),
        service=content.get("service", "Booking"),
        duration=content.get("duration", "30-min")
    )
    
    # Landing page elements
    landing_page = {
        "headline": title,
        "subheadline": content.get("subheadline", "Get instant access now!"),
        "bullet_points": content.get("bullet_points", [
            "Exclusive content",
            "Instant delivery",
            "100% Free"
        ]),
        "cta_button": content.get("cta", "Get Free Access"),
        "form_fields": ["email", "name"] if magnet_type != "discount" else ["email"],
        "trust_badges": ["500+ customers", "4.8★ rating", "Secure"]
    }
    
    # Target audience settings
    audience = target_audience or {}
    targeting = {
        "languages": audience.get("languages", ["ru", "en"]),
        "interests": audience.get("interests", ["travel", "events", "nightlife"]),
        "age_range": audience.get("age_range", [25, 55]),
        "locations": audience.get("locations", ["Thailand", "Russia", "Europe"])
    }
    
    magnet = {
        "magnet_id": magnet_id,
        "type": magnet_type,
        "title": title,
        "format": template["format"],
        "content": content,
        "landing_page": landing_page,
        "targeting": targeting,
        "expected_conversion": template["avg_conversion"],
        "best_for": template["best_for"],
        "status": "active",
        "leads_captured": 0,
        "created_at": datetime.now().isoformat()
    }
    
    DATA.lead_magnets[magnet_id] = magnet
    
    return {
        "magnet_id": magnet_id,
        "type": magnet_type,
        "title": title,
        "format": template["format"],
        "landing_page": landing_page,
        "targeting": targeting,
        "expected_conversion_rate": f"{template['avg_conversion']}%",
        "best_for": template["best_for"],
        "status": "active",
        "next_steps": [
            "Set up tracking pixel",
            "Create thank-you page",
            "Set up email automation"
        ],
        "created_at": datetime.now().isoformat()
    }

# === FUNCTION 8: AB_TEST_LEAD_CAPTURE ===
async def ab_test_lead_capture(test_name: str, variants: List[Dict], traffic_split: List[float] = None) -> Dict[str, Any]:
    """A/B тестирование вариантов захвата лидов"""
    
    test_id = f"AB{datetime.now().strftime('%y%m%d')}{str(uuid.uuid4())[:4].upper()}"
    
    # Default equal split
    if not traffic_split:
        traffic_split = [1.0 / len(variants)] * len(variants)
    
    # Validate split
    if abs(sum(traffic_split) - 1.0) > 0.01:
        return {"error": "Traffic split must sum to 1.0"}
    
    # Initialize variants with tracking
    test_variants = []
    for i, variant in enumerate(variants):
        var_id = f"{test_id}_V{chr(65 + i)}"  # V_A, V_B, etc.
        test_variants.append({
            "variant_id": var_id,
            "name": variant.get("name", f"Variant {chr(65 + i)}"),
            "traffic_percent": round(traffic_split[i] * 100, 1),
            "headline": variant.get("headline", ""),
            "cta": variant.get("cta", ""),
            "image": variant.get("image", ""),
            "form_fields": variant.get("form_fields", ["email"]),
            "impressions": 0,
            "conversions": 0,
            "conversion_rate": 0,
            "confidence": 0
        })
    
    test = {
        "test_id": test_id,
        "test_name": test_name,
        "variants": test_variants,
        "status": "running",
        "start_date": datetime.now().isoformat(),
        "end_date": None,
        "winner": None,
        "min_sample_size": 100,
        "confidence_threshold": 95
    }
    
    DATA.ab_tests[test_id] = test
    
    return {
        "test_id": test_id,
        "test_name": test_name,
        "variants_count": len(test_variants),
        "variants": test_variants,
        "traffic_split": [f"{s*100:.0f}%" for s in traffic_split],
        "status": "running",
        "min_sample_per_variant": 100,
        "confidence_threshold": "95%",
        "estimated_duration": "7-14 days",
        "recommendations": [
            "Run for at least 7 days",
            "Ensure minimum 100 conversions per variant",
            "Don't peek at results early"
        ],
        "started_at": datetime.now().isoformat()
    }

# === FUNCTION 9: ANALYZE_LEAD_FUNNEL ===
async def analyze_lead_funnel(period: str = "week", segment: str = None) -> Dict[str, Any]:
    """Детальный анализ воронки лидов по этапам"""
    
    period_days = {"day": 1, "week": 7, "month": 30, "quarter": 90}
    days = period_days.get(period, 7)
    
    # Get funnel stats
    funnel = DATA.funnel_stats.copy()
    total_leads = DATA.metrics.get("total_leads", 0) or 1
    
    # Define funnel stages with expected rates
    stages = [
        {"name": "Captured", "status": "new", "count": funnel.get("new", 0), "expected_rate": 100},
        {"name": "Contacted", "status": "contacted", "count": funnel.get("contacted", 0), "expected_rate": 70},
        {"name": "Qualified", "status": "qualified", "count": funnel.get("qualified", 0), "expected_rate": 40},
        {"name": "Proposal", "status": "proposal", "count": funnel.get("proposal", 0), "expected_rate": 25},
        {"name": "Negotiation", "status": "negotiation", "count": funnel.get("negotiation", 0), "expected_rate": 15},
        {"name": "Won", "status": "won", "count": funnel.get("won", 0), "expected_rate": 8}
    ]
    
    # Calculate actual rates and drop-offs
    for i, stage in enumerate(stages):
        stage["actual_rate"] = round(stage["count"] / total_leads * 100, 1)
        stage["vs_expected"] = round(stage["actual_rate"] - stage["expected_rate"], 1)
        
        if i > 0:
            prev_count = stages[i-1]["count"] or 1
            stage["stage_conversion"] = round(stage["count"] / prev_count * 100, 1)
            stage["drop_off"] = round((1 - stage["count"] / prev_count) * 100, 1)
        else:
            stage["stage_conversion"] = 100
            stage["drop_off"] = 0
    
    # Find bottleneck
    bottleneck = max(stages[1:], key=lambda x: x["drop_off"])
    
    # Segment analysis if specified
    segment_data = None
    if segment:
        segment_leads = [l for l in DATA.leads.values() if l.get("source") == segment or l.get("temperature") == segment]
        if segment_leads:
            segment_data = {
                "segment": segment,
                "total_leads": len(segment_leads),
                "qualified": len([l for l in segment_leads if l.get("status") == "qualified"]),
                "converted": len([l for l in segment_leads if l.get("status") == "won"]),
                "avg_score": sum(l.get("score", 0) for l in segment_leads) / len(segment_leads)
            }
    
    # Calculate velocity
    converted_leads = [l for l in DATA.leads.values() if l.get("status") == "won"]
    velocities = []
    for lead in converted_leads:
        try:
            created = datetime.fromisoformat(lead.get("created_at", ""))
            converted = datetime.fromisoformat(lead.get("conversion_data", {}).get("converted_at", ""))
            velocities.append((converted - created).total_seconds() / 3600)
        except:
            pass
    
    avg_velocity = sum(velocities) / len(velocities) if velocities else None
    
    return {
        "period": period,
        "period_days": days,
        "total_leads": total_leads,
        "funnel_stages": stages,
        "bottleneck": {
            "stage": bottleneck["name"],
            "drop_off_rate": f"{bottleneck['drop_off']}%",
            "recommendation": f"Focus on improving {bottleneck['name']} stage conversion"
        },
        "overall_conversion_rate": f"{stages[-1]['actual_rate']}%",
        "vs_expected": f"{stages[-1]['vs_expected']:+.1f}%",
        "avg_velocity_hours": round(avg_velocity, 1) if avg_velocity else None,
        "segment_analysis": segment_data,
        "health_score": min(100, int(stages[-1]["actual_rate"] / stages[-1]["expected_rate"] * 100)),
        "recommendations": [
            f"Reduce drop-off at {bottleneck['name']} stage",
            "Improve lead qualification process" if stages[2]["vs_expected"] < 0 else "Qualification performing well",
            "Speed up response time" if avg_velocity and avg_velocity > 48 else "Good response velocity"
        ],
        "analyzed_at": datetime.now().isoformat()
    }

# === FUNCTION 10: GENERATE_LEAD_REPORT ===
async def generate_lead_report(period: str = "week", include_details: bool = True) -> Dict[str, Any]:
    """Полный отчет по лидам с метриками и рекомендациями"""
    
    period_days = {"day": 1, "week": 7, "month": 30, "quarter": 90}
    days = period_days.get(period, 7)
    
    m = DATA.metrics
    total = m.get("total_leads", 0) or 1
    qualified = m.get("qualified_leads", 0)
    converted = m.get("converted", 0)
    revenue = m.get("revenue", 0)
    
    report = {
        "period": period,
        "period_days": days,
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_leads": total,
            "qualified_leads": qualified,
            "converted_leads": converted,
            "total_revenue": round(revenue, 2),
            "qualification_rate": round(qualified / total * 100, 1),
            "conversion_rate": round(converted / total * 100, 1),
            "avg_lead_score": round(m.get("avg_score", 0), 1),
            "avg_deal_value": round(revenue / max(converted, 1), 2)
        }
    }
    
    # By source breakdown
    report["by_source"] = {}
    for source, stats in DATA.sources_stats.items():
        if stats["total"] > 0:
            report["by_source"][source] = {
                "leads": stats["total"],
                "qualified": stats["qualified"],
                "converted": stats["converted"],
                "revenue": stats["revenue"],
                "conversion_rate": round(stats["converted"] / max(stats["total"], 1) * 100, 1),
                "quality_score": CONFIG.source_quality_scores.get(source, 50)
            }
    
    # Temperature distribution
    all_leads = list(DATA.leads.values())
    report["by_temperature"] = {
        "hot": len([l for l in all_leads if l.get("temperature") == "hot"]),
        "warm": len([l for l in all_leads if l.get("temperature") == "warm"]),
        "cold": len([l for l in all_leads if l.get("temperature") == "cold"])
    }
    
    # Trends (simulated for demo)
    report["trends"] = {
        "leads_growth": "+12%",
        "qualification_rate_trend": "+5%",
        "conversion_rate_trend": "+3%",
        "avg_score_trend": "+8 points"
    }
    
    if include_details:
        # Top leads
        hot_leads = sorted([l for l in all_leads if l.get("temperature") == "hot"], key=lambda x: x.get("score", 0), reverse=True)
        report["hot_leads"] = [{
            "lead_id": l.get("lead_id"),
            "score": l.get("score"),
            "source": l.get("source"),
            "status": l.get("status"),
            "created_at": l.get("created_at")
        } for l in hot_leads[:10]]
        
        # Best performing source
        best_source = max(report["by_source"].items(), key=lambda x: x[1]["conversion_rate"]) if report["by_source"] else None
        
        # Recommendations
        report["recommendations"] = [
            {"priority": "high", "action": f"Increase budget on {best_source[0]}" if best_source else "Diversify lead sources", "expected_impact": "+15% leads"},
            {"priority": "medium", "action": "Improve qualification process", "expected_impact": "+10% conversion"},
            {"priority": "medium", "action": "Speed up response time to < 5 min", "expected_impact": "+20% qualification"},
            {"priority": "low", "action": "Implement lead scoring automation", "expected_impact": "+5% efficiency"}
        ]
        
        # Campaigns performance
        if DATA.campaigns:
            report["campaigns"] = [{
                "campaign_id": c["campaign_id"],
                "source": c["source"],
                "leads": c["leads_captured"],
                "conversions": c["leads_converted"],
                "roi": round((c["revenue"] - c["spend"]) / max(c["spend"], 1) * 100, 1) if c["spend"] > 0 else 0
            } for c in DATA.campaigns.values()]
    
    return report

# === DEMO FUNCTION ===
async def demo_lead_generation():
    """Демонстрация работы Lead Generation Agent"""
    print("\n" + "="*60)
    print("ДЕМО: LEAD GENERATION AGENT - Party Pattaya Bot v10.2.1")
    print("="*60)
    
    print("\n1. Захват лида...")
    lead = await capture_lead(
        source="telegram",
        contact_info={"telegram": "@test_user", "name": "Иван"},
        initial_message="Хочу арендовать яхту на 15 человек",
        utm_params={"campaign": "summer_2025", "medium": "social"}
    )
    print(f"   Lead ID: {lead['lead_id']}")
    print(f"   Score: {lead['initial_score']}, Temp: {lead['temperature']}")
    
    print("\n2. Квалификация лида...")
    qual = await qualify_lead(lead["lead_id"], {
        "budget": 2000,
        "has_authority": True,
        "need_level": "high",
        "timeline": "this_week",
        "group_size": 15,
        "service_interest": ["yacht_premium"]
    })
    print(f"   Score: {qual['total_score']}, Level: {qual['qualification_level']}")
    
    print("\n3. Скоринг лида...")
    score = await score_lead(lead["lead_id"], {"is_repeat_customer": False})
    print(f"   Normalized Score: {score['total_score']}, Temp: {score['temperature']}")
    
    print("\n4. Назначение агенту...")
    assign = await assign_lead(lead["lead_id"])
    print(f"   Agent: {assign.get('agent_name', 'N/A')}, Priority: {assign.get('priority', 'N/A')}")
    
    print("\n5. Анализ воронки...")
    funnel = await analyze_lead_funnel(period="week")
    print(f"   Conversion: {funnel['overall_conversion_rate']}")
    print(f"   Bottleneck: {funnel['bottleneck']['stage']}")
    
    print("\n6. Генерация отчета...")
    report = await generate_lead_report(period="week")
    print(f"   Total Leads: {report['summary']['total_leads']}")
    print(f"   Qualified: {report['summary']['qualified_leads']}")
    
    print("\n" + "="*60)
    print("ДЕМО ЗАВЕРШЕНО")
    print("="*60)

# === MAIN ===
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   БЛОК 15: LEAD GENERATION AGENT - FULL                      ║
║                      Party Pattaya Bot v10.2.1                               ║
║                                                                              ║
║  Функций: 10 ПОЛНЫХ | Автор: Сергей Леонов | Дата: 26.11.2025               ║
║  Статус: ✅ ГОТОВ - изменения запрещены без разрешения                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        asyncio.run(demo_lead_generation())
    else:
        print("Команды:")
        print("  python block_15_lead_generation.py demo  - Запустить демо")
        print("\nИмпорт:")
        print("  from block_15_lead_generation import *")
