"""Atalho explícito para preparar o banco PostgreSQL hospedado no Supabase."""

from .preparar_postgres import Command as PrepararPostgresCommand


class Command(PrepararPostgresCommand):
    help = (
        "Executa as migrações e importa uma única vez os dados do db.sqlite3 "
        "para o PostgreSQL do Supabase configurado nas variáveis de ambiente."
    )
