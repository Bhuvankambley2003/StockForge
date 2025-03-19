from django.contrib import admin
from .models import InventoryItem, StockMovement, SensorBuild, DeployedSensor

admin.site.register(InventoryItem)
admin.site.register(StockMovement)
admin.site.register(SensorBuild)
admin.site.register(DeployedSensor)
