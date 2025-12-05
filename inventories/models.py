from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    id_product = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    creation_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
      
class Warehouse(models.Model):
    id_warehouse = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    creation_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    
class Shelve(models.Model):
    id_shelve= models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    capacity = models.IntegerField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='shelves')
    creation_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

class Inventory(models.Model):
    id_inventory = models.AutoField(primary_key=True)
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE)
    id_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    id_shelve = models.ForeignKey(Shelve, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    creation_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

class InventoryMovement(models.Model):
    id_movement = models.AutoField(primary_key=True)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=10)  # 'entrada' o 'salida'
    quantity = models.IntegerField()
    movement_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)
    
class WarehouseCreation(models.Model):
    id_warehouse_creation = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    creation_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    inventories = models.ManyToManyField(Inventory, related_name='warehouse_creations', blank=True)

class OrderCreation(models.Model):
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('verificado', 'Verificado'),
        ('despachado', 'Despachado'),
    ]
    id_order_creation = models.AutoField(primary_key=True)
    order_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente')
    quantity = models.IntegerField()
    creation_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    product_name = models.ManyToManyField(Product, related_name='order_creations', blank=True)
    inventories = models.ManyToManyField(Inventory, related_name='order_creations', blank=True)

class AuditLog(models.Model):
    ACTION_TYPES = [
        ('cambio_estado', 'Cambio de Estado'),
        ('cambio_inventario', 'Cambio de Inventario'),
        ('despacho', 'Despacho'),
    ]

    order = models.ForeignKey(OrderCreation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    detail = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.created_at} - {self.user} - {self.action_type}"
