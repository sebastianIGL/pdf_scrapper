"""capture_pdf.py

Script interactivo: permite abrir la primera página de un PDF, seleccionar
uno o varios rectángulos con el ratón y obtener el texto contenido en cada
uno de ellos. Cada rectángulo se asocia a una etiqueta (nombre de campo) que
el usuario introduce por consola. Al finalizar, se muestra un DataFrame con
los datos capturados y se pregunta si se desea exportarlo a CSV.

Uso:
    python3 capture_pdf.py RUTA/AL/PDF.pdf

Dependencias: PyMuPDF, matplotlib, pillow, pandas
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import List, Dict, Any

import fitz  # type: ignore
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
from matplotlib.patches import Rectangle
from PIL import Image


class PDFInteractiveCapturer:
    def __init__(self, pdf_path: Path, dpi: int = 150) -> None:
        if not pdf_path.exists():
            print(f"[ERROR] No se encontró el archivo: {pdf_path}")
            sys.exit(1)

        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.page = self.doc[0]
        self.scale = dpi / 72  # PDF points → pixels
        self.dpi = dpi

        # Datos capturados
        self.rows: List[Dict[str, Any]] = []
        self.df: pd.DataFrame | None = None

        # Pre-render
        pix = self.page.get_pixmap(dpi=dpi)  # type: ignore[attr-defined]
        self.img = Image.open(io.BytesIO(pix.tobytes("ppm")))

        # Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 11))
        self.ax.imshow(self.img)
        self.ax.set_title(
            "Arrastra para seleccionar un rectángulo – Cierra la ventana para finalizar"
        )
        self.ax.axis("off")

        # Rectangle selector
        self.selector = RectangleSelector(
            self.ax,
            self.on_select,
            useblit=True,
            button=None,
            minspanx=5,
            minspany=5,
            spancoords="pixels",
        )

    # ----------------------------------------------------------------------------------
    # Callbacks
    # ----------------------------------------------------------------------------------
    def on_select(self, eclick, erelease):
        """Se llama cuando el usuario dibuja un rectángulo."""
        x0, y0 = eclick.xdata, eclick.ydata
        x1, y1 = erelease.xdata, erelease.ydata

        # Normalizar a esquina sup-izq y inf-der
        x0, x1 = sorted([x0, x1])
        y0, y1 = sorted([y0, y1])

        # Dibujar rectángulo permanente
        rect_patch = Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, edgecolor="red")
        self.ax.add_patch(rect_patch)
        self.fig.canvas.draw()

        # Convertir píxeles → puntos PDF
        x0_pdf, y0_pdf = x0 / self.scale, y0 / self.scale
        x1_pdf, y1_pdf = x1 / self.scale, y1 / self.scale

        # Extraer texto en el rectángulo
        rect = fitz.Rect(x0_pdf, y0_pdf, x1_pdf, y1_pdf)
        raw_text = self.page.get_text("text", clip=rect).strip()  # type: ignore[attr-defined]
        clean_text = " ".join(raw_text.split())

        print("\nRectángulo seleccionado (puntos PDF):", (x0_pdf, y0_pdf, x1_pdf, y1_pdf))
        print("Texto capturado:")
        print(clean_text or "<vacío>")

        label = input("Etiqueta/columna para este texto (Enter para descartar): ").strip()
        if not label:
            print("Rectángulo descartado.")
            return

        self.rows.append(
            {
                "etiqueta": label,
                "texto": clean_text,
                "x0": round(x0_pdf, 2),
                "y0": round(y0_pdf, 2),
                "x1": round(x1_pdf, 2),
                "y1": round(y1_pdf, 2),
            }
        )
        # Actualizar DataFrame en vivo
        self.df = pd.DataFrame(self.rows)
        print("\n[Vista previa acumulada]")
        print(self.df)
        print("[OK] Guardado bajo la etiqueta '{label}'. Continúa seleccionando…")

    # ----------------------------------------------------------------------------------
    # Ejecución
    # ----------------------------------------------------------------------------------
    def run(self):
        page_rect = self.page.rect
        print("Dimensiones de la página (puntos PDF):", page_rect)
        print(
            "Instrucciones:\n"
            "  – Arrastra con el ratón para crear un rectángulo.\n"
            "  – Ingresa una etiqueta para guardar el texto; Enter en blanco para descartarlo.\n"
            "  – Cierra la ventana cuando hayas terminado.\n"
        )

        plt.show()  # bloquea hasta cerrar la ventana

        if not self.rows:
            print("No se capturó ningún rectángulo.")
            return

        # Convertir a DataFrame
        df = pd.DataFrame(self.rows)
        print("\n--- Resultado capturado ------------------------------")
        print(df)

        # Preguntar exportación
        answer = input("¿Exportar a CSV (captured_data.csv)? [s/N]: ").strip().lower()
        if answer == "s":
            out_path = Path("captured_data.csv")
            df.to_csv(out_path, index=False, encoding="utf-8")
            print(f"CSV guardado en {out_path.resolve()}")

        # Guardar plantilla de rectángulos
        answer_tpl = input("¿Guardar plantilla de coordenadas para reutilizar? [s/N]: ").strip().lower()
        if answer_tpl == "s":
            import json

            template = {row["etiqueta"]: [row["x0"], row["y0"], row["x1"], row["y1"]] for row in self.rows}
            tpl_path = Path("rect_template.json")
            with tpl_path.open("w", encoding="utf-8") as fp:
                json.dump(template, fp, ensure_ascii=False, indent=2)
            print(f"Plantilla guardada en {tpl_path.resolve()}")

        # ---------------- Plan de Salud acumulado -----------------------
        # Construir fila para plan_de_salud
        expected_cols = [
            "nombre_plan",
            "alto",
            "medio",
            "bajo",
            "alto_ambu",
            "medio_ambu",
            "bajo_ambu",
        ]

        plan_row = {col: "" for col in expected_cols}

        # Usar nombre del PDF como nombre_plan (sin extensión)
        plan_row["nombre_plan"] = self.pdf_path.stem

        for row in self.rows:
            label = row["etiqueta"]
            if label in expected_cols:
                plan_row[label] = row["texto"]

        plan_df_row = pd.DataFrame([plan_row])

        plan_csv = Path("plan_de_salud.csv")
        if plan_csv.exists():
            prev_df = pd.read_csv(plan_csv)
            plan_de_salud = pd.concat([prev_df, plan_df_row], ignore_index=True)
        else:
            plan_de_salud = plan_df_row

        # Asegurar columnas ordenadas
        plan_de_salud = plan_de_salud[expected_cols]
        plan_de_salud.to_csv(plan_csv, index=False, encoding="utf-8")
        print(f"Plan de salud actualizado en {plan_csv.resolve()}")


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 capture_pdf.py RUTA/AL/PDF.pdf")
        sys.exit(1)

    capturer = PDFInteractiveCapturer(Path(sys.argv[1]))
    capturer.run() 