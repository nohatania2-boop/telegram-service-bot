import os
import sqlite3
import threading
from flask import Flask, render_template_string, request, abort
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# --- সরাসরি এখানে আপনার তথ্যগুলো বসিয়ে দিন ---
TOKEN = "8862031612:AAFDDrCt6U8sH5t_bM2sMJkut1l672i6tZU"      # BotFather থেকে পাওয়া আপনার বটের টোকেন এখানে দিন
ADMIN_ID =8181168048             # আপনার টেলিগ্রাম ইউজার আইডি এখানে দিন (শুধু সংখ্যা)
ADMIN_SECRET = "my_secret_key"     # অ্যাডমিন প্যানেল সুরক্ষার জন্য একটি পাসওয়ার্ড দিন

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect("bot_database.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            balance REAL DEFAULT 0.0,
            holding REAL DEFAULT 0.0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            info TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect("bot_database.db", check_same_thread=False)

# --- Flask Web Server & Admin Panel ---
app = Flask(__name__)

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Panel - Telegram Bot</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h2 { color: #333; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #0088cc; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h2>👑 Admin Dashboard</h2>
        <h3>Total Users: {{ users|length }}</h3>
        <table>
            <tr>
                <th>User ID</th>
                <th>Username</th>
                <th>Name</th>
                <th>Balance (৳)</th>
                <th>Holding (৳)</th>
            </tr>
            {% for u in users %}
            <tr>
                <td>{{ u[0] }}</td>
                <td>@{{ u[1] }}</td>
                <td>{{ u[2] }}</td>
                <td>{{ u[3] }}</td>
                <td>{{ u[4] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    return "Bot is running successfully!"

@app.route(f"/admin/{ADMIN_SECRET}")
def admin_panel(secret):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, full_name, balance, holding FROM users")
    users = cursor.fetchall()
    subs = []
    conn.close()
    return render_template_string(ADMIN_TEMPLATE, users=users, subs=subs)

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- Telegram Bot Logic ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
                   (user.id, user.username, user.first_name))
    conn.commit()
    conn.close()

    keyboard = [
        [InlineKeyboardButton("📢 Payment Proof Channel", url="https://t.me/YourChannelLink")],
        [InlineKeyboardButton("📢 RM Airdrop", url="https://t.me/YourChannelLink")],
        [InlineKeyboardButton("✅ Verify Membership", callback_data="verify_membership")]
    ]
    await update.message.reply_text(
        "🔒 **Channel Verification Required**\n\n"
        "প্রথমে required channel-এ join করুন।\n"
        "তারপর নিচের **Verify Membership** button চাপুন।",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "verify_membership":
        user = query.from_user
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT balance, holding FROM users WHERE user_id = ?", (user.id,))
        row = cursor.fetchone()
        conn.close()
        
        balance = row[0] if row else 0.0
        holding = row[1] if row else 0.0

        keyboard = [
            [InlineKeyboardButton("📧 Gmail Sell", callback_data="gmail_sell"), InlineKeyboardButton("📱 TG Sell", callback_data="tg_sell")],
            [InlineKeyboardButton("💰 Balance", callback_data="balance"), InlineKeyboardButton("🎁 Refer & Earn", callback_data="refer")],
            [InlineKeyboardButton("📢 Channel", callback_data="channel"), InlineKeyboardButton("👤 My Account", callback_data="account")],
            [InlineKeyboardButton("📖 Help / Support", callback_data="support"), InlineKeyboardButton("❓ FAQ", callback_data="faq")]
        ]
        
        if user.id == ADMIN_ID:
            admin_url = f"https://your-render-app-url.onrender.com/admin/{ADMIN_SECRET}"
            keyboard.append([InlineKeyboardButton("👑 Admin Panel", url=admin_url)])

        await query.message.edit_text(
            f"✅ **Channel verification successful!**\n\n"
            f"🏠 **GMAIL SELL BOT**\n\n"
            f"👋 **Welcome,** {user.first_name}\n\n"
            f"💰 **Balance:** {balance:.2f} ৳\n"
            f"⏳ **Holding:** {holding:.2f} ৳\n\n"
            f"👇 **Select an option:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_Mode="Markdown"
        )

def main():
    t = threading.Thread(target=run_flask)
    t.start()

    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
