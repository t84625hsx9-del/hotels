from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

# 1. Удобства (Связь Many-to-Many с номерами)
class Amenity(models.Model):
    name = models.CharField(max_length=100, verbose_name="Удобство")
    icon = models.CharField(max_length=50, blank=True) # например, 'wifi'

    def __str__(self):
        return self.name

# 2. Отель
class Hotel(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название отеля")
    city = models.CharField(max_length=100, default="Не указан")
    address = models.TextField(verbose_name="Адрес")
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_hotels')

    def __str__(self):
        return self.name

# 3. Номер (Связь One-to-Many с Отелем и Many-to-Many с Удобствами)
class Room(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    number = models.CharField(max_length=10, verbose_name="Номер комнаты")
    capacity = models.IntegerField(default=2, verbose_name="Вместимость")
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    amenities = models.ManyToManyField(Amenity, blank=True, verbose_name="Удобства в номере")

    def __str__(self):
        return f"{self.hotel.name} - №{self.number}"

# 4. Бронирование
class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('confirmed', 'Подтверждено'),
        ('checked_in', 'Заселился'),
        ('cancelled', 'Отменено'),
        ('no_show', 'Не заехал'),

        
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateTimeField(verbose_name="Дата и время заезда")
    check_out = models.DateTimeField(verbose_name="Дата и время выезда")
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Проверка бизнес-логики перед сохранением"""
        if self.check_in and self.check_out:
            # 1. Запрет бронирования меньше чем на 24 часа
            if self.check_out - self.check_in < timezone.timedelta(days=1):
                raise ValidationError("Минимальный срок бронирования — 1 сутки.")
            
            # 2. Проверка, чтобы выезд не был раньше заезда
            if self.check_out <= self.check_in:
                raise ValidationError("Дата выезда должна быть позже даты заезда.")

    def save(self, *args, **kwargs):
        self.full_clean() # Вызывает clean() автоматически при сохранении
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Бронь {self.id} от {self.user.username} ({self.status})"

