from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('inventory_list')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def user_management(request):
    if not request.user.is_superuser:
        return redirect('inventory_list')
    users = User.objects.all()
    return render(request, 'user_management.html', {'users': users})

@login_required
@require_POST
def refresh_session(request):
    """
    Simple view to refresh the user's session
    """
    # Just by accessing the view, the session expiry is reset
    # due to SESSION_SAVE_EVERY_REQUEST = True
    return JsonResponse({"status": "success", "message": "Session refreshed"})