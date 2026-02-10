"""
Модель клиента.
"""
from django.db import models


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
