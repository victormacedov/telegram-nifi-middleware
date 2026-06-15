# Sistema de Abertura de Chamados via Telegram + Apache NiFi

Sistema de middleware desenvolvido como atividade acadêmica, que integra um bot do Telegram com o Apache NiFi para receber, processar e rotear chamados de clientes (Pessoa Física ou Pessoa Jurídica).

---

## Visão Geral

```
Usuário (Telegram)
       ↓
Script Python  ←  lê a última mensagem e envia via HTTP
       ↓
Apache NiFi (Middleware)
       ├── Identifica CPF (PF) ou CNPJ (PJ)
       ├── Monta mensagem formatada
       └── Envia resposta via API do Telegram
       ↓
Atendente recebe o chamado formatado (Telegram)
```

O Apache NiFi atua como **middleware**: ele recebe os dados brutos, processa, roteia e entrega a mensagem correta ao destino — sem que o remetente ou o destinatário precisem conhecer um ao outro.

---

## Pré-requisitos

- Python 3.x instalado
- Apache NiFi instalado e rodando em `https://localhost:8443`
- Bot do Telegram criado via [@BotFather](https://t.me/BotFather) (com token em mãos)
- `chat_id` do usuário que receberá os chamados

---

## Estrutura do Projeto

```
📁 projeto/
├── telegram_to_nifi.py          # Script Python principal
├── nifi_identify_script.groovy  # Script Groovy para o NiFi (ExecuteScript)
├── requirements.txt             # Dependências Python
├── .env.example                 # Modelo de variáveis de ambiente
├── .gitignore                   # Arquivos ignorados pelo Git
└── README.md
```

---

## Configuração

### 1. Instalar dependências Python

```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Copie o arquivo de exemplo e preencha com seus dados:

```bash
cp .env.example .env
```

Abra o `.env` e preencha:

```
BOT_TOKEN=token_do_seu_bot
CHAT_ID=chat_id_do_atendente
NIFI_URL=http://localhost:9090/contentListener
```

> O arquivo `.env` está no `.gitignore` e **nunca deve ser enviado ao repositório**.

### 3. Fluxo no Apache NiFi

Acesse `https://localhost:8443/nifi` e monte os processadores na ordem abaixo.

#### Processadores e configurações:

**① ListenHTTP**
| Propriedade | Valor |
|---|---|
| Listening Port | `9090` |
| Base Path | `contentListener` |

**② ExecuteScript**
| Propriedade | Valor |
|---|---|
| Script Engine | `Groovy` |
| Script Body | *(conteúdo do arquivo `nifi_identify_script.groovy`)* |

Identifica o tipo de documento pelo número de dígitos:
- 11 dígitos → CPF → `tipo_cliente = PF`
- 14 dígitos → CNPJ → `tipo_cliente = PJ`

**③ RouteOnAttribute**
| Nome da Rota | Expressão |
|---|---|
| `PF` | `${tipo_cliente:equals('PF')}` |
| `PJ` | `${tipo_cliente:equals('PJ')}` |

**④ ReplaceText — ramo PF**

Replacement Strategy: `Always Replace`

Replacement Value:
```
{"chat_id": "SEU_CHAT_ID", "text": "📋 NOVO CHAMADO ABERTO\n\nTipo: Pessoa Física\n\n👤 Nome: ${nome_cliente}\n🪪 CPF: ${documento_cliente}\n📝 Demanda: ${demanda_cliente}\n\n⏱ Aguarde, em breve entraremos em contato."}
```

**⑤ ReplaceText — ramo PJ**

Replacement Strategy: `Always Replace`

Replacement Value:
```
{"chat_id": "SEU_CHAT_ID", "text": "📋 NOVO CHAMADO ABERTO\n\nTipo: Pessoa Jurídica\n\n🏢 Empresa: ${nome_cliente}\n🪪 CNPJ: ${documento_cliente}\n📝 Demanda: ${demanda_cliente}\n\n⏱ Aguarde, em breve entraremos em contato."}
```

> Substitua `SEU_CHAT_ID` pelo valor da variável `CHAT_ID` do seu `.env`.

**⑥ InvokeHTTP** *(conectado aos dois ReplaceText)*
| Propriedade | Valor |
|---|---|
| HTTP Method | `POST` |
| Remote URL | `https://api.telegram.org/botSEU_TOKEN_AQUI/sendMessage` |
| Content-Type | `application/json` |

> Substitua `SEU_TOKEN_AQUI` pelo valor da variável `BOT_TOKEN` do seu `.env`.

#### Conexões:
```
ListenHTTP → ExecuteScript → RouteOnAttribute → ReplaceText PF → InvokeHTTP
                                              ↘ ReplaceText PJ ↗
```

Saídas não utilizadas (failure, unmatched, etc.) devem ser marcadas como **Auto-terminate**.

---

## Como Usar

### 1. Iniciar o NiFi

Certifique que o NiFi está rodando e todos os processadores estão **verdes (ativos)**.

### 2. Enviar uma mensagem para o bot

O cliente envia uma mensagem no seguinte formato:

```
Nome;CPF_ou_CNPJ;"mensagem"
```

Exemplos:

```
João Silva;123.456.789-09;"Preciso de suporte técnico"
```

```
Empresa XYZ Ltda;12.345.678/0001-99;"Solicito orçamento de serviços"
```

### 3. Executar o script Python

```bash
python telegram_to_nifi.py
```

O script lê a última mensagem recebida pelo bot e a envia ao NiFi via requisição HTTP.

---

## Mensagens Geradas

**Pessoa Física (CPF):**
```
📋 NOVO CHAMADO ABERTO

Tipo: Pessoa Física

👤 Nome: João Silva
🪪 CPF: 123.456.789-09
📝 Demanda: Preciso de suporte técnico

⏱ Aguarde, em breve entraremos em contato.
```

**Pessoa Jurídica (CNPJ):**
```
📋 NOVO CHAMADO ABERTO

Tipo: Pessoa Jurídica

🏢 Empresa: Empresa XYZ Ltda
🪪 CNPJ: 12.345.678/0001-99
📝 Demanda: Solicito orçamento de serviços

⏱ Aguarde, em breve entraremos em contato.
```

---

## Papel do Apache NiFi

O NiFi atua como **middleware** neste sistema, desempenhando o papel de camada intermediária entre quem envia e quem recebe o chamado:

- **Recebe** os dados brutos via HTTP (ListenHTTP)
- **Processa** e identifica o tipo de cliente (ExecuteScript)
- **Roteia** o fluxo conforme a regra de negócio — PF ou PJ (RouteOnAttribute)
- **Transforma** os dados em mensagem formatada (ReplaceText)
- **Entrega** ao destino final via API do Telegram (InvokeHTTP)

---

## Tecnologias Utilizadas

| Tecnologia | Versão | Função |
|---|---|---|
| Apache NiFi | 2.9.0 | Middleware de processamento e roteamento |
| Python | 3.x | Leitura do bot e envio ao NiFi |
| Telegram Bot API | — | Canal de comunicação com o cliente |
| Groovy | — | Script de identificação CPF/CNPJ no NiFi |
| python-dotenv | — | Gerenciamento de variáveis de ambiente |