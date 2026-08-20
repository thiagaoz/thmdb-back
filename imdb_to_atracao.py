import csv
import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv


def converter_runtime(valor: str | None) -> int | None:
    if not valor:
        return None
    try:
        return int(float(str(valor).split()[0]))
    except (ValueError, TypeError):
        return None

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

OMDB_API_KEY = os.getenv("OMDB_API_KEY")
OMDB_URL = "http://www.omdbapi.com/"

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_URL = "http://www.omdbapi.com/"

# Mapeamento dos nomes de colunas do CSV para as chaves do JSON
novo_nome = {
    "Const": "id",
    "Your Rating": "rating_th",
    "Title": "title",
    "Title Type": "type",
    "Genres": "genre",
    "Directors": "directors",
    "URL": "url",
}

caminho_imdb_csv = "../frontend/src/data/imdb_ratings.csv"
caminho_atracao_json = "../frontend/src/data/atracao.json"


def imdb_to_atracao() -> str:
    """Complementa os dados do CSV do IMDb com informações do OMDb."""
    if not Path(caminho_imdb_csv).exists():
        raise FileNotFoundError(f"Arquivo de origem não encontrado: {caminho_imdb_csv}.")

    # Utiliza encoding="utf-8-sig" para evitar problemas com BOM no CSV
    with open(caminho_imdb_csv, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        imdb_raw = [row for row in reader]

    if not imdb_raw:
        raise ValueError(f"O arquivo {caminho_imdb_csv} está vazio.")

    results = []
    erros = 0
    processados = 0
    total_itens = len(imdb_raw)

    print(f"Iniciando processamento de {total_itens} itens do CSV...\n")

    for row in imdb_raw:
        # Filtra episódios de TV antes de fazer qualquer requisição à API
        if row.get("Title Type") == "TV Episode":
            continue

        processados += 1

        # Aplica o mapeamento de colunas definido no dicionário novo_nome
        atracao = {novo_nome[k]: v for k, v in row.items() if k in novo_nome}

        atracao_id = atracao.get("id")
        titulo = atracao.get("title", "Título desconhecido")

        if not atracao_id:
            erros += 1
            print(f"[{processados}] Falha: ID ausente para '{titulo}'")
            continue

        print(f"[{processados}] Consultando OMDb para: {titulo} ({atracao_id})...")

        try:
            params = {"apikey": OMDB_API_KEY, "i": atracao_id}
            response = requests.get(OMDB_URL, params=params, timeout=10)
            response.raise_for_status()
            omdb_data = response.json()

            if omdb_data.get("Response") == "True":
                # Tratamento seguro para nota do usuário
                raw_rating = atracao.get("rating_th")
                try:
                    rating_th = float(raw_rating) if raw_rating else 0.0
                except (ValueError, TypeError):
                    rating_th = 0.0

                # Tratamento seguro para temporadas (filmes não possuem totalSeasons)
                total_seasons = omdb_data.get("totalSeasons")
                seasons = (
                    int(total_seasons)
                    if total_seasons and str(total_seasons).isdigit()
                    else None
                )

                item_processado = {
                    **atracao,
                    "rating_th": rating_th,
                    "plot": omdb_data.get("Plot"),
                    "poster": omdb_data.get("Poster"),
                    "year": omdb_data.get("Year"),
                    "runtime": converter_runtime(
                        row.get("Runtime (mins)") or omdb_data.get("Runtime")
                    ),
                }

                if seasons is not None:
                    item_processado["seasons"] = seasons

                results.append(item_processado)

            else:
                erros += 1
                erro_msg = omdb_data.get("Error", "Erro desconhecido na API")
                print(f"   -> OMDb retornou erro para '{titulo}': {erro_msg}")

        except requests.exceptions.RequestException as req_err:
            erros += 1
            print(f"   -> Erro de rede/timeout ao buscar '{titulo}': {req_err}")
        except (KeyError, ValueError, TypeError) as parse_err:
            erros += 1
            print(f"   -> Erro ao processar dados de '{titulo}': {parse_err}")

    Path(caminho_atracao_json).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_atracao_json, mode="w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    msg = f"\nProcessamento concluído: {len(results)} atrações salvas em {caminho_atracao_json} ({erros} falhas)."
    return msg


if __name__ == "__main__":
    try:
        resultado_msg = imdb_to_atracao()
        print(resultado_msg)
    except Exception as e:
        print(f"\nErro ao converter CSV para JSON: {e}")