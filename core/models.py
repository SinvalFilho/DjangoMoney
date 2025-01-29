from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.db.models import Sum

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=2, choices=USER_TYPE_CHOICES)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_permission_set',
        blank=True
    )

    def __str__(self):
        return self.username

    def update_balance(self):
        total_in = self.transactions.filter(type='IN').aggregate(total=Sum('amount'))['total'] or 0
        total_out = self.transactions.filter(type='OUT').aggregate(total=Sum('amount'))['total'] or 0
        self.balance = total_in - total_out
        self.save()

class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPE = [
        ('IN', 'Entrada'),
        ('OUT', 'Saída'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Dinheiro'),
        ('credit_card', 'Cartão de Crédito'),
        ('debit_card', 'Cartão de Débito'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=3, choices=TRANSACTION_TYPE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    date = models.DateField()
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES)

    def __str__(self):
        return f"{self.type} - {self.amount}"

    def save(self, *args, **kwargs):
        if not self.user or not User.objects.filter(id=self.user.id).exists():
            raise ValueError("O usuário associado não existe.")
        if not self.category or not Category.objects.filter(id=self.category.id).exists():
            raise ValueError("A categoria associada não existe.")
        super().save(*args, **kwargs)
