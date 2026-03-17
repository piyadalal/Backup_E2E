main
frame - urls
# urls.py in your Django app
from django.urls import path
from ../adminPage import views

urlpatterns = [
    path('action/', views.action_redirect, name='action_redirect'),
    path('summaryPage/', views.summaryPage, name='summaryPage'),
    path('adminFrame/', views.adminframe, name='adminFrame'),
]