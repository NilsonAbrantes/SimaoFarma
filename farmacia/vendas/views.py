from django.shortcuts import render, redirect
from .models import Produto, Venda
from .forms import ProdutoForm, VendaForm
from django.http import JsonResponse
from django.contrib import messages
from datetime import datetime
from django.db.models import Sum, F

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

# Realizar venda
def realizar_venda(request):
    if request.method == "POST":
        form = VendaForm(request.POST)
        if form.is_valid():
            venda = form.save(commit=False)  # Não salva ainda, para associar o produto

            # Atribuindo o produto selecionado ou pesquisado
            produto = form.cleaned_data.get('produto')  # Produto do campo ModelChoice ou do campo pesquisa_produto
            if not produto:
                messages.error(request, "Produto não selecionado ou encontrado.")
                return redirect('realizar_venda')

            venda.produto = produto  # Associa o produto encontrado à venda

            # Salvar a venda
            venda.save()

            messages.success(request, f"Venda realizada com sucesso!")
            return redirect('home')
        else:
            messages.error(request, "Erro ao realizar a venda: " + str(form.errors))
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