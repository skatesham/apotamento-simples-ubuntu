# Apontamento de Horas

Script CLI para coletar rápida­mente horas trabalhadas e salvá-las em `apontamentos.csv`.

## Começando rápido

```bash
chmod +x apontamento_horas.py
./apontamento_horas.py
```

Sempre informe:

1. **Atividade** – breve descrição (obrigatório)
2. **Tempo** – use `Xm`, `Yh` ou combinações (`1h30m`, `45m`, `2h15m`)
   - Durações maiores que 5h pedem confirmação extra

Antes de gravar, o script mostra uma pré-visualização e só salva se você confirmar. Depois de salvo, ele atualiza os totais de horas/valores pendentes (não pagos).

### Colunas do CSV

| Coluna       | Descrição                              |
|--------------|----------------------------------------|
| n            | ID sequencial                          |
| tempo_total  | Texto do tempo informado               |
| atividade    | Descrição digitada                     |
| data_inicio  | Término − duração                      |
| data_fim     | Horário do lançamento                  |
| valor        | `(minutos / 60) * VALOR_HORA`          |
| pago         | Sempre `"Não"` (atualize manualmente)  |

Cada execução grava apenas **um** apontamento.

## Alias no shell

Adicione ao `~/.zshrc` para rodar como `addhoras`:

```bash
alias addhoras="$HOME/CascadeProjects/apontamento-horas/apontamento_horas.py"
```

Depois rode `source ~/.zshrc` (ou abra um novo terminal) e use:

```bash
addhoras
```

## Exemplo de execução
```bash
➜  apontamento-horas git:(main) addhoras

=== Novo Apontamento de Horas ===
Atividade: 123
Tempo (ex: 30m, 1h30m, 2h): 1h

Pré-visualização do registro:
----------------------------------------
ID (n)      : 1
Atividade   : 123
Tempo total : 1h
Início      : 2025-12-07 18:31:59
Fim         : 2025-12-07 19:31:59
Valor (R$)  : R$ 113,63
----------------------------------------
Confirmar gravação? (s/n): s

✅ Apontamento salvo em apontamentos.csv

Pendências:
----------------------------------------
Total horas não pagas: 1h
Total não pago      : R$ 113,63
----------------------------------------

```

## Contribuições e Créditos

- Sham Vinicius Fiorin
