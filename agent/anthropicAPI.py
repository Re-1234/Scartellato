from dataclasses import dataclass
from anthropic import Anthropic


@dataclass
class CompileResult:
    ok: bool
    errors: list[str]


client = Anthropic()


def call_llm ( system : str , user : str , temperature : float = 0.7) -> str :
    """Una chiamata LLM , ritorna solo la stringa del testo ."""
    response = client . messages . create (
        model =" claude - sonnet -4 -5",
        max_tokens =2048 ,
        system = system ,
        messages =[{" role ": " user ", " content ": user }] ,
        temperature = temperature ,
    )
    return response . content [0]. text



