from django.urls import path
from django.contrib.auth import views as auth_views
from .views import hotel_list, hotel_detail, create_booking, register, my_bookings, update_booking_status
from . import views

urlpatterns = [
    path('', hotel_list, name='home'),
    path('hotel/<int:hotel_id>/', hotel_detail, name='hotel_detail'),
    path('book/<int:room_id>/', create_booking, name='create_booking'),
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='bookings/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('my-bookings/', my_bookings, name='my_bookings'),
    path('booking/<int:pk>/status/<str:new_status>/', views.update_booking_status, name='update_booking_status'),
    path('booking/<int:pk>/delete/', views.delete_booking, name='delete_booking'),
    path('rules/', views.rules_view, name='rules'),
    path('my-bookings/clean/', views.delete_old_bookings, name='clean_history'),


]



