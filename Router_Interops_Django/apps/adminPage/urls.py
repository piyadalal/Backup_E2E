from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('ifconfig/', views.ifconfig, name='ifconfig'),
    path('ethRefresh/', views.eth_refresh, name='ethRefresh'),
    path('restoreHistory/', views.restore_history, name='restoreHistory'),
    path('mainFrame/', views.restore_history, name='mainFrame'),


]