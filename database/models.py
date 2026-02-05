"""
Модели базы данных с использованием Django ORM для PostgreSQL.

Описывает сущности: клиенты, товары, заказы и позиции в заказе.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Customer(models.Model):
    """
    Модель клиента.

    Хранит персональные данные и контакты покупателя.
    Связана с заказами через Order (один клиент — много заказов).
    """
    # Персональные данные
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    email = models.EmailField(unique=True, verbose_name="Электронная почта")
    phone = models.CharField(max_length=20, verbose_name="Телефон", blank=True)
    address = models.TextField(verbose_name="Адрес", blank=True)
    # Служебные поля (заполняются автоматически)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        db_table = 'customers'
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        # Индексы для быстрого поиска по email и ФИО
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['last_name', 'first_name']),
        ]

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Product(models.Model):
    """
    Модель товара (номенклатура).

    Описывает товар: название, категория, цена, остаток на складе.
    Артикул (sku) уникален. Неактивные товары (is_active=False) можно скрывать из каталога.
    """
    # Допустимые значения категории (внутренний код — отображаемое название)
    CATEGORY_CHOICES = [
        ('electronics', 'Электроника'),
        ('clothing', 'Одежда'),
        ('books', 'Книги'),
        ('food', 'Продукты'),
        ('other', 'Другое'),
    ]

    name = models.CharField(max_length=200, verbose_name="Наименование")
    description = models.TextField(verbose_name="Описание", blank=True)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other',
        verbose_name="Категория"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена",
        validators=[MinValueValidator(0)]  # Цена не может быть отрицательной
    )
    quantity = models.IntegerField(
        verbose_name="Количество на складе",
        validators=[MinValueValidator(0)],
        default=0
    )
    sku = models.CharField(max_length=50, unique=True, verbose_name="Артикул")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        db_table = 'products'
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['sku']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Order(models.Model):
    """
    Модель заказа.

    Связывает клиента с набором позиций (OrderItem). Содержит общую сумму,
    статус и даты. PROTECT на клиенте — нельзя удалить клиента с заказами.
    """
    STATUS_CHOICES = [
        ('pending', 'В обработке'),
        ('processing', 'В процессе'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,  # Запрет удаления клиента при наличии заказов
        related_name='orders',
        verbose_name="Клиент"
    )
    order_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата заказа"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Общая сумма",
        default=0
    )
    notes = models.TextField(verbose_name="Примечания", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        db_table = 'orders'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['order_date']),
            models.Index(fields=['customer', 'order_date']),
        ]
        ordering = ['-order_date']  # Свежие заказы первыми

    def __str__(self):
        return f"Заказ #{self.id} - {self.customer}"


class OrderItem(models.Model):
    """
    Модель позиции в заказе (одна строка заказа).

    Связывает заказ и товар, хранит количество и цены. Один и тот же товар
    в одном заказе может быть только в одной позиции (unique_together).
    total_price пересчитывается в save().
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,  # При удалении заказа удаляются и позиции
        related_name='items',
        verbose_name="Заказ"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,  # Не удалять товар, на который есть заказы
        verbose_name="Товар"
    )
    quantity = models.IntegerField(
        verbose_name="Количество",
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена за единицу"
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Общая стоимость"
    )

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'
        unique_together = ['order', 'product']  # Один товар — одна строка в заказе

    def save(self, *args, **kwargs):
        # Автоматически рассчитываем общую стоимость позиции
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"