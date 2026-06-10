import hashlib
import hmac
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

_MP_API = 'https://api.mercadopago.com'


def _secret():
    return getattr(settings, 'MP_WEBHOOK_SECRET', '')


def _token():
    return getattr(settings, 'MP_ACCESS_TOKEN', '')


def validar_assinatura(request):
    """
    Valida o header x-signature enviado pelo Mercado Pago.

    Formato: x-signature: ts=TIMESTAMP,v1=HMAC_SHA256_HEX
    Mensagem assinada: id:{data.id};request-id:{x-request-id};ts:{ts};

    Retorna True se a assinatura for válida, False caso contrário.
    Se MP_WEBHOOK_SECRET não estiver configurado, rejeita.
    """
    secret = _secret()
    if not secret:
        logger.warning('MP webhook: MP_WEBHOOK_SECRET não configurado')
        return False

    xsig = request.META.get('HTTP_X_SIGNATURE', '')
    xreqid = request.META.get('HTTP_X_REQUEST_ID', '')

    try:
        body_data = json.loads(request.body)
        data_id = str(body_data.get('data', {}).get('id', ''))
    except (json.JSONDecodeError, AttributeError):
        return False

    ts = v1 = ''
    for part in xsig.split(','):
        if part.startswith('ts='):
            ts = part[3:]
        elif part.startswith('v1='):
            v1 = part[3:]

    if not ts or not v1:
        return False

    message = f'id:{data_id};request-id:{xreqid};ts:{ts};'
    expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, v1)


def buscar_pagamento(payment_id):
    """
    Busca os detalhes de um pagamento na API do Mercado Pago.
    Retorna o dict do pagamento ou lança uma exceção.
    """
    token = _token()
    if not token:
        raise ValueError('MP_ACCESS_TOKEN não configurado')

    url = f'{_MP_API}/v1/payments/{payment_id}'
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        logger.error('MP API erro %s para payment %s', exc.code, payment_id)
        raise
