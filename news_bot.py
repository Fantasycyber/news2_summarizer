#!/usr/bin/env python3
"""
🌍 Daily World News Bot
ดึงข่าวสำคัญ 24 ชั่วโมง → สรุปด้วย Gemini → ส่ง Telegram
"""

import os
import json
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GEMINI_API_KEY   = os.environ["GEMINI_API_KEY"]
TELEGRAM_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
NEWS_API_KEY     = os.environ.get("NEWS_API_KEY", "")  # optional แต่แนะนำ

GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
GEMINI_URL   = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# หมวดข่าวที่ต้องการ
NEWS_CATEGORIES = [
    {"label": "🌍 ข่าวโลก",          "q": "world news today",           "category": "general"},
    {"label": "💰 เศรษฐกิจ/การเงิน", "q": "economy finance markets",    "category": "business"},
    {"label": "🤖 เทคโนโลยี/AI",     "q": "technology AI innovation",   "category": "technology"},
]

# ─── FETCH NEWS ───────────────────────────────────────────────────────────────
def fetch_news_newsapi(query: str, category: str, hours: int = 24) -> list[dict]:
    """ดึงข่าวจาก NewsAPI.org"""
    if not NEWS_API_KEY:
        return []

    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "from": since,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 10,
        "apiKey": NEWS_API_KEY,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        articles = r.json().get("articles", [])
        return [
            {
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "source": a.get("source", {}).get("name", ""),
                "url": a.get("url", ""),
            }
            for a in articles if a.get("title") and "[Removed]" not in a.get("title", "")
        ]
    except Exception as e:
        print(f"⚠️  NewsAPI error ({query}): {e}")
        return []


def fetch_news_gnews(query: str, hours: int = 24) -> list[dict]:
    """ดึงข่าวจาก GNews (free tier, ไม่ต้องใช้ key สำหรับ RSS)"""
    # ใช้ RSS feed จาก Google News แทน (ไม่ต้อง key)
    rss_queries = {
        "world news today":        "https://news.google.com/rss/headlines/section/topic/WORLD",
        "economy finance markets": "https://news.google.com/rss/headlines/section/topic/BUSINESS",
        "technology AI innovation":"https://news.google.com/rss/headlines/section/topic/TECHNOLOGY",
    }
    url = rss_queries.get(query, "https://news.google.com/rss")

    try:
        import xml.etree.ElementTree as ET
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        root = ET.fromstring(r.content)
        items = root.findall(".//item")[:10]
        articles = []
        for item in items:
            title = item.findtext("title", "").strip()
            desc  = item.findtext("description", "").strip()
            link  = item.findtext("link", "").strip()
            source_el = item.find("source")
            source = source_el.text if source_el is not None else ""
            if title:
                articles.append({"title": title, "description": desc, "source": source, "url": link})
        return articles
    except Exception as e:
        print(f"⚠️  GNews RSS error ({query}): {e}")
        return []


def get_news_for_category(q: str, category: str) -> list[dict]:
    """ดึงข่าว — ลอง NewsAPI ก่อน fallback ไป Google News RSS"""
    articles = fetch_news_newsapi(q, category)
    if not articles:
        articles = fetch_news_gnews(q)
    return articles[:8]


# ─── SUMMARIZE WITH GEMINI ────────────────────────────────────────────────────
def summarize_with_gemini(all_news: dict) -> str:
    """ส่งข่าวทุกหมวดให้ Gemini สรุปเป็นภาษาไทย"""

    today = datetime.now(timezone(timedelta(hours=7))).strftime("%d %B %Y")

    # สร้าง prompt
    news_text = ""
    for label, articles in all_news.items():
        news_text += f"\n\n=== {label} ===\n"
        for i, a in enumerate(articles, 1):
            news_text += f"{i}. {a['title']}"
            if a.get("description"):
                news_text += f"\n   {a['description'][:200]}"
            news_text += f"\n   (แหล่งข่าว: {a.get('source','?')})\n"

    prompt = f"""คุณคือผู้สรุปข่าวภาษาไทยมืออาชีพ

วันที่: {today}

ด้านล่างคือพาดหัวข่าวและรายละเอียดสั้นๆ จากแหล่งข่าวต่างๆ ในช่วง 24 ชั่วโมงที่ผ่านมา:
{news_text}

กรุณาสรุปข่าวสำคัญเป็นภาษาไทย โดย:
1. แบ่งเป็น 3 หมวด: 🌍 ข่าวโลก | 💰 เศรษฐกิจ/การเงิน | 🤖 เทคโนโลยี/AI
2. แต่ละหมวดมี 3-5 ประเด็นสำคัญ
3. แต่ละประเด็นอธิบาย 2-3 ประโยค กระชับ เข้าใจง่าย
4. ใช้ bullet point (•)
5. ท้ายสุดมี "💡 บทสรุป" 2-3 ประโยคว่าวันนี้โลกเกิดอะไรที่น่าสนใจ

ห้ามใช้ภาษาอังกฤษ ยกเว้นชื่อเฉพาะที่แปลแล้วจะไม่สื่อความหมาย
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 2048,
        }
    }

    try:
        r = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}\nResponse: {r.text if 'r' in dir() else 'N/A'}")


# ─── SEND TELEGRAM ────────────────────────────────────────────────────────────
def send_telegram(text: str) -> None:
    """ส่งข้อความไป Telegram (แบ่งถ้ายาวเกิน 4096 ตัวอักษร)"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Telegram limit = 4096 chars
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    
    for i, chunk in enumerate(chunks):
        if i == 0:
            # Header เฉพาะชิ้นแรก
            now = datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M")
            header = f"📰 *สรุปข่าวโลก* | {now} น. (GMT+7)\n{'─'*30}\n\n"
            chunk = header + chunk

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "disable_web_page_preview": True,
        }
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()
        print(f"✅ Telegram chunk {i+1}/{len(chunks)} sent")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print(f"🚀 Starting news bot — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. ดึงข่าวทุกหมวด
    all_news = {}
    for cat in NEWS_CATEGORIES:
        print(f"📡 Fetching: {cat['label']} ...")
        articles = get_news_for_category(cat["q"], cat["category"])
        all_news[cat["label"]] = articles
        print(f"   → ได้ {len(articles)} บทความ")

    total = sum(len(v) for v in all_news.values())
    if total == 0:
        raise RuntimeError("❌ ไม่สามารถดึงข่าวได้เลย — ตรวจสอบ API keys")

    # 2. สรุปด้วย Gemini
    print("🤖 กำลังสรุปด้วย Gemini...")
    summary = summarize_with_gemini(all_news)
    print("✅ Gemini สรุปเสร็จแล้ว")
    print("─" * 50)
    print(summary[:500] + "...")

    # 3. ส่ง Telegram
    print("📤 กำลังส่ง Telegram...")
    send_telegram(summary)
    print("🎉 Done!")


if __name__ == "__main__":
    main()
