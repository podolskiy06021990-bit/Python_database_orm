from django.db import models
from  .Student import Student

class Teacher(Student):
    """
    Модель преподавателя, наследует от Student и добавляет дополнительные атрибуты.
    """
    qualification = models.CharField(max_length=100, verbose_name="Квалификация преподавателя")
    subject = models.CharField(max_length=100, verbose_name="Преподаваемый предмет")

    def __str__(self):
        return f"{self.first_name} ({self.teacher_id})"