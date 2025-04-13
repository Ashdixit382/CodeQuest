from django.urls import path
from . import views

urlpatterns = [
    path('sync-problems/', views.sync_problems, name='sync_problems'),
    path('register-handle/', views.register_user_handle, name='register_handle'),
    path('filter-problems/', views.filter_problems, name='filter_problems'),
    path('', views.filter_problems_page, name='filter_page'),
]
