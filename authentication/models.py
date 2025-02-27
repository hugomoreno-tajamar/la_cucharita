from django.db import models

# Modelo para USUARIOS
class Usuario(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    rol = models.CharField(max_length=50)  # Cliente o Propietario

    def __str__(self):
        return self.usernameç
    
# Modelo para RESTAURANTES
class Restaurante(models.Model):
    nombre = models.CharField(max_length=255)
    ubicacion = models.CharField(max_length=255)
    tipo = models.CharField(max_length=100)
    telefono = models.CharField(max_length=50)
    email = models.EmailField()
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre
