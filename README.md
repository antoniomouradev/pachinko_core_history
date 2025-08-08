
# Documentação do Projeto: Armazenamento de Payload com Tornado + Redis

**Versão gerada em:** 08/08/2025 20:06:40

## 📁 Estrutura de diretórios

```
history tree
.
├── Dockerfile
├── Makefile
├── README.md
├── app
│   ├── __pycache__
│   ├── app.py
│   ├── mylog.py
│   ├── redis_connection.py
│   └── test_api.py
├── bin
│   └── app_server
├── compile.sh
├── docker-compose.yml
├── log
│   └── server.log
├── requirements.txt
└── sample.txt
```

## 🧠 Descrição geral

O projeto consiste em um microserviço desenvolvido com **Tornado** para armazenamento de dados temporários em **Redis**, com endpoints protegidos por uma chave `X-API-KEY`. Os dados são serializados com `pickle` e armazenados com TTL padrão de 30 dias.

## ⚙️ Componentes principais

### `app.py`
- Define os endpoints:
    - `POST /save_input?uuid=` — armazena payload de entrada
    - `POST /save_output?uuid=` — armazena payload de saída
    - `GET /get_payload?uuid=` — retorna input/output salvos
- Uso do `ThreadPoolExecutor` para I/O não bloqueante.
- Segurança: exige `X-API-KEY` para todas as requisições.

### `redis_connection.py`
- Singleton com reconexão automática e serialização com `pickle`.
- TTL de 30 dias.
- Métodos: `save_input`, `save_output`, `get_payload`.

### `mylog.py`
- Sistema de log com GMT-3, console com cores (`colorlog`) e arquivo rotativo.
- Cria a pasta de log automaticamente.
- Detecta se está rodando em Docker para decidir se usa `/log` ou `./log`.

### `test_api.py`
- Script de teste com a biblioteca `requests`.
- Usa `.env` para carregar `API_KEY`, `UUID`, etc.
- Testa os três endpoints principais.

### `sample.txt`
- Contém exemplos de uso com `curl` e instruções de export de variáveis.

### `requirements.txt`
- Lista de dependências:
    - `tornado`, `redis`, `requests`, `python-dotenv`, `nuitka`, `colorlog`

### `compile.sh`
- Compila `app.py` usando **Nuitka** em modo `--onefile`.
- Move o binário final para `bin/app_server`.
- Limpa todos os diretórios temporários: `.build`, `.dist`, `.onefile-build`.

### `docker-compose.yml`
- Cria o serviço `save-matches-uuid`
- Carrega variáveis do `.env` (não incluído).
- Se conecta à rede Docker `minha-rede` (externa).
- Expõe a porta `8890`.

### `Dockerfile`
- Deve ser complementado com a instalação de dependências (`requirements.txt`).
- Inicia o servidor com `python app.py`.

### `Makefile`
- Alvo padrão: deve ser ajustado conforme desejado (build/test/run).

## 🔐 Segurança

Todas as rotas exigem um cabeçalho `X-API-KEY` compatível com `API_SECRET_KEY` definida como variável de ambiente:

```bash
export API_SECRET_KEY="sua-chave-aqui"
```

Exemplo de chamada:
```bash
curl -X GET "http://localhost:8890/get_payload?uuid=abc123" \
     -H "X-API-KEY: sua-chave-aqui"
```

## 🗂️ Uso do arquivo `.env`

Em ambientes Docker ou desenvolvimento local, você pode centralizar todas as variáveis de ambiente em um arquivo `.env` na raiz do projeto.

Exemplo de variáveis que devem ser definidas no `.env` (não incluímos aqui por segurança):
- `REDIS_SERVER`
- `REDIS_PORT`
- `REDIS_PASSWORD`
- `API_SECRET_KEY`

O `docker-compose.yml` já carrega automaticamente essas variáveis.

Para usar manualmente com o binário, você pode carregar o `.env` com ferramentas como `dotenv`, `direnv`, ou usando `export` direto no terminal.

## 🪵 Logs

O sistema de logs utiliza dois destinos:

- **Console com cores** (útil para desenvolvimento)
- **Arquivo rotativo** em: `log/server.log` (ou `/log/server.log` no Docker)

A lógica de definição do caminho de log é inteligente e cobre os seguintes cenários:

| Ambiente        | Caminho utilizado       |
|-----------------|--------------------------|
| Docker          | `/log/server.log`        |
| Local (sem exportar nada) | `./log/server.log`        |
| Com variável de ambiente | `LOG_FOLDER=/caminho`      |

O arquivo `mylog.py` cria automaticamente o diretório se necessário, então não é preciso se preocupar com permissões em ambientes locais.

Você pode visualizar os logs em tempo real com:

```bash
tail -f log/server.log
```

Ou no Docker (caso montado):

```bash
docker exec -it seu_container tail -f /log/server.log
```

## 🚀 Compilação com Nuitka

Use o script `compile.sh`:

```bash
./compile.sh
```

Após isso, o binário estará disponível em:

```bash
./bin/app_server
```

## 🧪 Execução manual do binário

```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=sua_senha
export API_SECRET_KEY=sua_chave

./bin/app_server
```

## 🧪 Exemplos de uso com `curl`

```bash
curl -X POST "http://localhost:8890/save_input?uuid=abc123" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: $API_SECRET_KEY" \
  -d '{"usuario": "Maria", "valor": 120}'

curl -X POST "http://localhost:8890/save_output?uuid=abc123" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: $API_SECRET_KEY" \
  -d '{"status": "ok", "tempo": 3.2}'

curl "http://localhost:8890/get_payload?uuid=abc123" \
  -H "X-API-KEY: $API_SECRET_KEY"
```

## ✅ Observações finais

- As variáveis de ambiente são obrigatórias para funcionamento local ou compilado.
- O Redis precisa estar acessível no host/porta definidos.

@cleytonpedroza
