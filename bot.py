# Combine and generate updated full code with category & country summary message
import json, time
from datetime import datetime
from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# === 設定 ===
TOKEN = "7828478601:AAH20mV61kItuAgy2iCs6mnZK31xd1t85-c"
ADMIN_GROUP_ID = -4767410856
COOLDOWN_SECONDS = 1.5
MAX_VIOLATIONS = 10

# === 檔案路徑 ===
LOG_TRACK_FILE = "user_last_log.json"
BLACKLIST_FILE = "blacklist.json"
TIMESTAMP_FILE = "user_timestamps.json"
VIOLATION_FILE = "user_violations.json"
CATEGORY_VIEWS_FILE = "user_category_views.json"
VIEWS_FILE = "views.json"
USER_VIEWS_FILE = "user_views.json"
STATS_MESSAGE_ID_FILE = "stats_message_id.json"

# === 分類鍵盤 ===
CATEGORY_ROW1 = ["🍭️ 購物", "🛡️ 保險", "🏥 醫療", "💰 金融", "🎓 教育"]
CATEGORY_ROW2 = ["📦 全部", "🔙 回上一頁"]

# === 讀取資料 ===
with open("post_data.json", "r", encoding="utf-8") as f:
    post_data = json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    countries = list(post_data.keys())
    keyboard = [
        [KeyboardButton(c) for c in countries[0:4]],
        [KeyboardButton(c) for c in countries[4:8]],
        [KeyboardButton(c) for c in countries[8:]]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "點選下方國家以查看數據👇\n若找不到您需要的國家或資訊，\n請聯絡 @aurictide 訂購服務。",
        reply_markup=reply_markup
    )

async def debug_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🔞 Chat ID：`{update.effective_chat.id}`", parse_mode=ParseMode.MARKDOWN
    )

async def unlock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("請提供 user_id，例如：/unlock 123456789")
        return
    user_id = context.args[0]
    for file in [BLACKLIST_FILE, VIOLATION_FILE, TIMESTAMP_FILE]:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        if user_id in data:
            del data[user_id]
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    await update.message.reply_text(f"✅ 已解除封鎖用戶 {user_id} 並清除違規紀錄")

async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or "(無使用者名稱)"
    display_username = f"@{username}" if user.username else "(無使用者名稱)"
    full_name = user.full_name
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = update.message.text
    country = context.user_data.get('selected_country')

    # 黑名單檢查
    try:
        with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
            blacklist = json.load(f)
    except FileNotFoundError:
        blacklist = {}

    if user_id in blacklist:
        await update.message.reply_text("❌ 您因為連續點擊已被暫時封鎖，請聯繫 @aurictide 解鎖")
        return

    try:
        with open(TIMESTAMP_FILE, "r", encoding="utf-8") as f:
            timestamps = json.load(f)
    except FileNotFoundError:
        timestamps = {}

    last_time = timestamps.get(user_id, 0)
    now_ts = time.time()

    if now_ts - last_time < COOLDOWN_SECONDS:
        try:
            with open(VIOLATION_FILE, "r", encoding="utf-8") as f:
                violations = json.load(f)
        except FileNotFoundError:
            violations = {}

        violations[user_id] = violations.get(user_id, 0) + 1
        if violations[user_id] >= MAX_VIOLATIONS:
            blacklist[user_id] = True
            with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
                json.dump(blacklist, f, ensure_ascii=False, indent=2)
            await update.message.reply_text("❌ 您因為連續點擊已被暫時封鎖，請聯繫 @aurictide 解鎖")
            return

        with open(VIOLATION_FILE, "w", encoding="utf-8") as f:
            json.dump(violations, f, ensure_ascii=False, indent=2)
        await update.message.reply_text("⚠️ 請稍候幾秒再查詢，避免連續點擊")
        return

    timestamps[user_id] = now_ts
    with open(TIMESTAMP_FILE, "w", encoding="utf-8") as f:
        json.dump(timestamps, f, ensure_ascii=False, indent=2)

    # 國家選擇
    if text in post_data:
        context.user_data['selected_country'] = text
        keyboard = [
            [KeyboardButton(c) for c in CATEGORY_ROW1],
            [KeyboardButton(c) for c in CATEGORY_ROW2]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"您選擇了：{text}\n請選擇類別 👇", reply_markup=reply_markup)
        return

    if text == "🔙 回上一頁":
        await start(update, context)
        return

    if not country:
        await update.message.reply_text("請先從 /start 選擇國家")
        return

     # ✅ 支援分類為 str 或 list
    all_posts = post_data.get(country, [])
    if text == "📦 全部":
        filtered_posts = all_posts
    else:
        category_keyword = text.split(" ")[-1]
        filtered_posts = []
        for p in all_posts:
            cat = p.get("category")
            if isinstance(cat, str) and cat == category_keyword:
                filtered_posts.append(p)
            elif isinstance(cat, list) and category_keyword in cat:
                filtered_posts.append(p)

    if filtered_posts:
        reply = f"【 {country} 】 數據如下：\n\n"
        for post in filtered_posts:
            reply += f"📌 [{post['title']}]({post['url']})\n\n"
    else:
        reply = f"目前 {country} 沒有「{text}」類別的數據喔～\n訂購請找 @aurictide"
    await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

    # 統計資料 views/user_views
    for fname, key in [(VIEWS_FILE, country), (USER_VIEWS_FILE, (user_id, country))]:
        try:
            with open(fname, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        if isinstance(key, tuple):
            if key[0] not in data:
                data[key[0]] = {}
            data[key[0]][key[1]] = data[key[0]].get(key[1], 0) + 1
        else:
            data[key] = data.get(key, 0) + 1
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # 分類 user_category_views
    try:
        with open(CATEGORY_VIEWS_FILE, "r", encoding="utf-8") as f:
            cat_views = json.load(f)
    except FileNotFoundError:
        cat_views = {}
    if user_id not in cat_views:
        cat_views[user_id] = {}
    cat_views[user_id][text] = cat_views[user_id].get(text, 0) + 1
    with open(CATEGORY_VIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(cat_views, f, ensure_ascii=False, indent=2)

    # 最常用國家/類別
    with open(USER_VIEWS_FILE, "r", encoding="utf-8") as f:
        user_views = json.load(f)
    with open(CATEGORY_VIEWS_FILE, "r", encoding="utf-8") as f:
        user_cats = json.load(f)

    top_country = max(user_views[user_id], key=user_views[user_id].get)
    top_category = max(user_cats[user_id], key=user_cats[user_id].get)
    query_result = f"{text[2:]}（無資料）" if not filtered_posts else text[2:]

    log_message = (
        f"\n用戶名稱：{full_name}"
        f"\n使用者：{display_username}"
        f"\n用戶 ID：{user_id}"
        f"\n最關注國家：{top_country}"
        f"\n最關注類別：{top_category}"
        f"\n時間：{now_str}"
        f"\n\n查詢項目：\n{country} {query_result}"
        f"\n\n--------------------"
    )

    # 管理員紀錄訊息
    try:
        with open(LOG_TRACK_FILE, "r", encoding="utf-8") as f:
            last_logs = json.load(f)
    except FileNotFoundError:
        last_logs = {}

    if user_id in last_logs:
        try:
            await context.bot.delete_message(chat_id=ADMIN_GROUP_ID, message_id=last_logs[user_id]["message_id"])
        except Exception:
            pass

    sent = await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=log_message)
    last_logs[user_id] = {"message_id": sent.message_id}
    with open(LOG_TRACK_FILE, "w", encoding="utf-8") as f:
        json.dump(last_logs, f, ensure_ascii=False, indent=2)

    # 更新統計摘要（編輯訊息）
    summary = "\n\n國家查詢統計：\n\n"
    with open(VIEWS_FILE, "r", encoding="utf-8") as f:
        country_counts = json.load(f)
    summary += "\n".join([f"{k}：{v}" for k, v in country_counts.items()])
    summary += f"\n\n\n分類查詢統計：\n\n"

    category_totals = {}
    for u in cat_views:
        for cat, count in cat_views[u].items():
            category_totals[cat] = category_totals.get(cat, 0) + count
    summary += "\n".join([f"{k}：{v}" for k, v in category_totals.items()])
    summary += f"\n\n總查詢：{sum(country_counts.values())}"

    try:
        with open(STATS_MESSAGE_ID_FILE, "r", encoding="utf-8") as f:
            stats_msg = json.load(f)
            await context.bot.edit_message_text(chat_id=ADMIN_GROUP_ID, message_id=stats_msg["id"], text=summary)
    except (FileNotFoundError, Exception):
        msg = await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=summary)
        with open(STATS_MESSAGE_ID_FILE, "w", encoding="utf-8") as f:
            json.dump({"id": msg.message_id}, f)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("chatid", debug_chat_id))
    app.add_handler(CommandHandler("unlock", unlock_user))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selection))
    print("🤖 Bot 已啟動！")
    app.run_polling()

main()
