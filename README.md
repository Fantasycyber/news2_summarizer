# 📰 Daily World News Bot

สรุปข่าวโลก 24 ชั่วโมง ด้วย Gemini AI → ส่ง Telegram ทุกเช้า 7:30 น.

---

## ✅ สิ่งที่ต้องเตรียม

| สิ่ง | วิธีได้มา | ฟรีไหม? |
|------|----------|---------|
| **Gemini API Key** | [aistudio.google.com](https://aistudio.google.com) | ✅ ฟรี |
| **Telegram Bot Token** | คุยกับ @BotFather ใน Telegram | ✅ ฟรี |
| **Telegram Chat ID** | ดูขั้นตอนด้านล่าง | ✅ ฟรี |
| **NewsAPI Key** (optional) | [newsapi.org](https://newsapi.org) | ✅ ฟรี (500 req/วัน) |

> ⚠️ ถ้าไม่มี NewsAPI Key — bot จะใช้ Google News RSS แทน (ฟรี ไม่ต้อง key)

---

## 🚀 ขั้นตอนการ Setup

### 1. สร้าง Telegram Bot

1. เปิด Telegram → ค้นหา **@BotFather**
2. พิมพ์ `/newbot`
3. ตั้งชื่อ bot เช่น `MyNewsBot`
4. คัดลอก **Token** ที่ได้ เช่น `7123456789:AAF...`

### 2. หา Telegram Chat ID

**วิธีง่ายที่สุด:**
1. ส่งข้อความใด ๆ ให้ bot ของคุณ
2. เปิด URL นี้ในเบราว์เซอร์ (แทนที่ TOKEN):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. ดูค่า `"id"` ใต้ `"chat"` → นั่นคือ Chat ID ของคุณ

**ถ้าต้องการส่งไป Group:**
1. เพิ่ม bot เข้า group
2. ส่งข้อความใน group
3. เปิด URL เดิม → Chat ID จะเป็นตัวเลขติดลบ เช่น `-1001234567890`

### 3. สร้าง Gemini API Key

1. ไปที่ [aistudio.google.com](https://aistudio.google.com)
2. คลิก **"Get API Key"** → **"Create API key"**
3. คัดลอก key ที่ได้

### 4. Upload ขึ้น GitHub

```bash
# สร้าง repo ใหม่ใน GitHub แล้วรัน:
git init
git add .
git commit -m "Initial: Daily news bot"
git remote add origin https://github.com/USERNAME/daily-news-bot.git
git push -u origin main
```

### 5. ตั้งค่า Secrets ใน GitHub

ไปที่ **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | ค่าที่ใส่ |
|-------------|----------|
| `GEMINI_API_KEY` | Gemini API key |
| `TELEGRAM_BOT_TOKEN` | Token จาก BotFather |
| `TELEGRAM_CHAT_ID` | Chat ID ของคุณ |
| `NEWS_API_KEY` | (optional) NewsAPI key |

### 6. ทดสอบ

ไปที่ **Actions tab** → เลือก workflow **"📰 Daily News Bot"** → คลิก **"Run workflow"**

---

## ⏰ เวลาทำงาน

Bot จะรันอัตโนมัติทุกวันเวลา **7:30 น. (Bangkok, GMT+7)**

แก้ไขเวลาได้ที่ `.github/workflows/daily_news.yml`:
```yaml
# 7:30 AM Bangkok = 00:30 UTC
- cron: "30 0 * * *"
```

ตัวแปลงเวลา: Bangkok GMT+7 → ลบ 7 ชั่วโมง = UTC

---

## 📁 โครงสร้างไฟล์

```
daily-news-bot/
├── news_bot.py                    # สคริปต์หลัก
├── requirements.txt               # Python dependencies
├── README.md                      # ไฟล์นี้
└── .github/
    └── workflows/
        └── daily_news.yml         # GitHub Actions schedule
```

---

## 🛠️ ปรับแต่ง

**เปลี่ยนหมวดข่าว** → แก้ `NEWS_CATEGORIES` ใน `news_bot.py`

**เปลี่ยนภาษาสรุป** → แก้ prompt ใน `summarize_with_gemini()`

**เพิ่มช่องทางส่ง** → เพิ่ม function ส่ง LINE Notify ต่อจาก `send_telegram()`
