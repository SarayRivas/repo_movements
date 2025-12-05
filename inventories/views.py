from django.utils import timezone
from rest_framework import viewsets
from .models import Product, Warehouse, Shelve, Inventory, InventoryMovement, WarehouseCreation, OrderCreation, AuditLog 
from .serializers import AuditLogSerializer, InventorySerializer, ProductSerializer, WarehouseSerializer, ShelveSerializer, InventoryMovementSerializer, WarehouseCreationSerializer, OrderCreationSerializer
from django.db import transaction, DatabaseError
from django.db.utils import OperationalError
from django.db.models import F
from rest_framework.exceptions import ValidationError
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.cache import cache
from rest_framework import request
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response




class InventoryMovementViewSet(viewsets.ModelViewSet):
    queryset = InventoryMovement.objects.all().order_by('id_movement')
    serializer_class = InventoryMovementSerializer
    
    def _delta(self, movement_type: str, qty: int) -> int:
        return qty if movement_type == 'entrada' else -qty  # EntradaProducto => +qty, SalidaProducto => -qty

    @transaction.atomic
    def perform_create(self, serializer):
        movement = serializer.save()
        inv = Inventory.objects.select_for_update().get(pk=movement.inventory.id_inventory)

        delta = self._delta(movement.movement_type, movement.quantity)
        # Validación para no dejar inventario negativo
        if inv.quantity + delta < 0:
            raise ValidationError({"quantity": "Inventario insuficiente para registrar la salida."})

        Inventory.objects.filter(pk=inv.pk).update(quantity=F('quantity') + delta)

    @transaction.atomic
    def perform_update(self, serializer):
        # 1) revertir el efecto anterior del movimiento
        instance = self.get_object()
        inv = Inventory.objects.select_for_update().get(pk=instance.inventory.id_inventory)

        prev_delta = self._delta(instance.movement_type, instance.quantity)
        Inventory.objects.filter(pk=inv.pk).update(quantity=F('quantity') - prev_delta)

        # 2) guardar cambios y aplicar el nuevo efecto
        movement = serializer.save()  # ya puede tener nuevos tipo/cantidad/inventario
        # si cambió de inventario, bloquear el nuevo
        new_inv = Inventory.objects.select_for_update().get(pk=movement.inventory.id_inventory)
        new_inv.refresh_from_db()  # cantidad después de revertir

        new_delta = self._delta(movement.movement_type, movement.quantity)
        if new_inv.quantity + new_delta < 0:
            # deshacer la reversión para no dejar inconsistencia
            Inventory.objects.filter(pk=new_inv.pk).update(quantity=F('quantity') + prev_delta)
            raise ValidationError({"quantity": "Inventario insuficiente para registrar la salida."})

        Inventory.objects.filter(pk=new_inv.pk).update(quantity=F('quantity') + new_delta)

    @transaction.atomic
    def perform_destroy(self, instance):
        inv = Inventory.objects.select_for_update().get(pk=instance.inventory.id_inventory)
        delta = self._delta(instance.movement_type, instance.quantity)

        # al borrar, se revierte el efecto del movimiento
        if inv.quantity - delta < 0:
            raise ValidationError({"quantity": "Eliminar este movimiento dejaría el inventario en negativo."})

        Inventory.objects.filter(pk=inv.pk).update(quantity=F('quantity') - delta)
        instance.delete()


def _no_store(response):
    # Se colocan encabezados para que no se guarde la respuesta que siempre esta disponible en el cache del balanceador
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    return response


    
@require_http_methods(["GET", "HEAD"])
def health_check(request):

    res = JsonResponse({"status": "ok"})
    return _no_store(res)
