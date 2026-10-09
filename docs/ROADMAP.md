# Plano de desenvolvimento — Pokémon FireRed: Unova Edition

Este documento separa **código implementado** de **recursos jogáveis comprovados**.

## Etapa 1 — Dados e ferramentas (em andamento)
- [x] Repositório inicializado.
- [x] Catálogo de 156 Pokémon nacionais #494–649 da quinta geração.
- [x] Primeira substituição dos três iniciais no laboratório.
- [x] Substituição programática dos encontros selvagens nas tabelas FireRed/LeafGreen.
- [x] Primeira substituição das espécies dos treinadores (com equivalências provisórias).
- [x] Testes unitários e validação de espécies com GitHub Actions.
- [ ] Revisão artesanal de habitat, taxa, faixa de nível e balanceamento de cada rota.
- [x] Inserir referências das 156 espécies em slots selvagens de FireRed (validação automática aprovada).
- [ ] Confirmar acessibilidade real das 156 espécies, incluindo lendários, durante o jogo e balancear raridade.
- [ ] Ajustar TMs/HMs e movimentos customizados dos treinadores.

## Etapa 2 — Dados do jogo
- [x] Compilação comprovada do código modificado para GBA via GitHub Actions.
- [ ] Inserção e verificação de todos os sprites, ícones, paletas e cries.
- [ ] Pokédex regional de 156 registros funcionais.
- [ ] Evoluções por troca adaptadas para jogar sozinho.
- [ ] Movesets e habilidades com mecânicas da quinta geração verificadas.
- [ ] Eventos e presentes estáticos substituídos por Unova.
- [ ] Revisar textos, NPCs, trocas e scripts fora das três tabelas iniciais.

## Etapa 3 — Campanha completa
- [ ] Pallet Town, escolhas do rival e primeira batalha testadas em emulador.
- [ ] Ginásios 1 a 8 testados manualmente.
- [ ] Team Rocket, Giovanni, Elite Four, campeão e pós-jogo.
- [ ] HM obrigatório sem bloqueios de progressão.
- [ ] Lendários, míticos e eventos especiais nas Ilhas Sevii.
- [ ] Captura, equipe, inventário, PC e save/load.
- [ ] Conferir que nenhuma rota depende de espécie removida.

## Etapa 4 — Distribuição
- [x] Patch BPS gerado, checksum validado e oferecido como artefato temporário em GitHub Actions.
- [x] Tela web local de aplicação do BPS, com confirmação de integridade; teste visual de navegador pendente.
- [x] Integração inicial do EmulatorJS no HTML sem ROM comercial; teste manual pendente.
- [ ] Pacote de documentação, licenças, créditos e instruções.

## Verificações realizadas
- Catálogo: 156 / 156 espécies cadastradas em JSON.
- Primeira integração de dados na base: 4.352 slots de encontros e 1.758 entradas de equipes processadas.
- Verificação de espécies nas duas tabelas: zero referências inválidas detectadas.
- Espécies únicas nos encontros FireRed após distribuição de cobertura: 156/156 (validador automático; não garante que todas as áreas estejam acessíveis).
- O programa de validação **não** comprova equilíbrio, recompensas, compatibilidade de golpes, teste de ROM nem campanha jogável.

**Atenção:** não confunda percentual de ferramentas concluídas com progresso do jogo como um todo. Ainda não existe build final jogável verificada.

## Estado técnico em 2026-10-09
- 12 testes unitários automatizados passaram após ajustes (não incluem gameplay em emulador).
- O script de cobertura verifica 156/156 espécies no conjunto de encontros FireRed.
- Primeiras edições de diálogos do laboratório e alternativas via Linking Cord para evolução por troca.
- Testes integrados da campanha do início ao fim e validação do launcher web continuam pendentes.
