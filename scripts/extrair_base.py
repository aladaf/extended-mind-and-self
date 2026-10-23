#!/usr/bin/env python3
"""
Monta a base local das entrevistas a partir dos .docx e .pdf da pasta do projeto no Drive.

Três formatos de transcrição convivem na pasta:
  rotulada    "eduardo.madella 00:04" ou "Isabela 00:00" numa linha, a fala nas linhas seguintes (8 arquivos);
  sem_rotulo  só " 00:03" antes de cada fala, sem indicar quem fala (Ben-Hur);
  legenda     blocos "00:00:35.000 --> 00:00:39.000" sem falante (o arquivo com nome de "Rodrigo" e sobrenome, que é
              uma segunda transcrição da entrevista de Lucas).
O texto das falas é gravado como está no .docx, sem corrigir pontuação nem grafia.
Os .pdf da pasta são literatura, não corpus: só viram texto em <out>/referencias/, fora da base.

Uso:
  python scripts/extrair_base.py [--drive <pasta>] [--out data]
Saída: <out>/entrevistas.db (SQLite com busca FTS5), <out>/turnos.csv,
       <out>/transcricoes/<id>.md, <out>/referencias/<id>.txt
"""
import argparse, csv, datetime as dt, glob, hashlib, os, re, shutil, sqlite3, unicodedata
import docx, fitz

DRIVE = os.environ.get("EMS_DRIVE", "/mnt/g/My Drive/COPPEAD/Papers/extended-mind-and-self")
ENTREVISTADOR = "eduardo.madella"

# Correções que a leitura dos arquivos mostrou serem necessárias (ver STATUS.md).
ARQUIVOS = {
    "PhD Paper 1 Entrevista Rodrigo ": dict(   # prefixo: o nome no Drive tem o sobrenome, que não vai para o código
        id="lucas-legenda", participante="Lucas", principal=0,
        observacao="Segunda transcrição da entrevista de Lucas (o cabeçalho traz o nome dele); o arquivo está "
                   "nomeado como 'Rodrigo' no Drive. Segmentos de legenda, sem falante."),
    "PhD Paper 1 Entrevista Ben-Hur.docx": dict(
        principal=0, data_gravacao="2025-12-16",
        observacao="Tratada em separado, fora do corpus principal (decisão de 23/10/2026). Transcrição sem rótulo "
                   "de falante. Data de gravação dita na abertura e no nome da gravação (GMT20251216-235038); "
                   "o cabeçalho traz 18/12, provavelmente a data da transcrição."),
    "PhD Paper 1 Entrevista Rodrigo.docx": dict(
        data_gravacao="2026-01-23",
        observacao="Data de gravação dita pelo entrevistado aos 53:55 ('hoje, Rodrigo, 23/01'); o cabeçalho traz 29/01."),
    "PhD Paper 1 Entrevista Mafe.docx": dict(
        observacao="Um turno rotulado 'Speaker 3' (24:06) é pergunta do entrevistador e foi marcado como tal."),
}
PAPEL_FORCADO = {("mafe", "Speaker 3"): "entrevistador"}
REFERENCIAS = {"10.1093/jcr/ucaf014": dict(id="epp-humphreys-2025", autores="Amber M. Epp; Ashlee Humphreys",
                                           periodico="Journal of Consumer Research", ano=2025)}

RE_ROTULO = re.compile(r"^(?:(\S+|Speaker \d+) )?(\d{1,2}:\d{2}(?::\d{2})?)$")
RE_LEGENDA = re.compile(r"^(\d{2}:\d{2}:\d{2})\.\d{3} --> (\d{2}:\d{2}:\d{2})\.\d{3}$")
RE_CABECALHO = re.compile(r"^⏰(\w{3}), (\d{2})/(\d{2}) (\d{1,2}:\d{2})\w* · (\d+)mins$")

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def segundos(hms):
    s = 0
    for parte in hms.split(":"): s = s * 60 + int(parte)
    return s

def hms(seg):
    h, r = divmod(seg, 3600); m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def palavras(t):
    return len(re.findall(r"\w+", t))

def sha256(path):
    with open(path, "rb") as f: return hashlib.sha256(f.read()).hexdigest()

def ano_pelo_dia_da_semana(dia_semana, mes, dia):
    """O cabeçalho '⏰Thu, 01/29 14:51PM' não traz o ano; fica o único ano de 2024 a 2027 que bate com o dia da semana."""
    anos = [a for a in range(2024, 2028) if dt.date(a, mes, dia).strftime("%a") == dia_semana]
    if len(anos) != 1: raise ValueError(f"ano ambíguo para {dia_semana} {dia}/{mes}: {anos}")
    return anos[0]

def juntar(linhas):
    return re.sub(r"\n{3,}", "\n\n", "\n\n".join(l.strip() for l in linhas)).strip()

def ler_docx(path):
    """Devolve (metadados, turnos); cada turno é dict(rotulo, inicio_seg, fim_seg, texto)."""
    ps = [p.text for p in docx.Document(path).paragraphs if p.text.strip()]
    meta, turnos = {"titulo": ps[0].strip()}, []
    if any(RE_LEGENDA.match(p.strip()) for p in ps[:5]):
        meta["formato"] = "legenda"
        corpo = ps[next(i for i, p in enumerate(ps) if RE_LEGENDA.match(p.strip())):]
        meta["titulo"] = " / ".join(p.strip() for p in ps[:len(ps) - len(corpo)])
        for p in corpo:
            m = RE_LEGENDA.match(p.strip())
            if m: turnos.append(dict(rotulo=None, inicio_seg=segundos(m[1]), fim_seg=segundos(m[2]), linhas=[]))
            else: turnos[-1]["linhas"].append(p)
    else:
        m = RE_CABECALHO.match(ps[1].strip())
        if not m or ps[2].strip() != "Transcript": raise ValueError(f"cabeçalho inesperado em {path}: {ps[:3]}")
        mes, dia = int(m[2]), int(m[3])
        meta["data_cabecalho"] = dt.date(ano_pelo_dia_da_semana(m[1], mes, dia), mes, dia).isoformat()
        meta["hora_cabecalho"], meta["duracao_min"] = m[4], int(m[5])
        for p in ps[3:]:
            m = RE_ROTULO.match(p.strip())
            if m: turnos.append(dict(rotulo=m[1], inicio_seg=segundos(m[2]), fim_seg=None, linhas=[]))
            else: turnos[-1]["linhas"].append(p)
        meta["formato"] = "rotulada" if any(t["rotulo"] for t in turnos) else "sem_rotulo"
    for t in turnos: t["texto"] = juntar(t.pop("linhas"))
    vazios = [hms(t["inicio_seg"]) for t in turnos if not t["texto"]]
    if vazios: print(f"  aviso: {len(vazios)} turno(s) sem texto em {os.path.basename(path)}: {vazios}")
    return meta, turnos

def papel(tid, participante, rotulo):
    if (tid, rotulo) in PAPEL_FORCADO: return PAPEL_FORCADO[(tid, rotulo)]
    if rotulo == ENTREVISTADOR: return "entrevistador"
    if rotulo and slug(rotulo) == slug(participante): return "entrevistado"
    return None

def ler_pdf(path):
    doc = fitz.open(path)
    paginas = [p.get_text().replace("\xad\n", "").replace("\xad", "") for p in doc]
    m = re.search(r"10\.\d{4,}/[^\s\xa0]+", (doc.metadata.get("subject") or "") + paginas[0])
    doi = m[0] if m else None
    ref = dict(titulo=doc.metadata.get("title") or None, doi=doi, **REFERENCIAS.get(doi, {}))
    ref.setdefault("id", slug(os.path.splitext(os.path.basename(path))[0]))
    return ref, paginas

ESQUEMA = """
CREATE TABLE meta (chave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE transcricoes (
  id TEXT PRIMARY KEY,            -- slug do participante; 'lucas-legenda' para a segunda transcrição
  participante TEXT NOT NULL,     -- primeiro nome, como no nome do arquivo no Drive
  principal INTEGER NOT NULL,     -- 1 = corpus principal (8 entrevistas); 0 = Ben-Hur (em separado) e lucas-legenda (duplicata)
  arquivo TEXT NOT NULL, sha256 TEXT NOT NULL,
  formato TEXT NOT NULL,          -- rotulada | sem_rotulo | legenda
  titulo TEXT,                    -- primeira(s) linha(s) do documento
  data_cabecalho TEXT,            -- data da linha '⏰' (ano inferido pelo dia da semana); pode ser a da transcrição
  hora_cabecalho TEXT, duracao_min INTEGER,
  data_gravacao TEXT,             -- só quando a própria gravação ou fala a informa
  n_turnos INTEGER, n_palavras INTEGER, n_palavras_entrevistado INTEGER,
  observacao TEXT
);
CREATE TABLE turnos (
  id INTEGER PRIMARY KEY,
  transcricao_id TEXT NOT NULL REFERENCES transcricoes(id),
  ordem INTEGER NOT NULL,
  rotulo TEXT,                    -- falante como aparece no arquivo
  papel TEXT,                     -- entrevistador | entrevistado | NULL (sem rótulo)
  inicio_seg INTEGER, fim_seg INTEGER,
  texto TEXT NOT NULL, n_palavras INTEGER NOT NULL
);
CREATE INDEX turnos_transcricao ON turnos(transcricao_id, ordem);
CREATE VIRTUAL TABLE turnos_fts USING fts5(texto, content='turnos', content_rowid='id',
                                           tokenize='unicode61 remove_diacritics 2');
CREATE VIEW turnos_analise AS
  SELECT t.*, r.participante FROM turnos t JOIN transcricoes r ON r.id = t.transcricao_id WHERE r.principal = 1;
"""

def escrever_md(path, r, turnos):
    cab = [f"# {r['participante']}" + ("" if r["principal"] else " (fora do corpus principal)"), "",
           f"- Arquivo: {r['arquivo']}", f"- Formato: {r['formato']}"]
    if r.get("data_cabecalho"): cab.append(f"- Cabeçalho: {r['data_cabecalho']} {r['hora_cabecalho']}, {r['duracao_min']} min")
    if r.get("data_gravacao"): cab.append(f"- Gravação: {r['data_gravacao']}")
    if r.get("observacao"): cab.append(f"- Observação: {r['observacao']}")
    corpo = []
    for t in turnos:
        quem = {"entrevistador": "Entrevistador", "entrevistado": r["participante"]}.get(t["papel"], t["rotulo"] or "?")
        corpo.append(f"**[{hms(t['inicio_seg'])}] {quem}:** {t['texto']}")
    with open(path, "w", encoding="utf-8") as f: f.write("\n".join(cab) + "\n\n" + "\n\n".join(corpo) + "\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drive", default=DRIVE); ap.add_argument("--out", default="data")
    a = ap.parse_args()
    db_path = os.path.join(a.out, "entrevistas.db")
    for d in ("transcricoes", "referencias"): shutil.rmtree(os.path.join(a.out, d), ignore_errors=True)
    os.makedirs(os.path.join(a.out, "transcricoes")); os.makedirs(os.path.join(a.out, "referencias"))
    if os.path.exists(db_path): os.remove(db_path)
    con = sqlite3.connect(db_path); con.executescript(ESQUEMA)
    con.executemany("INSERT INTO meta VALUES (?, ?)", [
        ("origem", a.drive), ("extraido_em", dt.datetime.now().isoformat(timespec="seconds")),
        ("script", "scripts/extrair_base.py")])

    linhas_csv = []
    for path in sorted(glob.glob(os.path.join(a.drive, "*.docx"))):
        arq = os.path.basename(path)
        m = re.match(r"PhD Paper 1 Entrevista (.+)\.docx$", arq)
        if not m: print(f"  ignorado (nome fora do padrão): {arq}"); continue
        r = {"participante": m[1], "principal": 1, **next((v for k, v in ARQUIVOS.items() if arq.startswith(k)), {})}
        r.setdefault("id", slug(r["participante"]))
        meta, turnos = ler_docx(path)
        r.update(meta, arquivo=arq, sha256=sha256(path))
        for i, t in enumerate(turnos, 1):
            t.update(ordem=i, papel=papel(r["id"], r["participante"], t["rotulo"]), n_palavras=palavras(t["texto"]))
            if t["rotulo"] and not t["papel"]: print(f"  aviso: rótulo sem papel em {arq}: {t['rotulo']!r}")
        r["n_turnos"], r["n_palavras"] = len(turnos), sum(t["n_palavras"] for t in turnos)
        r["n_palavras_entrevistado"] = sum(t["n_palavras"] for t in turnos if t["papel"] == "entrevistado") \
            if r["formato"] == "rotulada" else None
        cols = [c for c in ("id", "participante", "principal", "arquivo", "sha256", "formato", "titulo", "data_cabecalho",
                            "hora_cabecalho", "duracao_min", "data_gravacao", "n_turnos", "n_palavras",
                            "n_palavras_entrevistado", "observacao") if c in r]
        con.execute(f"INSERT INTO transcricoes ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", [r[c] for c in cols])
        con.executemany("INSERT INTO turnos (transcricao_id, ordem, rotulo, papel, inicio_seg, fim_seg, texto, n_palavras) "
                        "VALUES (?,?,?,?,?,?,?,?)", [(r["id"], t["ordem"], t["rotulo"], t["papel"], t["inicio_seg"],
                                                      t["fim_seg"], t["texto"], t["n_palavras"]) for t in turnos])
        escrever_md(os.path.join(a.out, "transcricoes", f"{r['id']}.md"), r, turnos)
        linhas_csv += [dict(transcricao_id=r["id"], participante=r["participante"], principal=r["principal"],
                            **{k: t[k] for k in ("ordem", "rotulo", "papel", "inicio_seg", "fim_seg", "n_palavras", "texto")})
                       for t in turnos]
        print(f"{r['id']:15} {r['formato']:10} {r['n_turnos']:4} turnos {r['n_palavras']:6} palavras")

    for path in sorted(glob.glob(os.path.join(a.drive, "*.pdf"))):
        ref, paginas = ler_pdf(path)
        cab = " | ".join(str(v) for v in (ref.get("autores"), ref.get("ano"), ref["titulo"], ref.get("periodico"),
                                          ref["doi"] and f"doi {ref['doi']}", os.path.basename(path)) if v)
        with open(os.path.join(a.out, "referencias", f"{ref['id']}.txt"), "w", encoding="utf-8") as f:
            f.write(cab + "".join(f"\n\n=== página {i} ===\n\n{t}" for i, t in enumerate(paginas, 1)))
        print(f"{ref['id']:15} pdf        {len(paginas):4} páginas")

    con.execute("INSERT INTO turnos_fts(turnos_fts) VALUES ('rebuild')")
    con.commit(); con.close()
    with open(os.path.join(a.out, "turnos.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas_csv[0])); w.writeheader(); w.writerows(linhas_csv)
    print(f"base: {db_path}")

if __name__ == "__main__":
    main()
