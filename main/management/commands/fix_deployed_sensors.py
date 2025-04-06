from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from main.models import DeployedSensor

class Command(BaseCommand):
    help = 'Fix deployed_by field for existing DeployedSensor records'

    def handle(self, *args, **options):
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('No admin user found! Create a superuser first.'))
            return
            
        null_records = DeployedSensor.objects.filter(deployed_by__isnull=True)
        count = null_records.count()
        
        if count > 0:
            null_records.update(deployed_by=admin_user)
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {count} records with admin user {admin_user.username}'))
        else:
            self.stdout.write(self.style.SUCCESS('No records needed updating.'))
