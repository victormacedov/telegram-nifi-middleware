# Guia de Montagem — Apache NiFi Middleware (Telegram Bot)

## Visão Geral do Fluxo

```
[ListenHTTP] → [ExecuteScript] → [RouteOnAttribute] → [ReplaceText PF] → [InvokeHTTP → Telegram]
                                                    ↘ [ReplaceText PJ] → [InvokeHTTP → Telegram]
```

---

## Passo 1 — Processador: ListenHTTP

| Propriedade        | Valor                  |
|--------------------|------------------------|
| Listening Port     | `9090`                 |
| Base Path          | `contentListener`      |
| Max Data to Receive| `1 MB`                 |

> Este é o endpoint que o script Python chama via curl.
> URL completa: `https://localhost:8443/contentListener`
> (O NiFi redireciona internamente a porta 9090 pelo proxy HTTPS)

---

## Passo 2 — Processador: ExecuteScript

| Propriedade     | Valor                        |
|-----------------|------------------------------|
| Script Engine   | `Groovy`                     |
| Script Body     | *(cole o conteúdo de `nifi_identify_script.groovy`)* |

Este script lê o JSON recebido, conta os dígitos do documento e adiciona:
- Atributo `tipo_cliente` = `PF` ou `PJ`
- Atributos: `nome_cliente`, `documento_cliente`, `demanda_cliente`

---

## Passo 3 — Processador: RouteOnAttribute

Crie duas rotas:

| Nome da Rota | Expressão NiFi EL              |
|--------------|-------------------------------|
| `PF`         | `${tipo_cliente:equals('PF')}` |
| `PJ`         | `${tipo_cliente:equals('PJ')}` |

---

## Passo 4a — Processador: ReplaceText (ramo PF)

| Propriedade          | Valor |
|----------------------|-------|
| Replacement Value    | `Abertura de chamado PF, dados do cliente: Nome: ${nome_cliente} \| Documento (CPF): ${documento_cliente} \| Demanda: ${demanda_cliente}` |
| Replacement Strategy | `Always Replace` |

---

## Passo 4b — Processador: ReplaceText (ramo PJ)

| Propriedade          | Valor |
|----------------------|-------|
| Replacement Value    | `Abertura de chamado PJ, dados da empresa: Nome: ${nome_cliente} \| Documento (CNPJ): ${documento_cliente} \| Demanda: ${demanda_cliente}` |
| Replacement Strategy | `Always Replace` |

---

## Passo 5 — Processador: ReplaceText (montar JSON do Telegram)

> Adicione este processador **após** cada ReplaceText de PF e PJ.
> Ele formata o corpo da requisição que será enviada à API do Telegram.

| Propriedade          | Valor |
|----------------------|-------|
| Replacement Value    | `{"chat_id": "SEU_CHAT_ID_AQUI", "text": "${message.body}"}` |
| Replacement Strategy | `Always Replace` |

**Atenção:** Substitua `SEU_CHAT_ID_AQUI` pelo chat_id real.

---

## Passo 6 — Processador: InvokeHTTP (enviar para o Telegram)

| Propriedade          | Valor |
|----------------------|-------|
| HTTP Method          | `POST` |
| Remote URL           | `https://api.telegram.org/botSEU_TOKEN_AQUI/sendMessage` |
| Content-Type         | `application/json` |

**Atenção:** Substitua `SEU_TOKEN_AQUI` pelo token real do bot.

---

## Como Testar

1. Inicie todos os processadores no NiFi.
2. Envie uma mensagem para o bot no formato:
   ```
   João Silva;123.456.789-09;"Preciso de suporte"
   ```
   ou para PJ:
   ```
   Empresa XYZ;12.345.678/0001-99;"Solicito orçamento"
   ```
3. Execute o script Python:
   ```bash
   python telegram_to_nifi.py
   ```
4. O NiFi processa e envia a mensagem formatada para o Telegram.

---

## Mensagens Esperadas no Telegram

**PF:**
```
Abertura de chamado PF, dados do cliente: Nome: João Silva | Documento (CPF): 123.456.789-09 | Demanda: Preciso de suporte
```

**PJ:**
```
Abertura de chamado PJ, dados da empresa: Nome: Empresa XYZ | Documento (CNPJ): 12.345.678/0001-99 | Demanda: Solicito orçamento
```
