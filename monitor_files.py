import time
import json
import os
from datetime import datetime

def monitor_files():
    print("👀 МОНИТОРИНГ ФАЙЛОВ В РЕАЛЬНОМ ВРЕМЕНИ")
    print("Нажмите Ctrl+C для остановки\n")
    
    last_users = None
    last_questions = None
    
    try:
        while True:
            # Проверяем users.json
            if os.path.exists('data/users.json'):
                with open('data/users.json', 'r', encoding='utf-8') as f:
                    users_content = f.read()
                    users_data = json.loads(users_content) if users_content else {}
                
                if users_data != last_users:
                    print(f"🕐 {datetime.now().strftime('%H:%M:%S')} - users.json ОБНОВЛЕН!")
                    print(f"   Текущий вопрос: {users_data.get('current_question', {}).get('question', 'Нет')}")
                    print(f"   Ответившие: {users_data.get('answered_users', [])}")
                    print(f"   Активные чаты: {users_data.get('active_chats', [])}")
                    print(f"   Пользователей: {len(users_data.get('users', {}))}")
                    print("-" * 50)
                    last_users = users_data
            
            # Проверяем questions.json
            if os.path.exists('data/questions.json'):
                with open('data/questions.json', 'r', encoding='utf-8') as f:
                    questions_content = f.read()
                    questions_data = json.loads(questions_content) if questions_content else {}
                
                if questions_data != last_questions:
                    print(f"🕐 {datetime.now().strftime('%H:%M:%S')} - questions.json ОБНОВЛЕН!")
                    questions = questions_data.get('questions', [])
                    used_count = sum(1 for q in questions if q.get('used'))
                    print(f"   Всего вопросов: {len(questions)}")
                    print(f"   Использовано: {used_count}")
                    for q in questions:
                        status = "✅" if q.get('used') else "❌"
                        print(f"   {status} ID{q['id']}: {q['question'][:30]}... (used: {q.get('used')})")
                    print("-" * 50)
                    last_questions = questions_data
            
            time.sleep(2)  # Проверяем каждые 2 секунды
            
    except KeyboardInterrupt:
        print("\n👋 Мониторинг остановлен")

if __name__ == '__main__':
    monitor_files()