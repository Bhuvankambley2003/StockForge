from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import InventoryItem, StockMovement, SensorBuild, SensorComponent, DeployedSensor
from .forms import InventoryItemForm
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
from django.conf import settings
import os
from datetime import datetime
from django.utils import timezone
from django.db import transaction

def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def add_inventory_item(request):
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            part_number = form.cleaned_data['part_number']
            total_stock = form.cleaned_data['total_stock']
            
            # Check for existing item with same part number
            existing_item = InventoryItem.objects.filter(part_number=part_number).first()
            
            if existing_item:
                # Update existing item's stock
                existing_item.total_stock += total_stock
                existing_item.save()
                
                # Create stock movement for additional stock
                StockMovement.objects.create(
                    item=existing_item,
                    movement_type='INWARD',
                    quantity=total_stock,
                    purpose='Procurement',
                    remarks='Additional stock added'
                )
            else:
                # Create new item
                item = form.save()
                StockMovement.objects.create(
                    item=item,
                    movement_type='INWARD', 
                    quantity=item.total_stock,
                    purpose='Procurement',
                    remarks='Initial stock added'
                )
            
            return redirect('inventory_list')
        else:
            print("Form errors:", form.errors)
    else:
        form = InventoryItemForm()
    return render(request, 'inventory_item_form.html', {'form': form})

@login_required
def inventory_list(request):
    items = InventoryItem.objects.all()
    raw_materials_count = InventoryItem.objects.filter(category='components').count()
    sensors_count = InventoryItem.objects.filter(category='built_equipment').count()
    return render(request, 'inventory_list.html', {
        'items': items,
        'raw_materials_count': raw_materials_count,
        'sensors_count': sensors_count
    })

@login_required
@user_passes_test(is_admin)
def stock_movement(request):
    items = InventoryItem.objects.all()
    if request.method == 'POST':
        item_id = request.POST['item']
        movement_type = request.POST['movement_type']
        quantity = int(request.POST['quantity'])
        vendor = request.POST.get('vendor', '')
        purpose = request.POST.get('purpose', '')

        item = InventoryItem.objects.get(id=item_id)
        if movement_type == 'OUTWARD':
            if item.total_stock < quantity:
                return render(request, 'stock_movement_form.html', {'error': 'Insufficient stock!', 'items': items})
            item.total_stock -= quantity
        elif movement_type == 'INWARD':
            item.total_stock += quantity

        item.save()
        StockMovement.objects.create(item=item, movement_type=movement_type, quantity=quantity, vendor=vendor, purpose=purpose)
        return redirect('stock_list')

    return render(request, 'stock_movement_form.html', {'items': items})

@login_required
def stock_list(request):
    stock_movements = StockMovement.objects.all().order_by('-date') 
    return render(request, 'stock_list.html', {'stock_movements': stock_movements})

@login_required
@user_passes_test(is_admin)
def sensor_build(request):
    raw_materials = InventoryItem.objects.filter(category='components')
    if request.method == 'POST':
        sensor_name = request.POST['sensor_name']
        part_number = request.POST['part_number']
        components = request.POST.getlist('components')
        quantities = request.POST.getlist('quantities')
        number_of_sensors = int(request.POST['number_of_sensors'])

        # Validate stock availability before proceeding
        for component_id, quantity in zip(components, quantities):
            component = InventoryItem.objects.get(id=component_id)
            quantity_used = int(quantity) 
            
            if component.total_stock < quantity_used:
                return render(request, 'sensor_build_form.html', 
                             {'error': f'Insufficient stock for {component.name}! Need {quantity_used}, have {component.total_stock}', 
                              'raw_materials': raw_materials})

        with transaction.atomic():
            # Create the new sensor with the correct stock amount from the beginning
            new_sensor = InventoryItem.objects.create(
                part_number=part_number,
                name=sensor_name,
                category='built_equipment',
                description='',
                total_stock=number_of_sensors  # Set the correct stock immediately
            )
            
            # Force refresh from database to ensure we have the latest data
            new_sensor.refresh_from_db()

            # Create the SensorBuild record
            sensor_build = SensorBuild.objects.create(sensor=new_sensor)

            # Create SensorComponent records and update stock movements
            for component_id, quantity in zip(components, quantities):
                component = InventoryItem.objects.get(id=component_id)
                quantity_used = int(quantity) 

                component.total_stock -= quantity_used
                component.save()
                component.refresh_from_db()

                SensorComponent.objects.create(
                    sensor_build=sensor_build,
                    component=component,
                    quantity_used=int(quantity)
                )

                # Create a StockMovement record for outward movement of raw materials
                StockMovement.objects.create(
                    item=component,
                    movement_type='OUTWARD',
                    quantity=quantity_used,
                    purpose='Production',
                    remarks=f'Used in building {number_of_sensors} {new_sensor.name}'
                )

            # Create a StockMovement record for inward movement of the new sensor
            StockMovement.objects.create(
                item=new_sensor,
                movement_type='INWARD',
                quantity=number_of_sensors,
                purpose='Production',
                remarks=f'{number_of_sensors} sensors built'
            )

        return redirect('inventory_list')

    return render(request, 'sensor_build_form.html', {'raw_materials': raw_materials})

@login_required
def sensor_detail(request, sensor_id):
    sensor = get_object_or_404(InventoryItem, id=sensor_id, category='built_equipment')
    sensor_builds = SensorBuild.objects.filter(sensor=sensor).prefetch_related('components__component')
    return render(request, 'sensor_details.html', {'sensor': sensor, 'sensor_builds': sensor_builds})

@login_required
def generate_pdf(request):
    items = InventoryItem.objects.all()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter,
                            rightMargin=36, leftMargin=36,
                            topMargin=72, bottomMargin=36)
    
    elements = []
    
    # Add logo and header
    # logo_path = os.path.join(settings.STATIC_ROOT, 'img/logo.png')
    # if os.path.exists(logo_path):
    #     logo = Image(logo_path, width=1.5*inch, height=0.5*inch)
    #     elements.append(logo)
    
    # Header text
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=12,
    )
    
    elements.append(Paragraph("Inventory Report", header_style))
    
    # Report metadata
    meta_style = ParagraphStyle(
        'Meta',
        parent=styles['BodyText'],
        textColor=colors.HexColor('#64748b'),
        fontSize=10,
        spaceAfter=24,
    )
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", meta_style))
    
    # Create table data
    data = [
        ['Part Number', 'Item Name', 'Category', 'Stock Level']
    ]
    
    for item in items:
        data.append([
            item.part_number,
            item.name,
            item.get_category_display(),
            str(item.total_stock)
        ])
    
    # Create table with professional styling
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 11),
        
        # Body
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 10),
        ('TEXTCOLOR', (0,1), (-1,-1), colors.HexColor('#1e293b')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (3,0), (3,-1), 'RIGHT'),
        
        # Grid lines
        ('LINEBELOW', (0,0), (-1,0), 1, colors.white),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        
        # Padding
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        
        # Alternating row colors
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#f8fafc')),
    ]))
    
    elements.append(table)
    
    # Add footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['BodyText'],
        textColor=colors.HexColor('#64748b'),
        fontSize=8,
        alignment=1,
    )
    
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated by Inventory Management System | Page 1 of 1", footer_style))
    
    doc.build(elements)
    return response

@login_required
@user_passes_test(is_admin)
def deployed_sensors(request):
    if request.method == 'POST':
        sensor_id = request.POST['sensor']
        company = request.POST['company']
        deployment_date = request.POST['deployment_date']
        expected_return_date = request.POST.get('expected_return_date')
        quantity = int(request.POST['quantity'])
        
        sensor = get_object_or_404(InventoryItem, id=sensor_id, category='built_equipment')
        
        if sensor.total_stock < quantity:
            return render(request, 'deployed_sensors.html', {
                'error': f'Insufficient stock for {sensor.name}! Need {quantity}, have {sensor.total_stock}',
                'sensors': InventoryItem.objects.filter(category='built_equipment'),
                'deployments': DeployedSensor.objects.all()
            })
        
        # Create single deployment record with quantity
        deployment = DeployedSensor.objects.create(
            sensor=sensor,
            company=company,
            deployment_date=deployment_date,
            expected_return_date=expected_return_date,
            status='DEPLOYED',
            quantity=quantity
        )
        
        # Update stock and create movement
        sensor.total_stock -= quantity
        sensor.save()
        
        StockMovement.objects.create(
            item=sensor,
            movement_type='OUTWARD',
            quantity=quantity,
            purpose='Deployment',
            remarks=f'{quantity} sensors deployed to {company}'
        )
        
        return redirect('deployed_sensors')
    
    return render(request, 'deployed_sensors.html', {
        'sensors': InventoryItem.objects.filter(category='built_equipment'),
        'deployments': DeployedSensor.objects.all()
    })

@login_required
@user_passes_test(is_admin)
def update_deployment_status(request, pk):
    deployment = get_object_or_404(DeployedSensor, pk=pk)
    previous_status = deployment.status
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        
        if new_status != previous_status:
            sensor = deployment.sensor
            
            if new_status == 'RETURNED':
                if previous_status in ['DEPLOYED', 'SOLD']:
                    sensor.total_stock += deployment.quantity
                    sensor.save()
                    deployment.actual_return_date = timezone.now()
                    
                    StockMovement.objects.create(
                        item=sensor,
                        movement_type='INWARD',
                        quantity=deployment.quantity,
                        purpose='Return',
                        remarks=f'Returned {deployment.quantity} from {deployment.company}'
                    )
                    
            elif new_status in ['DEPLOYED', 'SOLD']:
                if previous_status == 'RETURNED':
                    if sensor.total_stock >= deployment.quantity:
                        sensor.total_stock -= deployment.quantity
                        sensor.save()
                        
                        movement_type = 'Deployment' if new_status == 'DEPLOYED' else 'Sale'
                        StockMovement.objects.create(
                            item=sensor,
                            movement_type='OUTWARD',
                            quantity=deployment.quantity,
                            purpose=movement_type,
                            remarks=f'{movement_type} of {deployment.quantity} to {deployment.company}'
                        )
                    else:
                        return redirect('deployed_sensors')
                        
            deployment.status = new_status
            deployment.save()
    
    return redirect('deployed_sensors')



