"""
scraper.py — Baixa PDFs de provas objetivas do vestibular UFU.

As URLs de download ficam em onclick="window.open('URL','_blank')" na tabela #tb_cronograma.
Filtra apenas:
  - "Caderno de Prova" que NÃO seja discursiva
  - "Gabarito" + "Definitivo" que NÃO seja discursivo

Uso:
    pip install httpx beautifulsoup4
    python scraper.py
"""

import httpx
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup

BASE_URL = "https://www.portalselecao.ufu.br"
PDFS_DIR = Path(__file__).parent / "pdfs"
PDFS_DIR.mkdir(exist_ok=True)

# Edições conhecidas: (ano, semestre, id_cronograma)
EDICOES = [
    (2019, 2, 883),
    (2020, 2, 998),
    (2022, 2, 1231),
    (2023, 2, 1351),
    (2024, 2, 1481),
    (2025, 2, 1608),
]


def eh_relevante(texto: str) -> bool:
    t = texto.lower()
    if "discursiva" in t or "discursivo" in t:
        return False
    if "caderno de prova" in t:
        return True
    if "gabarito" in t and "definitivo" in t:
        return True
    return False


def descobrir_links_pdf(cronograma_id: int, ano: int, semestre: int, client: httpx.Client) -> list[dict]:
    url = f"{BASE_URL}/servicos/Edital/cronograma/{cronograma_id}"
    print(f"  Acessando: {url}")

    try:
        resp = client.get(url, follow_redirects=True, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ERRO: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    tabela = soup.find("table", id="tb_cronograma")
    if not tabela:
        print("  AVISO: tabela #tb_cronograma não encontrada")
        return []

    links = []
    for row in tabela.find_all("tr"):
        # Texto do item: div com classes col-sm-8
        texto_div = row.find("div", class_=lambda c: c and "col-sm-8" in c)
        if not texto_div:
            continue
        texto = texto_div.get_text(strip=True)

        if not eh_relevante(texto):
            continue

        # URL: onclick="window.open('URL','_blank')"
        btn = row.find("button", onclick=True)
        if not btn:
            continue
        m = re.search(r"window\.open\('([^']+)'", btn["onclick"])
        if not m:
            continue

        url_arquivo = m.group(1)
        links.append({"url": url_arquivo, "nome": texto})
        print(f"    [OK] {texto!r}")

    return links


def baixar_pdf(url: str, destino: Path, client: httpx.Client) -> bool:
    if destino.exists():
        print(f"    Já existe: {destino.name}")
        return True

    try:
        resp = client.get(url, follow_redirects=True, timeout=60)
        resp.raise_for_status()
        destino.write_bytes(resp.content)
        print(f"    Baixado: {destino.name} ({len(resp.content) / 1024:.0f} KB)")
        return True
    except Exception as e:
        print(f"    ERRO: {e}")
        return False


def main():
    headers = {"User-Agent": "Mozilla/5.0 (compatible; UFU-Vestibular-Scraper/1.0)"}

    with httpx.Client(headers=headers) as client:
        for ano, semestre, cronograma_id in EDICOES:
            print(f"\nVestibular {ano}-{semestre}")

            links = descobrir_links_pdf(cronograma_id, ano, semestre, client)
            if not links:
                print("  Nenhum link encontrado.")
                continue

            for i, link in enumerate(links, 1):
                slug = re.sub(r'[^\w\s]', '', link["nome"].lower()).strip()
                slug = re.sub(r'\s+', '_', slug)[:40]
                nome_arquivo = f"{ano}_{semestre}_{i:02d}_{slug}.pdf"
                baixar_pdf(link["url"], PDFS_DIR / nome_arquivo, client)
                time.sleep(0.5)

    print(f"\nPDFs em {PDFS_DIR}:")
    for p in sorted(PDFS_DIR.glob("*.pdf")):
        print(f"  {p.name} ({p.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
