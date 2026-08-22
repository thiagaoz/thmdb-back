import argparse
import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PADRAO = BASE_DIR / "frontend" / "src" / "data" / "imdb_ratings.csv"
JSON_PADRAO = BASE_DIR / "frontend" / "src" / "data" / "atracao.json"


def converter_runtime(valor: str | None) -> int | None:
    if not valor:
        return None
    try:
        return int(float(valor))
    except (ValueError, TypeError):
        return None


def atualizar_runtime(caminho_csv: Path = CSV_PADRAO, caminho_json: Path = JSON_PADRAO) -> str:
    if not caminho_csv.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {caminho_csv}")
    if not caminho_json.exists():
        raise FileNotFoundError(f"Arquivo JSON não encontrado: {caminho_json}")

    with caminho_csv.open(mode="r", encoding="utf-8-sig", newline="") as arquivo_csv:
        runtimes = {
            row.get("Const"): converter_runtime(row.get("Runtime (mins)"))
            for row in csv.DictReader(arquivo_csv)
        }

    with caminho_json.open(mode="r", encoding="utf-8") as arquivo_json:
        atracoes = json.load(arquivo_json)

    if not isinstance(atracoes, list):
        raise ValueError("O conteúdo do JSON deve ser uma lista de atrações.")

    atualizados = 0
    for atracao in atracoes:
        runtime = runtimes.get(atracao.get("id"))
        if runtime is not None:
            atracao["runtime"] = runtime
            atualizados += 1

    with caminho_json.open(mode="w", encoding="utf-8") as arquivo_json:
        json.dump(atracoes, arquivo_json, indent=4, ensure_ascii=False)
        arquivo_json.write("\n")

    return f"{atualizados} runtimes atualizados em {caminho_json}."


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Atualiza o campo runtime das atrações usando o CSV do IMDb."
    )
    parser.add_argument("--csv", type=Path, default=CSV_PADRAO, dest="caminho_csv")
    parser.add_argument("--json", type=Path, default=JSON_PADRAO, dest="caminho_json")
    args = parser.parse_args()
    print(atualizar_runtime(args.caminho_csv, args.caminho_json))


if __name__ == "__main__":
    main()