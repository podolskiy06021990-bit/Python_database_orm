"""
Главный файл приложения
"""
import sys
import os
from pathlib import Path

# Добавляем текущую директорию в путь Python
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def main():
    """Точка входа в приложение"""
    try:
        # Проверяем наличие необходимых модулей
        try:
            import tkinter as tk
            from tkinter import ttk
        except ImportError:
            print("❌ Tkinter не установлен. Установите его:")
            print("Windows: Установлен по умолчанию с Python")
            print("Linux: sudo apt-get install python3-tk")
            print("macOS: brew install python-tk")
            input("Нажмите Enter для выхода...")
            return

        # Проверяем настройки Django
        try:
            import django
            from database.PostgreSQLHandler import PostgreSQLHandler
        except ImportError as e:
            print(f"❌ Ошибка импорта: {e}")
            print("Установите необходимые зависимости:")
            print("pip install django psycopg2-binary python-dotenv")
            input("Нажмите Enter для выхода...")
            return
        except Exception as e:
            print(f"❌ Ошибка настройки Django: {e}")
            input("Нажмите Enter для выхода...")
            return

        # Проверяем подключение к базе и инициализируем таблицы
        print("🔍 Проверка подключения к базе данных...")
        handler = PostgreSQLHandler()
        if not handler.check_connection():
            print("\n⚠️  Не удалось подключиться к базе данных.")
            print("Хотите продолжить без подключения? (y/n)")
            choice = input().lower()
            if choice != 'y':
                print("Выход из программы...")
                return

        from database.PostgreSQLHandler import setup_database
        from database.PostgreSQLHandler import create_test_data
        if setup_database():
            create_test_data()

        # Импортируем окно приложения
        from ui.main_window import MainWindow

        # Создаем корневое окно
        root = tk.Tk()

        # Создаем и запускаем приложение
        app = MainWindow(root)

        # Запускаем главный цикл
        root.mainloop()

    except Exception as e:
        print(f"❌ Ошибка запуска приложения: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()