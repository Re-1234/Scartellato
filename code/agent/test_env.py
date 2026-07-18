import os

print("ANTHROPIC_API_KEY presente?", "ANTHROPIC_API_KEY" in os.environ)
print("Tutte le chiavi che contengono ANTHROPIC:", [k for k in os.environ if "ANTHROPIC" in k.upper()])