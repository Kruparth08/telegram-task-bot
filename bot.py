from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database
import ai_parser

PRIORITY_EMOJI = {
    "High": "🔴",
    "Medium": "🟡",
    "Low": "🟢"
}

PER_PAGE = 5

def render_tasks_page(user_id: int, page: int = 1):
    stats = database.get_task_stats(user_id)
    open_tasks = database.get_open_tasks(user_id)
    
    header = f"📊 <b>Task Summary</b>: Total: <code>{stats['total']}</code> | Completed: <code>{stats['completed']}</code> | Pending: <code>{stats['pending']}</code>\n\n"
    
    if not open_tasks:
        return header + "✨ You have no pending tasks! Enjoy your day or add a new task.", None
        
    total_pages = max(1, (len(open_tasks) + PER_PAGE - 1) // PER_PAGE)
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * PER_PAGE
    end_idx = start_idx + PER_PAGE
    page_tasks = open_tasks[start_idx:end_idx]
    
    text = header + f"📋 <b>Your Open Tasks</b> (Page {page}/{total_pages}):\n\n"
    keyboard = []
    
    for idx, t in enumerate(page_tasks, start_idx + 1):
        emoji = PRIORITY_EMOJI.get(t.priority, "🟡")
        due_str = f" | 🕒 {t.due_date.strftime('%b %d, %I:%M %p')}" if t.due_date else ""
        text += f"{idx}. {emoji} <b>{t.title}</b>{due_str}\n"
        
        keyboard.append([
            InlineKeyboardButton(f"✅ Done #{idx}", callback_data=f"done_{t.id}_{page}"),
            InlineKeyboardButton(f"🗑️ Delete #{idx}", callback_data=f"del_{t.id}_{page}")
        ])
        
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"page_{page-1}"))
        nav_row.append(InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"page_{page+1}"))
        keyboard.append(nav_row)
        
    return text, InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    database.get_or_create_user(user.id, user.username, user.first_name)
    
    first_name = user.first_name or "there"
    text = f"""👋 Hello <b>{first_name}</b>! Welcome to your <b>Task & Reminder Bot</b> 🚀

Simply send your tasks in plain language!

<b>Examples:</b>
• <i>"Buy groceries today at 8 PM"</i>
• <i>"Write book and draw diagrams"</i> (auto splits into 2 tasks)
• <i>"Finish DBMS assignment"</i>

<b>Commands:</b>
/tasks - View open tasks, task stats, & complete/delete buttons
"""
    await update.message.reply_text(text, parse_mode="HTML")

async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    database.get_or_create_user(user_id, update.effective_user.username, update.effective_user.first_name)
    
    text, reply_markup = render_tasks_page(user_id, page=1)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    
    database.get_or_create_user(user_id, update.effective_user.username, update.effective_user.first_name)
    
    parsed = ai_parser.parse_user_message(user_text)
    
    if parsed.intent == "LIST_TASKS":
        await tasks_command(update, context)
        return
        
    if parsed.intent == "COMPLETE_TASK":
        tasks = database.get_open_tasks(user_id)
        if not tasks:
            await update.message.reply_text("✨ You have no pending tasks to complete!")
            return
            
        matched_task = None
        if parsed.task_title:
            for t in tasks:
                if parsed.task_title.lower() in t.title.lower():
                    matched_task = t
                    break
        if not matched_task:
            matched_task = tasks[0]
            
        database.mark_completed(user_id, matched_task.id)
        await update.message.reply_text(f"🎉 Marked <b>{matched_task.title}</b> as completed!", parse_mode="HTML")
        return

    # CREATE_TASK (Single or Multiple)
    task_items = parsed.tasks
    if not task_items:
        task_items = [ai_parser.TaskItem(task_title=user_text, priority="Medium")]
        
    created = []
    for t_item in task_items:
        due_date = None
        if t_item.due_date_iso:
            try:
                due_date = datetime.fromisoformat(t_item.due_date_iso)
            except ValueError:
                due_date = None
                
        task = database.add_task(
            user_id=user_id,
            title=t_item.task_title,
            priority=t_item.priority or "Medium",
            due_date=due_date
        )
        created.append(task)
        
    if len(created) == 1:
        task = created[0]
        due_str = f"\n🕒 <b>Due</b>: {task.due_date.strftime('%b %d at %I:%M %p')}" if task.due_date else ""
        resp = f"✅ <b>Task Saved!</b>\n\n📌 <b>{task.title}</b>{due_str}"
    else:
        resp = f"✅ <b>Created {len(created)} Separate Tasks!</b>\n\n"
        for idx, t in enumerate(created, 1):
            due_str = f" (🕒 {t.due_date.strftime('%b %d %I:%M %p')})" if t.due_date else ""
            resp += f"{idx}. 📌 <b>{t.title}</b>{due_str}\n"
            
    await update.message.reply_text(resp, parse_mode="HTML")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "noop":
        return
        
    if data.startswith("page_"):
        page = int(data.split("_")[1])
        text, reply_markup = render_tasks_page(user_id, page=page)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
        return
        
    if data.startswith("done_"):
        parts = data.split("_")
        task_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 1
        database.mark_completed(user_id, task_id)
        
        text, reply_markup = render_tasks_page(user_id, page=page)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
        
    elif data.startswith("del_"):
        parts = data.split("_")
        task_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 1
        database.delete_task(user_id, task_id)
        
        text, reply_markup = render_tasks_page(user_id, page=page)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
