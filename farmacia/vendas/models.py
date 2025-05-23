from django.db import models

class Produto(models.Model):
    nome = models.CharField(max_length=255)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    codigo_barras = models.CharField(max_length=255, unique=True)
    estoque = models.IntegerField()

    def __str__(self):
        return self.nome

class Venda(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    data_venda = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Calcular o total antes de salvar a venda
        self.total = self.produto.preco * self.quantidade
        
        # Atualizar o estoque do produto
        if self.produto.estoque >= self.quantidade:
            self.produto.estoque -= self.quantidade
            self.produto.save()  # Salvar a atualização do estoque
        else:
            raise ValueError("Estoque insuficiente para realizar a venda.")
        
        super(Venda, self).save(*args, **kwargs)

    def __str__(self):
        return f"Venda de {self.produto.nome} em {self.data_venda}"
