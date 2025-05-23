from django.shortcuts import render, redirect
from .models import Produto, Venda
from .forms import ProdutoForm, VendaForm
from django.http import JsonResponse
from django.contrib import messages
from datetime import datetime
from django.db.models import Sum, F
import json 

# Página inicial
def home(request):
    return render(request, 'html/home.html')

# Cadastro de produto
def cadastrar_produto(request):
    if request.method == "POST":
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Produto cadastrado com sucesso!")
            return redirect('home')
        else:
            messages.error(request, "Erro ao realizar a venda: " + str(form.errors))
    else:
        form = ProdutoForm()
    return render(request, 'html/produtos/cadastrar_produto.html', {'form': form})

def realizar_venda(request):
    if request.method == "POST":
        carrinho = request.POST.get('carrinho')  # Obtendo o carrinho enviado via AJAX
        if not carrinho:
            messages.error(request, "O carrinho está vazio.")
            return redirect('realizar_venda')
        
        try:
            # Convertendo o carrinho JSON em uma lista de produtos e quantidades
            carrinho = json.loads(carrinho)
        except ValueError:
            messages.error(request, "Erro ao processar o carrinho.")
            return redirect('realizar_venda')

        # Processar cada item do carrinho
        for item in carrinho:
            produto_id = item.get('produtoId')
            quantidade = item.get('quantidade')

            try:
                produto = Produto.objects.get(id=produto_id)
            except Produto.DoesNotExist:
                messages.error(request, f"Produto com ID {produto_id} não encontrado.")
                return redirect('realizar_venda')

            if produto.estoque < quantidade:
                messages.error(request, f"Estoque insuficiente para o produto {produto.nome}.")
                return redirect('realizar_venda')

            # Criação da venda para cada item no carrinho
            venda = Venda(produto=produto, quantidade=quantidade)
            venda.save()

            # Atualizando o estoque do produto
            produto.estoque -= quantidade
            produto.save()

        messages.success(request, "Venda realizada com sucesso!")
        return redirect('home')  # Redirecionar para a página inicial

    else:
        form = VendaForm()

    return render(request, 'html/vendas/realizar_venda.html', {'form': form})

# Buscar produto por ID ou código de barras
def buscar_produto(request):
    produto_id = request.GET.get('produto_id')
    if produto_id:
        try:
            produto = Produto.objects.get(id=produto_id)
            return JsonResponse({'nome': produto.nome, 'preco': str(produto.preco)})
        except Produto.DoesNotExist:
            return JsonResponse({'error': 'Produto não encontrado'}, status=404)
    return JsonResponse({'error': 'ID ou código de barras não fornecido'}, status=400)

def relatorio_vendas(request):
    # Filtragem de vendas por período (se houver)
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')
    
    vendas = Venda.objects.all()

    # Se houver datas de início e fim, filtrar as vendas nesse período
    if inicio and fim:
        try:
            inicio = datetime.strptime(inicio, '%Y-%m-%d')
            fim = datetime.strptime(fim, '%Y-%m-%d')
            vendas = vendas.filter(data_venda__range=[inicio, fim])
        except ValueError:
            pass  # Se as datas não estiverem no formato correto, ignore o filtro
    
    # Calcular o total de vendas e a quantidade total de produtos vendidos
    total_vendas = vendas.aggregate(total_vendas=Sum('total'))
    total_quantidade = vendas.aggregate(total_quantidade=Sum('quantidade'))
    
    return render(request, 'html/vendas/relatorio_vendas.html', {
        'vendas': vendas,
        'total_vendas': total_vendas['total_vendas'],
        'total_quantidade': total_quantidade['total_quantidade'],
        'inicio': inicio,
        'fim': fim,
    })