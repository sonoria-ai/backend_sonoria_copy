from django.contrib import admin
from .models import PaymentPlan

@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "monthly_price", "yearly_price", "is_active")  # Updated fields
    list_filter = ("is_active",)
    search_fields = ("name",)

# If you want to register UserSubscription as well:
from .models import UserSubscription
admin.site.register(UserSubscription) 