# FastApiCrud

CRUD de usuários em **FastAPI** + **SQLAlchemy 2.0** + **Pydantic v2**.

Projeto de estudo, em construção. O código está versionado no estado em que foi
escrito (rascunho), justamente para registrar a evolução. A seção
[Próximos passos](#próximos-passos) lista o que falta para a API subir.

---

## Stack

| Camada | Ferramenta |
| --- | --- |
| Web framework | FastAPI |
| Servidor ASGI | Uvicorn |
| ORM | SQLAlchemy 2.0 (estilo declarativo com `Mapped` / `mapped_column`) |
| Validação | Pydantic v2 (`EmailStr`, `field_validator`, `ConfigDict`) |
| Hash de senha | Passlib + bcrypt |

---

## Estrutura

```
app/
├── main.py              # instancia o FastAPI e registra os routers
├── routers/
│   └── usuarios.py      # camada HTTP: POST /usuarios/registrar
├── schema/
│   └── user_schema.py   # contratos de entrada (CreateUser) e saída (ResponseUser)
├── service/
│   └── user.py          # regra de negócio: create_new_user
└── models/
    └── user.py          # entidade User (tabela users)
```

A ideia da separação é que cada camada só conheça a de baixo:

```
router  ->  service  ->  model
   \           \
    \           +-- schema (CreateUser na entrada)
     +------------- schema (ResponseUser na saída)
```

O router não fala com o banco e o service não sabe o que é HTTP status code — a
tradução de erro de domínio para resposta HTTP acontece na borda.

---

## Modelo de dados

Tabela `users`:

| Coluna | Tipo | Regras |
| --- | --- | --- |
| `id` | `int` | PK, autoincremento |
| `name` | `varchar(255)` | obrigatório, `CheckConstraint` de tamanho mínimo |
| `email` | `varchar(255)` | obrigatório, único, indexado |
| `hash_password` | `varchar(255)` | obrigatório, nunca exposto na resposta |
| `active` | `boolean` | default `True` |
| `created_at` | `timestamptz` | `server_default=now()` |

---

## Validações do `CreateUser`

- `name`: 3 a 50 caracteres, precisa ter **nome + sobrenome** e não pode conter
  dígitos.
- `email`: validado pelo `EmailStr` do Pydantic.
- `password`: recebido em texto puro e convertido em `hash_password` antes de
  chegar no banco.

O `ResponseUser` usa `model_config = ConfigDict(from_attributes=True)` para ler
direto do objeto ORM e devolve apenas `id`, `name`, `email` e `created_at` — a
senha (mesmo com hash) nunca sai da API.

---

## Endpoint

### `POST /usuarios/registrar`

**Request**

```json
{
  "name": "Jailton Matos",
  "email": "jailton@example.com",
  "password": "senha-secreta"
}
```

**Response — `201 Created`**

```json
{
  "id": 1,
  "name": "Jailton Matos",
  "email": "jailton@example.com",
  "created_at": "2026-10-22T21:48:00Z"
}
```

**Erros**

| Status | Quando |
| --- | --- |
| `409 Conflict` | e-mail já cadastrado (checagem prévia + `IntegrityError` no commit) |
| `422 Unprocessable Entity` | payload reprovado pelos validadores do Pydantic |

O tratamento do e-mail duplicado é feito em dois pontos de propósito: o `select`
antes do insert devolve uma mensagem limpa no caso comum, e o `except
IntegrityError` com `rollback()` cobre a corrida entre duas requisições
simultâneas, que o `select` sozinho não pega.

---

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Documentação interativa: <http://127.0.0.1:8000/docs>

---

## Próximos passos

O que ainda falta — na ordem em que compensa atacar:

**1. Camada de banco (não existe ainda)**

Criar `app/database.py` com `create_engine`, `sessionmaker` e a dependência
`get_db()`, e chamar `Base.metadata.create_all(bind=engine)` no `main.py`.
Hoje `get_db` é usado no router sem existir em lugar nenhum.

**2. `app/models/user.py`**

- `User` herda de `DeclarativeBase` em vez de herdar de `Base`.
- `__table_args__` precisa da vírgula final para ser tupla:
  `(CheckConstraint(...),)`.
- Na coluna `email`: `Unique=True` → `unique=True`, e falta a vírgula antes de
  `nullable=False`.
- Os imports do Pydantic não são usados nesse arquivo.

**3. `app/schema/user_schema.py`**

- `Configdict` → `ConfigDict`.
- `password` está sem tipo — deve ser `str = Field(min_length=8)`.
- `valid_email` é redundante: o `EmailStr` já garante o formato.
- O validador `limpar_nome` não limpa nada; faltou o `.strip()` / normalização
  do espaçamento que o nome promete.
- `min_length=3` no schema contra `length(name) >= 2` no `CheckConstraint`:
  alinhar os dois.

**4. `app/service/user.py`**

- `from app.models.user import user` → `User` (maiúsculo).
- Falta importar `HTTPException` e `status` do FastAPI.
- `status.409_CONFLICT` → `status.HTTP_409_CONFLICT`.
- `data_user.hash_password` não existe: o campo é `password` e precisa passar
  pelo `pwd.hash(...)` antes de virar `hash_password`.
- `deprecated="ato"` → `deprecated="auto"`.

**5. `app/routers/usuarios.py`**

- `from typing import annotated` → `Annotated`.
- Importar `CreateUser` e `ResponseUser` do schema.
- `DbSession` está declarado mas não usado — trocar
  `db: Session = Depends(get_db)` por `db: DbSession`.

**6. `app/main.py`**

- Remover o dicionário `u: User = {...}`: anotar um `dict` como `User` não
  cria uma instância do modelo nem valida nada.

**Depois disso**

- Completar o CRUD: `GET /usuarios`, `GET /usuarios/{id}`,
  `PATCH /usuarios/{id}`, `DELETE /usuarios/{id}` (soft delete via `active`).
- Autenticação com JWT.
- Migrations com Alembic no lugar do `create_all`.
- Testes com `pytest` + `TestClient`.
- `Dockerfile` e `docker-compose.yml` com Postgres.
