import requests
from bs4 import BeautifulSoup

def fetch_webpage_with_html(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

    soup = BeautifulSoup(response.text, 'html.parser')

    title = soup.title.string.strip() if soup.title else ""
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and "content" in meta_tag.attrs:
        meta_desc = meta_tag["content"].strip()

    paragraphs = soup.find_all('p')
    main_text = "\n".join(p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 50)

    return {
        "success": True,
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "main_text": main_text[:2000],
        "raw_html": response.text
    }

# # 示例调用
# if __name__ == "__main__":
#     url = "https://www.ymca.org/"
#     result = fetch_webpage_with_html(url)
#     if result["success"]:
#         print("网页原始 HTML 内容（前1000字符）:\n")
#         print(result["raw_html"][:1000])  # 可改为更长或保存文件
#     else:
#         print("抓取失败:", result["error"])
