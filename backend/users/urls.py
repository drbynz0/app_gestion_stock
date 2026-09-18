from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView,
    Verify2FALoginView,
    SendVerificationCodeView,
    VerifyCodeView,
    Toggle2FAView,
    CompanyRegisterView,
    CompanySettingsView,
    SellerListView,
    SellerRegisterView,
    SellerUpdateView,
    SellerDeleteView,
    ProfileView,
    SellerDashboard,
)

urlpatterns = [
    # Authentification principale
    path('login-view/', LoginView.as_view(), name='login'),
    path('login-app/', LoginView.as_view(), name='login-app'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Sécurité avancée : 2FA et codes de vérification SMS / Email
    path('security/send-code/', SendVerificationCodeView.as_view(), name='security-send-code'),
    path('security/verify-code/', VerifyCodeView.as_view(), name='security-verify-code'),
    path('security/2fa/verify/', Verify2FALoginView.as_view(), name='security-verify-2fa'),
    path('security/2fa/toggle/', Toggle2FAView.as_view(), name='security-toggle-2fa'),

    # Entreprise (Inscription, consultation, modification et suppression)
    path('companies/register/', CompanyRegisterView.as_view(), name='company-register'),
    path('company/settings/', CompanySettingsView.as_view(), name='company-settings'),

    # Équipe & Membres (Admins délégués et Vendeurs)
    path('sellers/', SellerListView.as_view(), name='seller-list'),
    path('sellers/create/', SellerRegisterView.as_view(), name='register-seller'),
    path('sellers/update/<int:pk>/', SellerUpdateView.as_view(), name='seller-update'),
    path('sellers/delete/<int:pk>/', SellerDeleteView.as_view(), name='seller-delete'),
    path('sellers/details/', SellerDashboard.as_view(), name='seller-dashboard'),

    # Profil personnel de l'utilisateur connecté
    path('profile/', ProfileView.as_view(), name='profile'),
]
