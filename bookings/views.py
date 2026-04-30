from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Min
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .models import Hotel, Room, Booking
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db.models import Q, Min



# --- ПАМЯТЬ НЕЙРОСЕТИ (ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ) ---
def get_user_ai_profile(user):
    """Собирает данные из базы, чтобы нейросеть могла их 'вспомнить'"""
    bookings = Booking.objects.filter(user=user).select_related('room__hotel')
    
    if not bookings.exists():
        return "Это новый гость. Предложи ему лучшие отели."

    cities = [b.room.hotel.address for b in bookings]
    total_spent = sum([b.total_price for b in bookings])
    
    return f"Пользователь {user.username}. Ранее бронировал в городах: {', '.join(set(cities))}. Общие расходы: {total_spent} руб."




def hotel_list(request):
    q = request.GET.get('q', '').strip()
    city_filter = request.GET.get('city_filter', '')
    sort_by = request.GET.get('sort', 'price_desc')

    # Аннотируем минимальную цену
    hotels = Hotel.objects.annotate(min_price=Min('rooms__price_per_night'))

    if q:
        # В Postgres icontains работает с кириллицей идеально.
        # Найдет "Отель", "отель", "ОТЕЛЬ", даже если ты ввел "ОТ"
        hotels = hotels.filter(name__icontains=q)

    # Фильтрация по городу (тоже можно через icontains для надежности)
    if city_filter:
        hotels = hotels.filter(city__icontains=city_filter)
    
    # Сортировка
    hotels = hotels.order_by('min_price' if sort_by == 'price_asc' else '-min_price')

    all_cities = Hotel.objects.values_list('city', flat=True).distinct().order_by('city')

    return render(request, 'bookings/index.html', {
        'hotels': hotels,
        'all_cities': all_cities,
        'query_name': q,
        'current_city': city_filter,
        'sort_by': sort_by
    })


def hotel_detail(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    rooms = hotel.rooms.prefetch_related('amenities').all()
    return render(request, 'bookings/hotel_detail.html', {
        'hotel': hotel, 
        'rooms': rooms, 
        'today': date.today().isoformat() 
    })

@login_required
def my_bookings(request):
    """Личный кабинет с проверкой наличия 'мусора' для кнопки удаления"""
    bookings = Booking.objects.filter(user=request.user).select_related('room__hotel').order_by('-created_at')
    today = date.today()
    
    # Считаем, есть ли что-то на удаление (отмененные или старые)
    bookings_has_trash = bookings.filter(
        Q(status='cancelled') | Q(status='no_show') | Q(check_out__lt=today)
    ).exists()
    
    ai_context = get_user_ai_profile(request.user)
    
    return render(request, 'bookings/my_bookings.html', {
        'bookings': bookings,
        'ai_context': ai_context,
        'bookings_has_trash': bookings_has_trash, 
        'today': today # Чтобы работало сравнение b.check_out < today в таблице
    })


@login_required
def create_booking(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        check_in_str = request.POST.get('check_in')  
        check_out_str = request.POST.get('check_out')

        if not check_in_str or not check_out_str:
            return redirect('hotel_detail', hotel_id=room.hotel.id)

        try:
            # 1. Парсим даты
            d1 = timezone.make_aware(datetime.strptime(check_in_str, '%Y-%m-%dT%H:%M'))
            d2 = timezone.make_aware(datetime.strptime(check_out_str, '%Y-%m-%dT%H:%M'))

            # Контекст для возврата при ошибке (с сортировкой номеров!)
            context_on_error = {
                'hotel': room.hotel, 
                'rooms': room.hotel.rooms.all().order_by('price_per_night'), # СОРТИРОВКА
                'today': timezone.now().date().isoformat(),
            }

            # 2. ПРОВЕРКА: Прошлое
            if d1 < timezone.now():
                context_on_error['error'] = "Нельзя бронировать на прошедшее время!"
                return render(request, 'bookings/hotel_detail.html', context_on_error)

            # 3. ПРОВЕРКА: Минимум 1 сутки
            duration = d2 - d1
            if duration < timedelta(days=1):
                context_on_error['error'] = "Минимальный срок бронирования — 1 сутки (24 часа)!"
                return render(request, 'bookings/hotel_detail.html', context_on_error)

            # 4. ПРОВЕРКА: Пересечение броней пользователя
            overlap = Booking.objects.filter(
                user=request.user,
                status__in=['pending', 'confirmed', 'checked_in'],
                check_in__lt=d2,
                check_out__gt=d1
            ).exists()

            if overlap:
                context_on_error['error'] = "У вас уже есть другая бронь на эти даты!"
                return render(request, 'bookings/hotel_detail.html', context_on_error)

            # 5. РАСЧЕТ ЦЕНЫ (Логика: Цена номера из БД * Сутки)
            days_count = duration.days
            if duration.seconds > 0:
                 days_count += 1
                 
            total_price = room.price_per_night * days_count

            # 6. СОЗДАНИЕ БРОНИ
            Booking.objects.create(
                user=request.user,
                room=room,
                check_in=d1,
                check_out=d2,
                total_price=total_price,
                status='pending'
            )
            
            return render(request, 'bookings/success.html', {'total_price': total_price})

        except (ValueError, TypeError) as e:
            print(f"Ошибка парсинга дат: {e}")
            return redirect('hotel_detail', hotel_id=room.hotel.id)

    return redirect('hotel_detail', hotel_id=room.hotel.id)







@login_required
def update_booking_status(request, pk, new_status):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    
    # Печатаем в консоль, чтобы проверить, какая строка пришла
    print(f"DEBUG: Пытаемся сменить статус на {new_status}")

    # Добавляем варианты написания, чтобы точно сработало
    if new_status in ['confirmed', 'cancelled', 'cancelled']:
        booking.status = new_status
        booking.save()
        print(f"DEBUG: Статус успешно изменен на {booking.status}")
    else:
        print(f"DEBUG: Статус {new_status} не входит в список разрешенных!")
        
    return redirect('my_bookings')


@login_required
def delete_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    today = date.today()
    is_finished = booking.status == 'confirmed' and booking.check_out < today
    is_cancelled = booking.status == 'cancelled'

    if is_finished or is_cancelled:
        booking.delete()
    
    return redirect('my_bookings')

@login_required
def delete_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if booking.status in ['confirmed', 'cancelled']:
        booking.delete()
    return redirect('my_bookings')

def rules_view(request):
    return render(request, 'bookings/rules.html')

@login_required
def delete_old_bookings(request):
    """Удаляет отмененные и уже завершенные поездки одной кнопкой"""
    today = date.today()
    # Ненужные — это те, что отменены ИЛИ те, где дата выезда прошла
    old_bookings = Booking.objects.filter(user=request.user).filter(
        Q(status='cancelled') | Q(status='confirmed', check_out__lt=today)
    )
    old_bookings.delete()
    return redirect('my_bookings')

def register(request):
    """Регистрация с автоматическим входом и запоминанием сессии"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Django запоминает пользователя "навсегда" в сессии
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'bookings/register.html', {'form': form})














