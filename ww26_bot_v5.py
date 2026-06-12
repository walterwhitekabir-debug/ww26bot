"""
🌍 WORLD WAR 26 - Bot v4.0 ULTRA
نسخه کاملاً بازنویسی‌شده با هوش مصنوعی پیشرفته

🆕 قابلیت‌های جدید:
- سیستم جاسوسی و عملیات مخفی
- سیستم دیپلماسی پیشرفته (صلح، تحریم، ناتو)
- رویدادهای تصادفی زنده (بلایای طبیعی، انقلاب، کودتا)
- سیستم تحقیق و توسعه (R&D)
- بازار نفت جهانی پویا
- سیستم اشتهار و قدرت نرم
- جنگ اطلاعاتی و پروپاگاندا
- بمباران اقتصادی و تحریم
- AI داستان‌سرای سینمایی فوق‌پیشرفته
- رنکینگ زنده جهانی
- سیستم دستاورد (Achievement)
"""

import logging, json, os, random, asyncio
from datetime import datetime, timedelta
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler)

# ─── تنظیمات اصلی ───────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8441499331"))
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CHANNEL_LINK = "https://t.me/ww26jang"
START_BUDGET = 250000
OIL_PRICE = 80  # دلار در هر بشکه - پویا

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DB_FILE = "ww26.json"

# ─── دیتابیس ────────────────────────────────────────────────────
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "players": {}, "declarations": [], "wars": [], "trades": [],
        "referrals": {}, "last_income": "", "last_news": "", "occupied": {},
        "alliances": {}, "spy_ops": [], "events": [], "sanctions": {},
        "peace_treaties": {}, "oil_price": 80, "research": {},
        "achievements": {}, "propaganda": [], "world_tension": 30,
        "un_resolutions": [], "market": {"oil": 80, "arms": 100}
    }

def save_db(d):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


# ─── فیلتر فحش (کلمه‌ای - سریع) ──────────────────────────────────
_PROF = ["کص","کس ","کیر","کون","جنده","مادرجنده","بیشعور","لاشی",
         "عوضی","گاییدم","کسکش","جاکش","حرامزاده",
         "fuck","shit","bitch","dick","pussy","cunt","whore"]
def has_profanity(text):
    t = text.lower().replace(" ","").replace("\u200c","")
    return any(w.lower().replace(" ","") in t for w in _PROF)

GAME_SETTINGS = {"shop": True, "decl": True, "war": True, "trade": True, "spy": True}

# ─── کشورها (کامل‌شده) ──────────────────────────────────────────
COUNTRIES = [
    {"id":"cn","name":"🇨🇳 چین","cont":"🌏 آسیا","oil":False,"nuclear":True,"oil_b":0,"borders":["ru","kz","vn","mm","in","pk","kp","kr"],"sea":True,"gdp":18000,"pop":1400,"army":2000},
    {"id":"ru","name":"🇷🇺 روسیه","cont":"🌏 آسیا/اروپا","oil":True,"nuclear":True,"oil_b":15000,"borders":["cn","kz","ua","pl","no","fi"],"sea":True,"gdp":2100,"pop":145,"army":1000},
    {"id":"ir","name":"🇮🇷 ایران","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":12000,"borders":["iq","tr","af","az","pk"],"sea":True,"gdp":360,"pop":87,"army":580},
    {"id":"sa","name":"🇸🇦 عربستان","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":20000,"borders":["iq","ae","ye","jo"],"sea":True,"gdp":1100,"pop":36,"army":230},
    {"id":"in","name":"🇮🇳 هند","cont":"🌏 آسیا","oil":False,"nuclear":True,"oil_b":0,"borders":["pk","cn","mm","bd","np"],"sea":True,"gdp":3700,"pop":1430,"army":1460},
    {"id":"pk","name":"🇵🇰 پاکستان","cont":"🌏 آسیا","oil":False,"nuclear":True,"oil_b":0,"borders":["ir","in","af","cn"],"sea":True,"gdp":375,"pop":231,"army":654},
    {"id":"kp","name":"🇰🇵 کره شمالی","cont":"🌏 آسیا","oil":False,"nuclear":True,"oil_b":0,"borders":["cn","kr"],"sea":True,"gdp":16,"pop":26,"army":1280},
    {"id":"kr","name":"🇰🇷 کره جنوبی","cont":"🌏 آسیا","oil":False,"nuclear":False,"oil_b":0,"borders":["kp"],"sea":True,"gdp":1800,"pop":52,"army":600},
    {"id":"jp","name":"🇯🇵 ژاپن","cont":"🌏 آسیا","oil":False,"nuclear":False,"oil_b":0,"borders":[],"sea":True,"gdp":4200,"pop":125,"army":247},
    {"id":"tr","name":"🇹🇷 ترکیه","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["ru","ir","iq","gr","sy","bg"],"sea":True,"gdp":906,"pop":85,"army":355},
    {"id":"iq","name":"🇮🇶 عراق","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":10000,"borders":["ir","tr","sa","ae","sy","ku"],"sea":True,"gdp":250,"pop":42,"army":195},
    {"id":"sy","name":"🇸🇾 سوریه","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":3000,"borders":["tr","iq","il","lb","jo"],"sea":True,"gdp":60,"pop":21,"army":170},
    {"id":"ae","name":"🇦🇪 امارات","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":8000,"borders":["sa","iq"],"sea":True,"gdp":500,"pop":10,"army":65},
    {"id":"il","name":"🇮🇱 اسرائیل","cont":"🌏 آسیا","oil":False,"nuclear":True,"oil_b":0,"borders":["eg","sy","lb","jo"],"sea":True,"gdp":525,"pop":9,"army":170},
    {"id":"az","name":"🇦🇿 آذربایجان","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":6000,"borders":["ru","ir","tr","am","ge"],"sea":True,"gdp":78,"pop":10,"army":67},
    {"id":"kz","name":"🇰🇿 قزاقستان","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":7000,"borders":["ru","cn","uz","tm"],"sea":False,"gdp":225,"pop":19,"army":75},
    {"id":"af","name":"🇦🇫 افغانستان","cont":"🌏 آسیا","oil":False,"nuclear":False,"oil_b":0,"borders":["ir","pk","cn","tj","uz","tm"],"sea":False,"gdp":20,"pop":40,"army":300},
    {"id":"mm","name":"🇲🇲 میانمار","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":2000,"borders":["cn","in","th","bd","la"],"sea":True,"gdp":65,"pop":54,"army":406},
    {"id":"th","name":"🇹🇭 تایلند","cont":"🌏 آسیا","oil":False,"nuclear":False,"oil_b":0,"borders":["mm","vn","my","la","kh"],"sea":True,"gdp":544,"pop":72,"army":361},
    {"id":"vn","name":"🇻🇳 ویتنام","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":3000,"borders":["cn","th","la","kh"],"sea":True,"gdp":430,"pop":97,"army":482},
    {"id":"my","name":"🇲🇾 مالزی","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":4000,"borders":["th","id","bn"],"sea":True,"gdp":440,"pop":33,"army":110},
    {"id":"id","name":"🇮🇩 اندونزی","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":5000,"borders":[],"sea":True,"gdp":1400,"pop":277,"army":395},
    {"id":"ph","name":"🇵🇭 فیلیپین","cont":"🌏 آسیا","oil":False,"nuclear":False,"oil_b":0,"borders":[],"sea":True,"gdp":440,"pop":115,"army":125},
    {"id":"bd","name":"🇧🇩 بنگلادش","cont":"🌏 آسیا","oil":False,"nuclear":False,"oil_b":0,"borders":["in","mm"],"sea":True,"gdp":460,"pop":170,"army":160},
    {"id":"us","name":"🇺🇸 آمریکا","cont":"🌎 آمریکا","oil":True,"nuclear":True,"oil_b":10000,"borders":["ca","mx"],"sea":True,"gdp":26000,"pop":335,"army":1385},
    {"id":"gb","name":"🇬🇧 انگلیس","cont":"🌍 اروپا","oil":False,"nuclear":True,"oil_b":0,"borders":[],"sea":True,"gdp":3100,"pop":68,"army":148},
    {"id":"fr","name":"🇫🇷 فرانسه","cont":"🌍 اروپا","oil":False,"nuclear":True,"oil_b":0,"borders":["de","es","it","be","ch","lu","mc"],"sea":True,"gdp":2900,"pop":68,"army":205},
    {"id":"de","name":"🇩🇪 آلمان","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["fr","pl","nl","be","at","ch","cz","dk","lu"],"sea":True,"gdp":4000,"pop":84,"army":183},
    {"id":"it","name":"🇮🇹 ایتالیا","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["fr","at","ch","si","sm","va"],"sea":True,"gdp":2100,"pop":60,"army":170},
    {"id":"es","name":"🇪🇸 اسپانیا","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["fr","pt","ma","ad"],"sea":True,"gdp":1500,"pop":47,"army":122},
    {"id":"pl","name":"🇵🇱 لهستان","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["de","ua","ru","cz","sk","by","lt"],"sea":True,"gdp":700,"pop":38,"army":120},
    {"id":"ua","name":"🇺🇦 اوکراین","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["ru","pl","ro","hu","sk","md","by"],"sea":True,"gdp":160,"pop":44,"army":900},
    {"id":"se","name":"🇸🇪 سوئد","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["no","fi","dk"],"sea":True,"gdp":590,"pop":10,"army":24},
    {"id":"no","name":"🇳🇴 نروژ","cont":"🌍 اروپا","oil":True,"nuclear":False,"oil_b":9000,"borders":["se","ru","fi"],"sea":True,"gdp":540,"pop":5,"army":23},
    {"id":"nl","name":"🇳🇱 هلند","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["de","be"],"sea":True,"gdp":1060,"pop":18,"army":36},
    {"id":"be","name":"🇧🇪 بلژیک","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["fr","de","nl","lu"],"sea":True,"gdp":590,"pop":12,"army":25},
    {"id":"gr","name":"🇬🇷 یونان","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["tr","rs","al","bg","mk"],"sea":True,"gdp":220,"pop":10,"army":141},
    {"id":"ro","name":"🇷🇴 رومانی","cont":"🌍 اروپا","oil":True,"nuclear":False,"oil_b":2000,"borders":["ua","rs","hu","bg","md"],"sea":True,"gdp":290,"pop":19,"army":69},
    {"id":"rs","name":"🇷🇸 صربستان","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["ro","gr","hu","hr","ba","mk","al","me","bg"],"sea":False,"gdp":65,"pop":7,"army":28},
    {"id":"ch","name":"🇨🇭 سوئیس","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["de","fr","it","at","li"],"sea":False,"gdp":810,"pop":9,"army":21},
    {"id":"at","name":"🇦🇹 اتریش","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["de","it","ch","hu","si","sk","cz"],"sea":False,"gdp":480,"pop":9,"army":22},
    {"id":"fi","name":"🇫🇮 فنلاند","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["se","no","ru","ee"],"sea":True,"gdp":280,"pop":6,"army":22},
    {"id":"pt","name":"🇵🇹 پرتغال","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["es"],"sea":True,"gdp":260,"pop":10,"army":26},
    {"id":"hu","name":"🇭🇺 مجارستان","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["at","ro","rs","ua","sk","si","hr"],"sea":False,"gdp":185,"pop":10,"army":26},
    {"id":"br","name":"🇧🇷 برزیل","cont":"🌎 آمریکا","oil":True,"nuclear":False,"oil_b":8000,"borders":["ar","co","ve","pe","bo","py","uy","sr","gy","fr","ve"],"sea":True,"gdp":2100,"pop":215,"army":368},
    {"id":"mx","name":"🇲🇽 مکزیک","cont":"🌎 آمریکا","oil":True,"nuclear":False,"oil_b":6000,"borders":["us","gt","bz"],"sea":True,"gdp":1450,"pop":128,"army":282},
    {"id":"ar","name":"🇦🇷 آرژانتین","cont":"🌎 آمریکا","oil":True,"nuclear":False,"oil_b":4000,"borders":["br","cl","bo","py","uy"],"sea":True,"gdp":640,"pop":46,"army":73},
    {"id":"co","name":"🇨🇴 کلمبیا","cont":"🌎 آمریکا","oil":True,"nuclear":False,"oil_b":3000,"borders":["br","ve","pe","ec","pa"],"sea":True,"gdp":360,"pop":52,"army":295},
    {"id":"ve","name":"🇻🇪 ونزوئلا","cont":"🌎 آمریکا","oil":True,"nuclear":False,"oil_b":9000,"borders":["br","co","gy"],"sea":True,"gdp":95,"pop":29,"army":123},
    {"id":"ca","name":"🇨🇦 کانادا","cont":"🌎 آمریکا","oil":True,"nuclear":False,"oil_b":8000,"borders":["us"],"sea":True,"gdp":2100,"pop":38,"army":71},
    {"id":"cl","name":"🇨🇱 شیلی","cont":"🌎 آمریکا","oil":False,"nuclear":False,"oil_b":0,"borders":["ar","pe","bo"],"sea":True,"gdp":360,"pop":19,"army":80},
    {"id":"cu","name":"🇨🇺 کوبا","cont":"🌎 آمریکا","oil":False,"nuclear":False,"oil_b":0,"borders":[],"sea":True,"gdp":100,"pop":11,"army":49},
    {"id":"pe","name":"🇵🇪 پرو","cont":"🌎 آمریکا","oil":True,"nuclear":False,"oil_b":3000,"borders":["br","cl","co","bo","ec"],"sea":True,"gdp":245,"pop":33,"army":95},
    {"id":"ng","name":"🇳🇬 نیجریه","cont":"🌍 آفریقا","oil":True,"nuclear":False,"oil_b":8000,"borders":["cm","bj","ne","cd"],"sea":True,"gdp":440,"pop":220,"army":135},
    {"id":"za","name":"🇿🇦 آفریقای جنوبی","cont":"🌍 آفریقا","oil":False,"nuclear":False,"oil_b":0,"borders":["zw","mz","bw","na","ls","sz"],"sea":True,"gdp":405,"pop":60,"army":78},
    {"id":"eg","name":"🇪🇬 مصر","cont":"🌍 آفریقا","oil":True,"nuclear":False,"oil_b":4000,"borders":["ly","sd","il","ps"],"sea":True,"gdp":475,"pop":105,"army":440},
    {"id":"ly","name":"🇱🇾 لیبی","cont":"🌍 آفریقا","oil":True,"nuclear":False,"oil_b":6000,"borders":["eg","dz","sd","tn","ne","td","su"],"sea":True,"gdp":45,"pop":7,"army":76},
    {"id":"dz","name":"🇩🇿 الجزایر","cont":"🌍 آفریقا","oil":True,"nuclear":False,"oil_b":5000,"borders":["ma","ly","tn","ml","mr","ne","eh"],"sea":True,"gdp":195,"pop":45,"army":130},
    {"id":"ma","name":"🇲🇦 مراکش","cont":"🌍 آفریقا","oil":False,"nuclear":False,"oil_b":0,"borders":["dz","es","eh"],"sea":True,"gdp":140,"pop":38,"army":196},
    {"id":"et","name":"🇪🇹 اتیوپی","cont":"🌍 آفریقا","oil":False,"nuclear":False,"oil_b":0,"borders":["sd","so","ke","er","dj","ss"],"sea":False,"gdp":128,"pop":123,"army":138},
    {"id":"sd","name":"🇸🇩 سودان","cont":"🌍 آفریقا","oil":True,"nuclear":False,"oil_b":2000,"borders":["eg","ly","et","ss","cf","td","er"],"sea":True,"gdp":36,"pop":46,"army":109},
    {"id":"ke","name":"🇰🇪 کنیا","cont":"🌍 آفریقا","oil":False,"nuclear":False,"oil_b":0,"borders":["et","tz","ug","so","ss"],"sea":True,"gdp":118,"pop":55,"army":24},
    {"id":"gh","name":"🇬🇭 غنا","cont":"🌍 آفریقا","oil":True,"nuclear":False,"oil_b":3000,"borders":["ci","tg","bf"],"sea":True,"gdp":77,"pop":32,"army":15},
    {"id":"ao","name":"🇦🇴 آنگولا","cont":"🌍 آفریقا","oil":True,"nuclear":False,"oil_b":4000,"borders":["cg","zm","na","cd"],"sea":True,"gdp":120,"pop":35,"army":107},
    {"id":"au","name":"🇦🇺 استرالیا","cont":"🌏 اقیانوسیه","oil":True,"nuclear":False,"oil_b":5000,"borders":[],"sea":True,"gdp":1700,"pop":26,"army":59},
    {"id":"nz","name":"🇳🇿 نیوزیلند","cont":"🌏 اقیانوسیه","oil":False,"nuclear":False,"oil_b":0,"borders":[],"sea":True,"gdp":250,"pop":5,"army":9},
]

def get_country(cid): return next((c for c in COUNTRIES if c["id"] == cid), None)
def has_land_border(c1id, c2id):
    c1 = get_country(c1id)
    return bool(c1 and c2id in c1.get("borders", []))
def has_sea(cid):
    c = get_country(cid)
    return bool(c and c.get("sea", False))

# ─── تجهیزات ────────────────────────────────────────────────────
EQUIP = {
    "✈️ هوایی": [
        {"id": "launcher", "name": "🚀 سیستم لانچر", "price": 40000, "oil": 0, "type": "attack", "desc": "الزامی برای شلیک موشک"},
        {"id": "f16", "name": "🛩️ ۸ جنگنده F-16", "price": 55000, "oil": 0, "type": "attack", "power": 80, "desc": "نابودی ۸۰ سرباز یا ۱ تانک"},
        {"id": "f35", "name": "🛩️ ۶ جنگنده F-35", "price": 90000, "oil": 0, "type": "attack", "power": 150, "desc": "نابودی ۱۵۰ سرباز یا ۲ تانک"},
        {"id": "f22", "name": "🛩️ ۴ جنگنده F-22", "price": 140000, "oil": 0, "type": "attack", "power": 220, "desc": "نابودی ۲۲۰ سرباز یا ۳ تانک"},
        {"id": "b52", "name": "💣 ۳ بمب‌افکن B-52", "price": 110000, "oil": 0, "type": "attack", "power": 350, "desc": "نابودی ۵ تانک یا ۳۵۰ سرباز"},
        {"id": "b2", "name": "💣 ۲ بمب‌افکن B-2", "price": 200000, "oil": 0, "type": "attack", "power": 450, "desc": "رادارگریز - نابودی ۸ تانک"},
        {"id": "b21", "name": "💣 B-21 Raider", "price": 350000, "oil": 0, "type": "attack", "power": 700, "desc": "جدیدترین بمب‌افکن استراتژیک آمریکا"},
        {"id": "apache", "name": "🚁 ۸ هلیکوپتر Apache", "price": 35000, "oil": 0, "type": "attack", "power": 180, "desc": "نابودی ۳ تانک یا ۱۸۰ سرباز"},
        {"id": "drone", "name": "🤖 ۲۰ پهپاد بیرقدار", "price": 25000, "oil": 0, "type": "attack", "power": 100, "desc": "نابودی ۱۰۰ سرباز"},
        {"id": "mq9", "name": "🤖 ۵ پهپاد MQ-9", "price": 80000, "oil": 0, "type": "attack", "power": 250, "desc": "پهپاد شکارچی پیشرفته آمریکا"},
        {"id": "shahed", "name": "🤖 ۵۰ شاهد ۱۳۶", "price": 30000, "oil": 0, "type": "attack", "power": 120, "desc": "پهپاد انتحاری - برد ۲۵۰۰km"},
        {"id": "manpad", "name": "🛡️ MANPAD", "price": 30000, "oil": 0, "type": "defense", "desc": "سرنگونی ۲۰ هلیکوپتر"},
        {"id": "s300", "name": "🛡️ سامانه S-300", "price": 120000, "oil": 0, "type": "defense", "desc": "سرنگونی ۲۵ جنگنده"},
        {"id": "s400", "name": "🛡️ سامانه S-400", "price": 200000, "oil": 0, "type": "defense", "desc": "سرنگونی ۴۰ جنگنده"},
        {"id": "s500", "name": "🛡️ سامانه S-500", "price": 350000, "oil": 0, "type": "defense", "desc": "سرنگونی هایپرسونیک و ICBMها"},
    ],
    "🚢 دریایی": [
        {"id": "cargo_ship", "name": "🚢 کشتی باربری", "price": 30000, "oil": 0, "type": "transport", "desc": "امکان معامله دریایی"},
        {"id": "corvette", "name": "⚓ ۳ کوروت رزمی", "price": 40000, "oil": 0, "type": "attack", "power": 60, "desc": "پشتیبانی ساحلی"},
        {"id": "frigate", "name": "🚢 ۲ فریگات", "price": 65000, "oil": 0, "type": "attack", "power": 120, "desc": "نابودی تجهیزات دریایی"},
        {"id": "destroyer", "name": "🚢 ناو اژدرافکن", "price": 100000, "oil": 0, "type": "attack", "power": 200, "desc": "نابودی ناوچه"},
        {"id": "carrier", "name": "🚢 ناو هواپیمابر", "price": 250000, "oil": 0, "type": "attack", "power": 500, "desc": "قدرتمندترین کشتی"},
        {"id": "submarine", "name": "🌊 ۲ زیردریایی", "price": 90000, "oil": 0, "type": "attack", "power": 180, "desc": "حمله مخفیانه"},
        {"id": "nuclear_sub", "name": "🌊☢️ زیردریایی اتمی", "price": 350000, "oil": 0, "type": "attack", "power": 800, "desc": "فقط کشورهای اتمی"},
        {"id": "mine_layer", "name": "⚓ مین‌گذار دریایی", "price": 45000, "oil": 0, "type": "defense", "desc": "مین‌گذاری آبراه‌ها - ضرر دشمن"},
        {"id": "coastal_bat", "name": "🛡️ باتری ساحلی", "price": 80000, "oil": 0, "type": "defense", "desc": "نابودی ۳ فریگات"},
    ],
    "🚀 موشکی": [
        {"id": "grad", "name": "🚀 ۲۰۰ راکت گراد", "price": 15000, "oil": 200, "type": "attack", "power": 80, "desc": "نابودی ۸۰ سرباز"},
        {"id": "tactical", "name": "🚀 ۵۰۰ موشک تاکتیکی", "price": 30000, "oil": 400, "type": "attack", "power": 150, "desc": "نابودی ۱۵۰ سرباز"},
        {"id": "cruise", "name": "🚀 ۵۰ موشک کروز", "price": 80000, "oil": 1200, "type": "attack", "power": 300, "desc": "دقت ۱ متری"},
        {"id": "ballistic", "name": "🚀 ۳۰ موشک بالستیک", "price": 130000, "oil": 2000, "type": "attack", "power": 450, "desc": "برد ۳۰۰۰ کیلومتر"},
        {"id": "precision", "name": "🎯 ۲۰ موشک نقطه‌زن", "price": 200000, "oil": 3500, "type": "attack", "power": 600, "desc": "دقت فوق‌العاله"},
        {"id": "hypersonic", "name": "⚡ ۱۰ موشک هایپرسونیک", "price": 300000, "oil": 6000, "type": "attack", "power": 900, "desc": "ماخ ۱۵ - غیرقابل رهگیری"},
        {"id": "kinzhal", "name": "⚡ کینژال", "price": 250000, "oil": 5000, "type": "attack", "power": 800, "desc": "هایپرسونیک روسی"},
        {"id": "oreshnik", "name": "⚡ اورشنیک", "price": 400000, "oil": 8000, "type": "attack", "power": 1200, "desc": "موشک فوق‌پیشرفته روسی ۲۰۲۴"},
        {"id": "icbm", "name": "🚀🌍 موشک قاره‌پیما", "price": 400000, "oil": 10000, "type": "attack", "power": 2000, "desc": "برد ۱۲۰۰۰ کیلومتر"},
        {"id": "atom", "name": "☢️ بمب اتمی", "price": 8000000, "oil": 0, "type": "attack", "power": 10000, "desc": "فقط کشورهای اتمی ⚠️"},
        {"id": "neutron", "name": "☢️ بمب نوترونی", "price": 5000000, "oil": 0, "type": "attack", "power": 7000, "desc": "فقط کشورهای اتمی ⚠️"},
        {"id": "thermobaric", "name": "🔥 موشک ترموباریک", "price": 120000, "oil": 0, "type": "attack", "power": 500, "desc": "پاک‌کننده سنگرها"},
        {"id": "cram", "name": "🛡️ C-RAM", "price": 45000, "oil": 0, "type": "defense", "desc": "رهگیری راکت ۹۵٪"},
        {"id": "patriot", "name": "🛡️ پاتریوت", "price": 90000, "oil": 0, "type": "defense", "desc": "رهگیری کروز ۸۵٪"},
        {"id": "thaad", "name": "🛡️ THAAD", "price": 180000, "oil": 0, "type": "defense", "desc": "رهگیری بالستیک ۹۰٪"},
        {"id": "iron_dome", "name": "🛡️ گنبد آهنین", "price": 120000, "oil": 0, "type": "defense", "desc": "رهگیری راکت ۹۵٪"},
        {"id": "arrow3", "name": "🛡️ Arrow-3", "price": 250000, "oil": 0, "type": "defense", "desc": "رهگیری هایپرسونیک ۷۰٪"},
    ],
    "🪖 زمینی": [
        {"id": "truck", "name": "🚛 ناوگان کامیون", "price": 20000, "oil": 0, "type": "transport", "desc": "امکان معامله زمینی"},
        {"id": "infantry", "name": "👤 ۵۰۰۰ سرباز پیاده", "price": 50000, "oil": 0, "type": "ground", "power": 100, "desc": "نیروی پایه"},
        {"id": "special", "name": "🪖 ۲۰۰۰ نیروی ویژه", "price": 80000, "oil": 0, "type": "ground", "power": 200, "desc": "آموزش‌دیده"},
        {"id": "marine", "name": "⚓ ۱۰۰۰ تفنگدار", "price": 70000, "oil": 0, "type": "ground", "power": 180, "desc": "عملیات آبی‌خاکی"},
        {"id": "para", "name": "🪂 ۵۰۰ چترباز", "price": 60000, "oil": 0, "type": "ground", "power": 150, "desc": "حمله از هوا"},
        {"id": "rpg", "name": "💥 ۵۰۰ RPG", "price": 30000, "oil": 0, "type": "attack", "power": 80, "desc": "ضد زره"},
        {"id": "javelin", "name": "🎯 جاولین", "price": 60000, "oil": 0, "type": "attack", "power": 200, "desc": "ضد تانک پیشرفته"},
        {"id": "t72", "name": "🚓 ۵۰ تانک T-72", "price": 45000, "oil": 0, "type": "ground", "power": 200, "desc": "تانک قابل اطمینان"},
        {"id": "t90", "name": "🦾 ۳۰ تانک T-90M", "price": 90000, "oil": 0, "type": "ground", "power": 350, "desc": "بهترین تانک روسی"},
        {"id": "abrams", "name": "🦾 ۳۰ تانک Abrams M1A2", "price": 100000, "oil": 0, "type": "ground", "power": 400, "desc": "بهترین تانک غربی"},
        {"id": "merkava", "name": "🛡️ ۲۰ تانک مرکاوا", "price": 120000, "oil": 0, "type": "ground", "power": 450, "desc": "دفاعی‌ترین تانک دنیا"},
        {"id": "howitzer", "name": "🎯 ۱۰ هویتزر", "price": 40000, "oil": 0, "type": "attack", "power": 150, "desc": "برد ۴۰ کیلومتر"},
        {"id": "mlrs", "name": "🚀 MLRS", "price": 70000, "oil": 0, "type": "attack", "power": 250, "desc": "راکت‌انداز چندلوله"},
        {"id": "himars", "name": "🎯 HIMARS", "price": 90000, "oil": 0, "type": "attack", "power": 350, "desc": "دقیق‌ترین توپخانه"},
        {"id": "trench", "name": "🛡️ سنگر", "price": 20000, "oil": 0, "type": "defense", "desc": "کاهش ۳۰٪ تلفات"},
        {"id": "gdef_light", "name": "🛡️ دفاع زمینی سبک", "price": 80000, "oil": 0, "type": "defense", "desc": "کاهش ۶۰٪ تلفات"},
        {"id": "gdef_mid", "name": "🛡️ دفاع زمینی متوسط", "price": 140000, "oil": 0, "type": "defense", "desc": "کاهش ۱۰۰٪ تلفات"},
        {"id": "gdef_heavy", "name": "🛡️ دفاع زمینی سنگین", "price": 220000, "oil": 0, "type": "defense", "desc": "خنثی یک موج کامل"},
        {"id": "landmine", "name": "💣 میدان مین زمینی", "price": 25000, "oil": 0, "type": "defense", "desc": "کاهش ۴۰٪ نیروی حمله‌ور"},
    ],
    "⛏️ اقتصادی": [
        {"id": "iron", "name": "⛏️ معدن آهن", "price": 10000, "oil": 0, "type": "economy", "daily": 4000, "desc": "۴,۰۰۰$/روز"},
        {"id": "copper", "name": "⛏️ معدن مس", "price": 15000, "oil": 0, "type": "economy", "daily": 6000, "desc": "۶,۰۰۰$/روز"},
        {"id": "silver", "name": "⛏️ معدن نقره", "price": 22000, "oil": 0, "type": "economy", "daily": 9000, "desc": "۹,۰۰۰$/روز"},
        {"id": "gold", "name": "⛏️ معدن طلا", "price": 35000, "oil": 0, "type": "economy", "daily": 14000, "desc": "۱۴,۰۰۰$/روز"},
        {"id": "diamond", "name": "⛏️ معدن الماس", "price": 60000, "oil": 0, "type": "economy", "daily": 22000, "desc": "۲۲,۰۰۰$/روز"},
        {"id": "uranium", "name": "☢️ معدن اورانیوم", "price": 80000, "oil": 0, "type": "economy", "daily": 30000, "desc": "فقط اتمی - ۳۰,۰۰۰$/روز"},
        {"id": "lithium", "name": "⚡ معدن لیتیوم", "price": 70000, "oil": 0, "type": "economy", "daily": 25000, "desc": "ماده آینده - ۲۵,۰۰۰$/روز"},
        {"id": "refinery", "name": "🛢️ پالایشگاه نفت", "price": 50000, "oil": 0, "type": "economy", "daily": 0, "oil_daily": 1500, "desc": "فقط نفتی - ۱۵۰۰ بشکه/روز"},
        {"id": "oil_plat", "name": "🛢️ سکوی نفتی", "price": 90000, "oil": 0, "type": "economy", "daily": 0, "oil_daily": 3000, "desc": "فقط نفتی - ۳۰۰۰ بشکه/روز"},
        {"id": "factory", "name": "🏭 کارخانه", "price": 70000, "oil": 0, "type": "economy", "daily": 15000, "desc": "۱۵,۰۰۰$/روز"},
        {"id": "port", "name": "⚓ بندر", "price": 45000, "oil": 0, "type": "economy", "daily": 10000, "desc": "۱۰,۰۰۰$/روز"},
        {"id": "bank", "name": "🏦 بانک مرکزی", "price": 100000, "oil": 0, "type": "economy", "daily": 25000, "desc": "۲۵,۰۰۰$/روز"},
        {"id": "tech_hub", "name": "💻 مرکز فناوری", "price": 150000, "oil": 0, "type": "economy", "daily": 40000, "desc": "درآمد دیجیتال - ۴۰,۰۰۰$/روز"},
        {"id": "tourism", "name": "🏖️ صنعت توریسم", "price": 80000, "oil": 0, "type": "economy", "daily": 18000, "desc": "۱۸,۰۰۰$/روز"},
        {"id": "arms_industry", "name": "🔫 صنایع دفاعی", "price": 200000, "oil": 0, "type": "economy", "daily": 50000, "desc": "فروش تسلیحات - ۵۰,۰۰۰$/روز"},
    ],
    "🖥️ سایبری": [
        {"id": "hack", "name": "💻 واحد هک تهاجمی", "price": 150000, "oil": 0, "type": "attack", "power": 400, "desc": "فلج زیرساخت دشمن"},
        {"id": "stuxnet", "name": "☢️💻 سلاح سایبری پیشرفته", "price": 400000, "oil": 0, "type": "attack", "power": 1000, "desc": "نابودی تأسیسات هسته‌ای دشمن"},
        {"id": "spy", "name": "🔍 جاسوسی سایبری", "price": 100000, "oil": 0, "type": "attack", "power": 200, "desc": "اطلاعات محرمانه"},
        {"id": "antihack", "name": "🛡️ ضدهک", "price": 80000, "oil": 0, "type": "defense", "desc": "دفع هک"},
        {"id": "antivirus", "name": "🛡️ آنتی‌ویروس", "price": 120000, "oil": 0, "type": "defense", "desc": "محافظت دیجیتال"},
        {"id": "satellite", "name": "🛸 ماهواره جاسوسی", "price": 200000, "oil": 0, "type": "attack", "power": 300, "desc": "رصد دشمن"},
        {"id": "radar", "name": "📡 رادار پیشرفته", "price": 90000, "oil": 0, "type": "defense", "desc": "شناسایی از ۵۰۰km"},
        {"id": "jammer", "name": "📡 جمر الکترونیکی", "price": 70000, "oil": 0, "type": "defense", "desc": "۵۰٪ کاهش دقت موشک"},
        {"id": "emp", "name": "💥 بمب EMP", "price": 250000, "oil": 0, "type": "attack", "power": 600, "desc": "فلج الکترونیک"},
        {"id": "deepfake", "name": "🎭 واحد دیپ‌فیک", "price": 120000, "oil": 0, "type": "attack", "power": 150, "desc": "جنگ اطلاعاتی پیشرفته"},
    ],
    "🕵️ جاسوسی": [
        {"id": "cia_network", "name": "🕵️ شبکه CIA", "price": 300000, "oil": 0, "type": "intel", "desc": "جاسوس در دولت دشمن"},
        {"id": "sleeper_agent", "name": "😴 عامل خفته", "price": 200000, "oil": 0, "type": "intel", "desc": "عملیات مخفی طولانی‌مدت"},
        {"id": "saboteur", "name": "💣 خرابکار", "price": 180000, "oil": 0, "type": "intel", "desc": "خرابکاری در زیرساخت"},
        {"id": "hamas_tunnel", "name": "🕳️ شبکه تونل", "price": 150000, "oil": 0, "type": "defense", "desc": "مقاومت در برابر اشغال"},
        {"id": "misinformation", "name": "📰 واحد اطلاعات‌غلط", "price": 100000, "oil": 0, "type": "intel", "desc": "پروپاگاندا در دشمن"},
        {"id": "assassin", "name": "🗡️ تیم ترور", "price": 500000, "oil": 0, "type": "intel", "desc": "حذف رهبران کلیدی دشمن"},
    ],
}

# ─── تحقیق و توسعه ──────────────────────────────────────────────
RESEARCH_TREE = {
    "nuclear_program": {"name": "☢️ برنامه هسته‌ای", "cost": 5000000, "time_days": 30, "effect": "دسترسی به سلاح هسته‌ای", "req": ["uranium"]},
    "hypersonic_tech": {"name": "⚡ فناوری هایپرسونیک", "cost": 3000000, "time_days": 20, "effect": "+50٪ قدرت موشک‌ها", "req": []},
    "stealth_tech": {"name": "🥷 فناوری استلث", "cost": 2000000, "time_days": 15, "effect": "+30٪ شانس حمله موفق", "req": []},
    "ai_warfare": {"name": "🤖 جنگ هوش مصنوعی", "cost": 4000000, "time_days": 25, "effect": "سیستم‌های خودمختار", "req": ["tech_hub"]},
    "space_program": {"name": "🚀 برنامه فضایی", "cost": 6000000, "time_days": 45, "effect": "ماهواره‌های جنگی + درآمد ۱۰۰k/روز", "req": ["satellite"]},
    "bio_weapons": {"name": "🦠 سلاح بیولوژیک", "cost": 8000000, "time_days": 60, "effect": "سلاح کشتار جمعی ⚠️", "req": []},
    "cyber_dominance": {"name": "💻 سلطه سایبری", "cost": 2500000, "time_days": 18, "effect": "+100٪ قدرت سایبری", "req": ["hack"]},
    "economic_miracle": {"name": "📈 معجزه اقتصادی", "cost": 3500000, "time_days": 22, "effect": "+50٪ درآمد روزانه", "req": ["bank", "factory"]},
}

# ─── رویدادهای تصادفی ───────────────────────────────────────────
RANDOM_EVENTS = [
    {"type": "earthquake", "name": "🌍 زلزله ویرانگر", "effect": "budget", "value": -50000, "msg": "زلزله ۷.۸ ریشتری در {country} رخ داد! خسارت: $50,000"},
    {"type": "oil_crisis", "name": "🛢️ بحران نفتی", "effect": "oil_price", "value": 40, "msg": "قیمت نفت ۵۰٪ جهش کرد! هر بشکه ${price}"},
    {"type": "oil_crash", "name": "📉 سقوط نفت", "effect": "oil_price", "value": -30, "msg": "سقوط قیمت نفت! هر بشکه ${price}"},
    {"type": "revolution", "name": "✊ انقلاب مردمی", "effect": "budget_gain", "value": 100000, "msg": "انقلاب در {country}! دولت جدید $100k از ذخایر آزاد کرد"},
    {"type": "pandemic", "name": "🦠 پاندمی جهانی", "effect": "all_income", "value": -0.3, "msg": "پاندمی جهانی! درآمد همه ۳۰٪ کاهش یافت"},
    {"type": "tech_boom", "name": "💻 انفجار فناوری", "effect": "budget_gain", "value": 200000, "msg": "انفجار فناوری در {country}! +$200,000"},
    {"type": "flood", "name": "🌊 سیل مرگبار", "effect": "budget", "value": -30000, "msg": "سیل مرگبار در {country}. خسارت: $30,000"},
    {"type": "gold_rush", "name": "🏅 کشف طلا", "effect": "budget_gain", "value": 150000, "msg": "کشف معادن طلا در {country}! +$150,000"},
    {"type": "coup", "name": "⚔️ کودتا", "effect": "equipment_loss", "value": 0.2, "msg": "کودتا در {country}! ۲۰٪ تجهیزات از دست رفت"},
    {"type": "sanctions_lifted", "name": "🤝 رفع تحریم", "effect": "budget_gain", "value": 300000, "msg": "تحریم‌ها علیه {country} برداشته شد! +$300,000"},
    {"type": "nuclear_accident", "name": "☢️ حادثه هسته‌ای", "effect": "reputation", "value": -50, "msg": "حادثه هسته‌ای در {country}! اعتبار بین‌الملل تنزل یافت"},
    {"type": "climate_disaster", "name": "🔥 فاجعه آب‌وهوایی", "effect": "budget", "value": -80000, "msg": "خشکسالی شدید در {country}. خسارت: $80,000"},
    {"type": "cyber_attack", "name": "💻 حمله سایبری مرموز", "effect": "budget", "value": -60000, "msg": "حمله سایبری به زیرساخت {country}! -$60,000"},
    {"type": "arms_deal", "name": "🔫 معامله تسلیحاتی", "effect": "budget_gain", "value": 250000, "msg": "فروش تسلیحات به متحد! +$250,000"},
    {"type": "world_cup", "name": "⚽ جام جهانی", "effect": "reputation", "value": 30, "msg": "{country} جام جهانی رو برگزار کرد! اعتبار +30"},
]

# ─── دستاوردها ──────────────────────────────────────────────────
ACHIEVEMENTS = {
    "first_blood": {"name": "🩸 اولین خون", "desc": "اولین جنگ", "reward": 50000},
    "conqueror": {"name": "🏴 فاتح", "desc": "اشغال ۳ کشور", "reward": 500000},
    "arms_dealer": {"name": "🔫 تاجر اسلحه", "desc": "۱۰ معامله", "reward": 200000},
    "oil_baron": {"name": "🛢️ پادشاه نفت", "desc": "۱۰۰,۰۰۰ بشکه ذخیره", "reward": 300000},
    "spy_master": {"name": "🕵️ استاد جاسوسی", "desc": "۵ عملیات جاسوسی", "reward": 400000},
    "diplomat": {"name": "🕊️ دیپلمات", "desc": "۳ قرارداد صلح", "reward": 250000},
    "billionaire": {"name": "💰 میلیاردر", "desc": "۱,۰۰۰,۰۰۰,۰۰۰$ بودجه", "reward": 1000000},
    "nuclear_power": {"name": "☢️ قدرت هسته‌ای", "desc": "خرید بمب اتمی", "reward": 0},
    "warmonger": {"name": "⚔️ جنگ‌طلب", "desc": "۱۰ جنگ انجام داده", "reward": 750000},
    "peacekeeper": {"name": "🕊️ صلح‌بان", "desc": "۵ میانجیگری موفق", "reward": 500000},
    "tech_pioneer": {"name": "🔬 پیشگام فناوری", "desc": "۳ تحقیق کامل", "reward": 600000},
    "world_dominator": {"name": "🌍 سلطان جهان", "desc": "اشغال ۱۰ کشور", "reward": 5000000},
    "information_warrior": {"name": "📰 جنگجوی اطلاعات", "desc": "۳ کمپین پروپاگاندا", "reward": 300000},
    "economic_giant": {"name": "📈 غول اقتصادی", "desc": "درآمد ۵۰۰k/روز", "reward": 800000},
    "all_arms": {"name": "🏋️ زرادخانه کامل", "desc": "خرید از همه دسته‌ها", "reward": 400000},
}

# ─── کلمات ممنوع ────────────────────────────────────────────────
PROFANITY = ["کس", "کیر", "کون", "جنده", "مادرجنده", "بیشعور", "خر", "گاو", "الاغ", "احمق", "لاشی", "عوضی", "اشغال", "بی‌ناموس", "ناموس", "fuck", "shit", "bitch", "ass", "dick", "pussy"]

WEAPON_KEYWORDS = {
    "بمب اتم": ["atom"], "اتمی": ["atom", "neutron"], "نوترون": ["neutron"],
    "موشک کروز": ["cruise"], "کروز": ["cruise"], "بالستیک": ["ballistic"],
    "هایپرسونیک": ["hypersonic", "kinzhal", "oreshnik"], "قاره پیما": ["icbm"], "قاره‌پیما": ["icbm"],
    "f35": ["f35"], "f-35": ["f35"], "f22": ["f22"], "f-22": ["f22"],
    "b52": ["b52"], "b-52": ["b52"], "b2": ["b2"], "b21": ["b21"],
    "ناو هواپیمابر": ["carrier"], "زیردریایی": ["submarine", "nuclear_sub"],
    "ابرامز": ["abrams"], "تانک سنگین": ["abrams", "merkava", "t90"],
    "پهپاد": ["drone", "mq9", "shahed"], "بیرقدار": ["drone"], "شاهد": ["shahed"],
    "himars": ["himars"], "هیمارس": ["himars"],
    "s400": ["s400"], "s-400": ["s400"], "s300": ["s300"], "s-300": ["s300"], "s500": ["s500"],
    "گنبد آهنین": ["iron_dome"], "پاتریوت": ["patriot"], "thaad": ["thaad"],
    "هک": ["hack", "stuxnet"], "سایبری": ["hack", "spy", "stuxnet"],
    "ماهواره": ["satellite"], "emp": ["emp"],
    "هلیکوپتر": ["apache"], "اپاچی": ["apache"],
    "grad": ["grad"], "گراد": ["grad"],
    "kinzhal": ["kinzhal"], "کینژال": ["kinzhal"],
    "oreshnik": ["oreshnik"], "اورشنیک": ["oreshnik"],
    "ترموباریک": ["thermobaric"],
    "تونل": ["hamas_tunnel"],
    "ترور": ["assassin"], "ترورسیم": ["assassin"],
}

WAITING_DECL_PHOTO = 1
WAITING_WAR = 2
WAITING_TRADE_DETAIL = 3
WAITING_ALLIANCE_INFO = 4
WAITING_TRADE_OFFER = 5
WAITING_TRADE_REQUEST = 6
WAITING_SPY_OP = 7
WAITING_PROPAGANDA = 8
WAITING_PEACE_MSG = 9
WAITING_SANCTION_MSG = 10
WAITING_RESEARCH = 11

def get_ai():
    return anthropic.Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None

def check_scenario(scenario, equip_list):
    equip_ids = {e["id"] for e in equip_list}
    sc_lower = scenario.lower()
    missing = []
    for kw, needed in WEAPON_KEYWORDS.items():
        if kw in sc_lower:
            if not any(n in equip_ids for n in needed):
                missing.append(kw)
    return missing

# ─── هوش مصنوعی ─────────────────────────────────────────────────
async def ai_check_scenario(scenario, equip_list):
    client = get_ai()
    equip_names = [e['name'] for e in equip_list]
    if not client:
        missing = check_scenario(scenario, equip_list)
        if missing:
            return {"valid": False, "reason": f"تجهیزات زیر رو نداری: {', '.join(missing)}"}
        return {"valid": True, "reason": ""}
    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=300,
            system='تو بررسی‌کننده دقیق سناریوی نظامی هستی. سناریو رو با لیست تجهیزات واقعی بازیکن مقایسه کن. اگه از سلاحی استفاده کرده که ندارد رد کن. فقط JSON: {"valid":true/false,"reason":"دلیل فارسی"}',
            messages=[{"role": "user", "content": f"تجهیزات بازیکن:\n{chr(10).join('- ' + n for n in equip_names)}\n\nسناریو:\n{scenario}"}]
        )
        return json.loads(r.content[0].text.strip().replace("```json", "").replace("```", ""))
    except:
        missing = check_scenario(scenario, equip_list)
        if missing:
            return {"valid": False, "reason": f"تجهیزات زیر رو نداری: {', '.join(missing)}"}
        return {"valid": True, "reason": ""}


async def ai_check_decl(country, text):
    for bad in PROFANITY:
        if bad.lower() in text.lower():
            return {"approved": False, "reason": "بیانیه حاوی کلمه نامناسب است", "edited": text}
    if len(text.strip()) < 30:
        return {"approved": False, "reason": "بیانیه خیلی کوتاه است", "edited": text}
    client = get_ai()
    if not client:
        return {"approved": True, "reason": "تایید", "edited": text}
    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=500,
            system='ناظر بازی جنگ جهانی ۲۶. سختگیرانه رد کن اگه: فحش، توهین، بی‌معنی یا غیررسمی. JSON: {"approved":true/false,"reason":"فارسی","edited":"متن"}',
            messages=[{"role": "user", "content": f"کشور:{country}\n{text}"}]
        )
        return json.loads(r.content[0].text.strip().replace("```json", "").replace("```", ""))
    except:
        return {"approved": True, "reason": "تایید", "edited": text}


async def ai_war_v4(atk_c, def_c, atk_p, def_p, scenario, db):
    """هوش مصنوعی جنگ فوق‌پیشرفته با داستان‌سرایی سینمایی"""
    client = get_ai()

    atk_eq_list = [e for e in atk_p.get('equipment', []) if e.get('type') in ['attack', 'ground', 'intel']]
    def_eq_list = [e for e in def_p.get('equipment', []) if e.get('type') in ['defense']]
    gnd_list = [e for e in atk_eq_list if e.get('type') == 'ground']

    atk_power = sum(e.get('power', 0) for e in atk_eq_list)
    def_power = sum(e.get('power', 50) for e in def_eq_list)

    atk_research = db.get('research', {}).get(str(atk_p.get('user_id', '')), {})
    def_research = db.get('research', {}).get(str(def_p.get('user_id', '')), {})

    world_tension = db.get('world_tension', 30)
    sanctions = db.get('sanctions', {})
    is_sanctioned = atk_c['id'] in sanctions

    alliance_bonus = ""
    alliances = db.get('alliances', {})
    for aid, al in alliances.items():
        members = [al.get('leader')] + al.get('members', [])
        if str(atk_p.get('user_id')) in members:
            ally_count = len(members) - 1
            if ally_count > 0:
                alliance_bonus = f"بونوس اتحاد: +{ally_count * 15}٪ قدرت"

    atk_txt = "\n".join(f"- {e['name']} (قدرت:{e.get('power', 0)}): {e['desc']}" for e in atk_eq_list) or "❌ هیچ"
    def_txt = "\n".join(f"- {e['name']}: {e['desc']}" for e in def_eq_list) or "❌ هیچ"

    if not client:
        winner = "attacker" if atk_power > def_power else "defender"
        return {
            "sat": f"📡 فعالیت نظامی در {atk_c['name']} رصد شد",
            "winner": winner, "atk_loss": 35, "def_loss": 20,
            "story": "نبرد رخ داد.", "territory": "بدون تغییر",
            "civilian": False, "fine": 0, "occupied": False,
            "key_moment": "لحظه تعیین‌کننده: جنگ آغاز شد",
            "aftermath": "وضعیت بعد از جنگ نامعلوم است"
        }

    try:
        prompt = f"""
حمله‌کننده: {atk_c['name']} (GDP: ${atk_c.get('gdp', 0)}B | جمعیت: {atk_c.get('pop', 0)}M | ارتش: {atk_c.get('army', 0)}k)
مدافع: {def_c['name']} (GDP: ${def_c.get('gdp', 0)}B | جمعیت: {def_c.get('pop', 0)}M | ارتش: {def_c.get('army', 0)}k)

تجهیزات حمله (قدرت کل: {atk_power}):
{atk_txt}

تجهیزات دفاع (قدرت کل: {def_power}):
{def_txt}

نیروی زمینی حمله‌کننده: {len(gnd_list)} یگان
تحقیقات حمله‌کننده: {list(atk_research.keys())}
تحقیقات مدافع: {list(def_research.keys())}
تنش جهانی: {world_tension}٪
تحت تحریم: {is_sanctioned}
{alliance_bonus}

سناریوی حمله:
{scenario}
"""

        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=2000,
            system="""تو ژنرال ارشد و داستان‌سرای نظامی بازی World War 26 هستی.

گزارش نبرد باید:
1. کاملاً واقع‌گرایانه و سینمایی باشه
2. از اسم شهرها و مکان‌های واقعی استفاده کنه
3. تعداد دقیق تلفات بده (مثلاً: ۱۲,۴۰۰ کشته، ۳۴,۰۰۰ زخمی، ۵۶۰ اسیر)
4. چه تجهیزاتی دقیقاً استفاده شد و نتیجه هر یک
5. یک لحظه تعیین‌کننده داشته باشه
6. وضعیت بعد از جنگ رو توضیح بده

قوانین مهم:
- اشغال فقط با نیروی زمینی ممکنه
- بمب اتمی = فاجعه انسانی + جریمه سازمان ملل
- تحریم = ۲۰٪ کاهش قدرت حمله
- تحقیقات stealth = +30٪ شانس موفقیت
- تحقیقات hypersonic = +50٪ قدرت موشک
- نبرد دریایی: فقط با کشورهای ساحلی

JSON دقیق (بدون چیز اضافه):
{
  "sat": "خبر ماهواره ۲ جمله هیجان‌انگیز",
  "winner": "attacker یا defender",
  "atk_loss": عدد_درصد,
  "def_loss": عدد_درصد,
  "story": "گزارش کامل ۸-۱۲ جمله با شهرها و تلفات دقیق",
  "key_moment": "لحظه تعیین‌کننده نبرد یک جمله",
  "territory": "وضعیت ارضی دقیق",
  "civilian": true/false,
  "fine": عدد_جریمه,
  "occupied": true/false,
  "aftermath": "وضعیت ۲ جمله بعد از نبرد",
  "war_crime": false,
  "international_reaction": "واکنش جهانی یک جمله"
}""",
            messages=[{"role": "user", "content": prompt}]
        )
        result = json.loads(r.content[0].text.strip().replace("```json", "").replace("```", ""))
        return result
    except Exception as e:
        logger.error(f"AI war error: {e}")
        winner = "attacker" if atk_power > def_power * 0.8 else "defender"
        return {
            "sat": f"📡 درگیری مسلحانه در مرز {atk_c['name']} و {def_c['name']}",
            "winner": winner, "atk_loss": 30, "def_loss": 20,
            "story": f"نیروهای {atk_c['name']} با استفاده از {len(atk_eq_list)} یگان نظامی حمله را آغاز کردند.",
            "key_moment": "لحظه شکستن خط دفاعی دشمن",
            "territory": "تغییر اندک",
            "civilian": False, "fine": 0, "occupied": False,
            "aftermath": "نبرد پایان یافت.", "war_crime": False,
            "international_reaction": "جهان نگران این درگیری است."
        }


async def ai_spy_operation(spy_c, target_c, op_type, spy_p, target_p):
    """هوش مصنوعی عملیات جاسوسی"""
    client = get_ai()
    spy_intel = [e for e in spy_p.get('equipment', []) if e.get('type') == 'intel']
    intel_power = len(spy_intel) * 100

    if not client:
        success = random.random() < 0.6
        return {
            "success": success,
            "story": "عملیات انجام شد.",
            "info_gained": "اطلاعات پایه",
            "damage": 50000 if success else 0
        }

    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=600,
            system="""تو رئیس سازمان اطلاعاتی بازی World War 26 هستی. عملیات جاسوسی رو واقع‌گرایانه تحلیل کن.

JSON:
{
  "success": true/false,
  "story": "گزارش عملیات ۴-۵ جمله جذاب",
  "info_gained": "اطلاعات کشف‌شده",
  "damage": عدد_خسارت_مالی_به_هدف,
  "agent_captured": true/false,
  "cover_blown": true/false
}""",
            messages=[{"role": "user", "content": f"جاسوس: {spy_c['name']} (قدرت اطلاعاتی: {intel_power})\nهدف: {target_c['name']}\nنوع عملیات: {op_type}\nتجهیزات جاسوسی: {[e['name'] for e in spy_intel]}"}]
        )
        return json.loads(r.content[0].text.strip().replace("```json", "").replace("```", ""))
    except:
        success = random.random() < 0.5 + (intel_power / 2000)
        return {
            "success": success,
            "story": f"عوامل {spy_c['name']} وارد خاک {target_c['name']} شدند.",
            "info_gained": "اطلاعات نظامی پایه" if success else "عملیات لو رفت",
            "damage": random.randint(20000, 100000) if success else 0,
            "agent_captured": not success,
            "cover_blown": not success
        }


async def ai_trade_route(from_c, to_c, method, goods):
    client = get_ai()
    if not client:
        return f"مسیر {method} از {from_c} به {to_c}"
    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=200,
            system="متخصص جغرافیای تجاری. مسیر واقعی رو با اسم دریاها/جاده‌ها بنویس. فارسی. ۲-۳ جمله.",
            messages=[{"role": "user", "content": f"مسیر {method} از {from_c} به {to_c} برای {goods}"}]
        )
        return r.content[0].text
    except:
        return f"مسیر {method} از {from_c} به {to_c}"


async def ai_news(db):
    """خبر BBC با هوش مصنوعی پیشرفته"""
    client = get_ai()
    wars = db.get('wars', [])[-5:]
    players = db.get('players', {})
    events = db.get('events', [])[-3:]
    world_tension = db.get('world_tension', 30)
    oil_price = db.get('market', {}).get('oil', 80)

    if not client:
        return "📺 *BBC WW26*\nگزارش امروز آماده نشد."

    try:
        wt = "\n".join(f"- {w['atk']} ⚔️ {w['def']} → برنده: {w['winner']}" for w in wars) or "جنگی نبود"
        et = "\n".join(f"- {e.get('name','رویداد')} در {e.get('country','؟')}" for e in events) or "رویداد خاصی نبود"

        # رنکینگ
        ranking = sorted(players.values(), key=lambda x: x.get('budget', 0) + x.get('oil', 0) * oil_price, reverse=True)[:3]
        rank_txt = "\n".join(f"{i+1}. {get_country(p['country_id'])['name'] if get_country(p['country_id']) else '؟'}" for i, p in enumerate(ranking))

        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=700,
            system="""تو خبرنگار ارشد BBC فارسی هستی که گزارش شبانه بازی World War 26 رو می‌نویسی.
گزارش باید:
- هیجان‌انگیز، سینمایی و خبرنگارانه باشه
- از اسامی کشورها و رویدادهای واقعی بازی استفاده کنه
- یک تحلیل سیاسی داشته باشه
- با یک سوال چالش‌برانگیز تموم بشه
فرمت: Markdown با ایموجی مناسب""",
            messages=[{"role": "user", "content": f"""بازیکنان فعال: {len(players)}
تنش جهانی: {world_tension}٪
قیمت نفت: ${oil_price}/بشکه
جنگ‌های اخیر:\n{wt}
رویدادها:\n{et}
برترین قدرت‌ها:\n{rank_txt}"""}]
        )
        return f"📺 *BBC World War 26 | گزارش شبانه*\n━━━━━━━━━━━━━━━\n{r.content[0].text}"
    except:
        return "📺 BBC WW26 | گزارش امروز"


async def ai_random_event(player, country):
    """رویداد تصادفی با هوش مصنوعی"""
    client = get_ai()
    event = random.choice(RANDOM_EVENTS)

    if not client:
        return event

    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=200,
            system="یک رویداد تصادفی برای بازی جنگ جهانی ۲۶ بساز. فارسی. ۲ جمله جذاب.",
            messages=[{"role": "user", "content": f"رویداد: {event['name']}\nکشور: {country['name']}\nوضعیت اقتصادی: ${player.get('budget', 0):,}"}]
        )
        event['ai_story'] = r.content[0].text
        return event
    except:
        return event


async def ai_propaganda(attacker_c, target_c, message):
    """هوش مصنوعی پروپاگاندا"""
    client = get_ai()
    if not client:
        return {"success": True, "story": "کمپین پروپاگاندا اجرا شد.", "effectiveness": 50}

    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=400,
            system="""تو مشاور ارشد جنگ اطلاعاتی هستی. کمپین پروپاگاندا رو تحلیل کن.
JSON: {"success":true/false,"story":"تحلیل کمپین ۳ جمله","effectiveness":عدد_۰_تا_۱۰۰,"backfire":true/false}""",
            messages=[{"role": "user", "content": f"کشور پروپاگاندیست: {attacker_c['name']}\nهدف: {target_c['name']}\nپیام: {message}"}]
        )
        return json.loads(r.content[0].text.strip().replace("```json", "").replace("```", ""))
    except:
        return {"success": True, "story": "کمپین پروپاگاندا در حال اجرا.", "effectiveness": random.randint(30, 80), "backfire": False}


# ─── توابع کمکی ─────────────────────────────────────────────────
def calc_military_power(player):
    """محاسبه قدرت نظامی کل"""
    eq = player.get('equipment', [])
    return sum(e.get('power', 0) for e in eq if e.get('type') in ['attack', 'ground', 'defense', 'intel'])

def calc_daily_income(player):
    """محاسبه درآمد روزانه"""
    eq = player.get('equipment', [])
    return sum(e.get('daily', 0) for e in eq if e.get('type') == 'economy')

def calc_daily_oil(player):
    """محاسبه نفت روزانه"""
    eq = player.get('equipment', [])
    return sum(e.get('oil_daily', 0) for e in eq if e.get('type') == 'economy')

def get_player_rank(db, uid):
    """رتبه بازیکن"""
    oil_price = db.get('market', {}).get('oil', 80)
    players = db.get('players', {})
    scores = {k: v.get('budget', 0) + v.get('oil', 0) * oil_price for k, v in players.items()}
    sorted_players = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for i, (pid, _) in enumerate(sorted_players):
        if pid == uid:
            return i + 1
    return len(sorted_players)

def check_achievements(player, db, uid):
    """بررسی دستاوردها"""
    new_achievements = []
    player_achievements = db.get('achievements', {}).get(uid, [])

    wars_fought = len([w for w in db.get('wars', []) if w.get('atk_uid') == uid])
    wars_won = len([w for w in db.get('wars', []) if w.get('atk_uid') == uid and w.get('winner_uid') == uid])
    occupied_count = len([k for k, v in db.get('occupied', {}).items() if v == uid])
    trades_done = len([t for t in db.get('trades', []) if uid in [t.get('from'), t.get('to')]])
    spy_ops = len([s for s in db.get('spy_ops', []) if s.get('spy_uid') == uid])
    peace_treaties = len([p for p in db.get('peace_treaties', {}).values() if uid in p.get('parties', [])])

    eq_ids = {e['id'] for e in player.get('equipment', [])}
    eq_cats = {e.get('type') for e in player.get('equipment', [])}

    checks = {
        "first_blood": wars_fought >= 1,
        "conqueror": occupied_count >= 3,
        "arms_dealer": trades_done >= 10,
        "oil_baron": player.get('oil', 0) >= 100000,
        "spy_master": spy_ops >= 5,
        "diplomat": peace_treaties >= 3,
        "billionaire": player.get('budget', 0) >= 1000000000,
        "nuclear_power": 'atom' in eq_ids or 'neutron' in eq_ids,
        "warmonger": wars_fought >= 10,
        "world_dominator": occupied_count >= 10,
        "information_warrior": len([p for p in db.get('propaganda', []) if p.get('uid') == uid]) >= 3,
        "all_arms": len({'attack', 'ground', 'defense', 'intel', 'economy'} & eq_cats) >= 5,
    }

    for ach_id, condition in checks.items():
        if condition and ach_id not in player_achievements:
            new_achievements.append(ach_id)
            player_achievements.append(ach_id)
            player['budget'] = player.get('budget', 0) + ACHIEVEMENTS[ach_id]['reward']

    if new_achievements:
        db.setdefault('achievements', {})[uid] = player_achievements

    return new_achievements


# ─── هندلرهای اصلی ──────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    uid = str(update.effective_user.id)

    if context.args and uid not in db["players"]:
        ref = context.args[0]
        if ref != uid and ref in db["players"] and uid not in db["referrals"]:
            db["players"][ref]["budget"] = db["players"][ref].get("budget", 0) + 20000
            db["referrals"][uid] = ref
            save_db(db)
            try:
                await context.bot.send_message(int(ref), "🎁 *دوست جدید دعوت کردی!*\n💰 +20,000$ پاداش!", parse_mode="Markdown")
            except:
                pass

    p = db["players"].get(uid)

    if p and update.effective_user.id == ADMIN_ID:
        kb = [[InlineKeyboardButton("👑 پنل ادمین", callback_data="admin")],
              [InlineKeyboardButton("📊 وضعیت", callback_data="status")]]
        await update.message.reply_text(f"👑 ادمین خوش اومدی!", reply_markup=InlineKeyboardMarkup(kb))
        return

    if p:
        c = get_country(p["country_id"])
        occ = db.get("occupied", {})
        my_occ = [k for k, v in occ.items() if v == uid]
        rank = get_player_rank(db, uid)
        daily = calc_daily_income(p)
        oil_daily = calc_daily_oil(p)
        mil_power = calc_military_power(p)
        oil_price = db.get('market', {}).get('oil', 80)
        total_wealth = p.get('budget', 0) + p.get('oil', 0) * oil_price

        kb = [
            [InlineKeyboardButton("📊 وضعیت کامل", callback_data="status"),
             InlineKeyboardButton("🛒 فروشگاه", callback_data="shop")],
            [InlineKeyboardButton("📜 بیانیه", callback_data="decl"),
             InlineKeyboardButton("⚔️ جنگ", callback_data="war")],
            [InlineKeyboardButton("🤝 معامله", callback_data="trade_menu"),
             InlineKeyboardButton("🕵️ جاسوسی", callback_data="spy_menu")],
            [InlineKeyboardButton("🤝 دیپلماسی", callback_data="diplomacy"),
             InlineKeyboardButton("🔬 تحقیق و توسعه", callback_data="rd_menu")],
            [InlineKeyboardButton("📰 پروپاگاندا", callback_data="propaganda_menu"),
             InlineKeyboardButton("🏆 رنکینگ", callback_data="ranking")],
            [InlineKeyboardButton("🎖️ دستاوردها", callback_data="achievements"),
             InlineKeyboardButton("🔗 دعوت دوستان", callback_data="ref")],
            [InlineKeyboardButton("🌐 رویدادهای جهانی", callback_data="world_events"),
             InlineKeyboardButton("📖 آموزش", callback_data="tutorial")],
        ]
        if update.effective_user.id == ADMIN_ID:
            kb.append([InlineKeyboardButton("👑 پنل ادمین", callback_data="admin")])

        occ_txt = f"\n🏴 {len(my_occ)} کشور تصرفی" if my_occ else ""
        tension_txt = f"\n⚡ تنش جهانی: {db.get('world_tension', 30)}٪"

        await update.message.reply_text(
            f"🌍 *WORLD WAR 26*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 {update.effective_user.first_name}\n"
            f"🏳️ {c['name'] if c else '?'}\n"
            f"💰 ${p.get('budget', 0):,}\n"
            f"🛢️ {p.get('oil', 0):,} بشکه\n"
            f"💪 قدرت نظامی: {mil_power:,}\n"
            f"📈 ${daily:,}/روز | 🛢️ {oil_daily:,}/روز\n"
            f"🏆 رتبه #{rank} جهانی\n"
            f"💎 ثروت کل: ${total_wealth:,}"
            f"{occ_txt}{tension_txt}\n\n"
            f"📢 {CHANNEL_LINK}",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
        )
    else:
        kb = [[InlineKeyboardButton("🌍 انتخاب کشور و شروع بازی", callback_data="choose")],
              [InlineKeyboardButton("📖 آموزش بازی", callback_data="tutorial")],
              [InlineKeyboardButton("🏆 رنکینگ جهانی", callback_data="ranking")]]
        await update.message.reply_text(
            "🌍⚔️ *WORLD WAR 26* ⚔️🌍\n"
            "━━━━━━━━━━━━━━━\n"
            "🎮 بازی استراتژی ملی تلگرام\n"
            "💣 جنگ • 🕵️ جاسوسی • 🤝 دیپلماسی\n"
            "💰 اقتصاد • 🔬 تحقیق • 📰 پروپاگاندا\n\n"
            "کشورت رو انتخاب کن و به قدرت برس! 🔥\n\n"
            f"📢 {CHANNEL_LINK}",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
        )


async def choose_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    taken = {p["country_id"] for p in db["players"].values()}
    occupied = set(db.get("occupied", {}).keys())

    conts = {}
    for c in COUNTRIES:
        conts.setdefault(c["cont"], []).append(c)

    kb = []
    for cont, cs in conts.items():
        kb.append([InlineKeyboardButton(f"━ {cont} ━", callback_data="noop")])
        row = []
        for c in cs:
            t = c["id"] in taken
            oc = c["id"] in occupied
            props = ("🛢️" if c["oil"] else "") + ("☢️" if c["nuclear"] else "")
            gdp_txt = f"${c.get('gdp', 0)}B"

            if t:
                lbl = f"🔒{c['name'].split(' ', 1)[1]}"
            elif oc:
                lbl = f"🟠{c['name'].split(' ', 1)[1]}"
            else:
                lbl = f"✅{c['name'].split(' ', 1)[1]}{props}"

            row.append(InlineKeyboardButton(lbl, callback_data=f"join_{c['id']}" if not t and not oc else "taken"))
            if len(row) == 2:
                kb.append(row)
                row = []
        if row:
            kb.append(row)

    kb.append([InlineKeyboardButton("🔙", callback_data="back")])
    await q.edit_message_text(
        "🌍 *انتخاب کشور*\n"
        "✅=آزاد 🔒=گرفته 🟠=تصرف‌شده\n"
        "🛢️=نفت ☢️=اتمی",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )


async def join_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cid = q.data.replace("join_", "")
    db = load_db()
    uid = str(update.effective_user.id)

    if uid in db["players"]:
        await q.edit_message_text("❌ قبلاً کشور داری! /start")
        return
    if cid in {p["country_id"] for p in db["players"].values()}:
        await q.edit_message_text("❌ گرفته شده!")
        return

    c = get_country(cid)
    if not c:
        return

    db["players"][uid] = {
        "user_id": uid,
        "username": update.effective_user.username or "?",
        "first_name": update.effective_user.first_name,
        "country_id": cid,
        "budget": START_BUDGET,
        "oil": c["oil_b"],
        "equipment": [],
        "joined_at": datetime.now().isoformat(),
        "last_decl": datetime.now().isoformat(),
        "banned": False,
        "borders": {"air": False, "land": False, "sea": False},
        "reputation": 50,
        "research_done": [],
        "active_research": None,
        "wars_won": 0,
        "wars_lost": 0,
    }
    save_db(db)

    props = []
    if c["oil"]: props.append("🛢️ نفت")
    if c["nuclear"]: props.append("☢️ اتمی")

    await q.edit_message_text(
        f"✅ *{c['name']}* انتخاب شد!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 ${START_BUDGET:,} بودجه اولیه\n"
        f"🛢️ {c['oil_b']:,} بشکه نفت\n"
        f"🌍 {c['cont']}\n"
        f"📊 GDP: ${c.get('gdp', 0)}B\n"
        f"👥 جمعیت: {c.get('pop', 0)}M\n"
        f"💪 ارتش: {c.get('army', 0)}k نفر\n"
        f"{'⚡ ' + ' | '.join(props) if props else '🏳️ کشور معمولی'}\n\n"
        f"بجنگ، تجارت کن، جاسوسی کن! ⚔️",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 شروع بازی", callback_data="back")]]))

    try:
        await context.bot.send_message(ADMIN_ID, f"🔔 {update.effective_user.first_name} → {c['name']}")
    except:
        pass


async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        await q.edit_message_text("❌ /start")
        return

    c = get_country(p["country_id"])
    eq = p.get("equipment", [])
    atk = [e for e in eq if e.get("type") in ["attack", "ground"]]
    defn = [e for e in eq if e.get("type") == "defense"]
    econ = [e for e in eq if e.get("type") == "economy"]
    trans = [e for e in eq if e.get("type") == "transport"]
    intel = [e for e in eq if e.get("type") == "intel"]

    daily = calc_daily_income(p)
    odaily = calc_daily_oil(p)
    mil_power = calc_military_power(p)
    rank = get_player_rank(db, uid)
    oil_price = db.get('market', {}).get('oil', 80)
    total_wealth = p.get('budget', 0) + p.get('oil', 0) * oil_price

    occ = db.get("occupied", {})
    my_occ = [get_country(k) for k, v in occ.items() if v == uid]
    bc = p.get("borders", {"air": False, "land": False, "sea": False})
    research = p.get('research_done', [])
    rep = p.get('reputation', 50)
    rep_emoji = "🟢" if rep >= 70 else "🟡" if rep >= 40 else "🔴"

    sanctions = db.get('sanctions', {})
    is_sanctioned = c['id'] in sanctions if c else False

    txt = (
        f"📊 *وضعیت {c['name']}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 ${p['budget']:,} | 🛢️ {p.get('oil', 0):,} بشکه\n"
        f"💎 ثروت کل: ${total_wealth:,}\n"
        f"📈 ${daily:,}/روز | 🛢️ {odaily:,}/روز\n"
        f"💪 قدرت نظامی: {mil_power:,}\n"
        f"🏆 رتبه جهانی: #{rank}\n"
        f"{rep_emoji} اعتبار: {rep}/100\n"
        f"{'🚫 تحت تحریم!' if is_sanctioned else ''}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🌍 {c.get('cont', '')} | 🛢️{'✅' if c['oil'] else '❌'} | ☢️{'✅' if c['nuclear'] else '❌'}\n"
        f"✈️{'🔒' if bc.get('air') else '✅'} | 🛣️{'🔒' if bc.get('land') else '✅'} | 🌊{'🔒' if bc.get('sea') else '✅'} مرزها\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚔️ حمله ({len(atk)}) | 🛡️ دفاع ({len(defn)}) | 🕵️ اطلاعات ({len(intel)})\n"
        f"⛏️ اقتصادی ({len(econ)}) | 🚛 حمل ({len(trans)})\n"
    )

    if research:
        txt += f"━━━━━━━━━━━━━━━\n🔬 تحقیقات: {', '.join(research)}\n"

    if my_occ:
        txt += f"━━━━━━━━━━━━━━━\n🏴 کشورهای تصرفی ({len(my_occ)}):\n"
        for oc in my_occ:
            if oc:
                txt += f" • {oc['name']}\n"

    kb = [
        [InlineKeyboardButton("📋 جزئیات تجهیزات", callback_data="equip_detail"),
         InlineKeyboardButton("🚧 مرزها", callback_data="borders")],
        [InlineKeyboardButton("🔙", callback_data="back")]
    ]
    await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))


async def show_ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    oil_price = db.get('market', {}).get('oil', 80)
    players = db.get('players', {})

    if not players:
        await q.edit_message_text("🏆 هنوز بازیکنی نیست!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))
        return

    def calc_score(p):
        budget = p.get('budget', 0)
        oil_val = p.get('oil', 0) * oil_price
        mil = calc_military_power(p) * 1000
        occupied = len([k for k, v in db.get('occupied', {}).items() if v == p.get('user_id', '')]) * 500000
        return budget + oil_val + mil + occupied

    ranking = sorted(players.items(), key=lambda x: calc_score(x[1]), reverse=True)

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    txt = "🏆 *رنکینگ جهانی World War 26*\n━━━━━━━━━━━━━━━\n"

    for i, (uid, p) in enumerate(ranking[:10]):
        c = get_country(p.get('country_id', ''))
        score = calc_score(p)
        medal = medals[i] if i < len(medals) else f"{i+1}."
        occ = len([k for k, v in db.get('occupied', {}).items() if v == uid])
        occ_txt = f" 🏴{occ}" if occ > 0 else ""
        txt += f"{medal} {c['name'] if c else '?'}\n"
        txt += f"   💎 ${score:,.0f}{occ_txt}\n"

    world_tension = db.get('world_tension', 30)
    tension_emoji = "🟢" if world_tension < 30 else "🟡" if world_tension < 60 else "🔴"
    txt += f"\n━━━━━━━━━━━━━━━\n{tension_emoji} تنش جهانی: {world_tension}٪\n🛢️ نفت: ${oil_price}/بشکه"

    await q.edit_message_text(txt, parse_mode="Markdown",
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))


async def spy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not GAME_SETTINGS.get("spy", True) and update.effective_user.id != ADMIN_ID:
        await q.edit_message_text("🔒 جاسوسی بسته!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))
        return

    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        await q.edit_message_text("❌ /start")
        return

    intel_eq = [e for e in p.get('equipment', []) if e.get('type') == 'intel']
    intel_power = len(intel_eq) * 100

    kb = [
        [InlineKeyboardButton("🔍 جاسوسی (سرقت اطلاعات)", callback_data="spy_op_intel")],
        [InlineKeyboardButton("💣 خرابکاری (آسیب اقتصادی)", callback_data="spy_op_sabotage")],
        [InlineKeyboardButton("🗡️ ترور رهبر", callback_data="spy_op_assassinate")],
        [InlineKeyboardButton("😴 کاشت عامل نفوذی", callback_data="spy_op_sleeper")],
        [InlineKeyboardButton("📋 تاریخچه عملیات", callback_data="spy_history")],
        [InlineKeyboardButton("🔙", callback_data="back")],
    ]

    txt = (
        f"🕵️ *مرکز عملیات مخفی*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💪 قدرت اطلاعاتی: {intel_power}\n"
        f"🔍 تجهیزات جاسوسی: {len(intel_eq)}\n\n"
        f"⚠️ هر عملیات ریسک لو رفتن داره!\n"
        f"برای قدرت بیشتر از فروشگاه > جاسوسی بخر"
    )

    await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))


async def spy_op_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    op_type = q.data.replace("spy_op_", "")
    context.user_data['spy_op'] = op_type

    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return

    others = {k: v for k, v in db["players"].items() if k != uid and not v.get("banned")}
    if not others:
        await q.edit_message_text("❌ هدفی وجود ندارد!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="spy_menu")]]))
        return

    op_names = {
        "intel": "🔍 جاسوسی",
        "sabotage": "💣 خرابکاری",
        "assassinate": "🗡️ ترور",
        "sleeper": "😴 کاشت عامل"
    }

    kb = []
    for k, v in others.items():
        c = get_country(v["country_id"])
        if c:
            kb.append([InlineKeyboardButton(f"🎯 {c['name']}", callback_data=f"spy_target_{k}")])
    kb.append([InlineKeyboardButton("🔙", callback_data="spy_menu")])

    await q.edit_message_text(
        f"🎯 *{op_names.get(op_type, 'عملیات')}*\n\nهدف رو انتخاب کن:",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )


async def spy_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    target_uid = q.data.replace("spy_target_", "")
    op_type = context.user_data.get('spy_op', 'intel')

    db = load_db()
    uid = str(update.effective_user.id)
    spy_p = db["players"].get(uid)
    target_p = db["players"].get(target_uid)

    if not spy_p or not target_p:
        return

    spy_c = get_country(spy_p["country_id"])
    target_c = get_country(target_p["country_id"])

    # چک کردن تجهیزات
    intel_eq = [e for e in spy_p.get('equipment', []) if e.get('type') == 'intel']
    if not intel_eq:
        await q.edit_message_text(
            "❌ تجهیزات جاسوسی نداری!\nاز فروشگاه > جاسوسی بخر.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛒 فروشگاه", callback_data="shop"), InlineKeyboardButton("🔙", callback_data="spy_menu")]])
        )
        return

    await q.edit_message_text("🕵️ عملیات در حال اجرا...")

    result = await ai_spy_operation(spy_c, target_c, op_type, spy_p, target_p)

    # ثبت عملیات
    db.setdefault('spy_ops', []).append({
        "spy_uid": uid,
        "target_uid": target_uid,
        "op_type": op_type,
        "success": result.get("success"),
        "date": datetime.now().isoformat()
    })

    # اعمال نتیجه
    if result.get("success"):
        damage = result.get("damage", 0)
        if damage > 0 and target_p:
            target_p["budget"] = max(0, target_p.get("budget", 0) - damage)
            db["players"][target_uid] = target_p

        # اطلاع به هدف
        try:
            await context.bot.send_message(
                int(target_uid),
                f"⚠️ *عملیات مخفی کشف شد!*\n\n"
                f"کشوری به شما حمله سایبری/جاسوسی کرد.\n"
                f"💸 خسارت: ${damage:,}",
                parse_mode="Markdown"
            )
        except:
            pass

    # بررسی دستاورد
    new_achs = check_achievements(spy_p, db, uid)
    db["players"][uid] = spy_p
    save_db(db)

    status = "✅ موفق" if result.get("success") else "❌ ناموفق"
    captured = "🚨 عامل دستگیر شد!" if result.get("agent_captured") else ""

    txt = (
        f"🕵️ *نتیجه عملیات*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"وضعیت: {status}\n"
        f"{captured}\n\n"
        f"📋 *گزارش:*\n{result.get('story', '')}\n\n"
        f"📊 *اطلاعات به‌دست‌آمده:*\n{result.get('info_gained', '')}\n"
    )

    if result.get("success") and result.get("damage", 0) > 0:
        txt += f"\n💸 خسارت به دشمن: ${result['damage']:,}"

    if new_achs:
        txt += f"\n\n🎖️ دستاورد جدید: {', '.join(ACHIEVEMENTS[a]['name'] for a in new_achs)}"

    # اطلاع به کانال
    try:
        chan_txt = f"🕵️ *عملیات جاسوسی*\n{spy_c['name']} {'موفق' if result.get('success') else 'ناموفق'} در عملیات علیه {target_c['name']}"
        await context.bot.send_message(CHANNEL_ID, chan_txt, parse_mode="Markdown")
    except:
        pass

    await q.edit_message_text(txt, parse_mode="Markdown",
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پنل", callback_data="back")]]))


async def diplomacy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return

    c = get_country(p["country_id"])

    kb = [
        [InlineKeyboardButton("🕊️ پیشنهاد صلح", callback_data="diplo_peace")],
        [InlineKeyboardButton("🚫 اعلام تحریم", callback_data="diplo_sanction")],
        [InlineKeyboardButton("🤝 پیمان عدم‌تعرض", callback_data="diplo_nonaggression")],
        [InlineKeyboardButton("🆘 کمک بشردوستانه", callback_data="diplo_aid")],
        [InlineKeyboardButton("🏛️ سازمان ملل", callback_data="diplo_un")],
        [InlineKeyboardButton("🔙", callback_data="back")],
    ]

    peace_count = len([k for k, v in db.get("peace_treaties", {}).items() if uid in v.get("parties", [])])
    sanctions_against = [k for k, v in db.get("sanctions", {}).items() if v.get("by") == uid]

    await q.edit_message_text(
        f"🤝 *دیپلماسی {c['name']}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🕊️ قراردادهای صلح: {peace_count}\n"
        f"🚫 تحریم‌های فعال: {len(sanctions_against)}\n"
        f"🌡️ تنش جهانی: {db.get('world_tension', 30)}٪\n\n"
        f"دیپلماسی قوی = قدرت نرم بیشتر!",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )


async def diplo_peace_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)

    others = {k: v for k, v in db["players"].items() if k != uid}
    kb = []
    for k, v in others.items():
        c = get_country(v["country_id"])
        if c:
            kb.append([InlineKeyboardButton(f"🕊️ {c['name']}", callback_data=f"peace_offer_{k}")])
    kb.append([InlineKeyboardButton("🔙", callback_data="diplomacy")])

    await q.edit_message_text("🕊️ *پیشنهاد صلح به:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))


async def peace_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    target_uid = q.data.replace("peace_offer_", "")
    db = load_db()
    uid = str(update.effective_user.id)

    p = db["players"].get(uid)
    target_p = db["players"].get(target_uid)
    if not p or not target_p:
        return

    c = get_country(p["country_id"])
    tc = get_country(target_p["country_id"])

    # ارسال به هدف
    try:
        kb = [[InlineKeyboardButton("✅ قبول", callback_data=f"peace_accept_{uid}"),
               InlineKeyboardButton("❌ رد", callback_data=f"peace_reject_{uid}")]]
        await context.bot.send_message(
            int(target_uid),
            f"🕊️ *پیشنهاد صلح*\n\n"
            f"{c['name']} پیشنهاد صلح داد.\n"
            f"قبول می‌کنی؟",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
        )
        await q.edit_message_text(f"✅ پیشنهاد صلح به {tc['name']} ارسال شد!",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="diplomacy")]]))
    except:
        await q.edit_message_text("❌ خطا در ارسال!")


async def peace_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    proposer_uid = q.data.replace("peace_accept_", "")
    db = load_db()
    uid = str(update.effective_user.id)

    p = db["players"].get(uid)
    proposer_p = db["players"].get(proposer_uid)
    if not p or not proposer_p:
        return

    c = get_country(p["country_id"])
    pc = get_country(proposer_p["country_id"])

    treaty_id = f"peace_{uid}_{proposer_uid}"
    db.setdefault("peace_treaties", {})[treaty_id] = {
        "parties": [uid, proposer_uid],
        "date": datetime.now().isoformat(),
        "countries": [c["id"], pc["id"]]
    }

    # کاهش تنش
    db["world_tension"] = max(0, db.get("world_tension", 30) - 5)
    save_db(db)

    try:
        await context.bot.send_message(int(proposer_uid), f"✅ {c['name']} قرارداد صلح رو قبول کرد! 🕊️")
    except:
        pass

    try:
        await context.bot.send_message(CHANNEL_ID,
                                       f"🕊️ *قرارداد صلح*\n\n{pc['name']} و {c['name']} پیمان صلح امضا کردند!",
                                       parse_mode="Markdown")
    except:
        pass

    await q.edit_message_text("✅ قرارداد صلح امضا شد! 🕊️",
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="diplomacy")]]))


async def diplo_sanction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)

    others = {k: v for k, v in db["players"].items() if k != uid}
    kb = []
    for k, v in others.items():
        c = get_country(v["country_id"])
        if c:
            kb.append([InlineKeyboardButton(f"🚫 {c['name']}", callback_data=f"sanction_{k}")])
    kb.append([InlineKeyboardButton("🔙", callback_data="diplomacy")])

    await q.edit_message_text("🚫 *تحریم علیه:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))


async def sanction_apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    target_uid = q.data.replace("sanction_", "")
    db = load_db()
    uid = str(update.effective_user.id)

    target_p = db["players"].get(target_uid)
    if not target_p:
        return

    tc = get_country(target_p["country_id"])
    p = db["players"].get(uid)
    c = get_country(p["country_id"]) if p else None

    db.setdefault("sanctions", {})[tc["id"]] = {
        "by": uid,
        "date": datetime.now().isoformat(),
        "effect": "20% attack penalty"
    }

    db["world_tension"] = min(100, db.get("world_tension", 30) + 3)
    save_db(db)

    try:
        await context.bot.send_message(int(target_uid),
                                       f"🚫 {c['name'] if c else '؟'} تحریم اعلام کرد! ۲۰٪ کاهش قدرت حمله.")
    except:
        pass

    try:
        await context.bot.send_message(CHANNEL_ID,
                                       f"🚫 *تحریم جدید*\n\n{c['name'] if c else '؟'} کشور {tc['name']} را تحریم کرد!",
                                       parse_mode="Markdown")
    except:
        pass

    await q.edit_message_text(f"✅ تحریم علیه {tc['name']} اعلام شد!",
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="diplomacy")]]))


async def rd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return

    done = p.get('research_done', [])
    active = p.get('active_research')

    kb = []
    for rid, r in RESEARCH_TREE.items():
        if rid not in done:
            req_met = all(any(e['id'] == req for e in p.get('equipment', [])) for req in r.get('req', []))
            status = "✅" if req_met else "🔒"
            kb.append([InlineKeyboardButton(f"{status} {r['name']} - ${r['cost']:,}", callback_data=f"rd_start_{rid}")])
        else:
            kb.append([InlineKeyboardButton(f"✔️ {r['name']} (کامل)", callback_data="noop")])
    kb.append([InlineKeyboardButton("🔙", callback_data="back")])

    active_txt = ""
    if active:
        r = RESEARCH_TREE.get(active['id'])
        if r:
            active_txt = f"\n🔬 *در حال تحقیق:* {r['name']}\n"

    await q.edit_message_text(
        f"🔬 *تحقیق و توسعه*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"تحقیقات کامل: {len(done)}/{len(RESEARCH_TREE)}\n"
        f"{active_txt}\n"
        f"✅=آماده | 🔒=نیاز به پیش‌نیاز",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )


async def rd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    rid = q.data.replace("rd_start_", "")
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)

    if not p:
        return

    r = RESEARCH_TREE.get(rid)
    if not r:
        return

    if rid in p.get('research_done', []):
        await q.answer("قبلاً این رو تحقیق کردی!", show_alert=True)
        return

    if p.get('budget', 0) < r['cost']:
        await q.answer(f"❌ بودجه کم! نیاز: ${r['cost']:,}", show_alert=True)
        return

    # بررسی پیش‌نیاز
    eq_ids = {e['id'] for e in p.get('equipment', [])}
    for req in r.get('req', []):
        if req not in eq_ids:
            await q.answer(f"❌ پیش‌نیاز: {req}", show_alert=True)
            return

    p['budget'] -= r['cost']
    p.setdefault('research_done', []).append(rid)
    p['active_research'] = None
    db["players"][uid] = p
    save_db(db)

    await q.edit_message_text(
        f"🔬 *تحقیق {r['name']} کامل شد!*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"✅ اثر: {r['effect']}\n"
        f"💰 هزینه: ${r['cost']:,}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 تحقیق‌ها", callback_data="rd_menu")]])
    )

    try:
        c = get_country(p['country_id'])
        await context.bot.send_message(CHANNEL_ID,
                                       f"🔬 *پیشرفت علمی*\n{c['name'] if c else '؟'} تحقیقات {r['name']} رو کامل کرد!",
                                       parse_mode="Markdown")
    except:
        pass


async def propaganda_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return

    c = get_country(p["country_id"])

    kb = [
        [InlineKeyboardButton("📣 کمپین ضد دشمن", callback_data="prop_start")],
        [InlineKeyboardButton("📊 تاریخچه کمپین‌ها", callback_data="prop_history")],
        [InlineKeyboardButton("🔙", callback_data="back")],
    ]

    await q.edit_message_text(
        f"📰 *جنگ اطلاعاتی {c['name']}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"پروپاگاندا = تضعیف روحیه دشمن\n"
        f"هزینه: $30,000 برای هر کمپین\n\n"
        f"کمپین موفق:\n"
        f"• کاهش درآمد دشمن ۱۰٪\n"
        f"• افزایش تنش جهانی\n"
        f"• افزایش اعتبار شما",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )


async def prop_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)

    if p.get('budget', 0) < 30000:
        await q.edit_message_text("❌ بودجه کم! نیاز به $30,000",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="propaganda_menu")]]))
        return

    others = {k: v for k, v in db["players"].items() if k != uid}
    kb = []
    for k, v in others.items():
        c = get_country(v["country_id"])
        if c:
            kb.append([InlineKeyboardButton(f"📣 علیه {c['name']}", callback_data=f"prop_target_{k}")])
    kb.append([InlineKeyboardButton("🔙", callback_data="propaganda_menu")])

    await q.edit_message_text("📣 *هدف کمپین پروپاگاندا:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))


async def prop_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    target_uid = q.data.replace("prop_target_", "")
    db = load_db()
    uid = str(update.effective_user.id)

    p = db["players"].get(uid)
    target_p = db["players"].get(target_uid)
    if not p or not target_p:
        return

    c = get_country(p["country_id"])
    tc = get_country(target_p["country_id"])

    # کم کردن هزینه
    p['budget'] -= 30000
    db["players"][uid] = p

    await q.edit_message_text("📰 کمپین پروپاگاندا در حال طراحی...")

    messages = [
        f"اقتصاد فاسد {tc['name']} در آستانه فروپاشی!",
        f"رهبران {tc['name']} مردم خود را فروخته‌اند!",
        f"{tc['name']} در پشت صحنه با تروریست‌ها همکاری می‌کند!",
        f"کودتای خونین در {tc['name']} - دولت در بحران!",
    ]
    prop_msg = random.choice(messages)

    result = await ai_propaganda(c, tc, prop_msg)

    # ثبت
    db.setdefault('propaganda', []).append({
        "uid": uid, "target_uid": target_uid,
        "message": prop_msg, "success": result.get("success"),
        "effectiveness": result.get("effectiveness", 50),
        "date": datetime.now().isoformat()
    })

    # اثر
    if result.get("success") and not result.get("backfire"):
        # کاهش درآمد هدف
        target_p['budget'] = max(0, target_p.get('budget', 0) - 20000)
        db["players"][target_uid] = target_p
        db["world_tension"] = min(100, db.get("world_tension", 30) + 2)
        p['reputation'] = min(100, p.get('reputation', 50) + 5)
        db["players"][uid] = p
    elif result.get("backfire"):
        p['reputation'] = max(0, p.get('reputation', 50) - 10)
        db["players"][uid] = p

    save_db(db)

    backfire_txt = "\n⚠️ پروپاگاندا بومرنگ شد! اعتبار کاهش یافت." if result.get("backfire") else ""

    await q.edit_message_text(
        f"📰 *نتیجه کمپین پروپاگاندا*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{'✅ موفق' if result.get('success') else '❌ ناموفق'}\n"
        f"📊 اثربخشی: {result.get('effectiveness', 0)}٪\n\n"
        f"📋 {result.get('story', '')}"
        f"{backfire_txt}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="propaganda_menu")]])
    )

    try:
        await context.bot.send_message(CHANNEL_ID,
                                       f"📰 *کمپین پروپاگاندا*\n{c['name']} کمپین اطلاعاتی علیه {tc['name']} راه‌اندازی کرد.",
                                       parse_mode="Markdown")
    except:
        pass


async def world_events_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    events = db.get('events', [])[-10:]
    wars = db.get('wars', [])[-5:]
    oil_price = db.get('market', {}).get('oil', 80)
    tension = db.get('world_tension', 30)

    txt = (
        f"🌐 *رویدادهای جهانی*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🌡️ تنش جهانی: {tension}٪\n"
        f"🛢️ قیمت نفت: ${oil_price}/بشکه\n"
        f"━━━━━━━━━━━━━━━\n"
    )

    if events:
        txt += "📅 *رویدادهای اخیر:*\n"
        for e in reversed(events[-5:]):
            txt += f"• {e.get('name', '؟')} در {e.get('country', '؟')}\n"
    else:
        txt += "📭 هیچ رویداد خاصی ثبت نشده\n"

    if wars:
        txt += "\n⚔️ *درگیری‌های اخیر:*\n"
        for w in reversed(wars[-5:]):
            txt += f"• {w['atk']} vs {w['def']} → 🏆 {w['winner']}\n"

    await q.edit_message_text(txt, parse_mode="Markdown",
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))


async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return

    player_achievements = db.get('achievements', {}).get(uid, [])

    txt = "🎖️ *دستاوردها*\n━━━━━━━━━━━━━━━\n"
    for ach_id, ach in ACHIEVEMENTS.items():
        done = ach_id in player_achievements
        status = "✅" if done else "⭕"
        reward = f" | 💰+${ach['reward']:,}" if ach['reward'] > 0 else ""
        txt += f"{status} {ach['name']}\n   📝 {ach['desc']}{reward}\n"

    txt += f"\n━━━━━━━━━━━━━━━\n✅ تکمیل‌شده: {len(player_achievements)}/{len(ACHIEVEMENTS)}"

    await q.edit_message_text(txt, parse_mode="Markdown",
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))


# ─── بخش‌های قبلی (بهبودیافته) ──────────────────────────────────
async def quit_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kb = [[InlineKeyboardButton("✅ بله، خارج میشم",callback_data="quit_confirm"),
           InlineKeyboardButton("❌ نه، برمیگردم",callback_data="back")]]
    await q.edit_message_text(
        "⚠️ *مطمئنی میخوای از بازی خارج بشی؟*\n\n"
        "تمام پیشرفت‌ات از بین میره!\n"
        "بودجه، تجهیزات، کشور - همه حذف میشه!",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def quit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if p:
        c = get_country(p.get("country_id",""))
        del db["players"][uid]
        # حذف از اشغال‌ها
        occ = {k:v for k,v in db.get("occupied",{}).items() if v != uid}
        db["occupied"] = occ
        # حذف از اتحادها
        for aid, al in list(db.get("alliances",{}).items()):
            if al.get("leader") == uid:
                del db["alliances"][aid]
            elif uid in al.get("members",[]):
                al["members"].remove(uid)
        save_db(db)
        try:
            await context.bot.send_message(CHANNEL_ID,
                f"👋 {c['name'] if c else '؟'} از بازی خارج شد.",
                parse_mode="Markdown")
        except: pass
    await q.edit_message_text(
        "👋 *از بازی خارج شدی!*\n\nهر وقت خواستی دوباره /start بزن.",
        parse_mode="Markdown")


async def borders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return
    bc = p.get("borders", {"air": False, "land": False, "sea": False})
    kb = [
        [InlineKeyboardButton(f"✈️ هوایی {'🔒بستن' if not bc.get('air') else '✅بازکردن'}", callback_data="border_air")],
        [InlineKeyboardButton(f"🛣️ زمینی {'🔒بستن' if not bc.get('land') else '✅بازکردن'}", callback_data="border_land")],
        [InlineKeyboardButton(f"🌊 دریایی {'🔒بستن' if not bc.get('sea') else '✅بازکردن'}", callback_data="border_sea")],
        [InlineKeyboardButton("🔙", callback_data="status")],
    ]
    await q.edit_message_text("🚧 *مدیریت مرزها*\n\nبستن مرزها از حملات زمینی/هوایی/دریایی جلوگیری می‌کنه!",
                              parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))


async def toggle_border(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    btype = q.data.replace("border_", "")
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return
    c = get_country(p["country_id"])
    bc = p.setdefault("borders", {"air": False, "land": False, "sea": False})
    bc[btype] = not bc.get(btype, False)
    db["players"][uid] = p
    save_db(db)
    status = "🔒 بسته" if bc[btype] else "✅ باز"
    bnames = {"air": "هوایی", "land": "زمینی", "sea": "دریایی"}
    try:
        await context.bot.send_message(CHANNEL_ID,
                                       f"🚧 {c['name']} مرز {bnames[btype]} را {status} کرد.",
                                       parse_mode="Markdown")
    except:
        pass
    await borders_menu(update, context)


async def shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not GAME_SETTINGS.get("shop", True) and update.effective_user.id != ADMIN_ID:
        await q.edit_message_text("🔒 فروشگاه بسته!",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))
        return
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        await q.edit_message_text("❌ /start")
        return
    oil_price = db.get('market', {}).get('oil', 80)
    kb = [[InlineKeyboardButton(cat, callback_data=f"cat_{cat}")] for cat in EQUIP]
    kb += [[InlineKeyboardButton("📋 لیست کامل", callback_data="fulllist")],
           [InlineKeyboardButton("🔙", callback_data="back")]]
    await q.edit_message_text(
        f"🛒 *فروشگاه تسلیحاتی*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 ${p['budget']:,} | 🛢️ {p.get('oil', 0):,} بشکه\n"
        f"🛢️ قیمت نفت: ${oil_price}/بشکه",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )


async def shop_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cat = q.data.replace("cat_", "")
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return
    eq_ids = {e['id'] for e in p.get('equipment', [])}
    kb = []
    for it in EQUIP.get(cat, []):
        owned = "✔️" if it['id'] in eq_ids else ""
        o = f"+{it['oil']:,}🛢️" if it.get("oil") else ""
        kb.append([InlineKeyboardButton(f"{owned}{it['name']} ${it['price']:,}{o}", callback_data=f"buy_{it['id']}")])
    kb.append([InlineKeyboardButton("🔙", callback_data="shop")])
    await q.edit_message_text(f"🛒 *{cat}*\n💰 ${p['budget']:,} | 🛢️ {p.get('oil', 0):,}",
                              parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    iid = q.data.replace("buy_", "")
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        await q.answer("❌", show_alert=True)
        return
    item = next((it for cat in EQUIP.values() for it in cat if it["id"] == iid), None)
    if not item:
        await q.answer("پیدا نشد!", show_alert=True)
        return
    if p["budget"] < item["price"]:
        await q.answer(f"❌ بودجه کم! ${item['price']:,}", show_alert=True)
        return
    if item.get("oil", 0) and p.get("oil", 0) < item["oil"]:
        await q.answer("❌ نفت کم!", show_alert=True)
        return
    c = get_country(p["country_id"])
    if item["id"] in ["refinery", "oil_plat"] and (not c or not c.get("oil")):
        await q.answer("❌ فقط کشورهای نفتی!", show_alert=True)
        return
    if item["id"] == "uranium" and (not c or not c.get("nuclear")):
        await q.answer("❌ فقط کشورهای اتمی!", show_alert=True)
        return
    if item["id"] in ["atom", "neutron", "nuclear_sub"] and (not c or not c.get("nuclear")):
        await q.answer("☢️ فقط کشورهای اتمی!", show_alert=True)
        return
    p["budget"] -= item["price"]
    if item.get("oil"):
        p["oil"] -= item["oil"]
    p.setdefault("equipment", []).append(item)

    # بررسی دستاورد
    new_achs = check_achievements(p, db, uid)
    db["players"][uid] = p
    save_db(db)

    ach_txt = ""
    if new_achs:
        ach_txt = f"\n🎖️ دستاورد: {', '.join(ACHIEVEMENTS[a]['name'] for a in new_achs)}"

    await q.answer(f"✅ {item['name']} خریداری شد!{ach_txt}", show_alert=bool(new_achs))


async def full_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    txt = "📋 *لیست کامل تجهیزات*\n"
    for cat, items in EQUIP.items():
        txt += f"\n{cat}\n━━━━━━━━━━\n"
        for it in items:
            d = f"📈${it['daily']:,}/روز" if it.get("daily") else ""
            od = f"🛢️{it.get('oil_daily', 0):,}/روز" if it.get("oil_daily") else ""
            pw = f"💪{it.get('power', 0)}" if it.get("power") else ""
            txt += f"• {it['name']}\n  💰${it['price']:,} {d}{od}{pw}\n  📝{it['desc']}\n"
    chunks = [txt[i:i + 3800] for i in range(0, len(txt), 3800)]
    kb = [[InlineKeyboardButton("🔙", callback_data="shop")]]
    await q.edit_message_text(chunks[0], parse_mode="Markdown",
                              reply_markup=InlineKeyboardMarkup(kb) if len(chunks) == 1 else None)
    for ch in chunks[1:]:
        await q.message.reply_text(ch, parse_mode="Markdown")
    if len(chunks) > 1:
        await q.message.reply_text(".", reply_markup=InlineKeyboardMarkup(kb))


# ─── بیانیه ─────────────────────────────────────────────────────
async def decl_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not GAME_SETTINGS.get("decl", True) and update.effective_user.id != ADMIN_ID:
        await q.edit_message_text("🔒 بیانیه بسته!",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))
        return ConversationHandler.END
    db = load_db()
    uid = str(update.effective_user.id)
    if uid not in db["players"]:
        await q.edit_message_text("❌ /start")
        return ConversationHandler.END
    if db["players"][uid].get("banned"):
        await q.edit_message_text("🚫 بن هستید!")
        return ConversationHandler.END
    await q.edit_message_text(
        "📜 *بیانیه رسمی*\n\n"
        "📸 عکس رئیس‌جمهور یا پرچم بفرست\n"
        "✍️ متن بیانیه رو زیر عکس (کپشن) بنویس\n\n"
        "✅ رسمی، مؤدبانه | ❌ بدون فحش",
        parse_mode="Markdown"
    )
    return WAITING_DECL_PHOTO


async def decl_recv_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return ConversationHandler.END
    c = get_country(p["country_id"])
    if not update.message.photo:
        await update.message.reply_text("❌ باید عکس بفرستی با متن زیرش!")
        return WAITING_DECL_PHOTO
    caption = update.message.caption or ""
    if len(caption.strip()) < 20:
        await update.message.reply_text("❌ متن خیلی کوتاهه! دوباره بفرست.")
        return WAITING_DECL_PHOTO
    await update.message.reply_text("⏳ AI بررسی می‌کنه...")
    r = await ai_check_decl(c["name"], caption)
    if r["approved"]:
        now = datetime.now()
        date_str = f"{now.year}/{now.month}/{now.day}"
        alliance_name = ""
        for aid, al in db.get("alliances", {}).items():
            if uid in al.get("members", []) or uid == al.get("leader"):
                alliance_name = al.get("name", "")
                break
        position = f"{c['name']} | {c.get('cont', '')}"
        if alliance_name:
            position += f" | اتحاد {alliance_name}"
        formatted = (
            f"⊱⋅ ──────────────────── ⋅⊰\n\n"
            f"❮ 🎖 ❯ ◈ —⊱ ؛ صادرکننده: {c['name']}\n"
            f"❮ 🗓 ❯ ◈ —⊱ ؛ تاریخ: {date_str}\n"
            f"❮ 📑 ❯ ◈ —⊱ ؛ خطاب به: جهانیان\n"
            f"❮ 📍 ❯ ◈ —⊱ ؛ موقعیت: {position}\n"
            f"❮ 🔒 ❯ ◈ —⊱ ؛ سطح دسترسی: عمومی\n\n"
            f"⊱⋅ ─────────────────── ⋅⊰\n\n"
            f"✍️ متن بیانیه:\n\n"
            f"{r['edited']}\n\n"
            f"⊱⋅ ─────────────────── ⋅⊰\n\n"
            f"🎖️ امضا: دولت {c['name']}\n"
            f"📡 𝗖𝗵𝗮𝗻𝗻𝗲𝗹: {CHANNEL_LINK}\n\n"
            f"⊱⋅ ─────────────────── ⋅⊰"
        )
        db["declarations"].append({"id": len(db["declarations"]) + 1, "user_id": uid, "country": c["name"],
                                    "text": r["edited"], "date": datetime.now().isoformat()})
        db["players"][uid]["last_decl"] = datetime.now().isoformat()
        save_db(db)
        try:
            await context.bot.send_photo(CHANNEL_ID, photo=update.message.photo[-1].file_id, caption=formatted)
            await update.message.reply_text("✅ بیانیه تایید و در کانال منتشر شد!")
        except Exception as e:
            await update.message.reply_text(f"✅ تایید شد - خطای کانال: {e}")
    else:
        await update.message.reply_text(f"❌ رد شد!\n💬 {r['reason']}")
    await update.message.reply_text(".",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پنل", callback_data="back")]]))
    return ConversationHandler.END


async def decl_recv_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ باید عکس بفرستی با متن زیرش (کپشن)!")
    return WAITING_DECL_PHOTO


# ─── جنگ ────────────────────────────────────────────────────────
async def war_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not GAME_SETTINGS.get("war", True) and update.effective_user.id != ADMIN_ID:
        await q.edit_message_text("🔒 جنگ بسته!",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))
        return
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        await q.edit_message_text("❌ /start")
        return
    if p.get("banned"):
        await q.edit_message_text("🚫 بن!")
        return

    atk_eq = [e for e in p.get('equipment', []) if e.get('type') in ['attack', 'ground', 'intel']]
    if not atk_eq:
        await q.edit_message_text(
            "❌ هیچ تجهیز نظامی ندارید!\nاول از فروشگاه بخرید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛒 فروشگاه", callback_data="shop"),
                                               InlineKeyboardButton("🔙", callback_data="back")]]))
        return

    others = {k: v for k, v in db["players"].items() if k != uid and not v.get("banned")}
    if not others:
        await q.edit_message_text("⚔️ بازیکن دیگه‌ای نیست!",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))
        return

    oil_price = db.get('market', {}).get('oil', 80)
    kb = []
    for k, v in others.items():
        c = get_country(v["country_id"])
        if c:
            mil_p = calc_military_power(v)
            score = v.get('budget', 0) + v.get('oil', 0) * oil_price
            kb.append([InlineKeyboardButton(f"⚔️ {c['name']} 💪{mil_p:,} 💰${score:,.0f}",
                                            callback_data=f"atk_{k}")])
    kb.append([InlineKeyboardButton("🔙", callback_data="back")])

    my_power = calc_military_power(p)
    await q.edit_message_text(
        f"⚔️ *اعلام جنگ*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💪 قدرت نظامی شما: {my_power:,}\n\n"
        f"هدف حمله رو انتخاب کن:",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )


async def atk_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    tid = q.data.replace("atk_", "")
    context.user_data["target"] = tid
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    target_p = db["players"].get(tid)
    if not p or not target_p:
        return

    atk_eq = [e for e in p.get('equipment', []) if e.get('type') in ['attack', 'ground', 'intel']]
    def_eq = [e for e in target_p.get('equipment', []) if e.get('type') == 'defense']
    tc = get_country(target_p["country_id"])

    eq_txt = "\n".join(f"• {e['name']} (💪{e.get('power', 0)})" for e in atk_eq)
    def_txt = "\n".join(f"• {e['name']}" for e in def_eq) if def_eq else "بدون پدافند"

    sanctions = db.get('sanctions', {})
    p_c = get_country(p["country_id"])
    sanction_warning = "\n⚠️ این کشور تحت تحریم شماست!" if p_c and p_c['id'] in sanctions else ""

    peace = db.get('peace_treaties', {})
    has_peace = any(uid in t.get('parties', []) and tid in t.get('parties', []) for t in peace.values())
    peace_warning = "\n☮️ قرارداد صلح دارید! حمله ممنوع است!" if has_peace else ""

    await q.edit_message_text(
        f"⚔️ *حمله به {tc['name']}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔫 *تجهیزات شما:*\n{eq_txt}\n\n"
        f"🛡️ *دفاع دشمن:*\n{def_txt}"
        f"{sanction_warning}{peace_warning}\n\n"
        f"⚠️ فقط از تجهیزاتی که داری استفاده کن!\n"
        f"✍️ سناریوی دقیق حمله رو بنویس:",
        parse_mode="Markdown"
    )
    return WAITING_WAR


async def war_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    uid = str(update.effective_user.id)
    tid = context.user_data.get("target")
    atk_p = db["players"].get(uid)
    def_p = db["players"].get(tid)
    if not atk_p or not def_p:
        return ConversationHandler.END

    ac = get_country(atk_p["country_id"])
    dc = get_country(def_p["country_id"])
    scenario = update.message.text

    atk_eq = [e for e in atk_p.get('equipment', []) if e.get('type') in ['attack', 'ground', 'intel']]
    if not atk_eq:
        await update.message.reply_text("❌ هیچ تجهیزی ندارید!",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛒", callback_data="shop")]]))
        return ConversationHandler.END

    # بررسی قرارداد صلح
    peace = db.get('peace_treaties', {})
    has_peace = any(uid in t.get('parties', []) and tid in t.get('parties', []) for t in peace.values())
    if has_peace:
        await update.message.reply_text(
            "☮️ نمیتونی به کشوری که باهاش قرارداد صلح داری حمله کنی!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]])
        )
        return ConversationHandler.END

    missing = check_scenario(scenario, atk_eq)
    if missing:
        await update.message.reply_text(
            f"❌ *سناریو تایید نشد!*\n\n"
            f"این تجهیزات رو نداری:\n🚫 {', '.join(missing)}\n\n"
            f"سناریو رو بر اساس تجهیزاتی که *واقعاً داری* بنویس.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))
        return ConversationHandler.END

    await update.message.reply_text("🔍 AI سناریو را بررسی می‌کند...")
    check = await ai_check_scenario(scenario, atk_eq)
    if not check.get("valid", True):
        await update.message.reply_text(
            f"❌ *سناریو تایید نشد!*\n\n💬 {check.get('reason', '')}\n\n"
            f"سناریو رو بر اساس تجهیزاتی که *واقعاً داری* بنویس.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))
        return ConversationHandler.END

    await update.message.reply_text("⚔️ AI نبرد را تحلیل می‌کند... 🎬")
    r = await ai_war_v4(ac, dc, atk_p, def_p, scenario, db)

    winner = ac["name"] if r["winner"] == "attacker" else dc["name"]
    loser = dc["name"] if r["winner"] == "attacker" else ac["name"]
    winner_uid = uid if r["winner"] == "attacker" else tid

    occ_msg = ""
    if r.get("occupied") and r["winner"] == "attacker":
        db.setdefault("occupied", {})[dc["id"]] = uid
        atk_p["budget"] = atk_p.get("budget", 0) + def_p.get("budget", 0) * 0.5
        atk_p["oil"] = atk_p.get("oil", 0) + def_p.get("oil", 0) * 0.3
        db["players"][uid] = atk_p
        occ_msg = f"\n\n🏴 *{ac['name']} کشور {dc['name']} را اشغال کرد!*"

    un_msg = ""
    if r.get("civilian") and r.get("fine", 0) > 0:
        fine = r["fine"]
        db["players"][uid]["budget"] = db["players"][uid].get("budget", 0) - fine
        un_msg = f"\n\n🏛️ *سازمان ملل:* {ac['name']} ${fine:,} جریمه شد!"
        db["world_tension"] = min(100, db.get("world_tension", 30) + 10)

    # بروزرسانی آمار
    if r["winner"] == "attacker":
        atk_p["wars_won"] = atk_p.get("wars_won", 0) + 1
        def_p["wars_lost"] = def_p.get("wars_lost", 0) + 1
    else:
        def_p["wars_won"] = def_p.get("wars_won", 0) + 1
        atk_p["wars_lost"] = atk_p.get("wars_lost", 0) + 1

    db["world_tension"] = min(100, db.get("world_tension", 30) + 5)

    db["wars"].append({
        "id": len(db["wars"]) + 1,
        "atk": ac["name"], "def": dc["name"],
        "atk_uid": uid, "def_uid": tid,
        "winner": winner, "winner_uid": winner_uid,
        "atk_loss": r["atk_loss"], "def_loss": r["def_loss"],
        "date": datetime.now().isoformat(),
        "scenario": scenario[:100]
    })

    atk_eq_list = [e for e in atk_p.get('equipment', []) if e.get('type') in ['attack', 'ground']]
    def_eq_list = [e for e in def_p.get('equipment', []) if e.get('type') == 'defense']

    # بررسی دستاوردها
    new_achs_atk = check_achievements(atk_p, db, uid)
    new_achs_def = check_achievements(def_p, db, tid)

    db["players"][uid] = atk_p
    db["players"][tid] = def_p
    save_db(db)

    atk_names = [e['name'] for e in atk_eq_list[:3]]
    def_names = [e['name'] for e in def_eq_list[:3]]

    txt = (
        f"📡 *{r.get('sat', '')}*\n\n"
        f"⚔️ *گزارش کامل نبرد*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔴 {ac['name']}\n"
        f"   🔫 {', '.join(atk_names)}{'...' if len(atk_eq_list) > 3 else ''}\n\n"
        f"🔵 {dc['name']}\n"
        f"   🛡️ {', '.join(def_names) if def_names else 'بدون پدافند'}{'...' if len(def_eq_list) > 3 else ''}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"📰 *شرح نبرد:*\n{r['story']}\n\n"
        f"⚡ *لحظه تعیین‌کننده:*\n{r.get('key_moment', '')}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏆 *برنده: {winner}*\n"
        f"💀 *بازنده: {loser}*\n\n"
        f"📉 تلفات {ac['name']}: {r['atk_loss']}٪\n"
        f"📉 تلفات {dc['name']}: {r['def_loss']}٪\n"
        f"📍 {r['territory']}\n"
        f"🌍 {r.get('international_reaction', '')}"
        f"{un_msg}{occ_msg}"
    )

    if r.get('aftermath'):
        txt += f"\n\n🌅 *وضعیت پس از جنگ:*\n{r['aftermath']}"

    if new_achs_atk:
        txt += f"\n\n🎖️ دستاورد: {', '.join(ACHIEVEMENTS[a]['name'] for a in new_achs_atk)}"

    try:
        await context.bot.send_message(CHANNEL_ID, txt, parse_mode="Markdown")
    except:
        pass

    try:
        await context.bot.send_message(
            int(tid),
            f"🚨 *{ac['name']} به شما حمله کرد!*\n\n"
            f"🏆 برنده: {winner}\n\n"
            f"📋 {r['story'][:300]}",
            parse_mode="Markdown"
        )
    except:
        pass

    await update.message.reply_text(txt, parse_mode="Markdown")
    await update.message.reply_text(".",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پنل", callback_data="back")]]))
    return ConversationHandler.END


# ─── معامله ─────────────────────────────────────────────────────
async def trade_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not GAME_SETTINGS.get("trade", True) and update.effective_user.id != ADMIN_ID:
        await q.edit_message_text("🔒 معامله بسته!",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))
        return
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return

    kb = [
        [InlineKeyboardButton("🛢️ فروش نفت", callback_data="trade_oil_sell")],
        [InlineKeyboardButton("🤝 معامله تجهیزات", callback_data="trade_equip")],
        [InlineKeyboardButton("💵 انتقال پول", callback_data="trade_money")],
        [InlineKeyboardButton("📋 تاریخچه", callback_data="trade_history")],
        [InlineKeyboardButton("🔙", callback_data="back")],
    ]
    oil_price = db.get('market', {}).get('oil', 80)
    oil_value = p.get('oil', 0) * oil_price

    await q.edit_message_text(
        f"🤝 *مرکز تجارت*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 ${p['budget']:,}\n"
        f"🛢️ {p.get('oil', 0):,} بشکه (≈${oil_value:,})\n"
        f"📈 قیمت نفت: ${oil_price}/بشکه",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )


async def trade_oil_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return

    if p.get('oil', 0) < 1000:
        await q.edit_message_text("❌ حداقل ۱۰۰۰ بشکه نفت نیاز داری!",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="trade_menu")]]))
        return

    oil_price = db.get('market', {}).get('oil', 80)
    amounts = [1000, 5000, 10000, 50000]
    kb = []
    for amt in amounts:
        if p.get('oil', 0) >= amt:
            income = amt * oil_price
            kb.append([InlineKeyboardButton(f"🛢️ {amt:,} بشکه → ${income:,}", callback_data=f"sell_oil_{amt}")])
    kb.append([InlineKeyboardButton("🔙", callback_data="trade_menu")])

    await q.edit_message_text(
        f"🛢️ *فروش نفت*\n"
        f"قیمت: ${oil_price}/بشکه\n"
        f"موجودی: {p.get('oil', 0):,} بشکه",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )


async def sell_oil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    amount = int(q.data.replace("sell_oil_", ""))
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return

    oil_price = db.get('market', {}).get('oil', 80)
    if p.get('oil', 0) < amount:
        await q.answer("❌ نفت کم!", show_alert=True)
        return

    income = amount * oil_price
    p['oil'] -= amount
    p['budget'] += income
    db["players"][uid] = p
    save_db(db)

    await q.edit_message_text(
        f"✅ *فروش موفق!*\n"
        f"🛢️ {amount:,} بشکه فروخته شد\n"
        f"💰 +${income:,}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="trade_menu")]])
    )


# ─── اتحاد ──────────────────────────────────────────────────────
async def alliance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    if uid not in db["players"]:
        await q.edit_message_text("❌ /start")
        return

    alliances = db.get("alliances", {})
    my_alliance = None
    my_aid = None
    for aid, al in alliances.items():
        if uid == al.get("leader") or uid in al.get("members", []):
            my_alliance = al
            my_aid = aid
            break

    if my_alliance:
        members_txt = ""
        for mid in [my_alliance["leader"]] + my_alliance.get("members", []):
            mp = db["players"].get(mid, {})
            mc = get_country(mp.get("country_id", ""))
            role = "👑 رهبر" if mid == my_alliance["leader"] else "👤 عضو"
            mil_p = calc_military_power(mp)
            members_txt += f"{role}: {mc['name'] if mc else '?'} (💪{mil_p:,})\n"

        kb = []
        if uid == my_alliance["leader"]:
            kb.append([InlineKeyboardButton("📋 درخواست‌ها", callback_data=f"al_requests_{my_aid}")])
            kb.append([InlineKeyboardButton("🗑️ انحلال", callback_data=f"al_dissolve_{my_aid}")])
        else:
            kb.append([InlineKeyboardButton("🚪 خروج", callback_data=f"al_leave_{my_aid}")])
        kb.append([InlineKeyboardButton("🔙", callback_data="back")])

        await q.edit_message_text(
            f"🤝 *اتحاد {my_alliance['name']}*\n"
            f"📣 {my_alliance.get('slogan', '')}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👥 اعضا ({len(my_alliance.get('members', [])) + 1}/4):\n{members_txt}",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
        )
    else:
        kb = [
            [InlineKeyboardButton("➕ ساخت اتحاد", callback_data="al_create")],
            [InlineKeyboardButton("🔍 پیوستن", callback_data="al_join_list")],
            [InlineKeyboardButton("🔙", callback_data="back")],
        ]
        txt = "🤝 *سیستم اتحاد*\n\nهنوز عضو اتحادی نیستی.\n\n"
        if alliances:
            txt += "📋 اتحادهای فعال:\n"
            for aid, al in alliances.items():
                count = len(al.get("members", [])) + 1
                txt += f"• {al['name']} ({count}/4) - {al.get('slogan', '')}\n"
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))


# ─── آموزش ──────────────────────────────────────────────────────
async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    txt = (
        "📖 *آموزش World War 26 v4*\n"
        "━━━━━━━━━━━━━━━\n\n"
        "🎮 *هدف بازی:*\n"
        "قوی‌ترین کشور جهان بشو!\n\n"
        "💰 *اقتصاد:*\n"
        "• از فروشگاه > اقتصادی معدن و کارخانه بخر\n"
        "• نفت رو بفروش\n"
        "• تحقیق اقتصادی = +۵۰٪ درآمد\n\n"
        "⚔️ *جنگ:*\n"
        "• تجهیز بخر، سناریو بنویس\n"
        "• AI نبرد رو تحلیل می‌کنه\n"
        "• قرارداد صلح = جنگ ممنوع\n"
        "• اشغال = ۵۰٪ بودجه دشمن\n\n"
        "🕵️ *جاسوسی:*\n"
        "• سرقت اطلاعات، خرابکاری، ترور\n"
        "• هر چقدر تجهیز جاسوسی بیشتر = موفقیت بیشتر\n\n"
        "🤝 *دیپلماسی:*\n"
        "• صلح، تحریم، اتحاد\n"
        "• قدرت نرم = اعتبار + تنش کمتر\n\n"
        "🔬 *تحقیق:*\n"
        "• برنامه هسته‌ای، هایپرسونیک، فضایی\n"
        "• هر تحقیق مزیت منحصر به فرد\n\n"
        "📰 *پروپاگاندا:*\n"
        "• تضعیف اقتصاد دشمن\n"
        "• ریسک بومرنگ وجود داره!\n\n"
        "🎖️ *دستاوردها:*\n"
        "انجام کارهای خاص = جایزه نقدی!\n\n"
        f"📢 {CHANNEL_LINK}"
    )

    await q.edit_message_text(txt, parse_mode="Markdown",
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))


# ─── پنل ادمین ──────────────────────────────────────────────────
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("❌ دسترسی نداری!", show_alert=True)
        return
    await q.answer()
    db = load_db()
    players = db.get('players', {})
    wars = db.get('wars', [])
    oil_price = db.get('market', {}).get('oil', 80)
    tension = db.get('world_tension', 30)

    kb = [
        [InlineKeyboardButton("📢 اخبار BBC", callback_data="adm_news"),
         InlineKeyboardButton("🎲 رویداد تصادفی", callback_data="adm_event")],
        [InlineKeyboardButton("🔓/🔒 جنگ", callback_data="adm_toggle_war"),
         InlineKeyboardButton("🔓/🔒 فروشگاه", callback_data="adm_toggle_shop")],
        [InlineKeyboardButton("💰 درآمد همه", callback_data="adm_income"),
         InlineKeyboardButton("📊 آمار", callback_data="adm_stats")],
        [InlineKeyboardButton("🛢️ قیمت نفت", callback_data="adm_oil_price"),
         InlineKeyboardButton("⚡ تنش جهانی", callback_data="adm_tension")],
        [InlineKeyboardButton("🔙", callback_data="back")],
    ]

    txt = (
        f"👑 *پنل ادمین*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 بازیکنان: {len(players)}\n"
        f"⚔️ جنگ‌ها: {len(wars)}\n"
        f"🛢️ قیمت نفت: ${oil_price}\n"
        f"⚡ تنش: {tension}٪\n"
        f"🛒 فروشگاه: {'✅' if GAME_SETTINGS['shop'] else '❌'}\n"
        f"⚔️ جنگ: {'✅' if GAME_SETTINGS['war'] else '❌'}"
    )

    await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))


async def adm_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("❌", show_alert=True)
        return
    await q.answer("⏳ در حال تولید...")
    db = load_db()
    news = await ai_news(db)
    try:
        await context.bot.send_message(CHANNEL_ID, news, parse_mode="Markdown")
        await q.edit_message_text("✅ خبر در کانال منتشر شد!",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin")]]))
    except Exception as e:
        await q.edit_message_text(f"❌ خطا: {e}",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin")]]))


async def adm_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("❌", show_alert=True)
        return
    await q.answer("🎲 رویداد تصادفی!")
    db = load_db()
    players = list(db["players"].items())
    if not players:
        await q.edit_message_text("❌ بازیکنی نیست!",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin")]]))
        return

    uid, p = random.choice(players)
    c = get_country(p["country_id"])
    if not c:
        return

    event = await ai_random_event(p, c)

    # اعمال اثر
    msg = event.get('ai_story', event.get('msg', '')).replace('{country}', c['name']).replace('{price}', str(db.get('market', {}).get('oil', 80)))

    if event['effect'] == 'budget':
        p['budget'] = max(0, p.get('budget', 0) + event['value'])
    elif event['effect'] == 'budget_gain':
        p['budget'] = p.get('budget', 0) + event['value']
    elif event['effect'] == 'oil_price':
        new_price = max(20, db.get('market', {}).get('oil', 80) + event['value'])
        db.setdefault('market', {})['oil'] = new_price
    elif event['effect'] == 'reputation':
        p['reputation'] = max(0, min(100, p.get('reputation', 50) + event['value']))

    db["players"][uid] = p
    db.setdefault('events', []).append({
        "name": event['name'], "country": c['name'],
        "date": datetime.now().isoformat()
    })
    save_db(db)

    try:
        await context.bot.send_message(CHANNEL_ID,
                                       f"🌍 *رویداد جهانی*\n\n{event['name']}\n\n{msg}",
                                       parse_mode="Markdown")
        await context.bot.send_message(int(uid),
                                       f"🌍 *رویداد در کشور شما!*\n\n{event['name']}\n\n{msg}",
                                       parse_mode="Markdown")
    except:
        pass

    await q.edit_message_text(f"✅ رویداد اعمال شد: {event['name']}",
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin")]]))


async def adm_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("❌", show_alert=True)
        return
    await q.answer("💰 درآمد توزیع می‌شود...")
    db = load_db()
    oil_price = db.get('market', {}).get('oil', 80)
    count = 0
    for uid, p in db["players"].items():
        if p.get("banned"):
            continue
        daily = calc_daily_income(p)
        oil_daily = calc_daily_oil(p)
        if daily > 0:
            p["budget"] = p.get("budget", 0) + daily
        if oil_daily > 0:
            p["oil"] = p.get("oil", 0) + oil_daily
        db["players"][uid] = p
        count += 1
    save_db(db)
    await q.edit_message_text(f"✅ درآمد روزانه به {count} بازیکن پرداخت شد!",
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin")]]))


async def adm_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("❌", show_alert=True)
        return
    await q.answer()
    db = load_db()
    players = db["players"]
    oil_price = db.get('market', {}).get('oil', 80)
    total_budget = sum(p.get('budget', 0) for p in players.values())
    total_oil = sum(p.get('oil', 0) for p in players.values())
    total_wars = len(db.get('wars', []))
    total_spy = len(db.get('spy_ops', []))
    total_trades = len(db.get('trades', []))

    txt = (
        f"📊 *آمار کلی بازی*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 بازیکنان: {len(players)}\n"
        f"💰 بودجه کل: ${total_budget:,}\n"
        f"🛢️ نفت کل: {total_oil:,} بشکه\n"
        f"⚔️ جنگ‌ها: {total_wars}\n"
        f"🕵️ عملیات جاسوسی: {total_spy}\n"
        f"🤝 معاملات: {total_trades}\n"
        f"⚡ تنش جهانی: {db.get('world_tension', 30)}٪\n"
        f"🛢️ قیمت نفت: ${oil_price}"
    )
    await q.edit_message_text(txt, parse_mode="Markdown",
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin")]]))


async def adm_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("❌", show_alert=True)
        return
    action = q.data.replace("adm_toggle_", "")
    GAME_SETTINGS[action] = not GAME_SETTINGS.get(action, True)
    await q.answer(f"{'✅ فعال' if GAME_SETTINGS[action] else '❌ غیرفعال'}: {action}")
    await admin_panel(update, context)


# ─── ارجاع ──────────────────────────────────────────────────────
async def ref_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = str(update.effective_user.id)
    db = load_db()
    ref_count = sum(1 for v in db.get('referrals', {}).values() if v == uid)
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={uid}"
    await q.edit_message_text(
        f"🔗 *دعوت دوستان*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 به ازای هر دعوت: +$20,000\n"
        f"👥 دوستان دعوت‌شده: {ref_count}\n\n"
        f"🔗 لینک دعوت:\n`{link}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]])
    )


async def equip_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return

    eq = p.get('equipment', [])
    if not eq:
        await q.edit_message_text("❌ هیچ تجهیزی نداری!",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="status")]]))
        return

    txt = "📋 *تجهیزات کامل*\n━━━━━━━━━━━━━━━\n"
    by_type = {}
    for e in eq:
        t = e.get('type', 'other')
        by_type.setdefault(t, []).append(e)

    type_names = {'attack': '⚔️ حمله', 'ground': '🪖 زمینی', 'defense': '🛡️ دفاع',
                  'economy': '📈 اقتصادی', 'transport': '🚛 حمل', 'intel': '🕵️ اطلاعات'}

    for t, items in by_type.items():
        txt += f"\n{type_names.get(t, t)}:\n"
        for e in items:
            txt += f"• {e['name']}"
            if e.get('power'):
                txt += f" 💪{e['power']}"
            if e.get('daily'):
                txt += f" 📈${e['daily']:,}/روز"
            txt += "\n"

    await q.edit_message_text(txt, parse_mode="Markdown",
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="status")]]))


# ─── هندلر بک ───────────────────────────────────────────────────
async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)

    if not p:
        kb = [[InlineKeyboardButton("🌍 انتخاب کشور", callback_data="choose")]]
        await q.edit_message_text("🌍 *WORLD WAR 26*\n\nکشورت رو انتخاب کن!",
                                  parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return

    c = get_country(p["country_id"])
    rank = get_player_rank(db, uid)
    daily = calc_daily_income(p)
    oil_price = db.get('market', {}).get('oil', 80)

    kb = [
        [InlineKeyboardButton("📊 وضعیت", callback_data="status"),
         InlineKeyboardButton("🛒 فروشگاه", callback_data="shop")],
        [InlineKeyboardButton("📜 بیانیه", callback_data="decl"),
         InlineKeyboardButton("⚔️ جنگ", callback_data="war")],
        [InlineKeyboardButton("🤝 معامله", callback_data="trade_menu"),
         InlineKeyboardButton("🕵️ جاسوسی", callback_data="spy_menu")],
        [InlineKeyboardButton("🤝 دیپلماسی", callback_data="diplomacy"),
         InlineKeyboardButton("🔬 تحقیق", callback_data="rd_menu")],
        [InlineKeyboardButton("📰 پروپاگاندا", callback_data="propaganda_menu"),
         InlineKeyboardButton("🏆 رنکینگ", callback_data="ranking")],
        [InlineKeyboardButton("🎖️ دستاوردها", callback_data="achievements"),
         InlineKeyboardButton("🔗 دعوت", callback_data="ref")],
        [InlineKeyboardButton("🌐 رویدادها", callback_data="world_events"),
         InlineKeyboardButton("🤝 اتحاد", callback_data="alliance_menu")],
    ]
    if update.effective_user.id == ADMIN_ID:
        kb.append([InlineKeyboardButton("👑 ادمین", callback_data="admin")])

    await q.edit_message_text(
        f"🌍 *{c['name']}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 ${p['budget']:,} | 🛢️ {p.get('oil', 0):,}\n"
        f"📈 ${daily:,}/روز\n"
        f"🏆 رتبه #{rank}",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )


async def quit_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kb = [[InlineKeyboardButton("✅ بله، خارج می‌شوم", callback_data="quit_confirm"),
           InlineKeyboardButton("❌ نه، برمی‌گردم", callback_data="back")]]
    await q.edit_message_text("⚠️ *مطمئنی می‌خوای از بازی خارج بشی?*\nتمام پیشرفت‌ات حذف می‌شه!",
                              parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))


async def quit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    if uid in db["players"]:
        del db["players"][uid]
        save_db(db)
    await q.edit_message_text("👋 از بازی خارج شدی!\nهر وقت خواستی دوباره /start بزن.")


# ─── اجرا ───────────────────────────────────────────────────────
async def job_daily_news(context):
    """ساعت ۹ صبح - خلاصه روزانه"""
    db = load_db()
    news = await ai_news(db)
    try:
        await context.bot.send_message(CHANNEL_ID, news, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"job_news error: {e}")

async def job_income(context):
    """ساعت ۱۲ ظهر - درآمد روزانه"""
    db = load_db()
    count = 0
    for uid, p in db["players"].items():
        if p.get("banned"): continue
        daily = sum(e.get("daily",0) for e in p.get("equipment",[]) if e.get("type")=="economy")
        oil_d = sum(e.get("oil_daily",0) for e in p.get("equipment",[]) if e.get("type")=="economy")
        if daily > 0: p["budget"] = p.get("budget",0) + daily
        if oil_d > 0: p["oil"] = p.get("oil",0) + oil_d
        db["players"][uid] = p; count += 1
    save_db(db)
    try:
        await context.bot.send_message(CHANNEL_ID,
            f"💰 *درآمد روزانه پرداخت شد!*\n👥 {count} بازیکن دریافت کردند.\n⛏️ معادن و کارخانه‌ها فعال هستند.",
            parse_mode="Markdown")
    except Exception as e:
        logger.error(f"job_income error: {e}")

async def job_random_event(context):
    """ساعت ۱۸ عصر - رویداد تصادفی"""
    db = load_db()
    players = [(k,v) for k,v in db["players"].items() if not v.get("banned")]
    if not players: return
    uid, p = random.choice(players)
    c = get_country(p.get("country_id",""))
    if not c: return
    events = [
        ("🌍 زلزله","budget",-50000),
        ("💻 حمله سایبری","budget",-40000),
        ("🏅 کشف معدن طلا","budget",150000),
        ("📈 رونق اقتصادی","budget",80000),
        ("🛢️ بحران نفتی","oil_price",20),
        ("✊ بحران سیاسی","budget",-30000),
        ("🤝 کمک خارجی","budget",100000),
        ("🌊 سیل","budget",-60000),
    ]
    ev_name, ev_type, ev_val = random.choice(events)
    if ev_type == "budget":
        p["budget"] = max(0, p.get("budget",0) + ev_val)
        db["players"][uid] = p
        msg = f"{ev_name} در {c['name']}! {'+'if ev_val>0 else ''}${ev_val:,}"
    elif ev_type == "oil_price":
        new_p = max(20, db.get("market",{}).get("oil",80) + ev_val)
        db.setdefault("market",{})["oil"] = new_p
        msg = f"{ev_name}! قیمت نفت: ${new_p}/بشکه"
    db.setdefault("events",[]).append({"name":ev_name,"country":c["name"],"date":datetime.now().isoformat()})
    save_db(db)
    try:
        await context.bot.send_message(CHANNEL_ID,
            f"🌍 *رویداد جهانی*\n\n{msg}", parse_mode="Markdown")
        await context.bot.send_message(int(uid),
            f"🌍 *رویداد در کشور شما!*\n{msg}", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"job_event error: {e}")

async def send_update_news(app, version="v5.0"):
    """ارسال پیام آپدیت به همه بازیکنان"""
    db = load_db()
    msg = (
        f"🎉 *بات آپدیت شد! نسخه {version}*\n"
        "━━━━━━━━━━━━━━━\n\n"
        "🆕 *چیزای جدید برای بازیکنان:*\n\n"
        "⏰ *زمان‌بندی خودکار:*\n"
        "• 🕙 ساعت ۹ شب → خلاصه اخبار روزانه\n"
        "• 🕛 ساعت ۱۲ شب → واریز درآمد روزانه\n"
        "• 🕛 ساعت ۱۲ ظهر → رویداد تصادفی\n\n"
        "🛡️ *بهبود بیانیه:*\n"
        "• فیلتر هوشمند - دیگه بیانیه‌های خوب رد نمیشن!\n"
        "• فقط فحش واقعی رد میشه\n\n"
        "⚔️ *بهبود جنگ:*\n"
        "• AI دقیق‌تر تجهیزات رو چک میکنه\n"
        "• تحلیل نبرد واقعی‌تر شد\n\n"
        f"📢 {CHANNEL_LINK}\n"
        "برای شروع: /start"
    )
    count = 0
    for uid, p in db["players"].items():
        if not p.get("banned"):
            try:
                await app.bot.send_message(int(uid), msg, parse_mode="Markdown")
                count += 1
            except: pass
    logger.info(f"Update news sent to {count} players")
    try:
        await app.bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
    except: pass


async def adminhelp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /adminhelp - راهنمای کامل ادمین"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ دسترسی نداری!"); return
    txt = (
        "👑 *راهنمای کامل دستورات ادمین*\n"
        "━━━━━━━━━━━━━━━\n\n"
        "📋 *دستورات اصلی:*\n"
        "/adminhelp - همین راهنما\n"
        "/adm stats - آمار کلی بازی\n"
        "/adm list - لیست همه بازیکنان + ID\n\n"
        "💰 *اقتصاد:*\n"
        "/adm income - واریز درآمد روزانه به همه\n"
        "/adm oil <price> - تغییر قیمت نفت\n"
        "   مثال: /adm oil 120\n"
        "/adm budget <uid> <amount> - تغییر بودجه بازیکن\n"
        "   مثال: /adm budget 123456 +50000\n"
        "   مثال: /adm budget 123456 -20000\n"
        "   مثال: /adm budget 123456 999999\n\n"
        "📰 *اخبار و رویداد:*\n"
        "/adm news - انتشار خبر روزانه در کانال\n"
        "/adm tension <0-100> - تغییر تنش جهانی\n"
        "   مثال: /adm tension 75\n\n"
        "👤 *مدیریت بازیکنان:*\n"
        "/adm ban <uid> - بن یا آنبن بازیکن\n"
        "   مثال: /adm ban 123456789\n"
        "/adm kick <uid> - حذف کامل بازیکن از بازی\n"
        "   مثال: /adm kick 123456789\n"
        "/adm broadcast <پیام> - ارسال پیام به همه بازیکنان\n"
        "   مثال: /adm broadcast سرور امشب ری‌استارت میشه\n\n"
        "🔒 *کنترل بخش‌ها:*\n"
        "/adm toggle <key> - روشن/خاموش کردن هر بخش\n"
        "   🛒 shop - فروشگاه\n"
        "   📜 decl - بیانیه\n"
        "   ⚔️ war - جنگ\n"
        "   🤝 trade - معامله\n"
        "   🤝 alliance - اتحاد\n"
        "   🏴 occupy - اشغال کشور\n"
        "   مثال: /adm toggle war\n\n"
        "━━━━━━━━━━━━━━━\n"
        "⏰ *زمان‌بندی خودکار:*\n"
        "🕙 ۲۱:۰۰ - خلاصه اخبار روزانه\n"
        "🕛 ۰۰:۰۰ - واریز درآمد\n"
        "🕛 ۱۲:۰۰ - رویداد تصادفی (بلای طبیعی و...)"
    )
    await update.message.reply_text(txt, parse_mode="Markdown")


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستورات ادمین: /adm <cmd> [args]"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ دسترسی نداری!"); return
    args = context.args
    if not args:
        await update.message.reply_text(
            "👑 *دستورات ادمین:*\n"
            "/adm income - درآمد همه\n"
            "/adm news - خبر روزانه\n"
            "/adm oil <price> - قیمت نفت (مثال: /adm oil 100)\n"
            "/adm tension <0-100> - تنش جهانی\n"
            "/adm ban <uid> - بن/آنبن بازیکن\n"
            "/adm budget <uid> <+/-amount> - تغییر بودجه\n"
            "/adm kick <uid> - حذف کامل بازیکن\n"
            "/adm broadcast <msg> - پیام به همه\n"
            "/adm toggle <key> - on/off بخش\n"
            "   کلیدها: shop decl war trade alliance occupy\n"
            "/adm stats - آمار کلی\n"
            "/adm list - لیست بازیکنان",
            parse_mode="Markdown"); return
    db = load_db()
    cmd = args[0].lower()

    if cmd == "income":
        count = 0
        for uid, p in db["players"].items():
            if p.get("banned"): continue
            d = sum(e.get("daily",0) for e in p.get("equipment",[]) if e.get("type")=="economy")
            o = sum(e.get("oil_daily",0) for e in p.get("equipment",[]) if e.get("type")=="economy")
            if d: p["budget"] = p.get("budget",0)+d
            if o: p["oil"] = p.get("oil",0)+o
            db["players"][uid] = p; count += 1
        save_db(db)
        await update.message.reply_text(f"✅ درآمد به {count} بازیکن پرداخت شد!")
        try: await context.bot.send_message(CHANNEL_ID, f"💰 *درآمد روزانه پرداخت شد!* 👥 {count} بازیکن", parse_mode="Markdown")
        except: pass

    elif cmd == "news":
        msg = await ai_news(db)
        try: await context.bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
        except: pass
        await update.message.reply_text("✅ خبر منتشر شد!")

    elif cmd == "oil" and len(args) >= 2:
        try:
            price = int(args[1])
            db.setdefault("market",{})["oil"] = price
            save_db(db)
            await update.message.reply_text(f"✅ قیمت نفت: ${price}/بشکه")
            try: await context.bot.send_message(CHANNEL_ID, f"🛢️ *قیمت نفت تغییر کرد: ${price}/بشکه*", parse_mode="Markdown")
            except: pass
        except: await update.message.reply_text("❌ فرمت: /adm oil 100")

    elif cmd == "tension" and len(args) >= 2:
        try:
            t = max(0, min(100, int(args[1])))
            db["world_tension"] = t; save_db(db)
            await update.message.reply_text(f"✅ تنش جهانی: {t}٪")
            try: await context.bot.send_message(CHANNEL_ID, f"⚡ *تنش جهانی: {t}٪*", parse_mode="Markdown")
            except: pass
        except: await update.message.reply_text("❌ فرمت: /adm tension 50")

    elif cmd == "ban" and len(args) >= 2:
        tuid = args[1]
        p = db["players"].get(tuid)
        if p:
            p["banned"] = not p.get("banned",False)
            db["players"][tuid] = p; save_db(db)
            c = get_country(p.get("country_id",""))
            status = "🚫 بن" if p["banned"] else "✅ آنبن"
            await update.message.reply_text(f"{status}: {c['name'] if c else tuid}")
            try:
                await context.bot.send_message(CHANNEL_ID,
                    f"👑 ادمین: {c['name'] if c else '؟'} {status} شد.")
                await context.bot.send_message(int(tuid),
                    "🚫 حساب شما تعلیق شد." if p["banned"] else "✅ تعلیق حساب شما برداشته شد.")
            except: pass
        else: await update.message.reply_text("❌ بازیکن پیدا نشد!")

    elif cmd == "budget" and len(args) >= 3:
        tuid = args[1]; amt_s = args[2]
        p = db["players"].get(tuid)
        if p:
            try:
                if amt_s.startswith("+"): p["budget"] = p.get("budget",0)+int(amt_s[1:])
                elif amt_s.startswith("-"): p["budget"] = max(0,p.get("budget",0)-int(amt_s[1:]))
                else: p["budget"] = int(amt_s)
                db["players"][tuid] = p; save_db(db)
                c = get_country(p.get("country_id",""))
                await update.message.reply_text(f"✅ بودجه {c['name'] if c else tuid}: ${p['budget']:,}")
                try: await context.bot.send_message(int(tuid), f"💰 ادمین بودجه شما رو تغییر داد: {amt_s}")
                except: pass
                try: await context.bot.send_message(CHANNEL_ID, f"👑 ادمین: بودجه {c['name'] if c else '؟'} → {amt_s}", parse_mode="Markdown")
                except: pass
            except: await update.message.reply_text("❌ فرمت: /adm budget 123456 +50000")
        else: await update.message.reply_text("❌ پیدا نشد!")

    elif cmd == "kick" and len(args) >= 2:
        tuid = args[1]
        p = db["players"].get(tuid)
        if p:
            c = get_country(p.get("country_id",""))
            del db["players"][tuid]; save_db(db)
            await update.message.reply_text(f"✅ {c['name'] if c else tuid} حذف شد!")
            try: await context.bot.send_message(int(tuid), "⚠️ کشور شما توسط ادمین ریست شد.")
            except: pass
            try: await context.bot.send_message(CHANNEL_ID, f"👑 ادمین: {c['name'] if c else '؟'} از بازی حذف شد.")
            except: pass
        else: await update.message.reply_text("❌ پیدا نشد!")

    elif cmd == "toggle" and len(args) >= 2:
        key = args[1]
        if key in GAME_SETTINGS:
            GAME_SETTINGS[key] = not GAME_SETTINGS[key]
            status = "✅ فعال" if GAME_SETTINGS[key] else "❌ غیرفعال"
            save_db(db)
            await update.message.reply_text(f"{status}: {key}")
            try: await context.bot.send_message(CHANNEL_ID, f"👑 ادمین: بخش «{key}» {status} شد.")
            except: pass
        else: await update.message.reply_text(f"❌ کلید نامعتبر! گزینه‌ها: {list(GAME_SETTINGS.keys())}")

    elif cmd == "broadcast" and len(args) >= 2:
        msg = " ".join(args[1:])
        count = 0
        for uid, p in db["players"].items():
            if not p.get("banned"):
                try: await context.bot.send_message(int(uid), f"📢 *پیام ادمین:*\n\n{msg}", parse_mode="Markdown"); count += 1
                except: pass
        await update.message.reply_text(f"✅ پیام به {count} نفر ارسال شد!")
        try: await context.bot.send_message(CHANNEL_ID, f"📢 *اطلاعیه:*\n{msg}", parse_mode="Markdown")
        except: pass

    elif cmd == "stats":
        players = db["players"]
        op = db.get("market",{}).get("oil",80)
        tb = sum(p.get("budget",0) for p in players.values())
        txt = (f"📊 *آمار کلی*\n"
               f"👥 بازیکنان: {len(players)}\n"
               f"⚔️ جنگ‌ها: {len(db.get('wars',[]))}\n"
               f"💰 بودجه کل: ${tb:,}\n"
               f"🏴 اشغال‌ها: {len(db.get('occupied',{}))}\n"
               f"🛢️ نفت: ${op}\n"
               f"⚡ تنش: {db.get('world_tension',30)}٪")
        await update.message.reply_text(txt, parse_mode="Markdown")

    elif cmd == "list":
        players = db["players"]
        op = db.get("market",{}).get("oil",80)
        txt = "👥 *بازیکنان:*\n"
        for uid, p in players.items():
            c = get_country(p.get("country_id",""))
            banned = "🚫" if p.get("banned") else ""
            txt += f"{banned}{c['name'] if c else '?'} | ${p.get('budget',0):,} | ID:{uid}\n"
        await update.message.reply_text(txt or "هیچ‌کس نیست!", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ دستور نامعتبر! /adm برای راهنما")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_decl = ConversationHandler(
        entry_points=[CallbackQueryHandler(decl_start, pattern="^decl$")],
        states={WAITING_DECL_PHOTO: [
            MessageHandler(filters.PHOTO, decl_recv_photo),
            MessageHandler(filters.TEXT & ~filters.COMMAND, decl_recv_text),
        ]},
        fallbacks=[CommandHandler("start", start)],
    )

    conv_war = ConversationHandler(
        entry_points=[CallbackQueryHandler(atk_target, pattern="^atk_")],
        states={WAITING_WAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, war_recv)]},
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adm", admin_cmd))
    app.add_handler(CommandHandler("adminhelp", adminhelp_cmd))
    app.add_handler(conv_decl)
    app.add_handler(conv_war)

    # ناوبری اصلی
    app.add_handler(CallbackQueryHandler(back_handler, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(choose_country, pattern="^choose$"))
    app.add_handler(CallbackQueryHandler(join_country, pattern="^join_"))
    app.add_handler(CallbackQueryHandler(show_status, pattern="^status$"))
    app.add_handler(CallbackQueryHandler(equip_detail, pattern="^equip_detail$"))
    app.add_handler(CallbackQueryHandler(show_ranking, pattern="^ranking$"))
    app.add_handler(CallbackQueryHandler(show_achievements, pattern="^achievements$"))
    app.add_handler(CallbackQueryHandler(world_events_show, pattern="^world_events$"))
    app.add_handler(CallbackQueryHandler(tutorial, pattern="^tutorial$"))
    app.add_handler(CallbackQueryHandler(ref_menu, pattern="^ref$"))
    app.add_handler(CallbackQueryHandler(quit_game, pattern="^quit$"))
    app.add_handler(CallbackQueryHandler(quit_confirm, pattern="^quit_confirm$"))

    # فروشگاه
    app.add_handler(CallbackQueryHandler(shop_menu, pattern="^shop$"))
    app.add_handler(CallbackQueryHandler(shop_cat, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(buy, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(full_list, pattern="^fulllist$"))

    # مرزها
    app.add_handler(CallbackQueryHandler(borders_menu, pattern="^borders$"))
    app.add_handler(CallbackQueryHandler(toggle_border, pattern="^border_"))

    # جنگ
    app.add_handler(CallbackQueryHandler(war_menu, pattern="^war$"))

    # معامله
    app.add_handler(CallbackQueryHandler(trade_menu, pattern="^trade_menu$"))
    app.add_handler(CallbackQueryHandler(trade_oil_sell, pattern="^trade_oil_sell$"))
    app.add_handler(CallbackQueryHandler(sell_oil, pattern="^sell_oil_"))

    # جاسوسی
    app.add_handler(CallbackQueryHandler(spy_menu, pattern="^spy_menu$"))
    app.add_handler(CallbackQueryHandler(spy_op_start, pattern="^spy_op_"))
    app.add_handler(CallbackQueryHandler(spy_execute, pattern="^spy_target_"))

    # دیپلماسی
    app.add_handler(CallbackQueryHandler(diplomacy_menu, pattern="^diplomacy$"))
    app.add_handler(CallbackQueryHandler(diplo_peace_start, pattern="^diplo_peace$"))
    app.add_handler(CallbackQueryHandler(peace_offer, pattern="^peace_offer_"))
    app.add_handler(CallbackQueryHandler(peace_accept, pattern="^peace_accept_"))
    app.add_handler(CallbackQueryHandler(diplo_sanction, pattern="^diplo_sanction$"))
    app.add_handler(CallbackQueryHandler(sanction_apply, pattern="^sanction_"))

    # تحقیق
    app.add_handler(CallbackQueryHandler(rd_menu, pattern="^rd_menu$"))
    app.add_handler(CallbackQueryHandler(rd_start, pattern="^rd_start_"))

    # پروپاگاندا
    app.add_handler(CallbackQueryHandler(propaganda_menu, pattern="^propaganda_menu$"))
    app.add_handler(CallbackQueryHandler(prop_start, pattern="^prop_start$"))
    app.add_handler(CallbackQueryHandler(prop_execute, pattern="^prop_target_"))

    # اتحاد
    app.add_handler(CallbackQueryHandler(alliance_menu, pattern="^alliance_menu$"))

    # ادمین
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin$"))
    app.add_handler(CallbackQueryHandler(adm_news, pattern="^adm_news$"))
    app.add_handler(CallbackQueryHandler(adm_event, pattern="^adm_event$"))
    app.add_handler(CallbackQueryHandler(adm_income, pattern="^adm_income$"))
    app.add_handler(CallbackQueryHandler(adm_stats, pattern="^adm_stats$"))
    app.add_handler(CallbackQueryHandler(adm_toggle, pattern="^adm_toggle_"))

    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern="^(noop|taken)$"))

    # ── زمان‌بندی خودکار ──
    jq = app.job_queue
    if jq:
        from datetime import time as t
        # ۹ شب (۲۱:۰۰) - خلاصه اخبار روزانه
        jq.run_daily(job_daily_news, time=t(hour=21, minute=0))
        # ۱۲ شب (۰۰:۰۰) - واریز درآمد
        jq.run_daily(job_income, time=t(hour=0, minute=0))
        # ۱۲ ظهر (۱۲:۰۰) - رویداد تصادفی / بلای طبیعی
        jq.run_daily(job_random_event, time=t(hour=12, minute=0))
        logger.info("✅ Jobs: 21:00 news | 00:00 income | 12:00 event")
    
    # ارسال پیام آپدیت به بازیکنان بعد از ۵ ثانیه
    async def on_startup(app2):
        import asyncio
        await asyncio.sleep(5)
        await send_update_news(app2)
    
    app.post_init = on_startup

    logger.info("🌍 WW26 Bot v4.0 FINAL Started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
