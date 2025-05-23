from django import forms
from .models import Produto, Venda

# Formulário para cadastro de produto
class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'descricao', 'preco', 'codigo_barras', 'estoque']

# Formulário para venda
class VendaForm(forms.ModelForm):
    pesquisa_produto = forms.CharField(required=False, label="Buscar Produto por ID ou Código de Barras")
    produto = forms.ModelChoiceField(queryset=Produto.objects.all(), required=False, label="Produto")
    quantidade = forms.IntegerField(min_value=1, label="Quantidade", initial=1)

    class Meta:
        model = Venda
        fields = ['produto', 'quantidade', 'pesquisa_produto']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicializa o queryset de produtos se nenhum produto for selecionado
        self.fields['produto'].queryset = Produto.objects.all()

    def clean(self):
        cleaned_data = super().clean()

        # Obtém os valores dos campos
        produto = cleaned_data.get('produto')
        pesquisa_produto = cleaned_data.get('pesquisa_produto')

        # Se a pesquisa for preenchida, tentamos encontrar o produto
        if pesquisa_produto:
            try:
                # Tenta buscar o produto pelo código de barras
                produto = Produto.objects.get(codigo_barras=pesquisa_produto)
            except Produto.DoesNotExist:
                try:
                    # Se não encontrar pelo código de barras, tenta pelo ID
                    produto = Produto.objects.get(id=pesquisa_produto)
                except Produto.DoesNotExist:
                    # Se não encontrar, gera um erro de validação
                    raise forms.ValidationError("Produto não encontrado com o ID ou Código de Barras fornecido.")
            
            # Atribui o produto encontrado à venda
            cleaned_data['produto'] = produto

        # Se o campo produto foi deixado em branco, precisamos garantir que a pesquisa tenha sido preenchida
        if not produto and not pesquisa_produto:
            raise forms.ValidationError("Você deve fornecer um produto, seja por pesquisa ou seleção.")

        return cleaned_data