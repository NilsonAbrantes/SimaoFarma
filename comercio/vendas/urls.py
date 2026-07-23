from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cadastrar_produto/', views.cadastrar_produto, name='cadastrar_produto'),
    path('listar_produtos/', views.listar_produtos, name='listar_produtos'),
    path('editar_produto/<int:produto_id>/', views.editar_produto, name='editar_produto'),
    path('excluir_produto/<int:produto_id>/', views.excluir_produto, name='excluir_produto'),
    path('realizar_venda/', views.realizar_venda, name='realizar_venda'),
    path('buscar_produto/', views.buscar_produto, name='buscar_produto'),
    path('relatorio_vendas/', views.relatorio_vendas, name='relatorio_vendas'),
    path('caderneta/', views.caderneta_home, name='caderneta_home'),
    path('caderneta/novo/', views.criar_cliente, name='criar_cliente'),
    path('caderneta/<int:cliente_id>/', views.detalhe_cliente, name='detalhe_cliente'),
]