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
- [ ] Garantir a acessibilidade de todas as 156 espécies (incluindo lendários).
- [ ] Ajustar TMs/HMs e movimentos customizados dos treinadores.

## Etapa 2 — Dados do jogo
- [ ] Compilação comprovada do código modificado para GBA.
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
- [ ] Patch BPS/UPS gerado e validado contra base correta.
- [ ] Tela opcional para aplicar patch a ROM legítima localmente.
- [ ] Emulador no navegador sem publicar ROM comercial.
- [ ] Pacote de documentação, licenças, créditos e instruções.

## Verificações realizadas
- Catálogo: 156 / 156 espécies cadastradas em JSON.
- Primeira integração de dados na base: 4.352 slots de encontros e 1.758 entradas de equipes processadas.
- Verificação de espécies nas duas tabelas: zero referências inválidas detectadas.
- Espécies únicas nestas duas tabelas juntas: 114; ainda não é a promessa de disponibilidade das 156.
- O programa de validação **não** comprova equilíbrio, recompensas, compatibilidade de golpes, teste de ROM nem campanha jogável.

**Atenção:** não confunda percentual de ferramentas concluídas com progresso do jogo como um todo. Ainda não existe build final jogável verificada.
