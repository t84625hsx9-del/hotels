from django.core.management.base import BaseCommand
from bookings.models import Hotel, Room, Booking, Amenity
from django.contrib.auth.models import User
from faker import Faker
import random
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Наполняет базу отелями и тестовыми бронированиями'

    def handle(self, *args, **kwargs):
        fake = Faker('ru_RU')

        self.stdout.write("Очистка базы...")
        Booking.objects.all().delete()
        Room.objects.all().delete()
        Hotel.objects.all().delete()
        Amenity.objects.all().delete()

        # Создаем админа, если его нет
        user, _ = User.objects.get_or_create(id=1, defaults={'username': 'admin'})

        # 1. Создаем базовые удобства
        amenity_names = ['Wi-Fi', 'Бассейн', 'Завтрак', 'Парковка', 'Кондиционер']
        created_amenities = []
        for name in amenity_names:
            am = Amenity.objects.create(name=name)
            created_amenities.append(am)

        self.stdout.write("Создание отелей и номеров...")

        # 2. Генерируем 100 отелей
        # 2. Генерируем 100 отелей
        for _ in range(100):
            city_name = fake.city()
            hotel = Hotel.objects.create(
                name=f"{random.choice(['Отель', 'Гостиница', 'Пансионат'])} {fake.company()}",
                city=city_name,
                address=f"г. {city_name}, {fake.street_address()}",
                description=f"Прекрасный вариант для отдыха в городе {city_name}.",
                owner=user
            )

            # --- ИСПРАВЛЕНИЕ ТУТ: Фиксируем цену за 1 человека для ЭТОГО отеля ---
            # Теперь цена за 1 место в этом отеле будет одинаковой для всех его номеров
            hotel_base_price = random.randint(15, 30) * 100 

            # 3. Создаем номера (теперь цена будет расти строго по вместимости)
            for _ in range(random.randint(3, 6)):
                capacity = random.randint(1, 4)
                
                # Итоговая цена номера = фиксированная база отеля * вместимость
                price = hotel_base_price * capacity
                
                room = Room.objects.create(
                    hotel=hotel,
                    number=str(random.randint(100, 500)),
                    capacity=capacity,
                    price_per_night=price
                )

                room.amenities.add(*random.sample(created_amenities, random.randint(1, 3)))

                # 4. Создаем тестовую бронь
                days = 2
                check_in_date = timezone.now() - timedelta(days=random.randint(1, 5))
                Booking.objects.create(
                    user=user,
                    room=room,
                    check_in=check_in_date,
                    check_out=check_in_date + timedelta(days=days),
                    total_price=price * days,
                    status='confirmed'
                )


        self.stdout.write(self.style.SUCCESS(f'База готова! Создано 100 отелей. Цены зависят от вместимости.'))



