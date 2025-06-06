from django.shortcuts import render, redirect
from .models import Produto, Venda
from .forms import ProdutoForm, VendaForm, AtualizarEstoqueForm
from django.http import JsonResponse
from django.contrib import messages
from datetime import datetime
from django.db.models import Sum, F
import json 
from django.views.decorators.csrf import csrf_exempt
from django import forms

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

        messages.success(request, "Venda realizada com sucesso!")
        return redirect('home')  # Redirecionar para a página inicial

    else:
        form = VendaForm()

    return render(request, 'html/vendas/realizar_venda.html', {'form': form})

# Buscar produto por ID ou código de barras
def buscar_produto(request):
    if request.method == "POST":
        pesquisa_produto = request.POST.get('pesquisa_produto')

        if not pesquisa_produto:
            return JsonResponse({'produto': None})

        # Limpar espaços extras
        pesquisa_produto = pesquisa_produto.strip()

        try:
            # Tente buscar pelo código de barras primeiro
            produto = Produto.objects.get(codigo_barras=pesquisa_produto)
        except Produto.DoesNotExist:
            try:
                # Se não encontrar pelo código de barras, tente pelo ID
                produto = Produto.objects.get(id=pesquisa_produto)
            except Produto.DoesNotExist:
                return JsonResponse({'produto': None})

        # Retorne o produto encontrado em formato JSON
        return JsonResponse({
            'produto': {
                'id': produto.id,
                'nome': produto.nome,
                'estoque': produto.estoque,
                'preco': produto.preco
            }
        })


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

# Atualizar estoque de produto
def atualizar_estoque(request):
    produto = None
    if request.method == "POST":
        pesquisa_produto = request.POST.get('pesquisa_produto')
        novo_estoque = request.POST.get('novo_estoque')

        if not pesquisa_produto:
            messages.error(request, "Digite o código de barras ou ID do produto.")
            return redirect('atualizar_estoque')

        # Limpar espaços extras
        pesquisa_produto = pesquisa_produto.strip()

        try:
            # Tente buscar pelo código de barras primeiro
            produto = Produto.objects.get(codigo_barras=pesquisa_produto)
        except Produto.DoesNotExist:
            try:
                # Se não encontrar pelo código de barras, tente pelo ID
                produto = Produto.objects.get(id=pesquisa_produto)
            except Produto.DoesNotExist:
                messages.error(request, f"Produto não encontrado para o código de barras ou ID: {pesquisa_produto}")
                return redirect('atualizar_estoque')

        # Verifica se o novo estoque é válido
        if novo_estoque and novo_estoque.isdigit() and int(novo_estoque) >= 1:
            produto.estoque = int(novo_estoque)
            produto.save()
            messages.success(request, f"Estoque do produto {produto.nome} atualizado com sucesso!")
            return JsonResponse({'status': 'success'})  # Resposta JSON indicando sucesso
        
        else:
            messages.error(request, "Informe um valor válido para o estoque.")
            return JsonResponse({'status': 'error', 'message': 'Valor inválido para o estoque.'})  # Resposta JSON de erro

    return render(request, 'html/produtos/atualizar_estoque.html', {'produto': produto})