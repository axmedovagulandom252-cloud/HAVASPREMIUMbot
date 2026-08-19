import asyncio
import os
import re

from aiohttp import web

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import BOT_TOKEN, MANAGER_ID, CARD_NUMBER, CARD_OWNER


# ==================================================
# BOT
# ==================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ==================================================
# TO'YXONALAR
# ==================================================

TOYXONALAR = {
    "1": {
        "name": "Kichik to'yxona",
        "people": "100 kishigacha",
        "price": "5 000 000 so'm",
        "image": "https://example.com/1.jpg"
    },

    "2": {
        "name": "O'rta to'yxona",
        "people": "200 kishigacha",
        "price": "8 000 000 so'm",
        "image": "https://example.com/2.jpg"
    },

    "3": {
        "name": "Katta to'yxona",
        "people": "400 kishigacha",
        "price": "12 000 000 so'm",
        "image": "https://example.com/3.jpg"
    },

    "4": {
        "name": "Premium to'yxona",
        "people": "600 kishigacha",
        "price": "20 000 000 so'm",
        "image": "https://example.com/4.jpg"
    }
}


# ==================================================
# HOLATLAR
# ==================================================

class Order(StatesGroup):
    choosing_hall = State()
    confirming_hall = State()
    name = State()
    phone = State()
    date = State()
    payment = State()


# ==================================================
# TO'YXONA TUGMALARI
# ==================================================

def hall_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 Kichik to'yxona",
                    callback_data="hall_1"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏛 O'rta to'yxona",
                    callback_data="hall_2"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👑 Katta to'yxona",
                    callback_data="hall_3"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Premium to'yxona",
                    callback_data="hall_4"
                )
            ]
        ]
    )


# ==================================================
# YANGI ZAKAZ
# ==================================================

async def start_new_order(
    message: types.Message,
    state: FSMContext
):

    await state.clear()

    await message.answer(
        "🎉 YANGI TO'YXONA ZAKAZI\n\n"
        "👇 Qaysi to'yxonani band qilmoqchisiz?",
        reply_markup=hall_keyboard()
    )

    await state.set_state(
        Order.choosing_hall
    )


# ==================================================
# START
# ==================================================

@dp.message(CommandStart())
async def start(
    message: types.Message,
    state: FSMContext
):

    await start_new_order(
        message,
        state
    )


# ==================================================
# TO'YXONA TANLASH
# ==================================================

@dp.callback_query(
    lambda c: c.data.startswith("hall_")
)
async def choose_hall(
    callback: types.CallbackQuery,
    state: FSMContext
):

    hall_id = callback.data.replace(
        "hall_",
        ""
    )

    hall = TOYXONALAR.get(hall_id)

    if not hall:

        await callback.answer(
            "To'yxona topilmadi!",
            show_alert=True
        )

        return

    await state.update_data(
        hall_id=hall_id,
        hall_name=hall["name"],
        hall_people=hall["people"],
        hall_price=hall["price"]
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ha, shuni tanlayman",
                    callback_data="confirm_hall"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Boshqasini tanlash",
                    callback_data="change_hall"
                )
            ]
        ]
    )

    text = (
        f"🎉 {hall['name']}\n\n"
        f"👥 Sig'imi: {hall['people']}\n"
        f"💰 Narxi: {hall['price']}\n\n"
        "Shu to'yxonani tanlaysizmi?"
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    try:

        await callback.message.answer_photo(
            photo=hall["image"],
            caption=text,
            reply_markup=keyboard
        )

    except Exception:

        await callback.message.answer(
            text,
            reply_markup=keyboard
        )

    await state.set_state(
        Order.confirming_hall
    )

    await callback.answer()


# ==================================================
# BOSHQA TO'YXONA
# ==================================================

@dp.callback_query(
    lambda c: c.data == "change_hall"
)
async def change_hall(
    callback: types.CallbackQuery,
    state: FSMContext
):

    await callback.message.answer(
        "🔄 Boshqa to'yxonani tanlang:",
        reply_markup=hall_keyboard()
    )

    await state.set_state(
        Order.choosing_hall
    )

    await callback.answer()


# ==================================================
# TO'YXONANI TASDIQLASH
# ==================================================

@dp.callback_query(
    lambda c: c.data == "confirm_hall"
)
async def confirm_hall(
    callback: types.CallbackQuery,
    state: FSMContext
):

    data = await state.get_data()

    await callback.message.answer(
        f"✅ {data['hall_name']} tanlandi!\n\n"
        f"👥 Sig'imi: {data['hall_people']}\n"
        f"💰 Narxi: {data['hall_price']}\n\n"
        "👤 Ismingizni yozing.\n\n"
        "⚠️ Faqat harflar."
    )

    await state.set_state(
        Order.name
    )

    await callback.answer()


# ==================================================
# ISM
# ==================================================

@dp.message(Order.name)
async def get_name(
    message: types.Message,
    state: FSMContext
):

    if not message.text:

        await message.answer(
            "❌ Ismingizni yozing."
        )

        return

    name = message.text.strip()

    if not all(
        x.isalpha() or x.isspace()
        for x in name
    ):

        await message.answer(
            "❌ Ism faqat harflardan iborat "
            "bo'lishi kerak.\n\n"
            "Masalan: Ali Valiyev"
        )

        return

    await state.update_data(
        name=name
    )

    await message.answer(
        "📞 Telefon raqamingizni yozing.\n\n"
        "⚠️ Faqat raqamlar.\n\n"
        "Masalan: 998901234567"
    )

    await state.set_state(
        Order.phone
    )


# ==================================================
# TELEFON
# ==================================================

@dp.message(Order.phone)
async def get_phone(
    message: types.Message,
    state: FSMContext
):

    if not message.text:

        await message.answer(
            "❌ Telefon raqamini yozing."
        )

        return

    phone = message.text.strip()

    if not phone.isdigit():

        await message.answer(
            "❌ Telefon faqat raqamlardan "
            "iborat bo'lishi kerak.\n\n"
            "Masalan: 998901234567"
        )

        return

    await state.update_data(
        phone=phone
    )

    await message.answer(
        "📅 To'y sanasini yozing.\n\n"
        "⚠️ Faqat shu formatda:\n"
        "25.09.2026"
    )

    await state.set_state(
        Order.date
    )


# ==================================================
# SANA
# ==================================================

@dp.message(Order.date)
async def get_date(
    message: types.Message,
    state: FSMContext
):

    if not message.text:

        await message.answer(
            "❌ Sanani yozing."
        )

        return

    date = message.text.strip()

    if not re.fullmatch(
        r"\d{2}\.\d{2}\.\d{4}",
        date
    ):

        await message.answer(
            "❌ Sana noto'g'ri.\n\n"
            "Masalan: 25.09.2026"
        )

        return

    day, month, year = map(
        int,
        date.split(".")
    )

    if month < 1 or month > 12:

        await message.answer(
            "❌ Oy 01-12 oralig'ida bo'lishi kerak."
        )

        return

    if day < 1 or day > 31:

        await message.answer(
            "❌ Kun noto'g'ri."
        )

        return

    await state.update_data(
        date=date
    )

    data = await state.get_data()

    await message.answer(
        "💳 TO'LOV UCHUN KARTA\n\n"
        f"{CARD_NUMBER}\n\n"
        f"👤 Karta egasi: {CARD_OWNER}\n\n"
        f"💰 To'lov: {data['hall_price']}\n\n"
        "Pulni ushbu kartaga o'tkazing.\n\n"
        "🧾 Keyin chekni RASM qilib yuboring.\n\n"
        "⚠️ Faqat rasm qabul qilinadi."
    )

    await state.set_state(
        Order.payment
    )


# ==================================================
# CHEK
# ==================================================

@dp.message(Order.payment)
async def get_payment(
    message: types.Message,
    state: FSMContext
):

    if not message.photo:

        await message.answer(
            "❌ Chekni faqat RASM qilib yuboring.\n\n"
            "📸 Galereyadan chek rasmini tanlang."
        )

        return

    data = await state.get_data()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"approve_{message.from_user.id}"
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"reject_{message.from_user.id}"
                )
            ]
        ]
    )

    manager_text = (
        "💰 TO'LOV CHEKI KELDI!\n\n"
        "━━━━━━━━━━━━━━\n"
        f"🏛 To'yxona: {data['hall_name']}\n"
        f"👥 Sig'imi: {data['hall_people']}\n"
        f"💰 Summa: {data['hall_price']}\n"
        "━━━━━━━━━━━━━━\n"
        f"👤 Ism: {data['name']}\n"
        f"📞 Telefon: {data['phone']}\n"
        f"📅 Sana: {data['date']}\n"
        f"🆔 Telegram ID: {message.from_user.id}\n"
        "━━━━━━━━━━━━━━"
    )

    await bot.send_photo(
        MANAGER_ID,
        message.photo[-1].file_id,
        caption=manager_text,
        reply_markup=keyboard
    )

    await message.answer(
        "✅ Chekingiz menejerga yuborildi!\n\n"
        "⏳ To'lov tasdiqlanishini kuting."
    )


# ==================================================
# MENEJER TASDIQLASH / RAD ETISH
# ==================================================

@dp.callback_query(
    lambda c: (
        c.data.startswith("approve_")
        or c.data.startswith("reject_")
    )
)
async def payment_result(
    callback: types.CallbackQuery
):

    action, user_id = callback.data.split("_")

    user_id = int(user_id)

    if action == "approve":

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Yangi to'yxona zakaz qilaman",
                        callback_data="new_order"
                    )
                ]
            ]
        )

        await bot.send_message(
            user_id,
            "✅ TO'LOV TASDIQLANDI!\n\n"
            "🎉 To'yxonangiz muvaffaqiyatli "
            "band qilindi.\n\n"
            "Yana zakaz qilmoqchi bo'lsangiz, "
            "pastdagi tugmani bosing.",
            reply_markup=keyboard
        )

        await callback.message.edit_reply_markup(
            reply_markup=None
        )

        await callback.answer(
            "To'lov tasdiqlandi ✅"
        )

    elif action == "reject":

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Chekni qayta yuborish",
                        callback_data="retry_payment"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="➕ Yangi to'yxona zakaz qilaman",
                        callback_data="new_order"
                    )
                ]
            ]
        )

        await bot.send_message(
            user_id,
            "❌ TO'LOV TASDIQLANMADI!\n\n"
            "Iltimos, chekni qayta yuboring.",
            reply_markup=keyboard
        )

        await callback.message.edit_reply_markup(
            reply_markup=None
        )

        await callback.answer(
            "To'lov rad etildi ❌"
        )


# ==================================================
# YANGI ZAKAZ
# ==================================================

@dp.callback_query(
    lambda c: c.data == "new_order"
)
async def new_order(
    callback: types.CallbackQuery,
    state: FSMContext
):

    await state.clear()

    await callback.answer(
        "Yangi zakaz boshlanmoqda..."
    )

    await callback.message.answer(
        "🎉 YANGI TO'YXONA ZAKAZI\n\n"
        "👇 Qaysi to'yxonani band qilmoqchisiz?",
        reply_markup=hall_keyboard()
    )

    await state.set_state(
        Order.choosing_hall
    )


# ==================================================
# CHEKNI QAYTA YUBORISH
# ==================================================

@dp.callback_query(
    lambda c: c.data == "retry_payment"
)
async def retry_payment(
    callback: types.CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    await callback.message.answer(
        "🧾 Chekni qayta yuboring.\n\n"
        "⚠️ Faqat RASM qabul qilinadi."
    )

    await state.set_state(
        Order.payment
    )


# ==================================================
# RENDER WEBHOOK
# ==================================================

async def on_startup():

    render_url = os.getenv("RENDER_EXTERNAL_URL")

    if not render_url:
        raise RuntimeError(
            "RENDER_EXTERNAL_URL topilmadi."
        )

    webhook_url = render_url.rstrip("/") + "/webhook"

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await bot.set_webhook(
        webhook_url
    )

    print("🤖 BOT ISHGA TUSHDI...")
    print("Webhook:", webhook_url)


async def on_shutdown():

    await bot.delete_webhook()
    await bot.session.close()


# ==================================================
# WEB SERVER
# ==================================================

def create_app():

    app = web.Application()

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    ).register(
        app,
        path="/webhook"
    )

    setup_application(
        app,
        dp,
        bot=bot
    )

    return app


# ==================================================
# ISHGA TUSHIRISH
# ==================================================

async def main():

    app = create_app()

    app.on_startup.append(
        lambda app: on_startup()
    )

    app.on_cleanup.append(
        lambda app: on_shutdown()
    )

    port = int(
        os.getenv("PORT", "10000")
    )

    print(f"🌐 Server port: {port}")

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()

    print("🚀 WEBHOOK SERVER ISHLAYAPTI!")

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())