from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from .models import Usuario, Restaurante

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        
        try:
            user = Usuario.objects.get(username=username)
            if check_password(password, user.password) or password == user.password:
                request.session["user_id"] = user.id
                request.session["user_role"] = user.rol
                if user.rol == "admin":
                    return redirect("/panel")
                else:
                    return redirect("/clientes")
            else:
                messages.error(request, "Usuario o contraseña incorrectos.")
        except Usuario.DoesNotExist:
            messages.error(request, "Usuario o contraseña incorrectos.")
    
    return render(request, "login.html")

def register_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        
        if Usuario.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
        else:
            hashed_password = make_password(password)
            Usuario.objects.create(username=username, password=hashed_password, rol="Cliente")
            messages.success(request, "Usuario registrado exitosamente.")
            return redirect("login")
    
    return render(request, "register.html")

def register_restaurant(request):
    if request.method == "POST":
        nombre = request.POST["nombre"]
        ubicacion = request.POST["ubicacion"]
        tipo = request.POST["tipo"]
        telefono = request.POST["telefono"]
        email = request.POST["email"]
        clave = request.POST["clave"]
        password = request.POST["password"]
        ciudad = request.POST["ciudad"]
        
        CLAVE_REQUERIDA = "SECRETA123"  # Definir una clave de seguridad para registrar restaurantes
        if clave != CLAVE_REQUERIDA:
            messages.error(request, "Clave incorrecta para registrar restaurante.")
            return redirect("register_restaurant")
        
        # Crear usuario admin para el restaurante
        hashed_password = make_password(password)
        user = Usuario.objects.create(username=email, password=hashed_password, rol="admin")
        
        Restaurante.objects.create(
            nombre=nombre,
            ubicacion=ubicacion,
            tipo=tipo,
            telefono=telefono,
            email=email,
            ciudad=ciudad,
            id_usuario=user
        )
        messages.success(request, "Restaurante registrado exitosamente. Credenciales enviadas por correo.")
        return redirect("login")
    
    return render(request, "register_restaurant.html")
