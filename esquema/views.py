from django.shortcuts import render

# Create your views here.
def listarBonosVarilleros(request):
    return render(request,'esquema/bonos_varilleros/listar.html')

