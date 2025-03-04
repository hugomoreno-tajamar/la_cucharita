from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path("register/", views.register_user, name="register"),
    path("register_restaurant/", views.register_restaurant, name="register_restaurant"),

]