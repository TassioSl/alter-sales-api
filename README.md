# Alter Sales API

API separada do dashboard para receber vendas detalhadas da operacao e expor um feed que outro sistema pode consumir.

## Objetivo

Essa API resolve dois problemas:

1. Receber um contrato interno mais rico da operacao.
2. Expor um feed estavel para consumo externo.

## Fluxo correto

1. Se `SQL_*` estiver configurado, a API consulta o DW em tempo real para montar o feed do dia.
2. Se `SQL_*` nao estiver configurado, a operacao envia um lote para `POST /api/sales/intake`.
3. A API salva o ultimo lote localmente como fallback.
4. O consumidor externo busca os dados em:
   - `GET /api/alter/feed/per-hour`
   - `GET /api/alter/feed/per-store`

Essa API nao envia dados para o Alter.
Ela apenas publica os dados para serem consumidos.

## Campos internos cobertos

- valor da venda
- itens por venda
- codigo do vendedor
- nome do vendedor
- horario da venda
- identificador da loja
- identificador de devolucao

## Endpoints

- `GET /api/health`
- `POST /api/sales/intake`
- `GET /api/sales/latest`
- `POST /api/alter/preview/per-hour`
- `POST /api/alter/preview/per-store`
- `GET /api/alter/feed/per-hour`
- `GET /api/alter/feed/per-store`

## Seguranca minima

A API aceita autenticacao basica opcional para proteger os endpoints.

Variaveis:

- `SQL_HOST`
- `SQL_DATABASE`
- `SQL_USER`
- `SQL_PASSWORD`
- `SQL_DRIVER`
- `LIVE_STORE_CODE`
- `LIVE_STORE_ALIAS_ID`
- `INBOUND_API_USERNAME`
- `INBOUND_API_PASSWORD`

Se `SQL_*` estiver preenchido, os feeds e `GET /api/sales/latest` passam a consultar o banco em tempo real.
Se `SQL_*` estiver vazio, a API usa o ultimo lote salvo via intake.
Se `INBOUND_API_USERNAME` e `INBOUND_API_PASSWORD` estiverem vazios, a API nao exige autenticacao.
Se estiverem preenchidos, os endpoints protegidos exigem `Authorization: Basic ...`.

## Formato de entrada

```json
{
  "sales": [
    {
      "sale_id": "VENDA-1001",
      "store_id": "009-BIOMUNDO CONJUNTO NACIONAL",
      "store_alias_id": 9,
      "sold_at": "2026-04-10T11:04:00-03:00",
      "total_amount": 189.90,
      "items_count": 4,
      "seller_code": "987",
      "seller_name": "Maria Souza",
      "return_id": null
    }
  ]
}
```

## Loja preparada

O projeto ja ficou preparado com um exemplo da loja:

- `009-BIOMUNDO CONJUNTO NACIONAL`

Arquivo:

- [examples/store-009-conjunto-nacional.json](C:/Users/Bio%20Mundo/Desktop/dashboar/alter-sales-api/examples/store-009-conjunto-nacional.json)

Observacao:

- o `store_alias_id` precisa estar preenchido para o feed por loja
- o default configurado para a loja 009 pode ser `9`

## Como rodar

```powershell
cd C:\Users\Bio Mundo\Desktop\dashboar\alter-sales-api
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

## Como ver a saida antes

Ordem recomendada:

1. `POST /api/sales/intake`
2. `POST /api/alter/preview/per-hour`
3. `POST /api/alter/preview/per-store`
4. `GET /api/alter/feed/per-hour`
5. `GET /api/alter/feed/per-store`

Script pronto:

- [scripts/test_store_009_preview.ps1](C:/Users/Bio%20Mundo/Desktop/dashboar/alter-sales-api/scripts/test_store_009_preview.ps1)

Exemplo:

```powershell
cd C:\Users\Bio Mundo\Desktop\dashboar\alter-sales-api
$env:ALTER_SALES_API_URL="http://127.0.0.1:8010"
$env:INBOUND_API_USERNAME="admin"
$env:INBOUND_API_PASSWORD="senha-forte"
.\scripts\test_store_009_preview.ps1
```

Para ver o feed salvo depois do intake:

```powershell
$pair = "{0}:{1}" -f $env:INBOUND_API_USERNAME, $env:INBOUND_API_PASSWORD
$token = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair))
$headers = @{ Authorization = "Basic $token" }
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8010/api/alter/feed/per-hour" -Headers $headers | ConvertTo-Json -Depth 8
```

## Deploy no Render

Arquivos prontos:

- [render.yaml](C:/Users/Bio%20Mundo/Desktop/dashboar/alter-sales-api/render.yaml)
- [DEPLOY_RENDER.md](C:/Users/Bio%20Mundo/Desktop/dashboar/alter-sales-api/DEPLOY_RENDER.md)
- [.env.production.example](C:/Users/Bio%20Mundo/Desktop/dashboar/alter-sales-api/.env.production.example)

Segredos necessarios no Render:

- `SQL_HOST`
- `SQL_DATABASE`
- `SQL_USER`
- `SQL_PASSWORD`
- `SQL_DRIVER`
- `LIVE_STORE_CODE`
- `LIVE_STORE_ALIAS_ID`
- `INBOUND_API_USERNAME`
- `INBOUND_API_PASSWORD`

## Observacoes

- Para a loja `009-BIOMUNDO CONJUNTO NACIONAL`, o ideal e validar se o alias corresponde exatamente ao ponto ja integrado `Bio Mundo CNB 09`.
- Com `SQL_*` configurado, `GET /api/alter/feed/per-hour` e `GET /api/alter/feed/per-store` passam a refletir as vendas do dia consultadas no DW.
