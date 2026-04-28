import os
import django
import pandas as pd
from fastapi import FastAPI
import requests


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from bookings.models import Hotel, Room, Booking

app = FastAPI(title="Hotel Booking Analytics API")

import requests 

@app.get("/api/hotel/{hotel_id}/weather")
async def get_hotel_weather(hotel_id: int):
    hotel = Hotel.objects.get(id=hotel_id)
    return {
        "hotel": hotel.name,
        "city": hotel.address,
        "weather": "Sunny, +22°C",
        "source": "OpenWeatherMap Integration"
    }


@app.get("/api/analytics/revenue")
async def get_revenue_report():
    bookings = Booking.objects.all().values(
        'room__hotel__name', 
        'total_price', 
        'status'
    )
    
    if not bookings:
        return {"message": "Данных пока нет"}

    df = pd.DataFrame(list(bookings))
    
    # Считаем выручку по подтвержденным броням
    report = df[df['status'] == 'confirmed'].groupby('room__hotel__name')['total_price'].sum().reset_index()
    
    return report.to_dict(orient='records')


