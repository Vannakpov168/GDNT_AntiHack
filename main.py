import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# បើកប្រព័ន្ធ Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 10000))

# បញ្ជីប្រភេទឯកសារដែលមានហានិភ័យខ្ពស់
DANGEROUS_EXTENSIONS = ['.exe', '.scr', '.bat', '.cmd', '.pif', '.js', '.vbs']

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
                        f"🚨 **រកឃើញមេរោគ ឬឯកសារមានគ្រោះថ្នាក់!**\n\n"
                        f"👤 អ្នកផ្ញើ: @{message.from_user.username or message.from_user.first_name}\n"
                        f"📁 ឯកសារ: `{file_name}`\n\n"
                        f"🛡️ ឯកសារនេះត្រូវបានលុបចេញដោយស្វ័យប្រវត្តិដើម្បីសុវត្ថិភាពសហគមន៍!"
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
    application.add_handler(MessageHandler(filters.Document.ALL & (~filters.COMMAND), scan_and_protect))

    print("🤖 Bot កំពុងដំណើរការ និងត្រៀមទប់ស្កាត់មេរោគ...")
    application.run_polling()

if __name__ == '__main__':
    main()
