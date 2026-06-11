import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Cria o superusuário admin padrão se não existir'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('ADMIN_USERNAME', 'admin')
        email = os.environ.get('ADMIN_EMAIL', 'admin@barrs.com.br')
        password = os.environ.get('ADMIN_PASSWORD', '')

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Superusuário "{username}" já existe — ignorando.')
            )
            return

        if not password:
            self.stdout.write(
                self.style.ERROR(
                    'ADMIN_PASSWORD não definida — superusuário NÃO criado. '
                    'Defina a variável de ambiente ADMIN_PASSWORD no Railway.'
                )
            )
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(
            self.style.SUCCESS(f'Superusuário "{username}" criado com sucesso.')
        )
