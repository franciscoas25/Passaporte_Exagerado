import secrets

ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TAMANHO = 7


def gerar_public_code() -> str:
    """Gera um código aleatório de 7 caracteres."""
    return "".join(secrets.choice(ALFABETO) for _ in range(TAMANHO))


def gerar_public_code_unico(existe_no_banco) -> str:
    """
    existe_no_banco: função que recebe um código e retorna True/False
    se ele já está em uso.
    """
    for _ in range(10):
        codigo = gerar_public_code()
        if not existe_no_banco(codigo):
            return codigo
    raise RuntimeError("Não foi possível gerar um public_code único após 10 tentativas")