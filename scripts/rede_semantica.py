#!/usr/bin/env python3
"""
Rede semântica (análise de similitude) das N palavras mais frequentes do corpus principal.

Texto: por padrão, só as falas dos entrevistados nas 8 entrevistas do corpus principal (visão turnos_analise).
Palavras: lemas do spaCy (pt_core_news_sm; verbos pelo simplemma), só substantivos, nomes próprios, verbos e adjetivos, menos os lemas
de scripts/stopwords_rede.txt. "IA", "IAs", "AI" e "inteligência artificial" viram IA; o "ia" minúsculo é o verbo ir.
Arestas: duas palavras se ligam quando aparecem na mesma frase (ou no mesmo turno, com --unidade turno). O peso é o
índice de Jaccard (frases com as duas / frases com qualquer uma delas) ou, com --indice coocorrencia, o número bruto
de frases em comum; com o número bruto, as palavras mais frequentes viram centro de estrela e a árvore diz pouco.
A figura mostra a árvore máxima desse grafo (como na análise de similitude do IRaMuTeQ), com as comunidades da
árvore (Louvain) em cores.

Uso:
  python scripts/rede_semantica.py [--n 50] [--falantes entrevistados|todos] [--unidade frase|turno]
                                   [--indice jaccard|coocorrencia]
Saída: figuras/rede_semantica.png, figuras/rede_semantica_nos.csv, figuras/rede_semantica_arestas.csv,
       figuras/rede_semantica.gexf (grafo completo de coocorrência, para abrir no Gephi)
"""
import argparse, csv, itertools, os, re, sqlite3, subprocess
from collections import Counter
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
import simplemma
import spacy

AQUI = os.path.dirname(os.path.abspath(__file__))
CLASSES = {"NOUN", "PROPN", "VERB", "ADJ"}
FORMAS_IA = {"IA", "IAs", "AI", "AIs"}
# Correções do lematizador e uniões de lemas, decididas olhando as formas de cada lema (ver STATUS.md)
UNIR = {"uso": "usar", "vejo": "ver", "fiz": "fazer", "preciso": "precisar", "fico": "ficar", "chatgpt": "ChatGPT", "gemini": "Gemini",
        "google": "Google", "claude": "Claude", "copilot": "Copilot"}

# Paleta categórica de referência (skill dataviz), na ordem fixa; superfície e textos do modo claro
CORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SUPERFICIE, TEXTO, TEXTO_2, ARESTA = "#fcfcfb", "#0b0b0b", "#52514e", "#b9b8b2"
# Pares de posições da paleta que o validador da skill reprova lado a lado (daltonismo ou visão normal);
# comunidades vizinhas na árvore não recebem um desses pares
CONFUNDIVEIS = {(0, 6), (1, 3), (1, 4), (1, 5), (1, 7), (2, 4), (2, 7), (4, 7), (5, 7)}
PT = 72   # pontos por polegada: o neato trabalha em polegadas, o matplotlib desenha em pontos

def ler_stopwords(path):
    with open(path, encoding="utf-8") as f:
        return {w for linha in f for w in linha.split("#")[0].split()}

def preparar(t):
    """Normaliza só para o processamento; a base continua com o texto original."""
    t = re.sub(r"\bintelig[êe]ncias? artificia(?:l|is)\b", "IA", t, flags=re.I)
    t = re.sub(r"\bchat\s*-?\s*gpt\b", "ChatGPT", t, flags=re.I)
    t = re.sub(r"\b(\w+)(?:-\1\b)+", r"\1", t, flags=re.I)   # gaguejo: 'é-é-é' -> 'é'
    t = t.replace("--", " ")                                 # palavra interrompida: 'grava-- a gravação'
    return re.sub(r"([.?!])(?=[A-ZÀ-Ú\"])", r"\1 ", t)      # ponto sem espaço: 'Tá.É' -> 'Tá. É'

VERBOS_CURTOS = {"ir", "ser", "ter", "ver", "ler", "dar", "vir", "pôr", "rir", "crer"}

def lema_verbo(w, l_spacy):
    """O spaCy erra a 1ª pessoa dos verbos ('entendo' -> 'enter', 'vejo' -> 'vejo', 'mando' -> 'mar'), o que inflaria a
    associação com a fala sobre si. Fica o lema do spaCy quando ele é um infinitivo reconhecido pelo simplemma; senão
    vale o do simplemma, que por sua vez erra quando a forma também é substantivo ('uso', 'gosto') e aí se completa -ar/-er/-ir."""
    if l_spacy != w and l_spacy.endswith(("ar", "er", "ir", "or", "ôr")) and (
            l_spacy in VERBOS_CURTOS or (len(l_spacy) > 3 and simplemma.is_known(l_spacy, lang="pt")
                                         and simplemma.lemmatize(l_spacy, lang="pt") == l_spacy)):
        return l_spacy
    l = simplemma.lemmatize(w, lang="pt")
    if l == w and w.endswith("o"):
        return next((w[:-1] + s for s in ("ar", "er", "ir") if simplemma.is_known(w[:-1] + s, lang="pt")), l)
    return l

def lema(tok, stop):
    if tok.text in FORMAS_IA: return "IA"
    if tok.pos_ not in CLASSES or not tok.text.isalpha() or len(tok.text) < 2: return None
    l = lema_verbo(tok.text.lower(), tok.lemma_.lower()) if tok.pos_ == "VERB" else tok.lemma_.lower()
    l = UNIR.get(l, l)
    return None if l in stop else l

def unidades(textos, nlp, stop, por_frase):
    """Uma lista de lemas por frase (ou por turno)."""
    for doc in nlp.pipe((preparar(t) for t in textos), batch_size=64):
        partes = doc.sents if por_frase else [doc]
        for s in partes:
            ls = [l for l in (lema(tok, stop) for tok in s) if l]
            if ls: yield ls

def colorir(T, comunidades):
    """Posição na paleta para cada comunidade, na ordem fixa, pulando as que se confundem com uma vizinha."""
    de = {n: c for c, g in enumerate(comunidades) for n in g}
    vizinhas = {c: set() for c in range(len(comunidades))}
    for u, v in T.edges:
        if de[u] != de[v]: vizinhas[de[u]].add(de[v]); vizinhas[de[v]].add(de[u])
    cor = {}
    def livre(c, s):
        return all(tuple(sorted((s, cor[v]))) not in CONFUNDIVEIS and s != cor[v] for v in vizinhas[c] if v in cor)
    for c in range(len(comunidades)):
        cands = [s for s in range(len(CORES)) if livre(c, s)]
        cor[c] = next((s for s in cands if s not in cor.values()), cands[0] if cands else c % len(CORES))
    return cor

def posicionar(T, caixas, seed):
    """Layout do neato (Graphviz) com remoção de sobreposição; caixas em pontos (largura, altura); devolve polegadas."""
    ids = {n: f"n{i}" for i, n in enumerate(T)}
    dot = ["graph G {", f'graph [overlap=prism, sep="+8", mode=major, start={seed}, pack=true];',
           'node [shape=box, fixedsize=true, label=""];']
    dot += [f'{ids[n]} [width={caixas[n][0] / PT:.3f}, height={caixas[n][1] / PT:.3f}];' for n in T]
    dot += [f"{ids[u]} -- {ids[v]} [len=0.9];" for u, v in T.edges] + ["}"]
    saida = subprocess.run(["neato", "-Tplain"], input="\n".join(dot), text=True, capture_output=True, check=True).stdout
    nome = {v: k for k, v in ids.items()}
    return {nome[p[1]]: (float(p[2]), float(p[3])) for p in (l.split() for l in saida.splitlines()) if p[0] == "node"}

def construir_rede(us, palavras, indice="jaccard", seed=42):
    """Grafo de coocorrência entre `palavras` nas unidades `us`, sua árvore máxima e as comunidades da árvore."""
    nos = set(palavras)
    cooc, presenca = Counter(), Counter()   # presenca: em quantas unidades a palavra aparece
    for u in us:
        s = sorted(set(u) & nos)
        presenca.update(s); cooc.update(itertools.combinations(s, 2))
    jac = lambda u, v, c: round(c / (presenca[u] + presenca[v] - c), 4)
    G = nx.Graph()
    G.add_nodes_from(palavras)
    G.add_edges_from((u, v, {"weight": jac(u, v, c) if indice == "jaccard" else c, "coocorrencias": c,
                             "jaccard": jac(u, v, c)}) for (u, v), c in cooc.items())
    soltas = [w for w in palavras if G.degree(w) == 0]
    if soltas: print(f"aviso: palavras sem coocorrência com as demais: {soltas}")
    T = nx.maximum_spanning_tree(G, weight="weight")
    comunidades = sorted(nx.community.louvain_communities(T, weight="weight", seed=seed),
                         key=lambda g: (-sum(presenca[n] for n in g), sorted(g)))
    return G, T, comunidades

def legenda_comunidades(T, comunidades, freq):
    """Cor de cada nó pela comunidade e a legenda correspondente (palavras mais frequentes de cada comunidade)."""
    paleta = colorir(T, comunidades)
    cor = {n: CORES[paleta[c]] for c, g in enumerate(comunidades) for n in g}
    alcas = [plt.Line2D([], [], ls="", marker="o", ms=9, mfc=CORES[paleta[c]], mec="none") for c in range(len(comunidades))]
    nomes = [", ".join(sorted(g, key=lambda n: -freq[n])[:4]) + ("…" if len(g) > 4 else "") for g in comunidades]
    return cor, list(zip(alcas, nomes))

def desenhar(T, tam, path, titulo, subtitulo, seed, cor, legenda, legenda_titulo, forma=None, ncol=2):
    """Desenha a árvore T; tam dá a área dos nós e o corpo dos rótulos, cor e forma ('o' ou 'D') vêm prontas."""
    fonte = next((f for f in ("Liberation Sans", "DejaVu Sans")
                  if any(f == x.name for x in font_manager.fontManager.ttflist)), "sans-serif")
    plt.rcParams["font.family"] = fonte
    forma = forma or {}
    fmax = max(tam[n] for n in T)
    area = {n: 60 + 2400 * tam[n] / fmax for n in T}                # área do marcador em pontos² (∝ tam)
    diam = {n: area[n] ** 0.5 for n in T}
    corpo = {n: 8 + 9 * (tam[n] / fmax) ** 0.5 for n in T}          # tamanho da fonte do rótulo
    prop = FontProperties(family=fonte, weight="semibold")
    rot = {n: TextPath((0, 0), n, size=corpo[n], prop=prop).get_extents() for n in T}
    caixas = {n: (max(diam[n], rot[n].width) + 4, diam[n] + rot[n].height + 8) for n in T}
    centro = posicionar(T, caixas, seed)
    # o neato devolve o centro da caixa; o círculo fica embaixo e o rótulo em cima
    pos = {n: (x, y - caixas[n][1] / 2 / PT + (2 + diam[n] / 2) / PT) for n, (x, y) in centro.items()}

    xs = [centro[n][0] + s * caixas[n][0] / 2 / PT for n in T for s in (-1, 1)]
    ys = [centro[n][1] + s * caixas[n][1] / 2 / PT for n in T for s in (-1, 1)]
    larg, alt = max(xs) - min(xs), max(ys) - min(ys)
    m, topo, base = 0.4, 1.0, 0.25 + 0.22 * -(-len(legenda) // ncol) + 0.3
    fig = plt.figure(figsize=(max(larg + 2 * m, 10), alt + topo + base + m), dpi=200)
    W, H = fig.get_size_inches()
    ax = fig.add_axes([(W - larg) / 2 / W, base / H, larg / W, alt / H])   # 1 unidade de dados = 1 polegada
    ax.set_xlim(min(xs), max(xs)); ax.set_ylim(min(ys), max(ys)); ax.axis("off")
    fig.patch.set_facecolor(SUPERFICIE)

    pesos = [T[u][v]["weight"] for u, v in T.edges]
    wmin, wmax = min(pesos), max(pesos)
    nx.draw_networkx_edges(T, pos, ax=ax, edge_color=ARESTA,
                           width=[0.8 + 4.2 * (w - wmin) / ((wmax - wmin) or 1) for w in pesos])
    for f in sorted({forma.get(n, "o") for n in T}):
        ns = [n for n in T if forma.get(n, "o") == f]
        nx.draw_networkx_nodes(T, pos, nodelist=ns, ax=ax, node_color=[cor[n] for n in ns], node_shape=f,
                               node_size=[area[n] * (0.7 if f == "D" else 1) for n in ns],   # losango com área ≈ círculo
                               edgecolors=TEXTO if f == "D" else SUPERFICIE, linewidths=1.5 if f == "D" else 2)
    for n in T:
        ax.annotate(n, pos[n], xytext=(0, diam[n] / 2 + 2), textcoords="offset points", ha="center", va="bottom",
                    fontsize=corpo[n], color=TEXTO, fontweight="semibold", fontstyle="italic" if forma.get(n) == "D" else "normal",
                    bbox=dict(boxstyle="square,pad=0.05", fc=SUPERFICIE, ec="none", alpha=0.8))
    fig.legend(*zip(*legenda), title=legenda_titulo, loc="lower left",
               bbox_to_anchor=(m / W, 0.15 / H), ncol=ncol, frameon=False, fontsize=9, title_fontsize=9,
               labelcolor=TEXTO_2, alignment="left", columnspacing=2.5, handletextpad=0.4)
    fig.text(m / W, 1 - 0.3 / H, titulo, fontsize=16, fontweight="semibold", color=TEXTO, va="top")
    fig.text(m / W, 1 - 0.62 / H, subtitulo, fontsize=9.5, color=TEXTO_2, va="top", wrap=True)
    fig.savefig(path, facecolor=SUPERFICIE)
    plt.close(fig)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/entrevistas.db")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--falantes", choices=["entrevistados", "todos"], default="entrevistados")
    ap.add_argument("--unidade", choices=["frase", "turno"], default="frase")
    ap.add_argument("--indice", choices=["jaccard", "coocorrencia"], default="jaccard")
    ap.add_argument("--stopwords", default=os.path.join(AQUI, "stopwords_rede.txt"))
    ap.add_argument("--saida", default="figuras/rede_semantica")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    sql = "SELECT texto FROM turnos_analise" + (" WHERE papel = 'entrevistado'" if a.falantes == "entrevistados" else "")
    textos = [t for (t,) in sqlite3.connect(a.db).execute(sql + " ORDER BY transcricao_id, ordem")]
    nlp = spacy.load("pt_core_news_sm", disable=["ner"])
    us = list(unidades(textos, nlp, ler_stopwords(a.stopwords), a.unidade == "frase"))

    freq = Counter(l for u in us for l in u)
    topo = [w for w, _ in freq.most_common(a.n)]
    G, T, comunidades = construir_rede(us, topo, a.indice, a.seed)

    os.makedirs(os.path.dirname(a.saida) or ".", exist_ok=True)
    comunidade = {n: c + 1 for c, g in enumerate(comunidades) for n in g}
    with open(a.saida + "_nos.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["palavra", "frequencia", "comunidade", "grau_na_arvore"])
        w.writerows([n, freq[n], comunidade[n], T.degree(n)] for n in topo)
    with open(a.saida + "_arestas.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["origem", "destino", "coocorrencias", "jaccard", "na_arvore"])
        w.writerows(sorted(([u, v, d["coocorrencias"], d["jaccard"], int(T.has_edge(u, v))]
                            for u, v, d in G.edges(data=True)), key=lambda r: -r[3]))
    for n in G: G.nodes[n].update(frequencia=freq[n], comunidade=comunidade[n])
    nx.write_gexf(G, a.saida + ".gexf")

    quem = "entrevistados" if a.falantes == "entrevistados" else "entrevistados e entrevistador"
    titulo = f"Rede semântica das {a.n} palavras mais frequentes"
    subtitulo = (f"Falas dos {quem} nas 8 entrevistas do corpus principal ({len(us):,} {a.unidade}s com ao menos uma palavra). "
                 f"Tamanho = frequência; espessura = " +
                 ("índice de Jaccard" if a.indice == "jaccard" else f"nº de {a.unidade}s em comum") +
                 f"; árvore máxima de coocorrência na mesma {a.unidade}; cores = comunidades (Louvain).")
    subtitulo = subtitulo.replace(f"{len(us):,}", f"{len(us):,}".replace(",", "."))
    cor, legenda = legenda_comunidades(T, comunidades, freq)
    desenhar(T, freq, a.saida + ".png", titulo, subtitulo, a.seed, cor, legenda,
             "Comunidades (palavras mais frequentes de cada uma)")
    print(f"{len(us)} {a.unidade}s; {G.number_of_edges()} pares com coocorrência; {len(comunidades)} comunidades")
    for c, g in enumerate(comunidades, 1):
        print(f"  {c}: " + ", ".join(f"{n} ({freq[n]})" for n in sorted(g, key=lambda n: -freq[n])))
    print(f"figura: {a.saida}.png")

if __name__ == "__main__":
    main()
