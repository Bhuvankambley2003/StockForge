from django.db import models
from django.conf import settings  # Add this import

class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('components', 'Components'),
        ('built_equipment', 'Built Equipment'),
    ]

    part_number = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, null=True)
    total_stock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.part_number})"


class StockMovement(models.Model):
    MOVEMENT_TYPE_CHOICES = [
        ('INWARD', 'Inward'),
        ('OUTWARD', 'Outward'),
    ]

    PURPOSE_CHOICES = [
        ('Production', 'Production'),
        ('Testing', 'Testing'),
        ('Deployment', 'Deployment'),
        ('Sales', 'Sales'),
        ('Return', 'Return'),
    ]

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    vendor = models.CharField(max_length=100, blank=True, null=True)  # Only for procurement
    purpose = models.CharField(max_length=50, choices=PURPOSE_CHOICES, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.movement_type} - {self.item.name} ({self.quantity})"


class SensorBuild(models.Model):
    sensor = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='sensor_builds')
    build_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sensor.name} build on {self.build_date}"


class SensorComponent(models.Model):
    sensor_build = models.ForeignKey(SensorBuild, on_delete=models.CASCADE, related_name='components')
    component = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='used_in_builds')
    quantity_used = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.component.name} used in {self.sensor_build.sensor.name} ({self.quantity_used})"


class DeployedSensor(models.Model):
    STATUS_CHOICES = [
        ('DEPLOYED', 'Deployed'),
        ('RETURNED', 'Returned'),
        ('SOLD', 'Sold'),
    ]

    sensor = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    company = models.CharField(max_length=100)
    deployment_date = models.DateField()
    expected_return_date = models.DateField(blank=True, null=True)
    actual_return_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DEPLOYED')
    quantity = models.PositiveIntegerField(default=1)
    deployed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='sensor_deployments',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.sensor.name} deployed at {self.company}"
    


class UserItemThreshold(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                           related_name='custom_thresholds')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE,
                           related_name='user_thresholds')
    low_threshold = models.PositiveIntegerField(default=5)
    medium_threshold = models.PositiveIntegerField(default=20)
    
    class Meta:
        unique_together = ['user', 'item']
    
    def __str__(self):
        return f"{self.user.username}'s thresholds for {self.item.name}"