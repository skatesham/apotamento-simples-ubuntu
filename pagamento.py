#!/usr/bin/env python3

import csv
import os
import re
from datetime import datetime

VALOR_HORA_PADRAO = 113.63

FIELDNAMES = [
    "n",
    "tempo_total",
    "atividade",
    "data_inicio",
    "data_fim",
    "valor_hora",
    "valor",
    "pago",
    "valor_pago",
    "valor_pendente",
    "data_pagamento",
    "descricao_pagamento",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def listar_projetos() -> list[str]:
    projetos = []
    for nome in os.listdir(BASE_DIR):
        caminho = os.path.join(BASE_DIR, nome)
        if os.path.isfile(caminho) and nome.lower().endswith(".csv"):
            projetos.append(nome)
    return sorted(projetos)


def normalizar_nome_projeto(nome: str) -> str | None:
    nome = nome.strip().lower()
    if not nome:
        return None
    slug = re.sub(r"[^\w\-]+", "_", nome)
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug:
        return None
    if not slug.endswith(".csv"):
        slug = f"{slug}.csv"
    return slug


def solicitar_valor_hora(valor_sugerido: float | None = None) -> float:
    while True:
        prompt = "Valor-hora (R$): " if valor_sugerido is None else f"Valor-hora (R$) [{valor_sugerido:.2f}]: "
        resposta = input(prompt).strip()
        if not resposta:
            if valor_sugerido is not None:
                return round(valor_sugerido, 2)
            print("Informe um valor maior que zero.")
            continue
        try:
            valor = float(resposta.replace(",", "."))
        except ValueError:
            print("Valor inválido. Digite apenas números.")
            continue
        if valor <= 0:
            print("O valor deve ser maior que zero.")
            continue
        return round(valor, 2)


def _parse_float_moeda(valor: str | None) -> float:
    if not valor:
        return 0.0
    s = str(valor).strip()
    if not s:
        return 0.0
    s = s.replace("R$", "").strip()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _fmt_2(v: float) -> str:
    return f"{v:.2f}"


def formatar_reais(valor: float) -> str:
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {texto}"


def ler_valor_hora_no_arquivo(filename: str) -> float | None:
    if not os.path.isfile(filename):
        return None
    with open(filename, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        if not reader.fieldnames or "valor_hora" not in reader.fieldnames:
            return None
        for row in reader:
            bruto = row.get("valor_hora")
            if not bruto:
                continue
            try:
                return float(str(bruto).replace(",", "."))
            except ValueError:
                continue
    return None


def sincronizar_layout_csv(filename: str, valor_hora_padrao: float | None = None):
    if not os.path.isfile(filename):
        return

    with open(filename, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        registros = list(reader)
        cabecalho = reader.fieldnames or []

    precisa_coluna = cabecalho != FIELDNAMES
    precisa_completar_valor_hora = any(not str(reg.get("valor_hora", "")).strip() for reg in registros)

    if not precisa_coluna and not (precisa_completar_valor_hora and valor_hora_padrao is not None):
        return

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()

        for row in registros:
            valor_hora_atual = str(row.get("valor_hora", "") or "").strip()
            if not valor_hora_atual and valor_hora_padrao is not None:
                valor_hora_atual = f"{valor_hora_padrao:.2f}"

            valor = row.get("valor", "")
            pago = row.get("pago", "")

            valor_pago = row.get("valor_pago", "")
            valor_pendente = row.get("valor_pendente", "")
            data_pag = row.get("data_pagamento", "")
            desc_pag = row.get("descricao_pagamento", "")

            if str(pago).strip().lower() == "parcial" and not str(valor_pendente).strip():
                total = _parse_float_moeda(valor)
                ja = _parse_float_moeda(valor_pago)
                pend = max(total - ja, 0.0)
                valor_pendente = _fmt_2(pend) if pend > 0 else "0.00"

            writer.writerow(
                {
                    "n": row.get("n", ""),
                    "tempo_total": row.get("tempo_total", ""),
                    "atividade": row.get("atividade", ""),
                    "data_inicio": row.get("data_inicio", ""),
                    "data_fim": row.get("data_fim", ""),
                    "valor_hora": valor_hora_atual,
                    "valor": valor,
                    "pago": pago,
                    "valor_pago": valor_pago,
                    "valor_pendente": valor_pendente,
                    "data_pagamento": data_pag,
                    "descricao_pagamento": desc_pag,
                }
            )


def obter_valor_hora_projeto(filename: str) -> float:
    valor_existente = ler_valor_hora_no_arquivo(filename)
    if valor_existente is not None:
        sincronizar_layout_csv(filename, valor_existente)
        return valor_existente

    print("\nEste projeto ainda não possui um valor-hora definido. Informe o valor que será usado para todos os lançamentos.")
    valor = solicitar_valor_hora(VALOR_HORA_PADRAO)
    sincronizar_layout_csv(filename, valor)
    return valor


def criar_novo_projeto() -> tuple[str, float]:
    print("\n--- Criar novo projeto ---")
    while True:
        nome_digitado = input("Nome do projeto: ").strip()
        arquivo = normalizar_nome_projeto(nome_digitado)
        if not arquivo:
            print("Nome inválido. Use letras, números, '-' ou '_'.")
            continue

        caminho = os.path.join(BASE_DIR, arquivo)
        if os.path.exists(caminho):
            print("Já existe um projeto com esse nome. Escolha outro.")
            continue

        valor_hora = solicitar_valor_hora(VALOR_HORA_PADRAO)

        with open(caminho, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()

        print(f"Projeto criado: {arquivo}")
        return caminho, valor_hora


def selecionar_ou_criar_projeto() -> tuple[str, float]:
    while True:
        projetos = listar_projetos()
        if projetos:
            print("\n=== Projetos disponíveis ===")
            for idx, nome in enumerate(projetos, start=1):
                print(f"{idx}. {nome}")
            print(f"{len(projetos) + 1}. Criar novo projeto")

            escolha = input("Selecione uma opção: ").strip()
            if not escolha.isdigit():
                print("Informe o número da opção.")
                continue

            indice = int(escolha)
            if 1 <= indice <= len(projetos):
                arquivo = projetos[indice - 1]
                caminho = os.path.join(BASE_DIR, arquivo)
                print(f"\nProjeto selecionado: {arquivo}")
                valor_hora = obter_valor_hora_projeto(caminho)
                return caminho, valor_hora
            if indice == len(projetos) + 1:
                return criar_novo_projeto()

            print("Opção inválida. Tente novamente.")
        else:
            print("\nNenhum projeto encontrado. Vamos criar o primeiro agora.")
            return criar_novo_projeto()


def _ler_registros(filename: str) -> list[dict]:
    if not os.path.isfile(filename):
        return []
    with open(filename, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def _escrever_registros_atomic(filename: str, registros: list[dict]):
    tmp = f"{filename}.tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in registros:
            writer.writerow({k: row.get(k, "") for k in FIELDNAMES})
    os.replace(tmp, filename)


def _saldo_pendente(registros: list[dict]) -> float:
    saldo = 0.0
    for r in registros:
        status = str(r.get("pago", "")).strip().lower()
        if status == "sim":
            continue
        if status == "parcial":
            saldo += _parse_float_moeda(r.get("valor_pendente"))
        else:
            saldo += _parse_float_moeda(r.get("valor"))
    return round(saldo, 2)


def _append_historico(row: dict, data_str: str, desc: str, valor_aplicado: float):
    linha = f"{data_str} | {desc} | {_fmt_2(valor_aplicado)}"
    atual_d = str(row.get("data_pagamento", "") or "").strip()
    atual_t = str(row.get("descricao_pagamento", "") or "").strip()

    # data_pagamento: lista de datas
    if atual_d:
        row["data_pagamento"] = atual_d + " ; " + data_str
    else:
        row["data_pagamento"] = data_str

    # descricao_pagamento: histórico textual com valor aplicado
    if atual_t:
        row["descricao_pagamento"] = atual_t + " || " + linha
    else:
        row["descricao_pagamento"] = linha


def consultar_saldo(filename: str):
    sincronizar_layout_csv(filename, ler_valor_hora_no_arquivo(filename) or None)
    registros = _ler_registros(filename)
    saldo = _saldo_pendente(registros)

    print("\nPendências:")
    print("-" * 60)
    print(f"Projeto        : {os.path.basename(filename)}")
    print(f"Saldo pendente : {formatar_reais(saldo)}")

    proximo = None
    for r in registros:
        st = str(r.get("pago", "")).strip().lower()
        if st == "sim":
            continue
        proximo = r
        break

    if proximo:
        st = str(proximo.get("pago", "")).strip()
        v = _parse_float_moeda(proximo.get("valor"))
        pend = _parse_float_moeda(proximo.get("valor_pendente"))
        alvo = pend if st.lower() == "parcial" else v
        print("-" * 60)
        print("Próximo a quitar:")
        print(f"ID (n)     : {proximo.get('n','')}")
        print(f"Status     : {st or 'Não'}")
        print(f"Atividade  : {proximo.get('atividade','')}")
        print(f"Valor alvo : {formatar_reais(alvo)}")
    print("-" * 60)


def solicitar_valor_pagamento() -> float:
    while True:
        bruto = input("Valor do pagamento (R$): ").strip()
        v = _parse_float_moeda(bruto)
        if v <= 0:
            print("Informe um valor maior que zero.")
            continue
        return round(v, 2)


def solicitar_data_pagamento() -> str:
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    while True:
        s = input(f"Data do pagamento [{agora}]: ").strip()
        if not s:
            return agora
        # aceita YYYY-MM-DD ou YYYY-MM-DD HH:MM[:SS]
        try:
            if len(s) == 10:
                datetime.strptime(s, "%Y-%m-%d")
                return s + " 00:00:00"
            if len(s) == 16:
                datetime.strptime(s, "%Y-%m-%d %H:%M")
                return s + ":00"
            datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
            return s
        except ValueError:
            print("Formato inválido. Use: YYYY-MM-DD ou YYYY-MM-DD HH:MM[:SS].")


def solicitar_descricao_pagamento() -> str:
    while True:
        d = input("Descrição do pagamento (ex: Pix, NF 123, referência): ").strip()
        if d:
            return d
        print("Descrição obrigatória.")


def efetivar_pagamento(filename: str):
    sincronizar_layout_csv(filename, ler_valor_hora_no_arquivo(filename) or None)
    registros = _ler_registros(filename)

    saldo_antes = _saldo_pendente(registros)
    if saldo_antes <= 0:
        print("\nNada a pagar. Saldo pendente é zero.")
        return

    print("\n=== Efetivar Pagamento ===")
    print(f"Saldo atual: {formatar_reais(saldo_antes)}")

    data_pag = solicitar_data_pagamento()
    desc_pag = solicitar_descricao_pagamento()
    valor_pag = solicitar_valor_pagamento()

    if valor_pag > saldo_antes:
        print("\nObs: pagamento maior que o saldo. Excedente será ignorado.")
        valor_pag = saldo_antes

    print("\nPrévia:")
    print("-" * 60)
    print(f"Data            : {data_pag}")
    print(f"Descrição       : {desc_pag}")
    print(f"Pagamento       : {formatar_reais(valor_pag)}")
    print(f"Saldo antes     : {formatar_reais(saldo_antes)}")

    pagamento_restante = valor_pag
    quitados = 0
    parcial_info = None

    for r in registros:
        st_raw = str(r.get("pago", "") or "").strip()
        st = st_raw.lower()

        if st == "sim":
            continue

        total = _parse_float_moeda(r.get("valor"))
        ja_pago = _parse_float_moeda(r.get("valor_pago"))
        pendente = _parse_float_moeda(r.get("valor_pendente"))

        if st == "parcial":
            alvo = pendente if pendente > 0 else max(total - ja_pago, 0.0)
        else:
            alvo = total

        alvo = round(alvo, 2)
        if alvo <= 0:
            r["pago"] = "Sim"
            r["valor_pago"] = _fmt_2(total if total > 0 else ja_pago)
            r["valor_pendente"] = "0.00"
            continue

        if pagamento_restante + 1e-9 >= alvo:
            pagamento_restante = round(pagamento_restante - alvo, 2)

            r["pago"] = "Sim"
            r["valor_pago"] = _fmt_2(total)
            r["valor_pendente"] = "0.00"

            _append_historico(r, data_pag, desc_pag, alvo)

            quitados += 1
            if pagamento_restante <= 0:
                break
        else:
            pago_agora = round(pagamento_restante, 2)
            novo_pendente = round(alvo - pago_agora, 2)

            if st == "parcial":
                novo_valor_pago = round(total - novo_pendente, 2)
            else:
                novo_valor_pago = round(pago_agora, 2)

            r["pago"] = "Parcial"
            r["valor_pago"] = _fmt_2(novo_valor_pago)
            r["valor_pendente"] = _fmt_2(novo_pendente)

            _append_historico(r, data_pag, desc_pag, pago_agora)

            parcial_info = {"n": r.get("n", ""), "pendente": novo_pendente}
            pagamento_restante = 0.0
            break

    saldo_depois = _saldo_pendente(registros)
    print(f"Saldo depois    : {formatar_reais(saldo_depois)}")
    print(f"Itens quitados  : {quitados}")
    if parcial_info:
        print(f"Parcial em (n)  : {parcial_info['n']}")
        print(f"Pendente        : {formatar_reais(parcial_info['pendente'])}")
    print("-" * 60)

    resp = input("Confirmar gravação? (s/n): ").strip().lower()
    if resp != "s":
        print("Operação cancelada. Nenhum dado foi salvo.")
        return

    _escrever_registros_atomic(filename, registros)
    print("\n✅ Pagamento registrado.")
    consultar_saldo(filename)


def menu_principal(filename: str):
    while True:
        print("\n=== Menu Pagamentos ===")
        print("1. Consultar saldo")
        print("2. Efetivar pagamento")
        print("3. Sair")
        op = input("Escolha: ").strip()

        if op == "1":
            consultar_saldo(filename)
        elif op == "2":
            efetivar_pagamento(filename)
        elif op == "3":
            return
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    arquivo_projeto, _valor_hora = selecionar_ou_criar_projeto()
    menu_principal(arquivo_projeto)