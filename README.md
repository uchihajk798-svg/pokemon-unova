# Pokémon FireRed: Unova Edition

ROM hack experimental do FireRed de GBA, preservando Kanto e trocando o elenco principal por Pokémon de Unova (geração V, #494–649).

**Estado real (2026-10-09):** o código **compila** em GitHub Actions; os 156 Pokémon possuem slots de encontros de FireRed, os três iniciais são Snivy/Tepig/Oshawott e equipes de treinadores foram convertidas. **A campanha não foi testada integralmente em emulador**. Encontros e times ainda precisam de revisão de balanceamento; não se trata de versão final polida. A interface web está pronta para publicação, mas não é um link ativo até que a hospedagem seja habilitada.

## 🎮 GBA Pocket — aplicativo de emulador GBA

**[Abrir GBA Pocket](https://uchihajk798-svg.github.io/pokemon-unova/app/)**

O novo app web progressivo (PWA) executa arquivos `.gba` locais no navegador pelo **EmulatorJS**. Possui controles de toque, biblioteca de jogos no IndexedDB, instalação na tela inicial, modo tela cheia e aplicação de patches `.bps` (SourceRead, TargetRead, SourceCopy e TargetCopy, com checksum CRC32).

**Como usar:** abra o link, selecione sua ROM `.gba`, escolha um patch `.bps` se desejar e clique em **Jogar GBA**. No menu do emulador, use as ferramentas internas de salvar/carregar estados ou saves. A instalação é opcional: Android/Chrome pelo botão Instalar app; iPhone/Safari pelo menu Compartilhar → Adicionar à Tela de Início.

**Limitações:** núcleo EmulatorJS servido por CDN (primeira inicialização depende de conexão). Saves e ROMs guardados no navegador podem desaparecer após limpar dados do site; faça backups de SAV. Não é um APK nativo, e o app não fornece jogos comerciais ou BIOS. Os arquivos selecionados não são enviados pelo código do app.

Código em `docs/app/`; testes automatizados em `tests/test_patch.mjs` e `.github/workflows/gba-pocket.yml`.

## Baixar o patch BPS (sem ROM)

1. Abra [Actions](https://github.com/uchihajk798-svg/pokemon-unova/actions).
2. Escolha uma execução **verde** de **Construir patch Pokémon Unova**.
3. Na seção **Artifacts**, baixe **pokemon-unova-bps** e extraia o arquivo `pokemon-unova.bps`.
4. O ZIP inclui `base-sha256.txt`, com o checksum SHA256 da versão limpa da ROM de referência. **Atenção:** este BPS usa uma ROM produzida a partir de `pokefirered-expansion` como base; não pode ser aplicado diretamente a uma ROM comercial normal de FireRed. Compile a ROM limpa correspondente, mantendo a revisão fixada abaixo.
5. Use `web/index.html` ou `docs/index.html` no navegador para aplicar o patch à base compilada e executar com EmulatorJS, ou aplique o patch com `tools/bps.py` e abra o arquivo resultante no **mGBA**.

Um dos artefatos com distribuição de 156 espécies e build aprovado: [execução 37940249413](https://github.com/uchihajk798-svg/pokemon-unova/actions/runs/37940249413) (7 dias de retenção por padrão; use a execução verde mais recente depois disso).

## Compilação reproduzível sem pagar

Para gerar a versão limpa de referência da expansão:

```bash
git clone https://github.com/Faceplantfloor/pokefirered-expansion.git firered-base
git -C firered-base checkout a2bb3bd82d43e636f5d78090682afdb756257bd5
git clone https://github.com/uchihajk798-svg/pokemon-unova.git unova
```

Instale o toolchain de GBA e o compilador `agbcc` conforme o arquivo [INSTALL](https://github.com/Faceplantfloor/pokefirered-expansion/blob/master/INSTALL.md). No Ubuntu, as dependências usadas na nossa CI são `build-essential binutils-arm-none-eabi gcc-arm-none-eabi libnewlib-arm-none-eabi libpng-dev`; o `agbcc` é compilado e instalado no projeto seguindo suas instruções.

```bash
make -C firered-base -j2
cp firered-base/pokefirered.gba firered-original.gba

# Aplica iniciais, diálogos, treinadores, encontros, eventos estáticos e evoluções por Linking Cord.
python3 unova/tools/apply_unova.py --game-dir firered-base
python3 unova/tools/validate_unova.py --game-dir firered-base
make -C firered-base -j2

# Cria patch diferencial local (NÃO envie arquivos .gba para o GitHub)
python3 unova/tools/bps.py create --base firered-original.gba --modified firered-base/pokefirered.gba --output pokemon-unova.bps
python3 unova/tools/bps.py verify --base firered-original.gba --patch pokemon-unova.bps
```

A base e as ferramentas upstream podem mudar. A CI utiliza código de expansão fixado em `a2bb3bd82d43e636f5d78090682afdb756257bd5`; confira o SHA publicado no pacote de patch para verificar compatibilidade exata.

## Arquivos

- `data/unova_species.json`: 156 espécies nacionais #494–649.
- `data/unova_habitats.json`: tipagens, estágios e habitats propostos.
- `tools/apply_unova.py`: substituições de encontros, treinadores e scripts.
- `tools/complete_encounters.py`: cobertura dos 156 Pokémon com encontros raros.
- `tools/validate_unova.py`: garante zero Pokémon de outras gerações em equipes/encounters e cobertura total em FireRed.
- `tools/bps.py`: cria/verifica patch BPS.
- `web/index.html`, `docs/index.html`: aplicador local com emulador GBA, sem ROM hospedada.
- `.github/workflows/tests.yml`: compilação, testes e artefato BPS gratuitos.

## Versão web grátis

Os arquivos para o site estão em `docs/index.html`, adequados ao **GitHub Pages**. Para publicar: GitHub → Settings → Pages → Source: Deploy from a branch → `main` → `/docs` → Save. A publicação depende dessa configuração no repositório, e o conteúdo **não inclui ROM**. Normalmente o endereço segue `https://uchihajk798-svg.github.io/pokemon-unova/`, mas verifique o link real no painel **Pages** antes de compartilhá-lo.

## O que falta antes de chamar de jogo 100% completo

Testar de ponta a ponta em **mGBA** a tela inicial, criação de save, primeiro encontro, capturas, oito ginásios, Team Rocket, Elite Four, Sevii e pós-jogo. Fazer auditoria de distribuição dos 156, eventos raros, movimentos e TMs/HMs; harmonizar Pokédex regional, todas as falas remanescentes e equilibrar treinadores/rotas. Consulte [docs/ROADMAP.md](docs/ROADMAP.md).

## Direitos autorais

É um projeto de fã não oficial, sem vínculo com Nintendo, Game Freak e The Pokémon Company. Não distribua ROMs comerciais, apenas código e patches diferenciais, observando os direitos/licenças dos recursos. Para criar a ROM final é necessário possuir os arquivos de origem necessários e compatíveis.
