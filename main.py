import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# បើកប្រព័ន្ធ Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 10000))

# បញ្ជីប្រភេទឯកសារដែលមានហានិភ័យ និងមេរោគទាំងអស់ (បានអាប់ដេតថ្មី)
DANGEROUS_EXTENSIONS = [
    # Executables & Scripts
    '.exe', '.com', '.scr', '.msi', '.msp', '.bat', '.cmd', '.vbs', '.vbe', '.js', '.jse', '.wsf', '.wsh',
    # PowerShell Scripts
    '.ps1', '.ps1xml', '.ps2', '.ps2xml', '.psc1', '.psc2', '.msh', '.msh1', '.msh2', '.mshxml', '.msh1xml', '.msh2xml',
    # System / App Packages / Shortcuts
    '.msc', '.cpl', '.appx', '.appxbundle', '.msix', '.msixbundle', '.application', '.gadget',
    '.lnk', '.url', '.inf', '.reg', '.scf', '.pif',
    # Macro-enabled Office Documents
    '.docm', '.xlsm', '.pptm', '.dotm', '.xltm', '.xlam', '.potm', '.ppam', '.sldm',
    # Disks, Archives & Others
    '.iso', '.img', '.vhd', '.vhdx', '.jar', '.hta', '.chm'
]

# ────────────── Web Server សម្រាប់ Render ចាប់យក Port ──────────────
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

# ────────────── Telegram Bot Logic ──────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>សួស្តី! ខ្ញុំជា Bot ការពារ Group ពីមេរោគ</b>\n\n"
        "ឯកសារទាំងអស់ដែលមាន Extension ដូចខាងក្រោម នឹងត្រូវលុបចេញដោយស្វ័យប្រវត្តិពី Telegram Group របស់អ្នក៖\n\n"
        "📁 <b>Executables & Scripts:</b> <code>.exe</code>, <code>.com</code>, <code>.scr</code>, <code>.msi</code>, <code>.msp</code>, <code>.bat</code>, <code>.cmd</code>, <code>.vbs</code>, <code>.vbe</code>, <code>.js</code>, <code>.jse</code>, <code>.wsf</code>, <code>.wsh</code>\n\n"
        "📁 <b>PowerShell Scripts:</b> <code>.ps1</code>, <code>.ps1xml</code>, <code>.ps2</code>, <code>.ps2xml</code>, <code>.psc1</code>, <code>.psc2</code>, <code>.msh</code>, <code>.msh1</code>, <code>.msh2</code>, <code>.mshxml</code>, <code>.msh1xml</code>, <code>.msh2xml</code>\n\n"
        "📁 <b>System / Shortcuts:</b> <code>.msc</code>, <code>.cpl</code>, <code>.appx</code>, <code>.appxbundle</code>, <code>.msix</code>, <code>.msixbundle</code>, <code>.application</code>, <code>.gadget</code>, <code>.lnk</code>, <code>.url</code>, <code>.inf</code>, <code>.reg</code>, <code>.scf</code>, <code>.pif</code>\n\n"
        "📁 <b>Office Macros:</b> <code>.docm</code>, <code>.xlsm</code>, <code>.pptm</code>, <code>.dotm</code>, <code>.xltm</code>, <code>.xlam</code>, <code>.potm</code>, <code>.ppam</code>, <code>.sldm</code>\n\n"
        "📁 <b>Disks & Archives:</b> <code>.iso</code>, <code>.img</code>, <code>.vhd</code>, <code>.vhdx</code>, <code>.jar</code>, <code>.hta</code>, <code>.chm</code>",
        parse_mode="HTML"
    )

async def scan_and_protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message and message.document:
        file_name = message.document.file_name.lower()
        is_dangerous = any(file_name.endswith(ext) for ext in DANGEROUS_EXTENSIONS)
        
        if is_dangerous:
            try:
                # 1. លុបសារឯកសារមេរោគចេញស្ងាត់ៗ
                await message.delete()
                
                # 💡 ប្រសិនបើថ្ងៃក្រោយចង់ឱ្យ Bot ផ្ញើសារព្រមានឡើងវិញ គ្រាន់តែលុបសញ្ញា """ ដើម និងចុងចេញ៖
                """
                bot_info = await context.bot.get_me()
                bot_username = bot_info.username
                user_mention = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
                
                warning_text = (
                    f"🚨 <b>រកឃើញមេរោគ ឬឯកសារមានគ្រោះថ្នាក់!</b>\n\n"
                    f"👤 អ្នកផ្ញើ: {user_mention}\n"
                    f"📁 ឯកសារ: <code>{file_name}</code>\n\n"
                    f"🛡️ ឯកសារនេះត្រូវបានលុបចេញដោយស្វ័យប្រវត្តិដើម្បីសុវត្ថិភាព!\n"
                    f"🛡️ ប្រើប្រាស់: @{bot_username} ដើម្បីការពារ Group Telegram របស់អ្នក\n"
                    f'📢 Channel Telegram របស់អគ្គនាយកដ្ឋានរតនាគារជាតិ: <a href="https://t.me/GDNTREASURY">t.me/GDNTREASURY</a>'
                )

                await context.bot.send_message(
                    chat_id=message.chat_id,
                    text=warning_text,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                """
            except Exception as e:
                logging.error(f"Error in scan_and_protect: {e}")

def main():
    if not TOKEN:
        print("❌ កំហុស៖ រកមិនឃើញ TOKEN នៅក្នុង Environment Variables ទេ!")
        return

    # ចាប់ផ្តើម Web Server ក្នុង Background Thread ដើម្បីបើក Port ឱ្យ Render
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()

    # បង្កើត Application របស់ Telegram Bot
    application = ApplicationBuilder().token(TOKEN).build()
    
    # បន្ថែម Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.Document.ALL & (~filters.COMMAND), scan_and_protect))

    print("🤖 Bot កំពុងដំណើរការ និងត្រៀមទប់ស្កាត់មេរោគ...")
    application.run_polling()

if __name__ == '__main__':
    main()
