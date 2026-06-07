# Beach Tênis Score Bordon - Code Review & Improvement Task

## Contexto
Aplicação de pontuação de Beach Tênis com:
- Frontend: React + TypeScript + Vite (porta 5175)
- Backend: FastAPI + SQLite (porta 8002)
- Local: /root/tennis-scorer/

## Bugs reportados
1. Ao selecionar jogadores na partida, o dropdown não mostra o jogador selecionado - fica em branco mesmo após selecionar
2. Ao clicar para marcar pontos, cria novas partidas em vez de atualizar a existente

## O que já foi corrigido
- Endpoint PATCH /api/matches/{mid}/players adicionado (estava faltando)
- Campo court_id em MatchCreate tornou-se opcional (era obrigatório)

## Sua tarefa
1. Leia todo o código:
   - /root/tennis-scorer/src/App.tsx
   - /root/tennis-scorer/src/api.ts
   - /root/tennis-scorer/server/main.py
   - /root/tennis-scorer/server/db.py
   - /root/tennis-scorer/src/index.css

2. Identifique bugs no fluxo de seleção de jogadores (modo singles e doubles)

3. Verifique os handlers onChange:
   - Estão passando corretamente os valores atuais de TODOS os jogadores ao atualizar um?
   - O estado atualiza corretamente após loadMatches()?

4. Verifique se o modo doubles (4 selects) funciona corretamente

5. Procure por issues de performance ou qualidade de código

6. Verifique edge cases no scoring (deuce, tiebreak, vitória de set, vitória de partida)

7. Verifique se MatchScreen exibe corretamente doubles (player1/player1b vs player2/player2b)

## Após corrigir
- Rebuild: cd /root/tennis-scorer && npm run build
- Restart backend: cd /root/tennis-scorer && python3 -m uvicorn server.main:app --host 0.0.0.0 --port 8002

## Expectations
- Modo singles: selecionar 2 jogadores
- Modo doubles: selecionar 4 jogadores (2 duplas)
- Dropdown deve mostrar nome do jogador selecionado após seleção
- Botão "Iniciar" só ativa quando todos os jogadores necessários estão selecionados
- Pontuação correta (deuce/advantage, tiebreak, sets, vitória da partida)