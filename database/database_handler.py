"""
Обработчик базы данных PostgreSQL с Django ORM
"""
import os
import sys
import django
from pathlib import Path
from typing import List, Optional, Dict, Any
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, connection
from django.db.utils import OperationalError, IntegrityError, ProgrammingError

# Добавляем текущую директорию в путь Python
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config')

try:
    django.setup()
    from .models import Customer, Product, Order, OrderItem
    from django.db import models as django_models
    DJANGO_SETUP = True
except Exception as e:
    print(f"❌ Ошибка настройки Django: {e}")
    DJANGO_SETUP = False
    Customer = Product = Order = OrderItem = None
    django_models = None


class PostgreSQLHandler:
    """Класс для работы с PostgreSQL через Django ORM"""

    def __init__(self):
        if not DJANGO_SETUP:
            print("❌ Django не настроен. Проверьте настройки.")
            return
        self.check_connection()

    def check_connection(self) -> bool:
        """Проверка соединения с базой данных"""
        if not DJANGO_SETUP:
            return False

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                result = cursor.fetchone()
                print(f"✅ Подключено к PostgreSQL: {result[0]}")
                return True
        except OperationalError as e:
            print(f"❌ Ошибка подключения к PostgreSQL: {e}")
            print("\nПроверьте:")
            print("1. Запущен ли PostgreSQL сервер")
            print("2. Правильность данных в файле .env")
            print(f"3. Существует ли база данных '{os.getenv('DB_NAME', 'desktop_app_db')}'")
            print("4. Правильность логина и пароля")
            return False
        except Exception as e:
            print(f"❌ Неожиданная ошибка при подключении: {e}")
            return False

    @transaction.atomic
    def create_customer(self, **kwargs) -> Optional[Customer]:
        """Создание нового клиента"""
        if not DJANGO_SETUP:
            return None

        try:
            customer = Customer.objects.create(**kwargs)
            print(f"✅ Клиент создан: {customer}")
            return customer
        except IntegrityError as e:
            print(f"❌ Ошибка при создании клиента (дубликат email): {e}")
            return None
        except Exception as e:
            print(f"❌ Неожиданная ошибка при создании клиента: {e}")
            return None

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """Получение клиента по ID"""
        if not DJANGO_SETUP:
            return None

        try:
            return Customer.objects.get(id=customer_id)
        except ObjectDoesNotExist:
            print(f"❌ Клиент с ID {customer_id} не найден")
            return None
        except Exception as e:
            print(f"❌ Неожиданная ошибка при получении клиента: {e}")
            return None

    def get_customers_by_name(self, name: str) -> List[Customer]:
        """Поиск клиентов по имени"""
        if not DJANGO_SETUP:
            return []

        try:
            return list(Customer.objects.filter(
                django_models.Q(first_name__icontains=name) |
                django_models.Q(last_name__icontains=name)
            ))
        except Exception as e:
            print(f"❌ Ошибка при поиске клиентов: {e}")
            return []

    @transaction.atomic
    def create_product(self, **kwargs) -> Optional[Product]:
        """Создание нового товара"""
        if not DJANGO_SETUP:
            return None

        try:
            product = Product.objects.create(**kwargs)
            print(f"✅ Товар создан: {product}")
            return product
        except IntegrityError as e:
            print(f"❌ Ошибка при создании товара (дубликат артикула): {e}")
            return None
        except Exception as e:
            print(f"❌ Неожиданная ошибка при создании товара: {e}")
            return None

    def get_products_by_category(self, category: str) -> List[Product]:
        """Получение товаров по категории"""
        if not DJANGO_SETUP:
            return []

        try:
            return list(Product.objects.filter(category=category, is_active=True))
        except Exception as e:
            print(f"❌ Ошибка при получении товаров: {e}")
            return []

    def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """Получение товаров с низким запасом"""
        if not DJANGO_SETUP:
            return []

        try:
            return list(Product.objects.filter(quantity__lt=threshold, is_active=True))
        except Exception as e:
            print(f"❌ Ошибка при получении товаров: {e}")
            return []

    @transaction.atomic
    def create_order(self, customer_id: int, items: List[Dict[str, Any]],
                    notes: str = "") -> Optional[Order]:
        """Создание заказа с элементами"""
        if not DJANGO_SETUP:
            return None

        try:
            customer = Customer.objects.get(id=customer_id)
            order = Order.objects.create(customer=customer, notes=notes)

            total_amount = 0
            for item in items:
                product = Product.objects.get(id=item['product_id'])

                # Проверяем наличие товара
                if product.quantity < item['quantity']:
                    raise ValueError(f"Недостаточно товара: {product.name}. На складе: {product.quantity}, требуется: {item['quantity']}")

                # Создаем элемент заказа
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item['quantity'],
                    unit_price=product.price
                )

                # Обновляем количество товара на складе
                product.quantity -= item['quantity']
                product.save()

                total_amount += float(order_item.total_price)

            # Обновляем общую сумму заказа
            order.total_amount = total_amount
            order.save()

            print(f"✅ Заказ создан: #{order.id}")
            return order

        except (ObjectDoesNotExist, ValueError, IntegrityError) as e:
            print(f"❌ Ошибка при создании заказа: {e}")
            transaction.set_rollback(True)
            return None
        except Exception as e:
            print(f"❌ Неожиданная ошибка при создании заказа: {e}")
            transaction.set_rollback(True)
            return None

    def get_orders_by_customer(self, customer_id: int) -> List[Order]:
        """Получение заказов клиента"""
        if not DJANGO_SETUP:
            return []

        try:
            return list(Order.objects.filter(customer_id=customer_id).order_by('-order_date'))
        except Exception as e:
            print(f"❌ Ошибка при получении заказов: {e}")
            return []

    def get_orders_by_status(self, status: str) -> List[Order]:
        """Получение заказов по статусу"""
        if not DJANGO_SETUP:
            return []

        try:
            return list(Order.objects.filter(status=status).order_by('-order_date'))
        except Exception as e:
            print(f"❌ Ошибка при получении заказов: {e}")
            return []

    @transaction.atomic
    def update_order_status(self, order_id: int, new_status: str) -> bool:
        """Обновление статуса заказа"""
        if not DJANGO_SETUP:
            return False

        try:
            order = Order.objects.get(id=order_id)
            order.status = new_status
            order.save()
            print(f"✅ Статус заказа #{order_id} обновлен на '{new_status}'")
            return True
        except ObjectDoesNotExist:
            print(f"❌ Заказ с ID {order_id} не найден")
            return False
        except Exception as e:
            print(f"❌ Неожиданная ошибка при обновлении статуса: {e}")
            return False

    def execute_custom_query(self, query: str, params: tuple = None) -> List[dict]:
        """Выполнение произвольного SQL запроса"""
        if not DJANGO_SETUP:
            return []

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params or ())
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                return []
        except ProgrammingError as e:
            print(f"❌ Ошибка SQL запроса: {e}")
            return []
        except Exception as e:
            print(f"❌ Неожиданная ошибка выполнения запроса: {e}")
            return []

    def get_database_stats(self) -> Dict[str, int]:
        """Получение статистики базы данных"""
        if not DJANGO_SETUP:
            return {}

        try:
            stats = {
                'customers': Customer.objects.count(),
                'products': Product.objects.count(),
                'active_products': Product.objects.filter(is_active=True).count(),
                'orders': Order.objects.count(),
                'pending_orders': Order.objects.filter(status='pending').count(),
            }
            return stats
        except Exception as e:
            print(f"❌ Ошибка при получении статистики: {e}")
            return {}


def _ensure_tables():
    """
    Создаёт таблицы по текущим моделям, если их ещё нет.
    Порядок: Customer, Product, Order, OrderItem (из-за внешних ключей).
    Не зависит от файлов миграций.
    """
    from django.db import connection

    models_to_create = [Customer, Product, Order, OrderItem]

    with connection.cursor() as cursor:
        existing_tables = set(connection.introspection.table_names(cursor))

    with connection.schema_editor() as schema_editor:
        for model in models_to_create:
            table = model._meta.db_table
            if table in existing_tables:
                continue
            schema_editor.create_model(model)
            existing_tables.add(table)
            print(f"  Создана таблица: {table}")


def setup_database():
    """Настройка базы данных (создание таблиц). Всегда создаёт недостающие таблицы."""
    if not DJANGO_SETUP:
        print("❌ Django не настроен")
        return False

    print("🔄 Инициализация таблиц в базе данных...")

    # Пробуем миграции (могут не создать таблицы, если миграций нет или не применяются)
    try:
        from django.core.management import call_command
        call_command('makemigrations', 'database', verbosity=0)
        call_command('migrate', verbosity=0)
    except Exception:
        pass

    # Всегда проверяем и создаём недостающие таблицы по моделям
    try:
        _ensure_tables()
        print("✅ Таблицы в базе данных созданы/обновлены")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_test_data():
    """Создание тестовых данных"""
    if not DJANGO_SETUP:
        print("❌ Django не настроен")
        return False

    try:
        handler = PostgreSQLHandler()

        # Создаем тестовых клиентов
        test_customers = [
            {'first_name': 'Иван', 'last_name': 'Иванов', 'email': 'ivan@test.com', 'phone': '+79991234567'},
            {'first_name': 'Мария', 'last_name': 'Петрова', 'email': 'maria@test.com', 'phone': '+79997654321'},
            {'first_name': 'Алексей', 'last_name': 'Сидоров', 'email': 'alex@test.com', 'phone': '+79999876543'},
        ]

        for customer_data in test_customers:
            handler.create_customer(**customer_data)

        # Создаем тестовые товары
        test_products = [
            {'name': 'Ноутбук HP', 'sku': 'NB001', 'category': 'electronics', 'price': 50000.00, 'quantity': 10, 'description': 'Мощный ноутбук'},
            {'name': 'Смартфон Samsung', 'sku': 'PH001', 'category': 'electronics', 'price': 30000.00, 'quantity': 15, 'description': 'Современный смартфон'},
            {'name': 'Футболка', 'sku': 'TS001', 'category': 'clothing', 'price': 1500.00, 'quantity': 50, 'description': 'Хлопковая футболка'},
            {'name': 'Книга Python', 'sku': 'BK001', 'category': 'books', 'price': 1200.00, 'quantity': 20, 'description': 'Учебник по Python'},
            {'name': 'Кофе', 'sku': 'FD001', 'category': 'food', 'price': 500.00, 'quantity': 100, 'description': 'Арабика молотый'},
        ]

        for product_data in test_products:
            handler.create_product(**product_data)

        print("✅ Тестовые данные созданы")
        return True

    except Exception as e:
        print(f"❌ Ошибка создания тестовых данных: {e}")
        return False


if __name__ == "__main__":
    # Тестирование подключения
    print("🔍 Тестирование подключения к PostgreSQL...")

    if not DJANGO_SETUP:
        print("❌ Не удалось настроить Django")
        sys.exit(1)

    handler = PostgreSQLHandler()

    if handler.check_connection():
        print("✅ Подключение успешно!")

        # Настраиваем базу данных
        if setup_database():
            print("✅ База данных настроена")

            # Создаем тестовые данные
            create_test_data()
    else:
        print("❌ Не удалось подключиться к базе данных")
        print("Проверьте настройки в файле .env")