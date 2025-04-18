import json
from typing import Dict, List, Union

class PlaybookParser:
    def __init__(self, company_info_path: str, target_info_path: str):
        self.company_info_path = company_info_path
        self.target_info_path = target_info_path
        self.company_info_raw = self._load_json(company_info_path)
        self.target_info_raw = self._load_json(target_info_path)

    @staticmethod
    def _load_json(path: str) -> Dict:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def _extract_text_from_data(data_list: List[Dict[str, Union[str, None]]]) -> str:
        return " ".join([
            item["value"].strip()
            for item in data_list
            if item.get("type") in ("text", "url") and item.get("value", "").strip()
        ])

    def parse_company_info(self) -> str:
        """Flatten and format company_info fields as a readable string"""
        entries = []
        for field_name, field_data in self.company_info_raw.items():
            if field_name == "meta":
                continue
            data_list = field_data.get("data", [])
            if isinstance(data_list, list):
                values = self._extract_text_from_data(data_list)
                if values:
                    entries.append(f"{field_name.strip()}: {values}")
        return "\n".join(entries)

    def parse_targets(self) -> List[Dict[str, str]]:
        """Extract and flatten all targets (accounts, personas, industries, etc)"""
        results = []
        for target_type, targets in self.target_info_raw.items():
            if target_type == "meta":
                continue
            for target_name, target_data in targets.items():
                if target_name == "meta" or not isinstance(target_data, dict):
                    continue
                data_list = target_data.get("data", [])
                context = self._extract_text_from_data(data_list)
                if context:
                    results.append({
                        "target_type": target_type,
                        "name": target_name,
                        "context": context
                    })
        return results

    def get_structured(self) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        """Return structured format for easy downstream usage"""
        return {
            "company_info": self.parse_company_info(),
            "targets": self.parse_targets()
        }