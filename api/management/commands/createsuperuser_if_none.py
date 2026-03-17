from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser if none exists'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Email address for the superuser')
        parser.add_argument('--password', required=True, help='Password for the superuser')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']

        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING('A superuser already exists. Skipping.'))
            return

        user = User.objects.create_superuser(
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f'Superuser created with email {email}'))
