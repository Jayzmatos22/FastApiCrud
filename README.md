# FastApiCrud

CRUD de usuários em **FastAPI** + **SQLAlchemy 2.0** + **Pydantic v2**.

Projeto de estudo. O escopo é deliberadamente pequeno: um CRUD de usuários com
validação de entrada e hash de senha, **sem autenticação** — não há JWT, sessão
ou qualquer controle de acesso. Todos os endpoints são abertos.

---

## Stack

| Camada | Ferramenta |
| --- | --- |
| Web framework | FastAPI |
| Servidor ASGI | Uvicorn |
| ORM | SQLAlchemy 2.0 (declarativo com `Mapped` / `mapped_column`) |
| Validação | Pydantic v2 (`EmailStr`, `field_validator`, `ConfigDict`) |
| Configuração | pydantic-settings (lê `DATABASE_URL` do `.env`) |
| Hash de senha | pwdlib + bcrypt |
| Banco (default) | SQLite |

---

## Estrutura

```
app/
├── main.py              # instancia o FastAPI, cria as tabelas e registra os routers
├── config.py            # Settings: DATABASE_URL via .env
├── database.py          # engine, SessionLocal, Base declarativo e a dependência get_db
├── routers/
│   └── usuarios.py      # camada HTTP: as 4 rotas
├── schema/
│   └── user_schema.py   # contratos: CreateUser, UpdateUser, ResponseUser
├── service/
│   └── user.py          # regra de negócio e acesso ao banco
└── models/
    └── user.py          # entidade User (tabela users)
```

Cada camada só conhece a de baixo:

```
router  ->  service  ->  model
   \           \
    \           +-- schema (CreateUser / UpdateUser na entrada)
     +------------- schema (ResponseUser na saída)
```

O router não monta query nenhuma: ele recebe a `Session` por injeção de
dependência (`DbSession`) e repassa ao service.

---

## Modelo de dados

Tabela `users`:

| Coluna | Tipo | Regras |
| --- | --- | --- |
| `id` | `int` | PK, autoincremento |
| `name` | `varchar(255)` | obrigatório, `CheckConstraint` `length(name) >= 2` |
| `email` | `varchar(255)` | obrigatório, único (`uq_users_email` + índice único) |
| `hash_password` | `varchar(255)` | obrigatório, nunca exposto na resposta |
| `active` | `boolean` | default `True`; usado no soft delete |
| `created_at` | `timestamp` | `server_default=now()` |

Índice composto adicional: `ix_users_name_active` sobre (`name`, `active`).

---

## Schemas

### `CreateUser` (entrada do POST)

- `name`: 3 a 50 caracteres, precisa ter **nome + sobrenome**, não pode conter
  dígitos, e passa por `.strip()`.
- `email`: validado pelo `EmailStr`.
- `password`: 8 a 72 caracteres, em texto puro. O limite de 72 é o máximo de
  bytes que o bcrypt processa.

### `UpdateUser` (entrada do PATCH)

- `name` e `email`, ambos opcionais. Só os campos presentes no corpo são
  alterados; um `null` explícito é ignorado (`exclude_unset` + `exclude_none`).
- `name` reaproveita o mesmo tipo `Nome` do `CreateUser`, então as regras de
  tamanho, nome + sobrenome, ausência de dígitos e `.strip()` valem nas duas
  rotas.

### `ResponseUser` (saída de todas as rotas)

Usa `ConfigDict(from_attributes=True)` para ler direto do objeto ORM e devolve
apenas `id`, `name`, `email` e `created_at`. A senha, mesmo com hash, nunca sai
da API.

Repare na assimetria proposital: o cliente envia `password` (texto puro) e o
banco guarda `hash_password`. Quem converte um no outro é o service.

---

## Endpoints

Prefixo comum: `/usuarios`.

| Método | Rota | O que faz |
| --- | --- | --- |
| `POST` | `/usuarios/registrar` | cria usuário |
| `GET` | `/usuarios/{email}` | busca por e-mail |
| `PATCH` | `/usuarios/{user_id}` | atualiza nome e/ou e-mail |
| `DELETE` | `/usuarios/{user_id}` | soft delete (marca `active = False`) |

### `POST /usuarios/registrar`

**Request**

```json
{
  "name": "Jailton Matos",
  "email": "jailton@example.com",
  "password": "senha12345"
}
```

**Response — `201 Created`**

```json
{
  "id": 1,
  "name": "Jailton Matos",
  "email": "jailton@example.com",
  "created_at": "2026-11-09T14:32:00"
}
```

| Status | Quando |
| --- | --- |
| `409 Conflict` | e-mail já cadastrado |
| `422 Unprocessable Entity` | payload reprovado pelos validadores |

O e-mail duplicado é tratado em dois pontos de propósito: o `select` antes do
insert devolve mensagem limpa no caso comum, e o `except IntegrityError` com
`rollback()` cobre a corrida entre duas requisições simultâneas, que o `select`
sozinho não pega.

### `GET /usuarios/{email}`

O `@` do e-mail pode ir literal ou codificado como `%40` — o FastAPI decodifica.

```
GET /usuarios/jailton@example.com
```

| Status | Quando |
| --- | --- |
| `200 OK` | usuário encontrado e ativo |
| `404 Not Found` | e-mail inexistente **ou** usuário com `active = False` |

### `PATCH /usuarios/{user_id}`

Atualização parcial, buscando por **id** (não por e-mail, como o GET).

```json
{ "name": "Jailton Santos" }
```

| Status | Quando |
| --- | --- |
| `200 OK` | atualizado, devolve o usuário completo |
| `409 Conflict` | o novo e-mail já pertence a outro usuário |
| `422 Unprocessable Entity` | payload reprovado pelos validadores |
| `404 Not Found` | id inexistente **ou** usuário com `active = False` |

Enviar o próprio e-mail atual do usuário não é conflito: responde `200`.

### `DELETE /usuarios/{user_id}`

**Soft delete**: não remove a linha, apenas marca `active = False`. O registro
continua no banco e o e-mail segue ocupando a constraint de unicidade.

| Status | Quando |
| --- | --- |
| `204 No Content` | marcado como inativo (sem corpo na resposta) |
| `404 Not Found` | id inexistente **ou** já inativo |

Note que a operação **não é idempotente**: um segundo `DELETE` no mesmo id
devolve `404`. É o preço de tratar inativo como inexistente em todas as rotas,
de forma consistente com o `GET` e o `PATCH`.

---

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate           # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Dois detalhes que custam tempo quando passam batido:

- O módulo é **`app.main`**, não `main` — o arquivo está em `app/`. Rodar
  `uvicorn main:app` devolve `Could not import module "main"`.
- O venv precisa estar ativo (o prompt mostra `(.venv)`). Sem ativar, usa-se o
  `uvicorn` do Python global e o erro vira
  `ModuleNotFoundError: No module named 'sqlalchemy'`.

Documentação interativa: <http://127.0.0.1:8000/docs>

As rotas `POST`, `PATCH` e `DELETE` não podem ser testadas pela barra de
endereço do navegador, que só emite `GET`. Use o `/docs`, curl ou Postman.

### Configuração

Sem `.env`, o banco é SQLite em `./app.db`, criado no primeiro start. Para
trocar, crie um `.env` na raiz:

```
DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/fastapicrud
```

Para Postgres é preciso instalar o driver, que não está no `requirements.txt`:
`pip install "psycopg[binary]"`.

As tabelas são criadas por `Base.metadata.create_all()` no start. Isso **não**
altera tabela existente: ao mudar o modelo, apague o `app.db` para recriar do
zero — ou adote o Alembic, já declarado nas dependências.

---

## Limitações conhecidas

Comportamentos verificados que ainda não estão resolvidos:

**1. Não há listagem**

Falta um `GET /usuarios` com paginação.

**2. Não há suíte de testes**

`pytest` e `httpx2` estão instalados e declarados, mas não existe diretório
`tests/`. As rotas foram verificadas manualmente via `TestClient`.

**3. Nenhum controle de acesso**

Por desenho, não há autenticação. Qualquer cliente pode alterar ou desativar
qualquer usuário informando o `id`. É aceitável para um projeto de estudo local,
mas inviabiliza qualquer exposição pública.

---

## Próximos passos

- `GET /usuarios` com paginação.
- Testes com `pytest` + `TestClient` (as dependências já estão instaladas, mas
  não existe suíte).
- Migrations com Alembic no lugar do `create_all`.
- `Dockerfile` e `docker-compose.yml` com Postgres.
