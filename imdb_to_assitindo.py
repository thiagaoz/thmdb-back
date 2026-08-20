import csv
import json
import os
import requests
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


def converter_runtime(valor: str | None) -> int | None:
    if not valor:
        return None
    try:
        return int(float(str(valor).split()[0]))
    except (ValueError, TypeError):
        return None

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


caminho_imdb_csv = "../frontend/src/data/assistindo.csv"
caminho_atracao_json = "../frontend/src/data/assistindo.json"

def imdb_to_assitindo() -> str:
    """Complementa os dados do CSV do IMDb com informações do OMDb."""
    if not Path(caminho_imdb_csv).exists():
        raise HTTPException(
            status_code=404,
            detail=f"Arquivo de origem não encontrado: {caminho_imdb_csv}.",
        )

    # Utiliza encoding="utf-8-sig" para evitar problemas com BOM no CSV
    with open(caminho_imdb_csv, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        assisindo_csv = [row for row in reader]

    if not assisindo_csv:
        raise HTTPException(
            status_code=400,
            detail=f"O arquivo {caminho_imdb_csv} está vazio.",
        )

    results = []
    erros = 0
    processados = 0

    for row in assisindo_csv:
        # Tenta pegar o ID pela coluna 'id' ou 'Const'
        atracao_id = row.get("id") or row.get("Const")
        
        if not atracao_id:
            print("⚠️ Linha sem ID válido ignorada.")
            erros += 1
            continue

        try:
            params = {"apikey": API_KEY, "i": atracao_id}
            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            omdb_data = response.json()

            if omdb_data.get("Response") == "True":
                # Filtra para aceitar apenas séries
                if omdb_data.get("Type") != "series":
                    continue

                item_processado = {
                    "id": atracao_id, 
                    "rating_th": 0,
                    "title": omdb_data.get("Title"),
                    "plot": omdb_data.get("Plot"),
                    "genre": omdb_data.get("Genre"),
                    "directors": omdb_data.get("Director"),
                    "url": f"https://www.imdb.com/title/{atracao_id}/",
                    "poster": omdb_data.get("Poster"),
                    "year": omdb_data.get("Year"),
                    "runtime": converter_runtime(omdb_data.get("Runtime")),
                    "seasons": int(omdb_data.get("totalSeasons")) if omdb_data.get("totalSeasons") is not None else None,
                    "currentSeason": int(row.get("current season")) if row.get("current season") is not None else None,
                }

                results.append(item_processado)
                processados += 1

                
            else:
                print(f"⚠️ Filme não encontrado no OMDb ID {id}: {omdb_data.get('Error')}")
                erros += 1
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de requisição para {id}: {e}")
            erros += 1
        except (KeyError, ValueError, TypeError) as e:
            print(f"❌ Erro no processamento de dados para {id}: {e}")
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
        imdb_to_assitindo()
    except Exception as e:
        print(f"❌ Erro ao converter CSV para JSON: {e}")
    finally:
        # Garante que o console permaneça aberto independente de erro ou sucesso
        input("\nPressione [ENTER] para sair...")