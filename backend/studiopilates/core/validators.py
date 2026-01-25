import re


def validar_cpf(cpf: str) -> bool:
    if not cpf:
        return False
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False

    def calc_digit(digs):
        s = sum(int(d) * f for d, f in zip(digs, range(len(digs) + 1, 1, -1)))
        r = (s * 10) % 11
        return 0 if r == 10 else r

    d1 = calc_digit(cpf[:9])
    d2 = calc_digit(cpf[:9] + str(d1))
    return cpf[-2:] == f"{d1}{d2}"
