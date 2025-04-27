
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
    {"placeholder": "hs_cos_wrapper_widget_1611686344563"},  # Main headline
    {"placeholder": "hs_cos_wrapper_banner"},                 # Banner paragraph
    {"placeholder": "hs_cos_wrapper_widget_1609866779313"}    # Subtitle
]


cache_data = cache.cache_data
company_info_from_cache = cache_data['company:'+playbook.company_info.company_name]
# print(f"[DEBUG] company_info_from_cache: {company_info_from_cache}")
company_info_text = company_info_from_cache.to_string()

# test with accounts only from the target.
for section_name, section_data in grouped_info.items():
    if section_name == 'accounts':
        for key, value_dict in section_data.items():
            cache_key = f"{section_name}:{key}"
            text = value_dict.get("text")
            url = value_dict.get("url", "")
            
            print(f"[DEBUG] text: {text}")
            print(f"[DEBUG] url: {url}")        
            
            # Prepare new entry basic info
            new_entry = FieldTemplate(
                text=text,
                url=url
            )

            cached_entry = cache_data.get(cache_key)

            if cached_entry:
                # If cache exists, compare URL
                if cached_entry.url == url and cached_entry.crawled_content and cached_entry.marketing_pitch:
                    print(f"[SKIP] {cache_key} - No changes detected, using cached data.")
                    continue
                else:
                    # --- Generate replacement content ---
                    if marketing_pitch:
                        replacement_content = generate_replacement_content(marketing_pitch, html_path, positions)
                        print(f"[DEBUG] replacement_content: {replacement_content}")
                        # --- Save replacements to output folder ---
                        output_path = f"output/{cache_key}.json"
                        with open(output_path, 'w') as f:
                            json.dump(replacement_content, f)

                    print(f"[UPDATE] {cache_key} - URL changed or missing crawled/marketing pitch, refreshing...")
            else:
                print(f"[NEW] {cache_key} - Not in cache, crawling and generating...")

            # --- Need to crawl new content ---
            crawled_content = None
            if url:
                crawled_content = url_content_crawler.crawl_content_from_url(url)

            # --- Need to generate new marketing pitch ---
            if crawled_content:
                try:
                    # print(f"[DEBUG] text: {text}")
                    # print(f"[DEBUG] crawled_content: {crawled_content}")
                    # print(f"[DEBUG] company_info_text: {company_info_text}")
                    marketing_pitch = generate_marketing_pitch(text, crawled_content, company_info_text)
                except Exception as e:
                    print(f"[ERROR] Failed to generate marketing pitch for {cache_key}: {str(e)}")
                    marketing_pitch = None
            else:
                marketing_pitch = None

            # --- Update new entry fields ---
            new_entry.crawled_content = crawled_content
            new_entry.marketing_pitch = marketing_pitch
            new_entry.last_updated = datetime.now().isoformat()

            # --- Save to cache ---
            cache_data[cache_key] = new_entry
            cache.save_cache()

            # --- Generate replacement content ---

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
                print(f"[DEBUG] replacement_content: {replacement_content}")
                # --- Save replacements to output folder ---
                output_path = f"output/{cache_key}.json"
                with open(output_path, 'w') as f:
                    json.dump(replacement_content, f)


