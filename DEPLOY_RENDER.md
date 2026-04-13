# Deploy no Render

## 1. Subir para um repositorio Git

Coloque a pasta `alter-sales-api` em um repositorio no GitHub.

Estrutura minima:

- `alter-sales-api/app`
- `alter-sales-api/render.yaml`
- `alter-sales-api/pyproject.toml`

## 2. Criar o servico

No Render:

1. Clique em `New +`
2. Escolha `Blueprint`
3. Conecte o repositorio
4. O Render vai ler o `render.yaml`

## 3. Variaveis obrigatorias

Preencha no Render:

- `INBOUND_API_USERNAME`
- `INBOUND_API_PASSWORD`

Ja vem preenchida no blueprint:

- `LOG_LEVEL=INFO`

## 4. Comando de start

O projeto ja esta configurado para subir com:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT

Build command recomendado:

```bash
poetry install --no-root
```
```

## 5. Teste depois do deploy

Troque `SUA-URL` pela URL gerada pelo Render:

```powershell
$env:ALTER_SALES_API_URL="https://SUA-URL.onrender.com"
$env:INBOUND_API_USERNAME="admin"
$env:INBOUND_API_PASSWORD="sua-senha"
.\scripts\test_store_009_preview.ps1
```

## 6. Ordem certa de validacao

1. testar `GET /api/health`
2. testar `POST /api/sales/intake`
3. testar `GET /api/sales/latest`
4. testar `GET /api/alter/feed/per-hour`
5. testar `GET /api/alter/feed/per-store`

## 7. Recomendacao pratica

Para a primeira publicacao:

- publique a API
- valide `health`, `intake` e os feeds
- depois entregue a URL para o Alter consumir
