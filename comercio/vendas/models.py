from django.db import models

class Produto(models.Model):
    nome = models.CharField(max_length=255)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    codigo_barras = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True
    )
    estoque = models.IntegerField()

    def __str__(self):
        return self.nome


class Venda(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendas'
    )
    quantidade = models.IntegerField()
    data_venda = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total = self.produto.preco * self.quantidade

        if self.produto.estoque >= self.quantidade:
            self.produto.estoque -= self.quantidade
            self.produto.save()
        else:
            raise ValueError("Estoque insuficiente para realizar a venda.")

        super(Venda, self).save(*args, **kwargs)

    def __str__(self):
        return f"Venda de {self.produto.nome} em {self.data_venda}"


class Cliente(models.Model):
    nome = models.CharField(max_length=150)

    def __str__(self):
        return self.nome


class Caderneta(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE)
    saldo_devedor = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.cliente.nome} - R$ {self.saldo_devedor}"


class Movimentacao(models.Model):
    TIPO_CHOICES = (
        ('divida', 'Dívida'),
        ('pagamento', 'Pagamento'),
    )

    caderneta = models.ForeignKey(Caderneta, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.CharField(max_length=255, blank=True, null=True)
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.valor}"