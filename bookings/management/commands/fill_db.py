from django.core.management.base import BaseCommand
from bookings.models import Hotel, Room, Booking, Amenity
from django.contrib.auth.models import User
from faker import Faker
import random
from django.utils import timezone # Используем для работы с DateTimeField
from datetime import timedelta

class Command(BaseCommand):
    help = 'Наполняет базу отелями и тестовыми бронированиями'

    def handle(self, *args, **kwargs):
        fake = Faker('ru_RU')

        self.stdout.write("Очистка базы...")
        Booking.objects.all().delete()
        Room.objects.all().delete()
        Hotel.objects.all().delete()

        user, _ = User.objects.get_or_create(id=1, defaults={'username': 'admin'})

        # 2. Генерируем 10 отелей
        # 2. Генерируем 10 отелей
        # 2. Генерируем 10 отелей
                # 2. Генерируем 10 отелей
        for _ in range(10):
            city_name = fake.city()  # Фиксируем город
            
            hotel = Hotel.objects.create(
                # ТЕПЕРЬ ТУТ ТОЛЬКО ИМЯ: например, "Отель Весна" или "Гостиница ООО Кристалл"
                name=f"{random.choice(['Отель', 'Гостиница', 'Пансионат'])} {fake.company()}",
                
                # Поле города для фильтра (остается)
                city=city_name,
                
                # АДРЕС С ГОРОДОМ (остается здесь)
                address=f"г. {city_name}, {fake.street_address()}",
                
                # Описание с городом (остается для контекста)
                description=f"Прекрасный вариант для отдыха в городе {city_name}. {fake.sentence(nb_words=10)}",
                owner=user
            )
            # ... далее создание номеров и броней (без изменений)


            # 3. Создаем номера
            for _ in range(random.randint(3, 6)):
                price = random.randint(15, 100) * 100
                room = Room.objects.create(
                    hotel=hotel,
                    number=str(random.randint(100, 500)),
                    capacity=random.randint(1, 4),
                    price_per_night=price
                )

                # 4. Создаем бронь
                check_in_date = timezone.now() - timedelta(days=1)
                Booking.objects.create(
                    user=user,
                    room=room,
                    check_in=check_in_date,
                    check_out=check_in_date + timedelta(days=2),
                    total_price=price * 2,
                    status='confirmed'
                )


        self.stdout.write(self.style.SUCCESS(f'База готова! Создано 10 отелей с привязкой городов к описанию.'))
