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

- `GET /`
- `GET /api/health`
- `POST /api/sales/intake`
- `GET /api/sales/latest`
- `POST /api/alter/preview/per-hour`
- `POST /api/alter/preview/per-store`
- `GET /api/alter/feed/per-hour`
- `GET /api/alter/feed/per-store`
- `GET /docs`

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

Loja padrao configurada:

- `009 - BIOMUNDO CONJUNTO NACIONAL`
- `store_alias_id = 9`

## Operacao

Fluxo recomendado hoje:

1. consultar o DW no ambiente interno
2. publicar o lote real em `POST /api/sales/intake` no Render
3. consumir os feeds do Render normalmente

Scripts prontos:

- [run_render_sync.bat](C:/Users/Bio%20Mundo/Desktop/dashboar/alter-sales-api/run_render_sync.bat)
- [run_render_sync_loop.bat](C:/Users/Bio%20Mundo/Desktop/dashboar/alter-sales-api/run_render_sync_loop.bat)
- [teste_com_senha.bat](C:/Users/Bio%20Mundo/Desktop/dashboar/alter-sales-api/teste_com_senha.bat)
- [teste_sem_senha.bat](C:/Users/Bio%20Mundo/Desktop/dashboar/alter-sales-api/teste_sem_senha.bat)

Para ver o feed salvo depois do intake:

```powershell
$pair = "biomundo_api:SUA_SENHA"
$token = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair))
$headers = @{ Authorization = "Basic $token" }
Invoke-RestMethod -Method Get -Uri "https://alter-sales-api-1.onrender.com/api/alter/feed/per-hour" -Headers $headers | ConvertTo-Json -Depth 8
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
