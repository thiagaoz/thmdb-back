import os
import uvicorn
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from tmdb import imdb_to_atracao
from watchlist import watchlist_to_json

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

app = FastAPI()

# Configura o middleware CORS para permitir solicitações do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens -->> ALTERAR PARA FRONTEND ESPECÍFICO EM PRODUÇÃO
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos HTTP  
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

def selecionar_tipo(type: str):
    if type == "movie":
        return "Filme"
    elif type == "series":
        return "Série"
    elif type == "game":
        return "Jogo"
    else:
        return "Outro"


def buscar_no_tmdb(query: str) -> list[dict]:
    """Busca títulos no TMDB por query string."""
    url = f"{TMDB_BASE_URL}/search/multi"
    
    # Trata autenticação por Bearer Token v4 ou API Key v3
    if TMDB_API_KEY and TMDB_API_KEY.startswith("eyJ"):
        headers = {
            "Authorization": f"Bearer {TMDB_API_KEY}",
            "accept": "application/json",
        }
        params = {"query": query, "language": "pt-BR"}
    else:
        headers = {}
        params = {
            "api_key": TMDB_API_KEY,
            "query": query,
            "language": "pt-BR",
        }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        dados = response.json()
        return dados.get("results", [])
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar no TMDB: {e}")
        return []


# Endpoint para buscar atrações por título no TMDB
@app.get("/busca-atracoes-title")
def buscar_atracoes_por_titulo(title: str):
    """Busca atrações no TMDB por título."""
    if not title or len(title.strip()) < 2:
        raise HTTPException(status_code=400, detail="Título deve ter pelo menos 2 caracteres")

    resultados = buscar_no_tmdb(title)
    
    if not resultados:
        return []

    # Formata resultados para o padrão de Atracao
    atracoes_formatadas = []
    for item in resultados:
        # Filtra episódios de TV
        if item.get("media_type") == "tv_episode":
            continue

        tmdb_id = item.get("id")
        titulo = item.get("title") or item.get("name", "Desconhecido")
        poster_path = item.get("poster_path")
        poster_url = (
            f"https://image.tmdb.org/t/p/w500{poster_path}"
            if poster_path
            else None
        )
        
        # Extrai o ano
        data_lancamento = item.get("release_date") or item.get("first_air_date", "")
        ano = data_lancamento.split("-")[0] if data_lancamento else None
        
        # Determina o tipo
        media_type = item.get("media_type", "").upper()
        if media_type == "MOVIE":
            tipo = "Filme"
        elif media_type == "TV":
            tipo = "Série"
        else:
            tipo = media_type

        atracao_formatada = {
            "id": f"tmdb_{tmdb_id}",  # Prefixo tmdb_ para diferenciar
            "title": titulo,
            "poster": poster_url,
            "type": tipo,
            "year": ano,
            "tmdb_id": tmdb_id,
        }
        atracoes_formatadas.append(atracao_formatada)

    return atracoes_formatadas


# Endpoint para disparar processamento CSV → Atrações com dados do TMDB
@app.get("/converter")
def converter_csv_para_atracao():
    """Processa CSV do IMDb e gera arquivo de atrações com dados do TMDB."""
    try:
        resultado = imdb_to_atracao()
        return {"status": "sucesso", "mensagem": resultado}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante processamento: {str(e)}")


@app.get("/converter-watchlist")
def converter_csv_para_watchlist():
    """Processa watchlist.csv e gera watchlist.json com dados do TMDB."""
    try:
        resultado = watchlist_to_json()
        return {"status": "sucesso", "mensagem": resultado}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (RuntimeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante processamento: {str(e)}")


if __name__ == "__main__":
    print("Iniciando servidor FastAPI...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

