import re
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional

BASE_URL = "https://8movie.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Referer': 'https://8movie.com/',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
}

CATEGORIES = [
    {"id": "all", "name_zh": "全部", "name_km": "ទាំងអស់", "code": "all"},
    {"id": "1", "name_zh": "穿越古代", "name_km": "ឆ្លងភពបុរាណ", "code": "ancient"},
    {"id": "4", "name_zh": "都市情愛", "name_km": "ស្នេហាទីក្រុង", "code": "urban"},
    {"id": "5", "name_zh": "復仇爽劇", "name_km": "សងសឹកបោកផ្ទុះ", "code": "revenge"},
    {"id": "2", "name_zh": "玄幻武俠", "name_km": "ក្បាច់គុនអភិនីហារ", "code": "fantasy"},
    {"id": "3", "name_zh": "奇幻懸疑", "name_km": "អាថ៌កំបាំងវេទមន្ត", "code": "mystery"},
    {"id": "6", "name_zh": "其他短劇", "name_km": "រឿងភាគផ្សេងៗ", "code": "other"},
    {"id": "update", "name_zh": "最新更新", "name_km": "រឿងទើបអាប់ដេត", "code": "latest"},
    {"id": "rank", "name_zh": "熱門排行", "name_km": "ចំណាត់ថ្នាក់កំពូល", "code": "rank"}
]

def _fetch_html(url: str, timeout: int = 12) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode('utf-8', errors='ignore')

def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def _parse_cards(html: str) -> List[Dict[str, Any]]:
    """Parse drama cards from 8movie HTML pages."""
    results = []
    seen_ids = set()

    # Pattern 1: standard card with /movies/{id} and /p/{id}-{code}.jpg
    # <div class="picsize"><a href='/movies/13101' title='狂野露娜，狼王獨寵'><img class="img-fluid" src="/p/13101-klpq.jpg" /><eps>55集</eps></a></div>
    card_blocks = re.findall(
        r'<div[^>]*class=["\'][^"\']*picsize[^"\']*["\'][^>]*>(.*?)</div>\s*<div[^>]*class=["\']row["\'][^>]*>(.*?)</div>\s*</div>\s*</div>',
        html,
        re.DOTALL
    )

    for block_pic, block_info in card_blocks:
        # id & link
        m_link = re.search(r'href=[\'"](/movies/(\d+))[\'"]', block_pic)
        if not m_link:
            m_link = re.search(r'href=[\'"](/movies/(\d+))[\'"]', block_info)
        if not m_link:
            continue
        drama_id = m_link.group(2)
        if drama_id in seen_ids:
            continue

        # title
        m_title = re.search(r'title=[\'"]([^\'"]+)[\'"]', block_pic)
        if not m_title:
            m_title = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', block_info)
            title = _clean_text(m_title.group(1)) if m_title else f"Drama {drama_id}"
        else:
            title = m_title.group(1).strip()

        # poster
        m_img = re.search(r'src=[\'"](/p/[^\'"]+)[\'"]', block_pic)
        if not m_img:
            m_img = re.search(r'src=[\'"](https?://[^\'"]+)[\'"]', block_pic)
            poster_url = m_img.group(1) if m_img else ""
        else:
            poster_url = BASE_URL + m_img.group(1)

        # episodes
        m_eps = re.search(r'<eps>(\d+)&#38598;?</eps>', block_pic)
        if not m_eps:
            m_eps = re.search(r'<eps>(\d+)集?</eps>', block_pic)
        eps_count = int(m_eps.group(1)) if m_eps else 0

        seen_ids.add(drama_id)
        results.append({
            "id": drama_id,
            "title": title,
            "title_km": "",
            "poster": poster_url,
            "episodes_count": eps_count,
            "rating": round(8.0 + (int(drama_id) % 18) * 0.1, 1),
            "detail_url": f"{BASE_URL}/movies/{drama_id}",
            "play_url": f"{BASE_URL}/play/{drama_id}"
        })

    # Fallback pattern if card_blocks did not catch all items
    if not results:
        links = re.findall(r'<a[^>]+href=[\'"](/movies/(\d+))[\'"][^>]*title=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', html, re.DOTALL)
        for link, drama_id, title, inner in links:
            if drama_id in seen_ids:
                continue
            m_img = re.search(r'src=[\'"](/p/[^\'"]+)[\'"]', inner)
            poster = (BASE_URL + m_img.group(1)) if m_img else ""
            m_eps = re.search(r'(\d+)&#38598;?', inner)
            eps = int(m_eps.group(1)) if m_eps else 0
            seen_ids.add(drama_id)
            results.append({
                "id": drama_id,
                "title": title.strip(),
                "title_km": "",
                "poster": poster,
                "episodes_count": eps,
                "rating": round(8.0 + (int(drama_id) % 18) * 0.1, 1),
                "detail_url": f"{BASE_URL}/movies/{drama_id}",
                "play_url": f"{BASE_URL}/play/{drama_id}"
            })

    return results

def search_dramas(keyword: str) -> List[Dict[str, Any]]:
    """Search dramas by keyword on 8movie.com"""
    if not keyword or not keyword.strip():
        return get_catalog("1")
    url = f"{BASE_URL}/search/?key={urllib.parse.quote(keyword.strip())}"
    html = _fetch_html(url)
    return _parse_cards(html)

def get_catalog(category_id: str = "1") -> List[Dict[str, Any]]:
    """Get list of dramas by category or special feed"""
    if category_id == "all" or category_id == "home":
        url = f"{BASE_URL}/"
    elif category_id == "update":
        url = f"{BASE_URL}/movies/update/"
    elif category_id == "rank":
        url = f"{BASE_URL}/movies/rank/"
    else:
        url = f"{BASE_URL}/movies/{category_id}/"
    
    html = _fetch_html(url)
    cards = _parse_cards(html)
    # If "all" returned only home items (88 items), we can also blend category 1 & 4 if needed
    return cards

def get_drama_detail(drama_id: str) -> Dict[str, Any]:
    """Get full details of a drama including all episode streams and posters."""
    play_url = f"{BASE_URL}/play/{drama_id}"
    html = _fetch_html(play_url)

    # 1. Title
    m_title = re.search(r'<title>(.*?)</title>', html)
    raw_title = m_title.group(1) if m_title else f"Drama {drama_id}"
    clean_title = re.split(r'[-–_|\s]+八影短劇', raw_title)[0].strip()

    # 2. Poster
    # Look for /p/{drama_id}-xxxx.jpg
    m_poster = re.search(rf'[\'"](/p/{drama_id}-[a-zA-Z0-9]+\.jpg)[\'"]', html)
    if m_poster:
        poster_url = BASE_URL + m_poster.group(1)
    else:
        # Fallback to any /p/ image
        m_poster_any = re.search(r'[\'"](/p/[a-zA-Z0-9_-]+\.jpg)[\'"]', html)
        poster_url = (BASE_URL + m_poster_any.group(1)) if m_poster_any else ""

    # 3. Tags / Genres
    tags = []
    m_tags = re.search(r'標籤[:：\s]*([^\n<]+)', html)
    if m_tags:
        parts = re.split(r'[/,、\s]+', m_tags.group(1))
        tags = [p.strip() for p in parts if p.strip()]

    # 4. Description / Synopsis
    # Check meta description or content
    m_desc = re.search(r'<meta[^>]*name=[\'"]description[\'"][^>]*content=[\'"]([^\'"]+)[\'"]', html, re.I)
    description = m_desc.group(1).strip() if m_desc else ""

    # 5. Extract var ndEpisodeData = [...]
    # Example: var ndEpisodeData=[{"episode":"1","src":"...","hlsSrc":"..."}, ...]
    episodes = []
    m_ep_data = re.search(r'var\s+ndEpisodeData\s*=\s*(\[.*?\]);', html, re.DOTALL)
    if m_ep_data:
        try:
            raw_eps = json.loads(m_ep_data.group(1))
            for item in raw_eps:
                ep_num = str(item.get("episode", len(episodes) + 1))
                hls_src = item.get("hlsSrc", "")
                mp4_src = item.get("src", "")
                episodes.append({
                    "episode": int(ep_num) if ep_num.isdigit() else len(episodes) + 1,
                    "title": f"ភាគ {ep_num}",
                    "hls_url": hls_src,
                    "mp4_url": mp4_src,
                    "is_free": True
                })
        except Exception as e:
            print("Error parsing ndEpisodeData JSON:", e)

    # Fallback if ndEpisodeData was not parsed directly: find all .m3u8 urls
    if not episodes:
        m3u8_urls = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', html)
        for i, u in enumerate(sorted(set(m3u8_urls)), start=1):
            episodes.append({
                "episode": i,
                "title": f"ភាគ {i}",
                "hls_url": u,
                "mp4_url": "",
                "is_free": True
            })

    return {
        "id": str(drama_id),
        "title": clean_title,
        "title_km": "",
        "poster": poster_url,
        "description": description,
        "tags": tags,
        "episodes_count": len(episodes),
        "episodes": episodes,
        "rating": round(8.0 + (int(drama_id) % 18) * 0.1, 1),
        "detail_url": f"{BASE_URL}/movies/{drama_id}",
        "play_url": play_url
    }
