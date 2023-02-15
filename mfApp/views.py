from django.shortcuts import render, redirect

def index(request):
    return render(request, 'index.html')

def list(request):
    return render(request)

def create(request):
    return

def update(request, id):
    return

def delete(request, id):
    return
