from django.db import models


class SiteCategoria(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        managed = False
        db_table = 'loja_categoria'
        app_label = 'core'


class SiteProduto(models.Model):
    nome = models.CharField(max_length=200)
    slug = models.SlugField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.IntegerField(default=0)
    categoria = models.ForeignKey(
        SiteCategoria, on_delete=models.SET_NULL, null=True, blank=True,
    )
    codigo_interno = models.CharField(max_length=50, blank=True)
    visivel = models.BooleanField(default=True)
    criado_em = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'loja_produto'
        app_label = 'core'


class SiteUser(models.Model):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()

    class Meta:
        managed = False
        db_table = 'auth_user'
        app_label = 'core'


class SitePerfilCliente(models.Model):
    user = models.OneToOneField(
        SiteUser, on_delete=models.CASCADE, related_name='perfil',
    )
    telefone = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)

    class Meta:
        managed = False
        db_table = 'loja_perfilcliente'
        app_label = 'core'


class SitePedido(models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    cep = models.CharField(max_length=10, blank=True, default='')
    # Na tabela do site (BarrsStore) a coluna chama-se "rua"
    logradouro = models.CharField(max_length=200, blank=True, default='', db_column='rua')
    numero = models.CharField(max_length=20, blank=True, default='')
    bairro = models.CharField(max_length=100, blank=True, default='')
    complemento = models.CharField(max_length=100, blank=True, default='')
    forma_pagamento = models.CharField(max_length=50, blank=True)
    codigo_rastreio = models.CharField(max_length=100, blank=True, default='')
    status = models.CharField(max_length=20)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    desconto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    frete = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    criado_em = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'loja_pedido'
        app_label = 'core'


class SiteItemPedido(models.Model):
    pedido = models.ForeignKey(
        SitePedido, on_delete=models.CASCADE, related_name='itens',
    )
    produto = models.ForeignKey(
        SiteProduto, on_delete=models.SET_NULL, null=True, blank=True,
    )
    nome_produto = models.CharField(max_length=200)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'loja_itempedido'
        app_label = 'core'
