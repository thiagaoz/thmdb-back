import argparse
import csv
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PADRAO = BASE_DIR / "frontend" / "src" / "data" / "watchlist.csv"
RATINGS_CSV_PADRAO = BASE_DIR / "frontend" / "src" / "data" / "imdb_ratings.csv"
JSON_PADRAO = BASE_DIR / "frontend" / "src" / "data" / "watchlist.json"
TMDB_URL = "https://api.themoviedb.org/3/find/{imdb_id}"


def converter_runtime(valor: str | None) -> int | None:
    if not valor:
        return None
    try:
        return int(float(valor))
    except (ValueError, TypeError):
        return None


def buscar_no_tmdb(imdb_id: str, api_key: str) -> dict | None:
    headers = {"accept": "application/json"}
    params = {"external_source": "imdb_id", "language": "pt-BR"}
    if api_key.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {api_key}"
    else:
        params["api_key"] = api_key

    resposta = requests.get(
        TMDB_URL.format(imdb_id=imdb_id),
        headers=headers,
        params=params,
        timeout=10,
    )
    resposta.raise_for_status()
    dados = resposta.json()
    for chave in ("movie_results", "tv_results", "tv_episode_results"):
        if dados.get(chave):
            return dados[chave][0]
    return None


def watchlist_to_json(caminho_csv: Path = CSV_PADRAO, caminho_json: Path = JSON_PADRAO) -> str:
    load_dotenv()
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        raise RuntimeError("A variável TMDB_API_KEY não foi encontrada.")
    if not caminho_csv.exists():
        raise FileNotFoundError(f"Arquivo de origem não encontrado: {caminho_csv}")
    if not RATINGS_CSV_PADRAO.exists():
        raise FileNotFoundError(f"Arquivo de ratings não encontrado: {RATINGS_CSV_PADRAO}")

    with caminho_csv.open(encoding="utf-8-sig", newline="") as arquivo:
        itens_csv = list(csv.DictReader(arquivo))
    with RATINGS_CSV_PADRAO.open(encoding="utf-8-sig", newline="") as arquivo:
        ids_vistos = {
            item.get("Const")
            for item in csv.DictReader(arquivo)
            if item.get("Const") and item.get("Your Rating", "").strip()
        }

    resultados = []
    erros = 0
    for item in itens_csv:
        imdb_id = item.get("Const")
        if not imdb_id:
            erros += 1
            continue
        if imdb_id in ids_vistos:
            continue
        try:
            tmdb = buscar_no_tmdb(imdb_id, api_key)
            if not tmdb:
                erros += 1
                continue
            data = tmdb.get("release_date") or tmdb.get("first_air_date", "")
            poster_path = tmdb.get("poster_path")
            resultados.append({
                "id": imdb_id,
                "title": item.get("Title", ""),
                "title-br": tmdb.get("title") or tmdb.get("name"),
                "type": item.get("Title Type", ""),
                "genre": item.get("Genres", ""),
                "plot": tmdb.get("overview", ""),
                "url": item.get("URL", ""),
                "poster": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
                "year": data.split("-")[0] if data else item.get("Year"),
                "runtime": converter_runtime(item.get("Runtime (mins)")),
                "tmdb_id": tmdb.get("id"),
            })
        except requests.exceptions.RequestException as erro:
            erros += 1
            print(f"Erro ao buscar {imdb_id}: {erro}")

    caminho_json.parent.mkdir(parents=True, exist_ok=True)
    with caminho_json.open("w", encoding="utf-8") as arquivo:
        json.dump(resultados, arquivo, indent=4, ensure_ascii=False)
        arquivo.write("\n")
    return f"{len(resultados)} itens salvos em {caminho_json} ({erros} falhas)."


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria watchlist.json a partir do watchlist.csv usando o TMDB.")
    parser.add_argument("--csv", type=Path, default=CSV_PADRAO, dest="caminho_csv")
    parser.add_argument("--json", type=Path, default=JSON_PADRAO, dest="caminho_json")
    args = parser.parse_args()
    print(watchlist_to_json(args.caminho_csv, args.caminho_json))


if __name__ == "__main__":
    main()