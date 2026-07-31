import os
import logging
import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = "7289730003:AAGAsp3WUecjW1xSj1ZnWQUc0bWUjU2ARQU"

# File paths
EXCEL_FILE = "students_results.xlsx"

# Global variable to store the DataFrame
df = None

# Admin chat IDs - YOUR ID
ADMIN_IDS = [1116152450]

def load_data():
    """Load the Excel file and return DataFrame"""
    global df
    try:
        if not os.path.exists(EXCEL_FILE):
            logger.error(f"File {EXCEL_FILE} not found!")
            return False
        
        df = pd.read_excel(EXCEL_FILE, sheet_name="Sheet1")
        df.columns = df.columns.str.strip()
        df.rename(columns={
            'Student ID': 'student_id',
            'Student Full Name': 'full_name',
            'Grade Level': 'grade_level',
            'Total': 'total',
            'Average': 'average',
            'Rank': 'rank',
            'Status': 'status'
        }, inplace=True)
        df['total'] = pd.to_numeric(df['total'], errors='coerce')
        df['average'] = pd.to_numeric(df['average'], errors='coerce')
        df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
        
        logger.info(f"Data loaded successfully. {len(df)} records found.")
        return True
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return False

def get_main_menu_keyboard():
    keyboard = [
        [KeyboardButton("✅ Check Result")],
        [KeyboardButton("📝 Complain")],
        [KeyboardButton("❓ Help"), KeyboardButton("📊 Stats")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_message = (
        f"👋 *Welcome to Dillfana Student Results Bot!*\n\n"
        f"Hi {user.first_name}! I can help you check student results.\n\n"
        f"📚 *Available Commands:*\n"
        f"/help - Show this help message\n"
        f"/search_name <name> - Search students by name\n"
        f"/search_id <student_id> - Search student by ID\n"
        f"/top <grade> - Show top 10 students\n"
        f"/stats <grade> - Show statistics for a grade\n"
        f"/grades - Show all available grade levels\n"
        f"/result <student_id> - Get full result for a student\n\n"
        f"📱 *Or use the buttons below:*"
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 *Dillfana Student Results Bot - Help*\n\n"
        "*Available Commands:*\n\n"
        "🔹 `/start` - Start the bot\n"
        "🔹 `/help` - Show this help\n"
        "🔹 `/search_name <name>` - Search students by name\n"
        "🔹 `/search_id <id>` - Search student by ID\n"
        "🔹 `/top <grade>` - Show top 10 students\n"
        "🔹 `/stats <grade>` - Show grade statistics\n"
        "🔹 `/grades` - List all available grades\n"
        "🔹 `/result <id>` - Get full student result\n\n"
        "*Quick Actions:*\n"
        "• Use the menu buttons below for easy access"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())

async def handle_complain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the Complain button - Set user state to complaint mode"""
    context.user_data['action'] = 'complaint'
    await update.message.reply_text(
        "📝 *Submit a Complaint*\n\n"
        "Please describe your complaint or issue in detail.\n\n"
        "📌 *Example:*\n"
        "My grade is incorrect. I got 70 but I should have 85.",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )

async def handle_complaint_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process complaint submissions and notify admins"""
    logger.info("===== COMPLAINT RECEIVED =====")
    
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name or user.username or "Unknown"
    complaint_text = update.message.text
    
    logger.info(f"User ID: {user_id}")
    logger.info(f"User Name: {user_name}")
    logger.info(f"Complaint: {complaint_text}")
    logger.info(f"Admin IDs: {ADMIN_IDS}")
    
    # Send confirmation to user
    await update.message.reply_text(
        "✅ *Your complaint has been received!*\n\n"
        "📤 The admin has been notified and will respond shortly.\n\n"
        f"📋 *Your complaint:*\n"
        f"_{complaint_text}_",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )
    
    # Send notification to admin (YOU!)
    admin_message = (
        f"⚠️ *NEW COMPLAINT RECEIVED* ⚠️\n\n"
        f"👤 *From:* {user_name}\n"
        f"🆔 *User ID:* `{user_id}`\n"
        f"📅 *Time:* {update.message.date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"📝 *Complaint:*\n"
        f"_{complaint_text}_\n\n"
        f"💬 *To reply:* Use /reply {user_id} <message>"
    )
    
    # Send to all admins
    for admin_id in ADMIN_IDS:
        try:
            logger.info(f"Attempting to send notification to admin {admin_id}")
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                parse_mode="Markdown"
            )
            logger.info(f"✅ Complaint notification sent to admin {admin_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send complaint to admin {admin_id}: {e}")
            logger.exception(e)
    
    # Reset the user action
    context.user_data['action'] = None
    
    # Send a test notification to confirm it's working
    await update.message.reply_text(
        "🔔 *Test:* If you're the admin, you should see the complaint notification above.",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    text = update.message.text.strip()
    
    # IMPORTANT: Check for complaint mode FIRST
    if context.user_data.get('action') == 'complaint':
        await handle_complaint_submission(update, context)
        return
    
    # If not in complaint mode, check for other actions
    if df is None:
        await update.message.reply_text("❌ Data not loaded. Please try again later.")
        return
    
    # Check if it looks like a student ID (starts with STU)
    if text.upper().startswith("STU"):
        student = get_student_by_id(text)
        if student is not None:
            message = format_student_result(student, full=True)
            await update.message.reply_text(message, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
            return
    
    # Search by name (but only if it seems like a name, not a complaint)
    if len(text) >= 2 and not any(word in text.lower() for word in ['grade', 'incorrect', 'wrong', 'error', 'issue']):
        results = get_students_by_name(text)
        if not results.empty:
            if len(results) == 1:
                student = results.iloc[0]
                message = format_student_result(student, full=True)
                await update.message.reply_text(message, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
            elif len(results) <= 10:
                message = f"🔍 Found {len(results)} students matching '{text}':\n\n"
                for _, student in results.iterrows():
                    name = student['full_name']
                    sid = student['student_id']
                    grade = student['grade_level']
                    total = student['total']
                    total_str = f"{total:.2f}" if pd.notna(total) else "No data"
                    message += f"📌 *{name}*\n"
                    message += f"   ID: `{sid}` | {grade} | Total: {total_str}\n\n"
                message += "_Use /result <student_id> for full details_"
                await update.message.reply_text(message, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
            else:
                message = f"🔍 Found {len(results)} students matching '{text}'.\n\nPlease use a more specific search."
                await update.message.reply_text(message, reply_markup=get_main_menu_keyboard())
            return
    
    # If nothing matches
    await update.message.reply_text(
        f"❌ No results found for '{text}'.\n\n"
        "Try using:\n"
        "- Click 📝 Complain to submit a complaint\n"
        "- Use /search_name <name> to search for a student\n"
        "- Use /search_id <id> to search by ID\n"
        "- Or use the menu buttons below.",
        reply_markup=get_main_menu_keyboard()
    )

def get_student_by_id(student_id):
    global df
    if df is None:
        return None
    result = df[df['student_id'].astype(str).str.strip() == str(student_id).strip()]
    if result.empty:
        return None
    return result.iloc[0]

def get_students_by_name(name_query):
    global df
    if df is None:
        return []
    mask = df['full_name'].str.contains(name_query, case=False, na=False)
    return df[mask]

def format_student_result(student, full=False):
    name = student['full_name']
    student_id = student['student_id']
    grade = student['grade_level']
    total = student['total']
    avg = student['average']
    rank = student['rank']
    status = student['status']
    if pd.isna(total):
        return f"👤 *{name}*\n🆔 ID: `{student_id}`\n📚 Grade: {grade}\nℹ️ *No result data available*"
    medal = ""
    if pd.notna(rank):
        if rank == 1:
            medal = "🥇 "
        elif rank == 2:
            medal = "🥈 "
        elif rank == 3:
            medal = "🥉 "
    status_emoji = "✅" if status == "Promoted" else "❌" if status == "Not Promoted" else "ℹ️"
    message = f"👤 *{name}*\n"
    message += f"🆔 ID: `{student_id}`\n"
    message += f"📚 Grade: {grade}\n"
    message += f"📊 Total: {total:.2f}\n"
    message += f"📈 Average: {avg:.2f}\n"
    message += f"🏆 Rank: {medal}#{int(rank) if pd.notna(rank) else 'N/A'}\n"
    message += f"{status_emoji} Status: {status if pd.notna(status) else 'N/A'}"
    return message

async def handle_reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin reply command"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("❌ Please specify user ID and message.\nExample: `/reply 123456789 Hello`")
        return
    try:
        target_id = int(context.args[0])
        reply_message = " ".join(context.args[1:])
        if not reply_message:
            await update.message.reply_text("❌ Please provide a message to send.")
            return
        await context.bot.send_message(
            chat_id=target_id,
            text=f"📨 *Admin Response:*\n\n{reply_message}",
            parse_mode="Markdown"
        )
        await update.message.reply_text(f"✅ Reply sent to user `{target_id}`.", parse_mode="Markdown")
        logger.info(f"Admin {user_id} replied to user {target_id}: {reply_message}")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID format.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending reply: {str(e)}")

def main():
    if not load_data():
        logger.error("Failed to load data. Bot will not start.")
        return
    if not TOKEN:
        logger.error("BOT_TOKEN not found!")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reply", handle_reply_command))
    
    # Menu button handlers
    application.add_handler(MessageHandler(filters.Regex('^📝 Complain$'), handle_complain))
    
    # Handle all other text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🤖 Bot is starting...")
    logger.info(f"👤 Admin ID: {ADMIN_IDS[0]}")
    logger.info("📝 Bot is ready to receive complaints!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()