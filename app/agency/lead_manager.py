"""
AI Lead Qualification & Agency Client Manager
Captures inbound client leads, evaluates budget, scores fit, and creates automated proposals.
"""
from datetime import datetime
from typing import Dict, Any, List

class LeadManager:
    def __init__(self):
        self.leads: List[Dict[str, Any]] = []

    def process_lead(self, name: str, email: str, company: str, budget: str, service: str) -> Dict[str, Any]:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate lead score
        score = 80
        if "10,000" in budget or "5,000" in budget:
            score += 15
        elif "1,000" in budget:
            score += 5

        proposal_type = "Enterprise Custom Implementation" if score >= 90 else "Standard Agency Retainer Package"

        lead_record = {
            "id": f"LEAD-{len(self.leads) + 1:03d}",
            "name": name,
            "email": email,
            "company": company,
            "budget": budget,
            "service": service,
            "score": score,
            "tier": proposal_type,
            "received_at": now_str,
            "status": "QUALIFIED"
        }

        self.leads.insert(0, lead_record)
        if len(self.leads) > 30:
            self.leads = self.leads[:30]

        return lead_record

    def get_leads(self) -> List[Dict[str, Any]]:
        return self.leads
