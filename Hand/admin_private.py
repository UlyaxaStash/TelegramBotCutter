from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession
from database.orm_query import (
    orm_add_product,
    orm_delete_product,
    orm_get_product,
    orm_get_products,
    orm_update_product,
)
from database.orm_query import orm_add_product, orm_get_product, orm_get_products, orm_delete_product
from filters.chat_types import ChatTypeFilter, IsAdmin
from kbds.inline import get_callback_btns
from kbds.reply import get_keyboard


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(['private']), IsAdmin())


class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    image = State()
    product_for_change = None

    texts = {
        'AddProduct:name': "Введите название заново:",
        'AddProduct:descriptor': "Введите описание заново:",
        'AddProduct:price': "Введите стоимость заново:",
        'AddProduct:image': "Этот стек последний, поэтому...",
    }




ADMIN_KB = get_keyboard(
    "Добавить товар",
    "Товары",
    placeholder="Выберите действие",
    sizes=(1, 1),
)
@admin_router.message(Command("admin"))
async def admin_features(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)

@admin_router.message(F.text == "Товары")
async def user_func(message: types.Message, session: AsyncSession):
    for product in await orm_get_products(session):
        await message.answer_photo(
            product.image,
            caption=f"<strong>{product.name}\
            </strong>\n{product.description}\nСтоимость: {round(product.price, 2)}",
            reply_markup=get_callback_btns(btns={
                "Удалить": f"delete_{product.id}",
                "Изменить": f"change_{product.id}"
            }),
        )
    await message.answer("Список товаров: ⏫")

@admin_router.callback_query(F.data.startswith('delete_'))
async def delete_product(callback: types.CallbackQuery, session: AsyncSession):
    product_id = callback.data.split("_")[-1]
    await orm_delete_product(session, int(product_id))

    await callback.answer("Товар удален")
    await callback.message.answer("Товар удален!")


@admin_router.callback_query(StateFilter(None), F.data.startswith('change_'))
async def change_product_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    product_id = callback.data.split("_")[-1]

    product_for_change = await orm_get_product(session, int(product_id))

    AddProduct.product_for_change = product_for_change
    await callback.answer()
    await callback.message.answer(
        "Введите название товара", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddProduct.name)

@admin_router.message(StateFilter(None), F.text == "Добавить товар")
async def add_prod_func(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название товара", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddProduct.name)


@admin_router.message(StateFilter("*"), Command("отмена"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "отмена", )
async def cancel_func(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    if AddProduct.product_for_change:
        AddProduct.product_for_change = None
    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


@admin_router.message(StateFilter("*"), Command("назад"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "назад")
async def re_func(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == AddProduct.name:
        await message.answer("Предыдущего шага нет, введите название товара")
        return
    previous = None
    for step in AddProduct.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Ок возврат к предыдущему шагу \n {AddProduct.texts[previous.state]}")
            return
        previous = step


@admin_router.message(AddProduct.name, or_f(F.text, F.text == "."))
async def add_name(message: types.Message, state: FSMContext):
    if message.text == ".":
        await state.update_data(name=AddProduct.product_for_change.name)
    else:

        if len(message.text) >= 100:
            await message.answer("Название товара не должно превышать 100 символов. \nВведите заново")
            return
        await state.update_data(name=message.text)
    await message.answer("Введите описание товара")
    await state.set_state(AddProduct.description)


@admin_router.message(AddProduct.name)
async def add_name2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, введите текст названия товара")


@admin_router.message(AddProduct.description, or_f(F.text, F.text == "."))
async def add_descr(message: types.Message, state: FSMContext):
    if message.text == ".":
        await state.update_data(description=AddProduct.product_for_change.description)
    else:
        await state.update_data(description=message.text)
    await message.answer("Цена")
    await state.set_state(AddProduct.price)

@admin_router.message(AddProduct.description)
async def add_descr2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, введите текст названия товара")

@admin_router.message(AddProduct.price, or_f(F.text, F.text == '.'))
async def add_file(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(price=AddProduct.product_for_change.price)
    else:
        try:
            float(message.text)
        except ValueError:
            await message.answer("Введите кореектную цену")
            return
        await state.update_data(price=message.text)
    await message.answer("Прикрепите файл товара")
    await state.set_state(AddProduct.image)
@admin_router.message(AddProduct.price)
async def add_price2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, введите стоимость товара")

@admin_router.message(AddProduct.image, or_f(F.photo, F.text == '.'))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text and message.text == '.':
        await state.update_data(image=AddProduct.product_for_change.image)
    else:

        await state.update_data(image=message.photo[-1].file_id)
    data = await state.get_data()
    try:
        if AddProduct.product_for_change:
            await orm_update_product(session, AddProduct.product_for_change.id, data)
        else:
            await orm_add_product(session, data)
        await message.answer("Товар добавлен", reply_marup=ADMIN_KB)
        await state.clear()
    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\nОбратитесь в поддержку", reply_markup=ADMIN_KB
        )
        await state.clear()
    AddProduct.product_for_change = None

@admin_router.message(AddProduct.image)
async def add_image2(message: types.Message, state: FSMContext):
    await message.answer("Отправьте фото")