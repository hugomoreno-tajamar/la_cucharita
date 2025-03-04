from django.db import models
from authentication.models import Restaurante

# Modelo para MENUS_DIARIOS
class MenuDiario(models.Model):
    id_restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateField()
    fecha_final = models.DateField()

    def __str__(self):
        return f"Menú {self.id_restaurante.nombre} - {self.fecha_inicio}"


class Plato(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

# Modelo para MENUS_PLATOS
class MenuPlato(models.Model):
    id_menu = models.ForeignKey(MenuDiario, on_delete=models.CASCADE)
    id_plato = models.ForeignKey('Plato', on_delete=models.CASCADE)

class PromocionMenu(models.Model):
    id_restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE)
    id_menu = models.ForeignKey(MenuDiario, on_delete=models.CASCADE)
    precio_promocional = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    def __str__(self):
        return f"Promoción de {self.id_plato.nombre} en {self.id_restaurante.nombre}"



