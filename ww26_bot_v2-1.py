"""
🌍 WORLD WAR 26 - Telegram Bot v2.0
"""
import logging, json, os
from datetime import datetime, time
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler)

BOT_TOKEN = os.environ.get("BOT_TOKEN","")
CHANNEL_ID = os.environ.get("CHANNEL_ID","")
ADMIN_ID = int(os.environ.get("ADMIN_ID","8441499331"))
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DB_FILE = "ww26.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE,"r",encoding="utf-8") as f: return json.load(f)
    return {"players":{},"declarations":[],"wars":[],"referrals":{},"last_income":"","last_news":""}

def save_db(d):
    with open(DB_FILE,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)

COUNTRIES = [
    # آسیا
    {"id":"cn","name":"🇨🇳 چین","cont":"🌏 آسیا","oil":False,"nuclear":True,"budget":500000,"oil_b":0},
    {"id":"ru","name":"🇷🇺 روسیه","cont":"🌏 آسیا/اروپا","oil":True,"nuclear":True,"budget":480000,"oil_b":15000},
    {"id":"ir","name":"🇮🇷 ایران","cont":"🌏 آسیا","oil":True,"nuclear":False,"budget":200000,"oil_b":12000},
    {"id":"sa","name":"🇸🇦 عربستان","cont":"🌏 آسیا","oil":True,"nuclear":False,"budget":350000,"oil_b":20000},
    {"id":"in","name":"🇮🇳 هند","cont":"🌏 آسیا","oil":False,"nuclear":True,"budget":340000,"oil_b":0},
    {"id":"pk","name":"🇵🇰 پاکستان","cont":"🌏 آسیا","oil":False,"nuclear":True,"budget":150000,"oil_b":0},
    {"id":"kp","name":"🇰🇵 کره شمالی","cont":"🌏 آسیا","oil":False,"nuclear":True,"budget":90000,"oil_b":0},
    {"id":"kr","name":"🇰🇷 کره جنوبی","cont":"🌏 آسیا","oil":False,"nuclear":False,"budget":300000,"oil_b":0},
    {"id":"jp","name":"🇯🇵 ژاپن","cont":"🌏 آسیا","oil":False,"nuclear":False,"budget":320000,"oil_b":0},
    {"id":"tr","name":"🇹🇷 ترکیه","cont":"🌏 آسیا/اروپا","oil":False,"nuclear":False,"budget":190000,"oil_b":0},
    {"id":"iq","name":"🇮🇶 عراق","cont":"🌏 آسیا","oil":True,"nuclear":False,"budget":140000,"oil_b":10000},
    {"id":"sy","name":"🇸🇾 سوریه","cont":"🌏 آسیا","oil":True,"nuclear":False,"budget":80000,"oil_b":3000},
    {"id":"ae","name":"🇦🇪 امارات","cont":"🌏 آسیا","oil":True,"nuclear":False,"budget":340000,"oil_b":8000},
    {"id":"il","name":"🇮🇱 اسرائیل","cont":"🌏 آسیا","oil":False,"nuclear":True,"budget":260000,"oil_b":0},
    {"id":"az","name":"🇦🇿 آذربایجان","cont":"🌏 آسیا","oil":True,"nuclear":False,"budget":120000,"oil_b":6000},
    {"id":"kz","name":"🇰🇿 قزاقستان","cont":"🌏 آسیا","oil":True,"nuclear":False,"budget":130000,"oil_b":7000},
    {"id":"th","name":"🇹🇭 تایلند","cont":"🌏 آسیا","oil":False,"nuclear":False,"budget":160000,"oil_b":0},
    {"id":"vn","name":"🇻🇳 ویتنام","cont":"🌏 آسیا","oil":True,"nuclear":False,"budget":140000,"oil_b":3000},
    {"id":"af","name":"🇦🇫 افغانستان","cont":"🌏 آسیا","oil":False,"nuclear":False,"budget":50000,"oil_b":0},
    {"id":"mm","name":"🇲🇲 میانمار","cont":"🌏 آسیا","oil":True,"nuclear":False,"budget":70000,"oil_b":2000},
    {"id":"my","name":"🇲🇾 مالزی","cont":"🌏 آسیا","oil":True,"nuclear":False,"budget":180000,"oil_b":4000},
    {"id":"id","name":"🇮🇩 اندونزی","cont":"🌏 آسیا","oil":True,"nuclear":False,"budget":200000,"oil_b":5000},
    # اروپا
    {"id":"us","name":"🇺🇸 آمریکا","cont":"🌎 آمریکای شمالی","oil":True,"nuclear":True,"budget":600000,"oil_b":10000},
    {"id":"gb","name":"🇬🇧 انگلیس","cont":"🌍 اروپا","oil":False,"nuclear":True,"budget":310000,"oil_b":0},
    {"id":"fr","name":"🇫🇷 فرانسه","cont":"🌍 اروپا","oil":False,"nuclear":True,"budget":290000,"oil_b":0},
    {"id":"de","name":"🇩🇪 آلمان","cont":"🌍 اروپا","oil":False,"nuclear":False,"budget":310000,"oil_b":0},
    {"id":"it","name":"🇮🇹 ایتالیا","cont":"🌍 اروپا","oil":False,"nuclear":False,"budget":250000,"oil_b":0},
    {"id":"es","name":"🇪🇸 اسپانیا","cont":"🌍 اروپا","oil":False,"nuclear":False,"budget":220000,"oil_b":0},
    {"id":"pl","name":"🇵🇱 لهستان","cont":"🌍 اروپا","oil":False,"nuclear":False,"budget":180000,"oil_b":0},
    {"id":"ua","name":"🇺🇦 اوکراین","cont":"🌍 اروپا","oil":False,"nuclear":False,"budget":120000,"oil_b":0},
    {"id":"se","name":"🇸🇪 سوئد","cont":"🌍 اروپا","oil":False,"nuclear":False,"budget":200000,"oil_b":0},
    {"id":"no","name":"🇳🇴 نروژ","cont":"🌍 اروپا","oil":True,"nuclear":False,"budget":270000,"oil_b":9000},
    {"id":"nl","name":"🇳🇱 هلند","cont":"🌍 اروپا","oil":False,"nuclear":False,"budget":230000,"oil_b":0},
    {"id":"gr","name":"🇬🇷 یونان","cont":"🌍 اروپا","oil":False,"nuclear":False,"budget":140000,"oil_b":0},
    {"id":"ro","name":"🇷🇴 رومانی","cont":"🌍 اروپا","oil":True,"nuclear":False,"budget":130000,"oil_b":2000},
    {"id":"rs","name":"🇷🇸 صربستان","cont":"🌍 اروپا","oil":False,"nuclear":False,"budget":100000,"oil_b":0},
    {"id":"ch","name":"🇨🇭 سوئیس","cont":"🌍 اروپا","oil":False,"nuclear":False,"budget":260000,"oil_b":0},
    {"id":"at","name":"🇦🇹 اتریش","cont":"🌍 اروپا","oil":False,"nuclear":False,"budget":180000,"oil_b":0},
    # آمریکا
    {"id":"br","name":"🇧🇷 برزیل","cont":"🌎 آمریکای جنوبی","oil":True,"nuclear":False,"budget":240000,"oil_b":8000},
    {"id":"mx","name":"🇲🇽 مکزیک","cont":"🌎 آمریکای شمالی","oil":True,"nuclear":False,"budget":180000,"oil_b":6000},
    {"id":"ar","name":"🇦🇷 آرژانتین","cont":"🌎 آمریکای جنوبی","oil":True,"nuclear":False,"budget":150000,"oil_b":4000},
    {"id":"co","name":"🇨🇴 کلمبیا","cont":"🌎 آمریکای جنوبی","oil":True,"nuclear":False,"budget":120000,"oil_b":3000},
    {"id":"ve","name":"🇻🇪 ونزوئلا","cont":"🌎 آمریکای جنوبی","oil":True,"nuclear":False,"budget":100000,"oil_b":9000},
    {"id":"ca","name":"🇨🇦 کانادا","cont":"🌎 آمریکای شمالی","oil":True,"nuclear":False,"budget":340000,"oil_b":8000},
    {"id":"cl","name":"🇨🇱 شیلی","cont":"🌎 آمریکای جنوبی","oil":False,"nuclear":False,"budget":140000,"oil_b":0},
    {"id":"cu","name":"🇨🇺 کوبا","cont":"🌎 آمریکای شمالی","oil":False,"nuclear":False,"budget":60000,"oil_b":0},
    # آفریقا
    {"id":"ng","name":"🇳🇬 نیجریه","cont":"🌍 آفریقا","oil":True,"nuclear":False,"budget":130000,"oil_b":8000},
    {"id":"za","name":"🇿🇦 آفریقای جنوبی","cont":"🌍 آفریقا","oil":False,"nuclear":False,"budget":160000,"oil_b":0},
    {"id":"eg","name":"🇪🇬 مصر","cont":"🌍 آفریقا","oil":True,"nuclear":False,"budget":140000,"oil_b":4000},
    {"id":"ly","name":"🇱🇾 لیبی","cont":"🌍 آفریقا","oil":True,"nuclear":False,"budget":90000,"oil_b":6000},
    {"id":"dz","name":"🇩🇿 الجزایر","cont":"🌍 آفریقا","oil":True,"nuclear":False,"budget":110000,"oil_b":5000},
    {"id":"ao","name":"🇦🇴 آنگولا","cont":"🌍 آفریقا","oil":True,"nuclear":False,"budget":80000,"oil_b":4000},
    {"id":"ma","name":"🇲🇦 مراکش","cont":"🌍 آفریقا","oil":False,"nuclear":False,"budget":90000,"oil_b":0},
    {"id":"et","name":"🇪🇹 اتیوپی","cont":"🌍 آفریقا","oil":False,"nuclear":False,"budget":60000,"oil_b":0},
    {"id":"sd","name":"🇸🇩 سودان","cont":"🌍 آفریقا","oil":True,"nuclear":False,"budget":50000,"oil_b":2000},
    # اقیانوسیه
    {"id":"au","name":"🇦🇺 استرالیا","cont":"🌏 اقیانوسیه","oil":True,"nuclear":False,"budget":330000,"oil_b":5000},
    {"id":"nz","name":"🇳🇿 نیوزیلند","cont":"🌏 اقیانوسیه","oil":False,"nuclear":False,"budget":180000,"oil_b":0},
]

EQUIP = {
    "✈️ هوایی":[
        {"id":"launcher","name":"🚀 سیستم لانچر","price":40000,"oil":0,"type":"attack","desc":"الزامی برای شلیک موشک"},
        {"id":"f16","name":"🛩️ ۸ جنگنده F-16","price":55000,"oil":0,"type":"attack","desc":"نابودی ۸۰ سرباز یا ۱ تانک"},
        {"id":"f35","name":"🛩️ ۶ جنگنده F-35","price":90000,"oil":0,"type":"attack","desc":"نابودی ۱۵۰ سرباز یا ۲ تانک"},
        {"id":"f22","name":"🛩️ ۴ جنگنده F-22 Raptor","price":140000,"oil":0,"type":"attack","desc":"نابودی ۲۲۰ سرباز یا ۳ تانک"},
        {"id":"b52","name":"💣 ۳ بمب‌افکن B-52","price":110000,"oil":0,"type":"attack","desc":"نابودی ۵ تانک یا ۳۵۰ سرباز"},
        {"id":"b2","name":"💣 ۲ بمب‌افکن B-2 Stealth","price":200000,"oil":0,"type":"attack","desc":"رادارگریز - نابودی ۸ تانک"},
        {"id":"apache","name":"🚁 ۸ هلیکوپتر AH-64 Apache","price":35000,"oil":0,"type":"attack","desc":"نابودی ۳ تانک یا ۱۸۰ سرباز"},
        {"id":"drone","name":"🤖 ۲۰ پهپاد بیرقدار","price":25000,"oil":0,"type":"attack","desc":"نابودی ۱۰۰ سرباز یا ۱ تانک"},
        {"id":"manpad","name":"🛡️ ۵۰۰ موشک MANPAD","price":30000,"oil":0,"type":"defense","desc":"سرنگونی ۲۰ هلیکوپتر/جنگنده"},
        {"id":"s300","name":"🛡️ سامانه S-300","price":120000,"oil":0,"type":"defense","desc":"سرنگونی ۲۵ جنگنده یا بمب‌افکن"},
        {"id":"s400","name":"🛡️ سامانه S-400","price":200000,"oil":0,"type":"defense","desc":"سرنگونی ۴۰ جنگنده یا ۱۰ بمب‌افکن"},
    ],
    "🚢 دریایی":[
        {"id":"corvette","name":"🚢 ۳ کوروت رزمی","price":40000,"oil":0,"type":"attack","desc":"پشتیبانی ساحلی"},
        {"id":"frigate","name":"🚢 ۲ فریگات","price":65000,"oil":0,"type":"attack","desc":"نابودی تجهیزات دریایی سبک"},
        {"id":"destroyer","name":"🚢 ناو اژدرافکن","price":100000,"oil":0,"type":"attack","desc":"نابودی ناوچه و زیردریایی"},
        {"id":"carrier","name":"🚢 ناو هواپیمابر","price":250000,"oil":0,"type":"attack","desc":"قدرتمندترین کشتی جنگی"},
        {"id":"submarine","name":"🌊 ۲ زیردریایی","price":90000,"oil":0,"type":"attack","desc":"حمله مخفیانه"},
        {"id":"nuclear_sub","name":"🌊☢️ زیردریایی اتمی","price":350000,"oil":0,"type":"attack","desc":"فقط کشورهای اتمی"},
        {"id":"coastal_bat","name":"🛡️ باتری موشک ساحلی","price":80000,"oil":0,"type":"defense","desc":"نابودی ۳ فریگات یا ۵ کوروت"},
        {"id":"sonar","name":"🛡️ سیستم سونار","price":40000,"oil":0,"type":"defense","desc":"شناسایی زیردریایی دشمن"},
    ],
    "🚀 موشکی":[
        {"id":"grad","name":"🚀 ۲۰۰ راکت گراد","price":15000,"oil":200,"type":"attack","desc":"نابودی ۸۰ سرباز یا ۱ تانک"},
        {"id":"tactical","name":"🚀 ۵۰۰ موشک تاکتیکی","price":30000,"oil":400,"type":"attack","desc":"نابودی ۱۵۰ سرباز یا ۲ تانک"},
        {"id":"cruise","name":"🚀 ۵۰ موشک کروز","price":80000,"oil":1200,"type":"attack","desc":"دقت ۱ متری - نابودی هر هدف"},
        {"id":"ballistic","name":"🚀 ۳۰ موشک بالستیک","price":130000,"oil":2000,"type":"attack","desc":"برد ۳۰۰۰ کیلومتر"},
        {"id":"precision","name":"🎯 ۲۰ موشک نقطه‌زن","price":200000,"oil":3500,"type":"attack","desc":"دقت ۰.۱ متری"},
        {"id":"hypersonic","name":"⚡ ۱۰ موشک هایپرسونیک","price":300000,"oil":6000,"type":"attack","desc":"ماخ ۱۵ - غیرقابل رهگیری"},
        {"id":"kinzhal","name":"⚡ ۱۵ موشک کینژال","price":250000,"oil":5000,"type":"attack","desc":"هایپرسونیک روسی"},
        {"id":"icbm","name":"🚀🌍 ۵ موشک قاره‌پیما","price":400000,"oil":10000,"type":"attack","desc":"برد ۱۲۰۰۰ کیلومتر"},
        {"id":"atom","name":"☢️ بمب اتمی","price":8000000,"oil":0,"type":"attack","desc":"فقط کشورهای اتمی ⚠️"},
        {"id":"neutron","name":"☢️ بمب نوترونی","price":5000000,"oil":0,"type":"attack","desc":"فقط کشورهای اتمی ⚠️"},
        {"id":"cram","name":"🛡️ سیستم C-RAM","price":45000,"oil":0,"type":"defense","desc":"رهگیری راکت و خمپاره"},
        {"id":"patriot","name":"🛡️ سامانه پاتریوت","price":90000,"oil":0,"type":"defense","desc":"رهگیری موشک تاکتیکی/کروز - ۸۵٪"},
        {"id":"thaad","name":"🛡️ سامانه THAAD","price":180000,"oil":0,"type":"defense","desc":"رهگیری بالستیک/قاره‌پیما - ۹۰٪"},
        {"id":"iron_dome","name":"🛡️ گنبد آهنین","price":120000,"oil":0,"type":"defense","desc":"رهگیری راکت کوتاه‌برد - ۹۵٪"},
        {"id":"arrow3","name":"🛡️ سامانه Arrow-3","price":250000,"oil":0,"type":"defense","desc":"رهگیری هایپرسونیک - ۷۰٪"},
    ],
    "🪖 زمینی":[
        {"id":"infantry","name":"👤 ۵۰۰۰ سرباز پیاده","price":50000,"oil":0,"type":"attack","desc":"نیروی پایه"},
        {"id":"special","name":"🪖 ۲۰۰۰ نیروی ویژه","price":80000,"oil":0,"type":"attack","desc":"آموزش‌دیده و مجهز"},
        {"id":"marine","name":"⚓ ۱۰۰۰ تفنگدار دریایی","price":70000,"oil":0,"type":"attack","desc":"عملیات آبی‌خاکی"},
        {"id":"para","name":"🪂 ۵۰۰ چترباز","price":60000,"oil":0,"type":"attack","desc":"حمله از هوا به زمین"},
        {"id":"rpg","name":"💥 ۵۰۰ RPG-29","price":30000,"oil":0,"type":"attack","desc":"ضد زره سبک"},
        {"id":"javelin","name":"🎯 ۲۰۰ موشک جاولین","price":60000,"oil":0,"type":"attack","desc":"ضد تانک پیشرفته"},
        {"id":"t72","name":"🚓 ۵۰ تانک T-72","price":45000,"oil":0,"type":"attack","desc":"تانک قابل اطمینان"},
        {"id":"abrams","name":"🦾 ۳۰ تانک Abrams M1A2","price":100000,"oil":0,"type":"attack","desc":"بهترین تانک جهان"},
        {"id":"howitzer","name":"🎯 ۱۰ هویتزر ۱۵۵mm","price":40000,"oil":0,"type":"attack","desc":"برد ۴۰ کیلومتر"},
        {"id":"mlrs","name":"🚀 ۵ سیستم MLRS","price":70000,"oil":0,"type":"attack","desc":"راکت‌انداز چندلوله"},
        {"id":"himars","name":"🎯 ۳ سیستم HIMARS","price":90000,"oil":0,"type":"attack","desc":"دقیق‌ترین توپخانه"},
        {"id":"trench","name":"🛡️ سنگر و موانع","price":20000,"oil":0,"type":"defense","desc":"کاهش ۳۰٪ تلفات"},
        {"id":"gdef_light","name":"🛡️ دفاع زمینی سبک","price":80000,"oil":0,"type":"defense","desc":"کاهش ۶۰٪ تلفات سرباز"},
        {"id":"gdef_mid","name":"🛡️ دفاع زمینی متوسط","price":140000,"oil":0,"type":"defense","desc":"کاهش ۱۰۰٪ تلفات نیروی ویژه"},
        {"id":"gdef_heavy","name":"🛡️ دفاع زمینی سنگین","price":220000,"oil":0,"type":"defense","desc":"خنثی یک موج کامل حمله"},
    ],
    "⛏️ اقتصادی":[
        {"id":"iron","name":"⛏️ معدن آهن","price":10000,"oil":0,"type":"economy","daily":4000,"desc":"۴,۰۰۰$/روز"},
        {"id":"copper","name":"⛏️ معدن مس","price":15000,"oil":0,"type":"economy","daily":6000,"desc":"۶,۰۰۰$/روز"},
        {"id":"silver","name":"⛏️ معدن نقره","price":22000,"oil":0,"type":"economy","daily":9000,"desc":"۹,۰۰۰$/روز"},
        {"id":"gold","name":"⛏️ معدن طلا","price":35000,"oil":0,"type":"economy","daily":14000,"desc":"۱۴,۰۰۰$/روز"},
        {"id":"diamond","name":"⛏️ معدن الماس","price":60000,"oil":0,"type":"economy","daily":22000,"desc":"۲۲,۰۰۰$/روز"},
        {"id":"uranium","name":"☢️ معدن اورانیوم","price":80000,"oil":0,"type":"economy","daily":30000,"desc":"۳۰,۰۰۰$/روز (فقط اتمی)"},
        {"id":"refinery","name":"🛢️ پالایشگاه نفت","price":50000,"oil":0,"type":"economy","daily":0,"oil_daily":1500,"desc":"۱۵۰۰ بشکه/روز (فقط نفتی)"},
        {"id":"oil_plat","name":"🛢️ سکوی نفتی","price":90000,"oil":0,"type":"economy","daily":0,"oil_daily":3000,"desc":"۳۰۰۰ بشکه/روز (فقط نفتی)"},
        {"id":"factory","name":"🏭 کارخانه تسلیحات","price":70000,"oil":0,"type":"economy","daily":15000,"desc":"۱۵,۰۰۰$/روز"},
        {"id":"port","name":"⚓ بندر تجاری","price":45000,"oil":0,"type":"economy","daily":10000,"desc":"۱۰,۰۰۰$/روز"},
        {"id":"bank","name":"🏦 بانک مرکزی","price":100000,"oil":0,"type":"economy","daily":25000,"desc":"۲۵,۰۰۰$/روز"},
    ],
    "🖥️ سایبری":[
        {"id":"hack","name":"💻 واحد هک تهاجمی","price":150000,"oil":0,"type":"attack","desc":"فلج کردن زیرساخت دشمن"},
        {"id":"spy","name":"🔍 جاسوسی سایبری","price":100000,"oil":0,"type":"attack","desc":"دسترسی به اطلاعات دشمن"},
        {"id":"antihack","name":"🛡️ سیستم ضدهک","price":80000,"oil":0,"type":"defense","desc":"دفع هک ساده + یک پیشرفته"},
        {"id":"antivirus","name":"🛡️ آنتی‌ویروس ملی","price":120000,"oil":0,"type":"defense","desc":"محافظت کامل دیجیتال"},
        {"id":"satellite","name":"🛸 ماهواره جاسوسی","price":200000,"oil":0,"type":"attack","desc":"رصد حرکات نظامی دشمن"},
        {"id":"radar","name":"📡 رادار پیشرفته","price":90000,"oil":0,"type":"defense","desc":"شناسایی از ۵۰۰ کیلومتری"},
        {"id":"jammer","name":"📡 جمر الکترونیکی","price":70000,"oil":0,"type":"defense","desc":"۵۰٪ کاهش دقت موشک دشمن"},
        {"id":"emp","name":"💥 بمب EMP","price":250000,"oil":0,"type":"attack","desc":"فلج کردن الکترونیک دشمن"},
    ],
    "🔬 فناوری پیشرفته":[
        {"id":"stealth","name":"👻 فناوری استلث","price":300000,"oil":0,"type":"attack","desc":"ناپدید از رادار دشمن"},
        {"id":"laser","name":"⚡ سلاح لیزری","price":400000,"oil":0,"type":"attack","desc":"رهگیری موشک با لیزر"},
        {"id":"bio_def","name":"🧬 دفاع بیولوژیک","price":180000,"oil":0,"type":"defense","desc":"محافظت از حملات بیولوژیک"},
        {"id":"nuke_shield","name":"☢️🛡️ سپر ضد اتمی","price":500000,"oil":0,"type":"defense","desc":"کاهش ۶۰٪ خسارت اتمی"},
    ],
}

WAITING_DECL = 1
WAITING_WAR = 2

def get_ai():
    return anthropic.Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None

async def ai_check_decl(country, text):
    if len(text.strip()) < 80 or len([l for l in text.split('\n') if l.strip()]) < 2:
        return {"approved":False,"reason":"بیانیه باید حداقل ۲ خط و ۸۰ کاراکتر باشد","edited":text}
    client = get_ai()
    if not client: return {"approved":True,"reason":"تایید","edited":text}
    try:
        r = client.messages.create(model="claude-sonnet-4-20250514",max_tokens=500,
            system='بیانیه رسمی بازی رو بررسی کن. رد کن اگه: فحش داره، غیررسمیه، کوتاهه، بی‌ربطه. فقط JSON: {"approved":true/false,"reason":"فارسی","edited":"متن"}',
            messages=[{"role":"user","content":f"کشور:{country}\n{text}"}])
        return json.loads(r.content[0].text.strip().replace("```json","").replace("```",""))
    except: return {"approved":True,"reason":"تایید","edited":text}

async def ai_war(atk_c,def_c,atk_p,def_p,scenario):
    client = get_ai()
    atk_eq=", ".join(e['name'] for e in atk_p.get('equipment',[]) if e.get('type')=='attack') or "هیچ"
    def_eq=", ".join(e['name'] for e in def_p.get('equipment',[]) if e.get('type')=='defense') or "هیچ"
    if not client:
        return {"sat":"📡 فعالیت نظامی رصد شد...","winner":"defender","atk_loss":35,"def_loss":20,
                "story":"نبرد سختی رخ داد.","territory":"بدون تغییر","civilian":False,"fine":0}
    try:
        r = client.messages.create(model="claude-sonnet-4-20250514",max_tokens=800,
            system='تحلیلگر نظامی بازی جنگ جهانی ۲۶. فقط JSON:\n{"sat":"پیام ماهواره هیجانی ۲ جمله","winner":"attacker یا defender","atk_loss":عدد,"def_loss":عدد,"story":"گزارش سینمایی ۴ جمله","territory":"وضعیت ارضی","civilian":true/false,"fine":عدد}',
            messages=[{"role":"user","content":f"حمله‌کننده:{atk_c['name']} بودجه:${atk_p.get('budget',0):,}\nتجهیزات:{atk_eq}\n\nمدافع:{def_c['name']} بودجه:${def_p.get('budget',0):,}\nتجهیزات دفاعی:{def_eq}\n\nسناریو:{scenario}"}])
        return json.loads(r.content[0].text.strip().replace("```json","").replace("```",""))
    except:
        return {"sat":"📡 فعالیت نظامی رصد شد...","winner":"defender","atk_loss":30,"def_loss":15,
                "story":"نبرد سختی رخ داد.","territory":"بدون تغییر","civilian":False,"fine":0}

async def ai_news(db):
    client = get_ai()
    wars=db.get('wars',[])[-5:]
    decls=db.get('declarations',[])[-5:]
    if not client: return "📺 BBC WW26 | گزارش امروز آماده نشد."
    try:
        wt="\n".join(f"- {w['atk']} ⚔️ {w['def']} → برنده:{w['winner']}" for w in wars) or "جنگی نبود"
        dt="\n".join(f"- {d['country']}" for d in decls) or "بیانیه‌ای نبود"
        r = client.messages.create(model="claude-sonnet-4-20250514",max_tokens=500,
            system="خبرنگار BBC فارسی هستی. گزارش شبانه بازی جنگ جهانی ۲۶ رو هیجان‌انگیز بنویس.",
            messages=[{"role":"user","content":f"بازیکنان:{len(db['players'])}\nجنگ‌ها:\n{wt}\nبیانیه‌ها:\n{dt}"}])
        return f"📺 *BBC World War 26 | گزارش شبانه*\n━━━━━━━━━━━━━━━\n{r.content[0].text}"
    except: return "📺 BBC WW26 | گزارش امروز"

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    db=load_db()
    uid=str(update.effective_user.id)
    if context.args and uid not in db["players"]:
        ref=context.args[0]
        if ref!=uid and ref in db["players"] and uid not in db["referrals"]:
            db["players"][ref]["budget"]=db["players"][ref].get("budget",0)+15000
            db["referrals"][uid]=ref
            save_db(db)
            try: await context.bot.send_message(int(ref),"🎁 بازیکن جدید با لینک شما وارد شد!\n💰 +15,000$ اضافه شد!")
            except: pass
    p=db["players"].get(uid)
    if p:
        c=next((x for x in COUNTRIES if x["id"]==p["country_id"]),None)
        kb=[
            [InlineKeyboardButton("📊 وضعیت کشور",callback_data="status"),InlineKeyboardButton("🛒 خرید",callback_data="shop")],
            [InlineKeyboardButton("📜 بیانیه",callback_data="decl"),InlineKeyboardButton("⚔️ جنگ",callback_data="war")],
            [InlineKeyboardButton("🌍 وضعیت بازی",callback_data="world"),InlineKeyboardButton("🔗 دعوت",callback_data="ref")],
            [InlineKeyboardButton("🚪 خروج",callback_data="quit")],
        ]
        if update.effective_user.id==ADMIN_ID:
            kb.append([InlineKeyboardButton("👑 پنل ادمین",callback_data="admin")])
        await update.message.reply_text(
            f"🌍 *{update.effective_user.first_name}* خوش اومدی!\n\n"
            f"🏳️ {c['name'] if c else '?'}\n💰 ${p.get('budget',0):,}\n🛢️ {p.get('oil',0):,} بشکه",
            parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(
            "🌍⚔️ *WORLD WAR 26* ⚔️🌍\n\nکشور انتخاب کن و وارد شو! 🔥",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌍 انتخاب کشور",callback_data="choose")]]))

async def choose_country(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    db=load_db()
    taken={p["country_id"] for p in db["players"].values()}
    conts={}
    for c in COUNTRIES:
        conts.setdefault(c["cont"],[]).append(c)
    kb=[]
    for cont,cs in conts.items():
        kb.append([InlineKeyboardButton(f"━ {cont} ━",callback_data="noop")])
        row=[]
        for c in cs:
            t=c["id"] in taken
            props=("🛢️" if c["oil"] else "")+("☢️" if c["nuclear"] else "")
            lbl=f"{'🔒' if t else '✅'}{c['name'].split(' ',1)[1]}{props}"
            row.append(InlineKeyboardButton(lbl,callback_data=f"join_{c['id']}" if not t else "taken"))
            if len(row)==2: kb.append(row); row=[]
        if row: kb.append(row)
    kb.append([InlineKeyboardButton("🔙",callback_data="back")])
    await q.edit_message_text("🌍 *انتخاب کشور*\n✅آزاد 🔒گرفته 🛢️نفت ☢️اتمی",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def join_country(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    cid=q.data.replace("join_","")
    db=load_db(); uid=str(update.effective_user.id)
    if uid in db["players"]: await q.edit_message_text("❌ قبلاً کشور داری! /start"); return
    if cid in {p["country_id"] for p in db["players"].values()}: await q.edit_message_text("❌ گرفته شده!"); return
    c=next((x for x in COUNTRIES if x["id"]==cid),None)
    if not c: return
    db["players"][uid]={"user_id":uid,"username":update.effective_user.username or "?",
        "first_name":update.effective_user.first_name,"country_id":cid,
        "budget":c["budget"],"oil":c["oil_b"],"equipment":[],
        "joined_at":datetime.now().isoformat(),"last_decl":datetime.now().isoformat(),"banned":False}
    save_db(db)
    props=[]
    if c["oil"]: props.append("🛢️نفت")
    if c["nuclear"]: props.append("☢️اتمی")
    await q.edit_message_text(
        f"✅ *{c['name']}* انتخاب شد!\n💰 ${c['budget']:,}\n🛢️ {c['oil_b']:,} بشکه\n🌍 {c['cont']}\n{' | '.join(props) if props else 'بدون امکانات خاص'}\n\nبجنگ! ⚔️",
        parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 پنل",callback_data="back")]]))
    try: await context.bot.send_message(ADMIN_ID,f"🔔 {update.effective_user.first_name} → {c['name']}")
    except: pass

async def show_status(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    db=load_db(); uid=str(update.effective_user.id)
    p=db["players"].get(uid)
    if not p: await q.edit_message_text("❌ /start"); return
    c=next((x for x in COUNTRIES if x["id"]==p["country_id"]),None)
    eq=p.get("equipment",[])
    atk=[e for e in eq if e.get("type")=="attack"]
    defn=[e for e in eq if e.get("type")=="defense"]
    econ=[e for e in eq if e.get("type")=="economy"]
    daily=sum(e.get("daily",0) for e in econ)
    odaily=sum(e.get("oil_daily",0) for e in econ)
    txt=(f"📊 *وضعیت {c['name']}*\n━━━━━━━━━━━━━━━\n"
        f"💰 بودجه: ${p['budget']:,}\n🛢️ نفت: {p.get('oil',0):,} بشکه\n"
        f"📈 درآمد: ${daily:,}/روز\n🛢️ تولید نفت: {odaily:,} بشکه/روز\n"
        f"🌍 {c.get('cont','')}\n🛢️ نفت: {'✅' if c['oil'] else '❌'} | ☢️ اتمی: {'✅' if c['nuclear'] else '❌'}\n"
        f"━━━━━━━━━━━━━━━\n⚔️ حمله ({len(atk)}):\n")
    for e in atk: txt+=f"• {e['name']}\n"
    txt+=f"🛡️ دفاع ({len(defn)}):\n"
    for e in defn: txt+=f"• {e['name']}\n"
    txt+=f"⛏️ اقتصادی ({len(econ)}):\n"
    for e in econ: txt+=f"• {e['name']}\n"
    await q.edit_message_text(txt,parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))

async def shop_menu(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    db=load_db(); uid=str(update.effective_user.id)
    p=db["players"].get(uid)
    if not p: await q.edit_message_text("❌ /start"); return
    kb=[[InlineKeyboardButton(cat,callback_data=f"cat_{cat}")] for cat in EQUIP]+\
       [[InlineKeyboardButton("📋 لیست کامل",callback_data="fulllist")]]+\
       [[InlineKeyboardButton("🔙",callback_data="back")]]
    await q.edit_message_text(f"🛒 *فروشگاه*\n💰 ${p['budget']:,} | 🛢️ {p.get('oil',0):,}",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def shop_cat(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    cat=q.data.replace("cat_","")
    db=load_db(); uid=str(update.effective_user.id)
    p=db["players"].get(uid)
    if not p: return
    items=EQUIP.get(cat,[])
    kb=[]
    for it in items:
        o=f"+{it['oil']:,}🛢️" if it.get("oil") else ""
        kb.append([InlineKeyboardButton(f"{it['name']} ${it['price']:,}{o}",callback_data=f"buy_{it['id']}")])
    kb.append([InlineKeyboardButton("🔙",callback_data="shop")])
    await q.edit_message_text(f"🛒 *{cat}*\n💰 ${p['budget']:,} | 🛢️ {p.get('oil',0):,}",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def buy(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    iid=q.data.replace("buy_","")
    db=load_db(); uid=str(update.effective_user.id)
    p=db["players"].get(uid)
    if not p: await q.answer("❌",show_alert=True); return
    item=next((it for cat in EQUIP.values() for it in cat if it["id"]==iid),None)
    if not item: await q.answer("پیدا نشد!",show_alert=True); return
    if p["budget"]<item["price"]: await q.answer(f"❌ بودجه کم! نیاز: ${item['price']:,}",show_alert=True); return
    if item.get("oil",0) and p.get("oil",0)<item["oil"]: await q.answer(f"❌ نفت کم! نیاز: {item['oil']:,}",show_alert=True); return
    c=next((x for x in COUNTRIES if x["id"]==p["country_id"]),None)
    if item["id"] in ["refinery","oil_plat"] and (not c or not c.get("oil")):
        await q.answer("❌ فقط کشورهای نفتی!",show_alert=True); return
    if item["id"] in ["uranium"] and (not c or not c.get("nuclear")):
        await q.answer("❌ فقط کشورهای اتمی!",show_alert=True); return
    if item["id"] in ["atom","neutron","nuclear_sub"] and (not c or not c.get("nuclear")):
        await q.answer("☢️ فقط کشورهای اتمی!",show_alert=True); return
    p["budget"]-=item["price"]
    if item.get("oil"): p["oil"]-=item["oil"]
    p.setdefault("equipment",[]).append(item)
    db["players"][uid]=p; save_db(db)
    await q.answer(f"✅ {item['name']} خریداری شد!",show_alert=True)

async def full_list(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    txt="📋 *لیست کامل تجهیزات*\n"
    for cat,items in EQUIP.items():
        txt+=f"\n{cat}\n━━━━━━━━━━\n"
        for it in items:
            d=f"📈${it['daily']:,}/روز" if it.get("daily") else ""
            od=f"🛢️{it.get('oil_daily',0):,}/روز" if it.get("oil_daily") else ""
            txt+=f"• {it['name']}\n  💰${it['price']:,} {d}{od}\n  📝{it['desc']}\n"
    chunks=[txt[i:i+3800] for i in range(0,len(txt),3800)]
    kb=[[InlineKeyboardButton("🔙",callback_data="shop")]]
    await q.edit_message_text(chunks[0],parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb) if len(chunks)==1 else None)
    for ch in chunks[1:]: await q.message.reply_text(ch,parse_mode="Markdown")
    if len(chunks)>1: await q.message.reply_text(".",reply_markup=InlineKeyboardMarkup(kb))

async def decl_start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    db=load_db(); uid=str(update.effective_user.id)
    if uid not in db["players"]: await q.edit_message_text("❌ /start"); return ConversationHandler.END
    if db["players"][uid].get("banned"): await q.edit_message_text("🚫 بن هستید!"); return ConversationHandler.END
    await q.edit_message_text("📜 *بیانیه رسمی*\n\n✅ حداقل ۲ خط\n✅ رسمی (بدون فحش)\n✅ مرتبط با بازی\n\n✍️ بنویس:",parse_mode="Markdown")
    return WAITING_DECL

async def decl_recv(update:Update,context:ContextTypes.DEFAULT_TYPE):
    db=load_db(); uid=str(update.effective_user.id)
    p=db["players"].get(uid)
    if not p: return ConversationHandler.END
    c=next((x for x in COUNTRIES if x["id"]==p["country_id"]),None)
    await update.message.reply_text("⏳ AI بررسی می‌کنه...")
    r=await ai_check_decl(c["name"],update.message.text)
    if r["approved"]:
        db["declarations"].append({"id":len(db["declarations"])+1,"user_id":uid,"country":c["name"],"text":r["edited"],"date":datetime.now().isoformat()})
        db["players"][uid]["last_decl"]=datetime.now().isoformat()
        save_db(db)
        try:
            await context.bot.send_message(CHANNEL_ID,f"📜 *بیانیه رسمی*\n🌍 {c['name']}\n━━━━━━━━━━━━━━━\n{r['edited']}",parse_mode="Markdown")
            await update.message.reply_text("✅ تایید و در کانال منتشر شد!")
        except Exception as e: await update.message.reply_text(f"✅ تایید شد - خطای کانال: {e}")
    else:
        await update.message.reply_text(f"❌ رد شد!\n💬 {r['reason']}")
    await update.message.reply_text(".",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پنل",callback_data="back")]]))
    return ConversationHandler.END

async def war_menu(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    db=load_db(); uid=str(update.effective_user.id)
    p=db["players"].get(uid)
    if not p: await q.edit_message_text("❌ /start"); return
    if p.get("banned"): await q.edit_message_text("🚫 بن!"); return
    others={k:v for k,v in db["players"].items() if k!=uid and not v.get("banned")}
    if not others:
        await q.edit_message_text("⚔️ بازیکن دیگه‌ای نیست!",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]])); return
    kb=[]
    for k,v in others.items():
        c=next((x for x in COUNTRIES if x["id"]==v["country_id"]),None)
        if c: kb.append([InlineKeyboardButton(f"⚔️ {c['name']}",callback_data=f"atk_{k}")])
    kb.append([InlineKeyboardButton("🔙",callback_data="back")])
    await q.edit_message_text("⚔️ *هدف حمله:*",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def atk_target(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    context.user_data["target"]=q.data.replace("atk_","")
    await q.edit_message_text("📋 *سناریو حمله*\n\nمثال: موشک‌های کروز به پایگاه هوایی شلیک می‌کنم\n\n✍️ بنویس:",parse_mode="Markdown")
    return WAITING_WAR

async def war_recv(update:Update,context:ContextTypes.DEFAULT_TYPE):
    db=load_db(); uid=str(update.effective_user.id)
    tid=context.user_data.get("target")
    atk_p=db["players"].get(uid); def_p=db["players"].get(tid)
    if not atk_p or not def_p: return ConversationHandler.END
    ac=next((x for x in COUNTRIES if x["id"]==atk_p["country_id"]),None)
    dc=next((x for x in COUNTRIES if x["id"]==def_p["country_id"]),None)
    await update.message.reply_text("⏳ AI نبرد رو تحلیل می‌کنه...")
    r=await ai_war(ac,dc,atk_p,def_p,update.message.text)
    winner=ac["name"] if r["winner"]=="attacker" else dc["name"]
    db["wars"].append({"id":len(db["wars"])+1,"atk":ac["name"],"def":dc["name"],"winner":winner,"atk_loss":r["atk_loss"],"def_loss":r["def_loss"],"date":datetime.now().isoformat()})
    un=""
    if r.get("civilian") and r.get("fine",0)>0:
        fine=r["fine"]
        db["players"][uid]["budget"]=db["players"][uid].get("budget",0)-fine
        un=f"\n\n🏛️ *سازمان ملل:* {ac['name']} به دلیل آسیب به غیرنظامیان ${fine:,} جریمه شد!"
    save_db(db)
    txt=(f"📡 {r.get('sat','')}\n\n⚔️ *گزارش نبرد*\n━━━━━━━━━━━━━━━\n"
        f"🔴 {ac['name']} vs 🔵 {dc['name']}\n━━━━━━━━━━━━━━━\n"
        f"📰 {r['story']}\n\n🏆 *برنده: {winner}*\n"
        f"📉 تلفات {ac['name']}: {r['atk_loss']}%\n📉 تلفات {dc['name']}: {r['def_loss']}%\n"
        f"📍 {r['territory']}{un}")
    try: await context.bot.send_message(CHANNEL_ID,txt,parse_mode="Markdown")
    except: pass
    try: await context.bot.send_message(int(tid),f"🚨 *{ac['name']} به شما حمله کرد!*\n\n{r['story']}\n🏆 {winner}",parse_mode="Markdown")
    except: pass
    await update.message.reply_text(txt,parse_mode="Markdown")
    await update.message.reply_text(".",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))
    return ConversationHandler.END

async def world_view(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    db=load_db()
    txt="🌍 *وضعیت بازی*\n━━━━━━━━━━━━━━━\n"
    for uid,p in db["players"].items():
        if p.get("banned"): continue
        c=next((x for x in COUNTRIES if x["id"]==p["country_id"]),None)
        if c: txt+=f"{c['name']}\n💰 ${p['budget']:,} | 🔧 {len(p.get('equipment',[]))}\n"
    await q.edit_message_text(txt or "کسی نیست",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))

async def ref_menu(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=str(update.effective_user.id)
    db=load_db()
    botu=(await context.bot.get_me()).username
    link=f"https://t.me/{botu}?start={uid}"
    cnt=sum(1 for v in db.get("referrals",{}).values() if v==uid)
    await q.edit_message_text(f"🔗 *دعوت دوستان*\n\n`{link}`\n\n👥 دعوت‌شدگان: {cnt}\n💰 پاداش هر دعوت: +15,000$",
        parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))

async def quit_ask(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.edit_message_text("🚪 مطمئنی؟ همه چیز حذف میشه! ⚠️",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ بله",callback_data="quit_yes"),InlineKeyboardButton("❌ نه",callback_data="back")]]))

async def quit_yes(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    db=load_db(); uid=str(update.effective_user.id)
    if uid in db["players"]:
        c=next((x for x in COUNTRIES if x["id"]==db["players"][uid]["country_id"]),None)
        del db["players"][uid]; save_db(db)
        await q.edit_message_text(f"🚪 خارج شدی. {c['name'] if c else ''} آزاد شد. /start")
    else: await q.edit_message_text("تو بازی نیستی!")

# ═══ ادمین ═══
async def adm_panel(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID:
        if update.callback_query: await update.callback_query.answer("❌",show_alert=True)
        return
    q=update.callback_query
    if q: await q.answer()
    db=load_db()
    kb=[
        [InlineKeyboardButton("👥 بازیکنان",callback_data="adm_p"),InlineKeyboardButton("📊 آمار",callback_data="adm_s")],
        [InlineKeyboardButton("⚔️ جنگ‌ها",callback_data="adm_w"),InlineKeyboardButton("📜 بیانیه‌ها",callback_data="adm_d")],
        [InlineKeyboardButton("🔙",callback_data="back")],
    ]
    txt=f"👑 *پنل ادمین*\n👥 {len(db['players'])} | ⚔️ {len(db['wars'])} | 📜 {len(db['declarations'])}"
    if q: await q.edit_message_text(txt,parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
    else: await update.message.reply_text(txt,parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def adm_p(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    q=update.callback_query; await q.answer()
    db=load_db()
    txt="👥 *بازیکنان*\n━━━━━━━━━━\n"
    for uid,p in db["players"].items():
        c=next((x for x in COUNTRIES if x["id"]==p["country_id"]),None)
        b="🚫" if p.get("banned") else "✅"
        txt+=f"{b} {p.get('username','?')} | {c['name'] if c else '?'}\nID:{uid} | ${p['budget']:,}\n"
    await q.edit_message_text(txt[:4000] or "کسی نیست",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="admin")]]))

async def adm_s(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    q=update.callback_query; await q.answer()
    db=load_db()
    await q.edit_message_text(
        f"📊 *آمار*\n\n👥 فعال:{len([p for p in db['players'].values() if not p.get('banned')])}\n"
        f"🚫 بن:{len([p for p in db['players'].values() if p.get('banned')])}\n"
        f"⚔️ جنگ:{len(db['wars'])}\n📜 بیانیه:{len(db['declarations'])}\n"
        f"💰 کل ثروت:${sum(p.get('budget',0) for p in db['players'].values()):,}",
        parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="admin")]]))

async def adm_w(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    q=update.callback_query; await q.answer()
    db=load_db()
    txt="⚔️ *آخرین جنگ‌ها*\n"
    for w in db["wars"][-10:]: txt+=f"• {w['atk']} ⚔️ {w['def']} → 🏆{w['winner']}\n"
    await q.edit_message_text(txt or "جنگی نبود",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="admin")]]))

async def adm_d(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    q=update.callback_query; await q.answer()
    db=load_db()
    txt="📜 *آخرین بیانیه‌ها*\n"
    for d in db["declarations"][-10:]: txt+=f"• {d['country']}: {d['text'][:50]}...\n"
    await q.edit_message_text(txt or "بیانیه‌ای نبود",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="admin")]]))

async def cmd_ban(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("استفاده: /ban <user_id>"); return
    db=load_db(); uid=context.args[0]
    if uid in db["players"]:
        db["players"][uid]["banned"]=True; save_db(db)
        await update.message.reply_text(f"🚫 {uid} بن شد.")
        try: await context.bot.send_message(int(uid),"🚫 از بازی بن شدید.")
        except: pass
    else: await update.message.reply_text("❌ پیدا نشد.")

async def cmd_unban(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("استفاده: /unban <user_id>"); return
    db=load_db(); uid=context.args[0]
    if uid in db["players"]:
        db["players"][uid]["banned"]=False; save_db(db)
        await update.message.reply_text(f"✅ {uid} آنبن شد.")
        try: await context.bot.send_message(int(uid),"✅ بن شما برداشته شد!")
        except: pass
    else: await update.message.reply_text("❌ پیدا نشد.")

async def cmd_kick(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("استفاده: /kick <user_id>"); return
    db=load_db(); uid=context.args[0]
    if uid in db["players"]:
        c=next((x for x in COUNTRIES if x["id"]==db["players"][uid]["country_id"]),None)
        del db["players"][uid]; save_db(db)
        await update.message.reply_text(f"🗑️ {uid} ({c['name'] if c else ''}) اخراج شد.")
        try: await context.bot.send_message(int(uid),"🗑️ توسط ادمین اخراج شدید.")
        except: pass
    else: await update.message.reply_text("❌ پیدا نشد.")

async def cmd_setbudget(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<2: await update.message.reply_text("/setbudget <id> <مقدار>"); return
    db=load_db(); uid=context.args[0]
    try: amt=int(context.args[1])
    except: await update.message.reply_text("عدد وارد کن!"); return
    if uid in db["players"]:
        old=db["players"][uid]["budget"]; db["players"][uid]["budget"]=amt; save_db(db)
        await update.message.reply_text(f"✅ بودجه {uid}: ${old:,} → ${amt:,}")
    else: await update.message.reply_text("❌ پیدا نشد.")

async def cmd_addbudget(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<2: await update.message.reply_text("/addbudget <id> <مقدار>"); return
    db=load_db(); uid=context.args[0]
    try: amt=int(context.args[1])
    except: await update.message.reply_text("عدد وارد کن!"); return
    if uid in db["players"]:
        db["players"][uid]["budget"]=db["players"][uid].get("budget",0)+amt; save_db(db)
        await update.message.reply_text(f"✅ +${amt:,} به {uid}. بودجه جدید: ${db['players'][uid]['budget']:,}")
    else: await update.message.reply_text("❌ پیدا نشد.")

async def cmd_setoil(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<2: await update.message.reply_text("/setoil <id> <مقدار>"); return
    db=load_db(); uid=context.args[0]
    try: amt=int(context.args[1])
    except: await update.message.reply_text("عدد وارد کن!"); return
    if uid in db["players"]:
        db["players"][uid]["oil"]=amt; save_db(db)
        await update.message.reply_text(f"✅ نفت {uid}: {amt:,} بشکه")
    else: await update.message.reply_text("❌ پیدا نشد.")

async def cmd_broadcast(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("/broadcast <پیام>"); return
    msg=" ".join(context.args); db=load_db(); sent=0
    for uid in db["players"]:
        try: await context.bot.send_message(int(uid),f"📢 *پیام ادمین:*\n{msg}",parse_mode="Markdown"); sent+=1
        except: pass
    await update.message.reply_text(f"✅ ارسال به {sent} نفر")

async def cmd_help(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    await update.message.reply_text(
        "👑 *کامندهای ادمین:*\n\n"
        "/ban <id>\n/unban <id>\n/kick <id>\n"
        "/setbudget <id> <مقدار>\n/addbudget <id> <مقدار>\n"
        "/setoil <id> <مقدار>\n/broadcast <پیام>\n"
        "/players | /adminstats | /adminhelp",parse_mode="Markdown")

async def cmd_players(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    db=load_db()
    txt="👥 بازیکنان:\n"
    for uid,p in db["players"].items():
        c=next((x for x in COUNTRIES if x["id"]==p["country_id"]),None)
        b="🚫" if p.get("banned") else "✅"
        txt+=f"{b} {uid} @{p.get('username','?')} {c['name'] if c else '?'} ${p['budget']:,}\n"
    await update.message.reply_text(txt[:4000] or "کسی نیست")

async def cmd_stats(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    db=load_db()
    await update.message.reply_text(f"📊 بازیکنان:{len(db['players'])} | جنگ:{len(db['wars'])} | بیانیه:{len(db['declarations'])}")

# ═══ زمان‌بندی ═══
async def job_income(context:ContextTypes.DEFAULT_TYPE):
    db=load_db()
    today=datetime.now().strftime("%Y-%m-%d")
    if db.get("last_income")==today: return
    db["last_income"]=today
    kicked=[]
    for uid,p in list(db["players"].items()):
        if p.get("banned"): continue
        try:
            last=datetime.fromisoformat(p.get("last_decl",p.get("joined_at",datetime.now().isoformat())))
            if (datetime.now()-last).days>=3:
                kicked.append(uid); continue
        except: pass
        eq=p.get("equipment",[])
        daily=sum(e.get("daily",0) for e in eq)
        odaily=sum(e.get("oil_daily",0) for e in eq)
        p["budget"]=p.get("budget",0)+daily
        p["oil"]=p.get("oil",0)+odaily
        if daily>0 or odaily>0:
            try: await context.bot.send_message(int(uid),f"💰 *درآمد واریز شد!*\n+${daily:,}\n{f'+{odaily:,} بشکه نفت' if odaily else ''}\nبودجه: ${p['budget']:,}",parse_mode="Markdown")
            except: pass
    for uid in kicked:
        c=next((x for x in COUNTRIES if x["id"]==db["players"][uid].get("country_id","")),None)
        try: await context.bot.send_message(int(uid),"⏰ ۳ روز بیانیه ندادی - اخراج شدی!")
        except: pass
        del db["players"][uid]
    save_db(db)
    wars_t=len([w for w in db["wars"] if w.get("date","").startswith(today)])
    decls_t=len([d for d in db["declarations"] if d.get("date","").startswith(today)])
    try:
        await context.bot.send_message(CHANNEL_ID,
            f"🌙 *گزارش شبانه WW26*\n━━━━━━━━━━━━━━━\n"
            f"💰 درآمدها واریز شد\n👥 بازیکنان: {len(db['players'])}\n"
            f"⚔️ جنگ‌های امروز: {wars_t}\n📜 بیانیه‌های امروز: {decls_t}\n"
            f"🗑️ اخراج: {len(kicked)}",parse_mode="Markdown")
    except: pass

async def job_news(context:ContextTypes.DEFAULT_TYPE):
    db=load_db()
    today=datetime.now().strftime("%Y-%m-%d")
    if db.get("last_news")==today: return
    db["last_news"]=today; save_db(db)
    news=await ai_news(db)
    try: await context.bot.send_message(CHANNEL_ID,news,parse_mode="Markdown")
    except: pass

async def noop(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
async def taken(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("🔒 این کشور گرفته شده!",show_alert=True)
async def back(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    db=load_db()
    uid=str(update.effective_user.id)
    p=db["players"].get(uid)
    if p:
        c=next((x for x in COUNTRIES if x["id"]==p["country_id"]),None)
        kb=[
            [InlineKeyboardButton("📊 وضعیت کشور",callback_data="status"),InlineKeyboardButton("🛒 خرید",callback_data="shop")],
            [InlineKeyboardButton("📜 بیانیه",callback_data="decl"),InlineKeyboardButton("⚔️ جنگ",callback_data="war")],
            [InlineKeyboardButton("🌍 وضعیت بازی",callback_data="world"),InlineKeyboardButton("🔗 دعوت",callback_data="ref")],
            [InlineKeyboardButton("🚪 خروج",callback_data="quit")],
        ]
        if update.effective_user.id==ADMIN_ID:
            kb.append([InlineKeyboardButton("👑 پنل ادمین",callback_data="admin")])
        try:
            await q.edit_message_text(
                f"🌍 *{update.effective_user.first_name}* خوش اومدی!\n\n"
                f"🏳️ {c['name'] if c else '?'}\n💰 ${p.get('budget',0):,}\n🛢️ {p.get('oil',0):,} بشکه",
                parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
        except:
            await q.message.reply_text(
                f"🌍 *{update.effective_user.first_name}* خوش اومدی!\n\n"
                f"🏳️ {c['name'] if c else '?'}\n💰 ${p.get('budget',0):,}\n🛢️ {p.get('oil',0):,} بشکه",
                parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
    else:
        try:
            await q.edit_message_text(
                "🌍⚔️ *WORLD WAR 26* ⚔️🌍\n\nکشور انتخاب کن و وارد شو! 🔥",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌍 انتخاب کشور",callback_data="choose")]]))
        except:
            await q.message.reply_text(
                "🌍⚔️ *WORLD WAR 26* ⚔️🌍\n\nکشور انتخاب کن و وارد شو! 🔥",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌍 انتخاب کشور",callback_data="choose")]]))
async def cancel(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ لغو شد.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))
    return ConversationHandler.END

def main():
    app=Application.builder().token(BOT_TOKEN).build()

    decl_conv=ConversationHandler(
        entry_points=[CallbackQueryHandler(decl_start,pattern="^decl$")],
        states={WAITING_DECL:[MessageHandler(filters.TEXT&~filters.COMMAND,decl_recv)]},
        fallbacks=[CommandHandler("cancel",cancel)])
    war_conv=ConversationHandler(
        entry_points=[CallbackQueryHandler(atk_target,pattern="^atk_")],
        states={WAITING_WAR:[MessageHandler(filters.TEXT&~filters.COMMAND,war_recv)]},
        fallbacks=[CommandHandler("cancel",cancel)])

    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("ban",cmd_ban))
    app.add_handler(CommandHandler("unban",cmd_unban))
    app.add_handler(CommandHandler("kick",cmd_kick))
    app.add_handler(CommandHandler("setbudget",cmd_setbudget))
    app.add_handler(CommandHandler("addbudget",cmd_addbudget))
    app.add_handler(CommandHandler("setoil",cmd_setoil))
    app.add_handler(CommandHandler("broadcast",cmd_broadcast))
    app.add_handler(CommandHandler("adminhelp",cmd_help))
    app.add_handler(CommandHandler("players",cmd_players))
    app.add_handler(CommandHandler("adminstats",cmd_stats))
    app.add_handler(decl_conv)
    app.add_handler(war_conv)
    app.add_handler(CallbackQueryHandler(choose_country,pattern="^choose$"))
    app.add_handler(CallbackQueryHandler(join_country,pattern="^join_"))
    app.add_handler(CallbackQueryHandler(back,pattern="^back$"))
    app.add_handler(CallbackQueryHandler(show_status,pattern="^status$"))
    app.add_handler(CallbackQueryHandler(shop_menu,pattern="^shop$"))
    app.add_handler(CallbackQueryHandler(shop_cat,pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(buy,pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(full_list,pattern="^fulllist$"))
    app.add_handler(CallbackQueryHandler(war_menu,pattern="^war$"))
    app.add_handler(CallbackQueryHandler(world_view,pattern="^world$"))
    app.add_handler(CallbackQueryHandler(ref_menu,pattern="^ref$"))
    app.add_handler(CallbackQueryHandler(quit_ask,pattern="^quit$"))
    app.add_handler(CallbackQueryHandler(quit_yes,pattern="^quit_yes$"))
    app.add_handler(CallbackQueryHandler(adm_panel,pattern="^admin$"))
    app.add_handler(CallbackQueryHandler(adm_p,pattern="^adm_p$"))
    app.add_handler(CallbackQueryHandler(adm_s,pattern="^adm_s$"))
    app.add_handler(CallbackQueryHandler(adm_w,pattern="^adm_w$"))
    app.add_handler(CallbackQueryHandler(adm_d,pattern="^adm_d$"))
    app.add_handler(CallbackQueryHandler(taken,pattern="^taken$"))
    app.add_handler(CallbackQueryHandler(noop,pattern="^noop$"))

    jq=app.job_queue
    jq.run_daily(job_income,time=time(20,30,0))   # ۱۲ شب ایران
    jq.run_daily(job_news,time=time(17,30,0))       # ۹ شب ایران

    print("✅ WW26 Bot v2.0 فعال شد!")
    app.run_polling()

if __name__=="__main__":
    main()
