
from rest_framework import viewsets
from .models import  InventoryMovement, Inventory
from .serializers import  InventoryMovementSerializer
from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse



class InventoryMovementViewSet(viewsets.ModelViewSet):
    queryset = InventoryMovement.objects.all().order_by('id_movement')
    serializer_class = InventoryMovementSerializer
    
    def _delta(self, movement_type: str, qty: int) -> int:
        if movement_type == 'por_confirmar':
            return 0
        return qty if movement_type == 'entrada' else -qty

    @transaction.atomic
    def perform_create(self, serializer):
        movement = serializer.save()
        inv = Inventory.objects.select_for_update().get(pk=movement.inventory.id_inventory)

        delta = self._delta(movement.movement_type, movement.quantity)

        if inv.quantity + delta < 0:
            raise ValidationError({"quantity": "Inventario insuficiente para registrar la salida."})

        Inventory.objects.filter(pk=inv.pk).update(quantity=F('quantity') + delta)

    @transaction.atomic
    def perform_update(self, serializer):
        instance = self.get_object()
        inv = Inventory.objects.select_for_update().get(pk=instance.inventory.id_inventory)

        prev_delta = self._delta(instance.movement_type, instance.quantity)
        Inventory.objects.filter(pk=inv.pk).update(quantity=F('quantity') - prev_delta)

        movement = serializer.save()
        new_inv = Inventory.objects.select_for_update().get(pk=movement.inventory.id_inventory)
        new_inv.refresh_from_db()

        new_delta = self._delta(movement.movement_type, movement.quantity)
        if new_inv.quantity + new_delta < 0:
            Inventory.objects.filter(pk=new_inv.pk).update(quantity=F('quantity') + prev_delta)
            raise ValidationError({"quantity": "Inventario insuficiente para registrar la salida."})

        Inventory.objects.filter(pk=new_inv.pk).update(quantity=F('quantity') + new_delta)

    @transaction.atomic
    def perform_destroy(self, instance):
        inv = Inventory.objects.select_for_update().get(pk=instance.inventory.id_inventory)
        delta = self._delta(instance.movement_type, instance.quantity)

        if inv.quantity - delta < 0:
            raise ValidationError({"quantity": "Eliminar este movimiento dejaría el inventario en negativo."})

        Inventory.objects.filter(pk=inv.pk).update(quantity=F('quantity') - delta)
        instance.delete()





    
@require_http_methods(["GET", "HEAD"])
def health_check(request):

    res = JsonResponse({"status": "ok"})
    return _no_store(res)
