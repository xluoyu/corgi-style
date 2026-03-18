from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.agent.plan_agent import PlanAgent
from app.agent.tools import RetrievalTool
from app.agent.short_circuit import ShortCircuitTool
from app.agent.combine_agent import CombineAgent
from app.models import OutfitRecord

class Supervisor:
    def __init__(self, db: Session):
        self.db = db
        self.plan_agent = PlanAgent(db)
        self.retrieval_tool = RetrievalTool(db)
        self.short_circuit_tool = ShortCircuitTool(db)
        self.combine_agent = CombineAgent(db)

    def generate_outfit(
        self,
        user_id: str,
        temperature: float,
        city: str,
        scene: str = "daily"
    ) -> Dict:
        schemes = self.plan_agent.generate_schemes(user_id, temperature, city, scene)

        all_retrieved = {}
        for scheme in schemes:
            retrieved = self.retrieval_tool.retrieve_by_scheme(user_id, scheme, temperature)
            all_retrieved[scheme["scheme_id"]] = retrieved

        perfect_scheme = self.short_circuit_tool.find_perfect_scheme(schemes, all_retrieved)

        if perfect_scheme:
            retrieved = all_retrieved[perfect_scheme["scheme_id"]]
            score = 100.0
        else:
            best_scheme = schemes[0]
            retrieved = all_retrieved[best_scheme["scheme_id"]]

            retrieved = self.combine_agent.combine_outfit(user_id, temperature, retrieved)

            score = self.short_circuit_tool.calculate_match_score(best_scheme, retrieved)
            perfect_scheme = best_scheme

        outfit_record = self._save_outfit_record(
            user_id=user_id,
            scheme_id=perfect_scheme["scheme_id"],
            temperature=temperature,
            city=city,
            retrieved=retrieved,
            scheme_description=perfect_scheme.get("description", ""),
            match_score=score
        )

        return {
            "outfit_id": outfit_record.id,
            "scheme_id": perfect_scheme["scheme_id"],
            "description": perfect_scheme.get("description", ""),
            "match_score": score,
            "temperature": temperature,
            "city": city,
            "scene": scene,
            "clothes": self._format_clothes_response(retrieved),
            "is_perfect_match": score >= 100.0
        }

    def _save_outfit_record(
        self,
        user_id: str,
        scheme_id: str,
        temperature: float,
        city: str,
        retrieved: Dict[str, Optional],
        scheme_description: str,
        match_score: float
    ) -> OutfitRecord:
        outfit = OutfitRecord(
            user_id=user_id,
            scheme_id=scheme_id,
            weather_temp=temperature,
            weather_city=city,
            top_clothes_id=retrieved.get("top").id if retrieved.get("top") else None,
            pants_clothes_id=retrieved.get("pants").id if retrieved.get("pants") else None,
            outer_clothes_id=retrieved.get("outer").id if retrieved.get("outer") else None,
            inner_clothes_id=retrieved.get("inner").id if retrieved.get("inner") else None,
            accessory_clothes_id=retrieved.get("accessory").id if retrieved.get("accessory") else None,
            scheme_description=scheme_description,
            match_score=match_score
        )
        self.db.add(outfit)
        self.db.commit()
        self.db.refresh(outfit)
        return outfit

    def _format_clothes_response(self, retrieved: Dict) -> List[Dict]:
        result = []
        for item_name, clothes in retrieved.items():
            if clothes:
                result.append({
                    "slot": item_name,
                    "clothes_id": clothes.id,
                    "image_url": clothes.image_url,
                    "category": clothes.category.value if hasattr(clothes.category, 'value') else clothes.category,
                    "color": clothes.color,
                    "description": clothes.description
                })
        return result