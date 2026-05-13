from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('profile/<int:id>/', views.ProfileView.as_view(), name='profile'),
    path('logout/', views.logout_view, name='logout'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
