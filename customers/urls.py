from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_view, name='customer_view'),
    path('restaurant/<int:menu_id>/', views.restaurant_view, name='restaurant_view'),
    path("enviar_valoracion_restaurante/", views.enviar_valoracion_restaurante, name="enviar_valoracion_restaurante"),
    path("enviar_valoracion_plato/", views.enviar_valoracion_plato, name="enviar_valoracion_plato"),
    path("reservar/", views.reservar, name="reservar"),
    path("filtrar/", views.search_restaurants, name="search_restaurants")
]
