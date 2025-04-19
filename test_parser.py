import os
from src.playbook_parser import PlaybookParser
if __name__ == "__main__":
    company_info_path = "data/company_info.json"
    target_info_path = "data/target_info.json"
    
    parser = PlaybookParser(company_info_path, target_info_path)
    
    # 保存解析后的数据到一个新的JSON文件
    output_path = "playbook_data.json"
    parser.save_to_json(output_path)
