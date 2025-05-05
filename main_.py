from datetime import datetime
import json
import os
from src.marketing_content_gen_with_planner import generate_replacement_content
from src_.utils import url_content_crawler
from src_.utils.gen_customized_web_content import extract_tagged_content_from_html, generate_customized_web_content
from src_.utils.gen_marketing_pitch import generate_marketing_pitch
from src_.entity.playbook import Playbook
from src_.entity.cache import Cache
from src_.entity.field_template import FieldTemplate


company_info_path = 'data/company_info.json'
target_info_path = 'data/target_info.json'
cache_path = 'cache/cache.json'
html_path = 'data/landing_page.html'


playbook = Playbook.load(company_info_path, target_info_path)
if not os.path.exists('cache'):
    os.makedirs("cache", exist_ok=True)
# create cache if not exists, create the file first
if not os.path.exists(cache_path):
    with open(cache_path, 'w') as f:
        json.dump({}, f)
        
cache = Cache(cache_path)
grouped_info = playbook.target_info_grouping()
# cache.update_cache_with_grouped_target_info(grouping_info)
cache.update_company_info(playbook.company_info)
# Persist updated cache
# update cache with first 10 grouped info

# print(company_info)
cache.save_cache()

positions = [
    {"placeholder": "hs_cos_wrapper_banner"},   # Banner 
    {"placeholder": "hs_cos_wrapper_widget_1611686344563"},  # Main headline
    {"placeholder": "hs_cos_wrapper_widget_1609866779313"}    # Content paragraph
]


cache_data = cache.cache_data
company_info_from_cache = cache_data['company:'+playbook.company_info.company_name]
# print(f"[DEBUG] company_info_from_cache: {company_info_from_cache}")
company_info_text = company_info_from_cache.to_string()


for section_name, section_data in grouped_info.items():
    if section_name == 'accounts':
        for key, value_dict in section_data.items():
            cache_key = f"{section_name}:{key}"
            print(f"[DEBUG] cache_key: {cache_key}")
            text = value_dict.get("text")
            url = value_dict.get("url")
            cached_entry = FieldTemplate(
                text=text,
                url=url,
                crawled_content={},
                marketing_pitch=None,
                last_updated=None
            )
            target_audience = key
            need_crawled = False
            need_generate_marketing_pitch = False
            is_modified_cache = False
            # Case 1: Not in cache → Need everything
            if cache_key not in cache_data.keys():
                print(f"[NEW] {cache_key}")
                need_crawled = True
                need_generate_marketing_pitch = True
                
            # Case 2: Key in cache but changing detected in 'url' or 'text'
            else:
                cached_entry = cache_data[cache_key]
                # print first 100 characters of marketing_pitch
                print(f"[DEBUG] marketing_pitch: {cached_entry.marketing_pitch[:100]}")
                # print(f"[DEBUG] cached_entry: {cached_entry}")
                # print(f"[DEBUG] key that need update: {key}, url: {url}, text: {text}")
                if cached_entry.url != url:
                    print(f"[UPDATE] {cache_key}, Need Crawled and Generate new Pitch")
                    need_crawled = True
                    need_generate_marketing_pitch = True
                    is_modified_cache = True
                if not cached_entry.crawled_content:
                    need_crawled = True
                if cached_entry.text != text:
                    print(f"[UPDATE] {cache_key}, URL not changes, updated new Pitch")
                    need_generate_marketing_pitch = True
                    is_modified_cache = True
                if not cached_entry.marketing_pitch:
                    print(f"[UPDATE] {cache_key}, No Marketing Pitch, Need Generate new Pitch")
                    need_generate_marketing_pitch = True
                    is_modified_cache = True
            # Do crawling if needed
            if need_crawled:
                try: 
                    print(f"[DEBUG] {cache_key} is labeled as 'need_crawl', Crawling {url}")
                    crawled_content = url_content_crawler.crawl_content_from_url(url)
                    cached_entry.crawled_content = crawled_content
                    need_generate_marketing_pitch = True
                    is_modified_cache = True
                except Exception as e:
                    print(f"[ERROR] Failed to crawl {url}: {e}")
                    cached_entry.crawled_content = {}
            # Do pitch generation if needed 
            if need_generate_marketing_pitch:
                try:
                    marketing_pitch = generate_marketing_pitch(target_audience=target_audience, text=text, crawled_content=cached_entry.crawled_content, company_info=company_info_text)
                    cached_entry.marketing_pitch = marketing_pitch
                    is_modified_cache = True
                except Exception as e:
                    print(f"[ERROR] Failed to generate marketing pitch: {e}")
                    
            if is_modified_cache:
                cached_entry.last_updated = datetime.now().isoformat()
                cache_data[cache_key] = cached_entry
                cache.save_cache()
            print(f"[DEBUG] need_crawled: {need_crawled}, need_generate_marketing_pitch: {need_generate_marketing_pitch}, is_modified_cache: {is_modified_cache}")
            
                
# --- Generate replacement content ---
for section_name, section_data in grouped_info.items():
    if section_name == 'accounts':
        for key, value_dict in section_data.items():
            cache_key = f"{section_name}:{key}"
            text = value_dict.get("text")
            url = value_dict.get("url", "")
            marketing_pitch = cache_data.get(cache_key).marketing_pitch
            if marketing_pitch:
                # print(f"[DEBUG] marketing_pitch: {marketing_pitch}")
                # cache key: accounts:YMCA, target_audience: YMCA
                target_audience = cache_key.split(':')[1]
                extracted_positions = extract_tagged_content_from_html(positions=positions, html_file_path=html_path)
                replacement_content = generate_customized_web_content(target_audience=target_audience,marketing_pitch=marketing_pitch, positions= extracted_positions)
                # print(f"[DEBUG] replacement_content: {replacement_content}")
                # --- Save replacements to output folder ---
                output_path = f"output/{cache_key}.json"
                # check if the output directory exists, make directory if not    
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w') as f:
                    json.dump(replacement_content, f)      
                
                
                
