# 📌 Minimal Task & Reminder Telegram Bot

A fast, intelligent, and minimalist personal productivity assistant built for **Telegram**. Manages daily tasks, automatically splits multi-task sentences, and delivers instant push notification alerts at the exact scheduled local time.

---

## ⚡ Key Features

- 💬 **Natural Language Input**: Simply text your bot naturally (*"Buy groceries today at 8 PM"* or *"Call client in 30 minutes"*).
- 🔀 **Multi-Task Auto-Splitting**: Automatically splits inputs like *"Write book and draw diagrams"* into distinct, individual task records.
- ⏰ **Automated Push Alerts**: Background watchdog (`APScheduler`) checks tasks every 30 seconds and pushes reminder alerts directly to your Telegram chat.
- 📄 **Paginated Task List**: Clean task UI displaying 5 items per page with `[ ◀️ Prev ]` and `[ Next ▶️ ]` navigation buttons to prevent button clutter.
- 📊 **Task Stats Header**: `/tasks` header displays Total Tasks, Completed Tasks, and Pending Tasks.
- 🛡️ **Dual Database Support**: Seamlessly runs on **SQLite** (local development) and **PostgreSQL / Supabase** (cloud production).
- 🤖 **Offline Fallback Engine**: Built-in rule parser ensures your bot continues working 100% even if the AI API quota is exhausted.

---

## 🛠️ Tech Stack

- **Language & Framework**: Python 3.11+, `python-telegram-bot` (v22+)
- **NLU / AI Engine**: Google Gemini API (`google-genai` SDK) with Pydantic Structured Output
- **Database**: SQLite / PostgreSQL (SQLAlchemy ORM + `psycopg2-binary`)
- **Scheduler**: `APScheduler` (AsyncIOScheduler)

---

## 📁 Project Structure

```
BOT/
├── config.py              # Environment configuration (.env loader)
├── database.py            # Database models (User, Task, Reminder) & CRUD methods
├── ai_parser.py           # Gemini NLU parser & fallback rule engine
├── reminder_scheduler.py  # APScheduler watchdog for push notifications
├── bot.py                 # Telegram handlers (/start, /tasks, inline buttons)
├── main.py                # App entry point with async post_init lifecycle hook
├── requirements.txt       # Dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git exclusion rules (protects API keys & database)
└── README.md              # Project documentation
```

---

## 🤖 Bot Commands & Usage

| Command / Text | Description | Example |
| :--- | :--- | :--- |
| `/start` | Welcome guide & quick start tips | `/start` |
| `/tasks` | Displays open tasks, task stats & action buttons | `/tasks` |
| **Add Single Task** | Text task with time or date | *"Submit assignment tomorrow at 5 PM"* |
| **Add Multi Tasks** | Text multiple actions | *"Write book and draw diagrams"* |
| **Mark Complete** | Text completion phrase or tap `✅ Done` button | *"Done assignment"* |

---

## ⚡ Local Setup Guide

### 1. Clone the Repository
```bash
git clone https://github.com/Kruparth08/telegram-task-bot.git
cd telegram-task-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the project root directory (you can copy `.env.example`):

```env
# Telegram Bot Token from @BotFather
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ

# Gemini API Key from Google AI Studio (Optional - bot works offline without it)
GEMINI_API_KEY=your_gemini_api_key_here

# Database URL (SQLite for local dev, PostgreSQL for production)
DATABASE_URL=sqlite:///taskbot.db
```

### 4. Run the Bot
```bash
python main.py
```

---

## 🌐 Free 24/7 Deployment Guide

To keep your bot running **24/7 online** without leaving your computer on:

1. **Database**: Create a free PostgreSQL database on [Supabase](https://supabase.com) and copy the URI string into `DATABASE_URL`.
2. **Hosting**: Deploy for free on **Koyeb.com**, **PythonAnywhere.com**, or **Render.com** (as a Web Service):
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
3. Add your `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, and `DATABASE_URL` under Environment Variables.

---

## 📄 License
This project is licensed under the MIT License.
