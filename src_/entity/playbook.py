from typing import Dict
from dataclasses import dataclass
import json

@dataclass
class CompanyInfo:
    company_name: str
    company_website: str
    company_description: str
    official_overview: str
    product_overview: str
    stampli_differentiators: str
    ap_automation: str

    @classmethod
    def from_json(cls, path: str):
        with open(path, "r", encoding="utf-8") as f:
            company_data = json.load(f)

        company_name = company_data["Company Name"]["data"][0]["value"]
        company_website = company_data["Company Website"]["data"][0]["value"]
        company_description = company_data["Company Description"]["data"][0]["value"]
        official_overview = company_data["Official Overview "]["data"][0]["value"]
        product_overview = company_data["Product Overview"]["data"][0]["value"]
        stampli_differentiators = company_data["Stampli differentiators"]["data"][0]["value"]
        ap_automation = company_data["AP Automation"]["data"][0]["value"]
        
        return cls(company_name, company_website, company_description, official_overview,
                   product_overview, stampli_differentiators, ap_automation)

    def get_all_fields(self):
        return {
            "Company Name": self.company_name,
            "Company Website": self.company_website,
            "Company Description": self.company_description,
            "Official Overview": self.official_overview,
            "Product Overview": self.product_overview,
            "Stampli differentiators": self.stampli_differentiators,
            "AP Automation": self.ap_automation
        }

@dataclass
class TargetInfo:
    accounts: Dict[str, dict]
    personas: Dict[str, dict]
    industries: Dict[str, dict]
    healthcare_subverticals: Dict[str, dict]

    @classmethod
    def from_json(cls, path: str):
        with open(path, "r", encoding="utf-8") as f:
            target_data = json.load(f)

        accounts = target_data["Accounts"]
        personas = target_data["Personas"]
        industries = target_data["Industries"]
        healthcare_subverticals = target_data["Healthcare Subverticals"]
        
        return cls(accounts, personas, industries, healthcare_subverticals)

    def get_accounts(self):
        return self.accounts

    def get_personas(self):
        return self.personas

    def get_industries(self):
        return self.industries
    
    def get_healthcare_subverticals(self):
        return self.healthcare_subverticals

@dataclass
class Playbook:
    company_info: CompanyInfo
    target_info: TargetInfo

    @classmethod
    def load(cls, company_path: str, target_path: str):
        company_info = CompanyInfo.from_json(company_path)
        target_info = TargetInfo.from_json(target_path)
        return cls(company_info, target_info)

    def to_dict(self) -> dict:
        return {
            "company_info": self.company_info.get_all_fields(),
            "target_info": {
                "accounts": self.target_info.get_accounts(),
                "personas": self.target_info.get_personas(),
                "industries": self.target_info.get_industries(),
                "healthcare_subverticals": self.target_info.get_healthcare_subverticals()
            },
            "target_info_grouping": self.target_info_grouping()
        }

    def target_info_grouping(self) -> dict:
        """
        Group the target info by account, industry, persona, and healthcare subvertical.
        Only include relevant fields: 'text' and 'url' values.
        """
        grouped_info = {
            "accounts": {},
            "industries": {},
            "personas": {},
            "healthcare_subverticals": {}
        }

        # Group accounts: Only include URL and text values
        for account_name, account_data in self.target_info.get_accounts().items():
            account_values = {}
            for entry in account_data.get("data", []):
                if "value" in entry:
                    if entry["type"] == "url":
                        account_values["url"] = entry["value"]
                    elif entry["type"] == "text":
                        account_values["text"] = entry["value"]
            if account_values:  # Only include accounts with data
                grouped_info["accounts"][account_name] = account_values

        # Group industries: Only include URL and text values
        for industry_name, industry_data in self.target_info.get_industries().items():
            industry_values = {}
            for entry in industry_data.get("data", []):
                if "value" in entry:
                    if entry["type"] == "url":
                        industry_values["url"] = entry["value"]
                    elif entry["type"] == "text":
                        industry_values["text"] = entry["value"]
            if industry_values:  # Only include industries with data
                grouped_info["industries"][industry_name] = industry_values

        # Group personas: Only include URL and text values
        for persona_name, persona_data in self.target_info.get_personas().items():
            persona_values = {}
            for entry in persona_data.get("data", []):
                if "value" in entry:
                    if entry["type"] == "url":
                        persona_values["url"] = entry["value"]
                    elif entry["type"] == "text":
                        persona_values["text"] = entry["value"]
            if persona_values:  # Only include personas with data
                grouped_info["personas"][persona_name] = persona_values

        # Group healthcare subverticals: Only include URL and text values
        for subvertical_name, subvertical_data in self.target_info.get_healthcare_subverticals().items():
            subvertical_values = {}
            for entry in subvertical_data.get("data", []):
                if "value" in entry:
                    if entry["type"] == "url":
                        subvertical_values["url"] = entry["value"]
                    elif entry["type"] == "text":
                        subvertical_values["text"] = entry["value"]
            if subvertical_values:  # Only include healthcare subverticals with data
                grouped_info["healthcare_subverticals"][subvertical_name] = subvertical_values

        return grouped_info

# # Example usage
# playbook = Playbook.load("../../data/company_info.json", "../../data/target_info.json")
# print(playbook.to_dict())
