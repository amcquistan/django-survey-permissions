# survey/urls.py

from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .tokens import user_tokenizer

urlpatterns = [
  path('register/', views.RegisterView.as_view(), name='register'),
  path('login/', auth_views.LoginView.as_view(template_name='survey/login.html'), name='login'),
  path('profile/', views.ProfileView.as_view(), name='profile'),
  path('logout/', auth_views.LogoutView.as_view(), name='logout'),
  path('surveys/create/', views.SurveyCreateView.as_view(), name='survey_create'),
  path('survey-assginment/<int:assignment_id>/', views.SurveyAssignmentView.as_view(), name='survey_assignment'),
  path('survey-management/<int:survey_id>/', views.SurveyManagerView.as_view(), name='survey_management'),
  path('survey-results/<int:survey_id>/', views.SurveyResultsView.as_view(), name='survey_results'),
  path('confirm-email/<str:user_id>/<str:token>/', views.ConfirmRegistrationView.as_view(), name='confirm_email'),
  path(
    'reset-password/',
    auth_views.PasswordResetView.as_view(
      template_name='survey/reset_password.html',
      html_email_template_name='survey/reset_password_email.html',
      success_url=settings.LOGIN_URL,
      token_generator=user_tokenizer),
    name='reset_password'
  ),
  path(
    'reset-password-confirmation/<str:uidb64>/<str:token>/',
    auth_views.PasswordResetConfirmView.as_view(
      template_name='survey/reset_password_update.html', 
      post_reset_login=True,
      post_reset_login_backend='django.contrib.auth.backends.ModelBackend',
      token_generator=user_tokenizer,
      success_url=settings.LOGIN_REDIRECT_URL),
    name='password_reset_confirm'
  ),
]
