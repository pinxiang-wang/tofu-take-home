import os
from src.playbook_parser import PlaybookParser

def main():
    os.makedirs("logs", exist_ok=True)
    with open("logs/parser_output.log", "w", encoding="utf-8") as f:
        parser = PlaybookParser("data/company_info.json", "data/target_info.json")

        f.write("Company Info Summary:\n")
        f.write(parser.parse_company_info())
        f.write("\n\n")

        f.write("Target Info List:\n")
        for t in parser.parse_targets():
            f.write(f"- [{t['target_type']}] {t['name']}: {t['context']}\n")

    print("Parser output written to logs/parser_output.log")

if __name__ == "__main__":
    main()
