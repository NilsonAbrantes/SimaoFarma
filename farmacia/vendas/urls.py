from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cadastrar_produto/', views.cadastrar_produto, name='cadastrar_produto'),
    path('realizar_venda/', views.realizar_venda, name='realizar_venda'),
    path('buscar_produto/', views.buscar_produto, name='buscar_produto'),
    path('relatorio_vendas/', views.relatorio_vendas, name='relatorio_vendas'),
]