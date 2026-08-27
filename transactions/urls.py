from django.urls import path
from . import views

app_name = 'transactions'
urlpatterns = [
    path('', views.checkout, name='checkout'),
    path('complete/', views.complete, name='complete'),
    path('simulate-payment/', views.simulate_payment, name='simulate_payment'),
    path('cart/', views.cart_partial, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
]
