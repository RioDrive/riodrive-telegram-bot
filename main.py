import os
import re
import sqlite3
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
    date TEXT
)
""")
conn.commit()

def extract_amount(text):
    matches = re.findall(r'\d+[.,]\d{2}', text)
    if matches:
        amounts = [float(m.replace(",", ".")) for m in matches]
        return max(amounts)
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Rio Drive – бот учёта расходов запущен.")

async def month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    month_str = now.strftime("%Y-%m")
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (f"{month_str}%",))
    result = cursor.fetchone()[0]
    total = result if result else 0
    await update.message.reply_text(f"Расходы за {month_str}: {round(total,2)} zł")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    amount = extract_amount(text)
    if amount:
        now = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO expenses (amount, date) VALUES (?, ?)", (amount, now))
        conn.commit()
        await update.message.reply_text(f"Добавлено: {amount} zł")
    else:
        await update.message.reply_text("Напиши сумму в формате 123.45")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("month", month))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

app.run_polling()
