from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from vendas.models import Caderneta, Cliente, Movimentacao, Produto, Venda


class Command(BaseCommand):
    help = (
        "Executa as migrações e importa uma única vez os dados extraídos do "
        "db.sqlite3 para o PostgreSQL configurado nas variáveis de ambiente."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "Apaga os dados atuais do app vendas antes de importar a fixture. "
                "Use somente quando quiser substituir o conteúdo do banco."
            ),
        )

    def handle(self, *args, **options):
        self.stdout.write("Aplicando migrações...")
        call_command("migrate", interactive=False, verbosity=options.get("verbosity", 1))

        models = [Produto, Cliente, Caderneta, Venda, Movimentacao]
        counts = {model._meta.verbose_name_plural: model.objects.count() for model in models}
        has_data = any(counts.values())

        if has_data and not options["force"]:
            formatted = ", ".join(f"{name}: {count}" for name, count in counts.items())
            raise CommandError(
                "O banco já contém dados do sistema e a importação foi cancelada "
                f"para evitar duplicações ({formatted}). Use --force apenas se "
                "quiser substituir esses registros."
            )

        if options["force"]:
            self.stdout.write(self.style.WARNING("Removendo dados atuais do app vendas..."))
            with transaction.atomic():
                Movimentacao.objects.all().delete()
                Venda.objects.all().delete()
                Caderneta.objects.all().delete()
                Cliente.objects.all().delete()
                Produto.objects.all().delete()

        self.stdout.write("Importando dados do SQLite...")
        call_command("loaddata", "dados_sqlite", verbosity=options.get("verbosity", 1))

        final_counts = {
            "produtos": Produto.objects.count(),
            "clientes": Cliente.objects.count(),
            "cadernetas": Caderneta.objects.count(),
            "vendas": Venda.objects.count(),
            "movimentações": Movimentacao.objects.count(),
        }
        formatted = ", ".join(f"{name}: {count}" for name, count in final_counts.items())
        self.stdout.write(self.style.SUCCESS(f"Banco preparado com sucesso — {formatted}."))
