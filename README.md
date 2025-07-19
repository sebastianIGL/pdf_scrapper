# Extractor de Planes de Salud (PyMuPDF)

Este proyecto permite extraer información de cuadros específicos en PDFs de "Planes de Salud".
Funciona en dos fases:

1. **Captura interactiva** (`capture_pdf.py`) – Seleccionas los rectángulos y se genera la plantilla `rect_template.json`.
2. **Extracción masiva** (`extract_with_template.py`) – Se aplica esa plantilla a uno o varios PDFs y se construye (o actualiza) el CSV `plan_de_salud.csv` con los datos capturados.

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 1️⃣  Capturar coordenadas de un PDF

```bash
python3 capture_pdf.py data/pdfs/PPS25130.pdf
```

### Para cada nuevo PDF que tenga la misma estructura (mismo diseño, posiciones idénticas)
####    python3 extract_with_template.py rect_template.json RUTA/AL/NUEVO_PLAN.pdf -o plan_de_salud.csv

### o bien, para procesar una carpeta completa:
#### python3 extract_with_template.py rect_template.json carpeta_con_pdfs -o plan_de_salud.csv




Pasos en la ventana interactiva:
1. Arrastra para dibujar un rectángulo sobre el PDF.
2. Ingresa la etiqueta correspondiente (`alto`, `bajo`, `alto_ambulatoria`, `bajo_ambulatorio`).
3. Repite para todos los cuadros requeridos.
4. Cierra la ventana.
5. Responde `s` cuando pregunte si quieres guardar la plantilla.

Se generará `rect_template.json` y se añadirá (o creará) una fila en `plan_de_salud.csv` con los textos capturados para ese PDF.

## 2️⃣  Extraer datos con la plantilla

### a) PDF específico
```bash
python3 extract_with_template.py rect_template.json RUTA/AL/OTRO_PLAN.pdf -o plan_de_salud.csv
```

### b) Carpeta con muchos PDFs
```bash
python3 extract_with_template.py rect_template.json RUTA/A/CARPETA_PDFS -o plan_de_salud.csv
```

En ambos casos el script añadirá una nueva fila al CSV `plan_de_salud.csv` por cada PDF procesado con las columnas:

| nombre_plan | alto | bajo | alto_ambulatoria | bajo_ambulatorio |

## Archivos/clases principales

| Archivo | Descripción |
|---------|-------------|
| `capture_pdf.py` | Interfaz gráfica (matplotlib) para seleccionar rectángulos y construir la plantilla + CSV individual. |
| `extract_with_template.py` | Procesa uno o varios PDFs aplicando la plantilla y actualiza `plan_de_salud.csv`. |
| `requirements.txt` | Dependencias del proyecto (PyMuPDF, pandas, matplotlib, Pillow). |

## Notas

• El sistema de coordenadas de PyMuPDF usa *puntos PDF* (1 punto = 1/72 de pulgada) con el origen `(0,0)` en la esquina superior-izquierda.  
• El proyecto asume que el contenido requerido está siempre en la primera página.  
• Si cambias el diseño de los PDFs, ejecuta de nuevo `capture_pdf.py` para generar una nueva plantilla.