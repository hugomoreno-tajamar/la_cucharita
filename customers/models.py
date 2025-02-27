from django.db import models
from authentication.models import Usuario, Restaurante
from admin_panel.models import Plato


# Modelo para RESERVAS
class Reserva(models.Model):
    id_cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reservas')
    id_restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE)
    fecha = models.DateField()

    def __str__(self):
        return f"Reserva de {self.id_cliente.username} en {self.id_restaurante.nombre}"


# Modelo para PLATOS_RESERVA
class PlatoReserva(models.Model):
    id_plato = models.ForeignKey(Plato, on_delete=models.CASCADE)
    id_reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id_plato.nombre} - Reserva {self.id_reserva.id}"
    

# Modelo para VALORACIONES_RESTAURANTES
class ValoracionRestaurante(models.Model):
    id_restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    puntuacion = models.IntegerField()
    comentario = models.TextField()
    fecha = models.DateField()

    def __str__(self):
        return f"{self.id_usuario.username} - {self.puntuacion} estrellas"


# Modelo para VALORACIONES_PLATOS
class ValoracionPlato(models.Model):
    id_plato = models.ForeignKey(Plato, on_delete=models.CASCADE)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    puntuacion = models.IntegerField()
    comentario = models.TextField()
    fecha = models.DateField()

    def __str__(self):
        return f"{self.id_usuario.username} - {self.puntuacion} estrellas"