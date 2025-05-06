
from src_.utils import url_content_crawler, url_content_crawler_with_html
from src_.utils.crawler_utils import fetch_webpage_with_html


url = "https://www.ymca.org/"
result = fetch_webpage_with_html(url)
raw_html = result["raw_html"]



result = url_content_crawler_with_html.crawl_content_from_url(url=url,raw_html=raw_html)
print(result)