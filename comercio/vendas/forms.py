from django import forms
from .models import Produto, Venda


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'descricao', 'preco', 'codigo_barras', 'estoque']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descricao'].required = False
        self.fields['codigo_barras'].required = False

    def clean_codigo_barras(self):
        codigo = self.cleaned_data.get('codigo_barras')
        if not codigo:
            return None
        return codigo.strip()


class VendaForm(forms.ModelForm):
    pesquisa_produto = forms.CharField(required=False, label="Buscar Produto por ID, Código de Barras ou Nome")
    produto = forms.ModelChoiceField(queryset=Produto.objects.all(), required=False, label="Produto")
    quantidade = forms.IntegerField(min_value=1, label="Quantidade", initial=1)

    class Meta:
        model = Venda
        fields = ['produto', 'quantidade', 'pesquisa_produto']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produto'].queryset = Produto.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        produto = cleaned_data.get('produto')
        pesquisa_produto = cleaned_data.get('pesquisa_produto')

        if pesquisa_produto:
            pesquisa_produto = pesquisa_produto.strip()

            produto = Produto.objects.filter(codigo_barras=pesquisa_produto).first()

            if not produto and pesquisa_produto.isdigit():
                produto = Produto.objects.filter(id=int(pesquisa_produto)).first()

            if not produto:
                produto = Produto.objects.filter(nome__iexact=pesquisa_produto).first()

            if not produto:
                produto = Produto.objects.filter(nome__icontains=pesquisa_produto).order_by('nome').first()

            if not produto:
                raise forms.ValidationError("Produto não encontrado com o ID, código de barras ou nome informado.")

            cleaned_data['produto'] = produto

        if not produto and not pesquisa_produto:
            raise forms.ValidationError("Você deve fornecer um produto, seja por pesquisa ou seleção.")

        return cleaned_data


class AtualizarEstoqueForm(forms.Form):
    codigo_produto = forms.CharField(max_length=100, label="ID, Código de Barras ou Nome")
    novo_estoque = forms.IntegerField(min_value=1, label="Novo Estoque", required=False)
    novo_preco = forms.IntegerField(min_value=1, label="Novo Preço", required=False)

    def buscar_produto(self):
        termo = self.cleaned_data.get('codigo_produto', '').strip()

        produto = Produto.objects.filter(codigo_barras=termo).first()
        if produto:
            return produto

        if termo.isdigit():
            produto = Produto.objects.filter(id=int(termo)).first()
            if produto:
                return produto

        produto = Produto.objects.filter(nome__iexact=termo).first()
        if produto:
            return produto

        produto = Produto.objects.filter(nome__icontains=termo).order_by('nome').first()
        if produto:
            return produto

        raise forms.ValidationError("Produto não encontrado.")

    def atualizar_estoque(self):
        produto = self.buscar_produto()
        novo_estoque = self.cleaned_data.get('novo_estoque')
        novo_preco = self.cleaned_data.get('novo_preco')

        if novo_estoque is not None:
            produto.estoque = novo_estoque

        if novo_preco is not None:
            produto.preco = novo_preco

        produto.save()
        return produto