from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.validators import UniqueValidator 
from django.utils.translation import gettext_lazy as _
from .models import User, Category, Transaction
from django.db.models import Q

from datetime import date


class UserDetailSerializer(serializers.ModelSerializer):
    user_type_display = serializers.CharField(
        source='get_user_type_display', 
        read_only=True,
        label=_('Tipo de Usuário')
    )
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'user_type',
            'user_type_display',
            'balance',
            'date_joined',
            'last_login'
        ]
        read_only_fields = [
            'id',
            'balance',
            'date_joined',
            'last_login'
        ]
        extra_kwargs = {
            'email': {
                'required': True,
                'allow_blank': False,
                'validators': [
                    UniqueValidator(
                        queryset=User.objects.all(),
                        message=_('Este email já está em uso.')
                    )
                ]
            },
            'username': {
                'validators': [
                    UniqueValidator(
                        queryset=User.objects.all(),
                        message=_('Este nome de usuário já está em uso.')
                    )
                ]
            }
        }

    def validate_email(self, value):
        if User.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
            raise serializers.ValidationError(_("Email já cadastrado."))
        return value

    def update(self, instance, validated_data):
        validated_data.pop('balance', None)
        return super().update(instance, validated_data)

class CustomTokenObtainSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        credentials = {
            'username': attrs.get("username"),
            'password': attrs.get("password")
        }
        
        user = User.objects.filter(
            Q(username__iexact=credentials['username']) | 
            Q(email__iexact=credentials['username'])
        ).first()

        if user and user.check_password(credentials['password']):
            if not user.is_active:
                raise serializers.ValidationError(_("Conta inativa."))
            
            refresh = self.get_token(user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'balance': user.balance
                }
            }
            return data
            
        raise serializers.ValidationError(_("Credenciais inválidas."))
    

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "user_type"]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True}
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("Email já cadastrado."))
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'user']
        read_only_fields = ['user']

    def validate_name(self, value):
        user = self.context['request'].user
        if Category.objects.filter(user=user, name=value).exists():
            raise serializers.ValidationError(_("Categoria já existe."))
        return value

class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'type', 'amount', 'description', 'date',
            'category', 'category_name', 'payment_method', 'user'
        ]
        read_only_fields = ['user', 'date']
        extra_kwargs = {
            'category': {'write_only': True}
        }

    def validate(self, data):
        if data['type'] == 'OUT' and data['amount'] > self.context['request'].user.balance:
            raise serializers.ValidationError(_("Saldo insuficiente."))
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data.setdefault('date', date.today())
        return super().create(validated_data)

