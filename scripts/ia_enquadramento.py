#!/usr/bin/env python3
"""
Oscilação no enquadramento da IA: como coisa (instrumento, negação explícita) ou como alguém (agente, interlocutor).

  extrair   grava data/ia_mencoes.csv: cada frase dos entrevistados (corpus principal) que menciona a IA, ou que tem
            um pronome logo depois de uma menção, com minuto aproximado e contexto, para codificar à mão.
  analisar  junta as menções aos códigos de codificacao/ia_enquadramento.csv (livro de códigos em
            codificacao/livro_de_codigos_ia.md) e gera a linha do tempo, o teste de alternância e as citações pareadas.
  amostra   grava data/ia_validacao_amostra.csv: 60 frases estratificadas pelo código, sem o código, para uma
            segunda codificação às cegas (a concordância se calcula depois contra codificacao/ia_enquadramento.csv).
  palavras  palavras que discriminam as frases de 'coisa' das de 'alguém': log-odds ponderado com prior informativo
            tirado de todas as falas dos entrevistados (Monroe, Colaresi e Quinn, 2008). Por padrão, todas as palavras
            como foram ditas; com --unidade lema, só lemas de conteúdo. Gera figuras/ia_coisa_alguem_palavras[_lemas]
            .png e a tabela completa em data/ (ela traz nomes de empresas, por isso fica fora do git).
  discriminante  análise discriminante linear de dois grupos (alguém × coisa) com os lemas: matrizes 2×2 fora da
            amostra, teste por permutação, cargas dos lemas e o mesmo modelo sem as pistas da codificação. Gera
            figuras/ia_discriminante_lemas.png e os CSVs figuras/ia_discriminante_*.

O minuto de cada frase é interpolado dentro do turno, pela posição do texto entre o início do turno e o do seguinte.

Uso:
  python scripts/ia_enquadramento.py extrair
  python scripts/ia_enquadramento.py analisar [--permutacoes 10000]
  python scripts/ia_enquadramento.py amostra
  python scripts/ia_enquadramento.py palavras [--prior 1000] [--n 15]
  python scripts/ia_enquadramento.py discriminante
"""
import argparse, csv, math, os, random, re, sqlite3, zlib
from collections import Counter, defaultdict
import spacy
from rede_semantica import preparar

# 'IA' e 'AI' só em maiúsculas: 'ia' é o verbo ir e 'ai' costuma ser 'aí'
SIGLAS_IA = re.compile(r"\b(IA|IAs|AI|AIs)\b")
TERMOS_IA = re.compile(r"\b(chat\s?gpt|gpts?|chatinho|chat|claude|gemini|copilot|perplexity|notebook\s?lm|grok|deepseek|"
                       r"manus|lovable|midjourney|llms?|agentes?|rob[ôo]s?|algoritmos?|m[áa]quinas?|assistentes?)\b", re.I)
PRONOMES = re.compile(r"\b(ele|ela|eles|elas|dele|dela|deles|delas|nele|nela|neles|nelas|lhe|lhes)\b", re.I)
# Perguntas do roteiro sobre tratamento social e personalidade da IA (marcadores na linha do tempo); procuradas só no
# trecho que antecede cada '?', para não contar a cortesia do entrevistador ("explore isso pra mim, por favor"),
# e sem 'obrigado' (o agradecimento ao entrevistado) nem a transição para outro tema ("saindo desse tema de personificação")
PERGUNTA_SOCIAL = re.compile(r"bom dia|por favor|personalidade|antropomorf|antropiz|personific|se dirige|"
                             r"relacionamento com a (ferramenta|IA|m[áa]quina)|mais à vontade", re.I)
TRANSICAO = re.compile(r"desse tema", re.I)

def pergunta_social(texto):
    janelas = (texto[max(0, m.start() - 250):m.start()] for m in re.finditer(r"\?", texto))
    return any(PERGUNTA_SOCIAL.search(j) and not TRANSICAO.search(j) for j in janelas)

def menciona_ia(texto):
    return bool(SIGLAS_IA.search(texto) or TERMOS_IA.search(texto))

def extrair(a):
    nlp = spacy.load("pt_core_news_sm", disable=["ner"])
    turnos = sqlite3.connect(a.db).execute(
        "SELECT transcricao_id, participante, ordem, papel, inicio_seg, texto FROM turnos_analise "
        "ORDER BY transcricao_id, ordem").fetchall()
    fim = {}   # fim de cada turno = início do turno seguinte da mesma entrevista
    for (t1, _, o1, _, _, _), (t2, _, _, _, s2, _) in zip(turnos, turnos[1:]):
        if t1 == t2: fim[(t1, o1)] = s2
    mencoes, perguntas = [], []
    falas = [t for t in turnos if t[3] == "entrevistado"]
    docs = {(t[0], t[2]): d for t, d in zip(falas, nlp.pipe((preparar(t[5]) for t in falas), batch_size=64))}
    ultima_pergunta = {}
    for tid, quem, ordem, papel, inicio, texto in turnos:
        if papel == "entrevistador":
            if "?" in texto: ultima_pergunta[tid] = texto
            if pergunta_social(texto):
                perguntas.append(dict(transcricao_id=tid, participante=quem, ordem=ordem, minuto=round(inicio / 60, 2),
                                      pergunta=texto[-300:]))
            continue
        doc = docs[(tid, ordem)]
        frases = list(doc.sents)
        duracao = fim.get((tid, ordem), inicio + 30) - inicio
        pergunta_com_ia = menciona_ia(ultima_pergunta.get(tid, ""))
        for i, s in enumerate(frases):
            termo = menciona_ia(s.text)
            recente = any(menciona_ia(frases[j].text) for j in range(max(0, i - 2), i)) or (i < 2 and pergunta_com_ia)
            anafora = bool(PRONOMES.search(s.text)) and recente
            if not (termo or anafora): continue
            antes = frases[i - 1].text if i else "[entrevistador] " + ultima_pergunta.get(tid, "")[-250:]
            depois = frases[i + 1].text if i + 1 < len(frases) else ""
            mencoes.append(dict(id=f"{tid}-{ordem:03d}-{i:02d}", participante=quem,
                                minuto=round((inicio + duracao * s.start_char / max(len(doc.text), 1)) / 60, 2),
                                gatilho="termo" if termo else "anáfora", contexto_antes=antes.strip(),
                                frase=s.text.strip(), contexto_depois=depois.strip()))
    for path, linhas in (("data/ia_mencoes.csv", mencoes), ("data/ia_perguntas_sociais.csv", perguntas)):
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(linhas[0])); w.writeheader(); w.writerows(linhas)
    por_pessoa = {}
    for m in mencoes: por_pessoa[m["participante"]] = por_pessoa.get(m["participante"], 0) + 1
    print(f"{len(mencoes)} frases candidatas ({sum(m['gatilho'] == 'anáfora' for m in mencoes)} por anáfora): {por_pessoa}")
    print(f"{len(perguntas)} perguntas do roteiro sobre tratamento social ou personalidade")

POLO = {"instrumento": "coisa", "negacao": "coisa", "agente": "alguém", "interlocutor": "alguém"}

def ler_csv(path, enc="utf-8-sig"):
    with open(path, encoding=enc) as f: return list(csv.DictReader(f))

def trocas(seq):
    return sum(x != y for x, y in zip(seq, seq[1:]))

def teste_trocas(seqs, n, rng):
    """Trocas de polo observadas contra as de sequências embaralhadas dentro de cada entrevista.
    p_blocos: chance de tão poucas trocas (os polos vêm em fases); p_alternancia: chance de tantas trocas."""
    obs = sum(trocas(s) for s in seqs)
    sims = []
    for _ in range(n):
        tot = 0
        for s in seqs:
            s = s[:]; rng.shuffle(s); tot += trocas(s)
        sims.append(tot)
    return dict(observadas=obs, esperadas=round(sum(sims) / n, 1), p_blocos=round(sum(x <= obs for x in sims) / n, 4),
                p_alternancia=round(sum(x >= obs for x in sims) / n, 4))

def mmss(minuto):
    m = float(minuto); return f"{int(m)}:{round((m - int(m)) * 60):02d}"

def analisar(a):
    from rede_semantica import CORES, SUPERFICIE, TEXTO, TEXTO_2
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rng = random.Random(a.seed)
    cod = {r["id"]: r for r in ler_csv(a.codigos, "utf-8")}
    mencoes = [{**m, **cod[m["id"]], "minuto": float(m["minuto"])} for m in ler_csv("data/ia_mencoes.csv") if m["id"] in cod]
    falta = [m["id"] for m in ler_csv("data/ia_mencoes.csv") if m["id"] not in cod]
    if falta: print(f"aviso: {len(falta)} menções sem código (ex.: {falta[:3]})")
    perguntas = ler_csv("data/ia_perguntas_sociais.csv")
    validas = sorted((m for m in mencoes if m["codigo"] in POLO and m["proprio"] == "1"), key=lambda m: (m["participante"], m["minuto"], m["id"]))
    pessoas = sorted({m["participante"] for m in validas})
    por = {p: [m for m in validas if m["participante"] == p] for p in pessoas}

    # resumo por entrevistado e teste de alternância (todas as menções; sem as expressões convencionais; só negação × alguém)
    variantes = {
        "todas": lambda m: True,
        "sem_conv": lambda m: not (POLO[m["codigo"]] == "alguém" and m["nota"].startswith("conv")),
        "negacao_x_alguem": lambda m: m["codigo"] != "instrumento",
    }
    linhas, testes = [], {}
    for nome, filtro in variantes.items():
        seqs = {p: [POLO[m["codigo"]] for m in por[p] if filtro(m)] for p in pessoas}
        testes[nome] = teste_trocas([s for s in seqs.values() if len(s) > 1], a.permutacoes, rng)
        for p in pessoas:
            t = teste_trocas([seqs[p]], a.permutacoes, rng) if len(seqs[p]) > 1 else {}
            linhas.append(dict(variante=nome, participante=p, coisa=seqs[p].count("coisa"), alguem=seqs[p].count("alguém"),
                               **{k: t.get(k, "") for k in ("observadas", "esperadas", "p_blocos", "p_alternancia")}))
    with open("data/ia_oscilacao_por_participante.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0])); w.writeheader(); w.writerows(linhas)

    # pares mais próximos entre negação explícita e o polo 'alguém', por entrevistado
    pares = []
    for p in pessoas:
        negs = [m for m in por[p] if m["codigo"] == "negacao"]
        alg = [m for m in por[p] if POLO[m["codigo"]] == "alguém"]
        if negs and alg:
            n_, g_ = min(((n, g) for n in negs for g in alg), key=lambda x: abs(x[0]["minuto"] - x[1]["minuto"]))
            pares.append(dict(participante=p, segundos=round(abs(n_["minuto"] - g_["minuto"]) * 60),
                              negacao_min=mmss(n_["minuto"]), negacao=n_["frase"],
                              alguem_min=mmss(g_["minuto"]), alguem_codigo=g_["codigo"], alguem=g_["frase"]))
    with open("data/ia_pares_negacao_alguem.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pares[0])); w.writeheader(); w.writerows(pares)

    # quanto do polo 'alguém' vem logo depois (5 min) de uma pergunta do roteiro sobre tratamento social ou personalidade
    perg = {p: [float(q["minuto"]) for q in perguntas if q["participante"] == p] for p in pessoas}
    alg_total = [m for m in validas if POLO[m["codigo"]] == "alguém"]
    alg_pos = [m for m in alg_total if any(0 <= m["minuto"] - q <= 5 for q in perg[m["participante"]])]

    # figura: uma linha por entrevistado, faixa de cima = coisa, faixa de baixo = alguém
    ordem = sorted(pessoas, key=lambda p: -sum(POLO[m["codigo"]] == "alguém" for m in por[p]) / len(por[p]))
    estilo = {"instrumento": dict(marker="|", s=55, lw=1.1, c=CORES[0], dy=0.17),
              "negacao": dict(marker="D", s=46, lw=0.8, c=CORES[0], dy=0.17, ec=TEXTO),
              "agente": dict(marker="o", s=34, lw=0.8, c=CORES[1], dy=-0.17, ec=SUPERFICIE),
              "interlocutor": dict(marker="^", s=50, lw=0.8, c=CORES[1], dy=-0.17, ec=TEXTO)}
    plt.rcParams["font.family"] = "Liberation Sans"
    fig, ax = plt.subplots(figsize=(14, 1.0 * len(ordem) + 1.9), dpi=200)
    fig.patch.set_facecolor(SUPERFICIE); ax.set_facecolor(SUPERFICIE)
    xmax = max(m["minuto"] for m in validas) + 2
    for i, p in enumerate(ordem):
        y = len(ordem) - 1 - i
        ax.axhline(y, color="#e6e5e0", lw=0.8, zorder=0)
        for q in perg[p]:
            ax.plot([q, q], [y - 0.36, y + 0.36], color=TEXTO_2, lw=0.9, ls=(0, (2, 2)), zorder=1)
        for cod_, e in estilo.items():
            ms = [m for m in por[p] if m["codigo"] == cod_]
            jit = [((zlib.crc32(m["id"].encode()) % 7) - 3) * 0.018 for m in ms]   # deslocamento fixo para separar marcas no mesmo minuto
            kw = dict(marker=e["marker"], s=e["s"], linewidths=e["lw"], zorder=3)
            if e["marker"] == "|": ax.scatter([m["minuto"] for m in ms], [y + e["dy"] + j for j in jit], color=e["c"], **kw)
            else: ax.scatter([m["minuto"] for m in ms], [y + e["dy"] + j for j in jit], facecolor=e["c"], edgecolors=e["ec"], **kw)
        t = next(l for l in linhas if l["variante"] == "todas" and l["participante"] == p)
        ax.text(xmax + 1, y, f"{t['coisa']} coisa · {t['alguem']} alguém\n{t['observadas']} trocas (esperadas {t['esperadas']})",
                va="center", ha="left", fontsize=8.5, color=TEXTO_2)
    ax.set_yticks(range(len(ordem))); ax.set_yticklabels(ordem[::-1], fontsize=10.5, color=TEXTO)
    ax.set_xlim(-1, xmax); ax.set_ylim(-0.6, len(ordem) - 0.4)
    ax.set_xlabel("minuto da entrevista", fontsize=9.5, color=TEXTO_2)
    ax.tick_params(axis="x", colors=TEXTO_2, labelsize=9); ax.tick_params(axis="y", length=0)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c2")
    leg = [plt.Line2D([], [], ls="", marker="|", ms=10, mew=1.4, color=CORES[0], label="instrumento (coisa)"),
           plt.Line2D([], [], ls="", marker="D", ms=6.5, mfc=CORES[0], mec=TEXTO, label="negação explícita (coisa)"),
           plt.Line2D([], [], ls="", marker="o", ms=7, mfc=CORES[1], mec=SUPERFICIE, label="agente (alguém)"),
           plt.Line2D([], [], ls="", marker="^", ms=7.5, mfc=CORES[1], mec=TEXTO, label="interlocutor social (alguém)"),
           plt.Line2D([], [], color=TEXTO_2, lw=0.9, ls=(0, (2, 2)), label="pergunta do roteiro sobre trato social ou personalidade")]
    fig.legend(handles=leg, loc="lower left", ncol=3, frameon=False, fontsize=9, labelcolor=TEXTO_2,
               bbox_to_anchor=(0.06, 0.0))
    tt = testes["todas"]
    fig.text(0.06, 0.975, "Coisa ou alguém: o enquadramento da IA ao longo de cada entrevista", fontsize=15,
             fontweight="semibold", color=TEXTO, va="top")
    fig.text(0.06, 0.935, f"{len(validas)} frases dos entrevistados codificadas (faixa de cima: IA como coisa; de baixo: como alguém). "
             f"{tt['observadas']} trocas de polo contra {tt['esperadas']} esperadas se a ordem fosse aleatória. "
             f"Ordenado pela proporção do polo 'alguém'.", fontsize=9.5, color=TEXTO_2, va="top", wrap=True)
    fig.subplots_adjust(left=0.1, right=0.83, top=0.87, bottom=0.15)
    os.makedirs("data/figuras", exist_ok=True)
    fig.savefig("data/figuras/ia_coisa_ou_alguem.png", facecolor=SUPERFICIE)
    plt.close(fig)

    print(f"{len(validas)} frases nos polos (voz própria): {sum(POLO[m['codigo']] == 'coisa' for m in validas)} coisa, "
          f"{len(alg_total)} alguém; {len(alg_pos)} das 'alguém' até 5 min depois de pergunta sobre trato ou personalidade")
    for nome, t in testes.items(): print(f"  trocas ({nome}): {t}")
    print("  por pessoa (todas): " + "; ".join(f"{l['participante']} {l['coisa']}/{l['alguem']} trocas {l['observadas']} vs {l['esperadas']} "
                                              f"(p_blocos {l['p_blocos']})" for l in linhas if l["variante"] == "todas"))
    print("figura: data/figuras/ia_coisa_ou_alguem.png; tabelas: data/ia_oscilacao_por_participante.csv, data/ia_pares_negacao_alguem.csv")

def amostra(a):
    """Amostra estratificada (mais casos dos códigos raros) para validar a codificação às cegas."""
    rng = random.Random(a.seed)
    cod = {r["id"]: r["codigo"] for r in ler_csv(a.codigos, "utf-8")}
    mencoes = ler_csv("data/ia_mencoes.csv")
    cotas = {"instrumento": 15, "agente": 15, "interlocutor": 12, "negacao": 10, "neutro": 5, "nao_ia": 3}
    sel = []
    for c, n in cotas.items():
        grupo = [m for m in mencoes if cod.get(m["id"]) == c]
        sel += rng.sample(grupo, min(n, len(grupo)))
    rng.shuffle(sel)
    with open("data/ia_validacao_amostra.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "contexto_antes", "frase", "contexto_depois", "codigo", "proprio"])
        w.writerows([m["id"], m["contexto_antes"], m["frase"], m["contexto_depois"], "", ""] for m in sel)
    print(f"{len(sel)} frases em data/ia_validacao_amostra.csv (colunas codigo e proprio em branco)")

# Pistas do livro de códigos: a associação delas com um polo é esperada por construção. Em lemas (--unidade lema) e nas
# formas em que aparecem (--unidade forma; os verbos só na 3ª pessoa, a da IA como sujeito, e não o 'sei' do falante)
CRITERIOS = {"usar", "ferramenta", "recurso", "acessório", "alimentar", "configurar", "pagar", "gerar", "transcrever",
             "resumir", "traduzir", "jogar", "máquina", "matemático", "algoritmo", "consciência", "autonomia",
             "pensar", "entender", "saber", "sugerir", "errar", "mentir", "ajudar", "perguntar", "aprender", "alertar",
             "falar", "dizer", "criar", "personalidade", "traço", "substituir", "autor", "autoria", "coautor",
             "conversar", "agradecer", "educado", "grosseiro", "desabafar", "estagiário", "assistente", "funcionário",
             "terapeuta", "terapia", "amigo", "colega", "parceiro", "júnior", "chatinho", "conhecer", "discutir",
             "irritar", "pessoa", "humanização", "amigável"}
CRITERIOS_FORMAS = {
    "usar", "uso", "usa", "usam", "usando", "usei", "usava", "utilizar", "utilizo", "utiliza", "utilizando",
    "ferramenta", "ferramentas", "recurso", "acessório", "máquina", "máquinas", "algoritmo", "algoritmos", "matemática",
    "personalidade", "personalidades", "autonomia", "falou", "fala", "falando", "disse", "diz", "pensa", "pensando",
    "pensamento", "entende", "entendeu", "sabe", "sabia", "sugere", "sugeriu", "sugerindo", "erra", "errou", "mente",
    "alucina", "ajuda", "ajudou", "ajudando", "ajudar", "ajude", "pergunta", "perguntou", "conversar", "converso",
    "conversando", "discutindo", "discuto", "obrigado", "obrigada", "estagiário", "júnior", "assistente", "amigo",
    "amiga", "parceiro", "parceira", "funcionário", "autor", "autora", "autoria", "coautor", "criou", "cria", "criar"}

def log_odds(ya, yb, fundo, a0):
    """z do log-odds ponderado com prior de Dirichlet informativo (Monroe, Colaresi e Quinn, 2008).
    ya, yb: contagens nos dois grupos; fundo: contagens no corpus todo, que vira o prior de força a0; z > 0 = grupo a."""
    na, nb, nf = sum(ya.values()), sum(yb.values()), sum(fundo.values())
    out = {}
    for w in set(ya) | set(yb):
        al = a0 * (fundo.get(w, 0) + 1) / (nf + len(fundo))
        d = (math.log((ya[w] + al) / (na + a0 - ya[w] - al)) - math.log((yb[w] + al) / (nb + a0 - yb[w] - al)))
        out[w] = d / math.sqrt(1 / (ya[w] + al) + 1 / (yb[w] + al))
    return out

def palavras(a):
    from rede_semantica import AQUI, CORES, SUPERFICIE, TEXTO, TEXTO_2, lema, ler_stopwords, unidades
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    nlp = spacy.load("pt_core_news_sm", disable=["ner"])
    stop = ler_stopwords(os.path.join(AQUI, "stopwords_rede.txt"))
    cod = {r["id"]: r for r in ler_csv(a.codigos, "utf-8")}
    sel = [{**m, **cod[m["id"]]} for m in ler_csv("data/ia_mencoes.csv")
           if m["id"] in cod and cod[m["id"]]["codigo"] in POLO and cod[m["id"]]["proprio"] == "1"]
    # forma: todas as palavras como aparecem (pronomes e preposições incluídos); lema: só lemas de conteúdo, como na rede
    if a.unidade == "forma":
        token = lambda t: (t.text if t.text in ("IA", "IAs", "AI") else t.text.lower()) if t.is_alpha else None
        criterios = CRITERIOS_FORMAS
    else:
        token = lambda t: lema(t, stop)
        criterios = CRITERIOS
    for m, doc in zip(sel, nlp.pipe((preparar(m["frase"]) for m in sel), batch_size=64)):
        m["lemas"] = [x for x in (token(t) for t in doc) if x]
    textos = [t for (t,) in sqlite3.connect(a.db).execute(
        "SELECT texto FROM turnos_analise WHERE papel = 'entrevistado' ORDER BY transcricao_id, ordem")]
    fundo = Counter(x for d in nlp.pipe((preparar(t) for t in textos), batch_size=64) for t in d for x in [token(t)] if x)

    grupos = {p: [m for m in sel if POLO[m["codigo"]] == p] for p in ("alguém", "coisa")}
    cont = {p: Counter(l for m in g for l in m["lemas"]) for p, g in grupos.items()}
    quem = {p: defaultdict(set) for p in grupos}
    for p, g in grupos.items():
        for m in g:
            for l in m["lemas"]: quem[p][l].add(m["participante"])
    z = log_odds(cont["alguém"], cont["coisa"], fundo, a.prior)
    linhas = sorted(({"palavra": w, "z": round(v, 2), "n_alguem": cont["alguém"][w], "n_coisa": cont["coisa"][w],
                      "pessoas_alguem": len(quem["alguém"][w]), "pessoas_coisa": len(quem["coisa"][w]),
                      "criterio": int(w in criterios)} for w, v in z.items()), key=lambda r: -r["z"])
    saida = "figuras/ia_coisa_alguem_palavras" + ("" if a.unidade == "forma" else "_lemas")
    # a tabela completa traz todas as palavras, inclusive nomes de empresas dos entrevistados: fica em data/, fora do git
    with open(saida.replace("figuras/", "data/") + ".csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0])); w.writeheader(); w.writerows(linhas)
    # no gráfico: |z| ≥ 1,96 e usada por ao menos 3 entrevistados no polo em que é mais frequente
    ok = lambda r, p: abs(r["z"]) >= 1.96 and r[f"pessoas_{'alguem' if p == 'alguém' else 'coisa'}"] >= 3
    alg = [r for r in linhas if r["z"] > 0 and ok(r, "alguém")][:a.n]
    coi = [r for r in linhas if r["z"] < 0 and ok(r, "coisa")][::-1][:a.n]
    mostrar = alg + coi[::-1]

    plt.rcParams["font.family"] = "Liberation Sans"
    fig, ax = plt.subplots(figsize=(10, 0.3 * len(mostrar) + 2.4), dpi=200)
    fig.patch.set_facecolor(SUPERFICIE); ax.set_facecolor(SUPERFICIE)
    ys = list(range(len(mostrar)))[::-1]
    zmax = max(abs(r["z"]) for r in mostrar)
    for y, r in zip(ys, mostrar):
        cor = CORES[1] if r["z"] > 0 else CORES[0]
        ax.barh(y, r["z"], height=0.68, color=cor, alpha=0.38 if r["criterio"] else 1, edgecolor=cor,
                hatch="////" if r["criterio"] else None, linewidth=0.8)
        lado = -1 if r["z"] > 0 else 1   # palavra do outro lado do zero, contagens na ponta da barra
        ax.text(lado * 0.12, y, r["palavra"], ha="right" if r["z"] > 0 else "left", va="center", fontsize=10,
                color=TEXTO, fontstyle="italic" if r["criterio"] else "normal")
        ax.text(r["z"] - lado * 0.12, y, f"{r['n_alguem']} | {r['n_coisa']}", ha="left" if r["z"] > 0 else "right",
                va="center", fontsize=7.5, color=TEXTO_2)
    for x in (-1.96, 1.96): ax.axvline(x, color=TEXTO_2, lw=0.7, ls=(0, (2, 2)), zorder=0)
    ax.axvline(0, color="#9a9993", lw=0.8)
    ax.set_xlim(-zmax - 1.6, zmax + 1.6); ax.set_ylim(-0.8, len(mostrar) - 0.2); ax.set_yticks([])
    ax.tick_params(axis="x", colors=TEXTO_2, labelsize=8.5)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c2")
    ax.set_xlabel("z do log-odds ponderado (linha tracejada: |z| = 1,96)", fontsize=9, color=TEXTO_2)
    for lado, rotulo, cor in ((1, "IA como alguém →", CORES[1]), (-1, "← IA como coisa", CORES[0])):
        ax.text(lado * zmax * 0.55, len(mostrar) - 0.3, rotulo, ha="center", fontsize=10.5, color=cor, fontweight="semibold")
    na, nb = len(grupos["alguém"]), len(grupos["coisa"])
    fig.text(0.04, 0.985, "Que palavras distinguem a IA como coisa da IA como alguém", fontsize=14, fontweight="semibold",
             color=TEXTO, va="top")
    fig.text(0.04, 0.95, f"{na} frases de 'alguém' contra {nb} de 'coisa', em voz própria; "
             + ("todas as palavras, como foram ditas. " if a.unidade == "forma" else "lemas de conteúdo. ")
             + f"Log-odds ponderado com prior do corpus inteiro (Monroe et al., 2008); só palavras usadas por ao menos 3 "
             f"entrevistados no polo. Números: ocorrências em alguém | coisa. Barras claras e hachuradas, em itálico: pistas "
             f"usadas na codificação (associação esperada por construção).", fontsize=8.5, color=TEXTO_2, va="top", wrap=True)
    fig.subplots_adjust(left=0.04, right=0.96, top=0.86, bottom=0.08)
    fig.savefig(saida + ".png", facecolor=SUPERFICIE)
    plt.close(fig)
    print(f"{na} frases alguém, {nb} coisa; {sum(r['z'] >= 1.96 for r in linhas)} palavras com z ≥ 1,96 e "
          f"{sum(r['z'] <= -1.96 for r in linhas)} com z ≤ −1,96 (antes do filtro de 3 entrevistados)")
    for nome, g in (("alguém", alg), ("coisa", coi)):
        print(f"  {nome}: " + ", ".join(f"{r['palavra']}{'*' if r['criterio'] else ''} ({r['z']}; {r['n_alguem']}|{r['n_coisa']})" for r in g))
    print(f"figura: {saida}.png")

def discriminante(a):
    """Análise discriminante linear de dois grupos (alguém × coisa) com a presença de cada lema na frase como preditor.
    LDA com encolhimento (Ledoit-Wolf), porque há mais lemas do que a matriz de covariância aguenta, e priors iguais
    (corte no meio, apesar de haver três vezes mais 'coisa'). A classificação é avaliada fora da amostra: validação
    cruzada em 10 partes e deixando um entrevistado de fora; a significância vem de 1.000 permutações dos rótulos.
    O modelo 'sem pistas' tira os lemas usados como pista na codificação, para medir o que não é circular. Para
    comparação, os mesmos modelos com as palavras como foram ditas."""
    import numpy as np
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
    from sklearn.model_selection import StratifiedKFold, LeaveOneGroupOut, cross_val_predict, permutation_test_score
    from sklearn.metrics import balanced_accuracy_score, confusion_matrix
    from rede_semantica import AQUI, CORES, SUPERFICIE, TEXTO, TEXTO_2, lema, ler_stopwords
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    nlp = spacy.load("pt_core_news_sm", disable=["ner"])
    stop = ler_stopwords(os.path.join(AQUI, "stopwords_rede.txt"))
    cod = {r["id"]: r for r in ler_csv(a.codigos, "utf-8")}
    sel = [{**m, **cod[m["id"]]} for m in ler_csv("data/ia_mencoes.csv")
           if m["id"] in cod and cod[m["id"]]["codigo"] in POLO and cod[m["id"]]["proprio"] == "1"]
    docs = list(nlp.pipe((preparar(m["frase"]) for m in sel), batch_size=64))
    y = np.array([1 if POLO[m["codigo"]] == "alguém" else 0 for m in sel])
    grupos = np.array([m["participante"] for m in sel])
    forma = lambda t: (t.text if t.text in ("IA", "IAs", "AI") else t.text.lower()) if t.is_alpha else None
    modelos = {"lemas": (lambda t: lema(t, stop), set()), "lemas sem pistas": (lambda t: lema(t, stop), CRITERIOS),
               "formas": (forma, set()), "formas sem pistas": (forma, CRITERIOS_FORMAS)}

    resumo, res = [], {}
    for nome, (tok, fora) in modelos.items():
        us = [set(x for x in (tok(t) for t in d) if x) for d in docs]
        df, quem = Counter(x for u in us for x in u), defaultdict(set)
        for u, p in zip(us, grupos):
            for x in u: quem[x].add(p)
        # preditores escolhidos só pela frequência (sem olhar o rótulo): ≥ 5 frases e ≥ 3 entrevistados
        feats = sorted(x for x, n in df.items() if n >= 5 and len(quem[x]) >= 3 and x not in fora)
        X = np.array([[x in u for x in feats] for u in us], dtype=float)
        lda = LDA(solver="lsqr", shrinkage="auto", priors=[0.5, 0.5])
        cv = StratifiedKFold(10, shuffle=True, random_state=a.seed)
        bac, perm, p = permutation_test_score(lda, X, y, cv=cv, scoring="balanced_accuracy", n_permutations=1000,
                                              random_state=a.seed, n_jobs=-1)
        pred = cross_val_predict(lda, X, y, cv=cv)
        escore = cross_val_predict(lda, X, y, cv=cv, method="decision_function")
        lopo = cross_val_predict(lda, X, y, cv=LeaveOneGroupOut(), groups=grupos)
        cm = confusion_matrix(y, pred, labels=[1, 0])   # linhas: real alguém, coisa; colunas: previsto
        cheio = lda.fit(X, y).decision_function(X)
        cargas = {f: float(np.corrcoef(X[:, j], cheio)[0, 1]) for j, f in enumerate(feats) if X[:, j].std() > 0}
        res[nome] = dict(cm=cm, escore=escore, cargas=cargas, criterios=fora or (CRITERIOS if "lema" in nome else CRITERIOS_FORMAS))
        resumo.append({"modelo": nome, "preditores": len(feats), "acerto_medio_por_grupo": round(bac, 3),
                       "acerto_global": round(float((pred == y).mean()), 3), "p_permutacao": round(p, 4),
                       "acerto_medio_entrevistado_fora": round(balanced_accuracy_score(y, lopo), 3),
                       "alguem_como_alguem": int(cm[0, 0]), "alguem_como_coisa": int(cm[0, 1]),
                       "coisa_como_alguem": int(cm[1, 0]), "coisa_como_coisa": int(cm[1, 1])})
    with open("figuras/ia_discriminante_resumo.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(resumo[0])); w.writeheader(); w.writerows(resumo)
    with open("figuras/ia_discriminante_cargas_lemas.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["lema", "carga", "pista_da_codificacao"])
        w.writerows([l, round(c, 3), int(l in CRITERIOS)] for l, c in sorted(res["lemas"]["cargas"].items(), key=lambda x: -x[1]))

    # figura: as duas matrizes 2×2 dos lemas, a distribuição dos escores e as cargas
    plt.rcParams["font.family"] = "Liberation Sans"
    fig = plt.figure(figsize=(12, 11), dpi=200)
    fig.patch.set_facecolor(SUPERFICIE)
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.55], width_ratios=[1, 1, 1.35], hspace=0.3, wspace=0.35,
                          left=0.06, right=0.97, top=0.86, bottom=0.06)
    rampa = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#184f95"]   # rampa sequencial azul da skill dataviz
    for k, nome in enumerate(("lemas", "lemas sem pistas")):
        ax = fig.add_subplot(gs[0, k]); cm = res[nome]["cm"]; r = next(x for x in resumo if x["modelo"] == nome)
        for i in range(2):
            for j in range(2):
                pct = cm[i, j] / cm[i].sum()
                cor = rampa[min(int(pct * 5), 4)]
                ax.add_patch(plt.Rectangle((j, 1 - i), 1, 1, facecolor=cor, edgecolor=SUPERFICIE, linewidth=3))
                ax.text(j + 0.5, 1.5 - i, f"{cm[i, j]}\n{pct:.0%}", ha="center", va="center", fontsize=12,
                        color="#ffffff" if pct >= 0.6 else TEXTO, fontweight="semibold")
        ax.set_xlim(0, 2); ax.set_ylim(0, 2); ax.set_aspect("equal")
        ax.set_xticks([0.5, 1.5]); ax.set_xticklabels(["alguém", "coisa"], fontsize=9.5, color=TEXTO)
        ax.set_yticks([1.5, 0.5]); ax.set_yticklabels(["alguém", "coisa"], fontsize=9.5, color=TEXTO)
        ax.xaxis.set_label_position("top"); ax.xaxis.tick_top()
        ax.set_xlabel("previsto", fontsize=9, color=TEXTO_2); ax.set_ylabel("real (codificação)", fontsize=9, color=TEXTO_2)
        ax.tick_params(length=0)
        for s in ax.spines.values(): s.set_visible(False)
        ax.set_title(f"{'Todos os lemas' if nome == 'lemas' else 'Sem as pistas da codificação'} ({r['preditores']})\n"
                     f"acerto médio por grupo {r['acerto_medio_por_grupo']:.0%} · entrevistado fora "
                     f"{r['acerto_medio_entrevistado_fora']:.0%}", fontsize=9.5, color=TEXTO, pad=26)
    ax = fig.add_subplot(gs[0, 2]); ax.set_facecolor(SUPERFICIE); e = res["lemas"]["escore"]
    bins = np.linspace(e.min(), e.max(), 26)
    for val, cor, rot in ((1, CORES[1], "alguém"), (0, CORES[0], "coisa")):
        ax.hist(e[y == val], bins=bins, density=True, histtype="step", linewidth=2, color=cor, label=f"{rot} ({(y == val).sum()})")
    ax.axvline(0, color=TEXTO_2, lw=0.9, ls=(0, (2, 2)))
    ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
    ax.text(0.15, ax.get_ylim()[1] * 0.99, "corte", fontsize=8, color=TEXTO_2, va="top")
    ax.set_xlabel("escore discriminante fora da amostra (todos os lemas)", fontsize=8.5, color=TEXTO_2)
    ax.set_yticks([]); ax.tick_params(axis="x", colors=TEXTO_2, labelsize=8)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c2")
    ax.legend(frameon=False, fontsize=8.5, labelcolor=TEXTO_2, loc="upper left")
    ax.set_title("Quanto os grupos se sobrepõem", fontsize=9.5, color=TEXTO, pad=8)

    ax = fig.add_subplot(gs[1, :]); ax.set_facecolor(SUPERFICIE)
    cargas = res["lemas"]["cargas"]
    pos = sorted((l for l in cargas if cargas[l] > 0), key=lambda l: -cargas[l])[:12]
    neg = sorted((l for l in cargas if cargas[l] < 0), key=lambda l: cargas[l])[:12]
    mostrar = pos + neg[::-1]
    cmax = max(abs(cargas[l]) for l in mostrar)
    for yy, l in zip(range(len(mostrar))[::-1], mostrar):
        c = cargas[l]; cor = CORES[1] if c > 0 else CORES[0]; pista = l in CRITERIOS
        ax.barh(yy, c, height=0.68, color=cor, alpha=0.38 if pista else 1, edgecolor=cor, hatch="////" if pista else None, linewidth=0.8)
        ax.text(-0.006 if c > 0 else 0.006, yy, l, ha="right" if c > 0 else "left", va="center", fontsize=9.5, color=TEXTO,
                fontstyle="italic" if pista else "normal")
    ax.axvline(0, color="#9a9993", lw=0.8)
    ax.set_xlim(-cmax * 1.35, cmax * 1.35); ax.set_ylim(-0.8, len(mostrar) + 0.6); ax.set_yticks([])
    ax.tick_params(axis="x", colors=TEXTO_2, labelsize=8.5)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c2")
    ax.set_xlabel("carga: correlação do lema com a função discriminante (todos os lemas)", fontsize=9, color=TEXTO_2)
    for lado, rot, cor in ((1, "puxa para alguém →", CORES[1]), (-1, "← puxa para coisa", CORES[0])):
        ax.text(lado * cmax * 0.7, len(mostrar) - 0.1, rot, ha="center", fontsize=10, color=cor, fontweight="semibold")
    ax.set_title("Lemas que mais carregam a função discriminante (hachurados, em itálico: pistas da codificação)",
                 fontsize=9.5, color=TEXTO, pad=10)
    rf = next(x for x in resumo if x["modelo"] == "formas sem pistas")
    fig.text(0.06, 0.975, "Análise discriminante: alguém × coisa a partir dos lemas", fontsize=15, fontweight="semibold",
             color=TEXTO, va="top")
    fig.text(0.06, 0.945, f"{len(y)} frases em voz própria ({(y == 1).sum()} alguém, {(y == 0).sum()} coisa). LDA com encolhimento, "
             f"priors iguais; matrizes de validação cruzada em 10 partes (acaso = 50%; todos os modelos p < 0,01 em 1.000 "
             f"permutações). Para comparação, as palavras como foram ditas, sem as pistas, acertam "
             f"{rf['acerto_medio_por_grupo']:.0%} ({rf['acerto_medio_entrevistado_fora']:.0%} com o entrevistado fora).",
             fontsize=8.8, color=TEXTO_2, va="top", wrap=True)
    fig.savefig("figuras/ia_discriminante_lemas.png", facecolor=SUPERFICIE)
    plt.close(fig)
    for r in resumo: print(r)
    print("lemas, para alguém: " + ", ".join(f"{l}{'*' if l in CRITERIOS else ''} ({cargas[l]:.2f})" for l in pos))
    print("lemas, para coisa: " + ", ".join(f"{l}{'*' if l in CRITERIOS else ''} ({cargas[l]:.2f})" for l in neg))
    print("figura: figuras/ia_discriminante_lemas.png")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("acao", choices=["extrair", "analisar", "amostra", "palavras", "discriminante"])
    ap.add_argument("--prior", type=float, default=1000, help="força do prior do corpus no log-odds")
    ap.add_argument("--n", type=int, default=15, help="máximo de palavras por polo no gráfico")
    ap.add_argument("--unidade", choices=["forma", "lema"], default="forma",
                    help="palavras como ditas (com pronomes e preposições) ou lemas de conteúdo")
    ap.add_argument("--db", default="data/entrevistas.db")
    ap.add_argument("--codigos", default="codificacao/ia_enquadramento.csv")
    ap.add_argument("--permutacoes", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    {"extrair": extrair, "analisar": analisar, "amostra": amostra, "palavras": palavras,
     "discriminante": discriminante}[a.acao](a)

if __name__ == "__main__":
    main()
