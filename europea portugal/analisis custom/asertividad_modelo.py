"""
asertividad_modelo.py
=====================
Calcula la asertividad del modelo Retention Partner por matricula y titulacion.

Logica:
  - Solo matriculas dadas de baja (fecha_baja no nula)
  - Solo matriculas con al menos 1 prediccion ANTES de la fecha de baja
  - Para cada matricula, toma las ultimas 3 predicciones previas a la baja
  - Evalua si el modelo catalogo como "high" o "medium" en esas predicciones
    tanto en nivel mensual como anual

Entrada : rp_bi_output.csv  (separador "|")
Salida  : asertividad_modelo.csv (separador ";")
"""

import pandas as pd
import numpy as np
import unicodedata

INPUT_FILE  = r"00. LABORATORIO PERSONAL\europea portugal\analisis custom\rp_bi_output.csv"
OUTPUT_FILE = r"00. LABORATORIO PERSONAL\europea portugal\analisis custom\asertividad_modelo.csv"
INPUT_SEP   = "|"
OUTPUT_SEP  = ";"

RIESGO_ALTO_MEDIO = {"high", "medium"}


def remove_accents(val):
    if pd.isna(val) or not isinstance(val, str):
        return val
    return unicodedata.normalize("NFD", val).encode("ascii", "ignore").decode("utf-8")


# ═════════════════════════════════════════════
# 1. LECTURA
# ═════════════════════════════════════════════
print(f"[1/5] Leyendo {INPUT_FILE} ...")
df = pd.read_csv(INPUT_FILE, sep=INPUT_SEP, dtype=str, encoding="utf-8")
print(f"      {len(df):,} filas | {df['id_matricula'].nunique():,} matriculas unicas")


# ═════════════════════════════════════════════
# 2. PREPARACION DE FECHAS Y CAMPOS
# ═════════════════════════════════════════════
print("[2/5] Preparando campos ...")

df["prediction_date"] = pd.to_datetime(df["prediction_date"], format="%Y%m%d")
df["fecha_baja"] = pd.to_datetime(df["fecha_baja"], errors="coerce")

# es_anual: 1 si nivel_riesgo_anual tiene valor, 0 si es nulo/vacio
df["es_anual"] = df["nivel_riesgo_anual"].apply(
    lambda x: 0 if (pd.isna(x) or str(x).strip() == "") else 1
)

# Normalizar niveles de riesgo a minusculas para comparacion
df["nivel_riesgo_mensual_norm"] = df["nivel_riesgo_mensual"].str.lower().str.strip()
df["nivel_riesgo_anual_norm"]   = df["nivel_riesgo_anual"].str.lower().str.strip()

# Limpiar acentos en nombre_titulacion
df["nombre_titulacion"] = df["nombre_titulacion"].apply(remove_accents)


# ═════════════════════════════════════════════
# 3. FILTRO: SOLO MATRICULAS CON BAJA
# ═════════════════════════════════════════════
print("[3/5] Filtrando matriculas con baja ...")

# Obtener la fecha de anulacion por matricula (unica por id_matricula)
fec_baja = (
    df[df["fecha_baja"].notna()]
    [["id_matricula", "fecha_baja"]]
    .drop_duplicates("id_matricula")
    .rename(columns={"fecha_baja": "fec_baja"})
)
print(f"      Matriculas con baja encontradas: {len(fec_baja):,}")

# Unir la fecha de baja al dataframe completo para tener todo el historico
df = df.merge(fec_baja, on="id_matricula", how="inner")

# Quedarse solo con predicciones ANTERIORES a la fecha de baja
df_prev = df[df["prediction_date"] < df["fec_baja"]].copy()
print(f"      Registros con prediccion antes de la baja: {len(df_prev):,}")

mats_validas = df_prev["id_matricula"].nunique()
print(f"      Matriculas con al menos 1 prediccion antes de la baja: {mats_validas:,}")

if mats_validas == 0:
    print()
    print("  ⚠️  ATENCION: No se encontraron matriculas con predicciones anteriores a su fecha de baja.")
    print("      Esto puede deberse a que el historico del archivo no cubre el periodo previo a las bajas.")
    print("      El archivo de salida se generara vacio (solo encabezados).")
    print()


# ═════════════════════════════════════════════
# 4. CALCULAR METRICAS POR MATRICULA
# ═════════════════════════════════════════════
print("[4/5] Calculando asertividad por matricula ...")

resultados = []

for id_mat, grupo in df_prev.groupby("id_matricula"):

    # Ordenar por fecha y tomar las ultimas 3 predicciones antes de la baja
    grupo_sorted = grupo.sort_values("prediction_date", ascending=False)
    ultimas_3    = grupo_sorted.head(3)

    # Datos fijos de la matricula (tomar del primer registro)
    ref               = grupo_sorted.iloc[0]
    cod_titulo        = ref["cod_titulo"]
    nombre_titulacion = ref["nombre_titulacion"]
    modalidad         = ref["modalidad"]
    fec_baja          = ref["fec_baja"]
    es_anual          = int(ref["es_anual"])

    # baja_predicha_mensual: alguna de las ultimas 3 fue high o medium mensual
    baja_predicha_mensual = int(
        ultimas_3["nivel_riesgo_mensual_norm"]
        .isin(RIESGO_ALTO_MEDIO)
        .any()
    )

    # baja_predicha_anual: alguna de las ultimas 3 fue high o medium anual
    # Se guarda como Int64 (nullable integer) para evitar el 0.0/1.0
    if es_anual == 1:
        baja_predicha_anual = int(
            ultimas_3["nivel_riesgo_anual_norm"]
            .isin(RIESGO_ALTO_MEDIO)
            .any()
        )
    else:
        baja_predicha_anual = pd.NA

    # fec_detectado: primera fecha (la mas antigua de las 3) en que fue high o medium
    mask_mensual = ultimas_3["nivel_riesgo_mensual_norm"].isin(RIESGO_ALTO_MEDIO)
    mask_anual   = ultimas_3["nivel_riesgo_anual_norm"].isin(RIESGO_ALTO_MEDIO)
    mask_cualq   = mask_mensual | mask_anual

    fechas_detectadas = ultimas_3.loc[mask_cualq, "prediction_date"]
    fec_detectado = fechas_detectadas.min() if not fechas_detectadas.empty else pd.NaT

    resultados.append({
        "id_matricula"          : id_mat,
        "cod_titulo"            : cod_titulo,
        "nombre_titulacion"     : nombre_titulacion,
        "modalidad"             : modalidad,
        "es_anual"              : es_anual,
        "fecha_baja"       : fec_baja.date() if pd.notna(fec_baja) else None,
        "baja_predicha_mensual" : baja_predicha_mensual,
        "baja_predicha_anual"   : baja_predicha_anual,
        "fec_detectado"         : fec_detectado.date() if pd.notna(fec_detectado) else None,
    })

df_out = pd.DataFrame(resultados)

# Convertir baja_predicha_anual a Int64 (entero nullable: 0, 1 o <NA>)
df_out["baja_predicha_anual"] = df_out["baja_predicha_anual"].astype("Int64")


# ═════════════════════════════════════════════
# 5. GUARDAR
# ═════════════════════════════════════════════
print("[5/5] Guardando resultado ...")
df_out.to_csv(OUTPUT_FILE, sep=OUTPUT_SEP, index=False, encoding="utf-8-sig")

# ─── Resumen ─────────────────────────────────
print()
print("═" * 55)
print("✅  Proceso completado")
print(f"   Matriculas procesadas       : {len(df_out):,}")
if len(df_out) > 0:
    print(f"   Bajas predecidas (mensual)  : {df_out['baja_predicha_mensual'].sum():,}  "
          f"({df_out['baja_predicha_mensual'].mean()*100:.1f}%)")
    anuales = df_out[df_out["es_anual"] == 1]
    if len(anuales) > 0:
        print(f"   Bajas predecidas (anual)    : {anuales['baja_predicha_anual'].sum():,.0f}  "
              f"({anuales['baja_predicha_anual'].mean()*100:.1f}% sobre titulaciones anuales)")
    print(f"   Titulaciones en el output   : {df_out['cod_titulo'].nunique():,}")
print(f"   Archivo generado            : {OUTPUT_FILE}")
print("═" * 55)
