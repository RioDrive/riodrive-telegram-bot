import os
import re
import sqlite3
import requests
import base64
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL,
    category TEXT,
    date TEXT
)
""")
conn.commit()

def extract_text_from_image(image_bytes):
    api_key = os.getenv("VISION_API_KEY")

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"

    payload = {
        "requests": [
            {
                "image": {
                    "content": image_base64
                },
                "features": [
                    {"type": "TEXT_DETECTION"}
                ]
            }
        ]
    }

    response = requests.post(url, json=payload)
    result = response.json()

    if "responses" in result and "textAnnotations" in result["responses"][0]:
        return result["responses"][0]["textAnnotations"][0]["description"]

    return ""
import re

def extract_amount(text: str):
    import re

    # сначала пробуем найти сумму рядом со словом SUMA
    match = re.search(r"SUMA.*?(\d+[.,]\d{2})", text, re.IGNORECASE)
    if match:
        return match.group(1).replace(",", ".")

    # пробуем найти рядом с PLN
    match = re.search(r"(\d+[.,]\d{2})\s*PLN", text, re.IGNORECASE)
    if match:
        return match.group(1).replace(",", ".")

    # обычный поиск числа
    match = re.search(r"\d+[.,]\d{2}", text)
    if match:
        return match.group().replace(",", ".")

    return None
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Rio Drive – бот учёта расходов запущен.")
await update.message.reply_text(text)
async def month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    month_str = now.strftime("%Y-%m")
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (f"{month_str}%",))
    result = cursor.fetchone()[0]
    total = result if result else 0
    await update.message.reply_text(f"Расходы за {month_str}: {round(total,2)} zł")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()

    text = extract_text_from_image(image_bytes)
    amount = extract_amount(text)

    if amount:
        now = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO expenses (amount, category, date) VALUES (?, ?, ?)",
            (amount, "не указана", now)
        )
        conn.commit()
        await update.message.reply_text(f"Добавлено: {amount} zł")
    else:
        await update.message.reply_text("Не удалось распознать сумму.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("month", month))

app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.run_polling()
