#!/usr/bin/env python3

import csv
import os
import re
from datetime import datetime, timedelta

# Valor-hora configurável (R$ por hora trabalhada)
VALOR_HORA = 113.63  # ajuste conforme necessário

LIMITE_ALERTA_MINUTOS = 5 * 60

FIELDNAMES = [
    "n",
    "tempo_total",
    "atividade",
    "data_inicio",
    "data_fim",
    "valor",
    "pago",
]

COMPONENTE_TEMPO_REGEX = re.compile(r"(\d+(?:[.,]\d+)?)([hm])", re.IGNORECASE)


def converter_para_minutos(valor: str | None) -> int | None:
    if not valor:
        return None

    compactado = valor.strip().lower().replace(" ", "")
    posicao = 0
    total_minutos = 0.0

    for match in COMPONENTE_TEMPO_REGEX.finditer(compactado):
        if match.start() != posicao:
            return None  # caractere inesperado entre componentes

        numero_bruto, unidade = match.groups()
        numero_normalizado = numero_bruto.replace(",", ".")

        try:
            quantidade = float(numero_normalizado)
        except ValueError:
            return None

        if unidade.lower() == "h":
            total_minutos += quantidade * 60
        else:
            total_minutos += quantidade

        posicao = match.end()

    if posicao != len(compactado):
        return None  # sobrou caractere não reconhecido

    minutos_inteiros = int(round(total_minutos))
    return minutos_inteiros if minutos_inteiros > 0 else None


def formatar_tempo(minutos: int) -> str:
    horas, resto = divmod(minutos, 60)
    partes = []
    if horas:
        partes.append(f"{horas}h")
    if resto:
        partes.append(f"{resto}m")
    if not partes:
        partes.append("0m")
    return "".join(partes)


def formatar_reais(valor: float) -> str:
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {texto}"


def solicitar_confirmacao_alerta(minutos: int) -> bool:
    horas = minutos / 60
    print(f"\n⚠️  Alerta: tempo informado equivale a {horas:.2f}h (> 5h).")
    resposta = input("Confirmar mesmo assim? (s/n): ").strip().lower()
    return resposta == "s"


def solicitar_tempo():
    while True:
        tempo_digitado = input("Tempo (ex: 30m, 1h30m, 2h): ").strip()
        minutos = converter_para_minutos(tempo_digitado)
        if minutos is None:
            print("Tempo inválido. Use combinações como '1h30m', '45m' ou '2h'.")
            continue

        if minutos > LIMITE_ALERTA_MINUTOS and not solicitar_confirmacao_alerta(minutos):
            print("Tempo descartado. Informe novamente.")
            continue

        return formatar_tempo(minutos), minutos

def proximo_id(filename: str) -> int:
    if not os.path.isfile(filename):
        return 1

    try:
        with open(filename, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            ultimo = 0
            for row in reader:
                try:
                    ultimo = max(ultimo, int(row.get("n", 0)))
                except (TypeError, ValueError):
                    continue
            return ultimo + 1
    except FileNotFoundError:
        return 1


def imprimir_resumo(registro: dict, titulo: str = "Registro salvo", mostrar_pago: bool = True):
    print(f"\n{titulo}:")
    print("-" * 40)
    print(f"ID (n)      : {registro['n']}")
    print(f"Atividade   : {registro['atividade']}")
    print(f"Tempo total : {registro['tempo_total']}")
    print(f"Início      : {registro['data_inicio']}")
    print(f"Fim         : {registro['data_fim']}")
    print(f"Valor (R$)  : {formatar_reais(float(registro['valor']))}")
    if mostrar_pago:
        print(f"Pago        : {registro['pago']}")
    print("-" * 40)


def calcular_totais_nao_pagos(filename: str) -> tuple[int, float]:
    if not os.path.isfile(filename):
        return 0, 0.0

    total_minutos = 0
    total_valor = 0.0

    with open(filename, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if str(row.get("pago", "")).strip().lower() == "sim":
                continue

            tempo = row.get("tempo_total")
            minutos = converter_para_minutos(tempo)
            if minutos:
                total_minutos += minutos

            try:
                valor = float(str(row.get("valor", "0")).replace(",", "."))
            except ValueError:
                valor = 0.0
            total_valor += valor

    return total_minutos, total_valor


def mostrar_totais_nao_pagos(filename: str):
    total_minutos, total_valor = calcular_totais_nao_pagos(filename)
    print("\nPendências:")
    print("-" * 40)
    print(f"Total horas não pagas: {formatar_tempo(total_minutos)}")
    print(f"Total não pago      : {formatar_reais(total_valor)}")
    print("-" * 40)


def confirmar_registro(registro: dict) -> bool:
    imprimir_resumo(registro, "Pré-visualização do registro", mostrar_pago=False)
    resposta = input("Confirmar gravação? (s/n): ").strip().lower()
    return resposta == "s"


def add_to_csv():
    print("\n=== Novo Apontamento de Horas ===")
    atividade = input("Atividade: ").strip()
    if not atividade:
        print("Descrição obrigatória. Operação cancelada.")
        return
    tempo_label, minutos = solicitar_tempo()

    fim = datetime.now()
    inicio = fim - timedelta(minutes=minutos)
    valor_calculado = (minutos / 60) * VALOR_HORA
    filename = "apontamentos.csv"
    registro = {
        "n": str(proximo_id(filename)),
        "tempo_total": tempo_label,
        "atividade": atividade,
        "data_inicio": inicio.strftime("%Y-%m-%d %H:%M:%S"),
        "data_fim": fim.strftime("%Y-%m-%d %H:%M:%S"),
        "valor": f"{valor_calculado:.2f}",
        "pago": "Não",
    }
    if not confirmar_registro(registro):
        print("Operação cancelada. Nenhum dado foi salvo.")
        return
    file_exists = os.path.isfile(filename)

    with open(filename, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(registro)

    print(f"\n✅ Apontamento salvo em {filename}")
    mostrar_totais_nao_pagos(filename)

if __name__ == "__main__":
    add_to_csv()
