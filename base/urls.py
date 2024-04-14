"""
URL configuration for InvTrackerPlus project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "base"
urlpatterns = [
    path("accounts/register/", views.register, name="register"),
    path("accounts/login/", views.CustomLoginView.as_view(), name="login"),
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("transfer/", views.transfer, name="transfer"),
    path("history/", views.history, name="history"),
    path("logout/", views.logout_page, name="logout"),
    path("settings/", views.settings, name="settings"),
    path(
        "password_change/",
        views.CustomPasswordChangeView.as_view(success_url="done/"),
        name="change-pw",
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="registration/password_change_done_.html"
        ),
        name="change-pw-done",
    ),
    path("transact/<int:pk>/", views.transact, name="transact"),
    path("delete/<int:pk>/", views.delete_transaction, name="delete"),
]
