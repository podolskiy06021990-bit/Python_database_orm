"""
Модель клиента.
"""
from logging import raiseExceptions

from django.db import models


class Student(models.Model):
    """
    Модель клиента.

    Хранит персональные данные и контакты покупателя.
    Связана с заказами через Order (один клиент — много заказов).
    """
    # Персональные данные
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    student_grade = models.CharField(max_length=100, verbose_name="Оценка студента")

    # Служебные поля (заполняются автоматически)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        ordering = ['first_name']  # добавьте этот атрибут

    def __str__(self):
        return self.first_name

    def clean(self):
        # Проверка, что имя не пустое
        if not self.first_name:
            raise ValueError("Имя студента не должно быть пустым.")
        # Проверка, что оценка — число от 0 до 100
        try:
            grade_value = float(self.student_grade)
        except ValueError:
            raise ValueError("Оценка должна быть числом.")
        if not (0 <= grade_value <= 100):
            raise ValueError("Оценка должна быть в диапазоне от 0 до 100.")

    def save(self, *args, **kwargs):
        self.clean()  # вызываем clean перед сохранением
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} ({self.id})"


