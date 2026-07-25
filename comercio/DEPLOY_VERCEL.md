# SimaoFarma no Vercel com Supabase

Esta versão usa:

- **SQLite** no desenvolvimento local, quando nenhuma URL PostgreSQL está configurada;
- **Supabase Postgres** em produção na Vercel;
- **Transaction Pooler** no runtime serverless;
- conexão não agrupada, quando disponibilizada pela integração, para migrações e importações executadas localmente.

Os dados do `db.sqlite3` enviado foram convertidos para:

- `vendas/fixtures/dados_sqlite.json`
- 116 produtos
- 20 vendas
- 6 clientes
- 6 cadernetas
- 23 movimentações

## 1. Publicar o código no GitHub

Abra o terminal nesta pasta, onde estão `manage.py` e `requirements.txt`:

```powershell
git init
git add .
git commit -m "Deploy Vercel com Supabase e dados do SQLite"
git branch -M main
git remote add origin URL_DO_SEU_REPOSITORIO
git push -u origin main
```

O `db.sqlite3` está ignorado pelo Git. Os dados de produção estão na fixture JSON, que deve ser enviada ao repositório.

## 2. Criar o projeto no Supabase

1. Acesse o Supabase e crie um projeto.
2. Defina e guarde a senha do banco.
3. Aguarde o banco ficar disponível.
4. No painel do projeto, use o botão **Connect** para consultar as strings de conexão.

A aplicação Django não precisa das chaves `anon`, `publishable` ou `service_role` para acessar o banco diretamente. Ela precisa apenas da URL PostgreSQL.

## 3. Conectar o Supabase à Vercel — opção recomendada

No projeto da Vercel:

1. abra **Storage** ou **Marketplace**;
2. procure por **Supabase**;
3. instale a integração e conecte o projeto Supabase criado;
4. selecione os ambientes **Production**, **Preview** e, se desejar, **Development**;
5. confirme em **Settings > Environment Variables** que existem pelo menos:
   - `POSTGRES_URL`
   - `POSTGRES_URL_NON_POOLING`

A configuração desta aplicação usa automaticamente:

- `POSTGRES_URL` no runtime da Vercel;
- `POSTGRES_URL_NON_POOLING` fora da Vercel, para migrações e importação.

## 4. Configurar as variáveis Django

Adicione em **Vercel > Settings > Environment Variables**:

```text
DJANGO_SECRET_KEY=uma-chave-longa-e-aleatoria
DJANGO_DEBUG=false
```

Para gerar uma chave no PowerShell:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Caso use domínio próprio:

```text
DJANGO_ALLOWED_HOSTS=seudominio.com,www.seudominio.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://seudominio.com,https://www.seudominio.com
```

Depois de criar ou alterar variáveis na Vercel, faça um novo deploy.

## 5. Alternativa: configurar a URL manualmente

Caso não use a integração da Vercel:

1. no Supabase, clique em **Connect**;
2. escolha **Transaction pooler**;
3. copie a URI que usa a porta `6543`;
4. adicione essa URI na Vercel como `DATABASE_URL` para Production e Preview.

Exemplo de formato:

```text
postgresql://postgres.PROJECT_REF:SENHA@aws-REGIAO.pooler.supabase.com:6543/postgres?sslmode=require
```

A aplicação detecta a porta `6543` e desativa automaticamente prepared statements e cursores vinculados à sessão, necessários para o Transaction Pooler.

Nunca publique a URL real no GitHub.

## 6. Importar o conteúdo do SQLite para o Supabase

Instale a CLI e vincule o diretório ao projeto Vercel:

```powershell
npm install -g vercel
vercel login
vercel link
```

Baixe as variáveis de produção para o arquivo local ignorado pelo Git:

```powershell
vercel env pull .env.local --environment=production --yes
```

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

Execute a preparação do Supabase:

```powershell
python manage.py preparar_supabase
```

O comando:

1. executa as migrações do Django;
2. verifica se as tabelas do sistema estão vazias;
3. importa a fixture com os dados do SQLite;
4. informa as quantidades importadas;
5. cancela a operação se encontrar dados, evitando duplicações.

Resultado esperado:

```text
Banco preparado com sucesso — produtos: 116, clientes: 6, cadernetas: 6, vendas: 20, movimentações: 23.
```

### Se a conexão não agrupada falhar por IPv6

A conexão direta do Supabase pode depender de IPv6. Caso `POSTGRES_URL_NON_POOLING` falhe no seu computador:

1. abra **Supabase > Connect**;
2. copie a URI de **Session pooler**, porta `5432`;
3. coloque-a temporariamente em `.env.local` como `DATABASE_URL`;
4. execute novamente `python manage.py preparar_supabase`.

Também é possível usar temporariamente a URI do Transaction Pooler, porta `6543`.

### Substituir dados existentes

Somente quando quiser apagar os registros atuais e restaurar novamente a cópia do SQLite:

```powershell
python manage.py preparar_supabase --force
```

Não use `--force` depois que o sistema começar a receber dados reais.

## 7. Publicar em produção

```powershell
vercel --prod
```

Ou faça push para a branch de produção conectada à Vercel.

## Prioridade das variáveis de banco

A aplicação aceita estas variáveis:

1. `DATABASE_URL` — substituição manual com maior prioridade;
2. `SUPABASE_DATABASE_URL` — alias manual;
3. na Vercel: `POSTGRES_URL`, criada pela integração;
4. localmente: `POSTGRES_URL_NON_POOLING`, criada pela integração;
5. sem nenhuma delas, usa `db.sqlite3` apenas fora da Vercel.

## Desenvolvimento local somente com SQLite

Remova ou não crie `.env.local` e execute:

```powershell
python manage.py runserver
```

Nunca coloque no GitHub a senha do banco, `DATABASE_URL`, `POSTGRES_URL`, `POSTGRES_URL_NON_POOLING` ou `DJANGO_SECRET_KEY`.
