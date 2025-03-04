import logging
import os
import csv
import pytz
from datetime import datetime, timedelta
from telegram import Update, InputFile, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка расписания намаза из CSV

def load_prayer_times(filename="prayer_times.csv"):
    prayer_times = {}
    try:
        with open(filename, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                prayer_times[row['date']] = {
                    "fajr": row['fajr'],
                    "dhuhr": row['dhuhr'],
                    "asr": row['asr'],
                    "maghrib": row['maghrib'],
                    "isha": row['isha']
                }
    except FileNotFoundError:
        logger.error(f"Файл {filename} не найден.")
    except Exception as e:
        logger.error(f"Ошибка при загрузке расписания: {e}")
    return prayer_times

# Функция для перевода названий намазов на русский

def translate_prayer_name(prayer_name):
    translations = {
        "fajr": "Фаджр",
        "dhuhr": "Зухр",
        "asr": "Аср",
        "maghrib": "Магриб",
        "isha": "Иша"
    }
    return translations.get(prayer_name, prayer_name)  # Если название неизвестно, оставить как есть


# Функция для отправки уведомлений
async def send_notification(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    user_id = job_data['user_id']
    prayer_name = translate_prayer_name(job_data['prayer_name'])  # Перевод названия намаза
    prayer_time = job_data['prayer_time']
    await context.bot.send_message(
        chat_id=user_id,
        text=f"До намаза <b>{prayer_name}</b> осталось 5 минут! <i>Время намаза:</i> <b>{prayer_time}</b>",
        parse_mode="HTML",
        reply_markup=keyboard  # Добавление клавиатуры с кнопками
    )


# Преобразование даты в формат "3 марта 2025"
def format_date(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    return f"{date_obj.day} {months[date_obj.month - 1]} {date_obj.year}"

# Клавиатура
keyboard = ReplyKeyboardMarkup(
    [["Расписание на сегодня"], ["Расписание на месяц"]],
    resize_keyboard=True,
    one_time_keyboard=False  # Устанавливаем False, чтобы клавиатура оставалась видимой
)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user_name = update.message.from_user.first_name
    user_username = update.message.from_user.username
    user_data = f"Пользователь {user_name} (@{user_username}) с ID {user_id} начал использовать бота."
    await context.bot.send_message(chat_id=7162436316, text=user_data, parse_mode="HTML")

    
    # Форматируем сообщение с использованием HTML
    welcome_message = (
        "<i>Бот активирован!</i> &#129302;\n"
        "Вам автоматически уведомления <b>за 5 минут до начала намаза</b> отправляются 💫\n\n"
        "Также можете посмотреть👁 \n"
        "📆 <i>Расписание на <b>сегодня</b> - </i>/today \n"
        "📆 <i>Расписание на <b>месяц</b> - </i>/month \n"
    )
    
    await update.message.reply_text(
        welcome_message,        
        reply_markup=keyboard,  # Добавление клавиатуры с кнопками
        parse_mode="HTML"  # Указываем, что сообщение будет в HTML
    )
    
    context.user_data['user_id'] = user_id
    schedule_notifications(user_id, context)

# Обработка команды /today
async def handle_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime("%Y-%m-%d")
    prayer_times = load_prayer_times()
    if today in prayer_times:
        times = prayer_times[today]
        formatted_date = format_date(today)
        
        # Форматирование сообщения с использованием HTML
        message = (f"📆 <b>Расписание намаза на сегодня</b> ({formatted_date}):\n\n"
                   f"🏙 <b>Фаджр:</b>     {times['fajr']}\n"
                   f"🌅 <b>Зухр:</b>         {times['dhuhr']}\n"
                   f"🌇 <b>Аср:</b>           {times['asr']}\n"
                   f"🌌 <b>Магриб:</b>    {times['maghrib']}\n"
                   f"🌃 <b>Иша:</b>          {times['isha']}\n\n"
                   "<i>Сообщите, если время намаза неправильно — @m_fayziev</i>")
        await update.message.reply_text(message, reply_markup=keyboard, parse_mode="HTML")  # Добавление клавиатуры с кнопками и HTML
    else:
        # Если расписание на сегодня не найдено
        await update.message.reply_text("<b>Расписание на сегодня не найдено.</b>", reply_markup=keyboard, parse_mode="HTML")

# Обработка команды /month
async def handle_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Получаем текущий месяц и год
        current_month_year = datetime.now().strftime("%B %Y")
        
        # Переводим название месяца на русский
        months = {
            "January": "Январь", "February": "Февраль", "March": "Март", "April": "Апрель",
            "May": "Май", "June": "Июнь", "July": "Июль", "August": "Август", "September": "Сентябрь",
            "October": "Октябрь", "November": "Ноябрь", "December": "Декабрь"
        }
        russian_month = months[current_month_year.split()[0]]
        russian_year = current_month_year.split()[1]

        # Отправляем картинку с расписанием
        with open("month.jpg", "rb") as photo:
            # Сначала отправляем картинку
            await update.message.reply_photo(photo=InputFile(photo))

            # Теперь отправляем сообщение с информацией о месяце
            message = f"📆 Расписание намаза на {russian_month} {russian_year}\n\n" \
                      "🕌 @namaz_tomsk_bot - Время намаза Томск\n" \
                      "🏠 Красная сборная мечеть"

            # Отправляем текстовое сообщение
            await update.message.reply_text(message, reply_markup=keyboard)

    except FileNotFoundError:
        await update.message.reply_text("Файл с расписанием на месяц не найден.", reply_markup=keyboard)  # Добавление клавиатуры с кнопками


# Функция для планирования уведомлений
def schedule_notifications(user_id, context: ContextTypes.DEFAULT_TYPE):
    prayer_times = load_prayer_times()
    today = datetime.now().strftime("%Y-%m-%d")
    tz = pytz.timezone("Asia/Tomsk")
    now = datetime.now(tz)
    
    if today in prayer_times:
        times = prayer_times[today]
        for prayer_name, prayer_time in times.items():
            try:
                # Проверяем, не запланировано ли уведомление для этого времени
                prayer_datetime = datetime.strptime(f"{today} {prayer_time}", "%Y-%m-%d %H:%M")
                prayer_datetime = tz.localize(prayer_datetime)
                notification_time = prayer_datetime - timedelta(minutes=5)
                
                # Логируем информацию для отладки
                logger.info(f"Планирование уведомления для {prayer_name}: {notification_time}")
                
                if notification_time > now:
                    # Запланировать уведомление, если оно еще не было запланировано
                    context.job_queue.run_once(
                        send_notification,
                        when=notification_time,
                        data={
                            'user_id': user_id,
                            'prayer_name': prayer_name,
                            'prayer_time': prayer_time
                        }
                    )
                    logger.info(f"Уведомление для {prayer_name} запланировано на {notification_time}.")
                else:
                    logger.warning(f"Время уведомления для {prayer_name} уже прошло.")
            except Exception as e:
                logger.error(f"Ошибка при планировании уведомления для {prayer_name}: {e}")


# Основная функция
def main():
    token = "7332091058:AAFgNFNHQVr6npjk1i1fMPVGX8cXZ0PfyRY"
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("today", handle_today))
    application.add_handler(CommandHandler("month", handle_month))
    application.add_handler(MessageHandler(filters.Text(["Расписание на сегодня"]), handle_today))
    application.add_handler(MessageHandler(filters.Text(["Расписание на месяц"]), handle_month))
    application.run_polling()

if __name__ == "__main__":
    main()
