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

def run_web_server():
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, SimpleHandler)
    logging.info(f"Starting web server on port {PORT}...")
    httpd.serve_forever()

# ────────────── Telegram Bot Logic ──────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **សួស្តី! ខ្ញុំជា Bot ការពារសហគមន៍ពីឯកសារមេរោគ។**\n\n"
        "ឯកសារទាំងអស់ដែលមាន Extension ដូចខាងក្រោម នឹងត្រូវលុបចេញដោយស្វ័យប្រវត្តិពី Telegram Group របស់អ្នក៖\n\n"
        "📁 **Executables & Scripts:** `.exe`, `.com`, `.scr`, `.msi`, `.msp`, `.bat`, `.cmd`, `.vbs`, `.vbe`, `.js`, `.jse`, `.wsf`, `.wsh`\n\n"
        "📁 **PowerShell Scripts:** `.ps1`, `.ps1xml`, `.ps2`, `.ps2xml`, `.psc1`, `.psc2`, `.msh`, `.msh1`, `.msh2`, `.mshxml`, `.msh1xml`, `.msh2xml`\n\n"
        "📁 **System / Shortcuts:** `.msc`, `.cpl`, `.appx`, `.appxbundle`, `.msix`, `.msixbundle`, `.application`, `.gadget`, `.lnk`, `.url`, `.inf`, `.reg`, `.scf`, `.pif`\n\n"
        "📁 **Office Macros:** `.docm`, `.xlsm`, `.pptm`, `.dotm`, `.xltm`, `.xlam`, `.potm`, `.ppam`, `.sldm`\n\n"
        "📁 **Disks & Archives:** `.iso`, `.img`, `.vhd`, `.vhdx`, `.jar`, `.hta`, `.chm`",
        parse_mode="Markdown"
    )

async def scan_and_protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message and message.document:
        file_name = message.document.file_name.lower()
        is_dangerous = any(file_name.endswith(ext) for ext in DANGEROUS_EXTENSIONS)
        
        if is_dangerous:
            try:
                await message.delete()
                await context.bot.send_message(
                    chat_id=message.chat_id,
                    text=(
                        f"🚨 រកឃើញមេរោគ ឬឯកសារមានគ្រោះថ្នាក់!**\n\n"
                        f"👤 អ្នកផ្ញើ: @{message.from_user.username or message.from_user.first_name}\n"
                        f"📁 ឯកសារ: `{file_name}`\n\n"
                        f"🛡️ ឯកសារនេះត្រូវបានលុបចេញដោយស្វ័យប្រវត្តិដើម្បីសុវត្ថិភាពសហគមន៍!"
                       f"🛡️ ប្រើប្រាស់: @{bot_username} ដើម្បីការពារ Group Telegram របស់អ្នក"
                        f"🛡️ Channel Telgram របស់អគ្គនាយកដ្ឋានរតនាគារជាតិ t.me/GDNTTREADURY"
                    ),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logging.error(f"មិនអាចលុបសារបានទេ៖ {e}")

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
