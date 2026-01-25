from studiopilates.core.validators import validar_cpf


def test_validar_cpf_valido():
    assert validar_cpf("529.982.247-25")


def test_validar_cpf_invalido():
    assert not validar_cpf("111.111.111-11")
