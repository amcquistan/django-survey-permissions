# survey/urls.py

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
  path('register/', views.RegisterView.as_view(), name='register'),
  path('login/', auth_views.LoginView.as_view(template_name='survey/login.html'), name='login'),
  path('profile/', views.ProfileView.as_view(), name='profile'),
  path('logout/', auth_views.LogoutView.as_view(), name='logout'),
  path('surveys/create/', views.SurveyCreateView.as_view(), name='survey_create'),
  path('survey/<int:survey_id>/', views.SurveyDetailView.as_view(), name='survey_details'),
]
