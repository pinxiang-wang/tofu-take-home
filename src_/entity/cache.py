from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
from typing import Dict, Optional
from src_.utils.gen_marketing_pitch import generate_marketing_pitch
from src_.entity.playbook import CompanyInfo
from src_.entity.field_template import FieldTemplate
from src_.utils.url_content_crawler import crawl_content_from_url

# this is a simple cache designed for this project only.
# It only supports single thread operation.

@dataclass
class Cache:
    cache_file: str = "cache.json"
    cache_data: Dict[str, FieldTemplate] = field(default_factory=dict)

    def __post_init__(self):
        self.cache_data = self.load_cache()

    def load_cache(self) -> Dict[str, FieldTemplate]:
        """
        Load the cache data from the file.
        If the cache file does not exist, return an empty dictionary.
        """
        try:
            with open(self.cache_file, "r") as file:
                raw_data = json.load(file)
                return {key: FieldTemplate(**value) for key, value in raw_data.items()}
        except FileNotFoundError:
            return {}

    def save_cache(self):
        """
        Save the cache data to the file.
        Converts the cache data into a dictionary format suitable for JSON serialization.
        """
        with open(self.cache_file, "w") as file:
            json.dump(
                {key: value.__dict__ for key, value in self.cache_data.items()},
                file,
                indent=4,
            )

    def check_field_update(self, key: str, new_text: str, new_url: str) -> bool:
        """
        Check if the field associated with the provided key needs to be updated.
        If there are changes in 'text' or 'url', it updates the cache and returns True.
        Otherwise, it returns False.
        """
        if key in self.cache_data:
            cached_data = self.cache_data[key]
            new_data = FieldTemplate(text=new_text, url=new_url)
            if cached_data.has_changed(new_data):
                # Update cache data if fields have changed
                self.cache_data[key] = FieldTemplate(
                    text=new_text, url=new_url, last_updated=datetime.now().isoformat()
                )
                self.save_cache()
                return True
            return False
        else:
            # If it's new data, directly store it in cache
            self.cache_data[key] = FieldTemplate(
                text=new_text, url=new_url, last_updated=datetime.now().isoformat()
            )
            self.save_cache()
            return True
    
    def get_cached_pitch(self, key: str) -> Optional[str]:
        """
        Get the cached marketing pitch for the given key.
        If no marketing pitch is found, it returns None.
        """
        return self.cache_data.get(key, {}).marketing_pitch

    def update_cached_pitch(self, key: str, marketing_pitch: str):
        """
        Update the cached marketing pitch for the given key.
        The marketing pitch is updated and saved back to the cache.
        """
        if key in self.cache_data:
            self.cache_data[key].marketing_pitch = marketing_pitch
            self.save_cache()
    
    
    def update_company_info(self, company_info: CompanyInfo):
        cache_key = f"company:{company_info.company_name}"
        
        # Build a new FieldTemplate with content storing the full company_info
        new_entry = FieldTemplate(
            text=company_info.company_description,
            url=company_info.company_website,
            content=asdict(company_info),  # Save the entire CompanyInfo object as a dict
            last_updated=datetime.now().isoformat()
        )

        if cache_key not in self.cache_data:
            print(f"[NEW] Adding {cache_key}")
            crawled_content = crawl_content_from_url(company_info.company_website)
            new_entry.crawled_content = crawled_content
            self.cache_data[cache_key] = new_entry
            
        else:
            cached_entry = self.cache_data[cache_key]
            if cached_entry.has_changed(new_entry, compare_content=True):
                print(f"[UPDATE] {cache_key} has changes")
                new_entry.marketing_pitch = cached_entry.marketing_pitch
                new_entry.crawled_content = cached_entry.crawled_content
                
                crawled_content = crawl_content_from_url(company_info.company_website)
                new_entry.crawled_content = crawled_content['data']
                self.cache_data[cache_key] = new_entry
            else:
                print(f"[SKIP] {cache_key} unchanged")

        self.save_cache()
        
    def update_cache_with_grouped_target_info(
        self, grouped_info: Dict[str, Dict[str, dict]]
    ):
        """
        Update the cache using grouped target information (accounts, personas, etc.).
        """
        # print(f"[CACHE] cache_key: {self.cache_data.keys()}")
        NEW_ENTRY_COUNT = 0
        UPDATED_ENTRY_COUNT = 0
        SKIPPED_ENTRY_COUNT = 0
        for section_name, section_data in grouped_info.items():
            for key, value_dict in section_data.items():
                cache_key = f"{section_name}:{key}"
                new_entry = FieldTemplate(
                    text=value_dict.get("text"), url=value_dict.get("url")
                )

                if cache_key not in self.cache_data.keys():
                    print(f"[NEW] Adding {cache_key}")
                    NEW_ENTRY_COUNT += 1
                    new_entry.last_updated = datetime.now().isoformat()
                    if value_dict.get("url") is not None and value_dict.get("url")!="":
                        crawled_content = crawl_content_from_url(value_dict.get("url"))
                        # marketing_pitch = generate_marketing_pitch(new_entry.text, crawled_content)
                        new_entry.crawled_content = crawled_content
                        # new_entry.marketing_pitch = marketing_pitch
                    self.cache_data[cache_key] = new_entry
                    
                else:
                    cached_entry = self.cache_data[cache_key]
                    if cached_entry.has_changed(new_entry):
                        print(f"[UPDATE] {cache_key} has changes")
                        UPDATED_ENTRY_COUNT += 1
                        new_entry.last_updated = datetime.now().isoformat()
                        # if the url has changed, we need to crawl the new url and generate a new marketing pitch
                        
                        if value_dict.get("url")!=cached_entry.url:
                            crawled_content = crawl_content_from_url(value_dict.get("url"))
                            new_entry.crawled_content = crawled_content
                            # marketing_pitch = generate_marketing_pitch(new_entry.text, crawled_content)
                            # new_entry.marketing_pitch = marketing_pitch
                        self.cache_data[cache_key] = new_entry
                    else:
                        print(f"[SKIP] {cache_key} unchanged")
                        SKIPPED_ENTRY_COUNT += 1
        self.save_cache()
        # print(f"[CACHE] Updated cache with {len(self.cache_data)} entries")
        print(f"[CACHE] New entries: {NEW_ENTRY_COUNT}")
        print(f"[CACHE] Updated entries: {UPDATED_ENTRY_COUNT}")
        print(f"[CACHE] Skipped entries: {SKIPPED_ENTRY_COUNT}")

    def clear_cache(self):
        """
        Clear all the cached data.
        Resets the cache and saves an empty cache to the file.
        """
        self.cache_data = {}
        self.save_cache()
