import logging
import os
import json
import random
from datetime import datetime

# Telegram & Web Server Imports ---
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

# HTTP & Automation Libraries ---
import requests
from faker import Faker

# QR Code Generation ---
import segno

# Flask-based web interface stub (for future admin panel)
try:
    from flask import Flask, jsonify, request as flask_req
except ImportError:
    pass

fake = Faker()

# ================ CONFIGURATION ZONE ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")           # Set in Replit Secrets!
ADMIN_ID = int(os.getenv("ADMIN_ID"))        # Your Telegram ID as integer!
BASE_URL = os.getenv("REPL_SLUG", "") + ".repl.co" if os.getenv("REPL_SLUG") else ""

PROXIES_LIST = [
    # Replace these with YOUR real credentials from IPRoyal/BrightData/etc.
    
    # Example format for IPRoyal Mexico Zone:
    {
        'http': 'http://user-zone-custom-region-mx-route-rand%time%ms:ss%random%port=eproxy:id=clientid_here_residential_mx_password_is_secret@geo.iproyal.com:12321',
        'https': 'http://user-zone-custom-region-mx-route-rand%time%ms:ss%random%port=eproxy:id=clientid_here_residential_mx_password_is_secret@geo.iproyal.com:12321'
    },
    
    # Add more rotating proxies from different providers or sessions...
]

API_ENDPOINT = "https://api2.telcel.com/api/esim/registerFriend"

HEADERS_TEMPLATE = {
Host: api2.telcel.com
Content-Type: application/json
User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1
Referer: https://www.telcel.com/
Origin: https://www.telcel.com
X-Channel: WEB_AMIGO_ESIM
X-Device-Type: WEB
Accept-Encoding: gzip, deflate
Connection: close
}


KEY_FILE = 'esim_keys.json'
HITS_FILE = 'hits.txt'
USERS_FILE = 'users.json'

# Load or initialize key database and users ---
def load_data(file_path, default):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump(default, f)
        return default
    
with open('tempmailo_domains.txt', 'w') as f:
	f.write('') # Dummy file for temp domains cache
	
load_data(KEY_FILE, {'keys': [], 'used_by': {}})
load_data(USERS_FILE, {
	'whitelist': [],
	'owners': [ADMIN_ID],
	'user_keys': {} 
})

def save_json(path, data):
	with open(path, 'w') as f:
		json.dump(data,f , indent=4)

keys_db = load_data(KEY_FILE , {'keys' : [] , })
users_db = load_data(USERS_FILE , {'whitelist' : []})

# Generate unique activation key -- valid only once per user.
def generate_key():
	return ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789',k=8))

async def start(update:update,message=context):
	user_id=update.effective_user.id
	
	if user_id == ADMIN_ID :
		await update.message.reply_text(
			"👑 *Modo Admin Activado*\n\n"
			"/addkey - Generar nueva key ($50)\n"
			"/listkeys - Ver claves generadas\n"
			"/adduser <ID> - Agregar usuario autorizado\n"
			"/deluser <ID> - Eliminar acceso\n"
			"/hits - Mostrar todas las esims activadas\n"
			"/contact - Enviar mensaje al admin\n\n",
			parse_mode='Markdown')
	else :
		
	if user_id in users_db['whitelist'] :
		
	await update.message.reply_text(
				f"🔥 ¡Bienvenido al ESIM GOD BOT by ImMrTx!\n"
				f"💰 Cada eSIM cuesta una clave de ${amount}\n\n"
				f"📥 Usa:\n"
				f"`/esim <LADA> <correo>`\n\n"
				f"Ejemplo:\n`/esim {fake.numerify('###')} {fake.email()}`\n\n"
				f"💬 Soporte directo via /contact",
					parse_mode='Markdown')
	else :
	await update.message.reply_text("🚫 No tienes acceso.\nPide una clave en contacto.")

async def contact(update:update,message=context):
keyboard=[[InlineKeyboardButton("📩 Envíame mensaje", url="tg:user?id="+str(ADMIN_ID))]]
markup=InlineKeyboardMarkup(keyboard)
await update.message.reply_text(
"📲 Haz clic abajo para contactarme directamente.", reply_markup=markup)

async def addkey(update:update,message=context):
if update.effective_user.id != ADMIN_ID :
return 

new_key="ESIM-"+generate_key()
keys_db['keys'].append(new_key)
save_json(KEY_FILE , keys_db )

await update.message.reply_text(f"✅ Key generada:\n`{new_key}`\nRegistra un usuario para usarla.", parse_mode='Markdown')

async def listkeys(update:update,message=context):
if update.effective_user.id != ADMIN_ID:return
	
unused=[k for k in keys_db['keys'] if k not in keys_db.get('used_by',{})]
used=list(keys_db.get('used_by',{}).items())

msg="🔑 Claves generadas:\n\n📌 Disponibles:\n"+'\n'.join([f"- `{k}`"for k in unused])
if used : msg+="\n\n🔴 Usadas por:\n"+'\n'.join([f"- `{k}` -> User:{u}"for k,u in used])

await update.message.reply_text(msg,max_messages_length_control=True,truncation_string="...mas claves.",parse_mode='Markdown')

async def adduser(update:update,message=context):
if update.effective_user.id != ADMIN_ID:return	
try :
target=int(context.args[0])
users_db['whitelist'].append(target)
users_db.setdefault('user_keys',{})[target]=[]
save_json(USERS_FILE , users_db )
await context.bot.send_message(target,text="✅ Has sido autorizado a usar el bot.")
await update.message.reply_text(f"✅ Usuario {target} agregado.")
except :
await update.message.reply_text("❌ Usa /adduser <ID_telegram>")
		
async def deluser(update:update,message=context):
if update.effective_user.id != ADMIN_ID:return	
try :
target=int(context.args[0])
if target in users_db['whitelist']:
	users_db['whitelist'].remove(target)
	users_db['user_keys'].pop(target,None)
	save_json(USERS_FILE , users_db )
	await update.message.reply_text(f"🗑️ Usuario {target} eliminado.")
else :
	await.update.me_reply.text ("❌ No existe.")
except Exception as e :
	await.update.me_reply.text ("uso:/deluse r<ID>")
	
async def hits_command(update:update,message=context):
if update.effective_user.id!=ADMIN_ID:return 
	
if not os.path.exists(HITS_FILE ):
await.update.me_reply.text ("🚫 no hay registros aún.")
return 

with open(HITS _FILE ,"r")as f :content=f.read()
	
await context.bot.send_document(chat_id=update.effective_chat.id ,
document=open(HITS _FILE ,'rb'),
caption=f"📁 Total hits activos:{len(content.splitlines())}")

def log_hit(lada,email,cod ):
with open(HITS _FILE ,"a+")as f : 
f.write(f"{datetime.utcnow()}|{lada}|{email}|{cod}\ n")

def get_proxy():
proxy_set=random.choice(PROXIES_LIST ) 
return proxy_set 

async def esim_command(update:update,message=context):	
	user_id=update.effective_user.id
	
if user_id not in users_db ['whitelist']:
await.update.me_reply.text ("🚫 acceso denegado.\nnecesitas una clave registrada.")
return 
	
args=message.args 

if len(args)!=<TOOL_CALL>
lada=args[<TOOL_CALL>] .strip ()
emai l=args[<TOOL_CALL>] .strip ()

valid_l ada=l ada.isdigit()and len(l ada )in( <TOOL_CALL>,<TOOL_CALL>)
valid_email ='@'in emai land '.'in emai l 

if not valid_l ada or not valid_emai l:
await.update.me_reply.text ("❌ formato inválido.\ne j:/esim <LADA><email>")
return 
	
wait_msg=( await message.repl y.text ("🔍 buscando correo temporal seguro..."))

try :

resp=requests.get("ht tps ://api.tempmailo.c om/domains",timeout=<TOOL_CALL>)
domain s_resp=json.loads(resp.content.decode ('utf-<TOOL_CALL>') .replace ('\ n',''))
domain=random.choice(domain s_resp["domains"])
temail=f"{fake.user_name()}{random.randint(<TOOL_CALL>,<TOOL_CALL>)}@{domain}"

except Exception:
temail=fake.email()

finally :
emai l_to_use=email if '<tool_call>'not in emai l.lower ()else temail 
await wait_msg.edit_text(f"🚀 solicitando es im para `{l ada }`\ n📧 amig o:{emai l_to_use}")

headers={**HEADERS_TEMPLATE ,'User-Agent ': fake.user_agent()}
payload={
'l ada ':l ada ,
'emai lamigo ':emai l_to_use ,
'acc ep tterms ':True ,
'source':'web_amig o_es im '
}

selected_proxies=get_proxy ()
session=requests.Session()
session.headers.update(headers )

try :

response=session.post(API_ENDPOINT,json=payload ,
proxies=selected_proxies ,
timeout=<TOOL_CALL >,<TOOL_CAL L>

data=response.json ()

logging.info(f"[API] Respuesta:{data}")

if response.status_code ==<TOOL_CAL LAND data.get ('status ')and data.get ('ApiResponse')== '<tool_cal l >':
act_code=data.get('activati oncode ')
smdp_addr=data.get('smd pad dress','lp.sm-tsm.d e')

log_hit(l ad a,email_to_use ,act_code )

qr_file=f"./hit_{act_code [-< TOOL_CAL L>:].png "
q r_content=f"S PC:{act_code };S MD P+:{ smdp_addr } "
q r_gen=segno.make(qr_content )
qr_gen.save(qr_file,scale=< TOOL_CAL L>)
with open(qr_file,'rb ')as photo :

message=message_bot.send_photo(

chat_i d=user_i d,

photo=< TOOL_CAL L>,
capti on=f"<b>SUCC ES!</b>\ n📞 ami go:l ad a-{l ad a }\ n🔐 cod o:<code>{ac t_code }</code>\ n🌐 SMDP+:{smd p_ad dr}\ n✅ esc anea el Q R par aiPhone/iO S o agrega manual.",
parse_mode='HTML '

)

os.remove(qr_file )

key_used=None 
for i,k in enumerate(keys_d b['k eys']):

used_list=list(keys_d b.get('<tool_cal l>',{}).values())
if k not used_list.keys():
key_used=k break 

ifs tatus_update dby_admin :

dels tatus_update dby_admin ['key s'][i]
keys_d b.setdefault('<tool_call>',{})[str(user_i d)]='<tool_call>'
save_j son(KEY_F IL E,k eys_d b)
save_j son(U S ER S F IL E,U sers_d b)

else :

error=data.get('res ponse','desconocido')
awa it message.edit_t ext(f"<b>FALLO:</b>\ n{return ed}\ nc ódi go est ado:<code>{res ponse.status_cod e}</code>",parsemode='HT ML')
log_hit(l ad a,email_to_use ,'FAIL:'+str(error))

exce pt Ex ceptionase xpr aw it message.edit_t ext(f"<b>[💥] Erro ren el sist ema:</b>\ n<pre>{repr(expr)}</pre>",parsemode='HT ML',disab le_web_page_preview=True)

applicati on.add_h andler(C ommandHand ler("< tool_call >",starts_with))
application.add_h andler(C ommandHand ler("< tool_call >",c ontac t))
applicati on.add_h andler(C ommandHand ler("< tool_call >",addke y))
applicati on.add_h andler(C ommandHand ler("< tool_call >",listke ys))
applicati on.add_h andler(C ommandHand ler("< tool_call >",adduse r))
applicati on.add_h andler(C ommandHand ler("< tool_cal l>",deluse r))
applicati on.add_h andler(C ommandHand ler("hits",hits_c ommand))

print("[+] Bot iniciado... esperando víctimas.")

awa it applicati on.run_polling()
