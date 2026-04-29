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
            total_before = b.total_price 
            duration = b.check_out - b.check_in
            nights = duration.days if duration.days > 0 else 1
            one_night_fee = total_before / nights
            refund_amount = total_before - one_night_fee
            b.status = 'no_show'
            b.total_price = one_night_fee
            b.save()
            self.stdout.write(
                f"Клиент {b.user.username} пропустил заезд. "
                f"Удержано (1 ночь): {one_night_fee:.2f} руб. "
                f"К возврату клиенту: {refund_amount:.2f} руб."
                )


