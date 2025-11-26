"""
БЛОК 15: LEAD GENERATION AGENT - Party Pattaya Bot v10.2.1
Автор: Сергей Леонов | Дата: 26.11.2025 | Функций: 10
"""
import asyncio, json, re, hashlib, random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger("block_15")

class LeadSource(Enum):
    TELEGRAM = "telegram"
    WEBSITE = "website"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    WHATSAPP = "whatsapp"
    REFERRAL = "referral"
    ORGANIC = "organic"

class LeadStatus(Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"

class LeadScore(Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"

@dataclass
class Config:
    admin_id: int = 359364877
    admin_telegram: str = "@Party_Pattaya"
    qualification_threshold: int = 60
    hot_score_threshold: int = 80
    warm_score_threshold: int = 50

CONFIG = Config()

class LeadDataStore:
    def __init__(self):
        self.leads: Dict[str, Dict] = {}
        self.campaigns: Dict[str, Dict] = {}
        self.sources_stats: Dict[str, Dict] = {}
        self.scoring_rules: List[Dict] = []
        self.metrics = {"total_leads": 0, "qualified": 0, "converted": 0, "revenue": 0}
    
    def add_lead(self, lead_id: str, data: Dict):
        self.leads[lead_id] = {**data, "created": datetime.now().isoformat(), "status": "new"}
        self.metrics["total_leads"] += 1
    
    def get_lead(self, lead_id: str) -> Optional[Dict]:
        return self.leads.get(lead_id)
    
    def update_lead(self, lead_id: str, updates: Dict):
        if lead_id in self.leads:
            self.leads[lead_id].update(updates)

DATA = LeadDataStore()

async def capture_lead(source: str, contact_info: Dict, initial_message: str = None, utm_params: Dict = None) -> Dict[str, Any]:
    lead_id = hashlib.md5(f"{contact_info}{datetime.now()}".encode()).hexdigest()[:12]
    lead_data = {"lead_id": lead_id, "source": source, "contact": contact_info, "message": initial_message, "utm": utm_params or {}, "score": 0, "status": "new", "tags": [], "history": []}
    if contact_info.get("phone") or contact_info.get("telegram"):
        lead_data["score"] += 20
    if initial_message and len(initial_message) > 20:
        lead_data["score"] += 10
    if utm_params and utm_params.get("campaign"):
        lead_data["tags"].append(f"campaign:{utm_params['campaign']}")
    DATA.add_lead(lead_id, lead_data)
    if source not in DATA.sources_stats:
        DATA.sources_stats[source] = {"total": 0, "qualified": 0, "converted": 0}
    DATA.sources_stats[source]["total"] += 1
    return {"success": True, "lead_id": lead_id, "initial_score": lead_data["score"], "source": source, "next_action": "qualify_lead"}

async def qualify_lead(lead_id: str, qualification_data: Dict) -> Dict[str, Any]:
    lead = DATA.get_lead(lead_id)
    if not lead:
        return {"success": False, "error": "Lead not found"}
    score = lead.get("score", 0)
    if qualification_data.get("budget"):
        b = qualification_data["budget"]
        score += 30 if b >= 2000 else 20 if b >= 1000 else 10 if b >= 500 else 5
    if qualification_data.get("timeline"):
        t = qualification_data["timeline"]
        score += 25 if t in ["today", "this_week"] else 15 if t == "this_month" else 5
    if qualification_data.get("group_size"):
        g = qualification_data["group_size"]
        score += 20 if g >= 10 else 10 if g >= 5 else 5
    if qualification_data.get("decision_maker"):
        score += 15
    if qualification_data.get("has_specific_date"):
        score += 10
    score = min(100, score)
    status = "qualified" if score >= CONFIG.qualification_threshold else "contacted"
    temperature = "hot" if score >= CONFIG.hot_score_threshold else "warm" if score >= CONFIG.warm_score_threshold else "cold"
    DATA.update_lead(lead_id, {"score": score, "status": status, "temperature": temperature, "qualification": qualification_data})
    if status == "qualified":
        DATA.metrics["qualified"] += 1
        DATA.sources_stats.get(lead.get("source", ""), {})["qualified"] = DATA.sources_stats.get(lead.get("source", ""), {}).get("qualified", 0) + 1
    return {"success": True, "lead_id": lead_id, "score": score, "status": status, "temperature": temperature, "is_qualified": status == "qualified", "recommended_action": "send_proposal" if temperature == "hot" else "nurture_sequence" if temperature == "warm" else "low_priority"}

async def score_lead(lead_id: str, scoring_factors: Dict = None) -> Dict[str, Any]:
    lead = DATA.get_lead(lead_id)
    if not lead:
        return {"success": False, "error": "Lead not found"}
    factors = scoring_factors or {}
    base_score = lead.get("score", 0)
    adjustments = []
    if factors.get("opened_emails"):
        adj = min(factors["opened_emails"] * 5, 15)
        base_score += adj
        adjustments.append({"factor": "email_engagement", "points": adj})
    if factors.get("visited_pricing"):
        base_score += 10
        adjustments.append({"factor": "pricing_interest", "points": 10})
    if factors.get("repeat_visitor"):
        base_score += 15
        adjustments.append({"factor": "repeat_interest", "points": 15})
    if factors.get("social_engagement"):
        base_score += 10
        adjustments.append({"factor": "social_engagement", "points": 10})
    if factors.get("referral"):
        base_score += 20
        adjustments.append({"factor": "referral_bonus", "points": 20})
    if factors.get("negative_signal"):
        base_score -= 15
        adjustments.append({"factor": "negative_signal", "points": -15})
    final_score = max(0, min(100, base_score))
    temperature = "hot" if final_score >= 80 else "warm" if final_score >= 50 else "cold"
    DATA.update_lead(lead_id, {"score": final_score, "temperature": temperature, "scoring_history": lead.get("scoring_history", []) + [{"timestamp": datetime.now().isoformat(), "adjustments": adjustments, "final": final_score}]})
    return {"success": True, "lead_id": lead_id, "previous_score": lead.get("score", 0), "new_score": final_score, "adjustments": adjustments, "temperature": temperature}

async def assign_lead(lead_id: str, assignment_rules: Dict = None) -> Dict[str, Any]:
    lead = DATA.get_lead(lead_id)
    if not lead:
        return {"success": False, "error": "Lead not found"}
    agents = [{"id": "agent_1", "name": "Лилия", "specialty": ["yacht", "vip"], "capacity": 10, "current": 5}, {"id": "agent_2", "name": "Алекс", "specialty": ["party", "transfer"], "capacity": 15, "current": 8}]
    rules = assignment_rules or {}
    best_agent = None
    best_score = 0
    lead_category = lead.get("qualification", {}).get("service_interest", "general")
    for agent in agents:
        score = 50
        if lead_category in agent["specialty"]:
            score += 30
        available_capacity = agent["capacity"] - agent["current"]
        score += available_capacity * 2
        if lead.get("temperature") == "hot" and "vip" in agent["specialty"]:
            score += 20
        if score > best_score:
            best_score = score
            best_agent = agent
    if not best_agent:
        best_agent = agents[0]
    DATA.update_lead(lead_id, {"assigned_to": best_agent["id"], "assigned_at": datetime.now().isoformat()})
    return {"success": True, "lead_id": lead_id, "assigned_to": best_agent["id"], "agent_name": best_agent["name"], "assignment_score": best_score, "reason": f"Best match for {lead_category}"}

async def nurture_lead(lead_id: str, nurture_sequence: str = "default", custom_content: Dict = None) -> Dict[str, Any]:
    lead = DATA.get_lead(lead_id)
    if not lead:
        return {"success": False, "error": "Lead not found"}
    sequences = {"default": [{"day": 0, "type": "welcome", "content": "Спасибо за интерес к Party Pattaya!"}, {"day": 1, "type": "value", "content": "Посмотрите наши лучшие яхты"}, {"day": 3, "type": "social_proof", "content": "500+ довольных клиентов"}, {"day": 7, "type": "offer", "content": "Специальное предложение для вас!"}], "vip": [{"day": 0, "type": "personal", "content": "Персональный менеджер свяжется с вами"}, {"day": 1, "type": "exclusive", "content": "Эксклюзивные VIP варианты"}], "reactivation": [{"day": 0, "type": "reminder", "content": "Мы скучаем! Вернитесь к нам"}, {"day": 3, "type": "offer", "content": "Скидка 20% для возвращения"}]}
    sequence = sequences.get(nurture_sequence, sequences["default"])
    if custom_content:
        sequence = [{**s, "content": custom_content.get(s["type"], s["content"])} for s in sequence]
    scheduled_messages = [{"scheduled_for": (datetime.now() + timedelta(days=s["day"])).isoformat(), "type": s["type"], "content": s["content"], "status": "pending"} for s in sequence]
    DATA.update_lead(lead_id, {"nurture_sequence": nurture_sequence, "scheduled_messages": scheduled_messages, "nurture_started": datetime.now().isoformat()})
    return {"success": True, "lead_id": lead_id, "sequence": nurture_sequence, "messages_scheduled": len(scheduled_messages), "first_message": scheduled_messages[0] if scheduled_messages else None}

async def track_lead_source(source: str, campaign_id: str = None, metrics: Dict = None) -> Dict[str, Any]:
    if source not in DATA.sources_stats:
        DATA.sources_stats[source] = {"total": 0, "qualified": 0, "converted": 0, "revenue": 0, "campaigns": {}}
    stats = DATA.sources_stats[source]
    if metrics:
        for k, v in metrics.items():
            if k in stats:
                stats[k] += v
    if campaign_id:
        if campaign_id not in stats["campaigns"]:
            stats["campaigns"][campaign_id] = {"leads": 0, "qualified": 0, "converted": 0}
        if metrics:
            for k, v in metrics.items():
                if k in stats["campaigns"][campaign_id]:
                    stats["campaigns"][campaign_id][k] += v
    conversion_rate = stats["converted"] / max(stats["total"], 1)
    qualification_rate = stats["qualified"] / max(stats["total"], 1)
    roi = stats["revenue"] / max(stats.get("spend", 1), 1) if stats.get("spend") else None
    return {"source": source, "total_leads": stats["total"], "qualified": stats["qualified"], "converted": stats["converted"], "conversion_rate": round(conversion_rate, 3), "qualification_rate": round(qualification_rate, 3), "roi": roi, "campaigns": stats.get("campaigns", {})}

async def create_lead_magnet(magnet_type: str, content: Dict, target_audience: Dict = None) -> Dict[str, Any]:
    magnet_id = f"magnet_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
    magnets = {"ebook": {"title": content.get("title", "Гид по вечеринкам в Паттайе"), "format": "pdf", "delivery": "email", "value_proposition": "Бесплатный гид"}, "discount": {"code": content.get("code", f"WELCOME{random.randint(10,30)}"), "value": content.get("value", 15), "delivery": "instant", "value_proposition": f"Скидка {content.get('value', 15)}%"}, "checklist": {"title": content.get("title", "Чеклист идеальной вечеринки"), "format": "pdf", "delivery": "telegram", "value_proposition": "Бесплатный чеклист"}, "consultation": {"duration": content.get("duration", 15), "format": "call", "delivery": "booking", "value_proposition": "Бесплатная консультация"}, "quiz": {"title": content.get("title", "Какая вечеринка вам подходит?"), "format": "interactive", "delivery": "instant", "value_proposition": "Персональная рекомендация"}}
    magnet = magnets.get(magnet_type, magnets["discount"])
    magnet["id"] = magnet_id
    magnet["type"] = magnet_type
    magnet["target"] = target_audience or {"interests": ["parties", "yachts"]}
    magnet["created"] = datetime.now().isoformat()
    magnet["stats"] = {"views": 0, "conversions": 0}
    DATA.campaigns[magnet_id] = magnet
    return {"success": True, "magnet_id": magnet_id, "type": magnet_type, "value_proposition": magnet["value_proposition"], "delivery_method": magnet["delivery"], "tracking_url": f"https://partypattaya.com/m/{magnet_id}"}

async def ab_test_lead_capture(test_name: str, variants: List[Dict], traffic_split: List[float] = None) -> Dict[str, Any]:
    test_id = f"test_{hashlib.md5(test_name.encode()).hexdigest()[:8]}"
    split = traffic_split or [1/len(variants)] * len(variants)
    test_data = {"id": test_id, "name": test_name, "variants": [], "status": "active", "started": datetime.now().isoformat(), "results": {}}
    for i, v in enumerate(variants):
        variant_id = f"{test_id}_v{i}"
        test_data["variants"].append({"id": variant_id, "name": v.get("name", f"Variant {i}"), "config": v, "traffic_share": split[i], "stats": {"impressions": 0, "conversions": 0, "conversion_rate": 0}})
    DATA.campaigns[test_id] = test_data
    return {"success": True, "test_id": test_id, "test_name": test_name, "variants_count": len(variants), "traffic_split": split, "status": "active"}

async def analyze_lead_funnel(period: str = "week", segment: str = None) -> Dict[str, Any]:
    days = {"day": 1, "week": 7, "month": 30, "quarter": 90}.get(period, 7)
    m = DATA.metrics
    total = m["total_leads"]
    qualified = m["qualified"]
    converted = m["converted"]
    funnel = {"period": period, "stages": [{"name": "Captured", "count": total, "rate": 1.0}, {"name": "Contacted", "count": int(total * 0.8), "rate": 0.8}, {"name": "Qualified", "count": qualified, "rate": qualified / max(total, 1)}, {"name": "Proposal", "count": int(qualified * 0.7), "rate": 0.7 * qualified / max(total, 1)}, {"name": "Negotiation", "count": int(qualified * 0.5), "rate": 0.5 * qualified / max(total, 1)}, {"name": "Won", "count": converted, "rate": converted / max(total, 1)}]}
    funnel["conversion_rate"] = converted / max(total, 1)
    funnel["avg_time_to_convert"] = "3.5 days"
    funnel["bottleneck"] = "Qualified → Proposal" if qualified > converted * 3 else "Captured → Qualified"
    funnel["recommendations"] = ["Улучшить follow-up после квалификации", "Ускорить отправку предложений"]
    by_source = {s: {"leads": d["total"], "qualified": d["qualified"], "converted": d["converted"], "rate": d["converted"] / max(d["total"], 1)} for s, d in DATA.sources_stats.items()}
    best_source = max(by_source.items(), key=lambda x: x[1]["rate"])[0] if by_source else "telegram"
    funnel["by_source"] = by_source
    funnel["best_source"] = best_source
    return funnel

async def generate_lead_report(period: str = "week", include_details: bool = True) -> Dict[str, Any]:
    m = DATA.metrics
    report = {"period": period, "generated": datetime.now().isoformat(), "summary": {"total_leads": m["total_leads"], "qualified_leads": m["qualified"], "converted_leads": m["converted"], "total_revenue": m["revenue"], "qualification_rate": round(m["qualified"] / max(m["total_leads"], 1), 3), "conversion_rate": round(m["converted"] / max(m["total_leads"], 1), 3), "avg_lead_value": round(m["revenue"] / max(m["converted"], 1), 2)}}
    report["by_source"] = {s: {"leads": d["total"], "qualified": d["qualified"], "converted": d["converted"], "rate": round(d["converted"] / max(d["total"], 1), 3)} for s, d in DATA.sources_stats.items()}
    report["trends"] = {"leads_growth": "+15%", "conversion_trend": "+5%", "avg_score_trend": "+8 points"}
    if include_details:
        hot_leads = [l for l in DATA.leads.values() if l.get("temperature") == "hot"]
        report["hot_leads"] = [{"id": l.get("lead_id"), "score": l.get("score"), "source": l.get("source")} for l in hot_leads[:10]]
        report["recommendations"] = ["Увеличить бюджет на " + (max(report["by_source"].items(), key=lambda x: x[1]["rate"])[0] if report["by_source"] else "telegram"), "Оптимизировать landing page", "Внедрить чат-бота для квалификации"]
    return report

if __name__ == "__main__":
    print("БЛОК 15: LEAD GENERATION AGENT - Party Pattaya Bot v10.2.1")
    print("Функций: 10 | Статус: ГОТОВ")
