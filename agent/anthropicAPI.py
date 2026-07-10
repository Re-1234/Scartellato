from dataclasses import dataclass
import subprocess
from anthropic import Anthropic
import re
import json, time

client = Anthropic()

def call_llm(system: str, user: str, temperature: float = 0.7)-> str:
    """Una chiamata LLM, ritorna solo la stringa del testo."""
    response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=2048,
    system=system,
    messages=[{"role": "user", "content": user}],
    temperature=temperature,
    )
    return response.content[0].texttent[0].text

@dataclass
class CompileResult:
    ok: bool
    errors: list[str]

def compile_program(source: str)-> CompileResult:
    """Compila un programma in L. Funzione PURA: stesso input, stesso output."""
    # opzione A: il compilatore e’ una libreria Python che avete scritto voi
    # from mycompiler import compile as _c
    # ok, errs = _c(source)
    # return CompileResult(ok=ok, errors=errs)
    #
    # opzione B: il compilatore e’ un eseguibile esterno

    r = subprocess.run(
    ["./mycompiler"], input=source, capture_output=True, text=True
    )
    return CompileResult(ok=(r.returncode == 0),
    errors=r.stderr.splitlines() if r.returncode != 0 else [])



def extract_code(raw: str)-> str:
    """Rimuove eventuali fence markdown e whitespace di troppo."""
    # rimuove ‘‘‘linguaggio ... ‘‘‘
    fenced = re.search(r"‘‘‘(?:\w+)?\n(.*?)‘‘‘", raw, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    return raw.strip()


with open("grammatica_L.lark", "r", encoding="utf-8") as file:
    GRAMMAR= file.read()
with open("few_example.md", "r", encoding="utf-8") as f:
    FEW_SHOT_EXAMPLES = f.read()

SYSTEM_GENERATOR = f"""Sei un generatore di programmi nel linguaggio L.
    GRAMMATICA: {GRAMMAR}
    ESEMPI VALIDI:
    {FEW_SHOT_EXAMPLES}
    Genera un programma valido in L. Rispondi SOLO con il codice."""


def generate_program()-> str:
    raw =call_llm(system=SYSTEM_GENERATOR,user="Genera un programma in L.",temperature=0.8)
    return extract_code(raw)

SYSTEM_REPAIR = f"""Sei un riparatore di programmi nel linguaggio scartellato.
    Ricevi un programma con errori e i messaggi del compilatore.
    Riscrivi il programma correggendo SOLO gli errori segnalati.
    Mantieni il piu’ possibile la struttura originale.
    GRAMMATICA:
    {GRAMMAR}
    Rispondi SOLO con il programma corretto."""

def repair_program(program: str, errors: list[str])-> str:
        user = f"PROGRAMMA:\n{program}\n\nERRORI:\n" + "\n".join(errors)
        raw = call_llm(system=SYSTEM_REPAIR, user=user, temperature=0.2)
        return extract_code(raw)

def generate_valid_program(max_repairs: int = 5)-> tuple[str | None, int]:
    """Genera un programma valido. Ritorna (programma, n_tentativi) o (None, N+1)."""
    program = generate_program()
    for attempt in range(max_repairs + 1):
        result = compile_program(program)
        if result.ok:
            return program, attempt + 1
        program = repair_program(program, result.errors)

    return None, max_repairs + 1


