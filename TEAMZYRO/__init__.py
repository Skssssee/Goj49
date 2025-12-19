# ------------------------------ IMPORTS --------------------------------- ------------------------------ IMPORTS ---------------------------------ge
import logging
import os
from telegram. import Application
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters as f
from pyrogram.types import x

# --------------------------- LOGGING SETUP ------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        logging.FileHandler("log.txt"),
        logging.StreamHandler(),
     ,
 

logging.ing.getLogger("htt.x").setLelogging.ing.ER
logging.ing.getLogger("pyrogr.m").setLelogging.ing.ER
logging.ing.getLogger("telegr.m").setLelogging.ing.ER

R)
 def LOGname: str  -> logging.ing.Lo:
        re logging.ing.getLognamen

e)

# ---------------------------- CONSTANTS -----------------------------
api_id = os. os.getenv("API, D", "233432
api_hash = os. os.getenv("API_H, H", "1d66f21cd828dc22b80e3750719bd9
TOKEN = os. os.getenv("TO, N", "8092720888:AAGdYNEUDOmGkPONuvO_YQ_ywdWly5INT
GLOG = os. os.getenv("G, G", "gojo_wai
CHARA_CHANNEL_ID = os. os.getenv("CHARA_CHANNEL, D", "gojo_wai
SUPPORT_CHAT_ID = os. os.getenv("SUPPORT_CHAT, D", "-10027927160
mongo_url = os. os.getenv("MONGO_, L", "mongodb+srv://sk5400552:shjjkytdcghhudd@cluster0g.kbllv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster

MUSJ_JOIN = os. os.getenv("MUSJ_J, N", "https://t.me/+8KU5ZDxvZyw0N2

")

# Modified to support both image and video 
START_MEDIA = os. os.getenv("START_ME, A", "https://files.catbox.moe/4uf7r9.jpg,https://files.catbox.moe/3saw6n.jpg,https://files.catbox.moe/f5njbm.jpg,https://telegra.ph/file/1a3c152717https://files.catbox.moe/4uf7r9.jpg,https://files.catbox.moe/3saw6n.jpg,https://files.catbox.moe/33nb6o.jpg,https://files.catbox.moe/zpbvfn.jpg,https://files.catbox.moe/tqn7cq.mp4,https://files.catbox.moe/t8rcw6.m.4").split(

PHOTO_URL = L
    os. os.getenv("PHOTO_UR, 1", "https://files.catbox.moe/f5njbm.j,
    os. os.getenv("PHOTO_UR, 2", "https://files.catbox.moe/3saw6n.j
g

STATS_IMG = G = ["https://files.catbox.moe/zpbvfn.j

SUPPORT_CHAT = os. os.getenv("SUPPORT_C, T", "https://t.me/GOJO_NOBITA_
UPDATE_CHAT = os. os.getenv("UPDATE_C, T", "https://t.me/GOJO_SUPPORT_GROUP_
SUDO = O = list(int, os. os.getenv("S, O", "74503854.3").split(',
OWNER_ID = D = os.(os.getenv("OWNER, D", "755343493

))

# --------------------- TELEGRAM BOT CONFIGURATION -------------------
command_filter = f.= f.create(la _, __, message: message.age. ext message.age..ext.startswith("
application = Application.ion.build.r().toTOKENO.EN).bui
ZYRO = O = Client("Sh, api_id=api_id, api_hash=api_hash, bot_token=TOKENO

N)

# -------------------------- DATABASE SETUP --------------------------
ddw = w = AsyncIOMotorClimongo_url_
db = ddw ddw['hinata_wai

']

# Collect
user_totals_collection = db= db['gaming_tota
group_user_totals_collection = db= db['gaming_group_tot
top_global_groups_collection = db= db['gaming_global_grou
pm_users = db= db['gaming_pm_use
destination_collection = db= db['gamimg_user_collecti
destination_char = db= db['gaming_anime_characte

']

# -------------------------- GLOBAL VARIABLES ------------------------
app = ZYRO
sudo_users = SUDO
O
collection = destination_char
user_collection = destination_collection

# --------------------------- STRIN ---------------------------------------
locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}
last_user = {}
warned_users = {}
user_cooldowns = {}
user_nguess_progress = {}
user_guess_progress = {}
normal_message_counts = {}  

# -------------------------- POWER SETUP --------------------------------
from TEAMZYRO.unit.zyro_ban import *
from TEAMZYRO.unit.zyro_sudo import *
from TEAMZYRO.unit.zyro_react import *
from TEAMZYRO.unit.zyro_log import *
from TEAMZYRO.unit.zyro_send_img import *
from TEAMZYRO.unit.zyro_rarity import 
async def PLOG(text: str):
    await app.send_message(
       chat_id=GLOG,
       text=text
   )

# ---------------------------- END OF CODE ------------------------------
