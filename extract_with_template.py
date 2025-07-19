"""extract_with_template.py

Uso:
    python3 extract_with_template.py TEMPLATE.json RUTA/AL/PDF_O_CARPETA [-o salida.csv]

Aplica una plantilla de rectángulos (JSON etiqueta → [x0,y0,x1,y1]) a uno o
muchos PDF y genera un CSV/DataFrame con los textos extraídos.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

import fitz  # type: ignore


def load_template(path: Path) -> Dict[str, Tuple[float, float, float, float]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: tuple(v) for k, v in data.items()}  # type: ignore


def extract_single(pdf_path: Path, rect_map: Dict[str, Tuple[float, float, float, float]]) -> Dict[str, str]:
    with fitz.open(pdf_path) as doc:
        page = doc[0]
        result: Dict[str, str] = {"nombre": pdf_path.stem}
        for key, rect in rect_map.items():
            txt = page.get_text("text", clip=fitz.Rect(rect)).strip()  # type: ignore[attr-defined]
            result[key] = " ".join(txt.split())
        return result


def main():
    parser = argparse.ArgumentParser(description="Extrae texto usando una plantilla de rectángulos")
    parser.add_argument("template", type=Path, help="Archivo JSON con la plantilla")
    parser.add_argument("pdf_path", type=Path, help="PDF individual o carpeta con PDFs")
    parser.add_argument("-o", "--output", type=Path, default=Path("batch_output.csv"), help="CSV de salida")
    args = parser.parse_args()

    rect_map = load_template(args.template)

    rows = []
    if args.pdf_path.is_file():
        rows.append(extract_single(args.pdf_path, rect_map))
    else:
        for pdf_file in sorted(args.pdf_path.glob("*.pdf")):
            rows.append(extract_single(pdf_file, rect_map))

    df = pd.DataFrame(rows)

    # Renombrar y asegurar columnas obligatorias
    df = df.rename(columns={"nombre": "nombre_plan"})

    expected_cols = [
        "nombre_plan",
        "alto",
        "medio",
        "bajo",
        "alto_ambu",
        "medio_ambu",
        "bajo_ambu",
    ]

    # Limitar / rellenar columnas
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    df = df.loc[:, expected_cols]

    print("\n--- planes_de_salud parcial ---")
    print(df)

    # Acumular en archivo existente si ya existe
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        prev = pd.read_csv(args.output)
        # Asegurar mismas columnas y orden, eliminar duplicados
        for col in expected_cols:
            if col not in prev.columns:
                prev[col] = ""
        prev = prev.loc[:, expected_cols]

        # Concatenar y resetear índice
        planes_de_salud = pd.concat([prev, df], ignore_index=True)
    else:
        planes_de_salud = df

    # Guardar actualizado
    planes_de_salud.to_csv(args.output, index=False, encoding="utf-8")
    print(f"\nArchivo actualizado: {args.output.resolve()}")

    # Mostrar DataFrame final
    print("\n=== planes_de_salud actualizado ===")
    print(planes_de_salud)


if __name__ == "__main__":
    main() 