import django_filters
from .models import Transaction

class TransactionFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='gte',
        label='Data inicial (YYYY-MM-DD)'
    )
    
    end_date = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='lte',
        label='Data final (YYYY-MM-DD)'
    )

    class Meta:
        model = Transaction
        fields = {
            'type': ['exact'],
            'category': ['exact'],
            'payment_method': ['exact'],
        }