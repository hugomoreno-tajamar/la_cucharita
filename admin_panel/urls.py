from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_pdf_page, name='html_page'),
    path("upload/", views.upload_pdf, name="pdf_upload"),
    path("promocionar/", views.promocionar_menu, name="promocionar_menu"),
]