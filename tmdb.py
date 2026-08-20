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
        return int(float(valor))
    except (ValueError, TypeError):
        return None

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

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





def buscar_no_tmdb(imdb_id: str) -> dict | None:
    """Busca os detalhes no TMDB utilizando o ID do IMDb."""
    url = f"{TMDB_BASE_URL}/find/{imdb_id}"

    # Trata autenticação por Bearer Token v4 ou API Key v3
    if TMDB_API_KEY and TMDB_API_KEY.startswith("eyJ"):
        headers = {
            "Authorization": f"Bearer {TMDB_API_KEY}",
            "accept": "application/json",
        }
        params = {"external_source": "imdb_id", "language": "pt-BR"}
    else:
        headers = {}
        params = {
            "api_key": TMDB_API_KEY,
            "external_source": "imdb_id",
            "language": "pt-BR",
        }

    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    dados = response.json()

    # Procura por resultados em filmes, séries ou episódios
    for chave in ["movie_results", "tv_results", "tv_episode_results"]:
        resultados = dados.get(chave, [])
        if resultados:
            return resultados[0]

    return None


def imdb_to_atracao() -> str:
    """Processa CSV do IMDb com dados do TMDB (título e plot traduzidos). Reescreve JSON do zero."""
    if not Path(caminho_imdb_csv).exists():
        raise FileNotFoundError(
            f"Arquivo de origem não encontrado: {caminho_imdb_csv}."
        )

    # Inicia lista vazia (reescreve do zero, ignorando atracao.json existente)
    results = []

    # Lê os dados do CSV do IMDb
    with open(caminho_imdb_csv, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        imdb_raw = [row for row in reader]

    if not imdb_raw:
        raise ValueError(f"O arquivo {caminho_imdb_csv} está vazio.")

    erros = 0
    ignorados = 0
    processados = 0
    total_itens = len(imdb_raw)

    print(f"Iniciando processamento de {total_itens} itens do CSV (reescrevendo JSON do zero)...\n")

    for i, row in enumerate(imdb_raw, start=1):
        # Filtra episódios de TV antes do processamento
        if row.get("Title Type") == "TV Episode":
            ignorados += 1
            continue

        atracao_id = row.get("Const")
        titulo_imdb = row.get("Title", "Título desconhecido")

        if not atracao_id:
            erros += 1
            print(f"[{i}] Falha: ID ausente no CSV para '{titulo_imdb}'")
            continue

        processados += 1
        print(f"[{i}] Consultando TMDB para: {titulo_imdb} ({atracao_id})...")

        try:
            tmdb_data = buscar_no_tmdb(atracao_id)

            if tmdb_data:
                # Tratamento seguro para nota do usuário
                raw_rating = row.get("Your Rating", "")
                try:
                    rating_th = float(raw_rating) if raw_rating else 0.0
                except (ValueError, TypeError):
                    rating_th = 0.0

                # Formatação do caminho do pôster no TMDB
                poster_path = tmdb_data.get("poster_path")
                poster_url = (
                    f"https://image.tmdb.org/t/p/w500{poster_path}"
                    if poster_path
                    else None
                )

                # Extrai o ano de lançamento (filmes usam release_date, séries usam first_air_date)
                data_lancamento = tmdb_data.get(
                    "release_date"
                ) or tmdb_data.get("first_air_date", "")
                ano = data_lancamento.split("-")[0] if data_lancamento else None

                # Título: original em inglês (do IMDB) e traduzido (do TMDB em pt-BR)
                titulo_tmdb_br = tmdb_data.get("title") or tmdb_data.get("name")

                # Plot: original em inglês (do TMDB)
                overview_tmdb = tmdb_data.get("overview", "")

                # Gêneros do TMDB (se disponível)
                generos = tmdb_data.get("genres", [])
                genre_names = ", ".join([g.get("name") for g in generos]) if generos else row.get("Genres", "")

                # Temporadas (apenas para séries)
                number_of_seasons = tmdb_data.get("number_of_seasons")

                item_processado = {
                    "id": atracao_id,
                    "title": titulo_imdb,  # Título original em inglês (IMDB)
                    "title-br": titulo_tmdb_br,  # Título traduzido do TMDB
                    "rating_th": rating_th,
                    "type": row.get("Title Type", ""),
                    "genre": genre_names,
                    "genre-br": genre_names,  # TODO: traduzir gêneros se necessário
                    "plot": overview_tmdb,  # Overview em inglês do TMDB
                    "plot-br": tmdb_data.get("overview", ""),  # Para futuro: traduzir se necessário
                    "directors": row.get("Directors", ""),
                    "url": row.get("URL", ""),
                    "poster": poster_url,
                    "year": ano,
                    "runtime": converter_runtime(row.get("Runtime (mins)")),
                    "tmdb_id": tmdb_data.get("id"),
                }

                # Adiciona seasons apenas se for série
                if number_of_seasons:
                    item_processado["seasons"] = number_of_seasons

                results.append(item_processado)

            else:
                erros += 1
                print(
                    f"   -> TMDB não encontrou correspondência para '{titulo_imdb}' ({atracao_id})"
                )

        except requests.exceptions.RequestException as req_err:
            erros += 1
            print(f"   -> Erro de rede/timeout ao buscar '{titulo_imdb}': {req_err}")
        except (KeyError, ValueError, TypeError) as parse_err:
            erros += 1
            print(f"   -> Erro ao processar dados de '{titulo_imdb}': {parse_err}")

    # Salva a lista no JSON (reescrevendo completamente)
    Path(caminho_atracao_json).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_atracao_json, mode="w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    msg = (
        f"\nProcessamento concluído:\n"
        f" - Itens processados: {processados}\n"
        f" - Episódios ignorados: {ignorados}\n"
        f" - Atrações adicionadas: {len(results)}\n"
        f" - Falhas no processamento: {erros}\n"
        f" Total salvo em {caminho_atracao_json}."
    )
    return msg


if __name__ == "__main__":
    try:
        resultado_msg = imdb_to_atracao()
        print(resultado_msg)
    except Exception as e:
        print(f"\nErro ao converter CSV para JSON: {e}")