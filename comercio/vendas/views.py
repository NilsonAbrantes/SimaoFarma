from django.shortcuts import render, redirect, get_object_or_404
from .models import Produto, Venda, Cliente, Caderneta, Movimentacao
from .forms import ProdutoForm, VendaForm
from django.http import JsonResponse
from django.contrib import messages
from datetime import datetime
from django.db.models import Sum
from django.db import transaction
from decimal import Decimal, InvalidOperation
from django.core.paginator import Paginator
import json


def home(request):
    return render(request, 'html/home.html')


def cadastrar_produto(request):
    if request.method == "POST":
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Produto cadastrado com sucesso!")
            return redirect('listar_produtos')
        else:
            messages.error(request, "Erro ao cadastrar produto: " + str(form.errors))
    else:
        form = ProdutoForm()

    return render(request, 'html/produtos/cadastrar_produto.html', {
        'form': form
    })


def listar_produtos(request):
    produtos = Produto.objects.all().order_by('id')

    filtro_codigo_barras = request.GET.get('codigo_barras', '').strip()
    filtro_nome = request.GET.get('nome', '').strip()

    if filtro_codigo_barras:
        produtos = produtos.filter(codigo_barras__icontains=filtro_codigo_barras)

    if filtro_nome:
        produtos = produtos.filter(nome__icontains=filtro_nome)

    return render(request, 'html/produtos/listar_produtos.html', {
        'produtos': produtos,
        'filtro_codigo_barras': filtro_codigo_barras,
        'filtro_nome': filtro_nome,
    })


def editar_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    if request.method == "POST":
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            form.save()
            messages.success(request, f"Produto {produto.nome} atualizado com sucesso!")
            return redirect('listar_produtos')
        else:
            messages.error(request, "Erro ao atualizar produto: " + str(form.errors))
    else:
        form = ProdutoForm(instance=produto)

    return render(request, 'html/produtos/editar_produto.html', {
        'form': form,
        'produto': produto,
    })


def excluir_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    if request.method == "POST":
        nome = produto.nome
        produto.delete()
        messages.success(request, f"Produto '{nome}' excluído com sucesso!")
        return redirect('listar_produtos')

    return redirect('listar_produtos')


def realizar_venda(request):
    if request.method == "POST":
        carrinho_raw = request.POST.get('carrinho')
        cliente_id = request.POST.get('cliente_id')

        if not carrinho_raw:
            return JsonResponse({
                'success': False,
                'message': 'O carrinho está vazio.'
            }, status=400)

        try:
            carrinho = json.loads(carrinho_raw)
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Erro ao processar o carrinho.'
            }, status=400)

        if not isinstance(carrinho, list) or len(carrinho) == 0:
            return JsonResponse({
                'success': False,
                'message': 'O carrinho está vazio.'
            }, status=400)

        cliente = None
        if cliente_id:
            try:
                cliente = Cliente.objects.get(id=cliente_id)
            except Cliente.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Cliente não encontrado.'
                }, status=400)

        try:
            with transaction.atomic():
                for item in carrinho:
                    produto_id = item.get('produtoId')
                    quantidade = int(item.get('quantidade', 0))

                    if not produto_id or quantidade <= 0:
                        raise ValueError("Item inválido no carrinho.")

                    try:
                        produto = Produto.objects.select_for_update().get(id=produto_id)
                    except Produto.DoesNotExist:
                        raise ValueError(f"Produto com ID {produto_id} não encontrado.")

                    if produto.estoque < quantidade:
                        raise ValueError(f"Estoque insuficiente para o produto {produto.nome}.")

                    venda = Venda(
                        produto=produto,
                        quantidade=quantidade,
                        cliente=cliente
                    )
                    venda.save()

                    if cliente:
                        caderneta, _ = Caderneta.objects.get_or_create(cliente=cliente)
                        saldo_atual = caderneta.saldo_devedor or Decimal('0.00')
                        caderneta.saldo_devedor = saldo_atual + venda.total
                        caderneta.save()

                        Movimentacao.objects.create(
                            caderneta=caderneta,
                            tipo='divida',
                            valor=venda.total,
                            descricao=f"{quantidade} x {produto.nome}"
                        )

        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

        return JsonResponse({
            'success': True,
            'message': 'Venda realizada com sucesso!'
        })

    form = VendaForm()
    produtos = Produto.objects.all().order_by('nome')
    clientes = Cliente.objects.all().order_by('nome')

    return render(request, 'html/vendas/realizar_venda.html', {
        'form': form,
        'produtos': produtos,
        'clientes': clientes,
    })


def buscar_produto(request):
    if request.method == "POST":
        pesquisa_produto = request.POST.get('pesquisa_produto')

        if not pesquisa_produto:
            return JsonResponse({'produto': None})

        pesquisa_produto = pesquisa_produto.strip()

        produto = Produto.objects.filter(codigo_barras=pesquisa_produto).first()

        if not produto and pesquisa_produto.isdigit():
            produto = Produto.objects.filter(id=int(pesquisa_produto)).first()

        if not produto:
            produto = Produto.objects.filter(nome__iexact=pesquisa_produto).first()

        if not produto:
            produto = Produto.objects.filter(nome__icontains=pesquisa_produto).order_by('nome').first()

        if not produto:
            return JsonResponse({'produto': None})

        return JsonResponse({
            'produto': {
                'id': produto.id,
                'nome': produto.nome,
                'estoque': produto.estoque,
                'preco': str(produto.preco)
            }
        })


def relatorio_vendas(request):
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')

    vendas = Venda.objects.all()

    if inicio and fim:
        try:
            inicio = datetime.strptime(inicio, '%Y-%m-%d')
            fim = datetime.strptime(fim, '%Y-%m-%d')
            vendas = vendas.filter(data_venda__range=[inicio, fim])
        except ValueError:
            pass

    total_vendas = vendas.aggregate(total_vendas=Sum('total'))
    total_quantidade = vendas.aggregate(total_quantidade=Sum('quantidade'))

    return render(request, 'html/vendas/relatorio_vendas.html', {
        'vendas': vendas,
        'total_vendas': total_vendas['total_vendas'],
        'total_quantidade': total_quantidade['total_quantidade'],
        'inicio': inicio,
        'fim': fim,
    })

def caderneta_home(request):
    clientes = Cliente.objects.all()
    return render(request, 'html/vendas/caderneta_home.html', {'clientes': clientes})

def criar_cliente(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')

        cliente = Cliente.objects.create(nome=nome)
        Caderneta.objects.create(cliente=cliente)

        messages.success(request, 'Cliente criado com sucesso!')
        return redirect('caderneta_home')

    return render(request, 'html/vendas/criar_cliente.html')


def detalhe_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    caderneta = cliente.caderneta

    movimentacoes_lista = caderneta.movimentacoes.all().order_by('-data')

    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        valor_raw = request.POST.get('valor', '').strip()
        descricao = request.POST.get('descricao')

        try:
            valor = Decimal(valor_raw)
        except (InvalidOperation, TypeError):
            messages.error(request, 'Informe um valor válido.')
            return redirect('detalhe_cliente', cliente_id=cliente.id)

        if valor <= 0:
            messages.error(request, 'O valor deve ser maior que zero.')
            return redirect('detalhe_cliente', cliente_id=cliente.id)

        saldo_atual = caderneta.saldo_devedor or Decimal('0.00')

        if tipo == 'divida':
            caderneta.saldo_devedor = saldo_atual + valor
        elif tipo == 'pagamento':
            caderneta.saldo_devedor = saldo_atual - valor
        else:
            messages.error(request, 'Tipo de movimentação inválido.')
            return redirect('detalhe_cliente', cliente_id=cliente.id)

        caderneta.save()

        Movimentacao.objects.create(
            caderneta=caderneta,
            tipo=tipo,
            valor=valor,
            descricao=descricao
        )

        return redirect('detalhe_cliente', cliente_id=cliente.id)

    paginator = Paginator(movimentacoes_lista, 10)
    page_number = request.GET.get('page')
    movimentacoes = paginator.get_page(page_number)

    return render(request, 'html/vendas/detalhe_cliente.html', {
        'cliente': cliente,
        'caderneta': caderneta,
        'movimentacoes': movimentacoes,
    })
