import asyncio
import logging
import secrets
from aiogram import Bot, Dispatcher, F, Router
import os
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

API_TOKEN = "8793973883:AAECdD4SSQ-9Tu7mXv_zAcFu3J1bJgIg7TE"

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

BOT_USERNAME = None  # Заполняется автоматически при запуске

# Настройки
SUPER_ADMIN = 8398088557  # Только этот пользователь может менять фото и название
ADMINS = [8235395380, 770710304, SUPER_ADMIN]  # Суперадмин всегда имеет права админа
BOT_NAME = "LOLZ TEAM"  # Название бота (меняется через /setname в админке)
WELCOME_PHOTO_ID = None  # file_id приветственного фото (устанавливается через /setphoto)
user_success = {770710304: 56, 8235395380: 56, 8398088557: 56}
user_wallets = {}         # user_id: {'type': wallet_type, 'data': wallet_data}
deals = {}                # deal_id: dict
user_deal_count = {}      # user_id: номер последней сделки
referrals = {}  # user_id: referrer_id
banned_users = set()  # забаненные пользователи
promo_keys = {}  # key: None (одноразовые промокоды для получения админки, генерирует только суперадмин)
user_lang = {}  # user_id: 'ru' | 'en'


# ══════════════════════════════════════════════════════════════════
#       Локализация / Localization
# ══════════════════════════════════════════════════════════════════

TEXTS = {
    "ru": {
        "banned": "🚫 Иди нахуй. Ты заблокирован.",
        "welcome": lambda name: (
            f"Добро пожаловать в {name} – надежный P2P-гарант\n\n"
            "💼 Покупайте и продавайте всё, что угодно – безопасно!\n\n"
            "🔹 Управление кошельками\n🔹 Сделки\n🔹 Поддержка\n\n"
            "Выберите нужный раздел ниже:"
        ),
        "btn_wallet": "🪙 Реквизиты",
        "btn_deal": "📄 Создать сделку",
        "btn_ref": "📎 Реф. ссылка",
        "btn_lang": "🌐 Language",
        "btn_support": "📞 Поддержка",
        "btn_back": "🔙 Назад",
        "btn_back_panel": "🔙 Назад в панель",
        "btn_cancel": "❌ Отмена",
        "btn_confirm_pay": "✅ Подтвердить оплату",
        "btn_sent_gift": "✅ Я отправил(а) подарок",
        "btn_cancel_deal": "❌ Отменить сделку",
        "choose_lang": "🌍 Выберите язык:",
        "lang_set": "✅ Язык изменён на Русский 🇷🇺",
        "ref_text": (
            "🔗 Ваша реферальная ссылка:\n<code>{link}</code>\n\n"
            "👥 Приглашено пользователей: <b>{count}</b>\n\n"
            "💎 Реферальная программа:\n"
            "Вы получаете 5% от суммы каждой сделки ваших рефералов.\n\n"
            "Приглашайте друзей и зарабатывайте вместе с нами!"
        ),
        "wallet_current": "💼 Ваши текущие реквизиты: {data} ({wtype})\n\nВыберите тип реквизитов:",
        "wallet_enter_ton": "💎 Введите адрес вашего TON кошелька:",
        "wallet_enter_bep20": "💰 Введите адрес вашего BEP20 (BSC) кошелька (USDT):",
        "wallet_enter_trc20": "💰 Введите адрес вашего TRC20 (TRON) кошелька (USDT):",
        "wallet_enter_card": "💳 Введите реквизиты вашей карты {country}:",
        "wallet_err_ton": "❌ Введите действительный адрес TON кошелька.",
        "wallet_err_bep20": "❌ Введите действительный адрес BEP20 кошелька (начинается с 0x, 42 символа).",
        "wallet_err_trc20": "❌ Введите действительный адрес TRC20 кошелька (начинается с T, 34 символа).",
        "wallet_err_card": "❌ Введите действительные реквизиты карты.",
        "wallet_saved": "✅ Ваши реквизиты ({wtype}) сохранены: {data}",
        "no_wallet": "❌ Вы не указали свои реквизиты.\n\nПожалуйста, сначала добавьте реквизиты.",
        "add_wallet_btn": "➕ Добавить реквизиты",
        "choose_method": "💰 Выберите метод получения оплаты:",
        "stars_enter_username": "⭐ Введите юзернейм Telegram (без @), на который придут звёзды покупателю:",
        "stars_username_err": "❌ Юзернейм должен содержать только буквы, цифры и подчёркивания (минимум 3 символа). Попробуйте ещё раз:",
        "stars_username_saved": "✅ Юзернейм @{username} сохранён.\n\n💰 Теперь введите сумму в формате: 100 {currency}",
        "enter_amount": "💼 Создание сделки\nВведите сумму в формате: 100.5 {currency}",
        "amount_zero": "❌ Сумма должна быть больше нуля. Введите сумму:",
        "amount_err": "❌ Неверный формат суммы. Введите число:",
        "enter_desc": "📝 Опишите, что вы продаете (пример: 10 кепок и пепе):",
        "deal_created": (
            "✅ Сделка создана!\n\n"
            "💰 Сумма: {amount} {currency}\n"
            "📜 Описание: {desc}\n"
            "🔗 Ссылка для покупателя: {link}"
        ),
        "deal_not_found": "❌ Сделка не найдена.",
        "deal_info_card": (
            "💳 Информация о сделке <b>#{deal_id}</b>\n\n"
            "👤 Вы покупатель в сделке.\n"
            "📌 Продавец: <a href=\'tg://user?id={seller_id}\'>@user</a>\n"
            "• Успешные сделки: {success}\n\n"
            "• Вы покупаете: {desc}\n\n"
            "🏦 Адрес для оплаты: <code>{wallet}</code>\n\n"
            "💰 Сумма: {amount} {currency}\n"
            "📝 Комментарий к платежу (мемо): <code>{memo}</code>\n\n"
            "⚠️ Убедитесь в правильности данных перед оплатой. Комментарий обязателен!"
        ),
        "deal_info_stars": (
            "🌟 Информация о сделке со звёздами <b>#{deal_id}</b>\n\n"
            "👤 Вы покупатель в сделке.\n"
            "📌 Продавец: <a href=\'tg://user?id={seller_id}\'>@user</a>\n"
            "• Успешные сделки: {success}\n\n"
            "• Вы покупаете: {desc}\n\n"
            "💰 Сумма: {amount} {currency}\n\n"
            "⭐ Звёзды придут на аккаунт: <b>@{stars_username}</b>\n"
            "После подтверждения оплаты продавец получит уведомление."
        ),
        "seller_notified_join": (
            "👤 Пользователь <a href=\'tg://user?id={buyer_id}\'>перешёл</a> по сделке #{deal_id}\n"
            "• Успешные сделки: {success}\n\n"
            "⚠️ Проверьте, что это тот же пользователь, с которым вы общались."
        ),
        "payment_confirmed_buyer": (
            "✅ Оплата подтверждена для сделки <b>#{deal_id}</b>\n"
            "Ожидайте подтверждения от продавца."
        ),
        "seller_msg_stars": (
            "✅ Оплата звёздами подтверждена в боте.\n\n"
            "🎁 Отправьте подарок покупателю.\n"
            "⭐ Для сделок со звёздами реквизиты не требуются.\n\n"
            "Бот проверяет наличие скрина. Модератор получает уведомление."
        ),
        "seller_msg_card": (
            "✅ Оплата заморожена в боте.\n\n"
            "🎁 Отправьте подарок покупателю.\n"
            "📸 Сделайте скрин и отправьте его в чат с ботом.\n\n"
            "Бот проверяет наличие скрина. Модератор получает уведомление."
        ),
        "deal_done_seller": (
            "✅ Сделка #{deal_id} успешно завершена!\n\n"
            "💰 Вы получили: {amount} {currency}\n"
            "📦 Товар: {desc}\n\n"
            "Спасибо за использование нашего сервиса!"
        ),
        "deal_done_buyer": (
            "✅ Сделка #{deal_id} успешно завершена!\n\n"
            "💰 Вы оплатили: {amount} {currency}\n"
            "📦 Товар: {desc}\n\n"
            "Если у вас есть вопросы, обратитесь в поддержку."
        ),
        "deal_sent_confirm": "⏳ Вы подтвердили отправку. Ожидаем подтверждения от покупателя...",
        "buyer_received_question": (
            "🎁 Продавец утверждает, что отправил вам подарок по сделке <b>#{deal_id}</b>.\n\n"
            "Вы получили подарок?"
        ),
        "btn_buyer_yes": "✅ Да, получил(а)",
        "btn_buyer_no": "❌ Нет, не получил(а)",
        "buyer_confirmed_received": "✅ Отлично! Сделка завершена. Спасибо!",
        "buyer_denied_received": "❌ Вы сообщили, что подарок не получен. Продавцу отправлено повторное уведомление.",
        "seller_resend_gift": (
            "⚠️ Покупатель сообщает, что НЕ получил подарок по сделке <b>#{deal_id}</b>.\n\n"
            "🎁 Пожалуйста, отправьте подарок покупателю и нажмите кнопку ещё раз."
        ),
        "deal_cancel_seller": (
            "❌ Сделка #{deal_id} отменена.\n\n"
            "💰 Сумма: {amount} {currency}\nПокупатель получит возврат средств."
        ),
        "deal_cancel_buyer": (
            "❌ Сделка #{deal_id} отменена продавцом.\n\n"
            "💰 Сумма: {amount} {currency} будет возвращена вам.\n"
            "Если возврат не поступил, обратитесь в поддержку."
        ),
        "deal_cancel_confirm": "❌ Вы отменили сделку. Покупатель получит возврат.",
        "self_ref": "❌ Нельзя пригласить самого себя.",
        "already_ref": "⚠️ Вы уже использовали реферальную ссылку.",
        "new_ref_notify": (
            "👤 Новый реферал: <a href=\'tg://user?id={uid}\'>пользователь</a>\n"
            "Всего рефералов: {count}"
        ),
        "ref_cmd_text": (
            "🔗 Ваша реферальная ссылка:\n<code>{link}</code>\n\n"
            "👥 Приглашено пользователей: <b>{count}</b>"
        ),
        "admin_only": "⛔ Неизвестно.",
        "s_no_id": "⚠️ Укажи ID сделки после /s",
        "s_confirmed": "✅ Сделка <b>#{deal_id}</b> подтверждена.\nПродавец получил инструкции.",
        "s_buyer_notify": "✅ Ваша сделка <b>#{deal_id}</b> подтверждена админом.\nОжидайте выполнения от продавца.",
        "photo_set": (
            "✅ Приветственное фото установлено!\n\n"
            "Теперь при /start и возврате в меню будет отображаться это фото.\n"
            "Чтобы убрать фото — используй /chochak → 🗑 Удалить фото"
        ),
        "unban_notify": "✅ Ваша блокировка снята. Добро пожаловать обратно!",
        "btn_my_deals": "📋 Мои сделки",
        "my_deals_empty": "📭 У вас пока нет сделок.",
        "my_deals_header": "📋 <b>Ваши сделки:</b>\n\n",
        "my_deals_as_seller": "🟢 <b>Продавец</b>",
        "my_deals_as_buyer": "🔵 <b>Покупатель</b>",
        "my_deals_status_open": "⏳ Открыта",
        "my_deals_status_paid": "💰 Оплачена",
        "my_deals_status_done": "✅ Завершена",
        "my_deals_status_cancelled": "❌ Отменена",
    },
    "en": {
        "banned": "🚫 You are banned.",
        "welcome": lambda name: (
            f"Welcome to {name} – trusted P2P escrow\n\n"
            "💼 Buy and sell anything – safely!\n\n"
            "🔹 Wallet management\n🔹 Deals\n🔹 Support\n\n"
            "Choose a section below:"
        ),
        "btn_wallet": "🪙 Add details",
        "btn_deal": "📄 Create a deal",
        "btn_ref": "📎 Referral link",
        "btn_lang": "🌐 Язык",
        "btn_support": "📞 Support",
        "btn_back": "🔙 Back",
        "btn_back_panel": "🔙 Back to panel",
        "btn_cancel": "❌ Cancel",
        "btn_confirm_pay": "✅ Confirm payment",
        "btn_sent_gift": "✅ I sent the gift",
        "btn_cancel_deal": "❌ Cancel deal",
        "choose_lang": "🌍 Choose language:",
        "lang_set": "✅ Language set to English 🇬🇧",
        "ref_text": (
            "🔗 Your referral link:\n<code>{link}</code>\n\n"
            "👥 Users invited: <b>{count}</b>\n\n"
            "💎 Referral program:\n"
            "You earn 5% of every deal your referrals make.\n\n"
            "Invite friends and earn together!"
        ),
        "wallet_current": "💼 Your current payment details: {data} ({wtype})\n\nChoose payment type:",
        "wallet_enter_ton": "💎 Enter your TON wallet address:",
        "wallet_enter_bep20": "💰 Enter your BEP20 (BSC) wallet address (USDT):",
        "wallet_enter_trc20": "💰 Enter your TRC20 (TRON) wallet address (USDT):",
        "wallet_enter_card": "💳 Enter your {country} card details:",
        "wallet_err_ton": "❌ Please enter a valid TON wallet address.",
        "wallet_err_bep20": "❌ Please enter a valid BEP20 wallet address (starts with 0x, 42 chars).",
        "wallet_err_trc20": "❌ Please enter a valid TRC20 wallet address (starts with T, 34 chars).",
        "wallet_err_card": "❌ Please enter valid card details.",
        "wallet_saved": "✅ Your payment details ({wtype}) saved: {data}",
        "no_wallet": "❌ You haven\'t added payment details yet.\n\nPlease add them first.",
        "add_wallet_btn": "➕ Add payment details",
        "choose_method": "💰 Choose a payment method:",
        "stars_enter_username": "⭐ Enter the Telegram username (without @) where stars will be sent to the buyer:",
        "stars_username_err": "❌ Username must contain only letters, digits and underscores (minimum 3 chars). Try again:",
        "stars_username_saved": "✅ Username @{username} saved.\n\n💰 Now enter the amount: 100 {currency}",
        "enter_amount": "💼 Creating a deal\nEnter the amount: 100.5 {currency}",
        "amount_zero": "❌ Amount must be greater than zero. Enter amount:",
        "amount_err": "❌ Invalid amount format. Enter a number:",
        "enter_desc": "📝 Describe what you are selling (e.g. 10 hats and pepe):",
        "deal_created": (
            "✅ Deal created!\n\n"
            "💰 Amount: {amount} {currency}\n"
            "📜 Description: {desc}\n"
            "🔗 Buyer link: {link}"
        ),
        "deal_not_found": "❌ Deal not found.",
        "deal_info_card": (
            "💳 Deal info <b>#{deal_id}</b>\n\n"
            "👤 You are the buyer.\n"
            "📌 Seller: <a href=\'tg://user?id={seller_id}\'>@user</a>\n"
            "• Successful deals: {success}\n\n"
            "• You are buying: {desc}\n\n"
            "🏦 Payment address: <code>{wallet}</code>\n\n"
            "💰 Amount: {amount} {currency}\n"
            "📝 Payment comment (memo): <code>{memo}</code>\n\n"
            "⚠️ Double-check all details before paying. Comment is required!"
        ),
        "deal_info_stars": (
            "🌟 Stars deal info <b>#{deal_id}</b>\n\n"
            "👤 You are the buyer.\n"
            "📌 Seller: <a href=\'tg://user?id={seller_id}\'>@user</a>\n"
            "• Successful deals: {success}\n\n"
            "• You are buying: {desc}\n\n"
            "💰 Amount: {amount} {currency}\n\n"
            "⭐ Stars will be sent to: <b>@{stars_username}</b>\n"
            "The seller will be notified once payment is confirmed."
        ),
        "seller_notified_join": (
            "👤 User <a href=\'tg://user?id={buyer_id}\'>opened</a> deal #{deal_id}\n"
            "• Successful deals: {success}\n\n"
            "⚠️ Make sure this is the same person you were talking to."
        ),
        "payment_confirmed_buyer": (
            "✅ Payment confirmed for deal <b>#{deal_id}</b>\n"
            "Awaiting seller\'s confirmation."
        ),
        "seller_msg_stars": (
            "✅ Stars payment confirmed in the bot.\n\n"
            "🎁 Send the gift to the buyer.\n"
            "⭐ No payment details required for Stars deals.\n\n"
            "The bot checks for a screenshot. A moderator is notified."
        ),
        "seller_msg_card": (
            "✅ Payment frozen in the bot.\n\n"
            "🎁 Send the gift to the buyer.\n"
            "📸 Take a screenshot and send it in the bot chat.\n\n"
            "The bot checks for a screenshot. A moderator is notified."
        ),
        "deal_done_seller": (
            "✅ Deal #{deal_id} completed successfully!\n\n"
            "💰 You received: {amount} {currency}\n"
            "📦 Item: {desc}\n\n"
            "Thank you for using our service!"
        ),
        "deal_done_buyer": (
            "✅ Deal #{deal_id} completed successfully!\n\n"
            "💰 You paid: {amount} {currency}\n"
            "📦 Item: {desc}\n\n"
            "If you have any questions, contact support."
        ),
        "deal_sent_confirm": "⏳ You confirmed the delivery. Waiting for buyer confirmation...",
        "buyer_received_question": (
            "🎁 The seller claims to have sent you the gift for deal <b>#{deal_id}</b>.\n\n"
            "Did you receive the gift?"
        ),
        "btn_buyer_yes": "✅ Yes, I received it",
        "btn_buyer_no": "❌ No, I didn't receive it",
        "buyer_confirmed_received": "✅ Great! Deal completed. Thank you!",
        "buyer_denied_received": "❌ You reported the gift was not received. The seller has been notified again.",
        "seller_resend_gift": (
            "⚠️ The buyer reports they did NOT receive the gift for deal <b>#{deal_id}</b>.\n\n"
            "🎁 Please send the gift to the buyer and press the button again."
        ),
        "deal_cancel_seller": (
            "❌ Deal #{deal_id} cancelled.\n\n"
            "💰 Amount: {amount} {currency}\nThe buyer will receive a refund."
        ),
        "deal_cancel_buyer": (
            "❌ Deal #{deal_id} was cancelled by the seller.\n\n"
            "💰 Amount: {amount} {currency} will be refunded to you.\n"
            "If the refund doesn\'t arrive, contact support."
        ),
        "deal_cancel_confirm": "❌ You cancelled the deal. The buyer will receive a refund.",
        "self_ref": "❌ You cannot invite yourself.",
        "already_ref": "⚠️ You have already used a referral link.",
        "new_ref_notify": (
            "👤 New referral: <a href=\'tg://user?id={uid}\'>user</a>\n"
            "Total referrals: {count}"
        ),
        "ref_cmd_text": (
            "🔗 Your referral link:\n<code>{link}</code>\n\n"
            "👥 Users invited: <b>{count}</b>"
        ),
        "admin_only": "⛔ Unknown.",
        "s_no_id": "⚠️ Specify deal ID after /s",
        "s_confirmed": "✅ Deal <b>#{deal_id}</b> confirmed.\nSeller received instructions.",
        "s_buyer_notify": "✅ Your deal <b>#{deal_id}</b> confirmed by admin.\nAwaiting fulfilment from the seller.",
        "photo_set": (
            "✅ Welcome photo set!\n\n"
            "It will now appear on /start and when returning to the menu.\n"
            "To remove it — use /chochak → 🗑 Delete photo"
        ),
        "unban_notify": "✅ Your ban has been lifted. Welcome back!",
        "btn_my_deals": "📋 My deals",
        "my_deals_empty": "📭 You have no deals yet.",
        "my_deals_header": "📋 <b>Your deals:</b>\n\n",
        "my_deals_as_seller": "🟢 <b>Seller</b>",
        "my_deals_as_buyer": "🔵 <b>Buyer</b>",
        "my_deals_status_open": "⏳ Open",
        "my_deals_status_paid": "💰 Paid",
        "my_deals_status_done": "✅ Completed",
        "my_deals_status_cancelled": "❌ Cancelled",
    }
}

def get_lang(user_id: int) -> str:
    return user_lang.get(user_id, "ru")

def T(user_id: int, key: str, **kwargs) -> str:
    lang = get_lang(user_id)
    text = TEXTS[lang].get(key, TEXTS["ru"].get(key, key))
    if callable(text):
        return text(**kwargs) if kwargs else text()
    return text.format(**kwargs) if kwargs else text

# Проверка бана
def is_banned(user_id: int) -> bool:
    return user_id in banned_users

# Валюты для разных стран
CURRENCIES = {
    "card_ru": "🇷🇺 RUB",
    "card_ua": "🇺🇦 UAH", 
    "card_uz": "🇺🇿 UZS",
    "card_by": "🇧🇾 BYN",
    "card_kz": "🇰🇿 KZT",
    "card_eu": "🇪🇺 EUR",
    "ton": "💎 TON",
    "bep20": "💰 USDT (BEP20)",
    "trc20": "💰 USDT (TRC20)",
    "stars": "🌟 Stars"
}

# Состояния
class Form(StatesGroup):
    wallet_type = State()
    wallet_data = State()
    deal_method = State()
    deal_stars_username = State()   # ← юзернейм для звёзд
    deal_amount = State()
    deal_description = State()

# Состояния суперадмин панели
class SuperAdminForm(StatesGroup):
    waiting_new_name = State()
    waiting_new_photo = State()
    waiting_ban_id = State()
    waiting_unban_id = State()

# Состояния обращений
class AppealForm(StatesGroup):
    waiting_suggestion = State()
    waiting_complaint = State()

# Главное меню
def main_menu(user_id: int = 0):
    lang = get_lang(user_id)
    tx = TEXTS[lang]
    builder = InlineKeyboardBuilder()
    # Ряд 1: Создать сделку (по середине)
    builder.button(text=tx["btn_deal"], callback_data="create_deal")
    # Ряд 2: Добавить реквизиты | Мои сделки
    builder.button(text=tx["btn_wallet"], callback_data="edit_wallet")
    builder.button(text=tx["btn_my_deals"], callback_data="my_deals")
    # Ряд 3: Change Language | Реферальная ссылка
    builder.button(text=tx["btn_lang"], callback_data="change_lang")
    builder.button(text=tx["btn_ref"], callback_data="referral_link")
    # Ряд 4: Обращения | О сервисе
    builder.button(text="📝 Обращения", callback_data="appeals_menu")
    builder.button(text="ℹ️ О сервисе", callback_data="about_service")
    # Ряд 5: Поддержка (по середине)
    builder.button(text=tx["btn_support"], url="https://t.me/Zolotov")
    builder.adjust(1, 2, 2, 2, 1)
    return builder.as_markup()

#рефка
@router.callback_query(F.data == "referral_link")
async def show_referral_link(call: CallbackQuery):
    user_id = call.from_user.id
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    ref_count = sum(1 for ref in referrals.values() if ref == user_id)
    
    text = T(user_id, "ref_text", link=link, count=ref_count)
    kb = InlineKeyboardBuilder()
    kb.button(text=T(user_id, "btn_back"), callback_data="back_to_menu")
    await safe_edit_or_resend(call, text, reply_markup=kb.as_markup())

# Мои сделки
STATUS_LABELS = {
    "open":      ("my_deals_status_open",),
    "paid":      ("my_deals_status_paid",),
    "done":      ("my_deals_status_done",),
    "cancelled": ("my_deals_status_cancelled",),
}

def get_deal_status_key(deal: dict) -> str:
    if deal.get("cancelled"):
        return "my_deals_status_cancelled"
    if deal.get("done"):
        return "my_deals_status_done"
    if deal.get("payment_confirmed"):
        return "my_deals_status_paid"
    return "my_deals_status_open"

@router.callback_query(F.data == "my_deals")
async def show_my_deals(call: CallbackQuery):
    uid = call.from_user.id

    # Собираем сделки, где пользователь — продавец или покупатель
    user_deals = []
    for deal_id, deal in deals.items():
        role = None
        if deal.get("seller_id") == uid:
            role = "seller"
        elif deal.get("buyer_id") == uid:
            role = "buyer"
        if role:
            user_deals.append((deal_id, deal, role))

    if not user_deals:
        kb = InlineKeyboardBuilder()
        kb.button(text=T(uid, "btn_back"), callback_data="back_to_menu")
        await safe_edit_or_resend(call, T(uid, "my_deals_empty"), reply_markup=kb.as_markup())
        return

    # Сортируем: сначала открытые, потом оплаченные, завершённые, отменённые
    order = {"my_deals_status_open": 0, "my_deals_status_paid": 1,
             "my_deals_status_done": 2, "my_deals_status_cancelled": 3}
    user_deals.sort(key=lambda x: order.get(get_deal_status_key(x[1]), 9))

    lang = get_lang(uid)
    text = T(uid, "my_deals_header")

    for deal_id, deal, role in user_deals:
        status_key = get_deal_status_key(deal)
        status_label = TEXTS[lang][status_key]
        role_label = TEXTS[lang]["my_deals_as_seller"] if role == "seller" else TEXTS[lang]["my_deals_as_buyer"]
        amount = deal.get("amount", "?")
        currency = deal.get("currency", "")
        desc = deal.get("description", "—")
        # Обрезаем описание если слишком длинное
        if len(desc) > 40:
            desc = desc[:37] + "..."
        text += (
            f"🔹 Сделка <b>#{deal_id}</b>\n"
            f"   {role_label} | {status_label}\n"
            f"   💰 {amount} {currency}\n"
            f"   📦 {desc}\n\n"
        )

    kb = InlineKeyboardBuilder()
    kb.button(text=T(uid, "btn_back"), callback_data="back_to_menu")
    await safe_edit_or_resend(call, text, reply_markup=kb.as_markup())

# Меню выбора типа реквизитов
def wallet_type_menu(user_id: int = 0):
    lang = get_lang(user_id)
    back = TEXTS[lang]["btn_back"]
    builder = InlineKeyboardBuilder()
    builder.button(text="💰BEP20", callback_data="wallet_bep20")
    builder.button(text="💰TRC20", callback_data="wallet_trc20")
    builder.button(text="🇰🇿 Карта (KZ)", callback_data="wallet_card_kz")
    builder.button(text="🇷🇺 Карта (RU)", callback_data="wallet_card_ru")
    builder.button(text="🇺🇦 Карта (UA)", callback_data="wallet_card_ua")
    builder.button(text="🇺🇿 Карта (UZ)", callback_data="wallet_card_uz")
    builder.button(text="🇧🇾 Карта (BY)", callback_data="wallet_card_by")
    builder.button(text="🇪🇺 Карта (EU)", callback_data="wallet_card_eu")
    builder.button(text="💎 TON", callback_data="wallet_ton")
    builder.button(text=back, callback_data="back_to_menu")
    builder.adjust(2, 2, 2, 2, 1, 1)
    return builder.as_markup()

# Назад
def back_menu(user_id: int = 0):
    lang = get_lang(user_id)
    builder = InlineKeyboardBuilder()
    builder.button(text=TEXTS[lang]["btn_back"], callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()

# Методы сделки
def deal_methods(user_id: int = 0):
    lang = get_lang(user_id)
    back = TEXTS[lang]["btn_back"]
    builder = InlineKeyboardBuilder()
    # Ряд 1: BEP20 | TRC20
    builder.button(text="💰 BEP20 (USDT)", callback_data="deal_bep20")
    builder.button(text="💰 TRC20 (USDT)", callback_data="deal_trc20")
    # Ряд 2: Card | Stars
    builder.button(text="💳 Card", callback_data="deal_card")
    builder.button(text="🌟 Stars", callback_data="deal_stars")
    # Ряд 3: TON по середине
    builder.button(text="💎 TON", callback_data="deal_ton")
    # Ряд 4: Назад
    builder.button(text=back, callback_data="back_to_menu")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()

# Языки
def lang_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Русский", callback_data="lang_ru")
    builder.button(text="🇬🇧 English", callback_data="lang_en")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()

# Безопасная функция редактирования или пересылки
async def safe_edit_or_resend(call: CallbackQuery, text: str, reply_markup=None):
    if call.message.text:
        await call.message.edit_text(text, reply_markup=reply_markup)
    else:
        await call.message.answer(text, reply_markup=reply_markup)
        await call.message.delete()

# Функция уведомления всех участников сделки
async def notify_all_deal_parties(deal_id: str, message_text: str, include_admins=False):
    deal = deals.get(deal_id)
    if not deal:
        return False
    
    seller_id = deal["seller_id"]
    buyer_id = deal.get("buyer_id")
    
    try:
        await bot.send_message(seller_id, message_text)
    except Exception as e:
        logging.error(f"Не удалось уведомить продавца {seller_id}: {e}")
    
    if buyer_id and buyer_id != seller_id:
        try:
            await bot.send_message(buyer_id, message_text)
        except Exception as e:
            logging.error(f"Не удалось уведомить покупателя {buyer_id}: {e}")
    
    if include_admins:
        for admin_id in ADMINS:
            if admin_id not in [seller_id, buyer_id]:
                try:
                    await bot.send_message(admin_id, f"Сделка #{deal_id}\n" + message_text)
                except Exception as e:
                    logging.error(f"Не удалось уведомить админа {admin_id}: {e}")
    
    return True

# Старт
def welcome_text(user_id: int = 0):
    lang = get_lang(user_id)
    return TEXTS[lang]["welcome"](BOT_NAME)

@router.message(F.text.startswith("/start"))
async def start_handler(message: Message):
    uid = message.from_user.id
    if is_banned(uid):
        await message.answer(T(uid, "banned"))
        return

    text = message.text.strip()
    parts = text.split(" ", 1)

    # Обработка deep link: /start deal_xxx
    if len(parts) > 1 and parts[1].startswith("deal_"):
        payload = parts[1].strip()
        deal = deals.get(payload)
        if not deal:
            await message.answer("❌ Сделка не найдена.")
            return
        seller_id = deal["seller_id"]
        description = deal["description"]
        amount = deal["amount"]
        currency = deal["currency"]
        method = deal.get("method", "deal_card")
        if method == "deal_stars":
            wallet = "🌟 Оплата звёздами - реквизиты не требуются"
            memo = "Оплата звёздами"
        else:
            wallet = user_wallets.get(seller_id, {}).get('data', "❌ Нет реквизитов")
            memo = f"{seller_id}{user_deal_count.get(seller_id, 0)}"
        deal_number = payload
        seller_success = user_success.get(seller_id, 56) if seller_id in ADMINS else user_success.get(seller_id, 0)
        if uid != seller_id:
            deals[payload]["buyer_id"] = uid
            seller_lang = get_lang(seller_id)
            buyer_success = user_success.get(uid, 56) if uid in ADMINS else user_success.get(uid, 0)
            seller_notify = TEXTS[seller_lang]["seller_notified_join"].format(
                buyer_id=uid, deal_id=deal_number, success=buyer_success
            )
            try:
                await bot.send_message(seller_id, seller_notify)
            except Exception as e:
                logging.error(f"Не удалось уведомить продавца: {e}")
        if method == "deal_stars":
            stars_username = deal.get("stars_username") or "не указан"
            text_msg = T(uid, "deal_info_stars",
                     deal_id=deal_number, seller_id=seller_id, success=seller_success,
                     desc=description, amount=amount, currency=currency,
                     stars_username=stars_username)
        else:
            text_msg = T(uid, "deal_info_card",
                     deal_id=deal_number, seller_id=seller_id, success=seller_success,
                     desc=description, wallet=wallet, amount=amount, currency=currency, memo=memo)
        kb = InlineKeyboardBuilder()
        if uid in ADMINS:
            kb.button(text=T(uid, "btn_confirm_pay"), callback_data=f"confirm_{deal_number}")
        kb.button(text=T(uid, "btn_back"), callback_data="back_to_menu")
        kb.adjust(1)
        await message.answer(text_msg, reply_markup=kb.as_markup())
        return

    # Обработка deep link: /start ref_xxx
    if len(parts) > 1 and parts[1].startswith("ref_"):
        ref_data = parts[1].strip()
        try:
            ref_id = int(ref_data.replace("ref_", ""))
        except ValueError:
            pass
        else:
            if uid == ref_id:
                await message.answer(T(uid, "self_ref"))
            elif uid in referrals:
                await message.answer(T(uid, "already_ref"))
            else:
                referrals[uid] = ref_id
                if ref_id in ADMINS:
                    ref_count = sum(1 for r in referrals.values() if r == ref_id)
                    ref_lang = get_lang(ref_id)
                    try:
                        await bot.send_message(ref_id, TEXTS[ref_lang]["new_ref_notify"].format(uid=uid, count=ref_count))
                    except Exception:
                        pass

    # Обычный /start
    if WELCOME_PHOTO_ID:
        await message.answer_photo(photo=WELCOME_PHOTO_ID, caption=welcome_text(uid), reply_markup=main_menu(uid))
    else:
        await message.answer(welcome_text(uid), reply_markup=main_menu(uid))

# ══════════════════════════════════════════════════════
#              👑 СУПЕРАДМИН ПАНЕЛЬ /chochak
# ══════════════════════════════════════════════════════

def superadmin_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить название бота", callback_data="sa_setname")
    builder.button(text="🖼 Установить фото", callback_data="sa_setphoto")
    builder.button(text="🗑 Удалить фото", callback_data="sa_removephoto")
    builder.button(text="🔨 Заблокировать юзера", callback_data="sa_ban")
    builder.button(text="✅ Разблокировать юзера", callback_data="sa_unban")
    builder.button(text="📋 Список банов", callback_data="sa_banlist")
    builder.button(text="📊 Статистика бота", callback_data="sa_stats")
    builder.button(text="🔑 Генерировать промокод (админ)", callback_data="sa_gen_promo")
    builder.adjust(1)
    return builder.as_markup()

def sa_back_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад в панель", callback_data="sa_panel")
    builder.adjust(1)
    return builder.as_markup()

def sa_cancel_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="sa_panel")
    builder.adjust(1)
    return builder.as_markup()

@router.message(F.text == "/chochak")
async def superadmin_panel(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN:
        await message.answer("⛔ Нет доступа.")
        return
    await state.clear()
    await message.answer(
        f"👑 <b>СУПЕРАДМИН ПАНЕЛЬ</b>\n\n"
        f"🤖 Название бота: <b>{BOT_NAME}</b>\n"
        f"🖼 Приветственное фото: {'✅ Установлено' if WELCOME_PHOTO_ID else '❌ Не установлено'}\n"
        f"🔨 Забанено пользователей: <b>{len(banned_users)}</b>\n"
        f"💼 Активных сделок: <b>{len(deals)}</b>\n"
        f"👥 Всего рефералов: <b>{len(referrals)}</b>\n\n"
        f"Выбери действие:",
        reply_markup=superadmin_menu()
    )

# Возврат в панель через кнопку
@router.callback_query(F.data == "sa_panel")
async def sa_panel_callback(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != SUPER_ADMIN:
        await call.answer("⛔ Нет доступа.", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text(
        f"👑 <b>СУПЕРАДМИН ПАНЕЛЬ</b>\n\n"
        f"🤖 Название бота: <b>{BOT_NAME}</b>\n"
        f"🖼 Приветственное фото: {'✅ Установлено' if WELCOME_PHOTO_ID else '❌ Не установлено'}\n"
        f"🔨 Забанено пользователей: <b>{len(banned_users)}</b>\n"
        f"💼 Активных сделок: <b>{len(deals)}</b>\n"
        f"👥 Всего рефералов: <b>{len(referrals)}</b>\n\n"
        f"Выбери действие:",
        reply_markup=superadmin_menu()
    )

# ── /setname ──
@router.callback_query(F.data == "sa_setname")
async def sa_setname_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != SUPER_ADMIN:
        await call.answer("⛔ Нет доступа.", show_alert=True)
        return
    await call.message.edit_text(
        f"✏️ <b>Изменение названия бота</b>\n\n"
        f"Текущее название: <b>{BOT_NAME}</b>\n\n"
        f"Введи новое название:",
        reply_markup=sa_cancel_kb()
    )
    await state.set_state(SuperAdminForm.waiting_new_name)

@router.message(SuperAdminForm.waiting_new_name)
async def sa_setname_input(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN:
        return
    global BOT_NAME
    old_name = BOT_NAME
    BOT_NAME = message.text.strip().upper()
    await state.clear()
    await message.answer(
        f"✅ <b>Название изменено!</b>\n\n"
        f"Было: <b>{old_name}</b>\n"
        f"Стало: <b>{BOT_NAME}</b>",
        reply_markup=sa_back_kb()
    )

# ── /setphoto ──
@router.callback_query(F.data == "sa_setphoto")
async def sa_setphoto_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != SUPER_ADMIN:
        await call.answer("⛔ Нет доступа.", show_alert=True)
        return
    await call.message.edit_text(
        "🖼 <b>Установка приветственного фото</b>\n\n"
        "Отправь фото, которое будет показываться при /start:",
        reply_markup=sa_cancel_kb()
    )
    await state.set_state(SuperAdminForm.waiting_new_photo)

@router.message(SuperAdminForm.waiting_new_photo, F.photo)
async def sa_setphoto_input(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN:
        return
    global WELCOME_PHOTO_ID
    WELCOME_PHOTO_ID = message.photo[-1].file_id
    await state.clear()
    await message.answer(
        "✅ <b>Приветственное фото установлено!</b>\n\n"
        "Теперь при /start будет отображаться это фото.",
        reply_markup=sa_back_kb()
    )

@router.message(SuperAdminForm.waiting_new_photo)
async def sa_setphoto_wrong(message: Message):
    if message.from_user.id != SUPER_ADMIN:
        return
    await message.answer("❌ Это не фото. Отправь изображение:", reply_markup=sa_cancel_kb())

# ── removephoto ──
@router.callback_query(F.data == "sa_removephoto")
async def sa_removephoto(call: CallbackQuery):
    if call.from_user.id != SUPER_ADMIN:
        await call.answer("⛔ Нет доступа.", show_alert=True)
        return
    global WELCOME_PHOTO_ID
    if not WELCOME_PHOTO_ID:
        await call.answer("⚠️ Фото и так не установлено.", show_alert=True)
        return
    WELCOME_PHOTO_ID = None
    await call.message.edit_text(
        "✅ <b>Приветственное фото удалено.</b>",
        reply_markup=sa_back_kb()
    )

# ── /ban ──
@router.callback_query(F.data == "sa_ban")
async def sa_ban_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != SUPER_ADMIN:
        await call.answer("⛔ Нет доступа.", show_alert=True)
        return
    banned_list = ""
    if banned_users:
        banned_list = "\n\n🔨 Уже забанены:\n" + "\n".join(f"• <code>{uid}</code>" for uid in list(banned_users)[:10])
    await call.message.edit_text(
        f"🔨 <b>Блокировка пользователя</b>{banned_list}\n\n"
        f"Введи <b>ID пользователя</b> для бана:",
        reply_markup=sa_cancel_kb()
    )
    await state.set_state(SuperAdminForm.waiting_ban_id)

@router.message(SuperAdminForm.waiting_ban_id)
async def sa_ban_input(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN:
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введи корректный числовой ID:", reply_markup=sa_cancel_kb())
        return
    if target_id == SUPER_ADMIN:
        await message.answer("❌ Нельзя забанить самого себя, умник.", reply_markup=sa_cancel_kb())
        return
    await state.clear()
    if target_id in banned_users:
        await message.answer(
            f"⚠️ Пользователь <code>{target_id}</code> уже забанен.",
            reply_markup=sa_back_kb()
        )
        return
    banned_users.add(target_id)
    try:
        await bot.send_message(target_id, T(target_id, "banned"))
    except Exception:
        pass
    await message.answer(
        f"🔨 <b>Пользователь <code>{target_id}</code> заблокирован!</b>",
        reply_markup=sa_back_kb()
    )

# ── /unban ──
@router.callback_query(F.data == "sa_unban")
async def sa_unban_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != SUPER_ADMIN:
        await call.answer("⛔ Нет доступа.", show_alert=True)
        return
    if not banned_users:
        await call.answer("✅ Список банов пуст — некого разбанивать.", show_alert=True)
        return
    banned_list = "\n".join(f"• <code>{uid}</code>" for uid in banned_users)
    await call.message.edit_text(
        f"✅ <b>Разблокировка пользователя</b>\n\n"
        f"🔨 Забаненные:\n{banned_list}\n\n"
        f"Введи <b>ID пользователя</b> для разбана:",
        reply_markup=sa_cancel_kb()
    )
    await state.set_state(SuperAdminForm.waiting_unban_id)

@router.message(SuperAdminForm.waiting_unban_id)
async def sa_unban_input(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN:
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введи корректный числовой ID:", reply_markup=sa_cancel_kb())
        return
    await state.clear()
    if target_id not in banned_users:
        await message.answer(
            f"⚠️ Пользователь <code>{target_id}</code> не был забанен.",
            reply_markup=sa_back_kb()
        )
        return
    banned_users.discard(target_id)
    try:
        await bot.send_message(target_id, T(target_id, "unban_notify"))
    except Exception:
        pass
    await message.answer(
        f"✅ <b>Пользователь <code>{target_id}</code> разблокирован!</b>",
        reply_markup=sa_back_kb()
    )

# ── banlist ──
@router.callback_query(F.data == "sa_banlist")
async def sa_banlist(call: CallbackQuery):
    if call.from_user.id != SUPER_ADMIN:
        await call.answer("⛔ Нет доступа.", show_alert=True)
        return
    if not banned_users:
        await call.message.edit_text(
            "✅ <b>Список банов пуст.</b>",
            reply_markup=sa_back_kb()
        )
        return
    ids = "\n".join(f"• <code>{uid}</code>" for uid in banned_users)
    await call.message.edit_text(
        f"🔨 <b>Забаненные пользователи ({len(banned_users)}):</b>\n\n{ids}",
        reply_markup=sa_back_kb()
    )

# ── stats ──
@router.callback_query(F.data == "sa_stats")
async def sa_stats(call: CallbackQuery):
    if call.from_user.id != SUPER_ADMIN:
        await call.answer("⛔ Нет доступа.", show_alert=True)
        return
    total_deals = sum(user_deal_count.values())
    active_deals = len(deals)
    total_referrals = len(referrals)
    total_banned = len(banned_users)
    total_admins = len(ADMINS)
    total_wallets = len(user_wallets)

    await call.message.edit_text(
        f"📊 <b>СТАТИСТИКА БОТА</b>\n\n"
        f"🤖 Название: <b>{BOT_NAME}</b>\n"
        f"🖼 Фото: {'✅ Установлено' if WELCOME_PHOTO_ID else '❌ Нет'}\n\n"
        f"💼 Активных сделок: <b>{active_deals}</b>\n"
        f"📈 Всего создано сделок: <b>{total_deals}</b>\n"
        f"🪙 Юзеров с реквизитами: <b>{total_wallets}</b>\n"
        f"👥 Рефералов: <b>{total_referrals}</b>\n"
        f"🛡 Админов: <b>{total_admins}</b>\n"
        f"🔨 Забанено: <b>{total_banned}</b>",
        reply_markup=sa_back_kb()
    )

# ── Генерация промокода ──
@router.callback_query(F.data == "sa_gen_promo")
async def sa_gen_promo(call: CallbackQuery):
    if call.from_user.id != SUPER_ADMIN:
        await call.answer("⛔ Нет доступа.", show_alert=True)
        return
    key = "ADMIN-" + secrets.token_hex(8).upper()
    promo_keys[key] = True  # True = не использован
    await call.message.edit_text(
        f"🔑 <b>Новый одноразовый промокод сгенерирован!</b>\n\n"
        f"<code>{key}</code>\n\n"
        f"⚠️ Этот ключ даёт права администратора.\n"
        f"Он одноразовый — после активации сгорает.\n\n"
        f"Передай его нужному пользователю лично.\n"
        f"Для активации: <code>/promo {key}</code>",
        reply_markup=sa_back_kb()
    )

@router.message(F.text.startswith("/promo"))
async def activate_promo(message: Message):
    user_id = message.from_user.id
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("⚠️ Укажи промокод: <code>/promo КЛЮЧ</code>")
        return
    key = parts[1].strip()
    if key not in promo_keys:
        await message.answer("❌ Неверный промокод.")
        return
    if promo_keys[key] is not True:
        await message.answer("❌ Этот промокод уже был использован.")
        return
    if user_id == SUPER_ADMIN:
        await message.answer("⚠️ Суперадмин уже имеет все права — промокод не нужен.")
        return
    if user_id in ADMINS:
        await message.answer("⚠️ У тебя уже есть права администратора.")
        return
    # Активируем
    promo_keys[key] = user_id  # сохраняем кто использовал
    ADMINS.append(user_id)
    user_success[user_id] = 56
    username = message.from_user.username or "нет юзернейма"
    await message.answer(
        "🛡 <b>Промокод активирован!</b>\n\n"
        "Вы получили права администратора."
    )
    # Уведомить суперадмина
    try:
        await bot.send_message(
            SUPER_ADMIN,
            f"🔑 Промокод <code>{key}</code> активирован!\n"
            f"👤 Пользователь: @{username} | <code>{user_id}</code>"
        )
    except Exception:
        pass



@router.message(F.text.startswith("/setname "))
async def set_bot_name(message: Message):
    global BOT_NAME
    if message.from_user.id != SUPER_ADMIN:
        await message.answer("⛔ Команда доступна только супер-админу.")
        return
    new_name = message.text.split("/setname ", 1)[1].strip()
    if not new_name:
        await message.answer("⚠️ Укажи название после /setname\nПример: /setname SAVA")
        return
    old_name = BOT_NAME
    BOT_NAME = new_name.upper()
    await message.answer(
        f"✅ Название бота изменено!\n\nБыло: <b>{old_name}</b>\nСтало: <b>{BOT_NAME}</b>"
    )

@router.message(F.text == "/removephoto")
async def remove_welcome_photo(message: Message):
    global WELCOME_PHOTO_ID
    if message.from_user.id != SUPER_ADMIN:
        await message.answer("⛔ Команда доступна только супер-админу.")
        return
    WELCOME_PHOTO_ID = None
    await message.answer("✅ Приветственное фото удалено.")

@router.message(F.text.startswith("/ban "))
async def ban_user(message: Message):
    if message.from_user.id != SUPER_ADMIN:
        await message.answer("⛔ Только супер-админ может банить.")
        return
    try:
        target_id = int(message.text.split(" ", 1)[1].strip())
    except (ValueError, IndexError):
        await message.answer("⚠️ Укажи ID пользователя: /ban 123456789")
        return
    if target_id == SUPER_ADMIN:
        await message.answer("❌ Нельзя забанить самого себя, умник.")
        return
    banned_users.add(target_id)
    await message.answer(f"🔨 Пользователь <code>{target_id}</code> забанен навсегда.")

@router.message(F.text.startswith("/unban "))
async def unban_user(message: Message):
    if message.from_user.id != SUPER_ADMIN:
        await message.answer("⛔ Только супер-админ может разбанивать.")
        return
    try:
        target_id = int(message.text.split(" ", 1)[1].strip())
    except (ValueError, IndexError):
        await message.answer("⚠️ Укажи ID пользователя: /unban 123456789")
        return
    if target_id in banned_users:
        banned_users.discard(target_id)
        await message.answer(f"✅ Пользователь <code>{target_id}</code> разбанен.")
    else:
        await message.answer(f"⚠️ Пользователь <code>{target_id}</code> не был забанен.")

@router.message(F.text == "/banlist")
async def ban_list(message: Message):
    if message.from_user.id != SUPER_ADMIN:
        await message.answer("⛔ Только супер-админ.")
        return
    if not banned_users:
        await message.answer("✅ Список забаненных пуст.")
        return
    ids = "\n".join(f"• <code>{uid}</code>" for uid in banned_users)
    await message.answer(f"🔨 Забаненные пользователи ({len(banned_users)}):\n{ids}")

# ══════════════════════════════════════════════════════
#       Реферальная система
# ══════════════════════════════════════════════════════


# deal_start_handler и referral_start объединены в start_handler выше

@router.message(F.text == "/ref")
async def ref_link(message: Message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.answer("⛔ Команда доступна только админам.")
        return
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    count = sum(1 for ref in referrals.values() if ref == user_id)
    await message.answer(T(user_id, "ref_cmd_text", link=link, count=count))

# ══════════════════════════════════════════════════════
#       Реквизиты
# ══════════════════════════════════════════════════════

@router.callback_query(F.data == "edit_wallet")
async def edit_wallet(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    current_wallet = user_wallets.get(user_id, {}).get('data', "❌ Не указан")
    current_type = user_wallets.get(user_id, {}).get('type', "не указан")
    text = T(user_id, "wallet_current", data=current_wallet, wtype=current_type)

    if WELCOME_PHOTO_ID:
        await call.message.answer_photo(photo=WELCOME_PHOTO_ID, caption=text, reply_markup=wallet_type_menu(user_id))
        await call.message.delete()
    else:
        await safe_edit_or_resend(call, text, reply_markup=wallet_type_menu(user_id))

@router.callback_query(F.data.startswith("wallet_"))
async def choose_wallet_type(call: CallbackQuery, state: FSMContext):
    wallet_type = call.data[len("wallet_"):]
    # Игнорируем если это не тип кошелька
    valid_types = ["ton", "bep20", "trc20", "card_kz", "card_ru", "card_ua", "card_uz", "card_by", "card_eu"]
    if wallet_type not in valid_types:
        return

    await state.clear()
    await state.update_data(wallet_type=wallet_type)
    
    country_map = {
        "ton": None, "bep20": None, "trc20": None,
        "card_kz": "Kazakhstan", "card_ru": "Russia",
        "card_ua": "Ukraine", "card_uz": "Uzbekistan", "card_by": "Belarus", "card_eu": "EU"
    }
    uid = call.from_user.id
    if wallet_type == "ton":
        text = T(uid, "wallet_enter_ton")
    elif wallet_type == "bep20":
        text = T(uid, "wallet_enter_bep20")
    elif wallet_type == "trc20":
        text = T(uid, "wallet_enter_trc20")
    else:
        text = T(uid, "wallet_enter_card", country=country_map.get(wallet_type, ""))
    await safe_edit_or_resend(call, text, reply_markup=back_menu(uid))
    await state.set_state(Form.wallet_data)

@router.message(Form.wallet_data)
async def save_wallet(message: Message, state: FSMContext):
    wallet_data = message.text.strip()
    data = await state.get_data()
    wallet_type = data['wallet_type']
    
    uid = message.from_user.id
    if wallet_type == "ton":
        if len(wallet_data) < 10 or not any(c.isalpha() for c in wallet_data):
            await message.answer(T(uid, "wallet_err_ton"))
            return
    elif wallet_type == "bep20":
        # BEP20 адрес начинается с 0x и имеет 42 символа
        if not (wallet_data.startswith("0x") and len(wallet_data) == 42):
            await message.answer(T(uid, "wallet_err_bep20"))
            return
    elif wallet_type == "trc20":
        # TRC20 адрес начинается с T и имеет 34 символа
        if not (wallet_data.startswith("T") and len(wallet_data) == 34):
            await message.answer(T(uid, "wallet_err_trc20"))
            return
    elif wallet_type in ["card_ru", "card_ua", "card_uz", "card_by", "card_kz", "card_eu"]:
        if len(wallet_data) < 6 or not any(c.isdigit() for c in wallet_data):
            await message.answer(T(uid, "wallet_err_card"))
            return
    user_wallets[uid] = {'type': wallet_type, 'data': wallet_data}
    type_names = {
        "ton": "TON", "bep20": "BEP20 (USDT)", "trc20": "TRC20 (USDT)",
        "card_kz": "KZ", "card_ru": "RU",
        "card_ua": "UA", "card_uz": "UZ", "card_by": "BY", "card_eu": "EU"
    }
    type_name = type_names.get(wallet_type, wallet_type)
    await message.answer(T(uid, "wallet_saved", wtype=type_name, data=wallet_data), reply_markup=back_menu(uid))
    await state.clear()

# ══════════════════════════════════════════════════════
#       Сделки
# ══════════════════════════════════════════════════════

@router.callback_query(F.data == "create_deal")
async def create_deal(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    text = T(uid, "choose_method")
    # Показываем выбор метода сразу — реквизиты проверяем ПОСЛЕ выбора типа
    if WELCOME_PHOTO_ID:
        await call.message.answer_photo(photo=WELCOME_PHOTO_ID, caption=text, reply_markup=deal_methods(uid))
        await call.message.delete()
    else:
        await safe_edit_or_resend(call, text, reply_markup=deal_methods(uid))


@router.callback_query(F.data.in_(["deal_ton", "deal_bep20", "deal_trc20", "deal_card", "deal_stars"]))
async def deal_method_chosen(call: CallbackQuery, state: FSMContext):
    method = call.data
    uid = call.from_user.id
    wallet = user_wallets.get(uid)
    wallet_type = wallet.get('type', 'card_ru') if wallet else 'card_ru'

    # ── Звёзды: реквизиты не нужны, запрашиваем юзернейм ──
    if method == "deal_stars":
        await state.clear()
        await state.update_data(method=method)
        kb = InlineKeyboardBuilder()
        kb.button(text=T(uid, "btn_back"), callback_data="back_to_menu")
        await safe_edit_or_resend(
            call,
            T(uid, "stars_enter_username"),
            reply_markup=kb.as_markup()
        )
        await state.set_state(Form.deal_stars_username)
        return

    # ── TON / BEP20 / TRC20 / Карта: нужны реквизиты ──
    if not wallet:
        kb = InlineKeyboardBuilder()
        kb.button(text=T(uid, "add_wallet_btn"), callback_data="edit_wallet")
        kb.button(text=T(uid, "btn_back"), callback_data="back_to_menu")
        kb.adjust(1)
        await safe_edit_or_resend(call, T(uid, "no_wallet"), reply_markup=kb.as_markup())
        return

    await state.clear()
    await state.update_data(method=method)

    if method == "deal_ton":
        currency = CURRENCIES["ton"]
    elif method == "deal_bep20":
        currency = CURRENCIES["bep20"]
    elif method == "deal_trc20":
        currency = CURRENCIES["trc20"]
    else:
        currency = CURRENCIES.get(wallet_type, CURRENCIES["card_ru"])

    await safe_edit_or_resend(call, T(uid, "enter_amount", currency=currency), reply_markup=back_menu(uid))
    await state.set_state(Form.deal_amount)


@router.message(Form.deal_stars_username)
async def deal_stars_username_input(message: Message, state: FSMContext):
    uid = message.from_user.id
    username = message.text.strip().lstrip("@")

    # Простая валидация юзернейма Telegram
    import re
    if not re.match(r'^\w{3,32}$', username):
        await message.answer(T(uid, "stars_username_err"), reply_markup=back_menu(uid))
        return

    currency = CURRENCIES["stars"]
    await state.update_data(stars_username=username)
    await message.answer(
        T(uid, "stars_username_saved", username=username, currency=currency),
        reply_markup=back_menu(uid)
    )
    await state.set_state(Form.deal_amount)



@router.message(Form.deal_amount)
async def deal_amount_input(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(',', '.'))
        uid = message.from_user.id
        if amount <= 0:
            await message.answer(T(uid, "amount_zero"))
            return
        await state.update_data(amount=str(amount))
        # Если это были звёзды — показываем сумму в Stars
        data = await state.get_data()
        method = data.get("method", "deal_card")
        if method == "deal_stars":
            currency = CURRENCIES["stars"]
            await message.answer(
                T(uid, "enter_desc") + f"\n\n💰 Сумма: {amount} {currency}",
                reply_markup=back_menu(uid)
            )
        else:
            await message.answer(T(uid, "enter_desc"), reply_markup=back_menu(uid))
        await state.set_state(Form.deal_description)
    except ValueError:
        await message.answer(T(message.from_user.id, "amount_err"))

@router.message(Form.deal_description)
async def deal_description_input(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    amount = data["amount"]
    description = message.text
    method = data.get("method", "deal_card")
    wallet_type = user_wallets.get(user_id, {}).get('type', 'card_ru')
    
    if method == "deal_ton":
        currency = CURRENCIES["ton"]
    elif method == "deal_bep20":
        currency = CURRENCIES["bep20"]
    elif method == "deal_trc20":
        currency = CURRENCIES["trc20"]
    elif method == "deal_stars":
        currency = CURRENCIES["stars"]
    else:
        currency = CURRENCIES.get(wallet_type, CURRENCIES["card_ru"])

    user_deal_count[user_id] = user_deal_count.get(user_id, 0) + 1
    deal_id = f"deal_{user_id}_{user_deal_count[user_id]}"

    deals[deal_id] = {
        "amount": amount,
        "currency": currency,
        "description": description,
        "seller_id": user_id,
        "method": method,
        "wallet_type": wallet_type,
        "stars_username": data.get("stars_username")   # None для не-звёздных сделок
    }

    link = f"https://t.me/{BOT_USERNAME}?start={deal_id}"
    uid = message.from_user.id

    share_text = f"По этой ссылке можно перейти на сделку со мной 🤝\n{link}"
    share_url = f"https://t.me/share/url?url={link}&text=По этой ссылке можно перейти на сделку со мной 🤝"

    kb = InlineKeyboardBuilder()
    kb.button(text="🔗 Поделиться ссылкой", url=share_url)
    kb.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    kb.adjust(1)

    await message.answer(
        T(uid, "deal_created", amount=amount, currency=currency, desc=description, link=link),
        reply_markup=kb.as_markup()
    )
    await state.clear()


# deal_start_handler перенесён в start_handler

@router.callback_query(F.data.regexp(r"^confirm_deal_"))
async def confirm_payment(call: CallbackQuery):
    user_id = call.from_user.id

    deal_id = call.data[len("confirm_"):]  # убираем "confirm_" в начале
    deal = deals.get(deal_id)
    if not deal:
        await call.answer("❌ Сделка не найдена.", show_alert=True)
        return

    # Только админ или суперадмин может подтверждать оплату
    if user_id not in ADMINS:
        await call.answer("⛔ Только администратор может подтвердить оплату.", show_alert=True)
        return

    if deal.get("payment_confirmed"):
        await call.answer("⚠️ Оплата уже подтверждена.", show_alert=True)
        return

    deal["payment_confirmed"] = True
    seller_id = deal["seller_id"]
    method = deal.get("method", "deal_card")

    seller_lang = get_lang(seller_id)
    seller_kb = InlineKeyboardBuilder()
    seller_kb.button(text=TEXTS[seller_lang]["btn_sent_gift"], callback_data=f"seller_sent_{deal_id}")
    seller_kb.button(text=TEXTS[seller_lang]["btn_cancel_deal"], callback_data=f"seller_cancel_{deal_id}")
    seller_kb.adjust(1)
    msg_key = "seller_msg_stars" if method == "deal_stars" else "seller_msg_card"
    await call.message.answer(T(user_id, "payment_confirmed_buyer", deal_id=deal_id))
    try:
        await bot.send_message(seller_id, TEXTS[seller_lang][msg_key], reply_markup=seller_kb.as_markup())
    except Exception as e:
        logging.error(f"Не удалось уведомить продавца: {e}")
    await call.answer("✅")

@router.callback_query(F.data.regexp(r"^seller_sent_deal_"))
async def seller_sent_gift(call: CallbackQuery):
    deal_id = call.data[len("seller_sent_"):]
    deal = deals.get(deal_id)

    if not deal:
        await call.answer("❌ Сделка не найдена.", show_alert=True)
        return

    seller_id = deal["seller_id"]
    buyer_id = deal.get("buyer_id")
    seller_lang = get_lang(seller_id)
    buyer_lang = get_lang(buyer_id) if buyer_id else "ru"

    # Защита от повторного нажатия
    if deal.get("gift_sent"):
        await call.answer("⚠️ Уже отправлено, ожидайте ответа покупателя.", show_alert=True)
        return
    deal["gift_sent"] = True

    # Продавцу — сообщение об ожидании подтверждения
    try:
        await call.message.edit_text(TEXTS[seller_lang]["deal_sent_confirm"])
    except Exception:
        await call.message.answer(TEXTS[seller_lang]["deal_sent_confirm"])

    # Покупателю — опрос с кнопками Да / Нет
    if buyer_id and buyer_id != seller_id:
        buyer_kb = InlineKeyboardBuilder()
        buyer_kb.button(
            text=TEXTS[buyer_lang]["btn_buyer_yes"],
            callback_data=f"buyer_received_yes_{deal_id}"
        )
        buyer_kb.button(
            text=TEXTS[buyer_lang]["btn_buyer_no"],
            callback_data=f"buyer_received_no_{deal_id}"
        )
        buyer_kb.adjust(1)
        try:
            await bot.send_message(
                buyer_id,
                TEXTS[buyer_lang]["buyer_received_question"].format(deal_id=deal_id),
                reply_markup=buyer_kb.as_markup()
            )
        except Exception as e:
            logging.error(f"Не удалось отправить опрос покупателю {buyer_id}: {e}")
    else:
        # Если покупатель не определён — завершаем сделку сразу
        await _complete_deal(deal_id)
    await call.answer()


@router.callback_query(F.data.regexp(r"^buyer_received_yes_deal_"))
async def buyer_confirmed_received(call: CallbackQuery):
    deal_id = call.data[len("buyer_received_yes_"):]
    deal = deals.get(deal_id)
    buyer_id = call.from_user.id

    if not deal:
        await call.answer("❌ Сделка не найдена.", show_alert=True)
        return

    buyer_lang = get_lang(buyer_id)
    try:
        await call.message.edit_text(TEXTS[buyer_lang]["buyer_confirmed_received"])
    except Exception:
        await call.message.answer(TEXTS[buyer_lang]["buyer_confirmed_received"])
    await _complete_deal(deal_id)
    await call.answer()


@router.callback_query(F.data.regexp(r"^buyer_received_no_deal_"))
async def buyer_denied_received(call: CallbackQuery):
    deal_id = call.data[len("buyer_received_no_"):]
    deal = deals.get(deal_id)
    buyer_id = call.from_user.id

    if not deal:
        await call.answer("❌ Сделка не найдена.", show_alert=True)
        return

    # Сбрасываем флаг, чтобы продавец мог снова нажать "Я отправил"
    deal["gift_sent"] = False

    seller_id = deal["seller_id"]
    buyer_lang = get_lang(buyer_id)
    seller_lang = get_lang(seller_id)

    # Покупателю — сообщение что уведомили продавца
    try:
        await call.message.edit_text(TEXTS[buyer_lang]["buyer_denied_received"])
    except Exception:
        await call.message.answer(TEXTS[buyer_lang]["buyer_denied_received"])

    # Продавцу — повторное уведомление с кнопкой «Я отправил подарок»
    seller_kb = InlineKeyboardBuilder()
    seller_kb.button(
        text=TEXTS[seller_lang]["btn_sent_gift"],
        callback_data=f"seller_sent_{deal_id}"
    )
    seller_kb.button(
        text=TEXTS[seller_lang]["btn_cancel_deal"],
        callback_data=f"seller_cancel_{deal_id}"
    )
    seller_kb.adjust(1)
    try:
        await bot.send_message(
            seller_id,
            TEXTS[seller_lang]["seller_resend_gift"].format(deal_id=deal_id),
            reply_markup=seller_kb.as_markup()
        )
    except Exception as e:
        logging.error(f"Не удалось уведомить продавца {seller_id}: {e}")
    await call.answer()


async def _complete_deal(deal_id: str):
    """Завершение сделки — уведомляет обе стороны и удаляет сделку."""
    deal = deals.get(deal_id)
    if not deal:
        return

    seller_id = deal["seller_id"]
    buyer_id = deal.get("buyer_id")
    amount = deal["amount"]
    currency = deal["currency"]
    description = deal["description"]
    method = deal.get("method", "deal_card")

    seller_lang = get_lang(seller_id)
    buyer_lang = get_lang(buyer_id) if buyer_id else "ru"

    # Успешные сделки продавца +1
    user_success[seller_id] = user_success.get(seller_id, 0) + 1

    try:
        await bot.send_message(seller_id, TEXTS[seller_lang]["deal_done_seller"].format(
            deal_id=deal_id, amount=amount, currency=currency, desc=description))
    except Exception as e:
        logging.error(f"Не удалось уведомить продавца {seller_id}: {e}")

    if buyer_id and buyer_id != seller_id:
        try:
            await bot.send_message(buyer_id, TEXTS[buyer_lang]["deal_done_buyer"].format(
                deal_id=deal_id, amount=amount, currency=currency, desc=description))
        except Exception as e:
            logging.error(f"Не удалось уведомить покупателя {buyer_id}: {e}")

    admin_message = (
        f"✅ Deal #{deal_id} completed:\n"
        f"Seller: {seller_id}\nBuyer: {buyer_id}\n"
        f"Amount: {amount} {currency}\nMethod: {method}\nItem: {description}"
    )
    for admin_id in ADMINS:
        if admin_id not in [seller_id, buyer_id]:
            try:
                await bot.send_message(admin_id, admin_message)
            except Exception as e:
                logging.error(f"Не удалось уведомить админа {admin_id}: {e}")

    deals.pop(deal_id, None)

@router.callback_query(F.data.regexp(r"^seller_cancel_deal_"))
async def seller_cancel_deal(call: CallbackQuery):
    deal_id = call.data[len("seller_cancel_"):]
    deal = deals.get(deal_id)
    
    if not deal:
        await call.answer("❌ Сделка не найдена.", show_alert=True)
        return
    
    seller_id = deal["seller_id"]
    buyer_id = deal.get("buyer_id")
    amount = deal["amount"]
    currency = deal["currency"]
    method = deal.get("method", "deal_card")
    
    seller_lang = get_lang(seller_id)
    buyer_lang = get_lang(buyer_id) if buyer_id else "ru"
    
    try:
        await call.message.edit_text(TEXTS[seller_lang]["deal_cancel_confirm"])
    except Exception:
        await call.message.answer(TEXTS[seller_lang]["deal_cancel_confirm"])
    
    try:
        await bot.send_message(seller_id, TEXTS[seller_lang]["deal_cancel_seller"].format(
            deal_id=deal_id, amount=amount, currency=currency))
    except Exception as e:
        logging.error(f"Не удалось уведомить продавца {seller_id}: {e}")
    if buyer_id and buyer_id != seller_id:
        try:
            await bot.send_message(buyer_id, TEXTS[buyer_lang]["deal_cancel_buyer"].format(
                deal_id=deal_id, amount=amount, currency=currency))
        except Exception as e:
            logging.error(f"Не удалось уведомить покупателя {buyer_id}: {e}")
    admin_message = (
        f"❌ Deal #{deal_id} cancelled:\n"
        f"Seller: {seller_id}\nBuyer: {buyer_id}\n"
        f"Amount: {amount} {currency}\nMethod: {method}"
    )
    for admin_id in ADMINS:
        if admin_id not in [seller_id, buyer_id]:
            try:
                await bot.send_message(admin_id, admin_message)
            except Exception as e:
                logging.error(f"Не удалось уведомить админа {admin_id}: {e}")
    
    deals.pop(deal_id, None)
    await call.answer()

# ══════════════════════════════════════════════════════
#       О сервисе / Обращения
# ══════════════════════════════════════════════════════

@router.callback_query(F.data == "about_service")
async def about_service(call: CallbackQuery):
    uid = call.from_user.id
    text = (
        f"🛡 <b>{BOT_NAME}</b> — безопасный сервис гарантийных сделок.\n\n"
        "📌 <b>Как работает:</b>\n"
        "1. Продавец создаёт сделку и получает ссылку\n"
        "2. Покупатель переходит по ссылке и вносит оплату\n"
        "3. Средства удерживаются у гаранта\n"
        "4. Продавец передаёт товар/подарок\n"
        "5. Покупатель подтверждает получение\n"
        "6. Средства переводятся продавцу\n\n"
        "🔒 <b>Ваши деньги всегда в безопасности!</b>"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    await safe_edit_or_resend(call, text, reply_markup=kb.as_markup())

@router.callback_query(F.data == "appeals_menu")
async def appeals_menu(call: CallbackQuery):
    text = (
        f"📝 <b>Центр обращений {BOT_NAME}</b>\n\n"
        "⚙️ <b>Раздел предложений и идей:</b>\n"
        "• Предложения по улучшению функционала\n"
        "• Идеи для новых функций\n"
        "• Запросы на интеграции\n"
        "• Отзывы о пользовательском опыте\n\n"
        "⛔️ <b>Раздел жалоб и претензий:</b>\n"
        "• Жалобы на пользователей\n"
        "• Проблемы со сделками\n"
        "• Технические проблемы\n"
        "• Некорректное поведение\n"
        "• Предполагаемое мошенничество\n\n"
        "📞 <b>Важная информация:</b>\n"
        "• Все обращения рассматриваются в течение 24 часов\n"
        "• Конфиденциальность гарантируется\n"
        "• По жалобам на мошенничество — моментальная реакция\n"
        "• Лучшие предложения внедряются в бота\n\n"
        "👇 Выберите раздел для обращения:"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="💡 Предложить", callback_data="appeal_suggest")
    kb.button(text="⛔ Пожаловаться", callback_data="appeal_complain")
    kb.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    kb.adjust(2, 1)
    await safe_edit_or_resend(call, text, reply_markup=kb.as_markup())

@router.callback_query(F.data == "appeal_suggest")
async def appeal_suggest_start(call: CallbackQuery, state: FSMContext):
    text = (
        "✍️ <b>Напишите ваше предложение:</b>\n\n"
        "ℹ️ Опишите подробно вашу идею, как она улучшит работу бота и какие преимущества принесет пользователям."
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    await state.set_state(AppealForm.waiting_suggestion)
    await safe_edit_or_resend(call, text, reply_markup=kb.as_markup())

@router.callback_query(F.data == "appeal_complain")
async def appeal_complain_start(call: CallbackQuery, state: FSMContext):
    text = (
        "⛔️ <b>Напишите вашу жалобу:</b>\n\n"
        "ℹ️ Укажите:\n"
        "• ID пользователя/сделки\n"
        "• Суть проблемы\n"
        "• Желаемое решение"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    await state.set_state(AppealForm.waiting_complaint)
    await safe_edit_or_resend(call, text, reply_markup=kb.as_markup())

@router.message(AppealForm.waiting_suggestion)
async def appeal_suggestion_received(message: Message, state: FSMContext):
    uid = message.from_user.id
    await state.clear()
    # Пересылаем суперадмину
    try:
        await bot.send_message(
            SUPER_ADMIN,
            f"💡 <b>Новое предложение</b>\n"
            f"От: <a href='tg://user?id={uid}'>{message.from_user.full_name}</a> (ID: {uid})\n\n"
            f"{message.text}"
        )
    except Exception as e:
        logging.error(f"Не удалось уведомить суперадмина: {e}")

    text = (
        f"✅ <b>Ваше обращение принято!</b>\n\n"
        f"💡 Тип: 💡 Предложение\n\n"
        f"Мы рассмотрим его в течение 24 часов.\n"
        f"Спасибо, что помогаете улучшать <b>{BOT_NAME}</b>!"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    await message.answer(text, reply_markup=kb.as_markup())

@router.message(AppealForm.waiting_complaint)
async def appeal_complaint_received(message: Message, state: FSMContext):
    uid = message.from_user.id
    await state.clear()
    # Пересылаем суперадмину
    try:
        await bot.send_message(
            SUPER_ADMIN,
            f"⛔️ <b>Новая жалоба</b>\n"
            f"От: <a href='tg://user?id={uid}'>{message.from_user.full_name}</a> (ID: {uid})\n\n"
            f"{message.text}"
        )
    except Exception as e:
        logging.error(f"Не удалось уведомить суперадмина: {e}")

    text = (
        f"✅ <b>Ваше обращение принято!</b>\n\n"
        f"⛔️ Тип: ⛔️ Жалоба\n\n"
        f"Мы рассмотрим его в течение 24 часов.\n"
        f"Спасибо, что помогаете улучшать <b>{BOT_NAME}</b>!"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    await message.answer(text, reply_markup=kb.as_markup())



@router.callback_query(F.data == "lang_ru")
async def set_lang_ru(call: CallbackQuery):
    uid = call.from_user.id
    user_lang[uid] = "ru"
    await call.answer(TEXTS["ru"]["lang_set"], show_alert=True)
    text = welcome_text(uid)
    if WELCOME_PHOTO_ID:
        await call.message.answer_photo(photo=WELCOME_PHOTO_ID, caption=text, reply_markup=main_menu(uid))
        await call.message.delete()
    else:
        await safe_edit_or_resend(call, text, reply_markup=main_menu(uid))

@router.callback_query(F.data == "lang_en")
async def set_lang_en(call: CallbackQuery):
    uid = call.from_user.id
    user_lang[uid] = "en"
    await call.answer(TEXTS["en"]["lang_set"], show_alert=True)
    text = welcome_text(uid)
    if WELCOME_PHOTO_ID:
        await call.message.answer_photo(photo=WELCOME_PHOTO_ID, caption=text, reply_markup=main_menu(uid))
        await call.message.delete()
    else:
        await safe_edit_or_resend(call, text, reply_markup=main_menu(uid))

@router.callback_query(F.data == "change_lang")
async def change_language(call: CallbackQuery):
    uid = call.from_user.id
    await safe_edit_or_resend(call, T(uid, "choose_lang"), reply_markup=lang_menu())

@router.callback_query(F.data == "back_to_menu")
async def go_back(call: CallbackQuery):
    uid = call.from_user.id
    if WELCOME_PHOTO_ID:
        await call.message.answer_photo(photo=WELCOME_PHOTO_ID, caption=welcome_text(uid), reply_markup=main_menu(uid))
    else:
        await call.message.answer(welcome_text(uid), reply_markup=main_menu(uid))
    await call.message.delete()

@router.message(F.text.startswith("/s "))
async def admin_confirm_other_deal(message: Message):
    admin_id = message.from_user.id
    if admin_id not in ADMINS:
        await message.answer(T(admin_id, "admin_only"))
        return
    try:
        deal_id = message.text.split(" ", 1)[1].strip()
    except IndexError:
        await message.answer(T(admin_id, "s_no_id"))
        return
    deal = deals.get(deal_id)
    if not deal:
        await message.answer(T(admin_id, "deal_not_found"))
        return

    seller_id = deal["seller_id"]
    buyer_id = deal.get("buyer_id", admin_id)
    method = deal.get("method", "deal_card")

    seller_lang = get_lang(seller_id)
    seller_kb = InlineKeyboardBuilder()
    seller_kb.button(text=TEXTS[seller_lang]["btn_sent_gift"], callback_data=f"seller_sent_{deal_id}")
    seller_kb.button(text=TEXTS[seller_lang]["btn_cancel_deal"], callback_data=f"seller_cancel_{deal_id}")
    seller_kb.adjust(1)
    msg_key = "seller_msg_stars" if method == "deal_stars" else "seller_msg_card"
    await message.answer(T(admin_id, "s_confirmed", deal_id=deal_id))
    await bot.send_message(seller_id, TEXTS[seller_lang][msg_key], reply_markup=seller_kb.as_markup())
    if buyer_id != admin_id:
        buyer_lang = get_lang(buyer_id)
        await bot.send_message(buyer_id, TEXTS[buyer_lang]["s_buyer_notify"].format(deal_id=deal_id))

# Установка фото от суперадмина вне FSM (оставлено для совместимости)
@router.message(F.photo)
async def set_welcome_photo(message: Message, state: FSMContext):
    global WELCOME_PHOTO_ID
    user_id = message.from_user.id
    if user_id != SUPER_ADMIN:
        return
    # Если активно состояние ожидания фото — оно обработается выше
    current_state = await state.get_state()
    if current_state == SuperAdminForm.waiting_new_photo:
        return
    WELCOME_PHOTO_ID = message.photo[-1].file_id
    await message.answer(T(user_id, "photo_set"))

# ══════════════════════════════════════════════════════
#       Middleware
# ══════════════════════════════════════════════════════

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any

class BanMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable, event: TelegramObject, data: Dict[str, Any]) -> Any:
        user = None
        if hasattr(event, 'from_user'):
            user = event.from_user
        elif hasattr(event, 'message') and event.message:
            user = event.message.from_user

        if user and user.id in banned_users and user.id != SUPER_ADMIN:
            ban_uid = user.id
            if hasattr(event, 'answer') and callable(event.answer):
                try:
                    await event.answer(T(ban_uid, "banned"), show_alert=True)
                except Exception:
                    pass
            elif hasattr(event, 'answer'):
                try:
                    await event.answer(T(ban_uid, "banned"))
                except Exception:
                    pass
            return
        return await handler(event, data)

# ══════════════════════════════════════════════════════
#       Запуск
# ══════════════════════════════════════════════════════

async def main():
    global BOT_USERNAME
    dp.message.middleware(BanMiddleware())
    dp.callback_query.middleware(BanMiddleware())
    bot_info = await bot.get_me()
    BOT_USERNAME = bot_info.username
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Бот запущен: @{BOT_USERNAME}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
