import json
import random
from datetime import datetime, timedelta
import os

# Импортируем из config вместо прямого определения
from config import QUESTIONS_FILE, SETTINGS_FILE, USERS_FILE, BOT_TOKEN

class QuizManager:
    def __init__(self):
        print("🔧 Инициализация QuizManager...")
        self.ensure_data_files()
        self.clean_old_questions_if_needed()
        print("✅ QuizManager инициализирован!")
    
    def ensure_data_files(self):
        """Создает необходимые файлы и папки если их нет"""
        print("📁 Проверка файлов данных...")
        os.makedirs("data", exist_ok=True)
        
        # Создаем questions.json если нет или он пустой/битый
        if not os.path.exists(QUESTIONS_FILE) or os.path.getsize(QUESTIONS_FILE) == 0:
            print("📝 Создаю questions.json...")
            sample_questions = {
                "questions": [
                    {
                        "id": 1,
                        "question": "Какой химический элемент обозначается как 'Fe'?",
                        "answer": "железо",
                        "used": False,
                        "used_date": None
                    },
                    {
                        "id": 2, 
                        "question": "Столица Франции?",
                        "answer": "париж",
                        "used": False,
                        "used_date": None
                    },
                    {
                        "id": 3,
                        "question": "Сколько планет в Солнечной системе?",
                        "answer": "8",
                        "used": False,
                        "used_date": None
                    }
                ]
            }
            with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(sample_questions, f, ensure_ascii=False, indent=2)
            print("✅ questions.json создан!")
        else:
            print("✅ questions.json уже существует")
        
        # Создаем settings.json если нет или он пустой/битый
        if not os.path.exists(SETTINGS_FILE) or os.path.getsize(SETTINGS_FILE) == 0:
            print("⚙️ Создаю settings.json...")
            default_settings = {
                "quiz_schedule": [
                    {"time": "12:00", "enabled": True},
                    {"time": "18:00", "enabled": True}
                ],
                "auto_reset_used_questions": True,
                "reset_after_days": 30
            }
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_settings, f, ensure_ascii=False, indent=2)
            print("✅ settings.json создан!")
        else:
            print("✅ settings.json уже существует")
        
        # Создаем users.json если нет или он пустой/битый
        if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
            print("👥 Создаю users.json...")
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            print("✅ users.json создан!")
        else:
            print("✅ users.json уже существует")
        
        print("✅ Все файлы данных проверены!")
    
    def load_questions(self):
        """Загрузка вопросов из JSON"""
        try:
            with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ Загружено {len(data.get('questions', []))} вопросов")
                return data.get("questions", [])
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка JSON в questions.json: {e}")
            # Пересоздаем файл если он битый
            self.ensure_data_files()
            return self.load_questions()
        except Exception as e:
            print(f"❌ Ошибка загрузки вопросов: {e}")
            return []
    
    def save_questions(self, questions):
        """Сохранение вопросов в JSON"""
        try:
            data = {"questions": questions}
            with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"💾 questions.json сохранен ({len(questions)} вопросов)")
        except Exception as e:
            print(f"❌ Ошибка сохранения вопросов: {e}")
    
    def load_users(self):
        """Загрузка пользователей из JSON"""
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка JSON в users.json: {e}")
            # Пересоздаем файл если он битый
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            return {}
        except Exception as e:
            print(f"❌ Ошибка загрузки пользователей: {e}")
            return {}
    
    def save_users(self, users):
        """Сохранение пользователей в JSON"""
        try:
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            print(f"💾 users.json успешно сохранен ({len(users)} записей)")
        except Exception as e:
            print(f"❌ Ошибка сохранения пользователей: {e}")
    
    def load_settings(self):
        """Загрузка настроек из JSON"""
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка JSON в settings.json: {e}")
            # Пересоздаем файл если он битый
            self.ensure_data_files()
            return self.load_settings()
        except Exception as e:
            print(f"❌ Ошибка загрузки настроек: {e}")
            return {}
    
    def clean_old_questions_if_needed(self):
        """Очистка старых использованных вопросов"""
        settings = self.load_settings()
        if not settings.get("auto_reset_used_questions", True):
            return
        
        reset_days = settings.get("reset_after_days", 30)
        questions = self.load_questions()
        changed = False
        
        for q in questions:
            if q.get("used") and q.get("used_date"):
                try:
                    used_date = datetime.fromisoformat(q["used_date"])
                    if datetime.now() - used_date > timedelta(days=reset_days):
                        q["used"] = False
                        q["used_date"] = None
                        changed = True
                except:
                    continue
        
        if changed:
            self.save_questions(questions)
    
    def get_random_question(self):
        """Получение случайного неиспользованного вопроса"""
        questions = self.load_questions()
        if not questions:
            print("❌ Нет вопросов в базе!")
            return None
            
        unused_questions = [q for q in questions if not q.get("used", False)]
        
        if not unused_questions:
            print("🔄 Сбрасываю все вопросы...")
            for q in questions:
                q["used"] = False
                q["used_date"] = None
            self.save_questions(questions)
            unused_questions = questions
        
        if unused_questions:
            question = random.choice(unused_questions)
            # НЕ помечаем вопрос как использованный здесь - это сделает set_current_question
            print(f"✅ Выбран вопрос: {question['question']}")
            return question
        
        return None
    
    def get_current_question(self):
        """Получение текущего активного вопроса"""
        users_data = self.load_users()
        return users_data.get("current_question")
    
    def set_current_question(self, question):
        """Установка текущего активного вопроса и пометка его как использованного"""
        print(f"📝 Устанавливаем текущий вопрос: {question['question']}")
        
        # Помечаем вопрос как использованный в questions.json
        questions = self.load_questions()
        question_updated = False
        for q in questions:
            if q['id'] == question['id']:
                q['used'] = True
                q['used_date'] = datetime.now().isoformat()
                question_updated = True
                print(f"✅ Вопрос {question['id']} помечен как использованный в questions.json")
                break
        
        if question_updated:
            self.save_questions(questions)
            print("💾 questions.json обновлен")
        else:
            print("⚠️ Вопрос не найден в questions.json для обновления")
        
        # Устанавливаем текущий вопрос в users.json
        users_data = self.load_users()
        users_data["current_question"] = question
        users_data["answered_users"] = []  # Сбрасываем список ответивших
        
        self.save_users(users_data)
        print("💾 Текущий вопрос сохранен в users.json")
    
    def check_answer(self, user_id, answer):
        """Проверка ответа пользователя"""
        users_data = self.load_users()
        current_question = users_data.get("current_question")
        answered_users = users_data.get("answered_users", [])
        
        print(f"🔍 Проверка ответа: user_id={user_id}, answer='{answer}'")
        print(f"📋 Текущий вопрос: {current_question}")
        print(f"👥 Уже ответили: {answered_users}")
        
        if not current_question:
            print("❌ Нет активного вопроса")
            return False, "no_question"
        
        # Проверяем, отвечал ли уже пользователь
        if str(user_id) in answered_users:
            print(f"⚠️ Пользователь {user_id} уже отвечал")
            return False, "already_answered"
        
        correct_answer = current_question["answer"].lower().strip()
        user_answer = answer.lower().strip()
        
        print(f"📊 Сравнение: '{user_answer}' vs '{correct_answer}'")
        
        is_correct = user_answer == correct_answer
        
        if is_correct:
            print(f"✅ Правильный ответ от пользователя {user_id}")
            # Добавляем пользователя в список ответивших
            answered_users.append(str(user_id))
            users_data["answered_users"] = answered_users
            
            # Обновляем счет пользователя
            self.update_user_score(user_id, 1)
            
            # Сохраняем изменения
            self.save_users(users_data)
            print(f"💾 Данные сохранены: answered_users={answered_users}")
        else:
            print(f"❌ Неправильный ответ от пользователя {user_id}")
        
        return is_correct, "correct" if is_correct else "wrong"
    
    def update_user_score(self, user_id, points=1):
        """Обновление счета пользователя"""
        print(f"📊 Обновление счета: user_id={user_id}, points={points}")
        
        users_data = self.load_users()
        
        if "users" not in users_data:
            users_data["users"] = {}
            print("👥 Создан новый раздел users")
        
        user_str = str(user_id)
        if user_str not in users_data["users"]:
            users_data["users"][user_str] = {
                "score": 0,
                "username": "",
                "first_name": ""
            }
            print(f"👤 Создан новый пользователь: {user_str}")
        
        users_data["users"][user_str]["score"] += points
        print(f"🎯 Пользователь {user_str} теперь имеет {users_data['users'][user_str]['score']} очков")
        
        # Сохраняем изменения
        self.save_users(users_data)
        print("💾 Счет пользователя сохранен")
    
    def update_user_info(self, user_id, username, first_name):
        """Обновление информации о пользователе"""
        users_data = self.load_users()
        
        if "users" not in users_data:
            users_data["users"] = {}
        
        user_str = str(user_id)
        if user_str not in users_data["users"]:
            users_data["users"][user_str] = {
                "score": 0,
                "username": username or "",
                "first_name": first_name or ""
            }
        else:
            users_data["users"][user_str]["username"] = username or ""
            users_data["users"][user_str]["first_name"] = first_name or ""
        
        self.save_users(users_data)
    
    def get_leaderboard(self):
        """Получение таблицы лидеров"""
        users_data = self.load_users()
        users = users_data.get("users", {})
        
        sorted_users = sorted(
            users.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )[:10]
        
        return sorted_users
    
    def get_user_score(self, user_id):
        """Получение счета конкретного пользователя"""
        users_data = self.load_users()
        user = users_data.get("users", {}).get(str(user_id), {})
        return user.get("score", 0)
    
    def get_quiz_times(self):
        """Получение расписания викторин"""
        settings = self.load_settings()
        return [s["time"] for s in settings.get("quiz_schedule", []) if s.get("enabled", True)]
    
    def add_quiz_time(self, time):
        """Добавление времени викторины"""
        settings = self.load_settings()
        settings["quiz_schedule"].append({"time": time, "enabled": True})
        self.save_settings(settings)
    
    def remove_quiz_time(self, time):
        """Удаление времени викторины"""
        settings = self.load_settings()
        settings["quiz_schedule"] = [s for s in settings["quiz_schedule"] if s["time"] != time]
        self.save_settings(settings)
    
    def get_all_users_count(self):
        """Получает общее количество зарегистрированных пользователей"""
        users_data = self.load_users()
        users = users_data.get('users', {})
        return len(users)

    def get_first_responder_info(self):
        """Получает информацию о первом ответившем пользователе"""
        users_data = self.load_users()
        answered_users = users_data.get("answered_users", [])
        
        if not answered_users:
            return None
        
        # Берем первого ответившего (первый в списке)
        first_responder_id = answered_users[0]
        users = users_data.get("users", {})
        first_responder = users.get(first_responder_id)
        
        if first_responder:
            return {
                'first_name': first_responder.get('first_name', 'Участник'),
                'username': first_responder.get('username', '')
            }
        
        return None

    # МЕТОДЫ ДЛЯ УПРАВЛЕНИЯ ЧАТАМИ
    def add_chat_id(self, chat_id):
        """Добавляет ID чата в список для автоматических викторин"""
        users_data = self.load_users()
        
        if "active_chats" not in users_data:
            users_data["active_chats"] = []
        
        if chat_id not in users_data["active_chats"]:
            users_data["active_chats"].append(chat_id)
            self.save_users(users_data)
            print(f"✅ Добавлен чат ID: {chat_id}")
        
        return users_data["active_chats"]

    def get_active_chats(self):
        """Получает список активных чатов"""
        users_data = self.load_users()
        return users_data.get("active_chats", [])

    def remove_chat_id(self, chat_id):
        """Удаляет ID чата из списка"""
        users_data = self.load_users()
        
        if "active_chats" in users_data:
            if chat_id in users_data["active_chats"]:
                users_data["active_chats"].remove(chat_id)
                self.save_users(users_data)
                print(f"🗑️ Удален чат ID: {chat_id}")
        
        return users_data.get("active_chats", [])