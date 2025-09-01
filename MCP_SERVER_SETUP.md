# 🔧 Configuração do MCP Server Optimus no Claude Code

Este documento explica como configurar o MCP Server do projeto Optimus no Claude Code.

## ✅ Configuração que Funciona (Testada em Agosto 2025)

### 🎯 Comando Completo

```bash
# 1. Remover configuração existente (se houver)
claude mcp remove optimus --scope user

# 2. Adicionar o servidor MCP
claude mcp add optimus --scope user \
  --env PYTHONPATH=/home/marcelo/projetos/oraljet/github/optimus_final \
  --env MCP_INDEXER_ENABLED=true \
  -- /home/marcelo/projetos/oraljet/github/optimus_final/ai-engine/venv/bin/python \
  -m mcp_servers.optimus_project_mcp.stdio_server

# 3. Verificar se funcionou
claude mcp list
```

### 📋 Pré-requisitos

1. **Dependências instaladas:**
   ```bash
   source ai-engine/venv/bin/activate
   pip install -r mcp_servers/optimus_project_mcp/requirements.txt
   ```

2. **Estrutura do projeto:**
   ```
   optimus_final/
   ├── ai-engine/venv/          # Ambiente virtual Python
   ├── mcp_servers/
   │   └── optimus_project_mcp/
   │       ├── stdio_server.py  # Servidor MCP stdio
   │       ├── server.py        # Servidor MCP HTTP
   │       └── requirements.txt # Dependências MCP
   └── ...
   ```

## 🌐 Para Usar em Outro Servidor

### 1. **Preparar o Ambiente**

```bash
# No novo servidor, ir para o diretório do projeto
cd /CAMINHO/DO/NOVO/SERVIDOR/optimus_final

# Ativar ambiente virtual e instalar dependências
source ai-engine/venv/bin/activate
pip install -r mcp_servers/optimus_project_mcp/requirements.txt
```

### 2. **Configurar no Claude Code**

```bash
# Substituir os caminhos pelos do novo servidor
claude mcp add optimus --scope user \
  --env PYTHONPATH=/CAMINHO/DO/NOVO/SERVIDOR/optimus_final \
  --env MCP_INDEXER_ENABLED=true \
  -- /CAMINHO/DO/NOVO/SERVIDOR/optimus_final/ai-engine/venv/bin/python \
  -m mcp_servers.optimus_project_mcp.stdio_server
```

### 3. **Verificar Funcionamento**

```bash
# Listar servidores MCP
claude mcp list

# Deve aparecer:
# optimus: /caminho/.../python -m mcp_servers... - ✓ Connected
```

## 🔧 Configurações Disponíveis

### Variáveis de Ambiente

- **`PYTHONPATH`**: Caminho para o projeto Optimus
- **`MCP_INDEXER_ENABLED`**: `true` para ativar auto-indexação
- **`MCP_INDEXER_INTERVAL`**: Intervalo de polling em segundos (padrão: 1.0)

### Scopes de Configuração

- **`--scope user`**: Disponível para todos os projetos do usuário
- **`--scope local`**: Apenas para o projeto atual
- **`--scope project`**: Compartilhado via `.mcp.json` no projeto

## 🛠️ Ferramentas Disponíveis

Após configuração, as seguintes ferramentas MCP estarão disponíveis:

### 📊 Sistema e Visão Geral
- **`system_overview`**: Visão completa do sistema Optimus
- **`service_contract`**: Contratos dos microserviços
- **`env_matrix`**: Matriz de variáveis de ambiente
- **`service_urls`**: URLs base dos serviços

### 🔍 Busca e Arquivos
- **`search`**: Busca no código do projeto
- **`open_file`**: Abrir arquivos do projeto
- **`refresh`**: Reindexar documentação

### 🏗️ Arquitetura e Validação
- **`plan_change`**: Orientações arquitetônicas para mudanças
- **`validate_diff`**: Validar diffs contra guardrails

### 📝 Prompts e Templates
- **`prompts_list`**: Listar templates de prompts
- **`prompts_get`**: Obter template específico
- **`prompts_apply`**: Aplicar template com variáveis

## 🚨 Solução de Problemas

### Problema: Servidor não aparece no `/mcp`

**❌ NÃO funciona:** Editar `~/.claude/settings.json` manualmente
**✅ Funciona:** Usar comandos CLI oficiais do Claude Code

### Problema: "Failed to connect"

1. **Verificar dependências:**
   ```bash
   source ai-engine/venv/bin/activate
   python -c "import mcp_servers.optimus_project_mcp.stdio_server"
   ```

2. **Verificar caminhos:**
   ```bash
   ls -la /caminho/para/ai-engine/venv/bin/python
   ```

3. **Reconfigurar:**
   ```bash
   claude mcp remove optimus --scope user
   # Repetir comando de configuração
   ```

### Problema: "Module not found"

**Causa:** PYTHONPATH não configurado corretamente

**Solução:**
```bash
# Certificar-se que o PYTHONPATH aponta para a raiz do projeto
--env PYTHONPATH=/caminho/completo/para/optimus_final
```

## 📈 Verificação de Funcionamento

### 1. **Status dos Servidores**
```bash
claude mcp list
# Deve mostrar: optimus: ... - ✓ Connected
```

### 2. **Teste no Claude Code**
```
/mcp
# Deve aparecer "optimus" na lista de servidores disponíveis
```

### 3. **Teste de Funcionalidade**
```
# No Claude Code, usar uma ferramenta MCP:
system_overview()
```

## 🎯 Comandos Úteis

```bash
# Ver todos os servidores MCP
claude mcp list

# Remover servidor
claude mcp remove optimus --scope user

# Ver configuração atual
cat ~/.claude.json

# Testar módulo Python
python -c "import mcp_servers.optimus_project_mcp.stdio_server; print('OK')"
```

---

## ✅ Status Final

- **Data da Configuração:** Agosto 2025
- **Versão Claude Code:** Atual
- **Status:** ✅ Funcionando 100%
- **Ferramentas Disponíveis:** 12 ferramentas MCP
- **Performance:** Conexão instantânea

**🎉 Configuração completa e testada com sucesso!**