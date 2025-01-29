from django.contrib import admin
from .models import User, Category, Transaction

class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'user_type', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('user_type', 'is_active')

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user')
    search_fields = ('name',)
    list_filter = ('user',)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'amount', 'category', 'user', 'payment_method', 'date')
    search_fields = ('type', 'description')
    list_filter = ('type', 'category', 'payment_method', 'user')
    list_per_page = 20

admin.site.register(User, UserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Transaction, TransactionAdmin)
