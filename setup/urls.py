"""
URL configuration for setup project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# setup/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    UserViewSet,
    CategoryViewSet,
    TransactionViewSet,
    LoginView,
    CustomTokenRefreshView,
    AnalyticsViewSet 
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'categories', CategoryViewSet)
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'analytics', AnalyticsViewSet, basename='analytics') 

urlpatterns = [
    path('api/auth/login/', LoginView.as_view(), name='auth-login'),
    path('api/auth/refresh/', CustomTokenRefreshView.as_view(), name='auth-refresh'),
    path('api/auth/register/', UserViewSet.as_view({'post': 'register'}), name='auth-register'),
    path('api/users/me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
    
    path('api/', include(router.urls)),
    path('admin/', admin.site.urls),
]

