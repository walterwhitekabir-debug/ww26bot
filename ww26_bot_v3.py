"""
🌍 WORLD WAR 26 - Bot v3.0
نسخه کامل با تمام قابلیت‌ها
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
CHANNEL_LINK = "https://t.me/ww26jang"
START_BUDGET = 250000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DB_FILE = "ww26.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE,"r",encoding="utf-8") as f: return json.load(f)
    return {"players":{},"declarations":[],"wars":[],"trades":[],"referrals":{},
            "last_income":"","last_news":"","occupied":{}}

def save_db(d):
    with open(DB_FILE,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)

GAME_SETTINGS = {"shop":True,"decl":True,"war":True,"trade":True}

COUNTRIES = [
    {"id":"cn","name":"🇨🇳 چین","cont":"🌏 آسیا","oil":False,"nuclear":True,"oil_b":0,"borders":["ru","kz","vn","mm","in","pk","kp","kr"],"sea":True},
    {"id":"ru","name":"🇷🇺 روسیه","cont":"🌏 آسیا/اروپا","oil":True,"nuclear":True,"oil_b":15000,"borders":["cn","kz","ua","pl","no","fi"],"sea":True},
    {"id":"ir","name":"🇮🇷 ایران","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":12000,"borders":["iq","tr","af","az","pk"],"sea":True},
    {"id":"sa","name":"🇸🇦 عربستان","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":20000,"borders":["iq","ae"],"sea":True},
    {"id":"in","name":"🇮🇳 هند","cont":"🌏 آسیا","oil":False,"nuclear":True,"oil_b":0,"borders":["pk","cn","mm","bd"],"sea":True},
    {"id":"pk","name":"🇵🇰 پاکستان","cont":"🌏 آسیا","oil":False,"nuclear":True,"oil_b":0,"borders":["ir","in","af","cn"],"sea":True},
    {"id":"kp","name":"🇰🇵 کره شمالی","cont":"🌏 آسیا","oil":False,"nuclear":True,"oil_b":0,"borders":["cn","kr"],"sea":True},
    {"id":"kr","name":"🇰🇷 کره جنوبی","cont":"🌏 آسیا","oil":False,"nuclear":False,"oil_b":0,"borders":["kp"],"sea":True},
    {"id":"jp","name":"🇯🇵 ژاپن","cont":"🌏 آسیا","oil":False,"nuclear":False,"oil_b":0,"borders":[],"sea":True},
    {"id":"tr","name":"🇹🇷 ترکیه","cont":"🌏 آسیا/اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["ru","ir","iq","gr","sy"],"sea":True},
    {"id":"iq","name":"🇮🇶 عراق","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":10000,"borders":["ir","tr","sa","ae","sy","ku"],"sea":True},
    {"id":"sy","name":"🇸🇾 سوریه","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":3000,"borders":["tr","iq","il"],"sea":True},
    {"id":"ae","name":"🇦🇪 امارات","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":8000,"borders":["sa","iq"],"sea":True},
    {"id":"il","name":"🇮🇱 اسرائیل","cont":"🌏 آسیا","oil":False,"nuclear":True,"oil_b":0,"borders":["eg","sy"],"sea":True},
    {"id":"az","name":"🇦🇿 آذربایجان","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":6000,"borders":["ru","ir","tr"],"sea":True},
    {"id":"kz","name":"🇰🇿 قزاقستان","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":7000,"borders":["ru","cn"],"sea":False},
    {"id":"af","name":"🇦🇫 افغانستان","cont":"🌏 آسیا","oil":False,"nuclear":False,"oil_b":0,"borders":["ir","pk","cn"],"sea":False},
    {"id":"mm","name":"🇲🇲 میانمار","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":2000,"borders":["cn","in","th","bd"],"sea":True},
    {"id":"th","name":"🇹🇭 تایلند","cont":"🌏 آسیا","oil":False,"nuclear":False,"oil_b":0,"borders":["mm","vn","my"],"sea":True},
    {"id":"vn","name":"🇻🇳 ویتنام","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":3000,"borders":["cn","th"],"sea":True},
    {"id":"my","name":"🇲🇾 مالزی","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":4000,"borders":["th"],"sea":True},
    {"id":"id","name":"🇮🇩 اندونزی","cont":"🌏 آسیا","oil":True,"nuclear":False,"oil_b":5000,"borders":[],"sea":True},
    {"id":"ph","name":"🇵🇭 فیلیپین","cont":"🌏 آسیا","oil":False,"nuclear":False,"oil_b":0,"borders":[],"sea":True},
    {"id":"bd","name":"🇧🇩 بنگلادش","cont":"🌏 آسیا","oil":False,"nuclear":False,"oil_b":0,"borders":["in","mm"],"sea":True},
    {"id":"us","name":"🇺🇸 آمریکا","cont":"🌎 آمریکای شمالی","oil":True,"nuclear":True,"oil_b":10000,"borders":["ca","mx"],"sea":True},
    {"id":"gb","name":"🇬🇧 انگلیس","cont":"🌍 اروپا","oil":False,"nuclear":True,"oil_b":0,"borders":[],"sea":True},
    {"id":"fr","name":"🇫🇷 فرانسه","cont":"🌍 اروپا","oil":False,"nuclear":True,"oil_b":0,"borders":["de","es","it","be"],"sea":True},
    {"id":"de","name":"🇩🇪 آلمان","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["fr","pl","nl","be","at","ch"],"sea":True},
    {"id":"it","name":"🇮🇹 ایتالیا","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["fr","at","ch"],"sea":True},
    {"id":"es","name":"🇪🇸 اسپانیا","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["fr","pt","ma"],"sea":True},
    {"id":"pl","name":"🇵🇱 لهستان","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["de","ua","ru","cz"],"sea":True},
    {"id":"ua","name":"🇺🇦 اوکراین","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["ru","pl","ro","hu"],"sea":True},
    {"id":"se","name":"🇸🇪 سوئد","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["no","fi"],"sea":True},
    {"id":"no","name":"🇳🇴 نروژ","cont":"🌍 اروپا","oil":True,"nuclear":False,"oil_b":9000,"borders":["se","ru","fi"],"sea":True},
    {"id":"nl","name":"🇳🇱 هلند","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["de","be"],"sea":True},
    {"id":"be","name":"🇧🇪 بلژیک","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["fr","de","nl"],"sea":True},
    {"id":"gr","name":"🇬🇷 یونان","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["tr","rs","al"],"sea":True},
    {"id":"ro","name":"🇷🇴 رومانی","cont":"🌍 اروپا","oil":True,"nuclear":False,"oil_b":2000,"borders":["ua","rs","hu","bg"],"sea":True},
    {"id":"rs","name":"🇷🇸 صربستان","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["ro","gr","hu","hr"],"sea":False},
    {"id":"ch","name":"🇨🇭 سوئیس","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["de","fr","it","at"],"sea":False},
    {"id":"at","name":"🇦🇹 اتریش","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["de","it","ch","hu"],"sea":False},
    {"id":"fi","name":"🇫🇮 فنلاند","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["se","no","ru"],"sea":True},
    {"id":"pt","name":"🇵🇹 پرتغال","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["es"],"sea":True},
    {"id":"hu","name":"🇭🇺 مجارستان","cont":"🌍 اروپا","oil":False,"nuclear":False,"oil_b":0,"borders":["at","ro","rs","ua"],"sea":False},
    {"id":"br","name":"🇧🇷 برزیل","cont":"🌎 آمریکای جنوبی","oil":True,"nuclear":False,"oil_b":8000,"borders":["ar","co","ve","pe","bo"],"sea":True},
    {"id":"mx","name":"🇲🇽 مکزیک","cont":"🌎 آمریکای شمالی","oil":True,"nuclear":False,"oil_b":6000,"borders":["us"],"sea":True},
    {"id":"ar","name":"🇦🇷 آرژانتین","cont":"🌎 آمریکای جنوبی","oil":True,"nuclear":False,"oil_b":4000,"borders":["br","cl","bo"],"sea":True},
    {"id":"co","name":"🇨🇴 کلمبیا","cont":"🌎 آمریکای جنوبی","oil":True,"nuclear":False,"oil_b":3000,"borders":["br","ve","pe"],"sea":True},
    {"id":"ve","name":"🇻🇪 ونزوئلا","cont":"🌎 آمریکای جنوبی","oil":True,"nuclear":False,"oil_b":9000,"borders":["br","co"],"sea":True},
    {"id":"ca","name":"🇨🇦 کانادا","cont":"🌎 آمریکای شمالی","oil":True,"nuclear":False,"oil_b":8000,"borders":["us"],"sea":True},
    {"id":"cl","name":"🇨🇱 شیلی","cont":"🌎 آمریکای جنوبی","oil":False,"nuclear":False,"oil_b":0,"borders":["ar","pe","bo"],"sea":True},
    {"id":"cu","name":"🇨🇺 کوبا","cont":"🌎 آمریکای شمالی","oil":False,"nuclear":False,"oil_b":0,"borders":[],"sea":True},
    {"id":"pe","name":"🇵🇪 پرو","cont":"🌎 آمریکای جنوبی","oil":True,"nuclear":False,"oil_b":3000,"borders":["br","cl","co","bo"],"sea":True},
    {"id":"ng","name":"🇳🇬 نیجریه","cont":"🌍 آفریقا","oil":True,"nuclear":False,"oil_b":8000,"borders":["cm","bj","ne"],"sea":True},
    {"id":"za","name":"🇿🇦 آفریقای جنوبی","cont":"🌍 آفریقا","oil":False,"nuclear":False,"oil_b":0,"borders":["zw","mz","bw","na"],"sea":True},
    {"id":"eg","name":"🇪🇬 مصر","cont":"🌍 آفریقا","oil":True,"nuclear":False,"oil_b":4000,"borders":["ly","sd","il"],"sea":True},
    {"id":"ly","name":"🇱🇾 لیبی","cont":"🌍 آفریقا","oil":True,"nuclear":False,"oil_b":6000,"borders":["eg","dz","sd","tn"],"sea":True},
    {"id":"dz","name":"🇩🇿 الجزایر","cont":"🌍 آفریقا","oil":True,"nuclear":False,"oil_b":5000,"borders":["ma","ly","tn","ml","mr"],"sea":True},
    {"id":"ma","name":"🇲🇦 مراکش","cont":"🌍 آفریقا","oil":False,"nuclear":False,"oil_b":0,"borders":["dz","es"],"sea":True},
    {"id":"et","name":"🇪🇹 اتیوپی","cont":"🌍 آفریقا","oil":False,"nuclear":False,"oil_b":0,"borders":["sd","so","ke","er"],"sea":False},
    {"id":"sd","name":"🇸🇩 سودان","cont":"🌍 آفریقا","oil":True,"nuclear":False,"oil_b":2000,"borders":["eg","ly","et","ss","cf"],"sea":True},
    {"id":"ke","name":"🇰🇪 کنیا","cont":"🌍 آفریقا","oil":False,"nuclear":False,"oil_b":0,"borders":["et","tz","ug","so"],"sea":True},
    {"id":"gh","name":"🇬🇭 غنا","cont":"🌍 آفریقا","oil":True,"nuclear":False,"oil_b":3000,"borders":["ci","tg","bf"],"sea":True},
    {"id":"ao","name":"🇦🇴 آنگولا","cont":"🌍 آفریقا","oil":True,"nuclear":False,"oil_b":4000,"borders":["cg","zm","na","cd"],"sea":True},
    {"id":"au","name":"🇦🇺 استرالیا","cont":"🌏 اقیانوسیه","oil":True,"nuclear":False,"oil_b":5000,"borders":[],"sea":True},
    {"id":"nz","name":"🇳🇿 نیوزیلند","cont":"🌏 اقیانوسیه","oil":False,"nuclear":False,"oil_b":0,"borders":[],"sea":True},
]

def get_country(cid): return next((c for c in COUNTRIES if c["id"]==cid),None)
def has_land_border(c1id,c2id):
    c1=get_country(c1id)
    return bool(c1 and c2id in c1.get("borders",[]))
def has_sea(cid):
    c=get_country(cid)
    return bool(c and c.get("sea",False))

EQUIP = {
    "✈️ هوایی":[
        {"id":"launcher","name":"🚀 سیستم لانچر","price":40000,"oil":0,"type":"attack","desc":"الزامی برای شلیک موشک"},
        {"id":"f16","name":"🛩️ ۸ جنگنده F-16","price":55000,"oil":0,"type":"attack","desc":"نابودی ۸۰ سرباز یا ۱ تانک"},
        {"id":"f35","name":"🛩️ ۶ جنگنده F-35","price":90000,"oil":0,"type":"attack","desc":"نابودی ۱۵۰ سرباز یا ۲ تانک"},
        {"id":"f22","name":"🛩️ ۴ جنگنده F-22","price":140000,"oil":0,"type":"attack","desc":"نابودی ۲۲۰ سرباز یا ۳ تانک"},
        {"id":"b52","name":"💣 ۳ بمب‌افکن B-52","price":110000,"oil":0,"type":"attack","desc":"نابودی ۵ تانک یا ۳۵۰ سرباز"},
        {"id":"b2","name":"💣 ۲ بمب‌افکن B-2","price":200000,"oil":0,"type":"attack","desc":"رادارگریز - نابودی ۸ تانک"},
        {"id":"apache","name":"🚁 ۸ هلیکوپتر Apache","price":35000,"oil":0,"type":"attack","desc":"نابودی ۳ تانک یا ۱۸۰ سرباز"},
        {"id":"drone","name":"🤖 ۲۰ پهپاد بیرقدار","price":25000,"oil":0,"type":"attack","desc":"نابودی ۱۰۰ سرباز"},
        {"id":"manpad","name":"🛡️ MANPAD","price":30000,"oil":0,"type":"defense","desc":"سرنگونی ۲۰ هلیکوپتر"},
        {"id":"s300","name":"🛡️ سامانه S-300","price":120000,"oil":0,"type":"defense","desc":"سرنگونی ۲۵ جنگنده"},
        {"id":"s400","name":"🛡️ سامانه S-400","price":200000,"oil":0,"type":"defense","desc":"سرنگونی ۴۰ جنگنده"},
    ],
    "🚢 دریایی":[
        {"id":"cargo_ship","name":"🚢 کشتی باربری","price":30000,"oil":0,"type":"transport","desc":"امکان معامله دریایی"},
        {"id":"corvette","name":"⚓ ۳ کوروت رزمی","price":40000,"oil":0,"type":"attack","desc":"پشتیبانی ساحلی"},
        {"id":"frigate","name":"🚢 ۲ فریگات","price":65000,"oil":0,"type":"attack","desc":"نابودی تجهیزات دریایی"},
        {"id":"destroyer","name":"🚢 ناو اژدرافکن","price":100000,"oil":0,"type":"attack","desc":"نابودی ناوچه"},
        {"id":"carrier","name":"🚢 ناو هواپیمابر","price":250000,"oil":0,"type":"attack","desc":"قدرتمندترین کشتی"},
        {"id":"submarine","name":"🌊 ۲ زیردریایی","price":90000,"oil":0,"type":"attack","desc":"حمله مخفیانه"},
        {"id":"nuclear_sub","name":"🌊☢️ زیردریایی اتمی","price":350000,"oil":0,"type":"attack","desc":"فقط کشورهای اتمی"},
        {"id":"coastal_bat","name":"🛡️ باتری ساحلی","price":80000,"oil":0,"type":"defense","desc":"نابودی ۳ فریگات"},
    ],
    "🚀 موشکی":[
        {"id":"grad","name":"🚀 ۲۰۰ راکت گراد","price":15000,"oil":200,"type":"attack","desc":"نابودی ۸۰ سرباز"},
        {"id":"tactical","name":"🚀 ۵۰۰ موشک تاکتیکی","price":30000,"oil":400,"type":"attack","desc":"نابودی ۱۵۰ سرباز"},
        {"id":"cruise","name":"🚀 ۵۰ موشک کروز","price":80000,"oil":1200,"type":"attack","desc":"دقت ۱ متری"},
        {"id":"ballistic","name":"🚀 ۳۰ موشک بالستیک","price":130000,"oil":2000,"type":"attack","desc":"برد ۳۰۰۰ کیلومتر"},
        {"id":"precision","name":"🎯 ۲۰ موشک نقطه‌زن","price":200000,"oil":3500,"type":"attack","desc":"دقت فوق‌العاله"},
        {"id":"hypersonic","name":"⚡ ۱۰ موشک هایپرسونیک","price":300000,"oil":6000,"type":"attack","desc":"ماخ ۱۵ - غیرقابل رهگیری"},
        {"id":"kinzhal","name":"⚡ کینژال","price":250000,"oil":5000,"type":"attack","desc":"هایپرسونیک روسی"},
        {"id":"icbm","name":"🚀🌍 موشک قاره‌پیما","price":400000,"oil":10000,"type":"attack","desc":"برد ۱۲۰۰۰ کیلومتر"},
        {"id":"atom","name":"☢️ بمب اتمی","price":8000000,"oil":0,"type":"attack","desc":"فقط کشورهای اتمی ⚠️"},
        {"id":"neutron","name":"☢️ بمب نوترونی","price":5000000,"oil":0,"type":"attack","desc":"فقط کشورهای اتمی ⚠️"},
        {"id":"cram","name":"🛡️ C-RAM","price":45000,"oil":0,"type":"defense","desc":"رهگیری راکت ۹۵٪"},
        {"id":"patriot","name":"🛡️ پاتریوت","price":90000,"oil":0,"type":"defense","desc":"رهگیری کروز ۸۵٪"},
        {"id":"thaad","name":"🛡️ THAAD","price":180000,"oil":0,"type":"defense","desc":"رهگیری بالستیک ۹۰٪"},
        {"id":"iron_dome","name":"🛡️ گنبد آهنین","price":120000,"oil":0,"type":"defense","desc":"رهگیری راکت ۹۵٪"},
        {"id":"arrow3","name":"🛡️ Arrow-3","price":250000,"oil":0,"type":"defense","desc":"رهگیری هایپرسونیک ۷۰٪"},
    ],
    "🪖 زمینی":[
        {"id":"truck","name":"🚛 ناوگان کامیون","price":20000,"oil":0,"type":"transport","desc":"امکان معامله زمینی"},
        {"id":"infantry","name":"👤 ۵۰۰۰ سرباز پیاده","price":50000,"oil":0,"type":"ground","desc":"نیروی پایه"},
        {"id":"special","name":"🪖 ۲۰۰۰ نیروی ویژه","price":80000,"oil":0,"type":"ground","desc":"آموزش‌دیده"},
        {"id":"marine","name":"⚓ ۱۰۰۰ تفنگدار","price":70000,"oil":0,"type":"ground","desc":"عملیات آبی‌خاکی"},
        {"id":"para","name":"🪂 ۵۰۰ چترباز","price":60000,"oil":0,"type":"ground","desc":"حمله از هوا"},
        {"id":"rpg","name":"💥 ۵۰۰ RPG","price":30000,"oil":0,"type":"attack","desc":"ضد زره"},
        {"id":"javelin","name":"🎯 جاولین","price":60000,"oil":0,"type":"attack","desc":"ضد تانک پیشرفته"},
        {"id":"t72","name":"🚓 ۵۰ تانک T-72","price":45000,"oil":0,"type":"ground","desc":"تانک قابل اطمینان"},
        {"id":"abrams","name":"🦾 ۳۰ تانک Abrams","price":100000,"oil":0,"type":"ground","desc":"بهترین تانک"},
        {"id":"howitzer","name":"🎯 ۱۰ هویتزر","price":40000,"oil":0,"type":"attack","desc":"برد ۴۰ کیلومتر"},
        {"id":"mlrs","name":"🚀 MLRS","price":70000,"oil":0,"type":"attack","desc":"راکت‌انداز چندلوله"},
        {"id":"himars","name":"🎯 HIMARS","price":90000,"oil":0,"type":"attack","desc":"دقیق‌ترین توپخانه"},
        {"id":"trench","name":"🛡️ سنگر","price":20000,"oil":0,"type":"defense","desc":"کاهش ۳۰٪ تلفات"},
        {"id":"gdef_light","name":"🛡️ دفاع زمینی سبک","price":80000,"oil":0,"type":"defense","desc":"کاهش ۶۰٪ تلفات"},
        {"id":"gdef_mid","name":"🛡️ دفاع زمینی متوسط","price":140000,"oil":0,"type":"defense","desc":"کاهش ۱۰۰٪ تلفات"},
        {"id":"gdef_heavy","name":"🛡️ دفاع زمینی سنگین","price":220000,"oil":0,"type":"defense","desc":"خنثی یک موج کامل"},
    ],
    "⛏️ اقتصادی":[
        {"id":"iron","name":"⛏️ معدن آهن","price":10000,"oil":0,"type":"economy","daily":4000,"desc":"۴,۰۰۰$/روز"},
        {"id":"copper","name":"⛏️ معدن مس","price":15000,"oil":0,"type":"economy","daily":6000,"desc":"۶,۰۰۰$/روز"},
        {"id":"silver","name":"⛏️ معدن نقره","price":22000,"oil":0,"type":"economy","daily":9000,"desc":"۹,۰۰۰$/روز"},
        {"id":"gold","name":"⛏️ معدن طلا","price":35000,"oil":0,"type":"economy","daily":14000,"desc":"۱۴,۰۰۰$/روز"},
        {"id":"diamond","name":"⛏️ معدن الماس","price":60000,"oil":0,"type":"economy","daily":22000,"desc":"۲۲,۰۰۰$/روز"},
        {"id":"uranium","name":"☢️ معدن اورانیوم","price":80000,"oil":0,"type":"economy","daily":30000,"desc":"فقط اتمی - ۳۰,۰۰۰$/روز"},
        {"id":"refinery","name":"🛢️ پالایشگاه نفت","price":50000,"oil":0,"type":"economy","daily":0,"oil_daily":1500,"desc":"فقط نفتی - ۱۵۰۰ بشکه/روز"},
        {"id":"oil_plat","name":"🛢️ سکوی نفتی","price":90000,"oil":0,"type":"economy","daily":0,"oil_daily":3000,"desc":"فقط نفتی - ۳۰۰۰ بشکه/روز"},
        {"id":"factory","name":"🏭 کارخانه","price":70000,"oil":0,"type":"economy","daily":15000,"desc":"۱۵,۰۰۰$/روز"},
        {"id":"port","name":"⚓ بندر","price":45000,"oil":0,"type":"economy","daily":10000,"desc":"۱۰,۰۰۰$/روز"},
        {"id":"bank","name":"🏦 بانک مرکزی","price":100000,"oil":0,"type":"economy","daily":25000,"desc":"۲۵,۰۰۰$/روز"},
    ],
    "🖥️ سایبری":[
        {"id":"hack","name":"💻 واحد هک تهاجمی","price":150000,"oil":0,"type":"attack","desc":"فلج زیرساخت دشمن"},
        {"id":"spy","name":"🔍 جاسوسی سایبری","price":100000,"oil":0,"type":"attack","desc":"اطلاعات محرمانه"},
        {"id":"antihack","name":"🛡️ ضدهک","price":80000,"oil":0,"type":"defense","desc":"دفع هک"},
        {"id":"antivirus","name":"🛡️ آنتی‌ویروس","price":120000,"oil":0,"type":"defense","desc":"محافظت دیجیتال"},
        {"id":"satellite","name":"🛸 ماهواره جاسوسی","price":200000,"oil":0,"type":"attack","desc":"رصد دشمن"},
        {"id":"radar","name":"📡 رادار پیشرفته","price":90000,"oil":0,"type":"defense","desc":"شناسایی از ۵۰۰km"},
        {"id":"jammer","name":"📡 جمر الکترونیکی","price":70000,"oil":0,"type":"defense","desc":"۵۰٪ کاهش دقت موشک"},
        {"id":"emp","name":"💥 بمب EMP","price":250000,"oil":0,"type":"attack","desc":"فلج الکترونیک"},
    ],
}

PROFANITY = ["کس","کیر","کون","جنده","مادرجنده","بیشعور","خر","گاو","الاغ","احمق","لاشی","عوضی","اشغال","بی‌ناموس","ناموس","fuck","shit","bitch","ass","dick","pussy"]

WEAPON_KEYWORDS = {
    "بمب اتم":["atom"],"اتمی":["atom","neutron"],"نوترون":["neutron"],
    "موشک کروز":["cruise"],"کروز":["cruise"],"بالستیک":["ballistic"],
    "هایپرسونیک":["hypersonic","kinzhal"],"قاره پیما":["icbm"],"قاره‌پیما":["icbm"],
    "f35":["f35"],"f-35":["f35"],"f22":["f22"],"f-22":["f22"],
    "b52":["b52"],"b-52":["b52"],"b2":["b2"],
    "ناو هواپیمابر":["carrier"],"زیردریایی":["submarine","nuclear_sub"],
    "ابرامز":["abrams"],"تانک سنگین":["abrams"],
    "پهپاد":["drone"],"بیرقدار":["drone"],
    "himars":["himars"],"هیمارس":["himars"],
    "s400":["s400"],"s-400":["s400"],"s300":["s300"],"s-300":["s300"],
    "گنبد آهنین":["iron_dome"],"پاتریوت":["patriot"],"thaad":["thaad"],
    "هک":["hack"],"سایبری":["hack","spy"],
    "ماهواره":["satellite"],"emp":["emp"],
    "هلیکوپتر":["apache"],"اپاچی":["apache"],
    "grad":["grad"],"گراد":["grad"],
    "kinzhal":["kinzhal"],"کینژال":["kinzhal"],
}

WAITING_DECL_PHOTO=1; WAITING_WAR=2; WAITING_TRADE_DETAIL=3
WAITING_ALLIANCE_INFO=4; WAITING_TRADE_OFFER=5; WAITING_TRADE_REQUEST=6

def get_ai(): return anthropic.Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None

def check_scenario(scenario, equip_list):
    equip_ids={e["id"] for e in equip_list}
    sc_lower=scenario.lower()
    missing=[]
    for kw,needed in WEAPON_KEYWORDS.items():
        if kw in sc_lower:
            if not any(n in equip_ids for n in needed):
                missing.append(kw)
    return missing

async def ai_check_scenario(scenario, equip_list):
    """AI سناریو رو با تجهیزات واقعی مقایسه میکنه"""
    client=get_ai()
    equip_names=[e['name'] for e in equip_list]
    if not client:
        missing=check_scenario(scenario,equip_list)
        if missing:
            return {"valid":False,"reason":f"تجهیزات زیر رو نداری: {', '.join(missing)}"}
        return {"valid":True,"reason":""}
    try:
        r=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=300,
            system='تو بررسی‌کننده سناریوی نظامی هستی. سناریو رو با لیست تجهیزات واقعی بازیکن مقایسه کن. اگه از سلاحی استفاده کرده که ندارد رد کن. فقط JSON: {"valid":true/false,"reason":"دلیل فارسی"}',
            messages=[{"role":"user","content":f"تجهیزات بازیکن:\n{chr(10).join('- '+n for n in equip_names)}\n\nسناریو:\n{scenario}"}])
        return json.loads(r.content[0].text.strip().replace("```json","").replace("```",""))
    except:
        missing=check_scenario(scenario,equip_list)
        if missing:
            return {"valid":False,"reason":f"تجهیزات زیر رو نداری: {', '.join(missing)}"}
        return {"valid":True,"reason":""}

async def ai_check_decl(country,text):
    for bad in PROFANITY:
        if bad.lower() in text.lower():
            return {"approved":False,"reason":"بیانیه حاوی کلمه نامناسب است","edited":text}
    if len(text.strip())<30:
        return {"approved":False,"reason":"بیانیه خیلی کوتاه است","edited":text}
    client=get_ai()
    if not client: return {"approved":True,"reason":"تایید","edited":text}
    try:
        r=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=500,
            system='ناظر بازی جنگ جهانی ۲۶. سختگیرانه رد کن اگه: فحش، توهین، بی‌معنی یا غیررسمی. JSON: {"approved":true/false,"reason":"فارسی","edited":"متن"}',
            messages=[{"role":"user","content":f"کشور:{country}\n{text}"}])
        return json.loads(r.content[0].text.strip().replace("```json","").replace("```",""))
    except: return {"approved":True,"reason":"تایید","edited":text}

async def ai_war(atk_c,def_c,atk_p,def_p,scenario):
    client=get_ai()
    atk_eq_list=[e for e in atk_p.get('equipment',[]) if e.get('type') in ['attack','ground']]
    def_eq_list=[e for e in def_p.get('equipment',[]) if e.get('type')=='defense']
    gnd_list=[e for e in atk_eq_list if e.get('type')=='ground']
    atk_txt="\n".join(f"- {e['name']}: {e['desc']}" for e in atk_eq_list) or "❌ هیچ"
    def_txt="\n".join(f"- {e['name']}: {e['desc']}" for e in def_eq_list) or "❌ هیچ"
    if not client:
        return {"sat":f"📡 فعالیت نظامی در {atk_c['name']} رصد شد","winner":"defender",
                "atk_loss":35,"def_loss":20,"story":"نبرد رخ داد.","territory":"بدون تغییر",
                "civilian":False,"fine":0,"occupied":False}
    try:
        r=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=1200,
            system='''تو تحلیلگر نظامی ارشد بازی جنگ جهانی ۲۶ هستی. گزارش نبرد باید خیلی دقیق و سینمایی باشه.

قوانین تحلیل:
- فقط از تجهیزات لیست‌شده استفاده کن - اگه سناریو با تجهیزات تناقض داشت واقعیت رو بنویس
- اشغال فقط با نیروی زمینی ممکنه (infantry/special/marine/t72/abrams/para)
- اگه بمب اتم: فاجعه هسته‌ای کامل با تعداد دقیق کشته و شهرهای نابودشده

گزارش story باید شامل باشه:
- اسم شهرهای واقعی که درگیر شدن
- تعداد دقیق تلفات (مثلاً ۲,۳۰۰ کشته، ۵,۰۰۰ زخمی)
- چه تجهیزاتی دقیقاً استفاده شد
- چه اتفاقاتی افتاد قدم به قدم
- وضعیت نهایی میدان نبرد

JSON دقیق:
{"sat":"خبر ماهواره هیجان‌انگیز ۲ جمله فارسی","winner":"attacker یا defender","atk_loss":عدد_درصد,"def_loss":عدد_درصد,"story":"گزارش کامل ۶-۸ جمله با جزئیات دقیق شهرها و تلفات","territory":"وضعیت ارضی دقیق","civilian":true/false,"fine":عدد,"occupied":true/false}''',
            messages=[{"role":"user","content":f"حمله: {atk_c['name']} vs {def_c['name']}\nتجهیزات حمله:\n{atk_txt}\nتجهیزات دفاع:\n{def_txt}\nنیروی زمینی: {len(gnd_list)}\nسناریو: {scenario}"}])
        return json.loads(r.content[0].text.strip().replace("```json","").replace("```",""))
    except:
        return {"sat":"📡 فعالیت نظامی رصد شد","winner":"defender","atk_loss":30,"def_loss":15,
                "story":"نبرد رخ داد.","territory":"بدون تغییر","civilian":False,"fine":0,"occupied":False}

async def ai_trade_route(from_c,to_c,method,goods):
    client=get_ai()
    if not client: return f"مسیر {method} از {from_c} به {to_c}"
    try:
        r=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=200,
            system="متخصص جغرافیا. مسیر واقعی رو با اسم دریاها/جاده‌ها و جزئیات بنویس. فارسی. ۲-۳ جمله.",
            messages=[{"role":"user","content":f"مسیر {method} از {from_c} به {to_c} برای {goods}"}])
        return r.content[0].text
    except: return f"مسیر {method} از {from_c} به {to_c}"

async def ai_news(db):
    client=get_ai()
    wars=db.get('wars',[])[-5:]; decls=db.get('declarations',[])[-5:]
    if not client: return "📺 *BBC WW26*\nگزارش امروز آماده نشد."
    try:
        wt="\n".join(f"- {w['atk']} ⚔️ {w['def']} → {w['winner']}" for w in wars) or "جنگی نبود"
        r=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=500,
            system="خبرنگار BBC فارسی. گزارش شبانه بازی جنگ جهانی ۲۶ رو هیجان‌انگیز بنویس.",
            messages=[{"role":"user","content":f"بازیکنان:{len(db['players'])}\nجنگ‌ها:\n{wt}"}])
        return f"📺 *BBC World War 26 | گزارش شبانه*\n━━━━━━━━━━━━━━━\n{r.content[0].text}"
    except: return "📺 BBC WW26 | گزارش امروز"

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    db=load_db(); uid=str(update.effective_user.id)
    if context.args and uid not in db["players"]:
        ref=context.args[0]
        if ref!=uid and ref in db["players"] and uid not in db["referrals"]:
            db["players"][ref]["budget"]=db["players"][ref].get("budget",0)+15000
            db["referrals"][uid]=ref; save_db(db)
            try: await context.bot.send_message(int(ref),"🎁 بازیکن جدید!\n💰 +15,000$")
            except: pass
    p=db["players"].get(uid)
    if not p and update.effective_user.id==ADMIN_ID:
        kb=[[InlineKeyboardButton("👑 پنل ادمین",callback_data="admin")],[InlineKeyboardButton("🌍 انتخاب کشور",callback_data="choose")]]
        await update.message.reply_text(f"👑 *خوش اومدی ادمین!*\n📢 {CHANNEL_LINK}",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
        return
    if p:
        c=get_country(p["country_id"])
        occ=db.get("occupied",{}); my_occ=[k for k,v in occ.items() if v==uid]
        kb=[
            [InlineKeyboardButton("📊 وضعیت کشور",callback_data="status"),InlineKeyboardButton("🛒 خرید تجهیزات",callback_data="shop")],
            [InlineKeyboardButton("📜 بیانیه رسمی",callback_data="decl"),InlineKeyboardButton("⚔️ اعلام جنگ",callback_data="war")],
            [InlineKeyboardButton("🤝 معامله",callback_data="trade_menu"),InlineKeyboardButton("🔗 دعوت دوستان",callback_data="ref")],
            [InlineKeyboardButton("📖 آموزش بازی",callback_data="tutorial"),InlineKeyboardButton("🚪 خروج از بازی",callback_data="quit")],
        ]
        if update.effective_user.id==ADMIN_ID: kb.append([InlineKeyboardButton("👑 پنل ادمین",callback_data="admin")])
        occ_txt=f"\n🏴 کشورهای تصرفی: {len(my_occ)}" if my_occ else ""
        await update.message.reply_text(
            f"🌍 *{update.effective_user.first_name}* خوش اومدی!\n\n"
            f"🏳️ {c['name'] if c else '?'}\n💰 ${p.get('budget',0):,}\n🛢️ {p.get('oil',0):,} بشکه{occ_txt}\n\n📢 {CHANNEL_LINK}",
            parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
    else:
        kb=[[InlineKeyboardButton("🌍 انتخاب کشور و ورود",callback_data="choose")],[InlineKeyboardButton("📖 آموزش بازی",callback_data="tutorial")]]
        await update.message.reply_text(f"🌍⚔️ *WORLD WAR 26* ⚔️🌍\n\nکشور انتخاب کن و وارد شو! 🔥\n\n📢 {CHANNEL_LINK}",
            parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def choose_country(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    db=load_db(); taken={p["country_id"] for p in db["players"].values()}
    occupied=set(db.get("occupied",{}).keys())
    conts={}
    for c in COUNTRIES: conts.setdefault(c["cont"],[]).append(c)
    kb=[]
    for cont,cs in conts.items():
        kb.append([InlineKeyboardButton(f"━ {cont} ━",callback_data="noop")])
        row=[]
        for c in cs:
            t=c["id"] in taken; oc=c["id"] in occupied
            props=("🛢️" if c["oil"] else "")+("☢️" if c["nuclear"] else "")
            if t: lbl=f"🔒{c['name'].split(' ',1)[1]}"
            elif oc: lbl=f"🟠{c['name'].split(' ',1)[1]}(تصرفی)"
            else: lbl=f"✅{c['name'].split(' ',1)[1]}{props}"
            row.append(InlineKeyboardButton(lbl,callback_data=f"join_{c['id']}" if not t and not oc else "taken"))
            if len(row)==2: kb.append(row); row=[]
        if row: kb.append(row)
    kb.append([InlineKeyboardButton("🔙",callback_data="back")])
    await q.edit_message_text("🌍 *انتخاب کشور*\n✅آزاد 🔒گرفته 🟠تصرف‌شده\n🛢️نفت ☢️اتمی",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def join_country(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    cid=q.data.replace("join_",""); db=load_db(); uid=str(update.effective_user.id)
    if uid in db["players"]: await q.edit_message_text("❌ قبلاً کشور داری! /start"); return
    if cid in {p["country_id"] for p in db["players"].values()}: await q.edit_message_text("❌ گرفته شده!"); return
    c=get_country(cid)
    if not c: return
    db["players"][uid]={"user_id":uid,"username":update.effective_user.username or "?",
        "first_name":update.effective_user.first_name,"country_id":cid,
        "budget":START_BUDGET,"oil":c["oil_b"],"equipment":[],
        "joined_at":datetime.now().isoformat(),"last_decl":datetime.now().isoformat(),"banned":False,
        "borders":{"air":False,"land":False,"sea":False}}
    save_db(db)
    props=[]
    if c["oil"]: props.append("🛢️نفت")
    if c["nuclear"]: props.append("☢️اتمی")
    await q.edit_message_text(f"✅ *{c['name']}* انتخاب شد!\n💰 ${START_BUDGET:,}\n🛢️ {c['oil_b']:,} بشکه\n🌍 {c['cont']}\n{' | '.join(props) if props else 'معمولی'}\n\nبجنگ! ⚔️",
        parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 پنل",callback_data="back")]]))
    try: await context.bot.send_message(ADMIN_ID,f"🔔 {update.effective_user.first_name} → {c['name']}")
    except: pass

async def show_status(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    db=load_db(); uid=str(update.effective_user.id); p=db["players"].get(uid)
    if not p: await q.edit_message_text("❌ /start"); return
    c=get_country(p["country_id"]); eq=p.get("equipment",[])
    atk=[e for e in eq if e.get("type") in ["attack","ground"]]
    defn=[e for e in eq if e.get("type")=="defense"]
    econ=[e for e in eq if e.get("type")=="economy"]
    trans=[e for e in eq if e.get("type")=="transport"]
    daily=sum(e.get("daily",0) for e in econ); odaily=sum(e.get("oil_daily",0) for e in econ)
    occ=db.get("occupied",{}); my_occ=[get_country(k) for k,v in occ.items() if v==uid]
    bc=p.get("borders",{"air":False,"land":False,"sea":False})
    txt=(f"📊 *وضعیت {c['name']}*\n━━━━━━━━━━━━━━━\n"
        f"💰 ${p['budget']:,} | 🛢️ {p.get('oil',0):,} بشکه\n"
        f"📈 ${daily:,}/روز | 🛢️ {odaily:,} بشکه/روز\n"
        f"🌍 {c.get('cont','')} | 🛢️{'✅' if c['oil'] else '❌'} | ☢️{'✅' if c['nuclear'] else '❌'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"✈️{'🔒' if bc.get('air') else '✅'} | 🛣️{'🔒' if bc.get('land') else '✅'} | 🌊{'🔒' if bc.get('sea') else '✅'} مرزها\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚔️ حمله ({len(atk)}):\n")
    for e in atk: txt+=f"  • {e['name']}\n"
    txt+=f"🛡️ دفاع ({len(defn)}):\n"
    for e in defn: txt+=f"  • {e['name']}\n"
    txt+=f"🚛 حمل‌ونقل ({len(trans)}):\n"
    for e in trans: txt+=f"  • {e['name']}\n"
    txt+=f"⛏️ اقتصادی ({len(econ)}):\n"
    for e in econ: txt+=f"  • {e['name']}\n"
    if my_occ:
        txt+=f"━━━━━━━━━━━━━━━\n🏴 تصرفی:\n"
        for oc in my_occ:
            if oc: txt+=f"  • {oc['name']}\n"
    kb=[[InlineKeyboardButton("🚧 مرزها",callback_data="borders"),InlineKeyboardButton("🔙",callback_data="back")]]
    await q.edit_message_text(txt,parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def borders_menu(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    db=load_db(); uid=str(update.effective_user.id); p=db["players"].get(uid)
    if not p: return
    bc=p.get("borders",{"air":False,"land":False,"sea":False})
    kb=[
        [InlineKeyboardButton(f"✈️ مرز هوایی {'🔒بستن' if not bc.get('air') else '✅بازکردن'}",callback_data="border_air")],
        [InlineKeyboardButton(f"🛣️ مرز زمینی {'🔒بستن' if not bc.get('land') else '✅بازکردن'}",callback_data="border_land")],
        [InlineKeyboardButton(f"🌊 مرز دریایی {'🔒بستن' if not bc.get('sea') else '✅بازکردن'}",callback_data="border_sea")],
        [InlineKeyboardButton("🔙",callback_data="status")],
    ]
    await q.edit_message_text("🚧 *مدیریت مرزها*",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def toggle_border(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    btype=q.data.replace("border_",""); db=load_db(); uid=str(update.effective_user.id); p=db["players"].get(uid)
    if not p: return
    c=get_country(p["country_id"]); bc=p.setdefault("borders",{"air":False,"land":False,"sea":False})
    bc[btype]=not bc.get(btype,False); db["players"][uid]=p; save_db(db)
    status="🔒 بسته" if bc[btype] else "✅ باز"
    bnames={"air":"هوایی","land":"زمینی","sea":"دریایی"}
    try: await context.bot.send_message(CHANNEL_ID,f"🚧 *اطلاعیه*\n\n{c['name']} مرز {bnames[btype]} را {status} کرد.",parse_mode="Markdown")
    except: pass
    await borders_menu(update,context)

async def shop_menu(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not GAME_SETTINGS.get("shop",True) and update.effective_user.id!=ADMIN_ID:
        await q.edit_message_text("🔒 فروشگاه بسته!",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]])); return
    db=load_db(); uid=str(update.effective_user.id); p=db["players"].get(uid)
    if not p: await q.edit_message_text("❌ /start"); return
    kb=[[InlineKeyboardButton(cat,callback_data=f"cat_{cat}")] for cat in EQUIP]
    kb+=[[InlineKeyboardButton("📋 لیست کامل",callback_data="fulllist")],[InlineKeyboardButton("🔙",callback_data="back")]]
    await q.edit_message_text(f"🛒 *فروشگاه*\n💰 ${p['budget']:,} | 🛢️ {p.get('oil',0):,}",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def shop_cat(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); cat=q.data.replace("cat_","")
    db=load_db(); uid=str(update.effective_user.id); p=db["players"].get(uid)
    if not p: return
    kb=[]
    for it in EQUIP.get(cat,[]):
        o=f"+{it['oil']:,}🛢️" if it.get("oil") else ""
        kb.append([InlineKeyboardButton(f"{it['name']} ${it['price']:,}{o}",callback_data=f"buy_{it['id']}")])
    kb.append([InlineKeyboardButton("🔙",callback_data="shop")])
    await q.edit_message_text(f"🛒 *{cat}*\n💰 ${p['budget']:,} | 🛢️ {p.get('oil',0):,}",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def buy(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; iid=q.data.replace("buy_",""); db=load_db(); uid=str(update.effective_user.id); p=db["players"].get(uid)
    if not p: await q.answer("❌",show_alert=True); return
    item=next((it for cat in EQUIP.values() for it in cat if it["id"]==iid),None)
    if not item: await q.answer("پیدا نشد!",show_alert=True); return
    if p["budget"]<item["price"]: await q.answer(f"❌ بودجه کم! ${item['price']:,}",show_alert=True); return
    if item.get("oil",0) and p.get("oil",0)<item["oil"]: await q.answer("❌ نفت کم!",show_alert=True); return
    c=get_country(p["country_id"])
    if item["id"] in ["refinery","oil_plat"] and (not c or not c.get("oil")):
        await q.answer("❌ فقط کشورهای نفتی!",show_alert=True); return
    if item["id"]=="uranium" and (not c or not c.get("nuclear")):
        await q.answer("❌ فقط کشورهای اتمی!",show_alert=True); return
    if item["id"] in ["atom","neutron","nuclear_sub"] and (not c or not c.get("nuclear")):
        await q.answer("☢️ فقط کشورهای اتمی!",show_alert=True); return
    p["budget"]-=item["price"]
    if item.get("oil"): p["oil"]-=item["oil"]
    p.setdefault("equipment",[]).append(item); db["players"][uid]=p; save_db(db)
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
    if not GAME_SETTINGS.get("decl",True) and update.effective_user.id!=ADMIN_ID:
        await q.edit_message_text("🔒 بیانیه بسته!",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]])); return ConversationHandler.END
    db=load_db(); uid=str(update.effective_user.id)
    if uid not in db["players"]: await q.edit_message_text("❌ /start"); return ConversationHandler.END
    if db["players"][uid].get("banned"): await q.edit_message_text("🚫 بن هستید!"); return ConversationHandler.END
    await q.edit_message_text("📜 *بیانیه رسمی*\n\n📸 عکس رییس‌جمهور یا پرچم بفرست\n✍️ متن بیانیه رو زیر عکس (کپشن) بنویس\n\n✅ رسمی | ❌ بدون فحش",parse_mode="Markdown")
    return WAITING_DECL_PHOTO

async def decl_recv_photo(update:Update,context:ContextTypes.DEFAULT_TYPE):
    db=load_db(); uid=str(update.effective_user.id); p=db["players"].get(uid)
    if not p: return ConversationHandler.END
    c=get_country(p["country_id"])
    if not update.message.photo:
        await update.message.reply_text("❌ باید عکس بفرستی با متن زیرش!")
        return WAITING_DECL_PHOTO
    caption=update.message.caption or ""
    if len(caption.strip())<20:
        await update.message.reply_text("❌ متن خیلی کوتاهه! دوباره بفرست.")
        return WAITING_DECL_PHOTO
    await update.message.reply_text("⏳ AI بررسی می‌کنه...")
    r=await ai_check_decl(c["name"],caption)
    if r["approved"]:
        now=datetime.now()
        date_str=f"{now.year}/{now.month}/{now.day}"
        # پیدا کردن اتحاد پلیر
        alliance_name=""
        for aid,al in db.get("alliances",{}).items():
            if uid in al.get("members",[]) or uid==al.get("leader"):
                alliance_name=al.get("name","")
                break
        position=f"{c['name']} | {c.get('cont','')}"
        if alliance_name: position+=f" | اتحاد {alliance_name}"

        formatted=(
            f"⊱⋅ ──────────────────── ⋅⊰\n\n"
            f"❮ 🎖 ❯ ◈ —⊱ ؛ صادر کننده: {c['name']}\n"
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
        db["declarations"].append({"id":len(db["declarations"])+1,"user_id":uid,"country":c["name"],"text":r["edited"],"date":datetime.now().isoformat()})
        db["players"][uid]["last_decl"]=datetime.now().isoformat(); save_db(db)
        try:
            await context.bot.send_photo(CHANNEL_ID,photo=update.message.photo[-1].file_id,caption=formatted)
            await update.message.reply_text("✅ بیانیه تایید و در کانال منتشر شد!")
        except Exception as e: await update.message.reply_text(f"✅ تایید شد - خطای کانال: {e}")
    else:
        await update.message.reply_text(f"❌ رد شد!\n💬 {r['reason']}")
    await update.message.reply_text(".",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پنل",callback_data="back")]]))
    return ConversationHandler.END

async def decl_recv_text(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ باید عکس بفرستی با متن زیرش (کپشن)!")
    return WAITING_DECL_PHOTO

async def war_menu(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not GAME_SETTINGS.get("war",True) and update.effective_user.id!=ADMIN_ID:
        await q.edit_message_text("🔒 جنگ بسته!",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]])); return
    db=load_db(); uid=str(update.effective_user.id); p=db["players"].get(uid)
    if not p: await q.edit_message_text("❌ /start"); return
    if p.get("banned"): await q.edit_message_text("🚫 بن!"); return
    atk_eq=[e for e in p.get('equipment',[]) if e.get('type') in ['attack','ground']]
    if not atk_eq:
        await q.edit_message_text("❌ هیچ تجهیز نظامی ندارید!\nاول از فروشگاه بخرید.",parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛒 فروشگاه",callback_data="shop"),InlineKeyboardButton("🔙",callback_data="back")]])); return
    others={k:v for k,v in db["players"].items() if k!=uid and not v.get("banned")}
    if not others:
        await q.edit_message_text("⚔️ بازیکن دیگه‌ای نیست!",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]])); return
    kb=[]
    for k,v in others.items():
        c=get_country(v["country_id"])
        if c: kb.append([InlineKeyboardButton(f"⚔️ {c['name']}",callback_data=f"atk_{k}")])
    kb.append([InlineKeyboardButton("🔙",callback_data="back")])
    await q.edit_message_text("⚔️ *هدف حمله:*",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def atk_target(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    tid=q.data.replace("atk_",""); context.user_data["target"]=tid
    db=load_db(); uid=str(update.effective_user.id); p=db["players"].get(uid)
    atk_eq=[e for e in p.get('equipment',[]) if e.get('type') in ['attack','ground']]
    eq_txt="\n".join(f"• {e['name']}" for e in atk_eq)
    await q.edit_message_text(
        f"📋 *سناریو حمله*\n\n🔫 *تجهیزات واقعی شما:*\n{eq_txt}\n\n"
        f"⚠️ فقط از همین تجهیزات استفاده کن!\n✍️ سناریو بنویس:",
        parse_mode="Markdown")
    return WAITING_WAR

async def war_recv(update:Update,context:ContextTypes.DEFAULT_TYPE):
    db=load_db(); uid=str(update.effective_user.id); tid=context.user_data.get("target")
    atk_p=db["players"].get(uid); def_p=db["players"].get(tid)
    if not atk_p or not def_p: return ConversationHandler.END
    ac=get_country(atk_p["country_id"]); dc=get_country(def_p["country_id"]); scenario=update.message.text
    atk_eq=[e for e in atk_p.get('equipment',[]) if e.get('type') in ['attack','ground']]
    if not atk_eq:
        await update.message.reply_text("❌ هیچ تجهیزی ندارید!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛒",callback_data="shop")]])); return ConversationHandler.END
    missing=check_scenario(scenario,atk_eq)
    if missing:
        await update.message.reply_text(
            f"❌ *سناریو تایید نشد!*\n\n"
            f"این تجهیزات رو در سناریو نوشتی ولی نداری:\n🚫 {', '.join(missing)}\n\n"
            f"سناریو رو بر اساس تجهیزاتی که *واقعاً داری* بنویس.",
            parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))
        return ConversationHandler.END
    # چک عمیق‌تر با AI
    await update.message.reply_text("🔍 در حال بررسی سناریو با AI...")
    check=await ai_check_scenario(scenario,atk_eq)
    if not check.get("valid",True):
        await update.message.reply_text(
            f"❌ *سناریو تایید نشد!*\n\n💬 {check.get('reason','')}\n\n"
            f"سناریو رو بر اساس تجهیزاتی که *واقعاً داری* بنویس.",
            parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پنل",callback_data="back")]]))
        return ConversationHandler.END
    await update.message.reply_text("⏳ AI داره نبرد رو تحلیل می‌کنه...")
    r=await ai_war(ac,dc,atk_p,def_p,scenario)
    winner=ac["name"] if r["winner"]=="attacker" else dc["name"]
    loser=dc["name"] if r["winner"]=="attacker" else ac["name"]
    occ_msg=""
    if r.get("occupied") and r["winner"]=="attacker":
        db.setdefault("occupied",{})[dc["id"]]=uid
        atk_p["budget"]=atk_p.get("budget",0)+def_p.get("budget",0)
        atk_p["oil"]=atk_p.get("oil",0)+def_p.get("oil",0)
        atk_p["equipment"]=atk_p.get("equipment",[])+def_p.get("equipment",[])
        db["players"][uid]=atk_p
        occ_msg=f"\n\n🏴 *{ac['name']} کشور {dc['name']} را اشغال کرد!*\nتمام دارایی‌ها منتقل شد!"
    un=""
    if r.get("civilian") and r.get("fine",0)>0:
        fine=r["fine"]; db["players"][uid]["budget"]=db["players"][uid].get("budget",0)-fine
        un=f"\n\n🏛️ *سازمان ملل:*\n{ac['name']} ${fine:,} جریمه شد!"
    db["wars"].append({"id":len(db["wars"])+1,"atk":ac["name"],"def":dc["name"],"winner":winner,"atk_loss":r["atk_loss"],"def_loss":r["def_loss"],"date":datetime.now().isoformat()})
    save_db(db)
    atk_names=[e['name'] for e in atk_eq[:3]]; def_eq=[e for e in def_p.get('equipment',[]) if e.get('type')=='defense']; def_names=[e['name'] for e in def_eq[:3]]
    txt=(f"📡 {r.get('sat','')}\n\n⚔️ *گزارش کامل نبرد*\n━━━━━━━━━━━━━━━\n"
        f"🔴 {ac['name']}\n  🔫 {', '.join(atk_names)}{'...' if len(atk_eq)>3 else ''}\n\n"
        f"🔵 {dc['name']}\n  🛡️ {', '.join(def_names) if def_names else 'بدون پدافند'}{'...' if len(def_eq)>3 else ''}\n"
        f"━━━━━━━━━━━━━━━\n\n📰 *شرح نبرد:*\n{r['story']}\n\n━━━━━━━━━━━━━━━\n"
        f"🏆 *برنده: {winner}*\n💀 *بازنده: {loser}*\n\n"
        f"📉 تلفات {ac['name']}: {r['atk_loss']}%\n📉 تلفات {dc['name']}: {r['def_loss']}%\n"
        f"📍 {r['territory']}{un}{occ_msg}")
    try: await context.bot.send_message(CHANNEL_ID,txt,parse_mode="Markdown")
    except: pass
    try: await context.bot.send_message(int(tid),f"🚨 *{ac['name']} به شما حمله کرد!*\n\n{r['story']}\n\n🏆 برنده: {winner}",parse_mode="Markdown")
    except: pass
    await update.message.reply_text(txt,parse_mode="Markdown")
    await update.message.reply_text(".",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پنل",callback_data="back")]]))
    return ConversationHandler.END

async def alliance_menu(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    db=load_db(); uid=str(update.effective_user.id)
    if uid not in db["players"]: await q.edit_message_text("❌ /start"); return
    alliances=db.get("alliances",{})
    # پیدا کردن اتحاد فعلی پلیر
    my_alliance=None; my_aid=None
    for aid,al in alliances.items():
        if uid==al.get("leader") or uid in al.get("members",[]):
            my_alliance=al; my_aid=aid; break
    if my_alliance:
        members_txt=""
        for mid in [my_alliance["leader"]]+my_alliance.get("members",[]):
            mp=db["players"].get(mid,{}); mc=get_country(mp.get("country_id",""))
            role="👑 رهبر" if mid==my_alliance["leader"] else "👤 عضو"
            members_txt+=f"{role}: {mc['name'] if mc else '?'}\n"
        kb=[]
        if uid==my_alliance["leader"]:
            kb.append([InlineKeyboardButton("📋 درخواست‌های عضویت",callback_data=f"al_requests_{my_aid}")])
            kb.append([InlineKeyboardButton("🗑️ انحلال اتحاد",callback_data=f"al_dissolve_{my_aid}")])
        else:
            kb.append([InlineKeyboardButton("🚪 خروج از اتحاد",callback_data=f"al_leave_{my_aid}")])
        kb.append([InlineKeyboardButton("🔙",callback_data="back")])
        await q.edit_message_text(
            f"🤝 *اتحاد {my_alliance['name']}*\n"
            f"📣 شعار: {my_alliance.get('slogan','')}\n"
            f"👥 اعضا ({len(my_alliance.get('members',[]))+1}/4):\n{members_txt}",
            parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
    else:
        kb=[
            [InlineKeyboardButton("➕ ساخت اتحاد جدید",callback_data="al_create")],
            [InlineKeyboardButton("🔍 پیوستن به اتحاد",callback_data="al_join_list")],
            [InlineKeyboardButton("🔙",callback_data="back")],
        ]
        txt="🤝 *سیستم اتحاد*\n\nشما عضو هیچ اتحادی نیستید.\n\n"
        if alliances:
            txt+="📋 اتحادهای موجود:\n"
            for aid,al in alliances.items():
                count=len(al.get("members",[]))+1
                txt+=f"• {al['name']} ({count}/4)\n"
        await q.edit_message_text(txt,parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def al_create_start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    db=load_db(); uid=str(update.effective_user.id)
    for al in db.get("alliances",{}).values():
        if uid==al.get("leader") or uid in al.get("members",[]):
            await q.edit_message_text("❌ شما قبلاً عضو یک اتحاد هستید!",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="alliance_menu")]])); return ConversationHandler.END
    await q.edit_message_text(
        "➕ *ساخت اتحاد جدید*\n\n"
        "بنویس:\n"
        "خط ۱: اسم اتحاد\n"
        "خط ۲: شعار اتحاد\n\n"
        "مثال:\n"
        "ناتو\n"
        "صلح و امنیت جهانی",
        parse_mode="Markdown")
    return WAITING_ALLIANCE_INFO

async def al_create_recv(update:Update,context:ContextTypes.DEFAULT_TYPE):
    db=load_db(); uid=str(update.effective_user.id)
    lines=[l.strip() for l in update.message.text.strip().split('\n') if l.strip()]
    if len(lines)<2:
        await update.message.reply_text("❌ باید اسم و شعار رو در دو خط بنویسی!"); return WAITING_ALLIANCE_INFO
    name=lines[0]; slogan=lines[1]
    aid=f"al_{len(db.get('alliances',{}))+1}_{uid[:6]}"
    db.setdefault("alliances",{})[aid]={"name":name,"slogan":slogan,"leader":uid,"members":[],"requests":[]}
    save_db(db)
    c=get_country(db["players"][uid]["country_id"])
    await update.message.reply_text(f"✅ اتحاد *{name}* ساخته شد!\n📣 شعار: {slogan}",parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پنل",callback_data="back")]]))
    try:
        await context.bot.send_message(CHANNEL_ID,
            f"🤝 *اتحاد جدید تاسیس شد!*\n\n"
            f"🏳️ نام: *{name}*\n📣 شعار: {slogan}\n👑 بنیان‌گذار: {c['name'] if c else '?'}",
            parse_mode="Markdown")
    except: pass
    return ConversationHandler.END

async def al_join_list(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    db=load_db(); uid=str(update.effective_user.id)
    alliances=db.get("alliances",{})
    kb=[]
    for aid,al in alliances.items():
        count=len(al.get("members",[]))+1
        if count<4 and uid!=al.get("leader") and uid not in al.get("members",[]):
            kb.append([InlineKeyboardButton(f"📩 {al['name']} ({count}/4)",callback_data=f"al_request_{aid}")])
    kb.append([InlineKeyboardButton("🔙",callback_data="alliance_menu")])
    if len(kb)==1:
        await q.edit_message_text("هیچ اتحادی برای پیوستن وجود ندارد!",reply_markup=InlineKeyboardMarkup(kb)); return
    await q.edit_message_text("🔍 اتحاد مورد نظر رو انتخاب کن:",reply_markup=InlineKeyboardMarkup(kb))

async def al_send_request(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    aid=q.data.replace("al_request_",""); db=load_db(); uid=str(update.effective_user.id)
    al=db.get("alliances",{}).get(aid)
    if not al: return
    if uid in al.get("requests",[]): await q.answer("قبلاً درخواست دادی!",show_alert=True); return
    al.setdefault("requests",[]).append(uid); save_db(db)
    c=get_country(db["players"][uid]["country_id"])
    try:
        kb=[[InlineKeyboardButton("✅ قبول",callback_data=f"al_accept_{aid}_{uid}"),InlineKeyboardButton("❌ رد",callback_data=f"al_reject_{aid}_{uid}")]]
        await context.bot.send_message(int(al["leader"]),
            f"📩 *درخواست عضویت*\n\n{c['name'] if c else '?'} درخواست پیوستن به اتحاد {al['name']} رو داده.",
            parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
    except: pass
    await q.edit_message_text(f"✅ درخواست به اتحاد {al['name']} ارسال شد!",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))

async def al_accept(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    parts=q.data.replace("al_accept_","").split("_",1); aid=parts[0]; req_uid=parts[1]
    db=load_db(); al=db.get("alliances",{}).get(aid)
    if not al: return
    if len(al.get("members",[]))>=3: await q.answer("اتحاد پر است! (حداکثر ۴ نفر)",show_alert=True); return
    al.setdefault("members",[]).append(req_uid)
    if req_uid in al.get("requests",[]): al["requests"].remove(req_uid)
    save_db(db)
    c=get_country(db["players"].get(req_uid,{}).get("country_id",""))
    try: await context.bot.send_message(int(req_uid),f"✅ درخواست شما برای پیوستن به اتحاد *{al['name']}* پذیرفته شد!",parse_mode="Markdown")
    except: pass
    await q.edit_message_text(f"✅ {c['name'] if c else req_uid} به اتحاد اضافه شد!")

async def al_reject(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    parts=q.data.replace("al_reject_","").split("_",1); aid=parts[0]; req_uid=parts[1]
    db=load_db(); al=db.get("alliances",{}).get(aid)
    if not al: return
    if req_uid in al.get("requests",[]): al["requests"].remove(req_uid)
    save_db(db)
    try: await context.bot.send_message(int(req_uid),f"❌ درخواست شما برای پیوستن به اتحاد {al['name']} رد شد.")
    except: pass
    await q.edit_message_text("❌ درخواست رد شد.")

async def al_leave(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    aid=q.data.replace("al_leave_",""); db=load_db(); uid=str(update.effective_user.id)
    al=db.get("alliances",{}).get(aid)
    if not al: return
    if uid in al.get("members",[]): al["members"].remove(uid)
    save_db(db)
    await q.edit_message_text(f"✅ از اتحاد {al['name']} خارج شدی.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))

async def al_dissolve(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    aid=q.data.replace("al_dissolve_",""); db=load_db(); uid=str(update.effective_user.id)
    al=db.get("alliances",{}).get(aid)
    if not al or al.get("leader")!=uid: return
    name=al["name"]
    # اطلاع به اعضا
    for mid in al.get("members",[]):
        try: await context.bot.send_message(int(mid),f"⚠️ اتحاد {name} توسط رهبر منحل شد.")
        except: pass
    del db["alliances"][aid]; save_db(db)
    await q.edit_message_text(f"🗑️ اتحاد {name} منحل شد.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))

async def al_requests_view(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    aid=q.data.replace("al_requests_",""); db=load_db(); uid=str(update.effective_user.id)
    al=db.get("alliances",{}).get(aid)
    if not al or al.get("leader")!=uid: return
    reqs=al.get("requests",[])
    if not reqs:
        await q.edit_message_text("📭 درخواست عضویتی وجود ندارد.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="alliance_menu")]])); return
    kb=[]
    for req_uid in reqs:
        p=db["players"].get(req_uid,{}); c=get_country(p.get("country_id",""))
        kb.append([InlineKeyboardButton(f"✅ {c['name'] if c else '?'}",callback_data=f"al_accept_{aid}_{req_uid}"),
                   InlineKeyboardButton("❌ رد",callback_data=f"al_reject_{aid}_{req_uid}")])
    kb.append([InlineKeyboardButton("🔙",callback_data="alliance_menu")])
    await q.edit_message_text("📋 درخواست‌های عضویت:",reply_markup=InlineKeyboardMarkup(kb))
    q=update.callback_query; await q.answer()
    if not GAME_SETTINGS.get("trade",True) and update.effective_user.id!=ADMIN_ID:
        await q.edit_message_text("🔒 معامله بسته!",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]])); return
    db=load_db(); uid=str(update.effective_user.id); p=db["players"].get(uid)
    if not p: return
    eq=p.get("equipment",[]); has_truck=any(e["id"]=="truck" for e in eq); has_ship=any(e["id"]=="cargo_ship" for e in eq)
    if not has_truck and not has_ship:
        await q.edit_message_text("❌ *معامله ممکن نیست!*\n\nنیاز دارید:\n🚛 کامیون باربری (زمینی)\n🚢 کشتی باربری (دریایی)",
            parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛒 فروشگاه",callback_data="shop"),InlineKeyboardButton("🔙",callback_data="back")]])); return
    others={k:v for k,v in db["players"].items() if k!=uid and not v.get("banned")}
    if not others:
        await q.edit_message_text("🤝 بازیکن دیگه‌ای نیست!",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]])); return
    kb=[]
    for k,v in others.items():
        c=get_country(v["country_id"])
        if c: kb.append([InlineKeyboardButton(f"🤝 {c['name']}",callback_data=f"trade_{k}")])
    kb.append([InlineKeyboardButton("🔙",callback_data="back")])
    await q.edit_message_text("🤝 *معامله*\nکشور طرف معامله:",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def trade_select(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    tid=q.data.replace("trade_",""); context.user_data["trade_target"]=tid
    db=load_db(); uid=str(update.effective_user.id)
    src_p=db["players"].get(uid); dst_p=db["players"].get(tid)
    if not src_p or not dst_p: return
    sc=get_country(src_p["country_id"]); dc=get_country(dst_p["country_id"])
    eq=src_p.get("equipment",[]); has_truck=any(e["id"]=="truck" for e in eq); has_ship=any(e["id"]=="cargo_ship" for e in eq)
    land_ok=has_truck and has_land_border(sc["id"],dc["id"])
    sea_ok=has_ship and has_sea(sc["id"]) and has_sea(dc["id"])
    if not land_ok and not sea_ok:
        await q.edit_message_text(f"❌ معامله با {dc['name']} ممکن نیست!\nمرز زمینی مشترک ندارید یا کشتی/کامیون لازم ندارید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="trade_menu")]])); return
    kb=[]
    if land_ok: kb.append([InlineKeyboardButton("🚛 معامله زمینی",callback_data="tmethod_land")])
    if sea_ok: kb.append([InlineKeyboardButton("🚢 معامله دریایی",callback_data="tmethod_sea")])
    kb.append([InlineKeyboardButton("🔙",callback_data="trade_menu")])
    await q.edit_message_text(f"🤝 معامله با {dc['name']}\nروش ارسال:",reply_markup=InlineKeyboardMarkup(kb))

async def trade_method(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    method=q.data.replace("tmethod_",""); context.user_data["trade_method"]=method
    await q.edit_message_text(
        f"🤝 *جزئیات معامله*\nروش: {'🚛 زمینی' if method=='land' else '🚢 دریایی'}\n\n"
        f"✍️ بنویس چی میدی و چی میخوای:\nمثال: ۵۰,۰۰۰$ در ازای معدن طلا\n\n"
        f"💡 برای معامله مخفی: ابتدا بنویس SECRET",
        parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="trade_menu")]]))
    return WAITING_TRADE_DETAIL

async def trade_recv(update:Update,context:ContextTypes.DEFAULT_TYPE):
    db=load_db(); uid=str(update.effective_user.id); tid=context.user_data.get("trade_target"); method=context.user_data.get("trade_method","land")
    src_p=db["players"].get(uid); dst_p=db["players"].get(tid)
    if not src_p or not dst_p: return ConversationHandler.END
    sc=get_country(src_p["country_id"]); dc=get_country(dst_p["country_id"]); detail=update.message.text
    is_secret=detail.upper().startswith("SECRET"); detail=detail.replace("SECRET","").replace("secret","").strip()
    route=await ai_trade_route(sc["name"],dc["name"],"کشتی" if method=="sea" else "کامیون",detail[:50])
    trade_id=len(db.get("trades",[]))+1
    trade={"id":trade_id,"from_uid":uid,"to_uid":tid,"from_country":sc["name"],"to_country":dc["name"],
           "detail":detail,"method":method,"route":route,"secret":is_secret,"status":"pending","date":datetime.now().isoformat()}
    db.setdefault("trades",[]).append(trade); save_db(db)
    try:
        kb=[[InlineKeyboardButton("✅ تایید",callback_data=f"taccept_{trade_id}"),InlineKeyboardButton("❌ رد",callback_data=f"treject_{trade_id}")]]
        await context.bot.send_message(int(tid),
            f"🤝 *درخواست معامله*\n\nاز: {sc['name']}\nروش: {'🚛 زمینی' if method=='land' else '🚢 دریایی'}\n📋 {detail}\n🗺️ {route}",
            parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
        await update.message.reply_text(f"✅ درخواست به {dc['name']} ارسال شد!")
    except: await update.message.reply_text("❌ خطا در ارسال.")
    await update.message.reply_text(".",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پنل",callback_data="back")]]))
    return ConversationHandler.END

async def parse_trade_assets(detail):
    """از متن معامله پول و نفت استخراج میکنه"""
    import re
    # جستجوی پول
    budget=0; oil=0
    money_patterns=[r'(\d[\d,]*)\s*\$',r'\$\s*(\d[\d,]*)',r'(\d[\d,]*)\s*دلار']
    for pat in money_patterns:
        m=re.search(pat,detail.replace('،',','))
        if m:
            try: budget=int(m.group(1).replace(',','').replace('،','')); break
            except: pass
    # جستجوی نفت
    oil_patterns=[r'(\d[\d,]*)\s*بشکه',r'(\d[\d,]*)\s*نفت']
    for pat in oil_patterns:
        m=re.search(pat,detail)
        if m:
            try: oil=int(m.group(1).replace(',','').replace('،','')); break
            except: pass
    return budget, oil

async def trade_accept(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    trade_id=int(q.data.replace("taccept_","")); db=load_db(); uid=str(update.effective_user.id)
    trade=next((t for t in db.get("trades",[]) if t["id"]==trade_id),None)
    if not trade or trade["status"]!="pending": await q.answer("دیگه معتبر نیست!",show_alert=True); return
    if trade["to_uid"]!=uid: await q.answer("برای شما نیست!",show_alert=True); return

    from_uid=trade["from_uid"]; to_uid=trade["to_uid"]
    detail=trade.get("detail","")
    from_p=db["players"].get(from_uid,{}); to_p=db["players"].get(to_uid,{})

    # استخراج پول و نفت از متن معامله
    budget_give, oil_give = await parse_trade_assets(detail)

    transfer_msg=""
    errors=""

    # پول از فرستنده (from) به گیرنده (to) منتقل میشه
    if budget_give>0:
        if from_p.get("budget",0)>=budget_give:
            db["players"][from_uid]["budget"]=from_p.get("budget",0)-budget_give
            db["players"][to_uid]["budget"]=to_p.get("budget",0)+budget_give
            transfer_msg+=f"\n💰 ${budget_give:,} از {trade['from_country']} به {trade['to_country']} منتقل شد"
        else:
            errors+=f"\n⚠️ {trade['from_country']} بودجه کافی ندارد!"

    # نفت از گیرنده (to) به فرستنده (from) منتقل میشه
    if oil_give>0:
        if to_p.get("oil",0)>=oil_give:
            db["players"][to_uid]["oil"]=to_p.get("oil",0)-oil_give
            db["players"][from_uid]["oil"]=from_p.get("oil",0)+oil_give
            transfer_msg+=f"\n🛢️ {oil_give:,} بشکه نفت از {trade['to_country']} به {trade['from_country']} منتقل شد"
        else:
            errors+=f"\n⚠️ {trade['to_country']} نفت کافی ندارد!"

    trade["status"]="accepted"; save_db(db)

    try:
        await context.bot.send_message(int(from_uid),
            f"✅ *معامله تایید شد!*\n{trade['to_country']} پذیرفت.\n📋 {detail}{transfer_msg}{errors}",
            parse_mode="Markdown")
    except: pass

    if not trade.get("secret"):
        try:
            await context.bot.send_message(CHANNEL_ID,
                f"🤝 *معامله رسمی تایید شد*\n━━━━━━━━━━━━━━━\n"
                f"🔵 {trade['from_country']} ↔️ 🟢 {trade['to_country']}\n"
                f"{'🚛' if trade['method']=='land' else '🚢'} {detail}\n"
                f"🗺️ {trade['route']}{transfer_msg}",
                parse_mode="Markdown")
        except: pass

    await q.edit_message_text(f"✅ معامله تایید شد!{transfer_msg}{errors}")

async def trade_reject(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    trade_id=int(q.data.replace("treject_","")); db=load_db(); uid=str(update.effective_user.id)
    trade=next((t for t in db.get("trades",[]) if t["id"]==trade_id),None)
    if not trade: return
    trade["status"]="rejected"; save_db(db)
    try: await context.bot.send_message(int(trade["from_uid"]),f"❌ {trade['to_country']} معامله رد کرد.")
    except: pass
    await q.edit_message_text("❌ معامله رد شد.")

async def ref_menu(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); uid=str(update.effective_user.id); db=load_db()
    botu=(await context.bot.get_me()).username; link=f"https://t.me/{botu}?start={uid}"
    cnt=sum(1 for v in db.get("referrals",{}).values() if v==uid)
    await q.edit_message_text(f"🔗 *دعوت دوستان*\n\n`{link}`\n\n👥 {cnt} نفر دعوت کردی\n💰 پاداش: +15,000$",
        parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))

async def tutorial(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    txt=(f"📖 *آموزش World War 26*\n━━━━━━━━━━━━━━━\n\n"
        f"🌍 *۱. انتخاب کشور*\nاز لیست کشورها انتخاب کن.\n\n"
        f"🛒 *۲. خرید تجهیزات*\nتجهیزات هوایی، دریایی، موشکی، زمینی و اقتصادی بخر.\n\n"
        f"📜 *۳. بیانیه*\nعکس + متن رسمی زیرش بفرست. AI چک و کانال منتشر میکنه.\n\n"
        f"⚔️ *۴. جنگ*\nفقط از تجهیزاتی که داری استفاده کن! AI چک میکنه.\n🏴 اشغال فقط با نیروی زمینی!\n\n"
        f"🤝 *۵. معامله*\nبا 🚛کامیون (زمینی) یا 🚢کشتی (دریایی) معامله کن.\n\n"
        f"🚧 *۶. مرزها*\nمرز هوایی، زمینی و دریایی رو باز/بسته کن.\n\n"
        f"💰 *۷. درآمد*\nهر شب ۱۲ درآمدها واریز میشه.\n\n"
        f"⚠️ *قوانین مهم*\n• ۳ روز بیانیه ندی = اخراج\n• فحش = رد بیانیه\n• سناریو باید با تجهیزات واقعی باشه\n\n"
        f"📢 کانال: {CHANNEL_LINK}")
    await q.edit_message_text(txt,parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))

async def quit_ask(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.edit_message_text("🚪 *خروج از بازی*\n\nمطمئنی؟ همه پیشرفتت حذف میشه! ⚠️",parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ بله خارج میشم",callback_data="quit_yes"),InlineKeyboardButton("❌ نه",callback_data="back")]]))

async def quit_yes(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); db=load_db(); uid=str(update.effective_user.id)
    if uid in db["players"]:
        c=get_country(db["players"][uid]["country_id"]); del db["players"][uid]; save_db(db)
        await q.edit_message_text(f"🚪 از بازی خارج شدی. {c['name'] if c else ''} آزاد شد. /start")
    else: await q.edit_message_text("تو بازی نیستی!")

async def adm_panel(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID:
        if update.callback_query: await update.callback_query.answer("❌",show_alert=True)
        return
    q=update.callback_query
    if q: await q.answer()
    db=load_db()
    kb=[[InlineKeyboardButton("👥 بازیکنان",callback_data="adm_p"),InlineKeyboardButton("📊 آمار",callback_data="adm_s")],
        [InlineKeyboardButton("⚔️ جنگ‌ها",callback_data="adm_w"),InlineKeyboardButton("📜 بیانیه‌ها",callback_data="adm_d")],
        [InlineKeyboardButton("🔙",callback_data="back")]]
    txt=f"👑 *پنل ادمین*\n👥 {len(db['players'])} | ⚔️ {len(db['wars'])} | 📜 {len(db['declarations'])}"
    if q:
        try: await q.edit_message_text(txt,parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
        except: await q.message.reply_text(txt,parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
    else: await update.message.reply_text(txt,parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

async def adm_p(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    q=update.callback_query; await q.answer(); db=load_db()
    txt="👥 *بازیکنان*\n━━━━━━━━━━\n"
    for uid,p in db["players"].items():
        c=get_country(p["country_id"]); b="🚫" if p.get("banned") else "✅"
        txt+=f"{b} @{p.get('username','?')} | {c['name'] if c else '?'}\nID:{uid} | ${p['budget']:,}\n"
    await q.edit_message_text(txt[:4000] or "کسی نیست",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="admin")]]))

async def adm_s(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    q=update.callback_query; await q.answer(); db=load_db()
    await q.edit_message_text(
        f"📊 *آمار*\n👥 فعال:{len([p for p in db['players'].values() if not p.get('banned')])}\n"
        f"🚫 بن:{len([p for p in db['players'].values() if p.get('banned')])}\n"
        f"⚔️ جنگ:{len(db['wars'])}\n📜 بیانیه:{len(db['declarations'])}\n🏴 اشغال:{len(db.get('occupied',{}))}\n"
        f"💰 کل:${sum(p.get('budget',0) for p in db['players'].values()):,}",
        parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="admin")]]))

async def adm_w(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    q=update.callback_query; await q.answer(); db=load_db()
    txt="⚔️ *جنگ‌ها*\n"
    for w in db["wars"][-10:]: txt+=f"• {w['atk']} ⚔️ {w['def']} → {w['winner']}\n"
    await q.edit_message_text(txt or "جنگی نبود",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="admin")]]))

async def adm_d(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    q=update.callback_query; await q.answer(); db=load_db()
    txt="📜 *بیانیه‌ها*\n"
    for d in db["declarations"][-10:]: txt+=f"• {d['country']}: {d['text'][:50]}...\n"
    await q.edit_message_text(txt or "بیانیه‌ای نبود",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="admin")]]))

async def cmd_addoil(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """اضافه کردن نفت به پلیر"""
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<2: await update.message.reply_text("/addoil <id> <مقدار>"); return
    db=load_db(); uid=context.args[0]
    try: amt=int(context.args[1])
    except: await update.message.reply_text("عدد وارد کن!"); return
    if uid in db["players"]:
        db["players"][uid]["oil"]=db["players"][uid].get("oil",0)+amt; save_db(db)
        await update.message.reply_text(f"✅ +{amt:,} بشکه نفت به {uid}")
        try: await context.bot.send_message(int(uid),f"🛢️ {amt:,} بشکه نفت به کشور شما اضافه شد!")
        except: pass
    else: await update.message.reply_text("❌ پیدا نشد.")

async def cmd_givemoney(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """پول دادن به همه بازیکنان"""
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("/givemoney <مقدار> - پول به همه"); return
    try: amt=int(context.args[0])
    except: await update.message.reply_text("عدد وارد کن!"); return
    db=load_db(); count=0
    for uid,p in db["players"].items():
        if not p.get("banned"):
            p["budget"]=p.get("budget",0)+amt; count+=1
    save_db(db)
    await update.message.reply_text(f"✅ ${amt:,} به {count} بازیکن داده شد!")
    try: await context.bot.send_message(CHANNEL_ID,f"🎁 *جایزه ادمین!*\n\nهر بازیکن ${amt:,} دریافت کرد!",parse_mode="Markdown")
    except: pass

async def cmd_clearwars(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """پاک کردن تاریخچه جنگ‌ها"""
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args or context.args[0]!="confirm":
        await update.message.reply_text("⚠️ /clearwars confirm"); return
    db=load_db(); count=len(db["wars"]); db["wars"]=[]; save_db(db)
    await update.message.reply_text(f"🗑️ {count} جنگ پاک شد.")

async def cmd_cleardecls(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """پاک کردن بیانیه‌ها"""
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args or context.args[0]!="confirm":
        await update.message.reply_text("⚠️ /cleardecls confirm"); return
    db=load_db(); count=len(db["declarations"]); db["declarations"]=[]; save_db(db)
    await update.message.reply_text(f"🗑️ {count} بیانیه پاک شد.")

async def cmd_freeall(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """آزاد کردن همه کشورهای اشغالی"""
    if update.effective_user.id!=ADMIN_ID: return
    db=load_db(); count=len(db.get("occupied",{})); db["occupied"]={}; save_db(db)
    await update.message.reply_text(f"✅ {count} کشور اشغالی آزاد شد.")
    try: await context.bot.send_message(CHANNEL_ID,"🕊️ *اعلام ادمین*\n\nتمام کشورهای اشغالی آزاد شدند!",parse_mode="Markdown")
    except: pass

async def cmd_freecountry(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """آزاد کردن یک کشور اشغالی"""
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("/freecountry <country_id>\nمثال: /freecountry ir"); return
    db=load_db(); cid=context.args[0]
    if cid in db.get("occupied",{}):
        del db["occupied"][cid]; save_db(db)
        c=get_country(cid)
        await update.message.reply_text(f"✅ {c['name'] if c else cid} آزاد شد.")
    else: await update.message.reply_text("❌ این کشور اشغال نشده.")

async def cmd_setcountry(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """تغییر کشور پلیر"""
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<2: await update.message.reply_text("/setcountry <user_id> <country_id>\nمثال: /setcountry 123456 ir"); return
    db=load_db(); uid=context.args[0]; cid=context.args[1]
    if uid not in db["players"]: await update.message.reply_text("❌ پلیر پیدا نشد."); return
    c=get_country(cid)
    if not c: await update.message.reply_text("❌ کشور پیدا نشد."); return
    if cid in {p["country_id"] for k,p in db["players"].items() if k!=uid}:
        await update.message.reply_text("❌ این کشور توسط پلیر دیگه‌ای گرفته شده!"); return
    db["players"][uid]["country_id"]=cid; save_db(db)
    await update.message.reply_text(f"✅ کشور {uid} به {c['name']} تغییر کرد.")
    try: await context.bot.send_message(int(uid),f"🌍 کشور شما توسط ادمین به {c['name']} تغییر کرد.")
    except: pass

async def cmd_warn(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """اخطار به پلیر"""
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<2: await update.message.reply_text("/warn <id> <دلیل>"); return
    db=load_db(); uid=context.args[0]; reason=" ".join(context.args[1:])
    if uid not in db["players"]: await update.message.reply_text("❌ پیدا نشد."); return
    try:
        await context.bot.send_message(int(uid),f"⚠️ *اخطار رسمی از ادمین*\n\n{reason}\n\nتکرار = بن دائمی!",parse_mode="Markdown")
        await update.message.reply_text(f"✅ اخطار به {uid} ارسال شد.")
    except: await update.message.reply_text("❌ خطا در ارسال.")

async def cmd_msg(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """ارسال پیام خصوصی به یک پلیر"""
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<2: await update.message.reply_text("/msg <id> <پیام>"); return
    uid=context.args[0]; msg=" ".join(context.args[1:])
    try:
        await context.bot.send_message(int(uid),f"📩 *پیام از ادمین:*\n\n{msg}",parse_mode="Markdown")
        await update.message.reply_text(f"✅ پیام به {uid} ارسال شد.")
    except: await update.message.reply_text("❌ خطا در ارسال.")

async def cmd_channel(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """ارسال پیام به کانال"""
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("/channel <پیام>"); return
    msg=" ".join(context.args)
    try:
        await context.bot.send_message(CHANNEL_ID,f"📢 *اطلاعیه رسمی*\n\n{msg}",parse_mode="Markdown")
        await update.message.reply_text("✅ در کانال منتشر شد.")
    except Exception as e: await update.message.reply_text(f"❌ خطا: {e}")

async def cmd_listcountries(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """لیست کشورها با ID"""
    if update.effective_user.id!=ADMIN_ID: return
    db=load_db(); taken={p["country_id"] for p in db["players"].values()}
    occ=set(db.get("occupied",{}).keys())
    txt="🌍 *لیست کشورها:*\n\n"
    for c in COUNTRIES:
        status="🔒" if c["id"] in taken else ("🟠" if c["id"] in occ else "✅")
        txt+=f"{status} `{c['id']}` - {c['name']}\n"
    for ch in [txt[i:i+4000] for i in range(0,len(txt),4000)]:
        await update.message.reply_text(ch,parse_mode="Markdown")

async def cmd_fullreset(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """ریست کامل بازی"""
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args or context.args[0]!="CONFIRM":
        await update.message.reply_text("⚠️ این کار کل بازی رو ریست میکنه!\n/fullreset CONFIRM"); return
    db={"players":{},"declarations":[],"wars":[],"trades":[],"referrals":{},"last_income":"","last_news":"","occupied":{}}
    save_db(db)
    await update.message.reply_text("🔄 کل بازی ریست شد!")
    try: await context.bot.send_message(CHANNEL_ID,"🔄 *بازی ریست شد!*\n\nهمه می‌تونن دوباره /start بزنن.",parse_mode="Markdown")
    except: pass

async def cmd_removeequip_all(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """حذف همه تجهیزات یک پلیر"""
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("/clearequip <id>"); return
    db=load_db(); uid=context.args[0]
    if uid not in db["players"]: await update.message.reply_text("❌ پیدا نشد."); return
    count=len(db["players"][uid].get("equipment",[])); db["players"][uid]["equipment"]=[]; save_db(db)
    await update.message.reply_text(f"✅ {count} تجهیز از {uid} حذف شد.")
    try: await context.bot.send_message(int(uid),"⚠️ همه تجهیزات شما توسط ادمین حذف شد.")
    except: pass

async def cmd_occupiedlist(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """لیست کشورهای اشغالی"""
    if update.effective_user.id!=ADMIN_ID: return
    db=load_db(); occ=db.get("occupied",{})
    if not occ: await update.message.reply_text("هیچ کشوری اشغال نشده."); return
    txt="🏴 *کشورهای اشغالی:*\n\n"
    for cid,uid in occ.items():
        c=get_country(cid); p=db["players"].get(uid,{})
        txt+=f"• {c['name'] if c else cid} ← @{p.get('username','?')}\n"
    await update.message.reply_text(txt,parse_mode="Markdown")

async def cmd_trades(update:Update,context:ContextTypes.DEFAULT_TYPE):
    """لیست معاملات"""
    if update.effective_user.id!=ADMIN_ID: return
    db=load_db(); trades=db.get("trades",[])[-10:]
    if not trades: await update.message.reply_text("هیچ معامله‌ای نبوده."); return
    txt="🤝 *آخرین معاملات:*\n\n"
    for t in trades:
        txt+=f"• {t['from_country']} → {t['to_country']}\n  {t['detail'][:40]}... | {t['status']}\n"
    await update.message.reply_text(txt,parse_mode="Markdown")

async def cmd_ban(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("/ban <id>"); return
    db=load_db(); uid=context.args[0]
    if uid in db["players"]:
        db["players"][uid]["banned"]=True; save_db(db)
        await update.message.reply_text(f"🚫 {uid} بن شد.")
        try: await context.bot.send_message(int(uid),"🚫 از بازی بن شدید.")
        except: pass
    else: await update.message.reply_text("❌ پیدا نشد.")

async def cmd_unban(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("/unban <id>"); return
    db=load_db(); uid=context.args[0]
    if uid in db["players"]:
        db["players"][uid]["banned"]=False; save_db(db); await update.message.reply_text(f"✅ {uid} آنبن شد.")
        try: await context.bot.send_message(int(uid),"✅ بن برداشته شد!")
        except: pass
    else: await update.message.reply_text("❌ پیدا نشد.")

async def cmd_kick(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("/kick <id>"); return
    db=load_db(); uid=context.args[0]
    if uid in db["players"]:
        del db["players"][uid]; save_db(db); await update.message.reply_text(f"🗑️ {uid} اخراج شد.")
        try: await context.bot.send_message(int(uid),"🗑️ اخراج شدید.")
        except: pass
    else: await update.message.reply_text("❌ پیدا نشد.")

async def cmd_setbudget(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<2: await update.message.reply_text("/setbudget <id> <مقدار>"); return
    db=load_db(); uid=context.args[0]
    try: amt=int(context.args[1])
    except: await update.message.reply_text("عدد وارد کن!"); return
    if uid in db["players"]:
        db["players"][uid]["budget"]=amt; save_db(db); await update.message.reply_text(f"✅ ${amt:,}")
    else: await update.message.reply_text("❌ پیدا نشد.")

async def cmd_addbudget(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<2: await update.message.reply_text("/addbudget <id> <مقدار>"); return
    db=load_db(); uid=context.args[0]
    try: amt=int(context.args[1])
    except: await update.message.reply_text("عدد وارد کن!"); return
    if uid in db["players"]:
        db["players"][uid]["budget"]=db["players"][uid].get("budget",0)+amt; save_db(db)
        await update.message.reply_text(f"✅ +${amt:,}")
    else: await update.message.reply_text("❌ پیدا نشد.")

async def cmd_setoil(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<2: await update.message.reply_text("/setoil <id> <مقدار>"); return
    db=load_db(); uid=context.args[0]
    try: amt=int(context.args[1])
    except: await update.message.reply_text("عدد وارد کن!"); return
    if uid in db["players"]:
        db["players"][uid]["oil"]=amt; save_db(db); await update.message.reply_text(f"✅ {amt:,} بشکه")
    else: await update.message.reply_text("❌ پیدا نشد.")

async def cmd_addequip(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<2: await update.message.reply_text("/addequip <id> <item_id>\n/equiplist"); return
    db=load_db(); uid=context.args[0]; iid=context.args[1]
    if uid not in db["players"]: await update.message.reply_text("❌ پیدا نشد."); return
    item=next((it for cat in EQUIP.values() for it in cat if it["id"]==iid),None)
    if not item: await update.message.reply_text(f"❌ '{iid}' پیدا نشد. /equiplist"); return
    db["players"][uid].setdefault("equipment",[]).append(item); save_db(db)
    await update.message.reply_text(f"✅ {item['name']} اضافه شد.")
    try: await context.bot.send_message(int(uid),f"🎁 {item['name']} به کشور شما اضافه شد!")
    except: pass

async def cmd_removeequip(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<2: await update.message.reply_text("/removeequip <id> <item_id>"); return
    db=load_db(); uid=context.args[0]; iid=context.args[1]
    if uid not in db["players"]: await update.message.reply_text("❌ پیدا نشد."); return
    eq=db["players"][uid].get("equipment",[]); new_eq=[e for e in eq if e.get("id")!=iid]
    if len(new_eq)==len(eq): await update.message.reply_text("❌ تجهیز پیدا نشد."); return
    db["players"][uid]["equipment"]=new_eq; save_db(db); await update.message.reply_text(f"✅ حذف شد.")

async def cmd_equiplist(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    txt="📋 *ID تجهیزات:*\n\n"
    for cat,items in EQUIP.items():
        txt+=f"{cat}\n"
        for it in items: txt+=f"  `{it['id']}` ← {it['name']}\n"
        txt+="\n"
    for ch in [txt[i:i+4000] for i in range(0,len(txt),4000)]: await update.message.reply_text(ch,parse_mode="Markdown")

async def cmd_playerinfo(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("/playerinfo <id>"); return
    db=load_db(); uid=context.args[0]; p=db["players"].get(uid)
    if not p: await update.message.reply_text("❌ پیدا نشد."); return
    c=get_country(p["country_id"]); eq=p.get("equipment",[])
    txt=(f"👤 *{p.get('username','?')}*\n🌍 {c['name'] if c else '?'}\n💰 ${p['budget']:,}\n🛢️ {p.get('oil',0):,}\n"
        f"🚫 بن: {'بله' if p.get('banned') else 'خیر'}\n\n🔧 تجهیزات ({len(eq)}):\n")
    for e in eq: txt+=f"  • {e['name']}\n"
    for ch in [txt[i:i+4000] for i in range(0,len(txt),4000)]: await update.message.reply_text(ch,parse_mode="Markdown")

async def cmd_toggle(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args:
        status="\n".join(f"{'✅' if v else '🔒'} {k}" for k,v in GAME_SETTINGS.items())
        await update.message.reply_text(f"⚙️ *وضعیت:*\n{status}\n\n/toggle shop|decl|war|trade",parse_mode="Markdown"); return
    key=context.args[0].lower()
    if key not in GAME_SETTINGS: await update.message.reply_text("❌ گزینه نامعتبر! (shop/decl/war/trade)"); return
    GAME_SETTINGS[key]=not GAME_SETTINGS[key]
    status="✅ باز" if GAME_SETTINGS[key] else "🔒 بسته"
    labels={"shop":"فروشگاه","decl":"بیانیه","war":"جنگ","trade":"معامله"}
    try: await context.bot.send_message(CHANNEL_ID,f"⚙️ *اطلاعیه ادمین*\n\n{labels.get(key,key)} {status} شد.",parse_mode="Markdown")
    except: pass
    await update.message.reply_text(f"{status}: {key}")

async def cmd_resetplayer(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("/resetplayer <id>"); return
    db=load_db(); uid=context.args[0]
    if uid not in db["players"]: await update.message.reply_text("❌ پیدا نشد."); return
    c=get_country(db["players"][uid]["country_id"])
    db["players"][uid]["budget"]=START_BUDGET; db["players"][uid]["oil"]=c["oil_b"] if c else 0
    db["players"][uid]["equipment"]=[]; save_db(db)
    await update.message.reply_text(f"🔄 {uid} ریست شد.")
    try: await context.bot.send_message(int(uid),"🔄 دارایی‌های شما ریست شد.")
    except: pass

async def cmd_resetall(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args or context.args[0]!="confirm":
        await update.message.reply_text("⚠️ /resetall confirm"); return
    db=load_db(); count=0
    for uid,p in db["players"].items():
        c=get_country(p["country_id"]); p["budget"]=START_BUDGET; p["oil"]=c["oil_b"] if c else 0; p["equipment"]=[]; count+=1
    save_db(db); await update.message.reply_text(f"🔄 {count} پلیر ریست شدند!")

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
        "👑 کامندهای ادمین - راهنمای کامل\n\n"
        "━━ 🚫 مدیریت کاربران ━━\n"
        "/ban id - بن کاربر\n"
        "/unban id - آنبن کاربر\n"
        "/kick id - اخراج از بازی\n"
        "/warn id دلیل - اخطار به پلیر\n"
        "/msg id پیام - پیام خصوصی به پلیر\n"
        "/players - لیست همه بازیکنان\n"
        "/playerinfo id - اطلاعات کامل پلیر\n\n"
        "━━ 💰 مدیریت دارایی ━━\n"
        "/setbudget id مقدار - تنظیم بودجه\n"
        "/addbudget id مقدار - اضافه کردن بودجه\n"
        "/setoil id مقدار - تنظیم نفت\n"
        "/addoil id مقدار - اضافه کردن نفت\n"
        "/givemoney مقدار - پول به همه\n"
        "/addequip id item_id - اضافه کردن تجهیز\n"
        "/removeequip id item_id - حذف یک تجهیز\n"
        "/clearequip id - حذف همه تجهیزات\n"
        "/equiplist - لیست ID تجهیزات\n\n"
        "━━ 🌍 مدیریت کشورها ━━\n"
        "/listcountries - لیست کشورها با ID\n"
        "/setcountry id country_id - تغییر کشور\n"
        "/occupiedlist - لیست کشورهای اشغالی\n"
        "/freecountry country_id - آزاد کردن کشور\n"
        "/freeall - آزاد کردن همه\n\n"
        "━━ 🔄 ریست ━━\n"
        "/resetplayer id - ریست یه پلیر\n"
        "/resetall confirm - ریست همه پلیرا\n"
        "/fullreset CONFIRM - ریست کامل بازی\n\n"
        "━━ ⚙️ کنترل بازی ━━\n"
        "/toggle - وضعیت بخش‌ها\n"
        "/toggle shop|decl|war|trade\n\n"
        "━━ 📜 آمار ━━\n"
        "/adminstats - آمار کلی\n"
        "/trades - آخرین معاملات\n"
        "/clearwars confirm - پاک کردن جنگ‌ها\n"
        "/cleardecls confirm - پاک کردن بیانیه‌ها\n\n"
        "━━ 📢 ارتباط ━━\n"
        "/broadcast پیام - پیام به همه\n"
        "/channel پیام - پست در کانال\n"
        "/adminhelp - این راهنما"
    )

async def cmd_players(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    db=load_db(); txt="👥 بازیکنان:\n"
    for uid,p in db["players"].items():
        c=get_country(p["country_id"]); b="🚫" if p.get("banned") else "✅"
        txt+=f"{b} {uid} @{p.get('username','?')} {c['name'] if c else '?'} ${p['budget']:,}\n"
    await update.message.reply_text(txt[:4000] or "کسی نیست")

async def cmd_stats(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    db=load_db()
    await update.message.reply_text(f"📊 بازیکنان:{len(db['players'])} | جنگ:{len(db['wars'])} | بیانیه:{len(db['declarations'])}")

async def job_income(context:ContextTypes.DEFAULT_TYPE):
    db=load_db(); today=datetime.now().strftime("%Y-%m-%d")
    if db.get("last_income")==today: return
    db["last_income"]=today; kicked=[]
    for uid,p in list(db["players"].items()):
        if p.get("banned"): continue
        try:
            last=datetime.fromisoformat(p.get("last_decl",p.get("joined_at",datetime.now().isoformat())))
            if (datetime.now()-last).days>=3: kicked.append(uid); continue
        except: pass
        eq=p.get("equipment",[]); daily=sum(e.get("daily",0) for e in eq); odaily=sum(e.get("oil_daily",0) for e in eq)
        p["budget"]=p.get("budget",0)+daily; p["oil"]=p.get("oil",0)+odaily
        if daily>0 or odaily>0:
            try: await context.bot.send_message(int(uid),f"💰 *درآمد واریز شد!*\n+${daily:,}\n{f'+{odaily:,} بشکه' if odaily else ''}\nبودجه: ${p['budget']:,}",parse_mode="Markdown")
            except: pass
    for uid in kicked:
        try: await context.bot.send_message(int(uid),"⏰ ۳ روز بیانیه ندادی - اخراج شدی!")
        except: pass
        if uid in db["players"]: del db["players"][uid]
    save_db(db)
    wars_t=len([w for w in db["wars"] if w.get("date","").startswith(today)])
    decls_t=len([d for d in db["declarations"] if d.get("date","").startswith(today)])
    try:
        await context.bot.send_message(CHANNEL_ID,
            f"🌙 *گزارش شبانه WW26*\n━━━━━━━━━━━━━━━\n💰 درآمدها واریز شد\n"
            f"👥 بازیکنان: {len(db['players'])}\n⚔️ جنگ‌های امروز: {wars_t}\n📜 بیانیه‌های امروز: {decls_t}\n🗑️ اخراج: {len(kicked)}",
            parse_mode="Markdown")
    except: pass

async def job_news(context:ContextTypes.DEFAULT_TYPE):
    db=load_db(); today=datetime.now().strftime("%Y-%m-%d")
    if db.get("last_news")==today: return
    db["last_news"]=today; save_db(db)
    news=await ai_news(db)
    try: await context.bot.send_message(CHANNEL_ID,news,parse_mode="Markdown")
    except: pass

async def noop(update:Update,context:ContextTypes.DEFAULT_TYPE): await update.callback_query.answer()
async def taken(update:Update,context:ContextTypes.DEFAULT_TYPE): await update.callback_query.answer("🔒 گرفته یا تصرف‌شده!",show_alert=True)

async def back(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    db=load_db(); uid=str(update.effective_user.id); p=db["players"].get(uid)
    if not p and update.effective_user.id==ADMIN_ID:
        kb=[[InlineKeyboardButton("👑 پنل ادمین",callback_data="admin")],[InlineKeyboardButton("🌍 انتخاب کشور",callback_data="choose")]]
        try: await q.edit_message_text("👑 *پنل ادمین*",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
        except: await q.message.reply_text("👑 *پنل ادمین*",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
        return
    if p:
        c=get_country(p["country_id"])
        occ=db.get("occupied",{}); my_occ=[k for k,v in occ.items() if v==uid]
        kb=[
            [InlineKeyboardButton("📊 وضعیت کشور",callback_data="status"),InlineKeyboardButton("🛒 خرید تجهیزات",callback_data="shop")],
            [InlineKeyboardButton("📜 بیانیه رسمی",callback_data="decl"),InlineKeyboardButton("⚔️ اعلام جنگ",callback_data="war")],
            [InlineKeyboardButton("🤝 معامله",callback_data="trade_menu"),InlineKeyboardButton("🏛️ اتحاد",callback_data="alliance_menu")],
            [InlineKeyboardButton("🔗 دعوت دوستان",callback_data="ref"),InlineKeyboardButton("📖 آموزش",callback_data="tutorial")],
            [InlineKeyboardButton("🚪 خروج از بازی",callback_data="quit")],
        ]
        if update.effective_user.id==ADMIN_ID: kb.append([InlineKeyboardButton("👑 پنل ادمین",callback_data="admin")])
        occ_txt=f"\n🏴 {len(my_occ)} کشور تصرفی" if my_occ else ""
        try:
            await q.edit_message_text(
                f"🌍 *{update.effective_user.first_name}*\n🏳️ {c['name'] if c else '?'}\n💰 ${p.get('budget',0):,}\n🛢️ {p.get('oil',0):,}{occ_txt}",
                parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
        except:
            await q.message.reply_text(
                f"🌍 *{update.effective_user.first_name}*\n🏳️ {c['name'] if c else '?'}\n💰 ${p.get('budget',0):,}\n🛢️ {p.get('oil',0):,}{occ_txt}",
                parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))
    else:
        try: await q.edit_message_text(f"🌍⚔️ *WORLD WAR 26*\n\n/start\n\n📢 {CHANNEL_LINK}",parse_mode="Markdown")
        except: pass

async def cancel(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ لغو شد.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))
    return ConversationHandler.END

def main():
    app=Application.builder().token(BOT_TOKEN).build()
    decl_conv=ConversationHandler(
        entry_points=[CallbackQueryHandler(decl_start,pattern="^decl$")],
        states={WAITING_DECL_PHOTO:[MessageHandler(filters.PHOTO,decl_recv_photo),MessageHandler(filters.TEXT&~filters.COMMAND,decl_recv_text)]},
        fallbacks=[CommandHandler("cancel",cancel)])
    war_conv=ConversationHandler(
        entry_points=[CallbackQueryHandler(atk_target,pattern="^atk_")],
        states={WAITING_WAR:[MessageHandler(filters.TEXT&~filters.COMMAND,war_recv)]},
        fallbacks=[CommandHandler("cancel",cancel)])
    trade_conv=ConversationHandler(
        entry_points=[CallbackQueryHandler(trade_method,pattern="^tmethod_")],
        states={WAITING_TRADE_DETAIL:[MessageHandler(filters.TEXT&~filters.COMMAND,trade_recv)]},
        fallbacks=[CommandHandler("cancel",cancel)])

    for cmd,fn in [("start",start),("ban",cmd_ban),("unban",cmd_unban),("kick",cmd_kick),
                   ("setbudget",cmd_setbudget),("addbudget",cmd_addbudget),("setoil",cmd_setoil),
                   ("addoil",cmd_addoil),("givemoney",cmd_givemoney),
                   ("addequip",cmd_addequip),("removeequip",cmd_removeequip),("clearequip",cmd_removeequip_all),
                   ("equiplist",cmd_equiplist),("playerinfo",cmd_playerinfo),
                   ("setcountry",cmd_setcountry),("listcountries",cmd_listcountries),
                   ("toggle",cmd_toggle),("resetplayer",cmd_resetplayer),
                   ("resetall",cmd_resetall),("fullreset",cmd_fullreset),
                   ("clearwars",cmd_clearwars),("cleardecls",cmd_cleardecls),
                   ("freeall",cmd_freeall),("freecountry",cmd_freecountry),
                   ("occupiedlist",cmd_occupiedlist),("trades",cmd_trades),
                   ("warn",cmd_warn),("msg",cmd_msg),("channel",cmd_channel),
                   ("broadcast",cmd_broadcast),("adminhelp",cmd_help),
                   ("players",cmd_players),("adminstats",cmd_stats)]:
        app.add_handler(CommandHandler(cmd,fn))

    alliance_conv=ConversationHandler(
        entry_points=[CallbackQueryHandler(al_create_start,pattern="^al_create$")],
        states={WAITING_ALLIANCE_INFO:[MessageHandler(filters.TEXT&~filters.COMMAND,al_create_recv)]},
        fallbacks=[CommandHandler("cancel",cancel)])

    app.add_handler(alliance_conv)
    app.add_handler(war_conv)
    app.add_handler(trade_conv)

    for pat,fn in [("^choose$",choose_country),("^join_",join_country),("^back$",back),
                   ("^status$",show_status),("^borders$",borders_menu),("^border_",toggle_border),
                   ("^shop$",shop_menu),("^cat_",shop_cat),("^buy_",buy),("^fulllist$",full_list),
                   ("^war$",war_menu),("^trade_menu$",trade_menu),("^trade_",trade_select),
                   ("^taccept_",trade_accept),("^treject_",trade_reject),
                   ("^alliance_menu$",alliance_menu),("^al_join_list$",al_join_list),
                   ("^al_request_",al_send_request),("^al_accept_",al_accept),
                   ("^al_reject_",al_reject),("^al_leave_",al_leave),
                   ("^al_dissolve_",al_dissolve),("^al_requests_",al_requests_view),
                   ("^ref$",ref_menu),("^tutorial$",tutorial),
                   ("^quit$",quit_ask),("^quit_yes$",quit_yes),
                   ("^admin$",adm_panel),("^adm_p$",adm_p),("^adm_s$",adm_s),
                   ("^adm_w$",adm_w),("^adm_d$",adm_d),("^taken$",taken),("^noop$",noop)]:
        app.add_handler(CallbackQueryHandler(fn,pattern=pat))

    jq=app.job_queue
    jq.run_daily(job_income,time=time(20,30,0))
    jq.run_daily(job_news,time=time(17,30,0))
    print("✅ WW26 Bot v3.0 فعال شد!")
    app.run_polling()

if __name__=="__main__":
    main()
