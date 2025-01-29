from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Sum, Value
from django.utils.translation import gettext_lazy as _
from .models import User, Category, Transaction
from django.db.models.functions import TruncMonth, Coalesce
from .serializers import (
    UserRegistrationSerializer,
    UserDetailSerializer,
    CategorySerializer,
    TransactionSerializer,
    CustomTokenObtainSerializer
)
from .filters import TransactionFilter
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from django_filters import rest_framework as django_filters


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CustomTokenObtainSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {'detail': 'Credenciais inválidas ou usuário inativo'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            if response.status_code == 200:
                response.data['message'] = 'Token atualizado com sucesso'
            return response
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer

    def get_permissions(self):
        if self.action == 'register':
            return [permissions.AllowAny()]
        elif self.action == 'me':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserDetailSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Category.objects.all()

    def get_queryset(self):
        return Category.objects.filter(
            Q(user=self.request.user) | Q(user__isnull=True)
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        category = self.get_object()
        if category.user is None:
            return Response(
                {"detail": "Categorias globais não podem ser modificadas."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        if category.user is None:
            return Response(
                {"detail": "Categorias globais não podem ser excluídas."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class TransactionViewSet(viewsets.ModelViewSet):
    filter_backends = [django_filters.DjangoFilterBackend]
    filterset_class = TransactionFilter
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Transaction.objects.all()
    search_fields = ['description']

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        user = request.user

        total_income = user.transactions.filter(type='IN').aggregate(Sum('amount'))['amount__sum'] or 0
        total_expenses = user.transactions.filter(type='OUT').aggregate(Sum('amount'))['amount__sum'] or 0
        balance = total_income - total_expenses

        return Response({
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": balance
        })

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        data = Transaction.objects.filter(
            user=request.user,
            type='OUT'
        ).annotate(
            category_name=Coalesce('category__name', Value('Sem Categoria'))
        ).values('category_name').annotate(total=Sum('amount')).order_by('-total')
        return Response(data)


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        user = request.user

        by_category = Transaction.objects.filter(
            user=user,
            type='OUT'
        ).values('category__name').annotate(total=Sum('amount'))

        by_date = Transaction.objects.filter(
            user=user
        ).annotate(
            month=TruncMonth('date')
        ).values('month', 'type').annotate(total=Sum('amount'))

        return Response({
            'by_category': by_category,
            'by_date': by_date
        })