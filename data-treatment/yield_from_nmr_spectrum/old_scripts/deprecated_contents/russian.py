import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://www.imemo.ru"
LIST_URL = "https://www.imemo.ru/publications/policy-briefs"

KEYWORDS = [
    # "15-я пятилетняя программа",
    "план",
    # "15",
    # "15",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}
def get_article_links():
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    links = []

    for a in soup.select('a[href^="/publications/"]'):
        href = a.get("href")
        title = a.get_text(strip=True)

        # 过滤空标题和导航链接
        if href and title and len(title) > 10:
            links.append({
                "title": title,
                "url": BASE_URL + href
            })

    # 去重
    unique = {item["url"]: item for item in links}
    return list(unique.values())



def article_contains_keywords(article_url):
    """
    检查文章正文是否包含关键词
    """
    resp = requests.get(article_url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 获取正文文本
    content_block = soup.select_one("div.publication-content")
    if not content_block:
        return []

    text = content_block.get_text(separator=" ", strip=True)

    matched = [kw for kw in KEYWORDS if kw in text]
    return matched


def main():
    results = []
    articles = get_article_links()

    print(f"发现文章数量：{len(articles)}")

    for art in articles:
        time.sleep(1)  # 防止请求过快
        matched = article_contains_keywords(art["url"])
        if matched:
            results.append({
                "title": art["title"],
                "url": art["url"],
                "keywords": matched
            })
            print("命中：", art["title"])

    print("\n=== 最终结果 ===")
    for r in results:
        print(f"\n标题: {r['title']}")
        print(f"链接: {r['url']}")
        print(f"关键词: {', '.join(r['keywords'])}")


if __name__ == "__main__":
    main()
