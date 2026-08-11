import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# បើកប្រព័ន្ធ Logging ដើម្បីមើលដំណាក់កាលរបស់ Bot
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ដាក់ Token របស់ Bot ដែលបានពី BotFather ទីនេះ
TOKEN = "YOUR_BOT_TOKEN_HERE"

# បញ្ជីប្រភេទឯកសារដែលអាចមានហានិភ័យខ្ពស់ (អាចបន្ថែមតាមតម្រូវការ)
DANGEROUS_EXTENSIONS = ['.exe', '.scr', '.bat', '.cmd', '.pif', '.js', '.vbs']

async def scan_and_protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    # ពិនិត្យមើលថាតើមានឯកសារ (Document) ឬកម្មវិធី (Audio/Video ដែលខុសប្រក្រតី) ដែរឬទេ
    if message.document:
        file_name = message.document.file_name.lower()
        file_id = message.document.file_id
        
        # ពិនិត្យนามสกุลឯកសារ (Extension)
        is_dangerous = any(file_name.endswith(ext) for ext in DANGEROUS_EXTENSIONS)
        
        if is_dangerous:
            try:
                # ១. លុបសារដែលមានផ្ទុកឯកសារមេរោគនោះចោលភ្លាមៗ
                await message.delete()
                
                # ២. ផ្ញើសារជូនដំណឹងទៅក្នុង Group
                warning_msg = await context.bot.send_message(
                    chat_id=message.chat_id,
                    text=(
                        f"🚨 **រកឃើញមេរោគ ឬឯកសារមានគ្រោះថ្នាក់!**\n\n"
                        f"👤 អ្នកផ្ញើ: @{message.from_user.username or message.from_user.first_name}\n"
                        f"📁 ឯកសារ: `{file_name}`\n\n"
                        f"🛡️ ឯកសារនេះត្រូវបានលុបចេញដោយស្វ័យប្រវត្តិដើម្បីសុវត្ថិភាពសហគមន៍!"
                    ),
                    parse_mode="Markdown"
                )
                
                # (ជាជម្រើស) លុបសារជូនដំណឹងវិញបន្ទាប់ពី ១០វិនាទី ដើម្បីកុំឱ្យញាំញីក្នុងกลุ่ม
                # context.job_queue.run_once(delete_warning, 10, data=warning_msg)
                
            except Exception as e:
                logging.error(f"មិនអាចលុបសារបានទេ៖ {e} (សូមឆែកមើលសិទ្ធិ Admin របស់ Bot)")

def main():
    # បង្កើត Application របស់ Bot
    application = ApplicationBuilder().token(TOKEN).build()

    # បន្ថែម Handler ដើម្បីចាប់យកាល់តែមានឯកសារផ្ញើចូល Group/Channel
    # filters.Document.ALL គឺសម្រាប់ចាប់យករាល់ File ទាំងអស់
    application.add_handler(MessageHandler(filters.Document.ALL & (~filters.COMMAND), scan_and_protect))

    print("🤖 Bot កំពុងដំណើរការ និងត្រៀមទប់ស្កាត់មេរោគ...")
    
    # ចាប់ផ្តើមដំណើរការ Bot
    application.run_polling()

if __name__ == '__main__':
    main()
