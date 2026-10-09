# Pokémon FireRed: Unova Edition

> **Estado atual: protótipo de ferramentas de ROM hack — ainda NÃO é uma ROM jogável.**

Projeto de fã que pretende preservar a campanha de **Pokémon FireRed** em Kanto,
substituindo o elenco por **156 espécies originalmente introduzidas em Unova (números nacionais 494–649)**.

## O que já existe

- Catálogo verificável das 156 espécies de Unova (`data/unova_species.json`).
- Ferramenta de aplicação de substituições em uma cópia local de [pokefirered-expansion](https://github.com/Faceplantfloor/pokefirered-expansion).
- Conversão inicial dos três Pokémon de laboratório, encontros selvagens e equipes de treinadores.
- Testes automatizados da ferramenta (sem necessidade de ROM).

**Ainda falta:** integração completa das espécies aos menus e Pokédex regional,
revisão individual de cada equipe e rota, reescrita dos eventos estáticos,
evoluções especiais, testes em mGBA, build validada, patch BPS e hospedagem web.

## Como começar sem pagar

Requisitos: Python 3.10+, Git e ferramentas de compilação descritas no [INSTALL da base](https://github.com/Faceplantfloor/pokefirered-expansion/blob/master/INSTALL.md).

```bash
git clone https://github.com/Faceplantfloor/pokefirered-expansion.git firered-base
git clone https://github.com/uchihajk798-svg/pokemon-unova.git unova
python3 unova/tools/apply_unova.py --game-dir firered-base --dry-run
python3 unova/tools/apply_unova.py --game-dir firered-base
```

A ferramenta cria uma cópia de segurança `.unova-backup` na primeira execução. Ela edita arquivos de dados de uma base existente; **não constrói sozinha um jogo pronto**. Para compilar, siga o guia da base, instale `agbcc` se exigido e rode `make -j2` na pasta `firered-base`. Uma compilação bem-sucedida ainda não substitui testes no emulador.

Verificação local:

```bash
python3 -m unittest discover -s unova/tests -v
```

## Escolhas do projeto

| Original FireRed | Unova Edition |
| --- | --- |
| Bulbasaur → Ivysaur → Venusaur | Snivy → Servine → Serperior |
| Charmander → Charmeleon → Charizard | Tepig → Pignite → Emboar |
| Squirtle → Wartortle → Blastoise | Oshawott → Dewott → Samurott |

A ordem das escolhas do rival é preservada. Nos encontros e treinadores,
a ferramenta usa um mapeamento temático inicial e valores provisórios quando
não há correspondência explícita. **Não considere o balanceamento finalizado.**

## Restrições legais

Não hospedamos ROMs comerciais nem distribuímos arquivos `.gba`. A fonte
decompilada e recursos de terceiros permanecem sujeitos a direitos e licenças
dos respectivos autores. Confira permissões antes de redistribuir qualquer
asset; a entrega pública final deverá priorizar patch diferencial (BPS/UPS).
Pokémon e FireRed pertencem a seus respectivos titulares. Este projeto é
independente e não oficial.

## Próximos passos

Veja [ROADMAP.md](docs/ROADMAP.md). O objetivo de longo prazo é a campanha
inteira — 8 ginásios, Elite Four, Ilhas Sevii e obtenção dos 156 Pokémon.
