import json, re, sys
import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
import time # For timestamp in orders

# ========== CONFIG ==========
BOT_TOKEN = "7989043300:AAECZAXZ9ycCSBhfYujXQx5CyVW03bh0AUs" # আপনার বট টোকেন
ADMIN_ID  = 6413241219  # আপনার অ্যাডমিন টেলিগ্রাম ইউজার আইডি
DATA_FILE = "bot_data.json"

BOT_ID = int(BOT_TOKEN.split(":")[0]) # <--- এটিই সঠিক লাইন

# --- Define the file_id for your general welcome image here ---
WELCOME_PHOTO_FILE_ID = "AgACAgUAAxkBAANeaN16I-UxernNmUXW0ez9QUwQa78AAkXEMRvSaPFW29cLmQ1jtvIBAAMCAAN5AAM2BA" # Example file_id, replace with yours!

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# ========== DATA ==========
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    data.setdefault("products", {}) # { "VPN_Name": [{"gmail": "...", "password": "..."}] }
    data.setdefault("balances", {})
    data.setdefault("pending_payments", {})
    data.setdefault("unmatched_payments", {})
    data.setdefault("orders", {})
    data.setdefault("total_sales", 0.0)
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

data               = load_data()
products           = data["products"]
balances           = data["balances"]
pending_payments   = data["pending_payments"]
unmatched_payments = data["unmatched_payments"]
orders             = data["orders"]
total_sales        = data["total_sales"]

# Updated vpn_prices structure based on your provided list
vpn_prices = {
    "Express VPN": {"price": 30, "days": 7},
    "Nord VPN": {"price": 40, "days": 7},
    "PIA VPN": {"price": 30, "days": 7},
    "Surfshark": {"price": 30, "days": 7},
    "HotspotShield VPN": {"price": 30, "days": 7},
    "HMA VPN": {"price": 30, "days": 7},
    "IPVanish VPN": {"price": 30, "days": 7},
    "Cyberghost VPN": {"price": 15, "days": 3}, # Changed to 3 Days
    "Vypr VPN": {"price": 15, "days": 3},    # Changed to 3 Days
    "X VPN": {"price": 30, "days": 7},
    "Pure VPN": {"price": 30, "days": 7},
    "Panda VPN": {"price": 15, "days": 3},   # Changed to 3 Days
    "Turbo VPN": {"price": 30, "days": 7},
    "Sky VPN": {"price": 30, "days": 7},
    "Potato VPN": {"price": 30, "days": 7},
    "Zoog VPN": {"price": 15, "days": 3},    # Changed to 3 Days
    "Bitdefender VPN": {"price": 30, "days": 7}
}

# --- NEW: Define expected fields for each VPN type ---
# Keys are the exact keys from vpn_prices.
# Values are lists of required fields in the order they should appear in the input/output.
product_fields = {
    "ExpressVPN": ["Gmail", "Password", "PC Key"],
    "HMA": ["Activation Key"], # HMA will only have an activation key
    # Default for others (if not specified here, it falls back to a generic GMail/Password)
    # You can explicitly list other VPNs if they have unique fields.
    # For now, if a VPN is not in this dict, it will use the default "Gmail", "Password".
}
# --- END NEW ---

# Payment gateway number (updated to your specified number)
PAYMENT_NUMBER = "01739089344" 

# Helper functions
def main_menu_markup():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🛒 Buy Products", "💰 Add Balance")
    kb.row("📦 My Orders", "💳 My Balance")
    return kb

def admin_menu_markup():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📊 Total Sales", "📈 Current Stock")
    kb.row("➕ Add VPN Account", "⬅️ Main Menu (User)")
    return kb

def norm_text(s): return " ".join(s.strip().split()).lower() if isinstance(s, str) else ""
def ensure_user(uid): balances.setdefault(uid, 0.0); orders.setdefault(uid, [])

def parse_trx_id(text): 
    m_bkash = re.search(r'TrxID[:\s]+([A-Za-z0-9]+)', text, re.I)
    if m_bkash:
        return m_bkash.group(1).lower()
    
    m_nagad = re.search(r'TxnID[:\s]+([A-Za-z0-9]+)', text, re.I)
    if m_nagad:
        return m_nagad.group(1).lower()
        
    return None

def parse_amount(text): 
    m = re.search(r'\bTk\s?([0-9]+(?:\.[0-9]{1,2})?)\b', text.replace(",", ""), re.I)
    return float(m.group(1)) if m else None

# ========== START COMMANDS ==========
@bot.message_handler(commands=['start', 'admin'])
def start_or_admin(message):
    uid = str(message.from_user.id)
    ensure_user(uid)
    
    # Define your welcome message
    welcome_message = (
        "আসসালামু আলাইকুম ❤️‍🩹 PremiumOne এ আপনাকে স্বাগতম। কোন প্রকার সমস্যা হলে যোগাযোগ করবেন @Abdurrahman0999\n"
        "—ধন্যবাদ 💞\n\n"
        "যেভাবে ব্যালেন্স এড করবেন 💳\n\n"
        "\t└ 💰ADD BALANCE এ ক্লিক করুন\n"
        "\t└ bKash/Nagad সিলেক্ট করুন\n"
        "\t└ নাম্বারটি কপি করে পেমেন্ট করুন\n"
        "\t└ Trx Id কপি করে রাখুন\n"
        "\t└ Payment Done ক্লিক করুন\n"
        "\t└ Trx Id দিন\n"
        "\t└ Balance Add হয়ে যাবে\n\n"
        "যেভাবে Vpn নিবেন 🛍\n\n"
        "\t└ Buy Products এ ক্লিক করুন\n"
        "\t└ VPN সিলেক্ট করুন\n"
        "\t└ Buy Now এ ক্লিক করুন"
    
    )

    if uid == str(ADMIN_ID):
        bot.send_message(message.chat.id, "👋 Welcome Admin! Choose an option:", reply_markup=admin_menu_markup())
    else:
        if WELCOME_PHOTO_FILE_ID:
            try:
                bot.send_photo(message.chat.id, WELCOME_PHOTO_FILE_ID, caption=welcome_message, reply_markup=main_menu_markup(), parse_mode="Markdown")
            except Exception as e:
                print(f"Error sending welcome photo with file_id: {e}")
                bot.send_message(message.chat.id, "Error sending welcome image. " + welcome_message, reply_markup=main_menu_markup(), parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, welcome_message, reply_markup=main_menu_markup(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: norm_text(m.text) == "💳 my balance")
def show_balance(message):
    uid = str(message.from_user.id)
    ensure_user(uid)
    bot.send_message(message.chat.id, f"💳 Your current balance: {balances.get(uid, 0.0):.2f}৳", reply_markup=main_menu_markup())

# ========== BUY PRODUCTS ==========
@bot.message_handler(func=lambda m: norm_text(m.text) == "🛒 buy products")
def show_vpn_list(message):
    markup = InlineKeyboardMarkup()
    for name, data_item in vpn_prices.items():
        price = data_item["price"]
        days = data_item["days"]
        stock_count = len(products.get(name, []))
        
        # Display as requested: name, days, price, and a checkmark (stock status not visible here)
        # Use a dot for out of stock, checkmark for in stock
        status_icon = "✅" if stock_count > 0 else "🔴" # Use a red dot for out of stock
        markup.add(InlineKeyboardButton(f"{name} {days} Days {price}৳ {status_icon}", callback_data=f"vpn|{name}")) 
    bot.send_message(message.chat.id, "🛍 Available VPNs:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("vpn|"))
def vpn_selected(c):
    vpn_name = c.data.split("|")[1]
    vpn_info = vpn_prices.get(vpn_name)
    if not vpn_info:
        bot.edit_message_text("❌ VPN not found.", c.message.chat.id, c.message.message_id)
        bot.answer_callback_query(c.id, "VPN not found.", show_alert=True)
        return

    price = vpn_info["price"]
    days = vpn_info["days"]
    uid = str(c.from_user.id)
    bal = balances.get(uid, 0.0)
    stock_count = len(products.get(vpn_name, [])) # Stock count for logic, not display to user

    kb = InlineKeyboardMarkup()
    
    # Message for display (without showing stock count to user)
    message_text = (
        f"🛍 *{vpn_name}* ({days} Days)\n"
        f"Price: {price}৳\n"
        f"Your Balance: {bal:.2f}৳\n\n"
    )
    
    if stock_count == 0:
        bot.answer_callback_query(c.id, "This VPN is currently out of stock. Please choose another.", show_alert=True)
        message_text += "🚫 This VPN is currently *Out of Stock*."
        # No "Buy Now" button if out of stock
    elif bal < price:
        bot.answer_callback_query(c.id, "Insufficient balance. Please add funds.", show_alert=True)
        message_text += "💰 Insufficient balance. Please add funds."
        kb.add(InlineKeyboardButton("➕ Add Balance", callback_data="add_balance_shortcut")) # Correct emoji
    else: # Sufficient balance and stock
        message_text += "Ready to purchase!"
        kb.add(InlineKeyboardButton("✅ Buy Now", callback_data=f"buy|{vpn_name}"))
    
    # Always include Cancel and Back to Main Menu
    kb.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_vpn_selection"))
    kb.add(InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main_menu")) # Correct emoji
    
    bot.edit_message_text(message_text, c.message.chat.id, c.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "cancel_vpn_selection")
def cancel_vpn_selection(c):
    bot.edit_message_text("Selection cancelled. Returning to main menu.", c.message.chat.id, c.message.message_id)
    bot.send_message(c.message.chat.id, "Choose an option:", reply_markup=main_menu_markup())
    bot.answer_callback_query(c.id, "Cancelled.")

@bot.callback_query_handler(func=lambda c: c.data == "back_to_main_menu")
def back_to_main_menu_callback(c):
    bot.edit_message_text("Returning to main menu.", c.message.chat.id, c.message.message_id)
    bot.send_message(c.message.chat.id, "Choose an option:", reply_markup=main_menu_markup())
    bot.answer_callback_query(c.id, "Back to main menu.")


@bot.callback_query_handler(func=lambda c: c.data.startswith("buy|"))
def buy_vpn(c):
    vpn_name = c.data.split("|")[1]
    vpn_info = vpn_prices.get(vpn_name)
    if not vpn_info:
        bot.edit_message_text("❌ VPN not found.", c.message.chat.id, c.message.message_id)
        bot.send_message(c.message.chat.id, "⬅️ Back to menu:", reply_markup=main_menu_markup())
        bot.answer_callback_query(c.id, "VPN not found.", show_alert=True)
        return

    price = vpn_info["price"]
    uid = str(c.from_user.id)
    
    user_balance = balances.get(uid, 0.0)
    vpn_stock = products.get(vpn_name, [])

    if user_balance >= price and len(vpn_stock) > 0:
        item = vpn_stock.pop(0) # Take one item from stock
        balances[uid] = round(user_balance - price, 2) # Update balance
        orders.setdefault(uid, []).append({"vpn_name": vpn_name, "item": item, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")})
            
        global total_sales
        total_sales += price # Add to total sales
        data["products"], data["balances"], data["orders"], data["total_sales"] = products, balances, orders, total_sales
        save_data(data)
        
        # --- MODIFIED: Display VPN details based on product_fields ---
        msg_details = f"🛍 *{vpn_name}* {vpn_info['days']} Days ✅:\n\n"
        
        # Get the fields for this VPN, or default to Gmail/Password
        fields_to_display = product_fields.get(vpn_name, ["Gmail", "Password"])

        for field_name in fields_to_display:
            # The actual key in the `item` dictionary will be lowercase and have underscores if multiple words
            # E.g., "PC Key" becomes "pc_key", "Activation Key" becomes "activation_key"
            item_key = field_name.replace(" ", "_").lower()
            msg_details += f"*{field_name}* ➡ `{item.get(item_key, 'N/A')}`\n"
        # --- END MODIFIED ---

        bot.edit_message_text(msg_details, c.message.chat.id, c.message.message_id, parse_mode="Markdown")
        bot.send_message(c.message.chat.id, "✅ Purchase successful! You can find this in '📦 My Orders'.", reply_markup=main_menu_markup()) 
        bot.answer_callback_query(c.id, "Purchase successful!", show_alert=True)
            
    else:
        error_msg = ""
        if len(vpn_stock) == 0:
            error_msg = "🚫 This VPN is currently *Out of Stock*."
        elif user_balance < price:
            error_msg = "💰 Insufficient balance. Please add funds."
        else:
            error_msg = "❌ VPN unavailable or insufficient balance. Please try again."
        
        bot.edit_message_text(f"{error_msg}\n\n🏠 Returning to main menu.", c.message.chat.id, c.message.message_id, parse_mode="Markdown")
        bot.send_message(c.message.chat.id, "Choose an option:", reply_markup=main_menu_markup())
        bot.answer_callback_query(c.id, error_msg, show_alert=True)

# ========== MY ORDERS ==========
@bot.message_handler(func=lambda m: norm_text(m.text) == "📦 my orders")
def show_my_orders(message):
    uid = str(message.from_user.id)
    user_orders = orders.get(uid)
    
    if not user_orders:
        bot.send_message(message.chat.id, "You haven't purchased any VPNs yet! Go to '🛒 Buy Products' to get started.", reply_markup=main_menu_markup())
        return
    
    order_list_text = "🛍 Your Recent Orders:\n\n"
    # Show last 5 orders, or fewer if less than 5
    for i, order_item in enumerate(user_orders[-5:]): 
        vpn_name = order_item.get("vpn_name", "N/A")
        item_details = order_item.get("item", {})
        timestamp = order_item.get("timestamp", "N/A")
        
        order_list_text += f"*{i+1}. {vpn_name}* (Purchased: {timestamp})\n"
        
        # --- MODIFIED: Display VPN details in orders based on product_fields ---
        fields_to_display = product_fields.get(vpn_name, ["Gmail", "Password"])
        for field_name in fields_to_display:
            item_key = field_name.replace(" ", "_").lower()
            order_list_text += f"  *{field_name}:* `{item_details.get(item_key, 'N/A')}`\n"
        order_list_text += "\n"
        # --- END MODIFIED ---
        
    bot.send_message(message.chat.id, order_list_text, parse_mode="Markdown", reply_markup=main_menu_markup())

# ========== ADD BALANCE ==========
@bot.message_handler(func=lambda m: norm_text(m.text) == "💰 add balance")
def add_balance_ui(message):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🟣 Bkash", callback_data="add_balance_bkash"))
    kb.add(InlineKeyboardButton("🟠 Nagad", callback_data="add_balance_nagad"))
    bot.send_message(message.chat.id, "Choose your payment method:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "add_balance_shortcut")
def add_balance_shortcut(c):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🟣 Bkash", callback_data="add_balance_bkash"))
    kb.add(InlineKeyboardButton("🟠 Nagad", callback_data="add_balance_nagad"))
    bot.edit_message_text("Choose your payment method:", c.message.chat.id, c.message.message_id, reply_markup=kb)
    bot.answer_callback_query(c.id, "Redirecting to Add Balance section.")

@bot.callback_query_handler(func=lambda c: c.data.startswith("add_balance_"))
def show_payment_details(c):
    method = c.data.split("_")[2].capitalize() # "Bkash" or "Nagad"
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Payment Done ✅", callback_data="send_trx"))
    
    bot.edit_message_text(
        f"নিচের দেওয়া {method} নাম্বারে এ সেন্ড মানি করবেন 👇\n\n`{PAYMENT_NUMBER}`\n\n"
        "Trx Id কপি করে রাখবেন\n\nটাকা পাঠানোর পর Payment Done ✅ এ ক্লিক করুন\n └ TRX ID দিন",
        c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb
    )
    bot.answer_callback_query(c.id, f"Showing {method} payment details.")

@bot.callback_query_handler(func=lambda c: c.data == "send_trx")
def ask_trx(c):
    msg = bot.send_message(c.message.chat.id, "📥 TRX ID দিন", reply_markup=ForceReply())
    bot.register_next_step_handler(msg, save_trx_id)
    bot.answer_callback_query(c.id, "Please send your TRX ID.")

def save_trx_id(message):
    uid = str(message.from_user.id)
    trx = (message.text or "").strip().lower()

    if not re.fullmatch(r"[A-Za-z0-9]+", trx):
        bot.reply_to(message, "❌ Invalid TRX ID format. Please enter a valid Transaction ID.")
        bot.send_message(message.chat.id, "⬅️ Back to menu:", reply_markup=main_menu_markup())
        return
    
    if trx in pending_payments:
        bot.reply_to(message, "⏳ This TRX ID is already pending admin confirmation.")
        bot.send_message(message.chat.id, "⬅️ Back to menu:", reply_markup=main_menu_markup())
        return
    # This check for existing TRX in orders might be redundant or could cause issues if a user
    # tries to use the same TRX for multiple payments (which they shouldn't).
    # if any(trx == order_item.get("trx_id", "").lower() for user_orders in orders.values() for order_item in user_orders):
    #    pass 

    pending_payments[trx] = uid
    data["pending_payments"] = pending_payments

    if trx in unmatched_payments:
        amt = unmatched_payments.pop(trx)
        balances[uid] = round(balances.get(uid, 0.0) + amt, 2)
        data["balances"], data["unmatched_payments"] = balances, unmatched_payments
        save_data(data)
        bot.reply_to(message, f"আপনার ব্যালেন্স সফলভাবে যুক্ত হয়েছে! 🎉\n \t└{amt} TK\n\t└ধন্যবাদ! 💖")
        bot.send_message(ADMIN_ID, f"✅ Auto-confirmed TRX `{trx.upper()}` for user `{uid}`. Amount: {amt} TK", parse_mode="Markdown")
    else:
        save_data(data)
        bot.reply_to(message, "✅ TRX ID received. Awaiting admin confirmation.")
        bot.send_message(ADMIN_ID, f"💳 *Payment Request*\nTRX ID: `{trx.upper()}`\nUser ID: `{uid}`\n\nForward the bKash/Nagad SMS here to confirm.", parse_mode="Markdown")
    
    bot.send_message(message.chat.id, "⬅️ Back to menu:", reply_markup=main_menu_markup())


@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text and 
                                     (("trxid" in m.text.lower() or "txnid" in m.text.lower() or "trnx id" in m.text.lower()) and 
                                      "tk" in m.text.lower() and 
                                      ("received" in m.text.lower() or "prepaid" in m.text.lower() or "cash in" in m.text.lower())))
def admin_bkash_nagad_parser(m):
    txt = (m.text or "").strip()
    trx = parse_trx_id(txt)
    amt = parse_amount(txt)

    if not trx or amt is None:
        bot.reply_to(m, "❌ Could not extract TRX ID or amount from the SMS.")
        return
    
    if trx in pending_payments:
        uid = pending_payments.pop(trx)
        balances[uid] = round(balances.get(uid, 0.0) + amt, 2)
        data["balances"], data["pending_payments"] = balances, pending_payments
        save_data(data)
        bot.send_message(int(uid), f"আপনার ব্যালেন্স সফলভাবে যুক্ত হয়েছে! 🎉:\n\t└ {amt} TK\n\t└Transaction ID: `{trx.upper()}`\n\t└ধন্যবাদ! 💖", parse_mode="Markdown")
        bot.reply_to(m, f"✅ Auto-confirmed.\nUser: `{uid}`\nAmount: {amt} TK\nTRX: `{trx.upper()}`", parse_mode="Markdown")
    elif trx not in unmatched_payments:
        unmatched_payments[trx] = amt
        data["unmatched_payments"] = unmatched_payments
        save_data(data)
        bot.reply_to(m, f"⚠ SMS saved. No pending user request found for TRX ID: `{trx.upper()}`. Will auto-confirm when user provides TRX ID.\nAmount: {amt} TK", parse_mode="Markdown")
    else:
        bot.reply_to(m, f"ℹ️ This TRX ID `{trx.upper()}` is already in unmatched payments.", parse_mode="Markdown")


# ========== ADMIN FEATURES ==========
@bot.message_handler(func=lambda m: norm_text(m.text) == "⬅️ main menu (user)" and str(m.from_user.id) == str(ADMIN_ID))
def back_to_main_menu_admin(message):
    bot.send_message(message.chat.id, "Returning to main user menu.", reply_markup=main_menu_markup())

@bot.message_handler(func=lambda m: norm_text(m.text) == "📊 total sales" and str(m.from_user.id) == str(ADMIN_ID))
def show_total_sales(message):
    bot.send_message(message.chat.id, f"📈 Total Sales Revenue: {total_sales:.2f}৳", reply_markup=admin_menu_markup())

@bot.message_handler(func=lambda m: norm_text(m.text) == "📈 current stock" and str(m.from_user.id) == str(ADMIN_ID))
def show_current_stock(message):
    stock_report = "📦 Current VPN Stock:\n\n"
    has_stock = False
    for vpn_name in sorted(vpn_prices.keys()): # Sort for consistent display
        stock_list = products.get(vpn_name, [])
        stock_report += f"*{vpn_name}:* {len(stock_list)} available\n"
        if len(stock_list) > 0:
            has_stock = True
    
    if not has_stock:
        stock_report += "No VPNs currently in stock."
    
    bot.send_message(message.chat.id, stock_report, parse_mode="Markdown", reply_markup=admin_menu_markup())

@bot.message_handler(func=lambda m: norm_text(m.text) == "➕ add vpn account" and str(m.from_user.id) == str(ADMIN_ID))
def ask_add_vpn_account(message):
    markup = InlineKeyboardMarkup()
    for name in sorted(vpn_prices.keys()): # Sort for consistent display
        markup.add(InlineKeyboardButton(name, callback_data=f"admin_add_vpn|{name}"))
    msg = bot.send_message(message.chat.id, "Which VPN account do you want to add stock for?", reply_markup=markup)
    
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_add_vpn|"))
def admin_selected_vpn_to_add(c):
    vpn_name = c.data.split("|")[1]
    
    # --- MODIFIED: Adjust prompt based on product_fields ---
    prompt_fields = product_fields.get(vpn_name, ["Gmail", "Password"]) # Default to Gmail/Password
    
    prompt_text = f"You selected *{vpn_name}*.\n\nPlease send the VPN account details in the following format:\n\n"
    format_example = ""
    for field in prompt_fields:
        format_example += f"*{field}*:your_{field.lower().replace(' ', '_')}_value\n"
    
    prompt_text += f"`{format_example.strip()}`"

    msg = bot.send_message(c.message.chat.id, prompt_text, parse_mode="Markdown", reply_markup=ForceReply())
    bot.register_next_step_handler(msg, process_add_vpn_account, vpn_name)
    bot.answer_callback_query(c.id, f"Ready to add {vpn_name} account.")


def process_add_vpn_account(message, vpn_name):
    txt = (message.text or "").strip()
    details = {}
    lines = txt.split('\n')
    
    # --- MODIFIED: Parse input based on expected fields ---
    required_fields_for_vpn = product_fields.get(vpn_name, ["Gmail", "Password"]) # Default to Gmail/Password
    
    parsed_count = 0
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            # Standardize key to lowercase and replace spaces with underscores for storage
            standardized_key = key.strip().lower().replace(" ", "_")
            details[standardized_key] = value.strip()
            parsed_count += 1
    
    # Check if all required fields are present
    missing_fields = []
    for field in required_fields_for_vpn:
        standardized_field_key = field.lower().replace(" ", "_")
        if standardized_field_key not in details or not details[standardized_field_key]:
            missing_fields.append(field)

    if missing_fields:
        bot.reply_to(message, f"❌ Invalid format. The following fields are required: {', '.join(missing_fields)}. Please try again.")
        bot.send_message(message.chat.id, "⬅️ Back to Admin Menu:", reply_markup=admin_menu_markup())
        return

    # If all required fields are present, add to products
    products.setdefault(vpn_name, []).append(details) # Store the details dictionary as is
    data["products"] = products
    save_data(data)
    
    bot.reply_to(message, f"✅ Successfully added 1 account for *{vpn_name}* to stock. Current stock: {len(products[vpn_name])}", parse_mode="Markdown")
    bot.send_message(message.chat.id, "⬅️ Back to Admin Menu:", reply_markup=admin_menu_markup())


# ========== ERROR HANDLER ==========
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    uid = str(message.from_user.id)
    if uid == str(ADMIN_ID):
        bot.send_message(message.chat.id, "Did not understand that admin command. Please use the buttons.", reply_markup=admin_menu_markup())
    else:
        bot.send_message(message.chat.id, "I don't understand that command. Please use the menu buttons.", reply_markup=main_menu_markup())


print("Bot polling...")
bot.infinity_polling()