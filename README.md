# Bot de Administração Discord com IA

## Como configurar

1. **Crie o bot no Discord:**
   - Acesse https://discord.com/developers/applications
   - Clique em "New Application" → aba "Bot"
   - Clique em "Reset Token" e copie o token
   - Em "Privileged Gateway Intents", ative **Message Content Intent** e **Server Members Intent**

2. **Crie a chave da IA (Google Gemini):**
   - Acesse https://aistudio.google.com/apikey e gere uma chave

3. **Configure o arquivo `.env`:**
   - Renomeie `.env.example` para `.env`
   - Cole seu token e sua chave Gemini

4. **Convide o bot para seu servidor:**
   - No painel do bot, vá em OAuth2 → URL Generator
   - Marque `bot` e `applications.commands`
   - Permissões: Administrator (ou as que quiser)
   - Use o link gerado para convidar

5. **Instale e rode:**
   ```
   pip install -r requirements.txt
   python bot.py
   ```

## Comandos
- `!ask <pergunta>` — conversa com a IA
- Mencione o bot para responder com IA
- `!ban`, `!kick`, `!mute`, `!unmute`, `!clear` — moderação
- `!limparmemoria` — reseta a memória da conversa
- `!ajuda` — lista os comandos
