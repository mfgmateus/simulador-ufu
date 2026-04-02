"""
extract_questions.py — Extrai questões objetivas dos PDFs do vestibular UFU via regex.

Funciona sem IA — parseia o texto extraído pelo pymupdf seguindo a estrutura padrão:
  - Cabeçalho de disciplina: linha em CAIXA ALTA (ex: BIOLOGIA, FILOSOFIA)
  - Questão: QUESTÃO 01, QUESTÃO 02, ...
  - Alternativas: A) ... B) ... C) ... D) ... E) ...
  - Gabarito: aplicado separadamente do PDF de gabarito

Uso:
    pip install pymupdf
    python extract_questions.py
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import io

import fitz  # pymupdf
from PIL import Image

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
PDFS_DIR = SCRIPT_DIR / "pdfs"
IMAGES_DIR = PROJECT_DIR / "public" / "images"
OUTPUT_JSON = PROJECT_DIR / "public" / "questions.json"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

MIN_IMG_W = 100  # ignora imagens muito pequenas (decorações, separadores)

# Mapeamento de disciplinas (como aparecem no PDF → nome canônico)
DISCIPLINAS_MAP = {
    "BIOLOGIA": "Biologia",
    "FILOSOFIA": "Filosofia",
    "FÍSICA": "Física",
    "GEOGRAFIA": "Geografia",
    "HISTÓRIA": "História",
    "LÍNGUA PORTUGUESA": "Língua Portuguesa",
    "LINGUA PORTUGUESA": "Língua Portuguesa",
    "LITERATURA": "Literatura",
    "MATEMÁTICA": "Matemática",
    "MATEMATICA": "Matemática",
    "QUÍMICA": "Química",
    "QUIMICA": "Química",
    "SOCIOLOGIA": "Sociologia",
    "LÍNGUA ESTRANGEIRA": "Língua Estrangeira",
    "LINGUA ESTRANGEIRA": "Língua Estrangeira",
    "INGLÊS": "Língua Estrangeira",
    "ESPANHOL": "Língua Estrangeira",
    "FRANCÊS": "Língua Estrangeira",
}

# Linhas a remover (cabeçalho repetido em cada página)
HEADER_PATTERN = re.compile(
    r'Processo Seletivo UFU/\d+-\d+\s*[–-]\s*Edital DIRPS.*?TIPO \d+\s*\n\s*Página \d+\s*\n',
    re.DOTALL,
)

# Padrão de início de questão
QUESTAO_RE = re.compile(r'\bQUESTÃO\s+(\d{1,2})\b')

# Padrão de alternativa: A) ou A. no início de linha
ALT_RE = re.compile(r'^\s*([A-E])\)\s+(.+)', re.MULTILINE)


def extrair_imagens_por_questao(doc: fitz.Document, pdf_stem: str) -> dict[int, list[str]]:
    """
    Para cada página, associa imagens às questões pela posição Y:
    a imagem pertence à questão cujo header aparece imediatamente acima dela.
    Retorna {numero_questao: [nome_arquivo, ...]}
    """
    resultado: dict[int, list[str]] = {}

    for page_num, page in enumerate(doc):
        imgs = [i for i in page.get_images(full=True) if i[2] >= MIN_IMG_W]
        if not imgs:
            continue

        # Encontra blocos com "QUESTÃO NN" e seus Y
        questoes_na_pagina = []
        for b in page.get_text("blocks"):
            m = re.search(r'QUESTÃO\s+(\d+)', b[4])
            if m:
                questoes_na_pagina.append((int(m.group(1)), b[1]))  # (numero, y_topo)

        if not questoes_na_pagina:
            continue

        for img_info in imgs:
            xref = img_info[0]
            rects = page.get_image_rects(xref)
            if not rects:
                continue
            img_y = rects[0].y0

            # Questão mais próxima acima da imagem
            candidatas = [(n, y) for n, y in questoes_na_pagina if y <= img_y]
            if not candidatas:
                candidatas = questoes_na_pagina  # fallback
            numero_q = max(candidatas, key=lambda x: x[1])[0]

            # Extrai e salva como PNG
            try:
                base = doc.extract_image(xref)
                img = Image.open(io.BytesIO(base["image"]))
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                nome = f"{pdf_stem}_q{numero_q:02d}_img{xref}.png"
                (IMAGES_DIR / nome).write_bytes(buf.getvalue())
                resultado.setdefault(numero_q, []).append(nome)
            except Exception as e:
                print(f"  AVISO: erro ao extrair imagem xref={xref}: {e}")

    return resultado


def extrair_texto(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    partes = []
    for page in doc:
        partes.append(page.get_text("text"))
    doc.close()
    texto = "\n".join(partes)
    # Remove cabeçalhos repetidos de cada página
    texto = HEADER_PATTERN.sub("\n", texto)
    return texto


def detectar_disciplina(linha: str) -> str | None:
    """Retorna o nome canônico se a linha for um cabeçalho de disciplina."""
    l = linha.strip()
    # Deve ser só texto em maiúsculas (pode ter acento), sem pontuação
    if not l or not re.match(r'^[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÀÈÌÒÙÇ\s]+$', l):
        return None
    return DISCIPLINAS_MAP.get(l.upper())


def parsear_questoes(texto: str, ano: int, semestre: int) -> list[dict]:
    """
    Faz uma passagem linear pelo texto rastreando disciplina atual,
    depois extrai campos de cada bloco de questão.
    """
    linhas = texto.splitlines()

    # Passo 1: mapeia número_de_linha → disciplina vigente
    disciplina_por_linha = {}
    disciplina_atual = "Desconhecida"
    for i, linha in enumerate(linhas):
        d = detectar_disciplina(linha)
        if d:
            disciplina_atual = d
        disciplina_por_linha[i] = disciplina_atual

    # Passo 2: encontra posição (linha) de cada QUESTÃO NN
    questao_posicoes = []  # [(numero, linha_inicio)]
    for i, linha in enumerate(linhas):
        m = re.match(r'^\s*QUESTÃO\s+(\d{1,2})\s*$', linha.strip())
        if m:
            questao_posicoes.append((int(m.group(1)), i))

    questoes = []

    for idx, (numero, linha_inicio) in enumerate(questao_posicoes):
        # Disciplina vigente na linha desta questão
        disc = disciplina_por_linha.get(linha_inicio, "Desconhecida")

        # Bloco vai até o início da próxima questão (ou fim do texto)
        if idx + 1 < len(questao_posicoes):
            linha_fim = questao_posicoes[idx + 1][1]
        else:
            linha_fim = len(linhas)

        bloco_linhas = linhas[linha_inicio + 1 : linha_fim]
        bloco = "\n".join(bloco_linhas)

        # Extrai alternativas (multi-linha: tudo entre A) e B), entre B) e C), etc.)
        alternativas = {}
        alt_matches = list(re.finditer(r'^\s*([A-E])\)\s+', bloco, re.MULTILINE))
        for j, m in enumerate(alt_matches):
            letra = m.group(1)
            inicio = m.end()
            fim = alt_matches[j + 1].start() if j + 1 < len(alt_matches) else len(bloco)
            texto_alt = bloco[inicio:fim].strip()
            # Colapsa quebras de linha internas da alternativa
            texto_alt = re.sub(r'\s*\n\s*', ' ', texto_alt).strip()
            alternativas[letra] = texto_alt

        # Enunciado: tudo antes da primeira alternativa
        if alt_matches:
            enunciado_bruto = bloco[: alt_matches[0].start()].strip()
        else:
            enunciado_bruto = bloco.strip()

        # Remove linhas de cabeçalho de disciplina do enunciado
        linhas_enunciado = [
            l for l in enunciado_bruto.splitlines()
            if not detectar_disciplina(l)
        ]
        enunciado = "\n".join(linhas_enunciado).strip()
        enunciado = re.sub(r'\n{3,}', '\n\n', enunciado)

        tem_figura = bool(re.search(r'[Ff]igura\s*\d+|[Gg]ráfico|[Ii]magem', enunciado))

        disc_slug = re.sub(r'[^\w]', '', disc.lower())[:6]
        q_id = f"{ano}-{semestre}-{disc_slug}-{numero:02d}"

        questoes.append({
            "id": q_id,
            "ano": ano,
            "semestre": semestre,
            "disciplina": disc,
            "numero": numero,
            "enunciado": enunciado,
            "imagens": [],
            "tem_figura": tem_figura,
            "alternativas": alternativas,
            "gabarito": "",
        })

    return questoes


def aplicar_gabarito(questoes: list[dict], gabarito_pdf: Path, ano: int, semestre: int):
    """Extrai respostas do PDF de gabarito e aplica nas questões."""
    try:
        doc = fitz.open(gabarito_pdf)
        texto = " ".join(page.get_text("text") for page in doc)
        doc.close()
    except Exception as e:
        print(f"  ERRO ao abrir gabarito: {e}")
        return

    # Padrões comuns em gabaritos UFU: "01 C", "01 - C", "01) C"
    pares = re.findall(r'\b(\d{1,2})\s*[-–).]?\s*([A-E])\b', texto)
    gabarito_map = {}
    for num_str, letra in pares:
        n = int(num_str)
        if 1 <= n <= 100:
            gabarito_map[n] = letra

    print(f"  Gabarito: {len(gabarito_map)} respostas encontradas em {gabarito_pdf.name}")

    atualizadas = 0
    for q in questoes:
        if q["ano"] == ano and q["semestre"] == semestre:
            n = q["numero"]
            if n in gabarito_map:
                q["gabarito"] = gabarito_map[n]
                atualizadas += 1

    print(f"  {atualizadas} questões atualizadas com gabarito")


def inferir_edicao(nome: str) -> tuple[int, int]:
    m = re.match(r"(\d{4})_(\d)", nome)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def main():
    # Usa apenas Tipo 1 de cada edição (evita duplicatas de Tipo 2, 3, 4)
    # Cadernos com língua estrangeira (Francês) são ignorados pois têm questões diferentes
    cadernos = sorted(
        p for p in PDFS_DIR.glob("*.pdf")
        if "gabarito" not in p.name.lower()
        and "franc" not in p.name.lower()
        and "tipo_1" in p.name.lower() or (
            "caderno" in p.name.lower()
            and not any(x in p.name.lower() for x in ["tipo_2", "tipo_3", "tipo_4", "franc"])
        )
    )

    # Fallback: se não encontrar "tipo_1", pega todos os cadernos não-gabarito
    if not cadernos:
        cadernos = sorted(
            p for p in PDFS_DIR.glob("*.pdf")
            if "gabarito" not in p.name.lower() and "franc" not in p.name.lower()
        )

    gabaritos = sorted(
        p for p in PDFS_DIR.glob("*.pdf")
        if "gabarito" in p.name.lower() and "franc" not in p.name.lower()
    )

    if not cadernos:
        print(f"Nenhum caderno de prova encontrado em {PDFS_DIR}")
        sys.exit(1)

    print(f"Cadernos: {[p.name for p in cadernos]}")
    print(f"Gabaritos: {[p.name for p in gabaritos]}")

    todas = []

    for pdf_path in cadernos:
        ano, semestre = inferir_edicao(pdf_path.stem)
        print(f"\nProcessando: {pdf_path.name} ({ano}-{semestre})")

        doc = fitz.open(pdf_path)
        texto = "\n".join(page.get_text("text") for page in doc)
        texto = HEADER_PATTERN.sub("\n", texto)

        imagens_por_questao = extrair_imagens_por_questao(doc, pdf_path.stem)
        doc.close()

        questoes = parsear_questoes(texto, ano, semestre)

        # Associa imagens extraídas às questões
        for q in questoes:
            imgs = imagens_por_questao.get(q["numero"], [])
            if imgs:
                q["imagens"] = imgs
                print(f"  Q{q['numero']:02d}: {len(imgs)} imagem(ns) → {imgs}")
        print(f"  {len(questoes)} questões extraídas")

        # Aplica gabarito correspondente
        for gab in gabaritos:
            ga, gs = inferir_edicao(gab.stem)
            if ga == ano and gs == semestre:
                aplicar_gabarito(questoes, gab, ano, semestre)
                break

        todas.extend(questoes)

    # Resumo
    from collections import Counter
    print(f"\n{'='*50}")
    print(f"Total: {len(todas)} questões")
    for disc, n in sorted(Counter(q["disciplina"] for q in todas).items()):
        print(f"  {disc:<25} {n:>3}")

    com_figura = sum(1 for q in todas if q.get("tem_figura"))
    sem_gabarito = sum(1 for q in todas if not q.get("gabarito"))
    print(f"\nCom referência a figura: {com_figura} (imagens precisam ser adicionadas manualmente)")
    print(f"Sem gabarito: {sem_gabarito}")

    # Remove campo auxiliar antes de salvar
    for q in todas:
        q.pop("tem_figura", None)
        q.pop("numero", None)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(todas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
