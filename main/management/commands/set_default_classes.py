from django.core.management.base import BaseCommand
from main.models import InventoryItem
import random

class Command(BaseCommand):
    help = 'Set default class values for existing inventory items'

    def handle(self, *args, **options):
        # Get all items without a class set
        items = InventoryItem.objects.filter(item_class='')
        
        classes = ['mechanical', 'electrical', 'board']
        count = 0
        
        for item in items:
            # For demonstration, assign random classes
            # In production, you might want a more specific logic
            item.item_class = random.choice(classes)
            item.save()
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {count} inventory items'))