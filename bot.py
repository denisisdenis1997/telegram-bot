import logging
import sys
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue
from quiz_manager import QuizManager

print("🚀 Бот запускается...")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

print("🔧 Инициализация бота...")

# Инициализация менеджера викторины
quiz_manager = QuizManager()

def save_user_info(update: Update):
    """Сохраняет информацию о пользователе при любом взаимодействии"""
    try:
        user = update.message.from_user
        quiz_manager.update_user_info(user.id, user.username, user.first_name)
        print(f"💾 Сохранен пользователь: {user.first_name} (ID: {user.id})")
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователя: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений (ответов) - только сообщения начинающиеся с -"""
    print(f"📨 Получено сообщение: '{update.message.text}' от {update.message.from_user.first_name}")
    
    # Игнорируем команды
    if update.message.text.startswith('/'):
        print("⚙️ Игнорируем команду")
        return
    
    # Игнорируем сообщения, которые НЕ начинаются с -
    if not update.message.text.startswith('-'):
        print("⚙️ Игнорируем сообщение (не начинается с -)")
        return
    
    user = update.message.from_user
    # Убираем - из начала ответа для проверки
    user_answer = update.message.text[1:].strip()
    
    # Проверяем, что после - есть текст
    if not user_answer:
        print("⚙️ Игнорируем сообщение (пустой ответ после -)")
        await update.message.reply_text("💡 Напиши ответ после дефиса!\nПример: - париж")
        return
    
    print(f"🔍 Проверяем ответ от {user.first_name}: '{user_answer}'")
    
    # Сохраняем информацию о пользователе
    save_user_info(update)
    
    # Проверяем ответ
    is_correct, reason = quiz_manager.check_answer(user.id, user_answer, context, update.effective_chat.id)
    
    print(f"📊 Результат проверки: correct={is_correct}, reason={reason}")
    
    if reason == "already_answered":
        print(f"⚠️ Пользователь {user.first_name} пытался ответить после правильного ответа")
        
        # Получаем информацию о том, кто ответил первым
        first_responder_info = quiz_manager.get_first_responder_info()
        
        if first_responder_info:
            responder_name = first_responder_info.get('first_name', 'другой участник')
            await update.message.reply_text(f"❌ Опоздал! На этот вопрос уже ответил {responder_name}!")
        else:
            await update.message.reply_text("❌ На этот вопрос уже ответили!")
            
    elif reason == "no_question":
        print("⚠️ Нет активного вопроса")
        await update.message.reply_text(
            "ℹ️ Сейчас нет активной викторины.\n"
            "Жди следующую викторину по расписанию! 📅\n"
            "Используй /schedule чтобы посмотреть расписание."
        )
        
    elif is_correct:
        user_score = quiz_manager.get_user_score(user.id)
        print(f"✅ Правильный ответ! {user.first_name} получает очко. Счет: {user_score}")
        
        # Поздравление для победителя
        import random
        congrats_messages = [
            f"🎉 БИНГО! {user.first_name} получает 1 очко!",
            f"✅ В ЯБЛОЧКО! {user.first_name} +1 очко!",
            f"🏆 ВЕРНО! {user.first_name} зарабатывает очко!",
            f"⭐ ОТЛИЧНО! {user.first_name} получает 1 балл!",
            f"🎯 ПОПАДАНИЕ! {user.first_name} +1 к счету!",
        ]
        congrats_message = random.choice(congrats_messages)
        
        await update.message.reply_text(
            f"{congrats_message}\n"
            f"📊 Твой счет: {user_score}\n\n"
            f"Используй /leaderboard чтобы посмотреть таблицу лидеров!"
        )
    else:
        # НИКАКОЙ РЕАКЦИИ НА НЕПРАВИЛЬНЫЕ ОТВЕТЫ - УБИРАЕМ СПАМ
        print(f"❌ Неправильный ответ от {user.first_name} - игнорируем")
        # НЕ отправляем сообщение - просто игнорируем

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    save_user_info(update)
    
    # Сохраняем ID чата для автоматических викторин
    chat_id = update.effective_chat.id
    quiz_manager.add_chat_id(chat_id)
    print(f"💾 Сохранен чат ID: {chat_id} для автоматических викторин")
    
    quiz_times = quiz_manager.get_quiz_times()
    times_text = "\n".join([f"• {time}" for time in quiz_times])
    
    welcome_text = f"""
🤖 Добро пожаловать в Карась-викторину!

🕐 Карась-Викторины запускаются автоматически каждый день в 12:00!

🎯 Доступные команды:
/start - показать это сообщение
/leaderboard - таблица лидеров
/question - показать текущий вопрос
/schedule - показать расписание
/profile - мой профиль и уровень
/achievements - мои достижения
/next_quiz - когда следующая Карась-викторина
/reset_stats - сброс статистики (только для админов)

💡 Просто напиши ответ в чат, когда увидишь вопрос!
Первый правильный ответ = 1 Карась-балл!

🏆 Накопи очки чтобы повысить уровень и получить достижения!
    """
    await update.message.reply_text(welcome_text)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /leaderboard"""
    save_user_info(update)
    
    leaders = quiz_manager.get_leaderboard()
    
    if not leaders:
        await update.message.reply_text("📊 Пока никто не заработал Карась-баллов. Будь первым!")
        return
    
    leaderboard_text = "🏆 ТАБЛИЦА ЛИДЕРОВ:\n\n"
    for i, (user_id, user_data) in enumerate(leaders, 1):
        name = user_data.get('username') or user_data.get('first_name') or f"User{user_id}"
        score = user_data.get('score', 0)
        level = quiz_manager.get_user_level(score)
        level_emoji = quiz_manager.get_user_profile(user_id)['level_emoji']
        leaderboard_text += f"{i}. {name}: {score} очков {level_emoji} Ур.{level}\n"
    
    # Добавляем общее количество игроков
    all_users = quiz_manager.load_users().get('users', {})
    total_players = len(all_users)
    leaderboard_text += f"\n👥 Всего игроков: {total_players}"
    
    await update.message.reply_text(leaderboard_text)

async def question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /question - показывает текущий вопрос"""
    print(f"🔍 Команда /question от {update.message.from_user.first_name}")
    
    save_user_info(update)
    
    current_question = quiz_manager.get_current_question()
    print(f"📋 Текущий вопрос из базы: {current_question}")
    
    if current_question:
        response_text = f"📝 ТЕКУЩИЙ ВОПРОС:\n\n{current_question['question']}"
        print(f"✅ Отправляем вопрос: {current_question['question'][:50]}...")
    else:
        response_text = (
            "ℹ️ Сейчас нет активного вопроса.\n"
            "Следующая викторина по расписанию!"
        )
        print("❌ Нет активного вопроса")
    
    await update.message.reply_text(response_text)

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /schedule - показывает расписание"""
    save_user_info(update)
    
    quiz_times = quiz_manager.get_quiz_times()
    if quiz_times:
        times_text = "\n".join([f"• {time}" for time in quiz_times])
        await update.message.reply_text(f"🕐 Расписание викторин (МСК):\n\n{times_text}")
    else:
        await update.message.reply_text("📅 Расписание не настроено.")

async def next_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает, когда следующая викторина"""
    save_user_info(update)
    
    quiz_times = quiz_manager.get_quiz_times()
    if not quiz_times:
        await update.message.reply_text("📅 Расписание не настроено.")
        return
    
    # Просто показываем расписание
    times_text = "\n".join([f"• {time}" for time in quiz_times])
    await update.message.reply_text(f"🕐 Следующие викторины (МСК):\n\n{times_text}")

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ручной запуск викторины (только для админов)"""
    save_user_info(update)
    
    try:
        # Проверка прав администратора
        chat_admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]
        
        if update.message.from_user.id not in admin_ids:
            await update.message.reply_text("❌ Эта команда только для администраторов чата!")
            return
        
        await update.message.reply_text("🔄 Запускаю викторину...")
        
        # Запускаем викторину
        await send_quiz_to_chat(update.effective_chat.id, context)
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при запуске викторины: {e}")
        print(f"❌ Ошибка quiz: {e}")

async def reset_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сброс всей статистики (только для админов)"""
    save_user_info(update)
    
    try:
        # Проверка прав администратора
        chat_admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]
        
        if update.message.from_user.id not in admin_ids:
            await update.message.reply_text("❌ Эта команда только для администраторов чата!")
            return
        
        # Сбрасываем статистику
        quiz_manager.reset_all_stats()
        
        await update.message.reply_text(
            "🔄 Вся статистика сброшена! 🎯\n\n"
            "✅ Таблица лидеров очищена\n"
            "✅ Все вопросы разблокированы\n" 
            "✅ Текущий вопрос сброшен\n"
            "✅ Все достижения сброшены\n"
            "📊 Теперь все начинают с 0 очков!\n\n"
            "Запусти новую викторину командой /quiz"
        )
        print(f"✅ Статистика сброшена администратором {update.message.from_user.first_name}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при сбросе статистики: {e}")
        print(f"❌ Ошибка reset_stats: {e}")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает профиль пользователя"""
    save_user_info(update)
    
    user = update.message.from_user
    profile = quiz_manager.get_user_profile(user.id)
    
    profile_text = f"""
👤 ПРОФИЛЬ: {user.first_name}

{profile['level_emoji']} Уровень: {profile['level']} ({profile['level_name']})
⭐ Очки: {profile['score']}
🏅 Достижений: {len(profile['achievements'])}
📈 Прогресс: {profile['progress_percent']}%

🎯 До следующего уровня: {profile['next_level_points'] - profile['score'] if isinstance(profile['next_level_points'], int) else 'максимум'} очков
    """
    
    await update.message.reply_text(profile_text)

async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает достижения пользователя"""
    save_user_info(update)
    
    user = update.message.from_user
    user_achievements = quiz_manager.get_user_achievements(user.id)
    profile = quiz_manager.get_user_profile(user.id)
    
    if not user_achievements:
        await update.message.reply_text(
            f"🎯 У тебя пока нет достижений, {user.first_name}!\n"
            f"🏆 Продолжай участвовать в викторинах чтобы получить свои первые награды!\n\n"
            f"📊 Твой уровень: {profile['level_emoji']} {profile['level_name']}\n"
            f"⭐ Очков: {profile['score']}"
        )
        return
    
    achievements_text = f"🏅 ТВОИ ДОСТИЖЕНИЯ, {user.first_name}:\n\n"
    
    for ach_id in user_achievements:
        ach = quiz_manager.ACHIEVEMENTS[ach_id]
        achievements_text += f"{ach['icon']} {ach['name']}\n{ach['description']}\n\n"
    
    achievements_text += f"📊 Уровень: {profile['level_emoji']} {profile['level_name']}\n"
    achievements_text += f"⭐ Очков: {profile['score']}\n"
    achievements_text += f"🎯 До следующего уровня: {profile['next_level_points'] - profile['score'] if isinstance(profile['next_level_points'], int) else 'максимум'} очков"
    
    await update.message.reply_text(achievements_text)

async def test_scheduler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая команда для проверки планировщика"""
    save_user_info(update)
    
    try:
        # Проверка прав администратора
        chat_admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]
        
        if update.message.from_user.id not in admin_ids:
            await update.message.reply_text("❌ Эта команда только для администраторов чата!")
            return
        
        await update.message.reply_text("🧪 Тестируем планировщик...")
        
        # Запускаем викторину через планировщик через 10 секунд
        context.job_queue.run_once(
            scheduled_quiz, 
            10,  # через 10 секунд
            chat_id=update.effective_chat.id,
            name="test_scheduled_quiz"
        )
        
        await update.message.reply_text("✅ Тест запущен! Викторина придет через 10 секунд...")
        print("⏰ Тестовый запуск планировщика через 10 секунд")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка тестирования: {e}")
        print(f"❌ Ошибка test_scheduler: {e}")

async def active_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает активные чаты (только для админов)"""
    save_user_info(update)
    
    try:
        # Проверка прав администратора
        chat_admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]
        
        if update.message.from_user.id not in admin_ids:
            await update.message.reply_text("❌ Эта команда только для администраторов чата!")
            return
        
        active_chats = quiz_manager.get_active_chats()
        
        if not active_chats:
            await update.message.reply_text("📊 Нет активных чатов")
            return
        
        chats_text = "📊 АКТИВНЫЕ ЧАТЫ:\n\n"
        for i, chat_id in enumerate(active_chats, 1):
            try:
                chat = await context.bot.get_chat(chat_id)
                chat_name = chat.title or chat.first_name or f"Чат {chat_id}"
                chats_text += f"{i}. {chat_name} (ID: {chat_id})\n"
            except:
                chats_text += f"{i}. Неизвестный чат (ID: {chat_id})\n"
        
        await update.message.reply_text(chats_text)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
        print(f"❌ Ошибка active_chats: {e}")

async def send_quiz_to_chat(chat_id, context):
    """Отправляет викторину в указанный чат"""
    try:
        question_data = quiz_manager.get_random_question()
        if question_data:
            print(f"📝 Устанавливаем новый вопрос: {question_data['question']}")
            quiz_manager.set_current_question(question_data)
            
            message = (
                f"🧠 ВИКТОРИНА!\n\n"
                f"{question_data['question']}\n\n"
                f"💡 Отвечайте, начиная сообщение с ДЕФИСА:\n"
                f"- ваш ответ\n\n"
                f"🎯 Первый правильный ответ получает 1 Карась-балл!"
            )
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=message
            )
            print(f"✅ Викторина отправлена в чат {chat_id}!")
            return True
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="😔 На сегодня вопросы закончились!"
            )
            return False
    except Exception as e:
        print(f"❌ Ошибка при отправке викторины: {e}")
        return False

async def scheduled_quiz(context: ContextTypes.DEFAULT_TYPE):
    """Функция для запуска викторины по расписанию"""
    print("🕐 Запуск викторины по расписанию...")
    
    # Получаем все активные чаты
    active_chats = quiz_manager.get_active_chats()
    print(f"📋 Активные чаты: {active_chats}")
    
    if not active_chats:
        print("⚠️ Нет активных чатов для отправки викторины")
        return
    
    # Отправляем викторину во все активные чаты
    successful_sends = 0
    for chat_id in active_chats:
        try:
            result = await send_quiz_to_chat(chat_id, context)
            if result:
                successful_sends += 1
        except Exception as e:
            print(f"❌ Ошибка отправки в чат {chat_id}: {e}")
    
    print(f"✅ Викторина отправлена в {successful_sends} из {len(active_chats)} чатов")

def setup_scheduler(application):
    """Настраивает планировщик для автоматических викторин"""
    try:
        job_queue = application.job_queue
        
        if job_queue is None:
            print("❌ JobQueue недоступен")
            return
        
        # Время викторин (МСК)
        quiz_times_msk = ["12:00"]
        
        print(f"⏰ Настройка планировщика для времени: {quiz_times_msk}")
        
        for time_msk in quiz_times_msk:
            try:
                # Конвертируем МСК в UTC (МСК = UTC+3)
                hours_msk, minutes = map(int, time_msk.split(':'))
                hours_utc = (hours_msk - 3) % 24  # МСК -> UTC
                
                # Правильное создание объекта времени
                from datetime import time as dt_time
                time_utc = dt_time(hour=hours_utc, minute=minutes, second=0)
                
                # Создаем job для каждого времени
                job_queue.run_daily(
                    scheduled_quiz,
                    time=time_utc,
                    days=tuple(range(7)),  # Все дни недели
                    name=f"quiz_{time_msk}"
                )
                print(f"✅ Викторина настроена на {time_msk} МСК ({hours_utc:02d}:{minutes:02d} UTC)")
                
            except Exception as e:
                print(f"❌ Ошибка настройки времени {time_msk}: {e}")
        
        print("✅ Планировщик успешно настроен!")
        
    except Exception as e:
        print(f"❌ Ошибка настройки планировщика: {e}")

def main():
    """Основная функция"""
    print("🔄 Запуск основной функции...")
    
    try:
        # Импортируем токен напрямую из config
        from config import BOT_TOKEN
        
        if BOT_TOKEN == "ВАШ_ТОКЕН_ОТ_BOTFATHER":
            print("❌ ЗАМЕНИТЕ ТОКЕН В config.py на настоящий!")
            input("Нажмите Enter чтобы выйти...")
            return
        
        print("✅ Токен загружен")
        
        # Создание приложения
        application = Application.builder().token(BOT_TOKEN).build()
        print("✅ Приложение создано")
        
        # Добавление обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("leaderboard", leaderboard))
        application.add_handler(CommandHandler("question", question))
        application.add_handler(CommandHandler("schedule", schedule))
        application.add_handler(CommandHandler("next_quiz", next_quiz))
        application.add_handler(CommandHandler("quiz", quiz))
        application.add_handler(CommandHandler("reset_stats", reset_stats))
        application.add_handler(CommandHandler("profile", profile))
        application.add_handler(CommandHandler("achievements", achievements))
        application.add_handler(CommandHandler("test_schedule", test_scheduler))
        application.add_handler(CommandHandler("active_chats", active_chats))
        
        # Обработчик сообщений ДОЛЖЕН БЫТЬ ПОСЛЕДНИМ!
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("✅ Все обработчики добавлены")
        
        # Настройка планировщика
        setup_scheduler(application)
        
        # Запуск бота
        print("🎯 Бот запускается для опроса...")
        print("⏰ Викторины будут каждые день в 12:00")
        print("🧪 Для тестирования используйте /test_schedule")
        print("🔄 Для сброса статистики используйте /reset_stats (админы)")
        print("🏆 Доступны команды /profile и /achievements")
        print("🔇 Бот НЕ реагирует на неправильные ответы (убрали спам)")
        print("🤖 Включено fuzzy-сравнение ответов (80% совпадение)")
        print("Остановите бота комбинацией Ctrl+C")
        
        # Используем run_polling вместо asyncio
        application.run_polling()
        
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter чтобы выйти...")

if __name__ == '__main__':
    print("📦 Запуск из main...")
    main()
    print("👋 Бот завершил работу")
