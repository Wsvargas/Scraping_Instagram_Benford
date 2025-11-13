import streamlit as st
import requests
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter
from dotenv import load_dotenv
import os
import math
from io import BytesIO
import base64
from datetime import datetime
import time

# ============================
#   SISTEMA DE LOGS
# ============================

LOGFILE = "logs.txt"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] {msg}"
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(linea + "\n")
    st.write(f"📝 {msg}")

log("=== INICIO DE EJECUCIÓN ===")

# ============================
#  CARGA COOKIES
# ============================

load_dotenv("cookies.env")

COOKIES = {
    "sessionid": os.getenv("SESSIONID"),
    "csrftoken": os.getenv("CSRFTOKEN"),
    "ds_user_id": os.getenv("DS_USER_ID"),
    "mid": os.getenv("MID"),
    "ig_did": os.getenv("IG_DID"),
    "rur": os.getenv("RUR"),
    "ps_l": os.getenv("PS_L"),
    "ps_n": os.getenv("PS_N"),
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-IG-App-ID": "936619743392459",
    "X-CSRFToken": COOKIES["csrftoken"],
    "Referer": "https://www.instagram.com/",
    "Accept": "*/*",
}

# ============================
# FUNCIONES BENFORD
# ============================

def primer_digito(n):
    return int(str(n)[0])

def benford_dist():
    return {k: math.log10(1 + 1/k) for k in range(1, 10)}

# ============================
# INSTAGRAM API FUNCIONES
# ============================

def get_user_id(username):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    log(f"Accediendo a URL: {url}")
    r = requests.get(url, cookies=COOKIES, headers=HEADERS)

    if r.status_code != 200:
        log(f"Error HTTP: {r.status_code} - {r.text[:200]}")
        return None

    data = r.json()
    if "data" not in data or "user" not in data["data"]:
        return None

    uid = data["data"]["user"]["id"]
    total_followers = data["data"]["user"]["edge_followed_by"]["count"]
    return uid, total_followers


def get_all_followers(user_id, max_total=550):
    """
    Obtiene seguidores con paginación real.
    Instagram devuelve aprox 12–50 por página.
    Se limita estrictamente a 'max_total' seguidores.
    """

    followers = []
    next_max_id = None

    while True:

        # Construcción de URL con paginación
        url = f"https://www.instagram.com/api/v1/friendships/{user_id}/followers/?count=50"
        if next_max_id:
            url += f"&max_id={next_max_id}"

        log(f"Consultando seguidores paginados: {url}")
        r = requests.get(url, cookies=COOKIES, headers=HEADERS)

        if r.status_code != 200:
            log(f"❌ Error al obtener seguidores (HTTP {r.status_code})")
            break

        data = r.json()

        if "users" not in data:
            log("❌ No se encontraron usuarios en la respuesta.")
            break

        # Añadir usuarios obtenidos
        followers.extend(data["users"])

        log(f"🧮 Acumulados: {len(followers)} seguidores...")

        # Corte EXACTO al llegar a max_total
        if len(followers) >= max_total:
            log(f"⛔ Alcanzado límite máximo de {max_total} seguidores.")
            followers = followers[:max_total]
            break

        # Obtener next_max_id
        next_max_id = data.get("next_max_id")

        if not next_max_id:
            log("⛔ Instagram no devolvió más paginación. Fin.")
            break

        # Delay anti-bloqueo entre páginas
        time.sleep(2 + (os.getpid() % 3))

    return followers

    """
    Obtiene seguidores con paginación real.
    Instagram devuelve ~12 por página.
    max_total: máximo de seguidores a recopilar.
    """
    followers = []
    next_max_id = None

    while True:
        url = f"https://www.instagram.com/api/v1/friendships/{user_id}/followers/?count=50"
        if next_max_id:
            url += f"&max_id={next_max_id}"

        log(f"Consultando seguidores paginados: {url}")
        r = requests.get(url, cookies=COOKIES, headers=HEADERS)

        if r.status_code != 200:
            log(f"Error al obtener seguidores (HTTP {r.status_code})")
            break

        data = r.json()

        if "users" not in data:
            log("No se encontraron usuarios en la respuesta.")
            break

        followers.extend(data["users"])
        log(f"Acumulados: {len(followers)} seguidores...")

        # Si ya tenemos suficientes, cortamos
        if len(followers) >= max_total:
            break

        # La clave de paginación:
        next_max_id = data.get("next_max_id")

        if not next_max_id:
            break  # No hay más páginas

    return followers[:max_total]



def get_follower_follower_count(pk, retries=3):
    """
    Obtiene el número de followers de un usuario.
    Incluye manejo de errores, reintentos y valores inválidos.
    """
    url = f"https://www.instagram.com/api/v1/users/{pk}/info/"

    for intento in range(1, retries + 1):
        try:
            r = requests.get(url, cookies=COOKIES, headers=HEADERS, timeout=10)

            # DEBUG: Mostrar respuesta cuando no es JSON
            if intento == 1 and not r.text.strip().startswith("{"):
                with open("respuesta_bloqueo.html", "w", encoding="utf-8") as f:
                    f.write(r.text)
                log("⚠️ Guardado HTML de bloqueo en respuesta_bloqueo.html")


            # Respuesta vacía o HTML (caso típico)
            if not r.text.strip().startswith("{"):
                log(f"⚠️ Respuesta no-JSON para pk={pk}. Intento {intento}/{retries}")
                time.sleep(5)
                continue

            data = r.json()

            if "user" not in data:
                log(f"⚠️ Sin campo 'user' en respuesta pk={pk}. Intento {intento}/{retries}")
                time.sleep(5)
                continue

            return data["user"].get("follower_count", None)

        except requests.exceptions.JSONDecodeError:
            log(f"❌ JSONDecodeError en pk={pk}. Intento {intento}/{retries}")
            time.sleep(5)
            continue

        except Exception as e:
            log(f"❌ Error general con pk={pk}: {e}. Intento {intento}/{retries}")
            time.sleep(5)
            continue

    # Si todos los reintentos fallaron:
    log(f"⛔ No se pudo obtener followers del pk={pk} tras {retries} intentos.")
    return None


# ============================
# STREAMLIT UI
# ============================

st.title("🔍 Analizador de Followers – Ley de Benford")
st.write("Detecta si un perfil tiene seguidores **orgánicos o bots** mediante distribución estadística.")
# Mantener Excel en memoria para que no se borre al recargar
if "excel_data" not in st.session_state:
    st.session_state["excel_data"] = None

username = st.text_input("Usuario a analizar:")

if st.button("Analizar"):
    uid_info = get_user_id(username)
    if not uid_info:
        st.error("❌ Usuario no encontrado o API bloqueada.")
        st.stop()

    user_id, total_followers = uid_info

    st.success(f"📌 Total de seguidores del usuario **{username}**: **{total_followers:,}**")

    st.info("📌 Obteniendo primeros seguidores…")
    seguidores = get_all_followers(user_id, max_total=550)


    data_list = []
    follower_counts = []

    for seg in seguidores:
        pk = seg["pk"]
        uname = seg["username"]
        followers_seg = get_follower_follower_count(pk)
        time.sleep(5)  # Evitar bloqueos por muchas solicitudes

        if followers_seg is None:
            continue

        d = primer_digito(followers_seg)

        # 🔒 PROTECCIÓN CONTRA DÍGITOS INVÁLIDOS (0, None, NaN, strings raras)
        if d not in range(1, 10):
            log(f"⚠️ Ignorado seguidor {uname} → dígito inválido: {d}")
            continue

        follower_counts.append(followers_seg)

        data_list.append({
            "usuario": uname,
            "followers_count": followers_seg,
            "primer_digito": d
        })


    if len(data_list) == 0:
        st.error("No se pudo obtener datos de los seguidores.")
        st.stop()

    # ===============================
    # BENFORD CALCULO
    # ===============================

    primeros = [x["primer_digito"] for x in data_list]
    dist_real_cnt = Counter(primeros)
    total = sum(dist_real_cnt.values())
    dist_real = {k: dist_real_cnt[k]/total for k in range(1, 10)}

    dist_benford = benford_dist()

    # Tabla comparativa
    tabla = []
    anomalías = []
    for d in range(1, 10):
        real = dist_real.get(d, 0)
        ben = dist_benford[d]
        diff = (real - ben) * 100

        tabla.append({
            "dígito": d,
            "observado": real * 100,
            "esperado": ben * 100,
            "diferencia": diff
        })

        if abs(diff) > 4:  
            anomalías.append(d)

    df_tabla = pd.DataFrame(tabla)

    # ===============================
    # GRAFICO PROFESIONAL
    # ===============================

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.bar(dist_real.keys(), [v*100 for v in dist_real.values()], label="Observado", alpha=0.6, color="#FF6B6B")
    ax.plot(dist_benford.keys(), [v*100 for v in dist_benford.values()], "o-", label="Benford", color="#FFA600")

    ax.set_xlabel("Dígito inicial")
    ax.set_ylabel("Porcentaje (%)")
    ax.set_title("Distribución de dígitos iniciales")

    ax.grid(True, alpha=0.3)
    ax.legend()

    st.pyplot(fig)

    # ===============================
    # TABLA DETALLADA
    # ===============================

    st.write("### Tabla Analítica Comparativa")
    st.dataframe(df_tabla.style.format({
        "observado": "{:.2f}%",
        "esperado": "{:.2f}%",
        "diferencia": "{:.2f}%"
    }))

    # ===============================
    # DETECCIÓN FINAL
    # ===============================

    if anomalías:
        st.warning(f"⚠️ Anomalía detectada en los dígitos: {', '.join(map(str, anomalías))}!")
    else:
        st.success("No se detectan anomalías significativas.")

    desviación_total = sum(abs((dist_real[d]-dist_benford[d])) for d in range(1, 10))
    st.info(f"📊 Desviación total: **{desviación_total:.4f}**")

    resultado = "SOSPECHOSO" if desviación_total > 0.25 else "ORGÁNICO"
    if resultado == "SOSPECHOSO":
        st.error(f"⚠️ El perfil **{username}** es **SOSPECHOSO**.")
    else:
        st.success(f"✅ El perfil **{username}** parece **ORGÁNICO**.")

    # ===============================
    # EXPORTAR EXCEL
    # ===============================

    df_export = pd.DataFrame(data_list)
    df_export["benford_prob"] = df_export["primer_digito"].apply(lambda d: dist_benford[d])
    df_export["desviacion"] = df_export["primer_digito"].apply(lambda d: abs(dist_real[d] - dist_benford[d]))
    df_export["es_bot"] = df_export["desviacion"] > 0.04

    # ===============================
    #  GUARDAR EXCEL AUTOMÁTICO LOCAL
    # ===============================

    folder = "resultados"
    os.makedirs(folder, exist_ok=True)

    excel_path = os.path.join(folder, f"{username}_benford.xlsx")

    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Benford')

    log(f"📂 Excel guardado automáticamente en: {excel_path}")

    # ===============================
    #  GUARDAR EN MEMORIA PARA STREAMLIT
    # ===============================

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Benford')

    st.session_state["excel_data"] = buffer.getvalue()


    