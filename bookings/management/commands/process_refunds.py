from django.core.management.base import BaseCommand
from bookings.models import Booking
from django.utils import timezone

class Command(BaseCommand):
    help = 'Находит незаехавших гостей и имитирует возврат средств'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        
        # Ищем брони: заезд был раньше текущего момента, а статус до сих пор "Подтверждено"
        late_bookings = Booking.objects.filter(
            check_in__lt=now,
            status='confirmed'
        )

        if not late_bookings.exists():
            self.stdout.write(self.style.WARNING("Прогульщиков не найдено."))
            return

        for b in late_bookings:
            # 1. Меняем статус на "Не заехал"
            b.status = 'no_show'
            b.save()
            
            # 2. Печатаем уведомление о возврате
            self.stdout.write(
                f"Клиент {b.user.username} пропустил заезд {b.check_in.strftime('%d.%m %H:%M')}. "
                f"Сумма {b.total_price} руб. возвращена."
            )

        self.stdout.write(self.style.SUCCESS(f"Обработано {late_bookings.count()} возвратов."))
