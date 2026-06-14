import logging,json,os,random,asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import anthropic
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import (Application,CommandHandler,CallbackQueryHandler,
    MessageHandler,filters,ContextTypes,ConversationHandler)

BOT_TOKEN=os.environ.get("BOT_TOKEN","")
CHANNEL_ID=os.environ.get("CHANNEL_ID","")
ADMIN_ID=int(os.environ.get("ADMIN_ID","8441499331"))
ANTHROPIC_KEY=os.environ.get("ANTHROPIC_API_KEY","")
CHANNEL_LINK="https://t.me/ww26jang"
START_BUDGET=250000
logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)
DB_FILE="ww26.json"
GAME_SETTINGS={"shop":True,"decl":True,"war":True,"trade":True,"alliance":True,"occupy":True,"start_budget":250000}

# ── دیتابیس ──
def load_db():
    d={}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE,"r",encoding="utf-8") as f:
                d=json.load(f)
        except: d={}
    for k,v in [("players",{}),("declarations",[]),("wars",[]),("trades",[]),
                ("referrals",{}),("occupied",{}),("alliances",{}),("events",[]),
                ("sanctions",{}),("peace_treaties",{}),("market",{"oil":80}),
                ("world_tension",30),("admin_log",[]),("trade_offers",[]),
                ("un_cases",[])]:
        d.setdefault(k,v)
    return d

def save_db(d):
    with open(DB_FILE,"w",encoding="utf-8") as f:
        json.dump(d,f,ensure_ascii=False,indent=2)

COUNTRIES=[
 {"id":"cn","name":"🇨🇳 چین","oil":False,"nuclear":True,"oil_b":0,"borders":["ru","in","pk","kp","kr","vn","kz","af"],"sea":True,"gdp":18000,"pop":1400,"army":2000,"cont":"🌏 آسیا"},

 {"id":"ru","name":"🇷🇺 روسیه","oil":True,"nuclear":True,"oil_b":15000,"borders":["cn","ua","pl","no","fi","kz","az"],"sea":True,"gdp":2100,"pop":145,"army":1000,"cont":"🌏 آسیا"},

 {"id":"ir","name":"🇮🇷 ایران","oil":True,"nuclear":False,"oil_b":12000,"borders":["iq","tr","af","az","pk"],"sea":True,"gdp":360,"pop":87,"army":580,"cont":"🌏 آسیا"},

 {"id":"sa","name":"🇸🇦 عربستان","oil":True,"nuclear":False,"oil_b":20000,"borders":["iq","ae","ye","jo"],"sea":True,"gdp":1100,"pop":36,"army":230,"cont":"🌏 آسیا"},

 {"id":"in","name":"🇮🇳 هند","oil":False,"nuclear":True,"oil_b":0,"borders":["pk","cn","bd","mm"],"sea":True,"gdp":3700,"pop":1430,"army":1460,"cont":"🌏 آسیا"},

 {"id":"pk","name":"🇵🇰 پاکستان","oil":False,"nuclear":True,"oil_b":0,"borders":["ir","in","af","cn"],"sea":True,"gdp":375,"pop":231,"army":654,"cont":"🌏 آسیا"},

 {"id":"kp","name":"🇰🇵 کره شمالی","oil":False,"nuclear":True,"oil_b":0,"borders":["cn","kr"],"sea":True,"gdp":16,"pop":26,"army":1280,"cont":"🌏 آسیا"},

 {"id":"kr","name":"🇰🇷 کره جنوبی","oil":False,"nuclear":False,"oil_b":0,"borders":["kp"],"sea":True,"gdp":1800,"pop":52,"army":600,"cont":"🌏 آسیا"},

 {"id":"jp","name":"🇯🇵 ژاپن","oil":False,"nuclear":False,"oil_b":0,"borders":[],"sea":True,"gdp":4200,"pop":125,"army":247,"cont":"🌏 آسیا"},

 {"id":"tr","name":"🇹🇷 ترکیه","oil":False,"nuclear":False,"oil_b":0,"borders":["ru","ir","iq","gr","sy"],"sea":True,"gdp":906,"pop":85,"army":355,"cont":"🌏 آسیا"},

 {"id":"iq","name":"🇮🇶 عراق","oil":True,"nuclear":False,"oil_b":10000,"borders":["ir","tr","sa","ae","sy"],"sea":True,"gdp":250,"pop":42,"army":195,"cont":"🌏 آسیا"},

 {"id":"il","name":"🇮🇱 اسرائیل","oil":False,"nuclear":True,"oil_b":0,"borders":["eg","sy","lb"],"sea":True,"gdp":525,"pop":9,"army":170,"cont":"🌏 آسیا"},

 {"id":"ae","name":"🇦🇪 امارات","oil":True,"nuclear":False,"oil_b":8000,"borders":["sa","iq"],"sea":True,"gdp":500,"pop":10,"army":65,"cont":"🌏 آسیا"},

 {"id":"az","name":"🇦🇿 آذربایجان","oil":True,"nuclear":False,"oil_b":6000,"borders":["ru","ir","tr"],"sea":True,"gdp":78,"pop":10,"army":67,"cont":"🌏 آسیا"},

 {"id":"kz","name":"🇰🇿 قزاقستان","oil":True,"nuclear":False,"oil_b":7000,"borders":["ru","cn"],"sea":False,"gdp":225,"pop":19,"army":75,"cont":"🌏 آسیا"},

 {"id":"af","name":"🇦🇫 افغانستان","oil":False,"nuclear":False,"oil_b":0,"borders":["ir","pk","cn"],"sea":False,"gdp":20,"pop":40,"army":300,"cont":"🌏 آسیا"},

 {"id":"vn","name":"🇻🇳 ویتنام","oil":True,"nuclear":False,"oil_b":3000,"borders":["cn","th"],"sea":True,"gdp":430,"pop":97,"army":482,"cont":"🌏 آسیا"},

 {"id":"th","name":"🇹🇭 تایلند","oil":False,"nuclear":False,"oil_b":0,"borders":["mm","vn","my"],"sea":True,"gdp":544,"pop":72,"army":361,"cont":"🌏 آسیا"},

 {"id":"id","name":"🇮🇩 اندونزی","oil":True,"nuclear":False,"oil_b":5000,"borders":[],"sea":True,"gdp":1400,"pop":277,"army":395,"cont":"🌏 آسیا"},

 {"id":"us","name":"🇺🇸 آمریکا","oil":True,"nuclear":True,"oil_b":10000,"borders":["ca","mx"],"sea":True,"gdp":26000,"pop":335,"army":1385,"cont":"🌎 آمریکا"},

 {"id":"gb","name":"🇬🇧 انگلیس","oil":False,"nuclear":True,"oil_b":0,"borders":[],"sea":True,"gdp":3100,"pop":68,"army":148,"cont":"🌍 اروپا"},

 {"id":"fr","name":"🇫🇷 فرانسه","oil":False,"nuclear":True,"oil_b":0,"borders":["de","es","it","be"],"sea":True,"gdp":2900,"pop":68,"army":205,"cont":"🌍 اروپا"},

 {"id":"de","name":"🇩🇪 آلمان","oil":False,"nuclear":False,"oil_b":0,"borders":["fr","pl","nl","be","at"],"sea":True,"gdp":4000,"pop":84,"army":183,"cont":"🌍 اروپا"},

 {"id":"it","name":"🇮🇹 ایتالیا","oil":False,"nuclear":False,"oil_b":0,"borders":["fr","at","ch"],"sea":True,"gdp":2100,"pop":60,"army":170,"cont":"🌍 اروپا"},

 {"id":"es","name":"🇪🇸 اسپانیا","oil":False,"nuclear":False,"oil_b":0,"borders":["fr","pt"],"sea":True,"gdp":1500,"pop":47,"army":122,"cont":"🌍 اروپا"},

 {"id":"pl","name":"🇵🇱 لهستان","oil":False,"nuclear":False,"oil_b":0,"borders":["de","ua","ru"],"sea":True,"gdp":700,"pop":38,"army":120,"cont":"🌍 اروپا"},

 {"id":"ua","name":"🇺🇦 اوکراین","oil":False,"nuclear":False,"oil_b":0,"borders":["ru","pl","ro"],"sea":True,"gdp":160,"pop":44,"army":900,"cont":"🌍 اروپا"},

 {"id":"no","name":"🇳🇴 نروژ","oil":True,"nuclear":False,"oil_b":9000,"borders":["se","ru","fi"],"sea":True,"gdp":540,"pop":5,"army":23,"cont":"🌍 اروپا"},

 {"id":"br","name":"🇧🇷 برزیل","oil":True,"nuclear":False,"oil_b":8000,"borders":["ar","co","ve"],"sea":True,"gdp":2100,"pop":215,"army":368,"cont":"🌎 آمریکا"},

 {"id":"mx","name":"🇲🇽 مکزیک","oil":True,"nuclear":False,"oil_b":6000,"borders":["us"],"sea":True,"gdp":1450,"pop":128,"army":282,"cont":"🌎 آمریکا"},

 {"id":"ar","name":"🇦🇷 آرژانتین","oil":True,"nuclear":False,"oil_b":4000,"borders":["br","cl"],"sea":True,"gdp":640,"pop":46,"army":73,"cont":"🌎 آمریکا"},

 {"id":"ca","name":"🇨🇦 کانادا","oil":True,"nuclear":False,"oil_b":8000,"borders":["us"],"sea":True,"gdp":2100,"pop":38,"army":71,"cont":"🌎 آمریکا"},

 {"id":"ve","name":"🇻🇪 ونزوئلا","oil":True,"nuclear":False,"oil_b":9000,"borders":["br","co"],"sea":True,"gdp":95,"pop":29,"army":123,"cont":"🌎 آمریکا"},

 {"id":"ng","name":"🇳🇬 نیجریه","oil":True,"nuclear":False,"oil_b":8000,"borders":["cm"],"sea":True,"gdp":440,"pop":220,"army":135,"cont":"🌍 آفریقا"},

 {"id":"za","name":"🇿🇦 آفریقای جنوبی","oil":False,"nuclear":False,"oil_b":0,"borders":[],"sea":True,"gdp":405,"pop":60,"army":78,"cont":"🌍 آفریقا"},

 {"id":"eg","name":"🇪🇬 مصر","oil":True,"nuclear":False,"oil_b":4000,"borders":["ly","sd","il"],"sea":True,"gdp":475,"pop":105,"army":440,"cont":"🌍 آفریقا"},

 {"id":"au","name":"🇦🇺 استرالیا","oil":True,"nuclear":False,"oil_b":5000,"borders":[],"sea":True,"gdp":1700,"pop":26,"army":59,"cont":"🌏 اقیانوسیه"},

 {"id":"ly","name":"🇱🇾 لیبی","oil":True,"nuclear":False,"oil_b":6000,"borders":["eg","dz"],"sea":True,"gdp":45,"pop":7,"army":76,"cont":"🌍 آفریقا"},

 {"id":"sy","name":"🇸🇾 سوریه","oil":True,"nuclear":False,"oil_b":3000,"borders":["tr","iq","il","lb"],"sea":True,"gdp":60,"pop":21,"army":170,"cont":"🌏 آسیا"},

 {"id":"sd","name":"🇸🇩 سودان","oil":True,"nuclear":False,"oil_b":2000,"borders":["eg","et"],"sea":True,"gdp":36,"pop":46,"army":109,"cont":"🌍 آفریقا"},

]
def get_country(cid): return next((c for c in COUNTRIES if c["id"]==cid),None)

EQUIP={
 "✈️ هوایی":[
  {"id":"launcher","name":"🚀 سیستم لانچر","price":40000,"oil":0,"type":"support","power":0,"desc":"الزامی برای شلیک موشک"},
  {"id":"f16","name":"🛩️ ۸ جنگنده F-16","price":55000,"oil":0,"type":"attack","power":80,"desc":"برد ۵۵۰km - نابودی ۸۰ سرباز"},
  {"id":"f35","name":"🛩️ ۶ جنگنده F-35","price":90000,"oil":0,"type":"attack","power":150,"desc":"استلث - برد ۱۰۰۰km"},
  {"id":"f22","name":"🛩️ ۴ جنگنده F-22","price":140000,"oil":0,"type":"attack","power":220,"desc":"فوق استلث - سریع‌ترین"},
  {"id":"su57","name":"🛩️ ۴ جنگنده Su-57","price":130000,"oil":0,"type":"attack","power":200,"desc":"استلث روسی - برد ۳۵۰۰km"},
  {"id":"b52","name":"💣 ۳ بمب‌افکن B-52","price":110000,"oil":0,"type":"attack","power":350,"desc":"بمباران فرش - ۳۱ تن بمب"},
  {"id":"b2","name":"💣 ۲ بمب‌افکن B-2","price":200000,"oil":0,"type":"attack","power":450,"desc":"فوق استلث - رادار نمیبینه"},
  {"id":"b21","name":"💣 B-21 Raider","price":350000,"oil":0,"type":"attack","power":700,"desc":"جدیدترین بمب‌افکن ۲۰۲۴"},
  {"id":"tu160","name":"💣 Tu-160 روسیه","price":280000,"oil":0,"type":"attack","power":600,"desc":"برد ۱۲۰۰۰km"},
  {"id":"apache","name":"🚁 ۸ هلیکوپتر Apache","price":35000,"oil":0,"type":"attack","power":180,"desc":"ضد زره - موشک Hellfire"},
  {"id":"ka52","name":"🚁 ۶ هلیکوپتر Ka-52","price":45000,"oil":0,"type":"attack","power":220,"desc":"هلیکوپتر شکارچی روسی"},
  {"id":"drone","name":"🤖 ۲۰ پهپاد Bayraktar","price":25000,"oil":0,"type":"attack","power":100,"desc":"پهپاد ترکی - سقف ۷۵۰۰m"},
  {"id":"mq9","name":"🤖 ۵ پهپاد MQ-9","price":80000,"oil":0,"type":"attack","power":250,"desc":"شکارچی آمریکایی"},
  {"id":"shahed","name":"🤖 ۵۰ شاهد ۱۳۶","price":30000,"oil":0,"type":"attack","power":120,"desc":"پهپاد انتحاری - برد ۲۵۰۰km"},
  {"id":"s300","name":"🛡️ S-300","price":120000,"oil":0,"type":"defense","power":150,"desc":"برد ۲۰۰km - ۲۵ جنگنده"},
  {"id":"s400","name":"🛡️ S-400","price":200000,"oil":0,"type":"defense","power":220,"desc":"برد ۴۰۰km - ضد استلث"},
  {"id":"s500","name":"🛡️ S-500","price":380000,"oil":0,"type":"defense","power":350,"desc":"رهگیری هایپرسونیک"},
  {"id":"patriot","name":"🛡️ پاتریوت PAC-3","price":90000,"oil":0,"type":"defense","power":120,"desc":"رهگیری کروز ۸۵٪"},
  {"id":"iron_dome","name":"🛡️ گنبد آهنین","price":120000,"oil":0,"type":"defense","power":180,"desc":"رهگیری راکت ۹۵٪"},
  {"id":"manpad","name":"🛡️ MANPAD","price":30000,"oil":0,"type":"defense","power":50,"desc":"سرنگونی هلیکوپتر"},
 ],
 "🚢 دریایی":[
  {"id":"cargo_ship","name":"🚢 کشتی باربری","price":30000,"oil":0,"type":"transport","power":0,"desc":"معامله دریایی"},
  {"id":"corvette","name":"⚓ ۳ کوروت Buyan-M","price":40000,"oil":0,"type":"attack","power":60,"desc":"موشک Kalibr - برد ۱۵۰۰km"},
  {"id":"frigate","name":"🚢 ۲ فریگات","price":65000,"oil":0,"type":"attack","power":120,"desc":"ضد زیردریایی - موشک کروز"},
  {"id":"destroyer","name":"🚢 ناو اژدرافکن","price":100000,"oil":0,"type":"attack","power":200,"desc":"۹۶ موشک Tomahawk"},
  {"id":"carrier","name":"🚢 ناو هواپیمابر","price":250000,"oil":0,"type":"attack","power":500,"desc":"۷۵ جنگنده - قدرت مطلق"},
  {"id":"submarine","name":"🌊 ۲ زیردریایی اتمی","price":120000,"oil":0,"type":"attack","power":250,"desc":"حمله مخفی - موشک Tomahawk"},
  {"id":"submarine_d","name":"🌊 ۳ زیردریایی دیزلی","price":70000,"oil":0,"type":"attack","power":150,"desc":"ارزان - مناسب آب کم‌عمق"},
  {"id":"mine_layer","name":"⚓ مین‌گذار","price":45000,"oil":0,"type":"defense","power":100,"desc":"مسدود کردن آبراه‌ها"},
  {"id":"coastal_bat","name":"🛡️ باتری ساحلی","price":80000,"oil":0,"type":"defense","power":150,"desc":"موشک ضدکشتی - برد ۳۰۰km"},
 ],
 "🚀 موشکی":[
  {"id":"grad","name":"🚀 ۲۰۰ راکت گراد","price":15000,"oil":200,"type":"attack","power":80,"desc":"برد ۴۰km - نیاز لانچر"},
  {"id":"smerch","name":"🚀 ۵۰ راکت Smerch","price":35000,"oil":500,"type":"attack","power":200,"desc":"برد ۹۰km - نیاز لانچر"},
  {"id":"tactical","name":"🚀 موشک Iskander","price":80000,"oil":600,"type":"attack","power":250,"desc":"برد ۵۰۰km - دقت ۵m"},
  {"id":"cruise","name":"🚀 ۵۰ موشک کروز","price":100000,"oil":1500,"type":"attack","power":350,"desc":"برد ۲۵۰۰km - دقت ۳m"},
  {"id":"kalibr","name":"🚀 ۳۰ موشک Kalibr","price":90000,"oil":1200,"type":"attack","power":300,"desc":"از دریا/زمین - برد ۲۰۰۰km"},
  {"id":"ballistic","name":"🚀 موشک بالستیک","price":130000,"oil":2000,"type":"attack","power":450,"desc":"برد ۳۰۰۰km"},
  {"id":"hypersonic","name":"⚡ هایپرسونیک","price":300000,"oil":6000,"type":"attack","power":900,"desc":"ماخ ۱۵ - غیرقابل رهگیری"},
  {"id":"kinzhal","name":"⚡ کینژال","price":250000,"oil":5000,"type":"attack","power":800,"desc":"هایپرسونیک روسی ماخ ۱۰"},
  {"id":"oreshnik","name":"⚡ اورشنیک","price":400000,"oil":8000,"type":"attack","power":1200,"desc":"جدیدترین موشک ۲۰۲۴"},
  {"id":"icbm","name":"🚀 موشک قاره‌پیما","price":500000,"oil":12000,"type":"attack","power":2000,"desc":"برد ۱۲۰۰۰km - MIRV"},
  {"id":"atom","name":"☢️ بمب اتمی","price":5000000,"oil":0,"type":"attack","power":8000,"desc":"نیاز: اتمی + معدن اورانیوم + غنی‌سازی ⚠️"},
  {"id":"hydrogen","name":"☢️ بمب هیدروژنی","price":12000000,"oil":0,"type":"attack","power":20000,"desc":"قوی‌ترین سلاح ⚠️"},
  {"id":"neutron","name":"☢️ بمب نوترونی","price":6000000,"oil":0,"type":"attack","power":9000,"desc":"کشتار بدون تخریب ⚠️"},
  {"id":"thaad","name":"🛡️ THAAD","price":180000,"oil":0,"type":"defense","power":250,"desc":"رهگیری بالستیک ۹۰٪"},
  {"id":"cram","name":"🛡️ C-RAM","price":45000,"oil":0,"type":"defense","power":80,"desc":"رهگیری راکت ۹۵٪"},
  {"id":"arrow3","name":"🛡️ Arrow-3","price":250000,"oil":0,"type":"defense","power":320,"desc":"رهگیری هایپرسونیک ۷۰٪"},
 ],
 "🪖 زمینی":[
  {"id":"truck","name":"🚛 ناوگان کامیون","price":20000,"oil":0,"type":"transport","power":0,"desc":"معامله زمینی"},
  {"id":"infantry","name":"👤 ۵۰۰۰ سرباز","price":50000,"oil":0,"type":"ground","power":100,"desc":"نیروی پایه"},
  {"id":"special","name":"🪖 ۲۰۰۰ نیروی ویژه","price":80000,"oil":0,"type":"ground","power":200,"desc":"عملیات شب - بدون اثر"},
  {"id":"marine","name":"⚓ ۱۵۰۰ تفنگدار","price":70000,"oil":0,"type":"ground","power":180,"desc":"عملیات آبی‌خاکی"},
  {"id":"para","name":"🪂 ۸۰۰ چترباز","price":60000,"oil":0,"type":"ground","power":150,"desc":"پیاده‌سازی هوایی"},
  {"id":"t72","name":"🚓 ۵۰ تانک T-72","price":45000,"oil":0,"type":"ground","power":200,"desc":"زره ۵۰۰mm - توپ ۱۲۵mm"},
  {"id":"t90","name":"🦾 ۳۰ تانک T-90M","price":90000,"oil":0,"type":"ground","power":350,"desc":"بهترین تانک روسی"},
  {"id":"abrams","name":"🦾 ۳۰ تانک Abrams","price":100000,"oil":0,"type":"ground","power":400,"desc":"بهترین تانک غربی"},
  {"id":"merkava","name":"🛡️ ۲۵ تانک Merkava","price":120000,"oil":0,"type":"ground","power":450,"desc":"ایمن‌ترین تانک - ضد موشک"},
  {"id":"k2","name":"🦾 ۲۵ تانک K2","price":130000,"oil":0,"type":"ground","power":480,"desc":"پیشرفته‌ترین تانک آسیا"},
  {"id":"bradley","name":"🚗 ۴۰ نفربر Bradley","price":60000,"oil":0,"type":"ground","power":180,"desc":"نفربر زرهی - توپ ۲۵mm"},
  {"id":"himars","name":"🎯 HIMARS","price":90000,"oil":0,"type":"attack","power":350,"desc":"دقیق‌ترین توپخانه - GPS"},
  {"id":"howitzer","name":"🎯 ۱۰ هویتزر","price":40000,"oil":0,"type":"attack","power":150,"desc":"برد ۴۰km"},
  {"id":"caesar","name":"🎯 ۸ توپ Caesar","price":70000,"oil":0,"type":"attack","power":250,"desc":"توپخانه فرانسوی - برد ۵۵km"},
  {"id":"javelin","name":"🎯 جاولین","price":60000,"oil":0,"type":"attack","power":200,"desc":"ضد تانک - برد ۴km"},
  {"id":"kornet","name":"🎯 موشک کورنت","price":40000,"oil":0,"type":"attack","power":150,"desc":"ضد تانک روسی"},
  {"id":"gdef_heavy","name":"🛡️ دفاع سنگین","price":220000,"oil":0,"type":"defense","power":300,"desc":"استحکامات بتنی + مین"},
  {"id":"gdef_mid","name":"🛡️ دفاع متوسط","price":140000,"oil":0,"type":"defense","power":180,"desc":"سنگر + سیم خاردار"},
  {"id":"trench","name":"🛡️ خندق و سنگر","price":20000,"oil":0,"type":"defense","power":60,"desc":"کاهش ۳۰٪ تلفات"},
  {"id":"landmine","name":"💣 میدان مین","price":25000,"oil":0,"type":"defense","power":80,"desc":"کاهش ۴۰٪ نیروی حمله"},
 ],
 "⛏️ اقتصادی":[
  {"id":"iron","name":"⛏️ معدن آهن","price":10000,"oil":0,"type":"economy","daily":4000,"desc":"۴,۰۰۰$/روز"},
  {"id":"copper","name":"⛏️ معدن مس","price":15000,"oil":0,"type":"economy","daily":6000,"desc":"۶,۰۰۰$/روز"},
  {"id":"silver","name":"⛏️ معدن نقره","price":22000,"oil":0,"type":"economy","daily":9000,"desc":"۹,۰۰۰$/روز"},
  {"id":"gold","name":"⛏️ معدن طلا","price":35000,"oil":0,"type":"economy","daily":14000,"desc":"۱۴,۰۰۰$/روز"},
  {"id":"diamond","name":"⛏️ معدن الماس","price":60000,"oil":0,"type":"economy","daily":22000,"desc":"۲۲,۰۰۰$/روز"},
  {"id":"lithium","name":"⚡ معدن لیتیوم","price":70000,"oil":0,"type":"economy","daily":25000,"desc":"۲۵,۰۰۰$/روز"},
  {"id":"uranium_mine","name":"☢️ معدن اورانیوم","price":80000,"oil":0,"type":"economy","daily":10000,"desc":"۱۰,۰۰۰$/روز - فقط اتمی"},
  {"id":"enrichment","name":"☢️ تأسیسات غنی‌سازی","price":500000,"oil":0,"type":"economy","daily":5000,"desc":"پیش‌نیاز بمب اتمی - فقط اتمی"},
  {"id":"refinery","name":"🛢️ پالایشگاه","price":50000,"oil":0,"type":"economy","daily":0,"oil_daily":1500,"desc":"فقط نفتی - ۱۵۰۰ بشکه/روز"},
  {"id":"oil_plat","name":"🛢️ سکوی نفتی","price":90000,"oil":0,"type":"economy","daily":0,"oil_daily":3000,"desc":"فقط نفتی - ۳۰۰۰ بشکه/روز"},
  {"id":"factory","name":"🏭 کارخانه","price":70000,"oil":0,"type":"economy","daily":15000,"desc":"۱۵,۰۰۰$/روز"},
  {"id":"port","name":"⚓ بندر","price":45000,"oil":0,"type":"economy","daily":10000,"desc":"۱۰,۰۰۰$/روز"},
  {"id":"bank","name":"🏦 بانک مرکزی","price":100000,"oil":0,"type":"economy","daily":25000,"desc":"۲۵,۰۰۰$/روز"},
  {"id":"tech_hub","name":"💻 مرکز فناوری","price":150000,"oil":0,"type":"economy","daily":40000,"desc":"۴۰,۰۰۰$/روز"},
  {"id":"arms_industry","name":"🔫 صنایع دفاعی","price":200000,"oil":0,"type":"economy","daily":50000,"desc":"۵۰,۰۰۰$/روز"},
  {"id":"space_center","name":"🚀 مرکز فضایی","price":300000,"oil":0,"type":"economy","daily":80000,"desc":"۸۰,۰۰۰$/روز"},
 ],
 "🖥️ سایبری":[
  {"id":"hack","name":"💻 واحد هک APT","price":150000,"oil":0,"type":"attack","power":400,"desc":"فلج شبکه برق و آب"},
  {"id":"stuxnet","name":"☢️💻 سلاح سایبری","price":400000,"oil":0,"type":"attack","power":1000,"desc":"نابودی تأسیسات هسته‌ای"},
  {"id":"spy_cyber","name":"🔍 جاسوسی سایبری","price":100000,"oil":0,"type":"intel","power":200,"desc":"دزدیدن اسرار نظامی"},
  {"id":"satellite","name":"🛸 ماهواره جاسوسی","price":200000,"oil":0,"type":"intel","power":300,"desc":"رصد زمان واقعی"},
  {"id":"antihack","name":"🛡️ ضدهک","price":80000,"oil":0,"type":"defense","power":150,"desc":"دفع ۸۰٪ حملات سایبری"},
  {"id":"radar","name":"📡 رادار فازآرایه","price":90000,"oil":0,"type":"defense","power":120,"desc":"شناسایی از ۵۰۰km"},
  {"id":"jammer","name":"📡 جمر الکترونیکی","price":70000,"oil":0,"type":"defense","power":100,"desc":"۵۰٪ کاهش دقت موشک"},
  {"id":"emp","name":"💥 بمب EMP","price":250000,"oil":0,"type":"attack","power":600,"desc":"فلج الکترونیک شعاع ۵۰km"},
 ],
 "🕵️ جاسوسی":[
  {"id":"cia_network","name":"🕵️ شبکه CIA/MI6","price":300000,"oil":0,"type":"intel","power":300,"desc":"جاسوس در کابینه دشمن"},
  {"id":"saboteur","name":"💣 تیم خرابکاری","price":180000,"oil":0,"type":"intel","power":200,"desc":"انفجار پل و نیروگاه"},
  {"id":"assassin","name":"🗡️ تیم ترور","price":500000,"oil":0,"type":"intel","power":500,"desc":"حذف رهبران کلیدی"},
  {"id":"sleeper","name":"😴 عامل خفته","price":250000,"oil":0,"type":"intel","power":250,"desc":"جاسوس در ارتش دشمن"},
  {"id":"misinformation","name":"📰 اطلاعات کاذب","price":100000,"oil":0,"type":"intel","power":100,"desc":"پخش اطلاعات غلط"},
  {"id":"tunnel","name":"🕳️ شبکه تونل","price":150000,"oil":0,"type":"defense","power":200,"desc":"مقاومت در برابر اشغال"},
 ],
}
def get_eq_name(eid):
    for cat in EQUIP.values():
        for item in cat:
            if item["id"]==eid: return item["name"]
    return eid

WEAPON_MAP={
 "f-16":"f16","f16":"f16","f-35":"f35","f35":"f35","f-22":"f22","f22":"f22",
 "b-52":"b52","b52":"b52","b-2":"b2","b2":"b2","b-21":"b21","b21":"b21",
 "اپاچی":"apache","apache":"apache","ka-52":"ka52","ka52":"ka52",
 "پهپاد":"drone","بیرقدار":"drone","mq-9":"mq9","mq9":"mq9","شاهد":"shahed",
 "گراد":"grad","grad":"grad","smerch":"smerch","اسکندر":"tactical","iskander":"tactical",
 "کروز":"cruise","cruise":"cruise","kalibr":"kalibr","کالیبر":"kalibr",
 "بالستیک":"ballistic","ballistic":"ballistic",
 "هایپرسونیک":"hypersonic","hypersonic":"hypersonic",
 "کینژال":"kinzhal","kinzhal":"kinzhal","اورشنیک":"oreshnik","oreshnik":"oreshnik",
 "قاره‌پیما":"icbm","قاره پیما":"icbm","icbm":"icbm",
 "اتمی":"atom","بمب اتم":"atom","هسته‌ای":"atom","هیدروژنی":"hydrogen","نوترونی":"neutron",
 "t-72":"t72","t72":"t72","t-90":"t90","t90":"t90",
 "ابرامز":"abrams","abrams":"abrams","مرکاوا":"merkava","merkava":"merkava","k2":"k2",
 "برادلی":"bradley","bradley":"bradley",
 "ناو هواپیمابر":"carrier","carrier":"carrier",
 "زیردریایی":"submarine","submarine":"submarine",
 "فریگات":"frigate","frigate":"frigate","کوروت":"corvette",
 "هیمارس":"himars","himars":"himars","هویتزر":"howitzer","howitzer":"howitzer",
 "سزار":"caesar","caesar":"caesar","جاولین":"javelin","javelin":"javelin","کورنت":"kornet",
 "s-400":"s400","s400":"s400","s-300":"s300","s300":"s300","s-500":"s500","s500":"s500",
 "گنبد آهنین":"iron_dome","iron dome":"iron_dome","پاتریوت":"patriot","patriot":"patriot",
 "thaad":"thaad","arrow":"arrow3","هلیکوپتر":"apache",
 "نیروی ویژه":"special","کماندو":"special","چترباز":"para","تفنگدار":"marine",
 "هک":"hack","سایبری":"hack","ماهواره":"satellite","emp":"emp",
 "موشک":"tactical","راکت":"grad","توپخانه":"howitzer","سرباز":"infantry",
}

def check_scenario(scenario,eq_ids):
    sc=scenario.lower()
    missing=[]
    for kw,eid in WEAPON_MAP.items():
        if kw in sc and eid not in eq_ids and eid not in missing:
            missing.append(eid)
    needs_launcher=any(w in sc for w in ["موشک","راکت","گراد","کروز","بالستیک","himars","هیمارس","اسکندر","iskander"])
    if needs_launcher and "launcher" not in eq_ids and "launcher" not in missing:
        missing.append("launcher")
    return missing

def calc_daily(p): return sum(e.get("daily",0) for e in p.get("equipment",[]) if e.get("type")=="economy")
def calc_oil_daily(p): return sum(e.get("oil_daily",0) for e in p.get("equipment",[]) if e.get("type")=="economy")
def calc_power(p): return sum(e.get("power",0) for e in p.get("equipment",[]) if e.get("type") in ["attack","ground","defense","intel"])
def get_rank(db,uid):
    op=db.get("market",{}).get("oil",80)
    scores={k:v.get("budget",0)+v.get("oil",0)*op for k,v in db["players"].items()}
    ranked=sorted(scores,key=scores.get,reverse=True)
    return ranked.index(uid)+1 if uid in ranked else len(ranked)+1
def get_ai(): return anthropic.Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None

RANDOM_EVENTS=[
 ("زلزله","budget",-80000,"زیرساخت کشور تخریب شد!"),
 ("سیل مرگبار","budget",-60000,"شهرهای ساحلی غرق شد!"),
 ("آتش سوزی","budget",-50000,"آتش سوزی گسترده!"),
 ("طوفان","budget",-70000,"طوفان ویرانگر!"),
 ("حادثه هسته ای","budget",-200000,"نشت رادیواکتیو!"),
 ("حمله سایبری","budget",-90000,"زیرساخت دیجیتال فلج شد!"),
 ("کودتا","budget",-150000,"ارتش قدرت گرفت!"),
 ("بحران اقتصادی","budget",-120000,"بورس سقوط کرد!"),
 ("اپیدمی","budget",-100000,"بیماری شیوع یافت!"),
 ("بحران غذایی","budget",-80000,"خشکسالی محصولات را نابود کرد!"),
 ("انفجار پالایشگاه","budget",-130000,"پالایشگاه اصلی منفجر شد!"),
 ("کشف ذخایر نفت","budget",200000,"اکتشاف نفت در سرزمین شما!"),
 ("کشف معدن طلا","budget",150000,"معادن طلا کشف شد!"),
 ("رونق اقتصادی","budget",100000,"صادرات رکورد زد!"),
 ("کمک بین المللی","budget",120000,"کمک مالی از متحدان!"),
 ("پیشرفت فناوری","budget",180000,"اختراع انقلابی!"),
 ("جام جهانی","budget",80000,"درآمد توریسم انفجار یافت!"),
 ("انقلاب انرژی","budget",90000,"انرژی تجدیدپذیر رشد کرد!"),
 ("کشف الماس","budget",170000,"معادن الماس کشف شد!"),
 ("بحران نفتی جهانی","oil_price",30,"قیمت نفت جهش کرد!"),
 ("سقوط قیمت نفت","oil_price",-25,"عرضه بیش از تقاضا!"),
 ("کشف دارو","budget",110000,"صادرات دارویی رکورد زد!"),
 ("بحران کشتیرانی","budget",-70000,"مسیر تجاری مسدود شد!"),
 ("زلزله شدید","budget",-90000,"زلزله ۸ ریشتری!"),
 ("سرمایه گذاری خارجی","budget",160000,"شرکت های بزرگ سرمایه گذاری کردند!"),
]

async def ai_war(ac,dc,ap,dp,scenario,db):
    client=get_ai()
    atk_eq=[e for e in ap.get("equipment",[]) if e.get("type") in ["attack","ground"]]
    def_eq=[e for e in dp.get("equipment",[]) if e.get("type")=="defense"]
    atk_pow=sum(e.get("power",0) for e in atk_eq)
    def_pow=sum(e.get("power",0) for e in def_eq)
    has_ground=any(e["type"]=="ground" for e in atk_eq)
    is_sanc=ac["id"] in db.get("sanctions",{})
    if is_sanc: atk_pow=int(atk_pow*0.8)
    atk_txt="\n".join(f"- {e['name']} ({e.get('power',0)}): {e['desc']}" for e in atk_eq) or "هیچ"
    def_txt="\n".join(f"- {e['name']} ({e.get('power',0)})" for e in def_eq) or "بدون پدافند"
    if not client:
        win="attacker" if atk_pow>def_pow else "defender"
        return {"winner":win,"atk_loss":35,"def_loss":25,"story":f"نیروهای {ac['name']} حمله کردند.","key_moment":"خط شکست","territory":"تغییر جزئی","civilian":False,"fine":0,"occupied":has_ground and win=="attacker","sat":f"درگیری {ac['name']} vs {dc['name']}","aftermath":"جنگ پایان یافت.","international_reaction":"جهان نگران.","un_action":"سازمان ملل خواستار آتش بس شد."}
    try:
        prompt=f"حمله کننده: {ac['name']} ارتش:{ac.get('army',0)}k\n"
        prompt+=f"مدافع: {dc['name']} ارتش:{dc.get('army',0)}k\n"
        prompt+=f"تجهیزات حمله (قدرت:{atk_pow}):\n{atk_txt}\n"
        prompt+=f"پدافند (قدرت:{def_pow}):\n{def_txt}\n"
        prompt+=f"نیروی زمینی: {has_ground}\n"
        prompt+=f"تحریم: {is_sanc}\n"
        prompt+=f"سناریو:\n{scenario}"
        r=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=1800,
         system='''ژنرال ارشد بازی World War 26.
قوانین: فقط تجهیزات لیست شده. اشغال فقط با زمینی. بمب اتمی=civilian:true+fine>=500000. تحریم=20% کاهش. موشک بدون لانچر=بی اثر.
اگه سناریو مناطق مسکونی ذکر نکرده ولی احتمال تلفات غیرنظامی هست civilian:true.
داستان: شهرهای واقعی، تلفات دقیق (مثلا 3400 کشته)، هر تجهیز توضیح داشته باشد.
فقط JSON بدون هیچ چیز اضافه:
{"winner":"attacker یا defender","atk_loss":عدد,"def_loss":عدد,"story":"10-12 جمله","key_moment":"یک جمله","territory":"وضعیت","civilian":bool,"fine":عدد,"occupied":bool,"sat":"2 جمله خبری","aftermath":"2 جمله","international_reaction":"1 جمله","un_action":"اقدام سازمان ملل"}''',
         messages=[{"role":"user","content":prompt}])
        txt=r.content[0].text.strip().replace("```json","").replace("```","")
        return json.loads(txt)
    except Exception as e:
        logger.error(f"AI war:{e}")
        win="attacker" if atk_pow>def_pow*0.8 else "defender"
        return {"winner":win,"atk_loss":30,"def_loss":25,"story":"نبرد سختی در جریان بود.","key_moment":"لحظه شکست","territory":"تغییر","civilian":False,"fine":0,"occupied":has_ground and win=="attacker","sat":f"جنگ {ac['name']} و {dc['name']}","aftermath":"نبرد پایان یافت.","international_reaction":"جهان نگران.","un_action":"سازمان ملل خواستار توقف درگیری شد."}

async def ai_decl(country,text):
    if len(text.strip())<15: return {"approved":False,"reason":"متن خیلی کوتاه","edited":text}
    client=get_ai()
    if not client: return {"approved":True,"reason":"","edited":text}
    try:
        r=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=400,
         system='ناظر بیانیه WW26. فقط اگه کاملا بی معنی یا اسپم است رد کن. JSON: {"approved":true,"reason":"","edited":"متن"}',
         messages=[{"role":"user","content":f"کشور:{country}\n{text}"}])
        return json.loads(r.content[0].text.strip().replace("```json","").replace("```",""))
    except: return {"approved":True,"reason":"","edited":text}

async def ai_news(db):
    client=get_ai()
    wars=db.get("wars",[])[-5:]
    players=db.get("players",{})
    op=db.get("market",{}).get("oil",80)
    tension=db.get("world_tension",30)
    if not client: return f"خلاصه روزانه\n{len(wars)} جنگ | {len(players)} بازیکن"
    try:
        wt="\n".join(f"- {w['atk']} vs {w['def']} => {w['winner']}" for w in wars) or "جنگی نبود"
        ranking=sorted(players.values(),key=lambda x:x.get("budget",0)+x.get("oil",0)*op,reverse=True)[:5]
        rtxt="\n".join(f"{i+1}. {get_country(p.get('country_id',''))['name'] if get_country(p.get('country_id','')) else '?'}" for i,p in enumerate(ranking))
        r=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=600,
         system="خبرنگار BBC فارسی WW26. خلاصه روزانه هیجانی بنویس. Markdown.",
         messages=[{"role":"user","content":f"بازیکنان:{len(players)}\nتنش:{tension}%\nنفت:${op}\n{wt}\n{rtxt}"}])
        return f"📰 *خلاصه روزانه BBC WW26*\n━━━━━━━━━━━━━━━\n{r.content[0].text}"
    except: return f"📰 خلاصه روزانه\n{len(wars)} جنگ | {len(players)} بازیکن"

W_DECL=1;W_WAR=2;W_GIVE_MONEY=3;W_GIVE_OIL=4;W_TRADE_OFFER=5;W_ADM_BUDGET=6;W_ALLIANCE_DECL=7

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

    if not p and update.effective_user.id == ADMIN_ID:
        kb = [[InlineKeyboardButton("👑 پنل ادمین", callback_data="admin")],
              [InlineKeyboardButton("🌍 انتخاب کشور", callback_data="choose")]]
        await update.message.reply_text("👑 ادمین خوش اومدی!\nمیتونی کشور انتخاب کنی یا بدون کشور ادمین کنی.", reply_markup=InlineKeyboardMarkup(kb))
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
            [InlineKeyboardButton("🚪 خروج از بازی", callback_data="quit")],
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
        "budget": GAME_SETTINGS.get("start_budget", START_BUDGET),
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
        "✍️ متن بیانیه رو بنویس (حداقل ۱۵ کاراکتر)\n"
        "📸 یا یک عکس همراه با متن در کپشن بفرست\n\n"
        "✅ رسمی، مؤدبانه | ❌ بدون فحش\n"
        "لغو: /cancel",
        parse_mode="Markdown"
    )
    return W_DECL


async def _publish_decl(update, context, db, uid, p, caption, photo_id=None):
    c = get_country(p["country_id"])
    await update.message.reply_text("⏳ AI بررسی می‌کنه...")
    r = await ai_decl(c["name"], caption)
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
            f"📡 کانال: {CHANNEL_LINK}\n\n"
            f"⊱⋅ ─────────────────── ⋅⊰"
        )
        db["declarations"].append({"id": len(db["declarations"]) + 1, "user_id": uid, "country": c["name"],
                                    "text": r["edited"], "date": datetime.now().isoformat()})
        db["players"][uid]["last_decl"] = datetime.now().isoformat()
        save_db(db)
        try:
            if photo_id:
                await context.bot.send_photo(CHANNEL_ID, photo=photo_id, caption=formatted)
            else:
                await context.bot.send_message(CHANNEL_ID, formatted)
            await update.message.reply_text("✅ بیانیه تایید و در کانال منتشر شد!")
        except Exception as e:
            await update.message.reply_text(f"✅ تایید شد - خطای کانال: {e}")
    else:
        await update.message.reply_text(f"❌ رد شد!\n💬 {r['reason']}")
    await update.message.reply_text(".",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پنل", callback_data="back")]]))


async def decl_recv_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return ConversationHandler.END
    caption = update.message.caption or ""
    if len(caption.strip()) < 15:
        await update.message.reply_text("❌ متن کپشن خیلی کوتاهه (حداقل ۱۵ کاراکتر)! دوباره بفرست یا /cancel")
        return W_DECL
    await _publish_decl(update, context, db, uid, p, caption, photo_id=update.message.photo[-1].file_id)
    return ConversationHandler.END


async def decl_recv_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p:
        return ConversationHandler.END
    text = update.message.text or ""
    if len(text.strip()) < 15:
        await update.message.reply_text("❌ متن خیلی کوتاهه (حداقل ۱۵ کاراکتر)! دوباره بفرست یا /cancel")
        return W_DECL
    await _publish_decl(update, context, db, uid, p, text, photo_id=None)
    return ConversationHandler.END


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
        ("🌍 زلزله ۷.۸ ریشتری","budget",-80000,"زیرساخت‌های کشور تخریب شد!"),
        ("🌊 سیل مرگبار","budget",-60000,"سیل شهرهای ساحلی را غرق کرد!"),
        ("🔥 خشکسالی و آتش‌سوزی","budget",-50000,"آتش‌سوزی جنگل‌های کشور را نابود کرد!"),
        ("🌪️ طوفان دسته‌۵","budget",-70000,"طوفان ویرانگر به سواحل کوبید!"),
        ("☢️ حادثه هسته‌ای","budget",-200000,"نشت رادیواکتیو در نیروگاه!"),
        ("💻 حمله سایبری گسترده","budget",-90000,"زیرساخت دیجیتال فلج شد!"),
        ("✊ کودتای نظامی","budget",-150000,"ارتش قدرت را به دست گرفت!"),
        ("📉 بحران اقتصادی","budget",-120000,"بورس سقوط کرد!"),
        ("🦠 اپیدمی","budget",-100000,"بیماری واگیردار شیوع یافت!"),
        ("🏅 کشف ذخایر نفت","budget",200000,"اکتشاف نفت در سرزمین شما!"),
        ("⛏️ کشف معدن طلا","budget",150000,"معادن طلا در کوهستان کشف شد!"),
        ("📈 رونق اقتصادی","budget",100000,"صادرات رکورد زد!"),
        ("🤝 کمک بین‌المللی","budget",120000,"کمک مالی از متحدان دریافت شد!"),
        ("🚀 پیشرفت فناوری","budget",180000,"اختراع انقلابی در کشور شما!"),
        ("🏆 جام جهانی","budget",80000,"میزبانی جام جهانی درآمد توریسم را انفجار داد!"),
        ("🛢️ بحران نفتی جهانی","oil_price",30,"قیمت نفت جهش کرد!"),
        ("📉 سقوط قیمت نفت","oil_price",-25,"عرضه بیش از تقاضا!"),
        ("⚡ انقلاب انرژی","budget",90000,"انرژی خورشیدی هزینه‌ها را کاهش داد!"),
        ("🎖️ قهرمانی ورزشی","budget",50000,"مدال‌های طلا پرستیژ ملی را بالا برد!"),
        ("🌱 بحران غذایی","budget",-80000,"خشکسالی محصولات کشاورزی را نابود کرد!"),
    ]
    ev_name, ev_type, ev_val, ev_desc = random.choice(events)
    if ev_type == "budget":
        p["budget"] = max(0, p.get("budget",0) + ev_val)
        db["players"][uid] = p
        sign = "+" if ev_val > 0 else ""
        msg = f"📍 کشور: {c['name']}\n💬 {ev_desc}\n{'💰' if ev_val>0 else '💸'} {sign}${abs(ev_val):,}"
    elif ev_type == "oil_price":
        new_p = max(20, db.get("market",{}).get("oil",80) + ev_val)
        db.setdefault("market",{})["oil"] = new_p
        msg = f"📍 تاثیر جهانی\n💬 {ev_desc}\n🛢️ قیمت جدید نفت: ${new_p}/بشکه"
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
        "─── تجهیزات ───\n"
        "/adm addequip <uid> <equip_id> - اضافه کردن تجهیز به بازیکن\n"
        "   مثال: /adm addequip 123456 abrams\n"
        "/adm removeequip <uid> <equip_id> - حذف تجهیز از بازیکن\n"
        "   مثال: /adm removeequip 123456 atom\n"
        "/adm clearequip <uid> - پاک کردن همه تجهیزات\n"
        "/adm listequip <uid> - لیست تجهیزات بازیکن\n"
        "   مثال: /adm listequip 123456789\n"
        "/adm startbudget <مقدار> - بودجه شروع بازیکنان جدید\n"
        "   مثال: /adm startbudget 300000\n\n"
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
    elif cmd == "startbudget" and len(args) >= 2:
        try:
            amt = int(args[1])
            GAME_SETTINGS["start_budget"] = amt
            save_db(db)
            await update.message.reply_text(f"✅ بودجه شروع: ${amt:,}")
        except: await update.message.reply_text("❌ /adm startbudget 300000")

    elif cmd == "addequip" and len(args) >= 3:
        tuid = args[1]; eid = args[2]
        p = db["players"].get(tuid)
        if not p:
            await update.message.reply_text("❌ بازیکن پیدا نشد!")
            return
        item = next((it for cat in EQUIP.values() for it in cat if it["id"] == eid), None)
        if not item:
            await update.message.reply_text(f"❌ تجهیز '{eid}' پیدا نشد!\nID های معتبر: f16, f35, f22, abrams, t90, atom, cruise, s400, ...")
            return
        p.setdefault("equipment", []).append(item)
        db["players"][tuid] = p; save_db(db)
        c = get_country(p.get("country_id",""))
        try: await context.bot.send_message(int(tuid), f"🎁 *ادمین {item['name']} به شما اضافه کرد!*", parse_mode="Markdown")
        except: pass
        try: await context.bot.send_message(CHANNEL_ID, f"👑 *ادمین {item['name']} به {c['name'] if c else tuid} داد*", parse_mode="Markdown")
        except: pass
        await update.message.reply_text(f"✅ {item['name']} به {c['name'] if c else tuid} اضافه شد!")

    elif cmd == "removeequip" and len(args) >= 3:
        tuid = args[1]; eid = args[2]
        p = db["players"].get(tuid)
        if not p:
            await update.message.reply_text("❌ بازیکن پیدا نشد!")
            return
        eq = p.get("equipment", [])
        found = next((e for e in eq if e["id"] == eid), None)
        if not found:
            await update.message.reply_text(f"❌ بازیکن این تجهیز رو نداره!")
            return
        eq.remove(found)
        p["equipment"] = eq
        db["players"][tuid] = p; save_db(db)
        c = get_country(p.get("country_id",""))
        try: await context.bot.send_message(int(tuid), f"⚠️ *ادمین {found['name']} از شما گرفت!*", parse_mode="Markdown")
        except: pass
        await update.message.reply_text(f"✅ {found['name']} از {c['name'] if c else tuid} حذف شد!")

    elif cmd == "clearequip" and len(args) >= 2:
        tuid = args[1]
        p = db["players"].get(tuid)
        if not p:
            await update.message.reply_text("❌ بازیکن پیدا نشد!")
            return
        count = len(p.get("equipment", []))
        p["equipment"] = []
        db["players"][tuid] = p; save_db(db)
        c = get_country(p.get("country_id",""))
        await update.message.reply_text(f"✅ {count} تجهیز از {c['name'] if c else tuid} پاک شد!")

    elif cmd == "listequip" and len(args) >= 2:
        tuid = args[1]
        p = db["players"].get(tuid)
        if not p:
            await update.message.reply_text("❌ بازیکن پیدا نشد!")
            return
        eq = p.get("equipment", [])
        c = get_country(p.get("country_id",""))
        if not eq:
            await update.message.reply_text(f"{c['name'] if c else tuid} هیچ تجهیزی ندارد!")
            return
        txt = f"📋 *تجهیزات {c['name'] if c else tuid}:*\n"
        for e in eq:
            txt += f"• `{e['id']}` - {e['name']}\n"
        await update.message.reply_text(txt, parse_mode="Markdown")

    elif cmd == "give" and len(args) >= 3:
        tuid = args[1]; p = db["players"].get(tuid)
        if p:
            try:
                amt = int(args[2])
                p["budget"] = p.get("budget",0)+amt
                db["players"][tuid] = p; save_db(db)
                c = get_country(p.get("country_id",""))
                await update.message.reply_text(f"✅ ${amt:,} به {c['name'] if c else tuid} داده شد")
                try: await context.bot.send_message(int(tuid), f"🎁 ادمین ${amt:,} به شما هدیه داد!")
                except: pass
            except: await update.message.reply_text("❌ /adm give uid 50000")
        else: await update.message.reply_text("❌ پیدا نشد!")

    elif cmd == "event":
        players = [(k,v) for k,v in db["players"].items() if not v.get("banned")]
        if players:
            uid, p = random.choice(players)
            c = get_country(p.get("country_id",""))
            ev_name, ev_type, ev_val, ev_desc = random.choice(RANDOM_EVENTS)
            if ev_type == "budget":
                p["budget"] = max(0, p.get("budget",0)+ev_val)
                db["players"][uid] = p; save_db(db)
            msg = f"🌍 *رویداد جهانی: {ev_name}*\n📍 {c['name'] if c else '?'}\n{ev_desc}"
            try: await context.bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
            except: pass
            await update.message.reply_text(f"✅ رویداد اجرا شد:\n{msg}", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ بازیکنی نیست!")

    else:
        await update.message.reply_text("❌ دستور نامعتبر! /adm برای راهنما")


# ── معامله پیشنهادی (fix کامل) ──
async def trade_offer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p: return
    others = {k:v for k,v in db["players"].items() if k!=uid and not v.get("banned")}
    if not others:
        await q.edit_message_text("هیچ بازیکنی نیست!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="trade_menu")]])); return
    kb = []
    for k,v in others.items():
        c = get_country(v.get("country_id",""))
        if c: kb.append([InlineKeyboardButton(f"🤝 پیشنهاد به {c['name']}",callback_data=f"offer_to_{k}")])
    kb.append([InlineKeyboardButton("🔙",callback_data="trade_menu")])
    await q.edit_message_text("*پیشنهاد معامله به:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def offer_to_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    tid = q.data.replace("offer_to_","")
    context.user_data["offer_target"] = tid
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p: return
    kb = [
        [InlineKeyboardButton("💵 پول میدم",callback_data="offer_type_money"),
         InlineKeyboardButton("🛢️ نفت میدم",callback_data="offer_type_oil")],
        [InlineKeyboardButton("🔙",callback_data="trade_offer_start")],
    ]
    tc = get_country(db["players"].get(tid,{}).get("country_id",""))
    await q.edit_message_text(
        f"معامله با {tc['name'] if tc else '?'}\n\nچی پیشنهاد میدی؟",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def offer_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    otype = q.data.replace("offer_type_","")
    context.user_data["offer_type"] = otype
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p: return
    if otype == "money":
        amounts = [10000,50000,100000,500000]
        kb = [[InlineKeyboardButton(f"💵 ${a:,}",callback_data=f"offer_give_{a}")] for a in amounts if p.get("budget",0)>=a]
    else:
        amounts = [1000,5000,10000,50000]
        kb = [[InlineKeyboardButton(f"🛢️ {a:,} بشکه",callback_data=f"offer_give_{a}")] for a in amounts if p.get("oil",0)>=a]
    kb.append([InlineKeyboardButton("🔙",callback_data="trade_offer_start")])
    await q.edit_message_text("چقدر میدی?", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def offer_give_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    amount = int(q.data.replace("offer_give_",""))
    context.user_data["offer_give"] = amount
    otype = context.user_data.get("offer_type","money")
    kb = [
        [InlineKeyboardButton("💵 پول میخوام",callback_data="offer_want_money"),
         InlineKeyboardButton("🛢️ نفت میخوام",callback_data="offer_want_oil")],
        [InlineKeyboardButton("🔙",callback_data="trade_offer_start")],
    ]
    give_txt = f"${amount:,}" if otype=="money" else f"{amount:,} بشکه نفت"
    await q.edit_message_text(f"تو {give_txt} میدی\nدر عوض چی میخوای?", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def offer_want_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    wtype = q.data.replace("offer_want_","")
    context.user_data["offer_want"] = wtype
    amounts = [10000,50000,100000,500000] if wtype=="money" else [1000,5000,10000,50000]
    kb = [[InlineKeyboardButton(f"{'💵 $' if wtype=='money' else '🛢️ '}{a:,}",callback_data=f"offer_want_amt_{a}")] for a in amounts]
    kb.append([InlineKeyboardButton("🔙",callback_data="trade_offer_start")])
    await q.edit_message_text("چقدر میخوای?", reply_markup=InlineKeyboardMarkup(kb))

async def offer_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    want_amt = int(q.data.replace("offer_want_amt_",""))
    db = load_db()
    uid = str(update.effective_user.id)
    tid = context.user_data.get("offer_target")
    otype = context.user_data.get("offer_type","money")
    give_amt = context.user_data.get("offer_give",0)
    wtype = context.user_data.get("offer_want","money")

    p = db["players"].get(uid)
    tp = db["players"].get(tid)
    if not p or not tp:
        await q.edit_message_text("❌ خطا!"); return

    c = get_country(p.get("country_id",""))
    tc = get_country(tp.get("country_id",""))

    # ذخیره پیشنهاد
    offer_id = f"offer_{uid}_{int(datetime.now().timestamp())}"
    db.setdefault("trade_offers",[]).append({
        "id": offer_id, "from": uid, "to": tid,
        "give_type": otype, "give_amt": give_amt,
        "want_type": wtype, "want_amt": want_amt,
        "status": "pending", "date": datetime.now().isoformat()
    })
    save_db(db)

    give_txt = f"${give_amt:,}" if otype=="money" else f"{give_amt:,} بشکه نفت"
    want_txt = f"${want_amt:,}" if wtype=="money" else f"{want_amt:,} بشکه نفت"

    try:
        kb = [[InlineKeyboardButton("✅ قبول",callback_data=f"accept_offer_{offer_id}"),
               InlineKeyboardButton("❌ رد",callback_data=f"reject_offer_{offer_id}")]]
        await context.bot.send_message(int(tid),
            f"🤝 *پیشنهاد معامله از {c['name'] if c else '?'}*\n\n"
            f"میده: {give_txt}\n"
            f"میخواد: {want_txt}",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    except Exception as e:
        logger.error(f"offer send err:{e}")

    await q.edit_message_text(f"✅ پیشنهاد ارسال شد!\n{give_txt} در برابر {want_txt}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="trade_menu")]]))

async def accept_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    offer_id = q.data.replace("accept_offer_","")
    db = load_db()
    uid = str(update.effective_user.id)

    offer = next((o for o in db.get("trade_offers",[]) if o["id"]==offer_id), None)
    if not offer or offer["status"]!="pending":
        await q.edit_message_text("❌ این پیشنهاد دیگه معتبر نیست!"); return

    from_uid = offer["from"]
    fp = db["players"].get(from_uid)
    tp = db["players"].get(uid)
    if not fp or not tp:
        await q.edit_message_text("❌ خطا!"); return

    # اجرای معامله
    ok = True
    if offer["give_type"]=="money":
        if fp.get("budget",0) < offer["give_amt"]: ok=False
        else:
            fp["budget"] = fp.get("budget",0) - offer["give_amt"]
            tp["budget"] = tp.get("budget",0) + offer["give_amt"]
    else:
        if fp.get("oil",0) < offer["give_amt"]: ok=False
        else:
            fp["oil"] = fp.get("oil",0) - offer["give_amt"]
            tp["oil"] = tp.get("oil",0) + offer["give_amt"]

    if ok:
        if offer["want_type"]=="money":
            if tp.get("budget",0) < offer["want_amt"]: ok=False
            else:
                tp["budget"] = tp.get("budget",0) - offer["want_amt"]
                fp["budget"] = fp.get("budget",0) + offer["want_amt"]
        else:
            if tp.get("oil",0) < offer["want_amt"]: ok=False
            else:
                tp["oil"] = tp.get("oil",0) - offer["want_amt"]
                fp["oil"] = fp.get("oil",0) + offer["want_amt"]

    if not ok:
        await q.edit_message_text("❌ معامله انجام نشد - موجودی کافی نیست!"); return

    offer["status"] = "done"
    db["players"][from_uid] = fp
    db["players"][uid] = tp
    db["trades"].append({**offer, "completed": datetime.now().isoformat()})
    save_db(db)

    fc = get_country(fp.get("country_id",""))
    tc = get_country(tp.get("country_id",""))
    give_txt = f"${offer['give_amt']:,}" if offer["give_type"]=="money" else f"{offer['give_amt']:,} بشکه"
    want_txt = f"${offer['want_amt']:,}" if offer["want_type"]=="money" else f"{offer['want_amt']:,} بشکه"

    try:
        await context.bot.send_message(int(from_uid),
            f"✅ *معامله انجام شد!*\n{tc['name'] if tc else '?'} قبول کرد!\n{give_txt} دادی - {want_txt} گرفتی",
            parse_mode="Markdown")
        await context.bot.send_message(CHANNEL_ID,
            f"🤝 *معامله*\n{fc['name'] if fc else '?'} و {tc['name'] if tc else '?'} معامله کردند!",
            parse_mode="Markdown")
    except: pass

    await q.edit_message_text(f"✅ *معامله انجام شد!*\n{give_txt} گرفتی - {want_txt} دادی",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))

async def reject_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    offer_id = q.data.replace("reject_offer_","")
    db = load_db()
    offer = next((o for o in db.get("trade_offers",[]) if o["id"]==offer_id), None)
    if offer: offer["status"] = "rejected"
    save_db(db)
    from_uid = offer["from"] if offer else None
    if from_uid:
        try: await context.bot.send_message(int(from_uid), "❌ پیشنهاد معامله رد شد!")
        except: pass
    await q.edit_message_text("❌ پیشنهاد رد شد.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))

# ── بیانیه اتحاد ──
async def alliance_decl_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    # پیدا کردن اتحاد
    my_alliance = None
    for aid, al in db.get("alliances",{}).items():
        if al.get("leader") == uid:
            my_alliance = al; break
    if not my_alliance:
        await q.answer("فقط رهبر اتحاد میتونه بیانیه مشترک بده!", show_alert=True); return
    await q.edit_message_text(
        f"📜 *بیانیه مشترک اتحاد {my_alliance.get('name','')}*\n\n"
        "عکس بفرست + متن بیانیه در کپشن\n/cancel لغو")
    context.user_data["alliance_decl"] = True
    return W_ALLIANCE_DECL

async def alliance_decl_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    uid = str(update.effective_user.id)
    if not update.message.photo:
        await update.message.reply_text("❌ باید عکس بفرستی!"); return W_ALLIANCE_DECL
    caption = update.message.caption or ""
    if len(caption.strip()) < 10:
        await update.message.reply_text("❌ متن کوتاهه!"); return W_ALLIANCE_DECL

    # پیدا کردن اتحاد
    my_alliance = None
    for aid, al in db.get("alliances",{}).items():
        if al.get("leader") == uid:
            my_alliance = al; break
    if not my_alliance:
        return ConversationHandler.END

    await update.message.reply_text("⏳ بررسی...")
    p = db["players"].get(uid,{})
    c = get_country(p.get("country_id",""))
    r = await ai_decl(c["name"] if c else "اتحاد", caption)

    if r["approved"]:
        now = datetime.now()
        members_txt = ""
        for mid in [my_alliance["leader"]] + my_alliance.get("members",[]):
            mp = db["players"].get(mid,{})
            mc = get_country(mp.get("country_id",""))
            if mc: members_txt += f"• {mc['name']}\n"

        formatted = (
            f"🤝 *بیانیه مشترک اتحاد {my_alliance.get('name','')}*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🗓 {now.year}/{now.month}/{now.day}\n"
            f"اعضا:\n{members_txt}\n"
            f"{r['edited']}\n\n"
            f"📡 {CHANNEL_LINK}"
        )
        try:
            await context.bot.send_photo(CHANNEL_ID, photo=update.message.photo[-1].file_id, caption=formatted, parse_mode="Markdown")
            await update.message.reply_text("✅ بیانیه مشترک منتشر شد!")
        except Exception as e:
            await update.message.reply_text(f"✅ تایید شد - خطای کانال: {e}")
    else:
        await update.message.reply_text(f"❌ رد شد: {r['reason']}")
    await update.message.reply_text(".", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))
    return ConversationHandler.END

# ── job های زمان‌بندی ──
async def job_news(context):
    db = load_db()
    news = await ai_news(db)
    try: await context.bot.send_message(CHANNEL_ID, news, parse_mode="Markdown")
    except Exception as e: logger.error(f"job_news:{e}")


async def job_event(context):
    db = load_db()
    players = [(k,v) for k,v in db["players"].items() if not v.get("banned")]
    if not players: return
    uid, p = random.choice(players)
    c = get_country(p.get("country_id",""))
    if not c: return
    ev_name, ev_type, ev_val, ev_desc = random.choice(RANDOM_EVENTS)
    emojis = {"زلزله":"🌍","سیل":"🌊","آتش":"🔥","طوفان":"🌪️","هسته":"☢️","سایبری":"💻","کودتا":"✊","اقتصادی":"📉","اپیدمی":"🦠","غذایی":"🌱","انفجار":"💥","نفت":"🏅","طلا":"⛏️","رونق":"📈","کمک":"🤝","فناوری":"🚀","جام":"🏆","انرژی":"⚡","الماس":"💎","نفتی":"🛢️","سقوط":"📉","دارو":"🔬","کشتیرانی":"🛳️","سرمایه":"💰"}
    emoji = next((v for k,v in emojis.items() if k in ev_name), "🌐")
    if ev_type=="budget":
        p["budget"] = max(0, p.get("budget",0)+ev_val)
        db["players"][uid] = p
        sign = "+" if ev_val>0 else ""
        msg = f"{emoji} *رویداد: {ev_name}*\n📍 {c['name']}\n💬 {ev_desc}\n{'💰' if ev_val>0 else '💸'} {sign}${abs(ev_val):,}"
    elif ev_type=="oil_price":
        new_p = max(20, db.get("market",{}).get("oil",80)+ev_val)
        db.setdefault("market",{})["oil"] = new_p
        msg = f"{emoji} *رویداد جهانی: {ev_name}*\n💬 {ev_desc}\n🛢️ قیمت نفت: ${new_p}/بشکه"
    else:
        msg = f"{emoji} *رویداد: {ev_name}*\n📍 {c['name']}\n💬 {ev_desc}"
    db.setdefault("events",[]).append({"name":ev_name,"country":c["name"],"date":datetime.now().isoformat()})
    save_db(db)
    try:
        await context.bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
        await context.bot.send_message(int(uid), f"🌍 *رویداد در کشور شما!*\n{msg}", parse_mode="Markdown")
    except Exception as e: logger.error(f"job_event:{e}")

# ── adminhelp ──


async def give_money_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    others = {k:v for k,v in db["players"].items() if k!=uid}
    kb = []
    for k,v in others.items():
        c = get_country(v.get("country_id",""))
        if c: kb.append([InlineKeyboardButton(f"💵 به {c['name']}",callback_data=f"give_m_{k}")])
    kb.append([InlineKeyboardButton("🔙",callback_data="trade_menu")])
    await q.edit_message_text("💵 *انتقال پول به:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def give_money_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    tid = q.data.replace("give_m_","")
    context.user_data["give_money_to"] = tid
    db = load_db()
    tp = db["players"].get(tid,{})
    tc = get_country(tp.get("country_id",""))
    await q.edit_message_text(f"💵 چقدر به {tc['name'] if tc else '?'} انتقال بدم?\n(عدد بنویس)\n/cancel لغو")
    return W_GIVE_MONEY

async def give_money_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    uid = str(update.effective_user.id)
    tid = context.user_data.get("give_money_to")
    try: amount = int(update.message.text.replace(",","").replace("$",""))
    except:
        await update.message.reply_text("❌ عدد صحیح وارد کن!"); return W_GIVE_MONEY
    p = db["players"].get(uid)
    tp = db["players"].get(tid)
    if not p or not tp: return ConversationHandler.END
    if p["budget"] < amount:
        await update.message.reply_text(f"❌ بودجه کم! ${p['budget']:,}"); return W_GIVE_MONEY
    c = get_country(p.get("country_id",""))
    tc = get_country(tp.get("country_id",""))
    p["budget"] -= amount
    tp["budget"] = tp.get("budget",0) + amount
    db["players"][uid] = p
    db["players"][tid] = tp
    db["trades"].append({"type":"money","from":uid,"to":tid,"amount":amount,"date":datetime.now().isoformat()})
    save_db(db)
    try: await context.bot.send_message(int(tid),f"💵 {c['name'] if c else '?'} ${amount:,} به شما انتقال داد!")
    except: pass
    await update.message.reply_text(f"✅ ${amount:,} به {tc['name'] if tc else '?'} انتقال یافت!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))
    return ConversationHandler.END

async def sell_oil_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    p = db["players"].get(uid)
    if not p: return
    oil_price = db.get("market",{}).get("oil",80)
    amounts = [1000,5000,10000,50000,100000]
    kb = []
    for amt in amounts:
        if p.get("oil",0) >= amt:
            income = amt * oil_price
            kb.append([InlineKeyboardButton(f"🛢️ {amt:,} → ${income:,}",callback_data=f"sell_oil_{amt}")])
    kb.append([InlineKeyboardButton("🔙",callback_data="trade_menu")])
    await q.edit_message_text(
        f"🛢️ *فروش نفت*\nقیمت: ${oil_price}/بشکه\nموجودی: {p.get('oil',0):,}",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))


async def al_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    for al in db.get("alliances",{}).values():
        if uid==al.get("leader") or uid in al.get("members",[]):
            await q.answer("قبلاً در اتحاد هستی!",show_alert=True); return
    aid = f"al_{uid}_{int(datetime.now().timestamp())}"
    p = db["players"].get(uid,{})
    c = get_country(p.get("country_id",""))
    db.setdefault("alliances",{})[aid] = {
        "leader":uid,"members":[],"name":f"اتحاد {c['name'] if c else '?'}",
        "slogan":"با هم قوی‌تریم!","created":datetime.now().isoformat(),"requests":[]
    }
    save_db(db)
    await q.edit_message_text("✅ اتحاد ساخته شد!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="alliance_menu")]]))
    try: await context.bot.send_message(CHANNEL_ID,f"🤝 اتحاد جدید توسط {c['name'] if c else '?'} ساخته شد!")
    except: pass

async def al_join_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    uid = str(update.effective_user.id)
    alliances = db.get("alliances",{})
    kb = []
    for aid,al in alliances.items():
        cnt = len(al.get("members",[]))+1
        if cnt<4 and uid!=al.get("leader") and uid not in al.get("members",[]):
            kb.append([InlineKeyboardButton(f"🔍 {al['name']} ({cnt}/4)",callback_data=f"al_request_{aid}")])
    kb.append([InlineKeyboardButton("🔙",callback_data="alliance_menu")])
    await q.edit_message_text("🔍 *اتحادهای قابل پیوستن:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def al_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    aid = q.data.replace("al_request_","")
    db = load_db()
    uid = str(update.effective_user.id)
    al = db.get("alliances",{}).get(aid)
    if not al: return
    al.setdefault("requests",[]).append(uid)
    save_db(db)
    p = db["players"].get(uid,{})
    c = get_country(p.get("country_id",""))
    try: await context.bot.send_message(int(al["leader"]),f"📩 {c['name'] if c else '?'} درخواست پیوستن داد!")
    except: pass
    await q.edit_message_text("✅ درخواست ارسال شد!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="alliance_menu")]]))

async def al_requests_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    aid = q.data.replace("al_requests_","")
    db = load_db()
    uid = str(update.effective_user.id)
    al = db.get("alliances",{}).get(aid)
    if not al or al.get("leader")!=uid: return
    requests = al.get("requests",[])
    if not requests:
        await q.edit_message_text("📭 درخواستی نیست!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="alliance_menu")]])); return
    kb = []
    for req_uid in requests:
        rp = db["players"].get(req_uid,{})
        rc = get_country(rp.get("country_id",""))
        kb.append([InlineKeyboardButton(f"✅ {rc['name'] if rc else '?'}",callback_data=f"al_accept_{aid}_{req_uid}"),
                   InlineKeyboardButton("❌ رد",callback_data=f"al_reject_{aid}_{req_uid}")])
    kb.append([InlineKeyboardButton("🔙",callback_data="alliance_menu")])
    await q.edit_message_text("📋 *درخواست‌ها:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def al_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    parts = q.data.replace("al_accept_","").split("_")
    # aid ممکنه چند _ داشته باشه
    req_uid = parts[-1]
    aid = "_".join(parts[:-1])
    db = load_db()
    al = db.get("alliances",{}).get(aid)
    if not al: return
    if len(al.get("members",[]))>=3:
        await q.answer("❌ اتحاد پر!",show_alert=True); return
    al.setdefault("members",[]).append(req_uid)
    if req_uid in al.get("requests",[]): al["requests"].remove(req_uid)
    save_db(db)
    rp = db["players"].get(req_uid,{})
    rc = get_country(rp.get("country_id",""))
    try: await context.bot.send_message(int(req_uid),f"✅ به اتحاد {al['name']} پیوستی!")
    except: pass
    try: await context.bot.send_message(CHANNEL_ID,f"🤝 {rc['name'] if rc else '?'} به {al['name']} پیوست!")
    except: pass
    await q.edit_message_text("✅ پذیرفته شد!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="alliance_menu")]]))

async def al_dissolve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    aid = q.data.replace("al_dissolve_","")
    db = load_db()
    uid = str(update.effective_user.id)
    al = db.get("alliances",{}).get(aid)
    if not al or al.get("leader")!=uid: return
    for mid in al.get("members",[]):
        try: await context.bot.send_message(int(mid),f"⚠️ اتحاد {al['name']} منحل شد!")
        except: pass
    del db["alliances"][aid]
    save_db(db)
    await q.edit_message_text("✅ اتحاد منحل شد.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="back")]]))

async def adm_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id!=ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    await q.answer()
    db = load_db()
    logs = db.get("admin_log",[])[-15:]
    txt = "📋 *لاگ ادمین*\n━━━━━━━━━━━━━━━\n"
    for l in reversed(logs):
        txt += f"• {l.get('date','')[:16]}: {l.get('action','')}\n"
    await q.edit_message_text(txt or "هیچ لاگی نیست", parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙",callback_data="admin")]]))

async def adm_oil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id!=ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    await q.answer()
    db = load_db()
    oil_price = db.get("market",{}).get("oil",80)
    kb = []
    for price in [40,60,80,100,120,150,200]:
        kb.append([InlineKeyboardButton(f"{'✅ ' if oil_price==price else ''}${price}",callback_data=f"set_oil_{price}")])
    kb.append([InlineKeyboardButton("🔙",callback_data="admin")])
    await q.edit_message_text(f"🛢️ قیمت نفت فعلی: ${oil_price}",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def set_oil_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id!=ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    price = int(q.data.replace("set_oil_",""))
    db = load_db()
    db.setdefault("market",{})["oil"] = price
    save_db(db)
    await q.answer(f"✅ ${price}")
    try: await context.bot.send_message(CHANNEL_ID,f"🛢️ قیمت نفت: ${price}/بشکه")
    except: pass
    await adm_oil(update, context)

async def adm_player_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id!=ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    await q.answer()
    db = load_db()
    kb = []
    for uid,p in db["players"].items():
        c = get_country(p.get("country_id",""))
        ban = "🚫" if p.get("banned") else ""
        kb.append([InlineKeyboardButton(f"{ban}{c['name'] if c else '?'} ${p.get('budget',0):,}",callback_data=f"adm_p_{uid}")])
    kb.append([InlineKeyboardButton("🔙",callback_data="admin")])
    await q.edit_message_text("👤 *بازیکنان:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def adm_player_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id!=ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    await q.answer()
    tuid = q.data.replace("adm_p_","")
    db = load_db()
    p = db["players"].get(tuid)
    if not p: return
    c = get_country(p.get("country_id",""))
    oil_price = db.get("market",{}).get("oil",80)
    total = p.get("budget",0)+p.get("oil",0)*oil_price
    kb = [
        [InlineKeyboardButton("🚫 بن/آنبن",callback_data=f"adm_ban_{tuid}"),
         InlineKeyboardButton("🗑️ حذف",callback_data=f"adm_kick_{tuid}")],
        [InlineKeyboardButton("🔙",callback_data="adm_player_list")],
    ]
    await q.edit_message_text(
        f"👤 {c['name'] if c else '?'}\n"
        f"🆔 {tuid}\n"
        f"💰 ${p.get('budget',0):,}\n"
        f"🛢️ {p.get('oil',0):,}\n"
        f"💎 ${total:,}\n"
        f"{'🚫 بن' if p.get('banned') else '✅ فعال'}",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def adm_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id!=ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    tuid = q.data.replace("adm_ban_","")
    db = load_db()
    p = db["players"].get(tuid)
    if not p: return
    p["banned"] = not p.get("banned",False)
    db["players"][tuid] = p
    save_db(db)
    c = get_country(p.get("country_id",""))
    st = "🚫 بن" if p["banned"] else "✅ آنبن"
    await q.answer(f"{st} شد!")
    try: await context.bot.send_message(CHANNEL_ID,f"👑 ادمین: {c['name'] if c else '?'} {st} شد.")
    except: pass
    await adm_player_detail(update, context)

async def adm_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id!=ADMIN_ID:
        await q.answer("❌",show_alert=True); return
    tuid = q.data.replace("adm_kick_","")
    db = load_db()
    p = db["players"].get(tuid)
    if p:
        c = get_country(p.get("country_id",""))
        del db["players"][tuid]
        save_db(db)
        await q.answer("✅ حذف شد!")
        try: await context.bot.send_message(int(tuid),"⚠️ کشور شما ریست شد.")
        except: pass
    await adm_player_list(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ لغو شد.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پنل",callback_data="back")]]))
    return ConversationHandler.END


async def adm_tension_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("❌", show_alert=True); return
    await q.answer()
    db = load_db()
    current = db.get("world_tension", 30)
    kb = [[InlineKeyboardButton(f"⚡ {t}٪", callback_data=f"set_tension_{t}")] for t in [0,10,20,30,50,70,90,100]]
    kb.append([InlineKeyboardButton("🔙", callback_data="admin")])
    await q.edit_message_text(f"⚡ تنش فعلی: {current}٪\n\nتنش جدید:", reply_markup=InlineKeyboardMarkup(kb))

async def set_tension(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("❌", show_alert=True); return
    await q.answer()
    t = int(q.data.replace("set_tension_",""))
    db = load_db()
    db["world_tension"] = t
    save_db(db)
    try: await context.bot.send_message(CHANNEL_ID, f"⚡ *تنش جهانی: {t}٪*", parse_mode="Markdown")
    except: pass
    await q.edit_message_text(f"✅ تنش جهانی: {t}٪",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin")]]))

async def ai_check_scenario(scenario: str, equip_list: list) -> dict:
    """چک سناریو با AI"""
    client = get_ai()
    eq_ids = {e["id"] for e in equip_list}
    missing = check_scenario(scenario, list(eq_ids))
    if missing:
        eq_names = [get_eq_name(m) for m in missing]
        return {"valid": False, "reason": f"از تجهیزاتی که نداری استفاده کردی: {', '.join(eq_names)}"}
    if not client:
        return {"valid": True, "reason": ""}
    try:
        eq_names = [e['name'] for e in equip_list]
        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=200,
            system='بررسی‌کننده سناریو نظامی. اگه سناریو منطقی و با تجهیزات لیست باشه valid:true. فقط JSON: {"valid":true,"reason":""}',
            messages=[{"role":"user","content":f"تجهیزات:\n{chr(10).join(eq_names)}\n\nسناریو:\n{scenario}"}])
        import json as _j
        return _j.loads(r.content[0].text.strip().replace("```json","").replace("```",""))
    except:
        return {"valid": True, "reason": ""}

async def ai_spy_operation(spy_c, target_c, op_type, spy_p, target_p) -> dict:
    """تحلیل عملیات جاسوسی با AI"""
    client = get_ai()
    intel_eq = [e for e in spy_p.get('equipment',[]) if e.get('type')=='intel']
    intel_power = sum(e.get('power',0) for e in intel_eq)
    def_eq = [e for e in target_p.get('equipment',[]) if e.get('type') in ['defense','intel']]
    def_power = sum(e.get('power',0) for e in def_eq)
    
    ops = {
        "intel": ("سرقت اطلاعات نظامی محرمانه","spy_intel"),
        "sabotage": ("خرابکاری در زیرساخت","saboteur"),
        "assassinate": ("ترور رهبر/ژنرال","assassin"),
        "sleeper": ("کاشت عامل نفوذی","sleeper"),
    }
    op_desc, req_eq = ops.get(op_type, ("عملیات مخفی","spy_cyber"))
    
    # محاسبه احتمال موفقیت
    success_chance = min(90, max(10, 50 + (intel_power - def_power) // 10))
    success = random.randint(1,100) <= success_chance
    agent_captured = not success and random.randint(1,100) <= 30
    
    damages = {"intel":0,"sabotage":random.randint(30000,100000),"assassinate":0,"sleeper":0}
    damage = damages.get(op_type,0) if success else 0
    
    if not client:
        story = f"عوامل {spy_c['name']} وارد عمل شدند."
        info = "اطلاعات محدود" if success else "عملیات لو رفت"
        return {"success":success,"agent_captured":agent_captured,"damage":damage,"story":story,"info_gained":info}
    
    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=400,
            system='تحلیلگر اطلاعات WW26. فقط JSON: {"success":bool,"agent_captured":bool,"damage":int,"story":"3جمله فارسی","info_gained":"1جمله"}',
            messages=[{"role":"user","content":f"جاسوس:{spy_c['name']} هدف:{target_c['name']} عملیات:{op_desc} قدرت جاسوس:{intel_power} دفاع هدف:{def_power} موفق:{success}"}])
        import json as _j
        return _j.loads(r.content[0].text.strip().replace("```json","").replace("```",""))
    except:
        return {"success":success,"agent_captured":agent_captured,"damage":damage,"story":f"عملیات {'موفق' if success else 'ناموفق'} بود.","info_gained":""}

async def ai_propaganda(spy_c, target_c, message) -> dict:
    """تحلیل کمپین پروپاگاندا"""
    client = get_ai()
    effectiveness = random.randint(20,90)
    success = effectiveness > 50
    backfire = random.randint(1,100) <= 15
    if not client:
        return {"success":success,"effectiveness":effectiveness,"backfire":backfire,"story":"کمپین اجرا شد."}
    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=300,
            system='تحلیلگر پروپاگاندا. JSON: {"success":bool,"effectiveness":int,"backfire":bool,"story":"2جمله فارسی"}',
            messages=[{"role":"user","content":f"از {spy_c['name']} علیه {target_c['name']}: {message}"}])
        import json as _j
        return _j.loads(r.content[0].text.strip().replace("```json","").replace("```",""))
    except:
        return {"success":success,"effectiveness":effectiveness,"backfire":backfire,"story":"کمپین اطلاعاتی اجرا شد."}

async def ai_random_event(p, c) -> dict:
    """رویداد تصادفی با AI"""
    client = get_ai()
    events_pool = [
        {"name":"زلزله","effect":"budget","value":-80000,"msg":"زلزله ویرانگر!"},
        {"name":"سیل","effect":"budget","value":-60000,"msg":"سیل مرگبار!"},
        {"name":"کشف نفت","effect":"budget_gain","value":150000,"msg":"ذخایر نفتی کشف شد!"},
        {"name":"رونق اقتصادی","effect":"budget_gain","value":100000,"msg":"اقتصاد رونق گرفت!"},
        {"name":"بحران نفتی","effect":"oil_price","value":25,"msg":"قیمت نفت جهش کرد!"},
        {"name":"سقوط نفت","effect":"oil_price","value":-20,"msg":"نفت ارزان شد!"},
        {"name":"حمله سایبری","effect":"budget","value":-90000,"msg":"زیرساخت دیجیتال آسیب دید!"},
        {"name":"کودتا","effect":"budget","value":-150000,"msg":"بی‌ثباتی سیاسی!"},
        {"name":"پیشرفت فناوری","effect":"budget_gain","value":180000,"msg":"اختراع انقلابی!"},
        {"name":"کمک بین‌المللی","effect":"budget_gain","value":120000,"msg":"کمک مالی دریافت شد!"},
    ]
    ev = random.choice(events_pool)
    ev["ai_story"] = ev["msg"]
    return ev

async def check_achievements(p, db, uid) -> list:
    """چک دستاوردها و برگشت لیست جدیدها"""
    earned = db.get('achievements',{}).get(uid,[])
    new_ones = []
    for ach_id, ach in ACHIEVEMENTS.items():
        if ach_id in earned:
            continue
        earned_it = False
        if ach_id == "first_buy" and len(p.get('equipment',[])) >= 1:
            earned_it = True
        elif ach_id == "rich" and p.get('budget',0) >= 1000000:
            earned_it = True
        elif ach_id == "warmonger" and p.get('wars_won',0) >= 5:
            earned_it = True
        elif ach_id == "peacemaker" and len(db.get('peace_treaties',{})) >= 1:
            earned_it = True
        elif ach_id == "nuclear" and any(e['id'] in ['atom','hydrogen','neutron'] for e in p.get('equipment',[])):
            earned_it = True
        elif ach_id == "spy_master" and len([s for s in db.get('spy_ops',[]) if s.get('spy_uid')==uid and s.get('success')]) >= 3:
            earned_it = True
        elif ach_id == "oil_baron" and p.get('oil',0) >= 50000:
            earned_it = True
        elif ach_id == "diplomat" and len([t for t in db.get('peace_treaties',{}).values() if uid in t.get('parties',[])]) >= 2:
            earned_it = True
        if earned_it:
            new_ones.append(ach_id)
            db.setdefault('achievements',{}).setdefault(uid,[]).append(ach_id)
            p['budget'] = p.get('budget',0) + ach.get('reward',0)
    return new_ones

def get_player_rank(db, uid) -> int:
    oil_price = db.get('market',{}).get('oil',80)
    scores = {k: v.get('budget',0)+v.get('oil',0)*oil_price for k,v in db['players'].items()}
    ranked = sorted(scores, key=scores.get, reverse=True)
    return ranked.index(uid)+1 if uid in ranked else len(ranked)+1

def calc_daily_income(p) -> int:
    return sum(e.get('daily',0) for e in p.get('equipment',[]) if e.get('type')=='economy')

def calc_daily_oil(p) -> int:
    return sum(e.get('oil_daily',0) for e in p.get('equipment',[]) if e.get('type')=='economy')

def calc_military_power(p) -> int:
    return sum(e.get('power',0) for e in p.get('equipment',[]) if e.get('type') in ['attack','ground','defense','intel'])

def ai_war_v4(ac, dc, ap, dp, scenario, db):
    return ai_war(ac, dc, ap, dp, scenario, db)

ACHIEVEMENTS = {
    "first_buy":   {"name":"🛒 اولین خرید",        "desc":"اولین تجهیز رو بخر",          "reward":10000},
    "rich":        {"name":"💰 میلیونر",             "desc":"یک میلیون دلار داشته باش",     "reward":50000},
    "warmonger":   {"name":"⚔️ جنگ‌طلب",            "desc":"۵ جنگ ببر",                    "reward":100000},
    "peacemaker":  {"name":"🕊️ صلح‌دوست",           "desc":"قرارداد صلح امضا کن",          "reward":30000},
    "nuclear":     {"name":"☢️ قدرت هسته‌ای",       "desc":"سلاح اتمی بخر",               "reward":200000},
    "spy_master":  {"name":"🕵️ استاد جاسوسی",      "desc":"۳ عملیات موفق جاسوسی",       "reward":80000},
    "oil_baron":   {"name":"🛢️ امپراتور نفت",       "desc":"۵۰,۰۰۰ بشکه نفت داشته باش",  "reward":75000},
    "diplomat":    {"name":"🤝 دیپلمات",             "desc":"۲ قرارداد صلح امضا کن",       "reward":40000},
}

RESEARCH_TREE = {
    "stealth": {"name":"🛩️ فناوری استلث","cost":200000,"effect":"جنگنده‌های شما ۳۰٪ کمتر دیده می‌شن","req":[]},
    "precision": {"name":"🎯 دقت موشکی","cost":150000,"effect":"دقت حملات موشکی ۴۰٪ بیشتر","req":["cruise"]},
    "cyber_war": {"name":"💻 جنگ سایبری","cost":250000,"effect":"توانایی هک زیرساخت","req":["hack"]},
    "nuclear_prog": {"name":"☢️ برنامه هسته‌ای","cost":500000,"effect":"امکان خرید بمب اتمی","req":["uranium_mine","enrichment"]},
    "hypersonic_rd": {"name":"⚡ تحقیق هایپرسونیک","cost":400000,"effect":"موشک‌های هایپرسونیک ۲۵٪ قوی‌تر","req":["hypersonic"]},
    "economy_boost": {"name":"📈 تحریک اقتصادی","cost":100000,"effect":"درآمد روزانه ۵۰٪ بیشتر","req":[]},
    "space_prog": {"name":"🚀 برنامه فضایی","cost":300000,"effect":"ماهواره جاسوسی رایگان","req":["tech_hub"]},
    "bioweapon": {"name":"🧫 تحقیق بیوشیمیایی","cost":350000,"effect":"سلاح بیولوژیک پنهان","req":["uranium_mine"]},
}


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_decl = ConversationHandler(
        entry_points=[CallbackQueryHandler(decl_start, pattern="^decl$")],
        states={W_DECL:[
            MessageHandler(filters.PHOTO, decl_recv_photo),
            MessageHandler(filters.TEXT & ~filters.COMMAND, decl_recv_text),
            CommandHandler("cancel", cancel),
        ]},
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )
    conv_war = ConversationHandler(
        entry_points=[CallbackQueryHandler(atk_target, pattern="^atk_")],
        states={W_WAR:[
            MessageHandler(filters.TEXT & ~filters.COMMAND, war_recv),
            CommandHandler("cancel", cancel),
        ]},
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )
    conv_give_money = ConversationHandler(
        entry_points=[CallbackQueryHandler(give_money_target, pattern="^give_m_")],
        states={W_GIVE_MONEY:[
            MessageHandler(filters.TEXT & ~filters.COMMAND, give_money_recv),
            CommandHandler("cancel", cancel),
        ]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    conv_alliance_decl = ConversationHandler(
        entry_points=[CallbackQueryHandler(alliance_decl_start, pattern="^alliance_decl$")],
        states={W_ALLIANCE_DECL:[
            MessageHandler(filters.PHOTO, alliance_decl_recv),
            CommandHandler("cancel", cancel),
        ]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adm", admin_cmd))
    app.add_handler(CommandHandler("adminhelp", adminhelp_cmd))
    app.add_handler(conv_decl)
    app.add_handler(conv_war)
    app.add_handler(conv_give_money)
    app.add_handler(conv_alliance_decl)

    app.add_handler(CallbackQueryHandler(back_handler, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(choose_country, pattern="^choose$"))
    app.add_handler(CallbackQueryHandler(join_country, pattern="^join_"))
    app.add_handler(CallbackQueryHandler(show_status, pattern="^status$"))
    app.add_handler(CallbackQueryHandler(equip_detail, pattern="^equip_detail$"))
    app.add_handler(CallbackQueryHandler(borders_menu, pattern="^borders$"))
    app.add_handler(CallbackQueryHandler(toggle_border, pattern="^border_"))
    app.add_handler(CallbackQueryHandler(show_ranking, pattern="^ranking$"))
    app.add_handler(CallbackQueryHandler(tutorial, pattern="^tutorial$"))
    app.add_handler(CallbackQueryHandler(ref_menu, pattern="^ref$"))
    app.add_handler(CallbackQueryHandler(quit_game, pattern="^quit$"))
    app.add_handler(CallbackQueryHandler(quit_confirm, pattern="^quit_confirm$"))

    app.add_handler(CallbackQueryHandler(shop_menu, pattern="^shop$"))
    app.add_handler(CallbackQueryHandler(shop_cat, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(buy, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(full_list, pattern="^fulllist$"))

    app.add_handler(CallbackQueryHandler(war_menu, pattern="^war$"))

    app.add_handler(CallbackQueryHandler(trade_menu, pattern="^trade_menu$"))
    app.add_handler(CallbackQueryHandler(sell_oil_menu, pattern="^sell_oil_menu$"))
    app.add_handler(CallbackQueryHandler(sell_oil, pattern=r"^sell_oil_\d+$"))
    app.add_handler(CallbackQueryHandler(give_money_menu, pattern="^give_money_menu$"))
    app.add_handler(CallbackQueryHandler(give_money_target, pattern="^give_m_"))
    app.add_handler(CallbackQueryHandler(trade_offer_start, pattern="^trade_offer_start$"))
    app.add_handler(CallbackQueryHandler(offer_to_target, pattern="^offer_to_"))
    app.add_handler(CallbackQueryHandler(offer_type, pattern="^offer_type_"))
    app.add_handler(CallbackQueryHandler(offer_give_amount, pattern="^offer_give_"))
    app.add_handler(CallbackQueryHandler(offer_want_type, pattern="^offer_want_(money|oil)$"))
    app.add_handler(CallbackQueryHandler(offer_confirm, pattern="^offer_want_amt_"))
    app.add_handler(CallbackQueryHandler(accept_offer, pattern="^accept_offer_"))
    app.add_handler(CallbackQueryHandler(reject_offer, pattern="^reject_offer_"))

    app.add_handler(CallbackQueryHandler(alliance_menu, pattern="^alliance_menu$"))
    app.add_handler(CallbackQueryHandler(al_create, pattern="^al_create$"))
    app.add_handler(CallbackQueryHandler(al_join_list, pattern="^al_join_list$"))
    app.add_handler(CallbackQueryHandler(al_request, pattern="^al_request_"))
    app.add_handler(CallbackQueryHandler(al_requests_menu, pattern="^al_requests_"))
    app.add_handler(CallbackQueryHandler(al_accept, pattern="^al_accept_"))
    app.add_handler(CallbackQueryHandler(al_dissolve, pattern="^al_dissolve_"))

    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin$"))
    app.add_handler(CallbackQueryHandler(adm_toggle, pattern="^adm_tog_"))
    app.add_handler(CallbackQueryHandler(adm_news, pattern="^adm_news$"))
    app.add_handler(CallbackQueryHandler(adm_income, pattern="^adm_income$"))
    app.add_handler(CallbackQueryHandler(adm_stats, pattern="^adm_stats$"))
    app.add_handler(CallbackQueryHandler(adm_log, pattern="^adm_log$"))
    app.add_handler(CallbackQueryHandler(adm_oil, pattern="^adm_oil$"))
    app.add_handler(CallbackQueryHandler(set_oil_price, pattern="^set_oil_"))
    app.add_handler(CallbackQueryHandler(adm_player_list, pattern="^adm_player_list$"))
    app.add_handler(CallbackQueryHandler(adm_player_detail, pattern="^adm_p_"))
    app.add_handler(CallbackQueryHandler(adm_ban, pattern="^adm_ban_"))
    app.add_handler(CallbackQueryHandler(adm_kick, pattern="^adm_kick_"))

    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), pattern="^(noop|taken|spy_history|prop_history|trade_history|trade_equip)$"))

    # ─── Handler های تکمیلی ───
    app.add_handler(CallbackQueryHandler(spy_menu,          pattern="^spy_menu$"))
    app.add_handler(CallbackQueryHandler(spy_op_start,      pattern="^spy_op_"))
    app.add_handler(CallbackQueryHandler(spy_execute,       pattern="^spy_target_"))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), pattern="^spy_history$"))
    app.add_handler(CallbackQueryHandler(diplomacy_menu,    pattern="^diplomacy$"))
    app.add_handler(CallbackQueryHandler(diplo_peace_start, pattern="^diplo_peace$"))
    app.add_handler(CallbackQueryHandler(peace_offer,       pattern="^peace_offer_"))
    app.add_handler(CallbackQueryHandler(peace_accept,      pattern="^peace_accept_"))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer("❌ رد شد.", show_alert=True), pattern="^peace_reject_"))
    app.add_handler(CallbackQueryHandler(diplo_sanction,    pattern="^diplo_sanction$"))
    app.add_handler(CallbackQueryHandler(sanction_apply,    pattern="^sanction_"))
    app.add_handler(CallbackQueryHandler(diplomacy_menu,    pattern="^diplo_nonaggression$"))
    app.add_handler(CallbackQueryHandler(diplomacy_menu,    pattern="^diplo_aid$"))
    app.add_handler(CallbackQueryHandler(diplomacy_menu,    pattern="^diplo_un$"))
    app.add_handler(CallbackQueryHandler(rd_menu,           pattern="^rd_menu$"))
    app.add_handler(CallbackQueryHandler(rd_start,          pattern="^rd_start_"))
    app.add_handler(CallbackQueryHandler(propaganda_menu,   pattern="^propaganda_menu$"))
    app.add_handler(CallbackQueryHandler(prop_start,        pattern="^prop_start$"))
    app.add_handler(CallbackQueryHandler(prop_execute,      pattern="^prop_target_"))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), pattern="^prop_history$"))
    app.add_handler(CallbackQueryHandler(show_achievements, pattern="^achievements$"))
    app.add_handler(CallbackQueryHandler(world_events_show, pattern="^world_events$"))
    app.add_handler(CallbackQueryHandler(trade_oil_sell,    pattern="^trade_oil_sell$"))
    app.add_handler(CallbackQueryHandler(give_money_menu,   pattern="^trade_money$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer("در حال توسعه!", show_alert=True), pattern="^trade_equip$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), pattern="^trade_history$"))
    app.add_handler(CallbackQueryHandler(adm_event,         pattern="^adm_event$"))
    app.add_handler(CallbackQueryHandler(adm_toggle,        pattern="^adm_toggle_"))
    app.add_handler(CallbackQueryHandler(adm_oil,           pattern="^adm_oil_price$"))
    app.add_handler(CallbackQueryHandler(adm_tension_menu,  pattern="^adm_tension$"))

    # ── زمان بندی با APScheduler ──
    scheduler = AsyncIOScheduler(timezone="Asia/Tehran")

    async def run_news():
        class Ctx: bot=app.bot
        await job_news(Ctx())
    async def run_income():
        class Ctx: bot=app.bot
        await job_income(Ctx())
    async def run_event():
        class Ctx: bot=app.bot
        await job_event(Ctx())

    scheduler.add_job(run_news, CronTrigger(hour=21, minute=0))
    scheduler.add_job(run_income, CronTrigger(hour=12, minute=0))
    # 5 بار رویداد در روز
    for h in [9,12,15,18,22]:
        scheduler.add_job(run_event, CronTrigger(hour=h, minute=0))

    app.add_handler(CallbackQueryHandler(set_tension, pattern="^set_tension_"))
    scheduler.start()
    logger.info("WW26 v5 FINAL started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
