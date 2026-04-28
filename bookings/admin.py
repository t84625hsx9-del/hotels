from django.contrib import admin
from .models import Hotel, Room, Amenity, Booking

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'address')
    # Менеджер видит только свои отели
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

admin.site.register(Room)
admin.site.register(Amenity)
admin.site.register(Booking)

