from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "7828478601:AAH20mV61kItuAgy2iCs6mnZK31xd1t85-c"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "*Aurictide 數據搜尋工具*\n"
        "(提供篩選搜尋各種菜品)\n\n"
        "❓ 找不到您要的國家或數據嗎？\n"
        " 請聯繫 @Aurictide\n\n"
        " 點擊下方按鈕開啟 APP ⬇️"
    )
    keyboard = [
        [
            InlineKeyboardButton(
                " Aurictide Data ",
                web_app=WebAppInfo(url="https://www.aurictide.com/data")
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # 使用 MarkdownV2 或 Markdown，這裡示範 Markdown
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
