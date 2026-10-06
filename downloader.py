"""
Descargador de ficheros ZIP de Infoelectoral (Ministerio del Interior).

Uso:
    python downloader.py               # descarga todas las convocatorias
    python downloader.py 202307        # descarga solo una convocatoria
    python downloader.py --list        # lista convocatorias disponibles

Los ZIP se guardan en data/raw/ y se descomprimen automáticamente.

NOTA sobre URLs:
  El Ministerio no tiene una API pública ni URLs estables documentadas.
  Los ZIP se descargan desde la página de descarga manualmente o con las
  URLs que aparecen en el HTML. Las URLs base conocidas son:
    https://infoelectoral.interior.gob.es/estaticos/docxl/apliextr/
  con nombres de fichero del tipo: 02_{YYYYMM}_1.zip
  Si una URL falla, descárgalo manualmente desde:
    https://infoelectoral.interior.gob.es/es/elecciones-celebradas/area-de-descarga/
  y colócalo en data/raw/
"""

import sys
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

from formats import CONVOCATORIAS

RAW_DIR = Path(__file__).parent / "data" / "raw"

DESCARGA_MANUAL_URL = "https://infoelectoral.interior.gob.es/es/elecciones-celebradas/area-de-descarga/"


def _print_manual_instructions(conv_id: str, label: str, zip_path: Path) -> None:
    print(f"\n  {'─'*56}")
    print(f"  Descarga automática no disponible para {label}.")
    print(f"  El Ministerio del Interior no expone las URLs directamente.")
    print(f"\n  PASOS PARA DESCARGA MANUAL:")
    print(f"  1. Abre: {DESCARGA_MANUAL_URL}")
    print(f"  2. Selecciona: Congreso → {label}")
    print(f"  3. Descarga el ZIP de datos (no el PDF de resultados)")
    print(f"  4. Renombra o copia el ZIP a:")
    print(f"     {zip_path}")
    print(f"  5. Ejecuta: python downloader.py {conv_id} --extract-only")
    print(f"  {'─'*56}\n")

# URLs de descarga directa. Si alguna falla actualizar desde la web del Ministerio.
# Patrón observado: 02_{YYYYMM}_1.zip  (tipo_eleccion=02, año+mes, vuelta=1)
BASE_URL = "https://infoelectoral.interior.gob.es/estaticos/docxl/apliextr"

DOWNLOAD_URLS = {
    "199306": f"{BASE_URL}/02_199306_1.zip",
    "199603": f"{BASE_URL}/02_199603_1.zip",
    "200003": f"{BASE_URL}/02_200003_1.zip",
    "200403": f"{BASE_URL}/02_200403_1.zip",
    "200803": f"{BASE_URL}/02_200803_1.zip",
    "201111": f"{BASE_URL}/02_201111_1.zip",
    "201512": f"{BASE_URL}/02_201512_1.zip",
    "201606": f"{BASE_URL}/02_201606_1.zip",
    "201904": f"{BASE_URL}/02_201904_1.zip",
    "201911": f"{BASE_URL}/02_201911_1.zip",
    "202307": f"{BASE_URL}/02_202307_1.zip",
}


def download_zip(conv_id: str, force: bool = False) -> Path:
    """Descarga y descomprime el ZIP de una convocatoria. Devuelve la carpeta extraída."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    label = CONVOCATORIAS[conv_id]["label"]
    url   = DOWNLOAD_URLS[conv_id]
    zip_path   = RAW_DIR / f"{conv_id}.zip"
    extract_to = RAW_DIR / conv_id

    if extract_to.exists() and not force:
        print(f"  [skip] {label} ya descargada en {extract_to}")
        return extract_to

    print(f"  Descargando {label} desde {url}")
    try:
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
    except requests.HTTPError as e:
        _print_manual_instructions(conv_id, label, zip_path)
        raise
    except requests.ConnectionError as e:
        _print_manual_instructions(conv_id, label, zip_path)
        raise

    total = int(resp.headers.get("content-length", 0))
    with open(zip_path, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc=label) as bar:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
            bar.update(len(chunk))

    print(f"  Descomprimiendo en {extract_to}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)

    return extract_to


def find_dat_file(conv_dir: Path, prefix: str) -> Path | None:
    """
    Busca un fichero DAT por prefijo dentro de la carpeta descomprimida.
    Los nombres varían entre convocatorias (ej: '08CAND9306.DAT' vs '08CAND2307.DAT').
    """
    candidates = list(conv_dir.rglob(f"{prefix}*.DAT"))
    if not candidates:
        candidates = list(conv_dir.rglob(f"{prefix.lower()}*.dat"))
    if not candidates:
        return None
    # Si hay varios, tomar el más corto (evita versiones de avance parcial)
    return min(candidates, key=lambda p: len(p.name))


def get_dat_paths(conv_id: str) -> dict[str, Path | None]:
    """Devuelve rutas a los ficheros DAT clave para una convocatoria."""
    conv_dir = RAW_DIR / conv_id
    if not conv_dir.exists():
        raise FileNotFoundError(
            f"Convocatoria {conv_id} no descargada. "
            f"Ejecuta: python downloader.py {conv_id}"
        )
    return {
        "candidaturas": find_dat_file(conv_dir, "08CAND"),
        "provincias":   find_dat_file(conv_dir, "04PROV"),
        "municipios":   find_dat_file(conv_dir, "09MUNI"),
    }


def check_availability(conv_id: str) -> None:
    """Diagnóstico: muestra qué ficheros se encontraron."""
    paths = get_dat_paths(conv_id)
    label = CONVOCATORIAS[conv_id]["label"]
    print(f"\n{label} ({conv_id})")
    for key, path in paths.items():
        status = f"✓ {path.name}" if path else "✗ NO ENCONTRADO"
        print(f"  {key:<15} {status}")


def extract_manual_zip(conv_id: str) -> Path:
    """Descomprime un ZIP que el usuario descargó manualmente."""
    zip_path   = RAW_DIR / f"{conv_id}.zip"
    extract_to = RAW_DIR / conv_id
    if not zip_path.exists():
        raise FileNotFoundError(
            f"No se encontró {zip_path}\n"
            f"Descarga el ZIP de {DESCARGA_MANUAL_URL} y colócalo ahí."
        )
    print(f"  Descomprimiendo {zip_path.name} en {extract_to}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)
    return extract_to


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--list" in args:
        for k, v in CONVOCATORIAS.items():
            print(f"  {k}  {v['label']}")
        sys.exit(0)

    extract_only = "--extract-only" in args
    targets      = [a for a in args if not a.startswith("--")]
    force        = "--force" in args

    if not targets:
        targets = list(CONVOCATORIAS.keys())

    action = "Extrayendo" if extract_only else "Descargando"
    print(f"{action} {len(targets)} convocatoria(s)...\n")
    for conv_id in targets:
        if conv_id not in CONVOCATORIAS:
            print(f"[ERROR] Convocatoria desconocida: {conv_id}")
            continue
        try:
            if extract_only:
                extract_manual_zip(conv_id)
            else:
                download_zip(conv_id, force=force)
            check_availability(conv_id)
        except Exception as e:
            print(f"  [FALLO] {conv_id}: {e}")
