import json
import os
from pathlib import Path

caminho_atracao_json = "../frontend/src/data/atracao.json"

def corretor_atracoes() -> None:
    """Carrega o JSON de atrações, trata os tipos dos campos e salva novamente."""
    caminho = Path(caminho_atracao_json)
    
    # 1. Verifica se o arquivo existe antes de abrir
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_atracao_json}")

    # 2. Abre e carrega os dados do JSON
    with open(caminho, mode="r", encoding="utf-8") as f:
        dados_json = json.load(f)

    if not isinstance(dados_json, list):
        raise ValueError("O conteúdo do JSON deve ser uma lista de atrações.")

    atracao_corrigida = []
    erros = 0  # Inicializa o contador de erros

    for atracao in dados_json:
        atracao_id = atracao.get("id")
        if not atracao_id:
            print("⚠️ Item sem o campo 'id' ignorado.")
            erros += 1
            continue

        # Trata o campo rating_th (converte para float com fallback para 0.0)
        raw_rating = atracao.get("rating_th")
        try:
            rating_th = float(raw_rating) if raw_rating is not None else 0.0
        except (ValueError, TypeError):
            rating_th = 0.0

        # Trata o campo seasons (converte para int apenas se existir valor, mantendo None para filmes)
        raw_seasons = atracao.get("seasons")
        if raw_seasons is not None and str(raw_seasons).isdigit():
            seasons = int(raw_seasons)
        else:
            seasons = None

        atracao_corrigida.append({
            **atracao,
            "rating_th": rating_th,
            "seasons": seasons
        })

    # 3. Reescreve o arquivo JSON com os dados corrigidos
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, mode="w", encoding="utf-8") as f:
        json.dump(atracao_corrigida, f, indent=4, ensure_ascii=False)

    msg = f"✅ Processamento concluído: {len(atracao_corrigida)} atrações salvas em {caminho_atracao_json} ({erros} falhas)."
    print(msg)


if __name__ == "__main__":
    try:
        corretor_atracoes()
    except Exception as e:
        print(f"❌ Erro ao tratar JSON de atrações: {e}")