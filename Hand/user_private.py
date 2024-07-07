from aiogram import Bot, types, Router, F
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_products
from filters.chat_types import ChatTypeFilter
from kbds import reply
from aiogram.utils.formatting import as_list, as_marked_section, Bold
from aiogram.types import FSInputFile

from kbds.inline import get_callback_btns

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(['private']))

@user_private_router.message(
    (F.text.lower().contains('меню')) | (F.text.lower().contains('поним')) | (F.text.lower().contains('помо')) | (
            F.text.lower() == 'старт') | (F.text.lower().contains('привет')) | (F.text.lower().contains('здрав')) | (
            F.text.lower() == 'start') | ((F.text.lower().contains('добр'))))
@user_private_router.message(Command('start'))
async def start_function(message: types.Message):
    await message.answer('''Приветствую, я бот-помощник!
Воспользуйтесь, пожалуйста, кнопками меню снизу, чтобы посмотреть цены''',
                         reply_markup=reply.get_keyboard(
                             "Связаться с нами",
                             "Цены",
                             "Доставка",
                             placeholder="Что Вас интересует?",
                             sizes=(1, 1, 2)
                         ),
                         )
@user_private_router.message(Command('prices'))
@user_private_router.message(F.text == "Цены")
async def prices_function(message: types.Message, session: AsyncSession):
    for product in await orm_get_products(session):
        await message.answer_photo(
            product.image,
            caption=f"<strong>{product.name}\
            </strong>\n{product.description}\nСтоимость: {round(product.price, 2)}"
        )
    await message.answer("Список товаров: ⏫")
@user_private_router.message(F.text == "Привод")
async def privod_funtion(message: types.Message):
    await message.reply("Выберите вариант коммерческого предложения",
                        reply_markup=reply.get_keyboard(
                            "Модернизация привода 1.0",
                            "Модернизация привода 2.0",
                            placeholder="Какая услуга Вас интересует?",
                            sizes=(1, 1))
                        )
@user_private_router.message(F.text == "Куттер")
async def cutter_funtion(message: types.Message):
    await message.reply("Выберите вариант коммерческого предложения",
                        reply_markup=reply.get_keyboard(
                            "Модернизируем Ваш куттер",
                            "Модернизация без предоплаты",
                            "Полный пакет услуг",
                            placeholder="Какая услуга Вас интересует?",
                            sizes=(1, 1, 1))
                        )

@user_private_router.message((F.text.lower().contains('челов')) | (F.text.lower().contains('операт')) |
                             (F.text.lower().contains('говор')) | (F.text.lower().contains('спрос')) |
                             (F.text.lower().contains('диспет')) | (F.text.lower().contains('консул')) |
                             (F.text.lower().contains('связ')) | (F.text.lower().contains('совет')))
@user_private_router.message(Command('human'))
async def human_function(message: types.Message):
    await message.reply('''Напишите пожалуйста в ТГ на номер: +79214452356, Ульяна
Или позвоните по номеру: 
+79105122834, Игорь''')

@user_private_router.message(F.text == "Доставка")
@user_private_router.message(Command('delivery'))
async def about_function(message: types.Message):
    text = as_marked_section(
        Bold("Варианты доставки:"),
        "Почта россии",
        "СДЭК (по договоренности)",
        marker="✅",
    )
    await message.answer(text.as_html())

@user_private_router.message(F.contact)
async def get_contact(message: types.Message):
    await message.answer(f"Номер получен")
    await message.answer(str(message.contact))


@user_private_router.message(F.location)
async def get_location(message: types.Message):
    await message.answer(f"Локация получена")
    await message.answer(str(message.location))
