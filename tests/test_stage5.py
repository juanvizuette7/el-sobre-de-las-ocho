"""Pruebas acotadas de las demostraciones de seguridad de etapa 5."""

from scripts.demo_sql_injection import demostrar


def test_sql_injection_solo_altera_consulta_concatenada():
    resultado = demostrar("' OR '1'='1' --")
    assert resultado["consulta_insegura"] == ["docente_demo", "estudiante_demo"]
    assert resultado["consulta_parametrizada"] == []


def test_consulta_parametrizada_trata_entrada_normal_como_dato():
    resultado = demostrar("estudiante_demo")
    assert resultado["consulta_insegura"] == ["estudiante_demo"]
    assert resultado["consulta_parametrizada"] == ["estudiante_demo"]
