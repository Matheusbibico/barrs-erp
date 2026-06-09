from django.db import models, transaction
from django.utils.text import slugify
from core.models import TimeStampedModel


class Categoria(TimeStampedModel):
    nome = models.CharField('Nome', max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    descricao = models.TextField('Descrição', blank=True)
    ativa = models.BooleanField('Ativa', default=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)


class Fornecedor(TimeStampedModel):
    nome = models.CharField('Nome', max_length=200)
    contato = models.CharField('Contato', max_length=100, blank=True)
    whatsapp = models.CharField('WhatsApp', max_length=20, blank=True)
    email = models.EmailField('E-mail', blank=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True)
    estado = models.CharField('Estado (UF)', max_length=2, blank=True)
    ativo = models.BooleanField('Ativo', default=True)
    observacoes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Produto(TimeStampedModel):
    STATUS_ATIVO = 'ativo'
    STATUS_INATIVO = 'inativo'
    STATUS_RASCUNHO = 'rascunho'
    STATUS_CHOICES = [
        (STATUS_ATIVO, 'Ativo'),
        (STATUS_INATIVO, 'Inativo'),
        (STATUS_RASCUNHO, 'Rascunho'),
    ]

    sku = models.CharField('SKU', max_length=50, unique=True)
    nome = models.CharField('Nome', max_length=200)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos',
        verbose_name='Categoria',
    )
    descricao = models.TextField('Descrição', blank=True)
    custo = models.DecimalField('Custo (R$)', max_digits=10, decimal_places=2, default=0)
    preco_venda = models.DecimalField('Preço de Venda (R$)', max_digits=10, decimal_places=2)
    estoque_total = models.IntegerField('Estoque Total', default=0)
    estoque_reservado = models.IntegerField('Estoque Reservado', default=0)
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos',
        verbose_name='Fornecedor',
    )
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default=STATUS_ATIVO)
    site_id = models.IntegerField('ID no Site', null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['nome']

    def __str__(self):
        return f'{self.sku} — {self.nome}'

    @property
    def estoque_disponivel(self):
        return self.estoque_total - self.estoque_reservado

    @property
    def margem(self):
        if self.preco_venda and self.custo:
            return round((self.preco_venda - self.custo) / self.preco_venda * 100, 2)
        return 0


class VariacaoProduto(TimeStampedModel):
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='variacoes',
        verbose_name='Produto',
    )
    cor = models.CharField('Cor', max_length=50, blank=True)
    tamanho = models.CharField('Tamanho', max_length=20, blank=True)
    sku_variacao = models.CharField('SKU da Variação', max_length=80, unique=True)
    custo = models.DecimalField('Custo (R$)', max_digits=10, decimal_places=2, default=0)
    preco_venda = models.DecimalField('Preço de Venda (R$)', max_digits=10, decimal_places=2, default=0)
    estoque = models.IntegerField('Estoque', default=0)
    site_id = models.IntegerField('ID no Site', null=True, blank=True, db_index=True)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Variação de Produto'
        verbose_name_plural = 'Variações de Produto'
        ordering = ['cor', 'tamanho']
        unique_together = [('produto', 'cor', 'tamanho')]

    def __str__(self):
        partes = [p for p in [self.cor, self.tamanho] if p]
        return f'{self.produto.nome} — {" / ".join(partes)}' if partes else self.produto.nome


class FotoProduto(TimeStampedModel):
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='fotos',
        verbose_name='Produto',
    )
    imagem = models.ImageField('Imagem', upload_to='produtos/%Y/%m/')
    principal = models.BooleanField('Principal', default=False)
    ordem = models.PositiveIntegerField('Ordem', default=0)

    class Meta:
        verbose_name = 'Foto do Produto'
        verbose_name_plural = 'Fotos do Produto'
        ordering = ['ordem', 'criado_em']

    def __str__(self):
        return f'Foto de {self.produto.nome}'

    def save(self, *args, **kwargs):
        if self.principal:
            with transaction.atomic():
                FotoProduto.objects.filter(produto=self.produto, principal=True).update(principal=False)
        super().save(*args, **kwargs)
