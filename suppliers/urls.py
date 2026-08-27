from django.urls import path

from . import views

app_name = 'suppliers'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('complete/', views.registration_complete, name='registration_complete'),
    path('statement/<uuid:token>/', views.statement, name='statement'),
]
