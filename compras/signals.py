from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='compras.RecebimentoMercadoria')
def processar_recebimento_confirmado(sender, instance, **kwargs):
    """Ao confirmar recebimento: entra estoque, atualiza custo e cria ContaPagar."""
    if not instance.confirmado:
        return

    from django.db import transaction
    from django.utils import timezone as tz
    from estoque.models import MovimentoEstoque
    from financeiro.models import ContaPagar

    with transaction.atomic():
        itens = instance.itens.select_related(
            'item_pedido_compra__produto',
            'item_pedido_compra__variacao',
        ).all()

        for item in itens:
            if item.quantidade_recebida <= 0 or item.condicao != 'ok':
                continue

            ipc = item.item_pedido_compra
            produto = ipc.produto
            variacao = ipc.variacao

            MovimentoEstoque.objects.create(
                produto=produto,
                variacao=variacao,
                tipo=MovimentoEstoque.TIPO_ENTRADA,
                quantidade=item.quantidade_recebida,
                motivo=f'Recebimento de compra — {instance.pedido_compra}',
                usuario=instance.usuario,
            )

            # Atualiza custo do produto/variação com custo médio ponderado
            if variacao:
                estoque_atual = variacao.estoque - item.quantidade_recebida
                if estoque_atual >= 0:
                    custo_medio = (
                        (variacao.custo * estoque_atual + ipc.custo_unitario * item.quantidade_recebida)
                        / variacao.estoque
                    ) if variacao.estoque > 0 else ipc.custo_unitario
                    from produtos.models import VariacaoProduto
                    VariacaoProduto.objects.filter(pk=variacao.pk).update(custo=custo_medio)
            else:
                estoque_atual = produto.estoque_total - item.quantidade_recebida
                if estoque_atual >= 0 and produto.estoque_total > 0:
                    custo_medio = (
                        (produto.custo * estoque_atual + ipc.custo_unitario * item.quantidade_recebida)
                        / produto.estoque_total
                    )
                    from produtos.models import Produto
                    Produto.objects.filter(pk=produto.pk).update(custo=custo_medio)

        # Cria ContaPagar se não existir para este pedido de compra
        pc = instance.pedido_compra
        conta_ja_existe = ContaPagar.objects.filter(
            descricao__contains=str(pc.id)[:8].upper()
        ).exists()

        if not conta_ja_existe and pc.total > 0:
            ContaPagar.objects.create(
                categoria='Compras',
                descricao=f'Pedido de Compra PC-{str(pc.id)[:8].upper()} — {pc.fornecedor.nome}',
                fornecedor=pc.fornecedor,
                valor=pc.total,
                vencimento=pc.previsao_entrega or tz.localdate(),
                status='pendente',
            )

        # Atualiza status do pedido de compra
        total_pedido = sum(i.quantidade for i in pc.itens.all())
        total_recebido = sum(
            ir.quantidade_recebida
            for rec in pc.recebimentos.filter(confirmado=True)
            for ir in rec.itens.filter(condicao='ok')
        )

        if total_recebido >= total_pedido:
            from compras.models import PedidoCompra
            PedidoCompra.objects.filter(pk=pc.pk).update(status=PedidoCompra.STATUS_RECEBIDO)
        else:
            from compras.models import PedidoCompra
            PedidoCompra.objects.filter(pk=pc.pk).update(status=PedidoCompra.STATUS_RECEBIDO_PARCIAL)
