import json
from dataclasses import dataclass
from logging import log
from time import time

from anthropic import Anthropic


@dataclass
class CompileResult:
    ok: bool
    errors: list[str]


client = Anthropic()


def call_llm ( system : str , user : str , temperature : float = 0.7) -> str :
    """Una chiamata LLM , ritorna solo la stringa del testo ."""
    log = open("agent\\log.md", "a")
    response = client . messages . create(
        model =" claude - sonnet -4 -5",
        max_tokens =2048 ,
        system = system ,
        messages =[{" role ": " user ", " content ": user }] ,
        temperature = temperature ,
    )
    log.write(json.dumps({"Step":"create d'agent","Response": response.content[0].text, "Time" : time.time()}))
    return response . content [0]. text