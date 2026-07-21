"""
Parsing del file "Categori Partion" (raccolta di programmi di test scritti a mano,
divisi per categoria, ciascuno con codice sorgente + ORACOLO atteso).

Uso:
    from estrai_test_cases import estrai_test_cases
    tests = estrai_test_cases("Categori Partion.txt")

Ogni elemento restituito e' un dict:
    {
        "categoria": str,
        "nome": str,            # es. "Primo programma"
        "codice": str,          # sorgente del linguaggio da compilare
        "oracolo": str,         # output/errore atteso, testo libero
        "stato": str | None,    # "FUNZIONA" / "DA_FIXARE" / "PROBLEMA_RISOLTO" / None
        "note": str,            # eventuali note PROBLEMA/COREZIONE/DA FIXARE
    }
"""
import re

RE_CATEGORIA = re.compile(r'^Programmi che testano (.+?):?\s*$', re.IGNORECASE)
RE_HEADER = re.compile(
    r'^(primo|prima|secondo|seconda|terzo|terza|quarto|quarta|quinto|quinta)\s+programm[ai]?\s*:?\s*$',
    re.IGNORECASE
)
RE_ORACOLO = re.compile(r'^ORACOLO\s*:?\s*(.*)$', re.IGNORECASE)
RE_FINE = re.compile(r'^FINE\s*$', re.IGNORECASE)
RE_FUNZIONA = re.compile(r'^\(?\s*FUNZIONA\s*\)?$', re.IGNORECASE)
RE_PROBLEMA = re.compile(r'^PROBLEMA\s*:?\s*(.*)$', re.IGNORECASE)
RE_COREZIONE = re.compile(r'^CO?REZIONE\s*:?\s*(.*)$', re.IGNORECASE)
RE_DAFIXARE = re.compile(r'.*DA FIXARE.*', re.IGNORECASE)


def _pulisci_bordi(lines):
    """Rimuove righe vuote iniziali/finali da una lista di righe."""
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _finalizza_test(categoria, nome, buffer):
    """Data una lista di righe grezze appartenenti ad un test, separa
    codice sorgente / oracolo atteso / stato / note."""
    if nome is None:
        return None  # note/preamboli prima del primo header: non e' un test

    buffer = list(buffer)

    idx_oracolo = None
    for i, line in enumerate(buffer):
        if RE_ORACOLO.match(line.strip()):
            idx_oracolo = i
            break

    if idx_oracolo is not None:
        righe_codice = buffer[:idx_oracolo]
        righe_oracolo = buffer[idx_oracolo:]
    else:
        righe_codice = buffer
        righe_oracolo = []

    stato = None
    note = []
    righe_codice_pulite = []
    for line in righe_codice:
        s = line.strip()
        m_prob = RE_PROBLEMA.match(s)
        m_corr = RE_COREZIONE.match(s)
        if m_prob:
            note.append("PROBLEMA: " + m_prob.group(1))
            stato = stato or "PROBLEMA_RISOLTO"
            continue
        if m_corr:
            note.append("CORREZIONE: " + m_corr.group(1))
            continue
        if RE_DAFIXARE.match(s):
            stato = "DA_FIXARE"
            note.append(s)
            continue
        righe_codice_pulite.append(line)

    righe_oracolo_pulite = []
    for line in righe_oracolo:
        s = line.strip()
        if RE_FINE.match(s):
            continue
        if RE_FUNZIONA.match(s):
            stato = "FUNZIONA"
            continue
        if RE_DAFIXARE.match(s):
            stato = "DA_FIXARE"
            note.append(s)
            continue
        m = RE_ORACOLO.match(s)
        if m is not None and not righe_oracolo_pulite:
            # prima riga: toglie il prefisso "ORACOLO:"
            resto = m.group(1)
            if resto:
                righe_oracolo_pulite.append(resto)
            continue
        righe_oracolo_pulite.append(line)

    righe_codice_pulite = _pulisci_bordi(righe_codice_pulite)
    righe_oracolo_pulite = _pulisci_bordi(righe_oracolo_pulite)

    return {
        "categoria": categoria,
        "nome": nome,
        "codice": "\n".join(righe_codice_pulite),
        "oracolo": "\n".join(righe_oracolo_pulite).strip(),
        "stato": stato,
        "note": "\n".join(note),
    }


def estrai_test_cases(path):
    with open(path, "r", encoding="utf-8") as f:
        testo = f.read()

    lines = testo.split("\n")

    tests = []
    categoria_corrente = "Generale"
    nome_corrente = None
    buffer = []

    def chiudi_corrente():
        t = _finalizza_test(categoria_corrente, nome_corrente, buffer)
        if t is not None and (t["codice"].strip() or t["oracolo"].strip()):
            tests.append(t)

    for raw_line in lines:
        s = raw_line.strip()

        m_cat = RE_CATEGORIA.match(s)
        if m_cat:
            chiudi_corrente()
            categoria_corrente = m_cat.group(1).strip()
            nome_corrente = None
            buffer = []
            continue

        m_head = RE_HEADER.match(s)
        if m_head:
            chiudi_corrente()
            nome_corrente = s.rstrip(":").strip()
            buffer = []
            continue

        buffer.append(raw_line)

    chiudi_corrente()
    return tests