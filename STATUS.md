# STATUS (atualizado em 23/10/2026, fim do dia)

**Projeto:** análise do discurso de entrevistas com profissionais sobre o uso de IA generativa no trabalho e no dia a dia (tema *extended mind and self*). Os arquivos se chamam "PhD Paper 1 Entrevista …". As entrevistas foram conduzidas por Eduardo Madella (rótulo `eduardo.madella` nas transcrições). Autores e prazo: a definir. Meta: periódico Q1 ou Q2. A direção proposta está em "Direção do artigo", abaixo. Fonte: pasta do Drive `COPPEAD/Papers/extended-mind-and-self` (10 .docx e 1 .pdf, lidos em 23/10). Repositório privado: https://github.com/aladaf/extended-mind-and-self (`data/` fora do git).

**Resumo do dia 23/10:**
1. A base local foi montada a partir do Drive.
2. Vieram as análises de vocabulário: rede semântica, pegada do self e palavras que distinguem coisa de alguém.
3. As 656 menções à IA foram codificadas como coisa ou alguém, com a linha do tempo da oscilação.
4. Testamos se a oscilação aparece só pelas palavras (discriminante) ou pela sintaxe (rede relacional): a resposta foi pouco e em parte.
5. Por fim, discutimos a contribuição e a amostra.

A conclusão foi propor como eixo do artigo a IA como extensão do self que responde, com a autoria como o lugar onde se decide se ela é coisa ou alguém.

## Estado

- **Base local montada em 23/10** (`data/`, fora do git; ver "A base" abaixo). Todo o texto das falas dos .docx entrou na base. A diferença de palavras entre o .docx e a base é exatamente o cabeçalho de cada arquivo.
- **Corpus principal: 8 entrevistas, cerca de 64 mil palavras**, das quais 51 mil são falas dos entrevistados. Todas foram conduzidas por Eduardo e têm o falante de cada turno marcado.
- **Ben-Hur fica em separado** (decisão de 23/10). A entrevista continua na base, mas fica fora do corpus principal (ver item 2 abaixo).
- O PDF da pasta é literatura, não corpus: Epp e Humphreys (2025), *Collaborating with Generative AI in Consumer Culture Research*, *Journal of Consumer Research* 52(1), doi 10.1093/jcr/ucaf014. O texto está em `data/referencias/epp-humphreys-2025.txt`, fora da base.

| id | data no cabeçalho | min | turnos | palavras | do entrevistado | observação |
|----|-------------------|----:|-------:|---------:|----------------:|------------|
| ben-hur | 18/12/2025 | 20 | 98 | 5.579 | ? | **em separado**; sem rótulo de falante; gravada em 16/12/2025 |
| benesson | 29/01/2026 | 43 | 91 | 5.285 | 4.099 | |
| emanuele | 23/02/2026 | 39 | 144 | 6.859 | 4.390 | |
| fernanda | 26/01/2026 | 50 | 83 | 8.122 | 6.641 | gravação começa no meio da conversa |
| isabela | 23/02/2026 | 57 | 89 | 10.600 | 8.781 | |
| leticia | 23/02/2026 | 40 | 103 | 6.811 | 4.716 | |
| lucas | 02/02/2026 | 38 | 81 | 5.064 | 3.767 | há uma segunda transcrição (ver abaixo) |
| mafe | 23/02/2026 | 48 | 59 | 7.930 | 6.527 | gravação começa no meio da conversa |
| rodrigo | 29/01/2026 | 86 | 72 | 13.333 | 12.060 | gravada em 23/01/2026 |

## O que a leitura dos arquivos mostrou (23/10)

1. **O arquivo "PhD Paper 1 Entrevista Rodrigo [sobrenome].docx" é a entrevista de Lucas**, não a de um Rodrigo. O cabeçalho traz o nome e a idade de Lucas, o entrevistador o chama de Lucas, e o conteúdo é o mesmo de "Entrevista Lucas.docx": disclaimer, idade e a mesma mudança de emprego. É uma segunda transcrição, feita com outra ferramenta (segmentos de legenda, sem falante). Está na base como `lucas-legenda`, com `principal = 0`, e fica fora da análise. A entrevista de Rodrigo (`rodrigo`, 86 min) é de outra pessoa.
2. **Ben-Hur não tem rótulo de falante.** Os 98 turnos estão com `papel` nulo. A alternância de falantes não resolve: a primeira e a última fala são do entrevistador, e com 98 turnos a alternância daria a última ao entrevistado. O arquivo também tem outra origem (gravação do Zoom "GMT20251216-235038_Recording"), é mais curto (20 min) e não identifica o entrevistador. **Decisão de 23/10:** Ben-Hur será tratado em separado e está na base com `principal = 0`.
3. **A data do cabeçalho não é a data da entrevista.** Quatro cabeçalhos marcam 23/02/2026 entre 14h55 e 15h07, mas as gravações duram de 39 a 57 min. O cabeçalho de Lucas diz 02/02/2026, e a outra transcrição dele foi criada em 23/01/2026. Rodrigo diz "hoje, Rodrigo, 23/01" aos 53:55, e o cabeçalho dele marca 29/01. Provavelmente é a data de exportação. Só duas datas são conhecidas pela própria fala: Ben-Hur (16/12/2025) e Rodrigo (23/01/2026). O ano do cabeçalho foi inferido pelo dia da semana.
4. **Na entrevista da Mafe, um turno está rotulado "Speaker 3"** (24:06). É uma pergunta do entrevistador e foi marcado como tal.
5. **O consentimento lido na gravação aparece em 6 dos 9 entrevistados.** Não aparece em Ben-Hur, Fernanda e Mafe. As de Fernanda e Mafe começam no meio da conversa. Pode ter sido pedido antes de gravar; vale confirmar com o Eduardo.
6. **O texto está como a transcrição automática o deixou.** Há pontos sem espaço ("Tá.É"), erros de reconhecimento ("head user", "earledoppet" por *early adopter*) e grafias divergentes ("Benerson" na fala, "Benesson" no rótulo). Nada foi corrigido na base.
7. **Há dados pessoais**: nomes reais e empregadores. Por isso `data/` está no `.gitignore`, e as tabelas que trazem nomes ou empresas ficam lá. No git ficam só os primeiros nomes: nos identificadores das frases (`codificacao/`) e nas citações deste STATUS. Os pseudônimos ainda não foram atribuídos.

## A base (`data/`, fora do git)

- `entrevistas.db` (SQLite):
  - `transcricoes`: uma linha por arquivo, com formato, cabeçalho, contagens e observações.
  - `turnos`: uma linha por fala, com rótulo original, `papel` (entrevistador, entrevistado ou nulo), início em segundos e texto.
  - `turnos_fts`: busca textual que ignora acentos.
  - `turnos_analise`: visão só com as 8 entrevistas do corpus principal.
- `turnos.csv`: os mesmos turnos, para abrir no Excel ou no R.
- `transcricoes/<id>.md`: transcrições limpas para leitura, com tempo e falante.
- `referencias/epp-humphreys-2025.txt`: texto do artigo de Epp e Humphreys, só para consulta.

Os rótulos de falante foram conferidos em 23/10. As 8 falas mais longas atribuídas ao entrevistador são de fato dele: explicações da pesquisa, casos próprios e trechos em que chama o entrevistado pelo nome. Quando o nome do entrevistado aparece numa fala atribuída a ele, é porque ele está citando alguém que se dirige a ele. O filtro `papel = 'entrevistado'` serve para isolar as falas dos entrevistados.

Consultas de exemplo:

```sql
-- só as falas dos entrevistados, em ordem
SELECT participante, ordem, inicio_seg, texto FROM turnos_analise WHERE papel = 'entrevistado' ORDER BY participante, ordem;

-- falas de entrevistados que mencionam dependência (com ou sem acento)
SELECT participante, inicio_seg, texto FROM turnos_analise
WHERE papel = 'entrevistado' AND id IN (SELECT rowid FROM turnos_fts WHERE turnos_fts MATCH 'dependencia OR dependente');
```

## Rede semântica (23/10)

`python scripts/rede_semantica.py` gera `figuras/rede_semantica.png` e, para conferência, os CSVs de nós e arestas e um `.gexf` com o grafo completo (abre no Gephi). A figura usa as 50 palavras mais frequentes nas falas dos entrevistados do corpus principal (2.580 frases com ao menos uma palavra).

- **Palavras:** lemas do spaCy (`pt_core_news_sm`, instalado em 23/10), só substantivos, nomes próprios, verbos e adjetivos.
  - Ficam de fora verbos auxiliares, marcadores da fala ("acho que", "sei lá", "a gente", "tipo", "cara", "hum"), substantivos genéricos e unidades de tempo. A lista comentada está em `scripts/stopwords_rede.txt`.
  - "IA", "AI" e "inteligência artificial" viram IA; o "ia" minúsculo é o verbo ir. "uso" foi juntado com "usar", e alguns erros do lematizador foram corrigidos à mão (`UNIR` no script).
  - **Verbos (corrigido em 23/10, à tarde):** o spaCy erra a 1ª pessoa dos irregulares ("entendo" → "enter", "peço" → "peçar", "vejo" e "fiz" ficam como estão). Agora vale o lema do spaCy só quando ele é um infinitivo reconhecido pelo `simplemma` (instalado em 23/10); nos demais casos vale o do `simplemma`. Isso trocou 741 dos 7.929 verbos, quase todos em 1ª pessoa. Sem a correção, a análise do self teria associações falsas com a fala sobre si.
  - **A correção mudou a figura:** Gemini saiu do top 50, entrou "escrever", e as comunidades passaram de 6 para 8. **A cópia no Drive (`rede_semantica.png`) é a versão anterior.**
- **Ligações:** duas palavras se ligam quando aparecem na mesma frase. O peso é o índice de Jaccard, e a figura mostra a árvore máxima, como na análise de similitude do IRaMuTeQ.
  - Com a contagem bruta (`--indice coocorrencia`), a árvore vira duas estrelas em torno de "usar" e "IA", e por isso o Jaccard ficou como padrão.
  - As comunidades são calculadas na própria árvore (Louvain, semente fixa; o layout também é reprodutível).
- **Resultado:** 8 comunidades.
  - (1) usar, IA, pessoa, trabalho, ferramenta, ChatGPT
  - (2) precisar, empresa, criar, grande, tempo, trabalhar, pegar, agente
  - (3) querer, entender, tentar, pedir, gostar, botar, chegar, testar
  - (4) colocar, trazer, ideia, novo, resultado, resposta, perguntar
  - (5) dia, ajudar, pensar, escrever, negócio
  - (6) informação, mercado, dado, área, entrar, produto, análise
  - (7) mundo, acontecer, equipe, profissional, pessoal
  - (8) texto, prompt, imagem, mandar
- **Cautela:** cada ligação da árvore se apoia em poucas frases (mediana de 5; 11 das 49 ligações em só 2 ou 3 frases). A periferia é frágil. Antes de interpretar uma ligação, vale ler as frases em que as duas palavras aparecem.

## Pegada do self (23/10)

`python scripts/self_footprint.py` gera duas figuras:

- `figuras/self_pegada_rede_total.png`: a rede total, colorida pela associação com a fala de self.
- `figuras/self_vizinhanca.png`: os termos do dicionário e as palavras associadas a eles.

O script também grava as tabelas `figuras/self_*.csv`. Ficam fora do git, em `data/`, as frases marcadas (`self_frases.csv`) e a tabela por participante (`self_participantes.csv`). O dicionário e a literatura que o sustenta estão em `dicionarios/` (`self_identidade.csv` e `README.md`).

- **Não há dicionário validado de self ou identidade.** O mais próximo é a categoria de pronomes de 1ª pessoa do LIWC (BP-LIWC2015). O nosso combina:
  - LIWC;
  - autodefinição: "Quem sou eu?" (Kuhn e McPartland) e *identity talk* (Snow e Anderson);
  - agência e autoria (Gallagher, 2000);
  - self e mente estendidos (Belk; Clark e Chalmers; Gallagher, 2013);
  - vocabulário do self (Oyserman et al.; Leary e Tangney).
- **A fala explícita de self é rara:** 129 das 3.144 frases (4,1%) têm um termo-semente. Os mais frequentes:
  - "sou" (63 frases, 8 pessoas);
  - "autoria" (24);
  - "é meu" (15);
  - "na minha cabeça/mente" (8);
  - "me sinto" (7).

  "Identidade" aparece uma vez (Mafe), e "self" nenhuma. Os pronomes de 1ª pessoa estão em 45% das frases e ficaram só como medida.
- **Elicitação:** 51 das 129 frases respondem a uma pergunta da mesma categoria. Isso vale para 20 das 24 frases com "autoria" e para 12 das 15 com "é meu". Nas de "sou", só 13 das 63 foram elicitadas. Em Rodrigo, 17 das 20 frases de self são elicitadas.
- **Vizinhança (G² ≥ 3,84; ≥ 3 ocorrências; ≥ 2 pessoas):** 8 palavras.
  - Robustas, porque continuam significativas só com as frases espontâneas:
    - "avaliação" (avaliação de desempenho e autoavaliação);
    - "direto" ("sou da linha do prompt direto", "sou mais direta e franca");
    - "fato";
    - "responsável".
  - Ligadas à pergunta sobre autoria: "pedir", "ideia", "prompt" e "responsabilidade" ("o resultado é meu, porque quem colocou o prompt e pediu fui eu").
- **Pegada na rede total:** 4 das 50 palavras são mais frequentes na fala de self (pedir, ideia, prompt, ChatGPT). Outras 5 são menos frequentes: usar, empresa, agente, área e informação. A fala sobre si se afasta do vocabulário da empresa e do uso.
- **Opção não usada:** com `--janela 1`, que soma a frase anterior e a seguinte no mesmo turno, a vizinhança vai a 23 palavras (responsabilidade, direto, usuária, output, humano, explorar…). Ela também passa a trazer palavras genéricas ("IA", "ferramenta").

## Coisa ou alguém: oscilação no enquadramento da IA (23/10)

`python scripts/ia_enquadramento.py extrair | analisar | amostra`. O livro de códigos está em `codificacao/livro_de_codigos_ia.md` e os códigos em `codificacao/ia_enquadramento.csv`; os dois ficam no git, mas os códigos não trazem o texto das falas. As frases, a figura e as tabelas, que têm nomes, ficam em `data/`, fora do git.

- **Unidade:** a frase do entrevistado que menciona a IA ou se refere a ela por pronome. São 656 frases.
  - A extração perde frases fortes sem termo nem pronome, como "é parceiro de raciocínio". Por isso a medida é conservadora.
  - Em português, "ele" e "ela" para a IA são obrigatórios pela concordância e não indicam antropomorfização.
- **Códigos (Claude, uma leitura, ainda não validada):** instrumento 404, agente 107, interlocutor 40, negação explícita 27, neutro 54, não é IA 24. Os polos são **coisa** (instrumento, negação) e **alguém** (agente, interlocutor).
- **O fenômeno existe:** os 8 entrevistados usam os dois polos. Das 550 frases em voz própria, 141 (26%) tratam a IA como alguém.
  - Os pares mais próximos entre negar e personificar estão a 2 a 16 segundos em 6 dos 7 que fazem negações explícitas; em Benesson, a 97 segundos.
  - Emanuele: "é uma máquina trabalhando pra gente" e, 2 segundos depois, "que eles não me escutem quando tiver a revolta das máquinas".
  - Mafe: "o grande perigo da IA é essa humanização" e, 7 segundos depois, "ChatGPT, eu posso comer tal coisa?".
  - Fernanda: "é uma máquina que precisa de direcionamento" e, 7 segundos depois, "é mais fácil… do que de um júnior ou de um estagiário".
- **Mistura ou fases?** No conjunto, há menos trocas de polo do que numa ordem aleatória (160 contra 202 esperadas; permutação, p < 0,001). Por entrevistado, o quadro muda:
  - Isabela (24 contra 50) e Rodrigo (17 contra 23; p = 0,016) concentram a fala de "alguém" em episódios: Isabela no bloco sobre a personalidade do GPT e no "sonho" de ter agentes trabalhando para ela; Rodrigo entre os minutos 57 e 74, quando fala de autoria e do futuro.
  - Nos outros 6, os dois polos se misturam ao longo da entrevista no ritmo de uma ordem aleatória.
  - A sequência só de negações e "alguém" também não forma fases (34 contra 39; p = 0,12). Negar e personificar se intercalam.
  - Sem as expressões convencionais ("me ajuda", "junto com a IA"), o resultado se mantém (142 contra 184).
- **Elicitação:** só 38 das 141 frases de "alguém" (27%) vêm até 5 minutos depois de uma pergunta do roteiro sobre trato ou personalidade. Benesson não teve esse bloco.
- **Achados laterais:**
  - Fernanda, sobre self estendido: "vira, sei lá, o meu eu externo, o meu eu máquina" (24:36). O dicionário de self não pega essa forma; vale incluir.
  - Lucas: "a IA tá mais disponível do que qualquer ser humano", que lembra o critério de disponibilidade de Clark e Chalmers.
  - Fernanda diz que responsabilidade é um tema que discutiu "muito com o André Fonseca", e Isabela também cita o André. Vários entrevistados cursaram a ênfase em IA do MBA da Coppead. É um ponto de reflexividade para o método.
- **Para validar:** `data/ia_validacao_amostra.csv` tem 60 frases estratificadas pelo código, com o código em branco, para uma segunda codificação às cegas. A concordância (kappa) se calcula depois contra `codificacao/ia_enquadramento.csv`.
- **Palavras que distinguem os polos** (`ia_enquadramento.py palavras`; `figuras/ia_coisa_alguem_palavras.png`; a tabela completa fica em `data/` porque traz nomes de empresas): log-odds ponderado com prior informativo do corpus inteiro (Monroe, Colaresi e Quinn, 2008), comparando as 141 frases de "alguém" com as 409 de "coisa". Entram só palavras usadas por ao menos 3 entrevistados no polo. O resultado é estável com prior entre 500 e 2000.
  - Alguém (a fala é narrativa, em primeira pessoa e relacional):
    - *me, mim, minha*: a IA age sobre o falante;
    - *ele, falou*: a IA tem voz;
    - *acho, sei*: a posição de quem fala;
    - *era, há*: a IA tem história ("antes ele era amigável", "uso há bastante tempo, ele já tá afinado");
    - *pouco, vezes*: o comportamento dela vem com ressalva ("às vezes tira um pouco dos vieses", "muitas vezes assume verdades").
  - Coisa (a fala é de finalidade e de organização): *pra* ("usar pra…"), *uso, usar, usando*, *tem* ("a gente tem o Copilot"), *já*, *no* ("no Gemini") e os produtos corporativos (*Copilot, Gemini*, *empresa*). Também *agente*: os agentes de IA são falados como peças técnicas.
  - Cautelas:
    - *usar*, *uso* e *falou* foram pistas da codificação e saem hachuradas no gráfico.
    - *onde* vem em parte da pergunta do roteiro "onde termina o seu pensamento e começa o da IA?".
    - Com `--unidade lema` (só lemas de conteúdo), a separação é mais fraca: *chegar, trabalhar, querer, resposta, pensar* contra *usar, ferramenta, Gemini, Copilot, agente, área*.
- **Análise discriminante com os lemas** (`ia_enquadramento.py discriminante`; `figuras/ia_discriminante_lemas.png`, `figuras/ia_discriminante_resumo.csv`):
  - **Modelo:** LDA de dois grupos, com encolhimento de Ledoit-Wolf e priors iguais.
  - **Preditores:** a presença de cada lema na frase, só lemas com pelo menos 5 frases e 3 entrevistados (131 no total).
  - **Avaliação:** fora da amostra, com validação cruzada em 10 partes e também deixando cada entrevistado de fora. O acaso é 50%.
  - **Todos os lemas:** acertam 65% em média por grupo (63% com o entrevistado fora).
    - Alguém classificado como alguém: 88 de 141 (62%).
    - Coisa classificada como coisa: 278 de 409 (68%).
  - **Sem as pistas da codificação:** 57% (54% com o entrevistado fora), quase o acaso.
  - **Palavras como ditas, sem as pistas:** 60% (57%).
  - Todos os modelos ficam acima do acaso (1.000 permutações, p < 0,01), mas com folga pequena.
  - Cargas para alguém: *resposta, gostar, chegar, trabalhar, Claude, trazer, final, lembrar*. Para coisa: *usar, ferramenta, Copilot, Gemini, colocar, dado, área, fácil*.
  - **Conclusão:** palavras soltas mal separam os dois enquadramentos. A diferença está na construção da frase, isto é, em quem é o sujeito do verbo e quem recebe a ação. As frases são curtas (mediana de 3 lemas do modelo) e 42 delas não têm nenhum lema informativo além de "IA". Por isso dicionários e contagens não captam a oscilação, e a codificação por leitura é necessária. É também um argumento de método para o artigo.

## Rede relacional "quem faz o quê a quem" (23/10, versão para crítica)

`python scripts/rede_relacional.py` gera `figuras/ia_rede_relacional.png` e `figuras/ia_rede_relacional_arestas.csv`; as triplas com as frases ficam em `data/ia_triplas.csv`. Instalei o modelo médio do spaCy (`pt_core_news_md`), que analisa a sintaxe melhor que o pequeno.

- **Método:** gramática semântica sujeito–ação–objeto (Franzosi, 2010), tirada da sintaxe das 656 menções e sem usar a codificação manual.
  - Atores: *eu* (eu, me, mim, a gente e o sujeito oculto de 1ª pessoa) e *IA* (o termo ou o pronome que se refere a ela).
  - O papel da IA vem da preposição: pra/pro = destinatário; na/no = recipiente; "com" = parceria só com "junto" ou verbo de troca, senão instrumento.
  - A negação e a cópula ("a IA não é X") são marcadas.
- **Resultado:** 627 triplas em 466 frases.
  - eu → IA: 285 (*usar, ter, fazer, criar, colocar*).
  - eu → IA com pra/pro: 49 (*pedir, perguntar, dar, falar*).
  - eu com a IA: 6 (*conversar*).
  - IA → eu: 20 (*ajudar, trazer*).
  - IA age: 224 (*fazer, ter, trazer, falar, dar, conseguir*).
  - IA é: 43.
- **Concordância com a codificação manual (polos):** 66%, kappa 0,26.
  - A maior divergência são os verbos operacionais com a IA como sujeito ("a IA faz a leitura", "o Copilot dá insights"): a sintaxe diz "IA age", a minha leitura disse "instrumento".
  - Tratando esses verbos como coisa, a concordância sobe para 73% (kappa 0,31), mas a rede passa a perder mais frases de "alguém".
  - 156 frases não geram tripla (124 de coisa, 32 de alguém).
- **Questões para a crítica:**
  - Agência gramatical já é personificação, na linha de Nass e Moon, ou é só o jeito de o português descrever o que uma ferramenta produz ("a máquina lava a roupa")?
  - "Pedir pra IA" é comando ou interpelação?
  - A rede só liga eu e IA: terceiros que agem sobre a IA ficam de fora.

## Direção do artigo (discussão de 23/10)

- **Status e ocultação, descartados como eixo.** A ideia era que saber IA dá status e usar IA se esconde. Os dados a refinam: o que se esconde são os rastros da IA.
  - Os entrevistados declaram transparência ("não vejo motivo pra esconder", "declaro abertamente", "é meu dever informar").
  - Estigmatizam a "cara de IA" nos outros ("travessão", "sem revisão", "pejorativo", "humilhante").
  - O bom uso fica nos bastidores (Lucas: a IA "no backstage").
  - Fernanda resume o duplo vínculo: não usar é ser "dinossauro"; parecer feito por IA é ser substituível.

  Não serve de eixo por dois motivos. Já há literatura sobre a penalidade de revelar o uso de IA (Reif, Larrick e Soll, 2025; Schilke e Reimann, 2025). E o roteiro pergunta diretamente sobre "marcador", "declarar" e "omitir". Os dados também não mostram o "cada vez mais": as narrativas de antes e agora apontam para a normalização do uso.
- **Eixo proposto: a IA generativa como extensão do self que responde.** O self estendido (Belk, 1988, 2013) e a mente estendida (Clark e Chalmers, 1998) supõem que a extensão é uma coisa; aqui ela fala, discorda e tem "vieses meus".
  - A extensão aparece explicitamente: "meu eu externo, meu eu máquina", "não sei onde começa o meu e onde começa o da IA", "não trabalho mais sozinha".
  - A oscilação entre coisa e alguém não é descuido: é rápida, intercalada e às vezes vigiada pela própria pessoa.
  - **A autoria é onde se decide o que a IA é.** Nos turnos em que o entrevistado reivindica autoria, posse ou responsabilidade, a negação explícita aparece em 27% das menções. Os outros enquadramentos ficam assim:

    | enquadramento | nos turnos de autoria | forma típica |
    |---|---|---|
    | negação | 27% (7/26) | "é meu porque fiz o prompt… a IA não é uma pessoa… é uma máquina" |
    | agente | 17% | coautoria: "minha autoria junto com a IA", "a IA seria a autora da ideia" |
    | instrumento | 8% | — |
    | interlocutor | 3% | quase some |

    Ou a IA vira coisa e o resultado é do falante, ou vira coautora e o crédito se divide.
- **Contribuições possíveis:**
  - teoria do self estendido: incorporar uma extensão que fala exige despersonalizá-la para reivindicar o resultado;
  - antropomorfização como prática discursiva situada e ligada a uma função, não como traço nem como resposta automática (contra Nass e Moon, 2000; com Epley et al., 2007);
  - autoria com IA: o mecanismo discursivo por trás do "efeito *ghostwriter*" (Draxler et al., 2024);
  - método, como contribuição secundária: negação e personificação usam o mesmo vocabulário, e medidas do inglês (*he/she* × *it*, AnthroScore) não funcionam numa língua com gênero gramatical.

  Concorrente a contrapor: Hoffman e Novak (2018, *JCR*), sobre a agência de objetos inteligentes.
- **Riscos para Q1:**
  - 8 entrevistas homogêneas, de ex-alunos da ênfase em IA da Coppead, alguns ligados ao André; parte do vocabulário ecoa o curso ("o híbrido que a gente fala lá na Coppead");
  - o roteiro elicia autoria e personalidade;
  - a codificação ainda não foi validada;
  - o teste da autoria é pequeno (26 negações).
- **Amostra (recomendação):** manter o núcleo, profissionais do conhecimento que assinam o que produzem. Recrutar 12 a 15 entrevistas novas, fora da ênfase em IA e sem relação com os pesquisadores, numa amostragem teórica com duas dimensões:
  - autoria alta (advogados, jornalistas, pesquisadores, redatores, designers) × autoria baixa (operações, análise);
  - só uso profissional × também uso pessoal.

  Somar 3 ou 4 casos negativos (usuários eventuais ou céticos) e parar na saturação do mecanismo. Ben-Hur, que é jornalista, pode ser o piloto da célula de autoria alta.
- **Roteiro (recomendação):** deixar autoria e personalidade para o fim e pedir a cada participante uma conversa real com a IA, com consentimento específico, para comparar o que a pessoa diz com como se dirige à IA.
- **Periódicos a considerar** (confirmar o quartil vigente): *Journal of Consumer Research* (ambicioso com a amostra atual), *Psychology & Marketing*, *Journal of Business Research*, *New Media & Society*.

## Como reconstruir a base

```bash
python scripts/extrair_base.py            # lê do Drive; outra pasta: EMS_DRIVE=<pasta> ou --drive <pasta>
```

O script apaga e regrava `data/entrevistas.db`, `data/turnos.csv`, `data/transcricoes/` e `data/referencias/`. As correções da seção acima (Lucas, Ben-Hur, Mafe) estão no início do script, em `ARQUIVOS` e `PAPEL_FORCADO`.

## Próximos passos

1. Decidir a direção do artigo (ver acima) e escrever um memorando de uma página: pergunta, posicionamento, contribuições e o que falta coletar.
2. Escrever o protocolo de amostragem (critérios de inclusão, células, casos negativos) e o roteiro revisado, para levar ao Eduardo.
3. Validar a codificação coisa/alguém: segunda codificação às cegas da amostra de 60 frases e kappa.
4. Fortalecer o teste da autoria: relação entre negação, agência e reivindicação de autoria, separando o elicitado do espontâneo.
5. Montar a ficha dos participantes (idade, profissão, organização, nível de uso de IA) e atribuir pseudônimos.
6. Incluir "meu eu externo" e "meu eu máquina" no dicionário de self.
7. Se Ben-Hur entrar (piloto de autoria alta), atribuir os falantes na entrevista dele. É preciso ler os 98 turnos.

## Decisões pendentes (André)

- Direção do artigo: extensão do self que responde, com a autoria como lugar da decisão sobre o que a IA é?
- Ampliar a amostra (12 a 15 entrevistas novas, fora da ênfase em IA)? Pedir conversas reais com a IA?
- Periódico-alvo.
- O arquivo com nome de "Rodrigo" e sobrenome está só com o nome errado, ou falta na pasta uma entrevista de outra pessoa?
- Datas reais das entrevistas e confirmação do consentimento de Ben-Hur, Fernanda e Mafe (com o Eduardo).
- Qual vertente de análise do discurso seguir.
- Dicionário de self:
  - Os pronomes de 1ª pessoa entram como semente?
  - "Personalidade" e "autonomia", que no corpus são atributos da IA, entram como semente?
  - Frase única ou janela de ±1 frase?
  - A análise de vizinhança usa todas as frases de self ou só as espontâneas?
- Codificação coisa/alguém: quem faz a segunda codificação da amostra de 60 frases?

## Registro

- **23/10/2026:** repositório criado. Lidos os 11 arquivos do Drive. Montada a base local (`scripts/extrair_base.py`). STATUS.md criado. Depois, o artigo de Epp e Humphreys saiu da base, por não ser corpus. Ben-Hur passou a ser tratado em separado, e o corpus principal ficou com 8 entrevistas. Primeira rede semântica (`scripts/rede_semantica.py`, `figuras/`). Dicionário de self (`dicionarios/`), pegada e vizinhança do self (`scripts/self_footprint.py`). Correção dos lemas de verbos, que mudou a rede total. Codificação das 656 menções à IA (coisa ou alguém) e linha do tempo da oscilação. Palavras que distinguem os polos (log-odds), análise discriminante com os lemas e rede relacional sujeito–ação–objeto. Discussão de contribuição e amostra (ver "Direção do artigo"). Retirados dos arquivos versionados os identificadores indiretos (sobrenome, empregadores); as tabelas com nomes ou empresas foram para `data/`. Primeiro commit e push para o repositório privado.
