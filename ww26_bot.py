"""
🌍 WORLD WAR 26 - Telegram Bot
ساخته شده برای بازی جنگ جهانی ۲۶
"""

import logging
import json
import os
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ═══════════════════════════════════════════════
# ⚙️ تنظیمات اصلی
# ═══════════════════════════════════════════════
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8682325524:AAElXFNyFSAWup8aIwbpxRPEBLCOW40XXoo")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "-1003351040814")   # اگه کار نکرد بدون -100 امتحان کن
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8441499331"))
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")   # کلید API کلود رو اینجا بذار

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════
# 💾 دیتابیس ساده (فایل JSON)
# ═══════════════════════════════════════════════
DB_FILE = "ww26_data.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"players": {}, "declarations": [], "wars": [], "channel_posts": []}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ═══════════════════════════════════════════════
# 🌍 لیست کشورها
# ═══════════════════════════════════════════════
COUNTRIES = [
    {"id": "us",  "name": "🇺🇸 آمریکا",    "oil": True,  "nuclear": True,  "budget": 500000, "oil_barrels": 10000},
    {"id": "ru",  "name": "🇷🇺 روسیه",     "oil": True,  "nuclear": True,  "budget": 450000, "oil_barrels": 12000},
    {"id": "cn",  "name": "🇨🇳 چین",       "oil": False, "nuclear": True,  "budget": 480000, "oil_barrels": 0},
    {"id": "ir",  "name": "🇮🇷 ایران",     "oil": True,  "nuclear": False, "budget": 200000, "oil_barrels": 8000},
    {"id": "sa",  "name": "🇸🇦 عربستان",   "oil": True,  "nuclear": False, "budget": 350000, "oil_barrels": 15000},
    {"id": "de",  "name": "🇩🇪 آلمان",     "oil": False, "nuclear": False, "budget": 280000, "oil_barrels": 0},
    {"id": "fr",  "name": "🇫🇷 فرانسه",    "oil": False, "nuclear": True,  "budget": 260000, "oil_barrels": 0},
    {"id": "uk",  "name": "🇬🇧 انگلیس",    "oil": False, "nuclear": True,  "budget": 300000, "oil_barrels": 0},
    {"id": "tr",  "name": "🇹🇷 ترکیه",     "oil": False, "nuclear": False, "budget": 180000, "oil_barrels": 0},
    {"id": "pk",  "name": "🇵🇰 پاکستان",   "oil": False, "nuclear": True,  "budget": 150000, "oil_barrels": 0},
    {"id": "in",  "name": "🇮🇳 هند",       "oil": False, "nuclear": True,  "budget": 320000, "oil_barrels": 0},
    {"id": "br",  "name": "🇧🇷 برزیل",     "oil": True,  "nuclear": False, "budget": 220000, "oil_barrels": 5000},
    {"id": "il",  "name": "🇮🇱 اسرائیل",   "oil": False, "nuclear": True,  "budget": 250000, "oil_barrels": 0},
    {"id": "kp",  "name": "🇰🇵 کره شمالی", "oil": False, "nuclear": True,  "budget": 100000, "oil_barrels": 0},
    {"id": "jp",  "name": "🇯🇵 ژاپن",      "oil": False, "nuclear": False, "budget": 310000, "oil_barrels": 0},
    {"id": "az",  "name": "🇦🇿 آذربایجان", "oil": True,  "nuclear": False, "budget": 130000, "oil_barrels": 6000},
    {"id": "iq",  "name": "🇮🇶 عراق",      "oil": True,  "nuclear": False, "budget": 140000, "oil_barrels": 9000},
    {"id": "ve",  "name": "🇻🇪 ونزوئلا",   "oil": True,  "nuclear": False, "budget": 120000, "oil_barrels": 7000},
]

# ═══════════════════════════════════════════════
# 🛒 لیست تجهیزات
# ═══════════════════════════════════════════════
EQUIPMENT = {
    "air": [
        {"id": "launcher",      "name": "🚀 لانچر موشکی",        "price": 35000,   "oil": 0,     "type": "attack",  "power": 0,    "desc": "الزامی برای شلیک هر نوع موشک"},
        {"id": "f35",           "name": "🛩️ ۱۰ فروند F-35",      "price": 65000,   "oil": 0,     "type": "attack",  "power": 100,  "desc": "نابودی ۱۰۰ سرباز"},
        {"id": "b52",           "name": "💣 ۵ بمب‌افکن B-52",    "price": 100000,  "oil": 0,     "type": "attack",  "power": 300,  "desc": "نابودی ۵ تانک یا ۳۰۰ سرباز"},
        {"id": "heli",          "name": "🚁 ۵ هلیکوپتر هجومی",   "price": 25000,   "oil": 0,     "type": "attack",  "power": 150,  "desc": "نابودی ۲ تانک یا ۱۵۰ سرباز"},
        {"id": "airdef_light",  "name": "🛡️ پدافند هوایی سبک",   "price": 50000,   "oil": 0,     "type": "defense", "power": 10,   "desc": "نابودی ۱۰ جنگنده یا هلیکوپتر"},
        {"id": "airdef_heavy",  "name": "🛡️ پدافند هوایی سنگین", "price": 100000,  "oil": 0,     "type": "defense", "power": 5,    "desc": "نابودی ۵ بمب‌افکن"},
    ],
    "naval": [
        {"id": "frigate",       "name": "🚢 ۵ ناوچه رزمی",       "price": 35000,   "oil": 0,     "type": "attack",  "power": 50,   "desc": "پشتیبانی ساحلی"},
        {"id": "warship",       "name": "🚢 ۳ ناو جنگی",         "price": 50000,   "oil": 0,     "type": "attack",  "power": 100,  "desc": "نابودی تجهیزات ساحلی"},
        {"id": "carrier",       "name": "🚢 ناو هواپیمابر",       "price": 120000,  "oil": 0,     "type": "attack",  "power": 200,  "desc": "امکان جنگنده دریایی"},
        {"id": "coastal_def",   "name": "🛡️ پدافند ساحلی",       "price": 100000,  "oil": 0,     "type": "defense", "power": 150,  "desc": "نابودی ۵ ناوچه و ۲ ناو"},
    ],
    "missiles": [
        {"id": "normal_ms",     "name": "🚀 ۱۰۰۰ موشک عادی",      "price": 24000,   "oil": 500,   "type": "attack",  "power": 100,  "desc": "موشک پایه"},
        {"id": "cruise",        "name": "🚀 ۱۰۰ موشک کروز",        "price": 48000,   "oil": 1000,  "type": "attack",  "power": 300,  "desc": "دقت بالا"},
        {"id": "ballistic",     "name": "🚀 ۱۰۰ موشک بالستیک",     "price": 80000,   "oil": 1500,  "type": "attack",  "power": 500,  "desc": "برد بلند"},
        {"id": "precision",     "name": "🎯 ۱۰۰ موشک نقطه‌زن",    "price": 120000,  "oil": 3000,  "type": "attack",  "power": 700,  "desc": "دقت فوق‌العاده"},
        {"id": "hypersonic",    "name": "⚡ ۱۰۰ موشک هایپرسونیک",  "price": 180000,  "oil": 6000,  "type": "attack",  "power": 900,  "desc": "سرعت فوق صوت"},
        {"id": "icbm",          "name": "🚀🌍 موشک قاره‌پیما",      "price": 200000,  "oil": 12000, "type": "attack",  "power": 1500, "desc": "برد جهانی"},
        {"id": "atom_bomb",     "name": "☢️ بمب اتمی",             "price": 15000000,"oil": 0,     "type": "attack",  "power": 10000,"desc": "سلاح کشتار جمعی ⚠️"},
        {"id": "msdef_light",   "name": "🛡️ پدافند موشکی سبک",    "price": 24000,   "oil": 0,     "type": "defense", "power": 1000, "desc": "خنثی ۱۰۰۰ موشک عادی"},
        {"id": "msdef_adv",     "name": "🛡️ پدافند موشکی پیشرفته","price": 48000,   "oil": 0,     "type": "defense", "power": 500,  "desc": "خنثی کروز و بالستیک"},
        {"id": "msdef_ultra",   "name": "🛡️ پدافند فوق پیشرفته",  "price": 80000,   "oil": 0,     "type": "defense", "power": 300,  "desc": "خنثی نقطه‌زن و هایپرسونیک"},
        {"id": "icbm_def",      "name": "🛡️ پدافند قاره‌پیما",    "price": 200000,  "oil": 0,     "type": "defense", "power": 1,    "desc": "خنثی ۱ موشک قاره‌پیما"},
    ],
    "ground": [
        {"id": "soldier",       "name": "👤 ۱۰۰۰۰ سرباز عادی",    "price": 100000,  "oil": 0,     "type": "attack",  "power": 100,  "desc": "پیاده نظام"},
        {"id": "special",       "name": "🪖 ۱۰۰۰۰ نیروی ویژه",    "price": 200000,  "oil": 0,     "type": "attack",  "power": 200,  "desc": "نیروی ویژه"},
        {"id": "rpg",           "name": "💥 ۱۰۰۰ RPG",            "price": 50000,   "oil": 0,     "type": "attack",  "power": 150,  "desc": "ضد زره"},
        {"id": "tank",          "name": "🚓 ۱۰۰ تانک",            "price": 40000,   "oil": 0,     "type": "attack",  "power": 200,  "desc": "زره پوش"},
        {"id": "heavy_tank",    "name": "🦾 ۱۰ تانک سنگین",       "price": 70000,   "oil": 0,     "type": "attack",  "power": 300,  "desc": "زره پوش سنگین"},
        {"id": "artillery",     "name": "🎯 ۱۰ توپخانه",          "price": 30000,   "oil": 0,     "type": "attack",  "power": 250,  "desc": "آتشبار سنگین"},
        {"id": "gdef_light",    "name": "🛡️ دفاع زمینی سبک",      "price": 90000,   "oil": 0,     "type": "defense", "power": 90,   "desc": "کاهش ۹۰٪ تلفات سرباز"},
        {"id": "gdef_mid",      "name": "🛡️ دفاع زمینی متوسط",    "price": 150000,  "oil": 0,     "type": "defense", "power": 150,  "desc": "کاهش ۱۵۰٪ تلفات نیروی ویژه"},
        {"id": "gdef_heavy",    "name": "🛡️ دفاع زمینی سنگین",    "price": 240000,  "oil": 0,     "type": "defense", "power": 500,  "desc": "خنثی یک موج کامل حمله"},
    ],
    "economy": [
        {"id": "iron",          "name": "⛏️ معدن آهن",            "price": 10000,   "oil": 0,     "type": "economy", "daily": 5000,  "desc": "۵,۰۰۰$/روز"},
        {"id": "silver",        "name": "⛏️ معدن نقره",           "price": 20000,   "oil": 0,     "type": "economy", "daily": 8000,  "desc": "۸,۰۰۰$/روز"},
        {"id": "gold",          "name": "⛏️ معدن طلا",            "price": 25000,   "oil": 0,     "type": "economy", "daily": 11000, "desc": "۱۱,۰۰۰$/روز"},
        {"id": "diamond",       "name": "⛏️ معدن الماس",          "price": 45000,   "oil": 0,     "type": "economy", "daily": 16000, "desc": "۱۶,۰۰۰$/روز"},
        {"id": "refinery",      "name": "🛢️ پالایشگاه نفت",       "price": 40000,   "oil": 0,     "type": "economy", "daily": 0, "oil_daily": 1000, "desc": "۱۰۰۰ بشکه/روز (نیاز به نفت)"},
    ],
    "cyber": [
        {"id": "antihack",      "name": "🖥️ ضد هک",              "price": 600000,  "oil": 0,     "type": "defense", "power": 100,  "desc": "دفع هک ساده + یک هک پیشرفته"},
        {"id": "antivirus",     "name": "👾 آنتی ویروس",          "price": 900000,  "oil": 0,     "type": "defense", "power": 200,  "desc": "سیستم امنیتی پیشرفته"},
    ],
}

CAT_LABELS = {
    "air": "✈️ هوایی",
    "naval": "🚢 دریایی",
    "missiles": "🚀 موشکی",
    "ground": "🪖 زمینی",
    "economy": "⛏️ اقتصادی",
    "cyber": "🖥️ سایبری",
}

# States for ConversationHandler
WAITING_DECLARATION = 1
WAITING_WAR_TARGET = 2
WAITING_WAR_SCENARIO = 3

# ═══════════════════════════════════════════════
# 🤖 توابع هوش مصنوعی
# ═══════════════════════════════════════════════
def get_ai_client():
    if ANTHROPIC_API_KEY:
        return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return None

async def ai_review_declaration(country_name: str, text: str) -> dict:
    client = get_ai_client()
    if not client:
        return {"approved": True, "reason": "تایید خودکار (AI غیرفعال)", "edited": text}
    try:
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system="""تو دستیار بازی جنگ جهانی ۲۶ هستی. بیانیه‌های کشورها رو بررسی می‌کنی.
اگه بیانیه توهین‌آمیز یا نامناسب نباشه تایید کن.
پاسخ فقط JSON بده بدون هیچ چیز اضافه:
{"approved": true, "reason": "دلیل فارسی", "edited": "متن نهایی"}""",
            messages=[{"role": "user", "content": f"کشور: {country_name}\nبیانیه:\n{text}"}]
        )
        raw = msg.content[0].text.strip().replace("```json","").replace("```","")
        return json.loads(raw)
    except:
        return {"approved": True, "reason": "تایید خودکار", "edited": text}

async def ai_simulate_war(attacker: dict, defender: dict, atk_eq: list, def_eq: list, scenario: str) -> dict:
    client = get_ai_client()
    if not client:
        return {
            "winner": "defender",
            "atk_loss": 35, "def_loss": 20,
            "narrative": "نبرد سختی بود. مدافع با استفاده از دفاعیات خود حمله را دفع کرد.",
            "territory": "وضعیت ارضی تغییری نکرد."
        }
    try:
        atk_list = ", ".join([e["name"] for e in atk_eq]) or "هیچ"
        def_list = ", ".join([e["name"] for e in def_eq]) or "هیچ"
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system="""تو تحلیلگر نظامی بازی جنگ جهانی ۲۶ هستی. نتیجه نبرد رو تحلیل کن.
پاسخ فقط JSON بده:
{"winner": "attacker یا defender", "atk_loss": عدد_درصد, "def_loss": عدد_درصد, "narrative": "توضیح فارسی ۳ جمله", "territory": "وضعیت ارضی"}""",
            messages=[{"role": "user", "content": f"""
حمله‌کننده: {attacker['name']} | بودجه: ${attacker.get('budget',0):,}
تجهیزات حمله: {atk_list}

مدافع: {defender['name']} | بودجه: ${defender.get('budget',0):,}
تجهیزات دفاع: {def_list}

سناریو: {scenario}
"""}]
        )
        raw = msg.content[0].text.strip().replace("```json","").replace("```","")
        return json.loads(raw)
    except:
        return {
            "winner": "defender",
            "atk_loss": 30, "def_loss": 15,
            "narrative": "نبرد سختی بود. نتیجه قطعی نشد.",
            "territory": "وضعیت تغییری نکرد."
        }

# ═══════════════════════════════════════════════
# 🎮 دستورات اصلی بات
# ═══════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user_id = str(update.effective_user.id)
    player = db["players"].get(user_id)

    if player:
        country = next((c for c in COUNTRIES if c["id"] == player["country_id"]), None)
        name = country["name"] if country else "نامشخص"
        kb = [
            [InlineKeyboardButton("📊 پنل من", callback_data="panel"),
             InlineKeyboardButton("🛒 خرید تجهیزات", callback_data="shop_menu")],
            [InlineKeyboardButton("📜 ارسال بیانیه", callback_data="declare"),
             InlineKeyboardButton("⚔️ اعلام جنگ", callback_data="war_menu")],
            [InlineKeyboardButton("🌍 وضعیت کشورها", callback_data="world_status"),
             InlineKeyboardButton("🚪 خروج از بازی", callback_data="quit_game")],
        ]
        if update.effective_user.id == ADMIN_ID:
            kb.append([InlineKeyboardButton("👑 پنل ادمین", callback_data="admin_panel")])
        await update.message.reply_text(
            f"🌍 خوش اومدی {update.effective_user.first_name}!\n\n"
            f"کشور فعلی‌ات: {name}\n"
            f"💰 بودجه: ${player.get('budget', 0):,}\n"
            f"🛢️ نفت: {player.get('oil', 0):,} بشکه",
            reply_markup=InlineKeyboardMarkup(kb)
        )
    else:
        kb = [[InlineKeyboardButton("🌍 انتخاب کشور و ورود به بازی", callback_data="select_country")]]
        await update.message.reply_text(
            "🌍⚔️ *WORLD WAR 26* ⚔️🌍\n\n"
            "به بازی جنگ جهانی ۲۶ خوش اومدی!\n\n"
            "یه کشور انتخاب کن، تجهیزات بخر، بیانیه بده و به جنگ برو! 🔥\n\n"
            "برای شروع روی دکمه زیر بزن 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )

async def show_country_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    taken = {p["country_id"] for p in db["players"].values()}
    query = update.callback_query
    await query.answer()

    kb = []
    row = []
    for i, c in enumerate(COUNTRIES):
        t = c["id"] in taken
        label = c["name"] + (" ✅" if not t else " 🔒")
        cb = f"join_{c['id']}" if not t else "taken"
        row.append(InlineKeyboardButton(label, callback_data=cb))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_start")])

    await query.edit_message_text(
        "🌍 *لیست کشورها*\n\n"
        "✅ = آزاد | 🔒 = گرفته شده\n"
        "🛢️ = دارای نفت | ☢️ = توان اتمی\n\n"
        "کشورت رو انتخاب کن:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def join_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    country_id = query.data.replace("join_", "")
    db = load_db()
    user_id = str(update.effective_user.id)

    if user_id in db["players"]:
        await query.edit_message_text("❌ تو قبلاً کشوری انتخاب کردی!\nبرای بازگشت /start بزن.")
        return

    taken = {p["country_id"] for p in db["players"].values()}
    if country_id in taken:
        await query.edit_message_text("❌ این کشور قبلاً انتخاب شده!\n/start رو بزن.")
        return

    country = next((c for c in COUNTRIES if c["id"] == country_id), None)
    if not country:
        return

    db["players"][user_id] = {
        "user_id": user_id,
        "username": update.effective_user.username or update.effective_user.first_name,
        "country_id": country_id,
        "budget": country["budget"],
        "oil": country["oil_barrels"],
        "equipment": [],
        "joined_at": str(update.effective_message.date),
    }
    save_db(db)

    props = []
    if country["oil"]: props.append("🛢️ نفت")
    if country["nuclear"]: props.append("☢️ توان اتمی")

    kb = [[InlineKeyboardButton("📊 رفتن به پنل", callback_data="panel")]]
    await query.edit_message_text(
        f"✅ *{country['name']}* با موفقیت انتخاب شد!\n\n"
        f"💰 بودجه اولیه: ${country['budget']:,}\n"
        f"🛢️ نفت: {country['oil_barrels']:,} بشکه\n"
        f"🏷️ امکانات: {' | '.join(props) if props else 'معمولی'}\n\n"
        f"حالا می‌تونی تجهیزات بخری، بیانیه بدی و جنگ کنی! ⚔️",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

    # اطلاع به ادمین
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"🔔 بازیکن جدید!\n👤 {update.effective_user.first_name} (@{update.effective_user.username})\n🌍 کشور: {country['name']}"
        )
    except:
        pass

async def show_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db = load_db()
    user_id = str(update.effective_user.id)
    player = db["players"].get(user_id)

    if not player:
        await query.edit_message_text("❌ تو هنوز وارد بازی نشدی!\n/start بزن.")
        return

    country = next((c for c in COUNTRIES if c["id"] == player["country_id"]), None)
    eq = player.get("equipment", [])
    atk = [e for e in eq if e.get("type") == "attack"]
    defn = [e for e in eq if e.get("type") == "defense"]
    econ = [e for e in eq if e.get("type") == "economy"]

    daily = sum(e.get("daily", 0) for e in econ)
    oil_daily = sum(e.get("oil_daily", 0) for e in econ)

    kb = [
        [InlineKeyboardButton("🛒 خرید تجهیزات", callback_data="shop_menu"),
         InlineKeyboardButton("📜 ارسال بیانیه", callback_data="declare")],
        [InlineKeyboardButton("⚔️ اعلام جنگ", callback_data="war_menu"),
         InlineKeyboardButton("🌍 وضعیت کشورها", callback_data="world_status")],
        [InlineKeyboardButton("🚪 خروج از بازی", callback_data="quit_game")],
    ]
    if update.effective_user.id == ADMIN_ID:
        kb.append([InlineKeyboardButton("👑 پنل ادمین", callback_data="admin_panel")])

    text = (
        f"📊 *پنل کشور {country['name']}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 بودجه: ${player['budget']:,}\n"
        f"🛢️ نفت: {player.get('oil', 0):,} بشکه\n"
        f"📈 درآمد روزانه: ${daily:,}/روز\n"
        f"🛢️ تولید نفت: {oil_daily:,} بشکه/روز\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚔️ تجهیزات حمله: {len(atk)}\n"
        f"🛡️ تجهیزات دفاع: {len(defn)}\n"
        f"⛏️ تجهیزات اقتصادی: {len(econ)}\n"
        f"━━━━━━━━━━━━━━━\n"
    )
    if eq:
        text += "🔧 *تجهیزات فعلی:*\n"
        for e in eq[-5:]:
            text += f"• {e['name']}\n"
        if len(eq) > 5:
            text += f"_و {len(eq)-5} مورد دیگه..._\n"

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def show_shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db = load_db()
    user_id = str(update.effective_user.id)
    player = db["players"].get(user_id)
    if not player:
        await query.edit_message_text("❌ اول وارد بازی شو! /start")
        return

    kb = []
    for cat_id, label in CAT_LABELS.items():
        kb.append([InlineKeyboardButton(label, callback_data=f"shop_{cat_id}")])
    kb.append([InlineKeyboardButton("🔙 برگشت", callback_data="panel")])

    await query.edit_message_text(
        f"🛒 *فروشگاه تجهیزات*\n\n"
        f"💰 بودجه: ${player['budget']:,}\n"
        f"🛢️ نفت: {player.get('oil', 0):,} بشکه\n\n"
        f"دسته‌بندی رو انتخاب کن:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def show_shop_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data.replace("shop_", "")
    db = load_db()
    user_id = str(update.effective_user.id)
    player = db["players"].get(user_id)
    if not player:
        return

    items = EQUIPMENT.get(cat, [])
    kb = []
    for item in items:
        oil_txt = f" + {item['oil']:,}🛢️" if item.get("oil") else ""
        label = f"{item['name']} | ${item['price']:,}{oil_txt}"
        kb.append([InlineKeyboardButton(label, callback_data=f"buy_{item['id']}")])
    kb.append([InlineKeyboardButton("🔙 برگشت به فروشگاه", callback_data="shop_menu")])

    await query.edit_message_text(
        f"🛒 *{CAT_LABELS[cat]}*\n\n"
        f"💰 بودجه: ${player['budget']:,} | 🛢️ {player.get('oil',0):,} بشکه\n\n"
        f"روی آیتم بزن تا بخری:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item_id = query.data.replace("buy_", "")
    db = load_db()
    user_id = str(update.effective_user.id)
    player = db["players"].get(user_id)
    if not player:
        return

    # پیدا کردن آیتم
    item = None
    for cat_items in EQUIPMENT.values():
        for it in cat_items:
            if it["id"] == item_id:
                item = it
                break
    if not item:
        await query.answer("آیتم پیدا نشد!", show_alert=True)
        return

    # چک بودجه
    if player["budget"] < item["price"]:
        await query.answer(f"❌ بودجه کافی نیست! نیاز: ${item['price']:,}", show_alert=True)
        return

    # چک نفت
    if item.get("oil", 0) and player.get("oil", 0) < item["oil"]:
        await query.answer(f"❌ نفت کافی نیست! نیاز: {item['oil']:,} بشکه", show_alert=True)
        return

    # چک پالایشگاه نفت
    if item["id"] == "refinery":
        country = next((c for c in COUNTRIES if c["id"] == player["country_id"]), None)
        if not country or not country.get("oil"):
            await query.answer("❌ کشور شما ذخایر نفتی ندارد!", show_alert=True)
            return

    # خرید
    player["budget"] -= item["price"]
    if item.get("oil"):
        player["oil"] -= item["oil"]
    if "equipment" not in player:
        player["equipment"] = []
    player["equipment"].append(item)
    db["players"][user_id] = player
    save_db(db)

    await query.answer(f"✅ {item['name']} خریداری شد!", show_alert=True)
    # بروزرسانی پیام
    cat = None
    for c, items in EQUIPMENT.items():
        if any(i["id"] == item_id for i in items):
            cat = c
            break
    if cat:
        await show_shop_category(update, context)

# ═══════════════════════════════════════════════
# 📜 بیانیه
# ═══════════════════════════════════════════════
async def declare_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db = load_db()
    user_id = str(update.effective_user.id)
    if user_id not in db["players"]:
        await query.edit_message_text("❌ اول وارد بازی شو! /start")
        return ConversationHandler.END

    await query.edit_message_text(
        "📜 *ارسال بیانیه رسمی*\n\n"
        "متن بیانیه رسمی کشورت رو بنویس.\n"
        "هوش مصنوعی بررسی می‌کنه و بعد از تایید در کانال منتشر میشه.\n\n"
        "✍️ بیانیه‌ات رو بنویس:",
        parse_mode="Markdown"
    )
    return WAITING_DECLARATION

async def receive_declaration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user_id = str(update.effective_user.id)
    player = db["players"].get(user_id)
    if not player:
        return ConversationHandler.END

    country = next((c for c in COUNTRIES if c["id"] == player["country_id"]), None)
    text = update.message.text

    await update.message.reply_text("⏳ هوش مصنوعی داره بیانیه رو بررسی می‌کنه...")

    result = await ai_review_declaration(country["name"], text)

    if result["approved"]:
        # ذخیره
        decl = {
            "id": len(db["declarations"]) + 1,
            "user_id": user_id,
            "country": country["name"],
            "text": result["edited"],
            "date": str(update.message.date),
        }
        db["declarations"].append(decl)
        save_db(db)

        # پست در کانال
        channel_text = (
            f"📜 *بیانیه رسمی*\n"
            f"🌍 {country['name']}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{result['edited']}"
        )
        try:
            await context.bot.send_message(CHANNEL_ID, channel_text, parse_mode="Markdown")
            await update.message.reply_text("✅ بیانیه تایید و در کانال منتشر شد!")
        except Exception as e:
            await update.message.reply_text(f"✅ تایید شد ولی ارسال به کانال خطا داشت:\n{e}")

        # اطلاع ادمین
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"📜 بیانیه جدید از {country['name']}\n\n{result['edited']}"
            )
        except:
            pass
    else:
        await update.message.reply_text(f"❌ بیانیه رد شد!\n\n💬 دلیل: {result['reason']}")

    kb = [[InlineKeyboardButton("🔙 برگشت به پنل", callback_data="panel")]]
    await update.message.reply_text("بزن به پنل برگردی:", reply_markup=InlineKeyboardMarkup(kb))
    return ConversationHandler.END

# ═══════════════════════════════════════════════
# ⚔️ جنگ
# ═══════════════════════════════════════════════
async def war_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db = load_db()
    user_id = str(update.effective_user.id)
    player = db["players"].get(user_id)
    if not player:
        await query.edit_message_text("❌ اول وارد بازی شو! /start")
        return

    others = {uid: p for uid, p in db["players"].items() if uid != user_id}
    if not others:
        kb = [[InlineKeyboardButton("🔙 برگشت", callback_data="panel")]]
        await query.edit_message_text("⚔️ هنوز بازیکن دیگه‌ای در بازی نیست!", reply_markup=InlineKeyboardMarkup(kb))
        return

    kb = []
    for uid, p in others.items():
        country = next((c for c in COUNTRIES if c["id"] == p["country_id"]), None)
        if country:
            kb.append([InlineKeyboardButton(f"⚔️ حمله به {country['name']}", callback_data=f"attack_{uid}")])
    kb.append([InlineKeyboardButton("🔙 برگشت", callback_data="panel")])

    await query.edit_message_text(
        "⚔️ *انتخاب هدف حمله*\n\nکدوم کشور رو هدف می‌گیری؟",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def attack_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    target_id = query.data.replace("attack_", "")
    context.user_data["war_target"] = target_id

    await query.edit_message_text(
        "📋 *سناریو حمله*\n\n"
        "توضیح بده چطور حمله می‌کنی:\n"
        "مثلاً: با موشک‌های بالستیک پایگاه‌های هوایی رو هدف می‌گیرم\n\n"
        "✍️ سناریوت رو بنویس:",
        parse_mode="Markdown"
    )
    return WAITING_WAR_SCENARIO

async def receive_war_scenario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user_id = str(update.effective_user.id)
    target_id = context.user_data.get("war_target")
    scenario = update.message.text

    attacker_p = db["players"].get(user_id)
    defender_p = db["players"].get(target_id)

    if not attacker_p or not defender_p:
        await update.message.reply_text("❌ خطا در یافتن بازیکنان!")
        return ConversationHandler.END

    atk_country = next((c for c in COUNTRIES if c["id"] == attacker_p["country_id"]), None)
    def_country = next((c for c in COUNTRIES if c["id"] == defender_p["country_id"]), None)

    await update.message.reply_text("⏳ هوش مصنوعی داره نبرد رو تحلیل می‌کنه...")

    atk_eq = [e for e in attacker_p.get("equipment", []) if e.get("type") == "attack"]
    def_eq = [e for e in defender_p.get("equipment", []) if e.get("type") == "defense"]

    result = await ai_simulate_war(attacker_p, defender_p, atk_eq, def_eq, scenario)

    winner_name = atk_country["name"] if result["winner"] == "attacker" else def_country["name"]

    war_record = {
        "id": len(db["wars"]) + 1,
        "attacker": atk_country["name"],
        "defender": def_country["name"],
        "scenario": scenario,
        "winner": winner_name,
        "atk_loss": result["atk_loss"],
        "def_loss": result["def_loss"],
        "narrative": result["narrative"],
        "date": str(update.message.date),
    }
    db["wars"].append(war_record)
    save_db(db)

    war_text = (
        f"⚔️ *گزارش نبرد*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔴 حمله‌کننده: {atk_country['name']}\n"
        f"🔵 مدافع: {def_country['name']}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📋 سناریو: {scenario}\n\n"
        f"📰 {result['narrative']}\n\n"
        f"🏆 *برنده: {winner_name}*\n"
        f"📉 تلفات حمله‌کننده: {result['atk_loss']}%\n"
        f"📉 تلفات مدافع: {result['def_loss']}%\n"
        f"📍 {result['territory']}"
    )

    # ارسال به کانال
    try:
        await context.bot.send_message(CHANNEL_ID, war_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Channel post error: {e}")

    # اطلاع به مدافع
    try:
        await context.bot.send_message(
            int(target_id),
            f"🚨 *هشدار! {atk_country['name']} به کشور شما حمله کرد!*\n\n{result['narrative']}\n\n🏆 برنده: {winner_name}"
            , parse_mode="Markdown"
        )
    except:
        pass

    await update.message.reply_text(war_text, parse_mode="Markdown")
    kb = [[InlineKeyboardButton("🔙 برگشت به پنل", callback_data="panel")]]
    await update.message.reply_text(".", reply_markup=InlineKeyboardMarkup(kb))
    return ConversationHandler.END

# ═══════════════════════════════════════════════
# 🌍 وضعیت کشورها
# ═══════════════════════════════════════════════
async def world_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db = load_db()

    text = "🌍 *وضعیت کشورهای بازی*\n━━━━━━━━━━━━━━━\n"
    if not db["players"]:
        text += "هنوز کسی وارد بازی نشده!"
    else:
        for uid, p in db["players"].items():
            country = next((c for c in COUNTRIES if c["id"] == p["country_id"]), None)
            if country:
                eq_count = len(p.get("equipment", []))
                text += f"{country['name']}\n"
                text += f"  💰 ${p['budget']:,} | 🔧 {eq_count} تجهیز\n"

    kb = [[InlineKeyboardButton("🔙 برگشت", callback_data="panel")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# ═══════════════════════════════════════════════
# 🚪 خروج از بازی
# ═══════════════════════════════════════════════
async def quit_game_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [
        [InlineKeyboardButton("✅ بله، از بازی خارج میشم", callback_data="quit_confirm")],
        [InlineKeyboardButton("❌ نه، بمونم", callback_data="panel")],
    ]
    await query.edit_message_text(
        "🚪 *خروج از بازی*\n\n"
        "مطمئنی؟ تمام تجهیزات و پیشرفتت حذف میشه و کشورت آزاد میشه!\n\n"
        "این عمل برگشت‌پذیر نیست! ⚠️",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def quit_game_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db = load_db()
    user_id = str(update.effective_user.id)
    player = db["players"].get(user_id)

    if player:
        country = next((c for c in COUNTRIES if c["id"] == player["country_id"]), None)
        del db["players"][user_id]
        save_db(db)
        country_name = country["name"] if country else "نامشخص"
        await query.edit_message_text(
            f"🚪 از بازی خارج شدی.\n\n"
            f"کشور {country_name} آزاد شد.\n\n"
            f"هر وقت خواستی دوباره /start بزن! 👋"
        )
        try:
            await context.bot.send_message(ADMIN_ID, f"🚪 {update.effective_user.first_name} از بازی خارج شد. ({country_name} آزاد شد)")
        except:
            pass
    else:
        await query.edit_message_text("❌ تو تو بازی نیستی!")

# ═══════════════════════════════════════════════
# 👑 پنل ادمین
# ═══════════════════════════════════════════════
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    query = update.callback_query
    await query.answer()
    db = load_db()

    kb = [
        [InlineKeyboardButton("👥 لیست بازیکنان", callback_data="admin_players"),
         InlineKeyboardButton("📜 بیانیه‌ها", callback_data="admin_decls")],
        [InlineKeyboardButton("⚔️ تاریخچه جنگ‌ها", callback_data="admin_wars"),
         InlineKeyboardButton("💬 ارسال پیام به کانال", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="panel")],
    ]
    await query.edit_message_text(
        f"👑 *پنل ادمین*\n\n"
        f"👥 بازیکنان: {len(db['players'])}\n"
        f"📜 بیانیه‌ها: {len(db['declarations'])}\n"
        f"⚔️ جنگ‌ها: {len(db['wars'])}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def admin_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    query = update.callback_query
    await query.answer()
    db = load_db()

    text = "👥 *لیست بازیکنان*\n━━━━━━━━━━━━━━━\n"
    for uid, p in db["players"].items():
        country = next((c for c in COUNTRIES if c["id"] == p["country_id"]), None)
        text += f"• {p.get('username','?')} → {country['name'] if country else '?'}\n"
        text += f"  💰 ${p['budget']:,} | 🔧 {len(p.get('equipment',[]))} تجهیز\n"

    kb = [[InlineKeyboardButton("🔙 برگشت", callback_data="admin_panel")]]
    await query.edit_message_text(text or "کسی در بازی نیست", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def admin_wars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    query = update.callback_query
    await query.answer()
    db = load_db()

    text = "⚔️ *تاریخچه جنگ‌ها*\n━━━━━━━━━━━━━━━\n"
    for w in db["wars"][-10:]:
        text += f"• {w['attacker']} ⚔️ {w['defender']}\n  🏆 {w['winner']}\n"

    kb = [[InlineKeyboardButton("🔙 برگشت", callback_data="admin_panel")]]
    await query.edit_message_text(text or "جنگی ثبت نشده", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("🔙 برگشت به پنل", callback_data="panel")]]
    await update.message.reply_text("❌ لغو شد.", reply_markup=InlineKeyboardMarkup(kb))
    return ConversationHandler.END

async def taken_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("❌ این کشور قبلاً انتخاب شده!", show_alert=True)

async def back_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await start(update, context)

# ═══════════════════════════════════════════════
# 🚀 اجرای بات
# ═══════════════════════════════════════════════
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler برای بیانیه
    decl_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(declare_start, pattern="^declare$")],
        states={WAITING_DECLARATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_declaration)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler برای جنگ
    war_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(attack_target, pattern="^attack_")],
        states={WAITING_WAR_SCENARIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_war_scenario)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(decl_conv)
    app.add_handler(war_conv)

    app.add_handler(CallbackQueryHandler(show_country_list, pattern="^select_country$"))
    app.add_handler(CallbackQueryHandler(join_country, pattern="^join_"))
    app.add_handler(CallbackQueryHandler(show_panel, pattern="^panel$"))
    app.add_handler(CallbackQueryHandler(show_shop_menu, pattern="^shop_menu$"))
    app.add_handler(CallbackQueryHandler(show_shop_category, pattern="^shop_[a-z]+$"))
    app.add_handler(CallbackQueryHandler(buy_item, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(war_menu, pattern="^war_menu$"))
    app.add_handler(CallbackQueryHandler(world_status, pattern="^world_status$"))
    app.add_handler(CallbackQueryHandler(quit_game_confirm, pattern="^quit_game$"))
    app.add_handler(CallbackQueryHandler(quit_game_execute, pattern="^quit_confirm$"))
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(admin_players, pattern="^admin_players$"))
    app.add_handler(CallbackQueryHandler(admin_wars, pattern="^admin_wars$"))
    app.add_handler(CallbackQueryHandler(taken_cb, pattern="^taken$"))
    app.add_handler(CallbackQueryHandler(back_start, pattern="^back_start$"))

    print("✅ بات World War 26 فعال شد!")
    app.run_polling()

if __name__ == "__main__":
    main()
