"""书籍信息查询服务 - 优先豆瓣，备用 Google Books"""

import logging
import re

import httpx

logger = logging.getLogger(__name__)


DOUBAN_SUGGEST = "https://book.douban.com/j/subject_suggest"
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


# 进程内缓存：同一书名不重复请求外部 API（重启失效）
_search_cache: dict[str, dict] = {}


async def search(query: str) -> dict | None:
    """
    根据书名搜索书籍，返回最匹配的结果。
    优先豆瓣（中文书覆盖好），豆瓣失败时回退 Google Books。
    返回格式：{"title", "author", "description", "cover_url", "isbn", "categories"}
    """
    normalized_query = " ".join(query.split())
    cache_key = normalized_query.casefold()
    # 豆瓣建议接口不支持复合查询（带空格会返回空），只用第一个词（书名）
    simple_query = normalized_query.split()[0] if " " in normalized_query else normalized_query
    # 命中缓存直接返回
    if cache_key in _search_cache:
        return _search_cache[cache_key]
    result = await _search_douban(simple_query)
    if not result:
        result = await _search_google(normalized_query)
    # 只缓存命中结果，失败不缓存（避免临时失败被长期记住）
    if result:
        _search_cache[cache_key] = result
    return result


async def _search_douban(query: str) -> dict | None:
    """通过豆瓣搜索书籍"""
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
            # 搜索建议接口
            resp = await client.get(DOUBAN_SUGGEST, params={"q": query})
            if resp.status_code != 200:
                return None

            items = resp.json()
            if not items or not isinstance(items, list):
                return None

            # 取第一个书籍结果
            item = None
            for i in items:
                if i.get("type") == "b":
                    item = i
                    break
            if not item:
                return None

            title = item.get("title", "")
            author = item.get("author_name", "")
            cover_url = item.get("pic", "")
            douban_id = item.get("id", "")

            # 尝试从详情页获取简介
            description = ""
            if douban_id:
                try:
                    detail_resp = await client.get(
                        f"https://book.douban.com/subject/{douban_id}/",
                        follow_redirects=True,
                    )
                    if detail_resp.status_code == 200:
                        html = detail_resp.text
                        # 从 og:description 提取简介
                        m = re.search(
                            r'<meta\s+property="og:description"\s+content="([^"]+)"',
                            html,
                        )
                        if m:
                            description = m.group(1)
                        # 从 og:image 获取更清晰的封面
                        m2 = re.search(
                            r'<meta\s+property="og:image"\s+content="([^"]+)"',
                            html,
                        )
                        if m2:
                            cover_url = m2.group(1)
                except Exception as e:
                    logger.warning("豆瓣详情页解析失败（id=%s）: %s", douban_id, e)

            return {
                "title": title,
                "author": author,
                "description": description,
                "cover_url": cover_url,
                "isbn": "",
                "categories": "",
            }
    except Exception as e:
        logger.warning("豆瓣搜索失败（query=%s）: %s", query, e)
        return None


async def _search_google(query: str) -> dict | None:
    """通过 Google Books 搜索书籍（备用）"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                GOOGLE_BOOKS_API, params={"q": query, "maxResults": 1}
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            items = data.get("items", [])
            if not items:
                return None

            info = items[0].get("volumeInfo", {})

            images = info.get("imageLinks", {})
            cover_url = (
                images.get("extraLarge")
                or images.get("large")
                or images.get("medium")
                or images.get("small")
                or images.get("thumbnail")
                or ""
            )
            if cover_url.startswith("http://"):
                cover_url = "https://" + cover_url[7:]

            isbn = ""
            for ident in info.get("industryIdentifiers", []):
                if ident.get("type") in ("ISBN_13", "ISBN_10"):
                    isbn = ident.get("identifier", "")
                    break

            categories = ", ".join(info.get("categories", []))

            return {
                "title": info.get("title", ""),
                "author": ", ".join(info.get("authors", [])),
                "description": info.get("description", ""),
                "cover_url": cover_url,
                "isbn": isbn,
                "categories": categories,
            }
    except Exception as e:
        logger.warning("Google Books 搜索失败（query=%s）: %s", query, e)
        return None
