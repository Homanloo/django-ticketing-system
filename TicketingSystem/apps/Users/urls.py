from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', views.LoginView.as_view(), name='v1-login'),
    path('auth/register/', views.RegisterView.as_view(), name='v1-register'),
    path('auth/logout/', views.LogoutView.as_view(), name='v1-logout'),
    path('auth/refresh/', views.CookieTokenRefreshView.as_view(), name='v1-token-refresh'),
    
    # User profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='v1-profile'),
    path('profile/change-password/', views.ChangePasswordView.as_view(), name='v1-change-password'),
]