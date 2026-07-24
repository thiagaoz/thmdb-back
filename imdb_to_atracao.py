import csv
import json
import os
import requests
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

API_KEY = os.getenv("OMDB_API_KEY")
BASE_URL = "http://www.omdbapi.com/"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        raise HTTPException(
            status_code=404,
            detail=f"Arquivo de origem não encontrado: {caminho_imdb_csv}.",
        )

    # Utiliza encoding="utf-8-sig" para evitar problemas com BOM no CSV
    with open(caminho_imdb_csv, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        imdb_raw = [row for row in reader]

    if not imdb_raw:
        raise HTTPException(
            status_code=400,
            detail=f"O arquivo {caminho_imdb_csv} está vazio.",
        )

    results = []
    erros = 0
    processados = 0

    # Processa apenas os 100 primeiros itens
    for row in imdb_raw:
        # 1. Filtra antes de fazer qualquer requisição à API
        if row.get("Title Type") == "TV Episode":
            
            continue

        # Aplica o mapeamento de colunas definido no dicionário novo_nome
        atracao = {novo_nome[k]: v for k, v in row.items() if k in novo_nome}

        atracao_id = atracao.get("id")
        if not atracao_id:
            print("⚠️ Item sem o campo 'id' (Const) ignorado.")
            erros += 1
            continue

        try:
            params = {"apikey": API_KEY, "i": atracao_id}
            response = requests.get(BASE_URL, params=params, timeout=10)
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
                seasons = int(total_seasons) if total_seasons and str(total_seasons).isdigit() else None

                item_processado = {
                    **atracao,
                    "rating_th": rating_th,
                    "plot": omdb_data.get("Plot"),
                    "poster": omdb_data.get("Poster"),
                    "year": omdb_data.get("Year"),
                }

                if seasons is not None:
                    item_processado["seasons"] = seasons

                results.append(item_processado)
                processados += 1

                
            else:
                print(f"⚠️ Filme não encontrado no OMDb ID {atracao_id}: {omdb_data.get('Error')}")
                erros += 1
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de requisição para {atracao_id}: {e}")
            erros += 1
        except (KeyError, ValueError, TypeError) as e:
            print(f"❌ Erro no processamento de dados para {atracao_id}: {e}")
            erros += 1

    Path(caminho_atracao_json).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_atracao_json, mode="w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    msg = f"\n✅ Processamento concluído: {len(results)} atrações salvas em {caminho_atracao_json} ({erros} falhas)."
    print(msg)
    print(processados)
    return msg

if __name__ == "__main__":
    try:
        imdb_to_atracao()
    except Exception as e:
        print(f"❌ Erro ao converter CSV para JSON: {e}")
        input("\nPressione [ENTER] para continuar...")