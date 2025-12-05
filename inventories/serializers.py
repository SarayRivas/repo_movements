from rest_framework import serializers
from . import models


class InventoryMovementSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id_movement', 'inventory', 'movement_type', 'quantity', 'movement_date', 'notes',)
        model = models.InventoryMovement

