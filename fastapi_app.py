import os
import django
import pandas as pd
from fastapi import FastAPI, Query
from datetime import datetime

# 1. Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from bookings.models import Hotel, Booking

app = FastAPI(title="Hotel Business Intelligence API")

@app.get("/api/analytics/performance")
async def get_hotel_performance(month: int = Query(None, ge=1, le=12)):
    """
    Эндпоинт показывает:
    - Реальную выручку (confirmed)
    - Потенциальные потери (canceled)
    - Самые популярные отели
    """
    
    # Забираем данные (включая дату создания брони)
    bookings_query = Booking.objects.all().values(
        'room__hotel__name', 
        'total_price', 
        'status',
        'created_at' # Предполагаем, что такое поле есть в модели
    )
    
    if not bookings_query:
        return {"message": "Данные в базе отсутствуют"}

    df = pd.DataFrame(list(bookings_query))
    
    # Преобразуем дату в формат pandas
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    # Фильтр по месяцу, если он передан в URL (?month=5)
    if month:
        df = df[df['created_at'].dt.month == month]
        if df.empty:
            return {"message": f"За месяц {month} данных нет"}

    # Считаем показатели
    performance = df.groupby('room__hotel__name').agg(
        confirmed_revenue=('total_price', lambda x: x[df['status'] == 'confirmed'].sum()),
        lost_revenue=('total_price', lambda x: x[df['status'] == 'canceled'].sum()),
        bookings_count=('total_price', 'count'),
        conversion_rate=('status', lambda x: (x == 'confirmed').mean() * 100)
    ).reset_index()

    # Округляем для красоты
    performance['conversion_rate'] = performance['conversion_rate'].round(1).astype(str) + '%'
    
    return {
        "period": f"Month: {month}" if month else "All time",
        "data": performance.to_dict(orient='records')
    }

@app.get("/api/analytics/top-rooms")
async def get_top_rooms():
    """Показывает топ самых прибыльных типов номеров"""
    bookings = Booking.objects.filter(status='confirmed').values(
        'room__room_type', # Предполагаемое поле
        'total_price'
    )
    
    if not bookings:
        return {"message": "Нет данных"}

    df = pd.DataFrame(list(bookings))
    top_rooms = df.groupby('room__room_type')['total_price'].sum().sort_values(ascending=False)
    
    return top_rooms.to_dict()




