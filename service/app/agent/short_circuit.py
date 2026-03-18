from typing import List, Dict, Optional
from sqlalchemy.orm import Session

class ShortCircuitTool:
    def __init__(self, db: Session):
        self.db = db

    def check_perfect_match(self, scheme: Dict, retrieved_clothes: Dict[str, Optional]) -> bool:
        for item_name, item_info in scheme.get("items", {}).items():
            expected_color = item_info.get("color")
            clothes = retrieved_clothes.get(item_name)

            if not clothes:
                return False

            if expected_color and expected_color not in clothes.color and \
               not (clothes.description and expected_color in clothes.description):
                return False

        return True

    def find_perfect_scheme(self, schemes: List[Dict], all_retrieved: Dict[str, Dict]) -> Optional[Dict]:
        for scheme in schemes:
            retrieved = all_retrieved.get(scheme["scheme_id"], {})
            if self.check_perfect_match(scheme, retrieved):
                return scheme
        return None

    def calculate_match_score(self, scheme: Dict, retrieved_clothes: Dict[str, Optional]) -> float:
        if not retrieved_clothes:
            return 0.0

        matched_count = 0
        total_count = 0

        for item_name, item_info in scheme.get("items", {}).items():
            total_count += 1
            clothes = retrieved_clothes.get(item_name)

            if clothes:
                expected_color = item_info.get("color")
                if expected_color:
                    if expected_color in clothes.color or \
                       (clothes.description and expected_color in clothes.description):
                        matched_count += 1
                else:
                    matched_count += 1

        return (matched_count / total_count * 100) if total_count > 0 else 0.0