import sqlite3
from datetime import date, timedelta, datetime as dt

import streamlit as st

# =========================
# CONFIG DB
# =========================
DB_NAME = "agenda.db"


def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Tabla de clientes
    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            business_name TEXT,
            address TEXT,
            zone TEXT,
            phone TEXT,
            notes TEXT,
            is_monthly INTEGER DEFAULT 0,
            monthly_day INTEGER
        );
    """)

    # Tabla de servicios (citas)
    c.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            service_type TEXT,
            pest_type TEXT,
            address TEXT,
            zone TEXT,
            phone TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            price REAL,
            status TEXT,
            notes TEXT,
            created_at TEXT,
            is_monthly_service INTEGER DEFAULT 0
        );
    """)

    conn.commit()
    conn.close()


# ---------- FUNCIONES DB ----------
def add_client(name, business_name, address, zone, phone, notes,
               is_monthly=False, monthly_day=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO clients (
            name, business_name, address, zone, phone, notes,
            is_monthly, monthly_day
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        business_name,
        address,
        zone,
        phone,
        notes,
        1 if is_monthly else 0,
        monthly_day,
    ))
    conn.commit()
    conn.close()


def update_client(client_id, name, business_name, address, zone, phone, notes):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE clients
        SET name = ?, business_name = ?, address = ?, zone = ?, phone = ?, notes = ?
        WHERE id = ?
    """, (
        name,
        business_name,
        address,
        zone,
        phone,
        notes,
        client_id,
    ))
    conn.commit()
    conn.close()


def delete_client(client_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()


def get_clients():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM clients ORDER BY business_name, name;")
    rows = c.fetchall()
    conn.close()
    return rows


def add_appointment(client_name, service_type, pest_type,
                    address, zone, phone, fecha, hora,
                    price, status, notes, is_monthly_service=False):
    conn = get_conn()
    c = conn.cursor()
    created_at = dt.now().isoformat(timespec="seconds")

    c.execute("""
        INSERT INTO appointments (
            client_name, service_type, pest_type,
            address, zone, phone,
            date, time, price,
            status, notes, created_at, is_monthly_service
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        client_name,
        service_type,
        pest_type,
        address,
        zone,
        phone,
        fecha,
        hora,
        price,
        status,
        notes,
        created_at,
        1 if is_monthly_service else 0,
    ))
    conn.commit()
    conn.close()


def get_appointments(date_from=None, date_to=None, status=None):
    conn = get_conn()
    c = conn.cursor()

    query = "SELECT * FROM appointments WHERE 1=1"
    params = []

    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date <= ?"
        params.append(date_to)
    if status and status != "Todos":
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY date, time"

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows


def update_appointment_full(appointment_id, client_name, service_type, pest_type,
                            address, zone, phone, fecha, hora,
                            price, status, notes, is_monthly_service):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE appointments
        SET client_name = ?,
            service_type = ?,
            pest_type = ?,
            address = ?,
            zone = ?,
            phone = ?,
            date = ?,
            time = ?,
            price = ?,
            status = ?,
            notes = ?,
            is_monthly_service = ?
        WHERE id = ?
    """, (
        client_name,
        service_type,
        pest_type,
        address,
        zone,
        phone,
        fecha,
        hora,
        price,
        status,
        notes,
        1 if is_monthly_service else 0,
        appointment_id,
    ))
    conn.commit()
    conn.close()


# =========================
# INICIO APP
# =========================
init_db()

st.set_page_config(page_title="Agenda FX 2025", layout="wide")
st.title("📅 Agenda Fumigaciones Xterminio")

# ---------------------------
# CSS (personalizado — caja oscura + menú más marcado)
# ---------------------------
st.markdown("""
<style>
/* Inputs con fondo negro y texto blanco (solo los text inputs estándar) */
input[type="text"], input[type="time"], input[type="date"] {
    background-color: #000000 !important;
    color: #ffffff !important;
    border-radius: 6px !important;
}

/* Estilo para el selectbox/popover y menú de sugerencias */
div[data-baseweb="select"] > div {
    background-color: #0b0b0b !important;
    color: #ffffff !important;
    border: 2px solid #4CAF50 !important;     /* Borde verde más marcado */
    border-radius: 6px !important;
}

div[data-baseweb="popover"] {
    background-color: #0b0b0b !important;
    border: 2px solid #4CAF50 !important;     /* Marca la cuadrícula */
    border-radius: 8px !important;
}

/* Lista dentro del menú de sugerencias */
div[data-baseweb="menu"] ul {
    background: #0b0b0b !important;
    border: 1px solid #4CAF50 !important;
    border-radius: 8px !important;
}

/* Items de la lista más visibles */
div[data-baseweb="menu-item"] {
    padding: 10px !important;
    border-bottom: 1px solid #2b2b2b !important;
}

/* Highlight al pasar el mouse */
div[data-baseweb="menu-item"]:hover {
    background-color: #064d06 !important;     /* Verde oscuro al hover */
}
</style>
""", unsafe_allow_html=True)

# Estado inicial en session_state para los campos del formulario
for key in [
    "buscar_cliente_text", "sugerencia_sel", "selected_cliente_id",
    "prefill_name", "prefill_business", "prefill_phone",
    "prefill_zone", "prefill_address", "prefill_notes"
]:
    if key not in st.session_state:
        st.session_state[key] = "" if "prefill" in key or "buscar" in key else None

# Cargar clientes
clientes = get_clients()

# Crear mapa de etiquetas a cliente (etiqueta para mostrar en sugerencias)
mapa_clientes = {}
etiquetas = []
for c in clientes:
    etiqueta = c["business_name"] or c["name"]
    if c["business_name"] and c["name"]:
        etiqueta = f"{c['business_name']} ({c['name']})"
    etiquetas.append(etiqueta)
    mapa_clientes[etiqueta] = c

# ---------------------------
# BUSCADOR AUTOCOMPLETE (input + sugerencias)
# ---------------------------
st.subheader("Buscar cliente rápido (escribe y selecciona)")

col_search_1, col_search_2 = st.columns([3, 1])

with col_search_1:
    # input donde el usuario escribe el nombre (se actualiza en session_state['buscar_cliente_text'])
    buscar_text = st.text_input(
        "Escribe nombre o negocio...",
        value=st.session_state["buscar_cliente_text"],
        key="buscar_cliente_text",
        placeholder="Empieza a escribir para ver sugerencias..."
    )

with col_search_2:
    # Botón de buscar tradicional (por si el usuario prefiere presionar)
    if st.button("🔍 Buscar"):
        # Si hay coincidencia exacta (etiqueta completa) la seleccionamos
        if buscar_text and buscar_text in mapa_clientes:
            sel = buscar_text
            st.session_state["sugerencia_sel"] = sel
            # Llenar campos
            cliente = mapa_clientes[sel]
            st.session_state["selected_cliente_id"] = cliente["id"]
            st.session_state["prefill_name"] = cliente["name"] or ""
            st.session_state["prefill_business"] = cliente["business_name"] or ""
            st.session_state["prefill_phone"] = cliente["phone"] or ""
            st.session_state["prefill_zone"] = cliente["zone"] or ""
            st.session_state["prefill_address"] = cliente["address"] or ""
            st.session_state["prefill_notes"] = cliente["notes"] or ""
        else:
            # Buscamos coincidencias parciales y, si hay exactamente 1, la usamos
            query = (buscar_text or "").strip().lower()
            matches = [e for e in etiquetas if query and query in e.lower()]
            if len(matches) == 1:
                sel = matches[0]
                st.session_state["sugerencia_sel"] = sel
                cliente = mapa_clientes[sel]
                st.session_state["selected_cliente_id"] = cliente["id"]
                st.session_state["prefill_name"] = cliente["name"] or ""
                st.session_state["prefill_business"] = cliente["business_name"] or ""
                st.session_state["prefill_phone"] = cliente["phone"] or ""
                st.session_state["prefill_zone"] = cliente["zone"] or ""
                st.session_state["prefill_address"] = cliente["address"] or ""
                st.session_state["prefill_notes"] = cliente["notes"] or ""
            else:
                # si hay 0 o >1 coincidencias, solo informamos
                if not matches:
                    st.warning("No se encontraron coincidencias con lo escrito.")
                else:
                    st.info(f"Se encontraron {len(matches)} coincidencias. Selecciona una sugerencia.")

# Mostrar sugerencias filtradas dinámicamente (selectbox con on_change)
# Filtrar etiquetas según lo escrito
texto = (st.session_state["buscar_cliente_text"] or "").strip().lower()
if texto:
    opciones_filtradas = [e for e in etiquetas if texto in e.lower()]
else:
    opciones_filtradas = []

# Agregamos una opción vacía al inicio
opciones_para_select = ["--"] + opciones_filtradas

def on_select_sugerencia():
    sel = st.session_state.get("sugerencias")
    if sel and sel != "--":
        cliente = mapa_clientes.get(sel)
        if cliente:
            st.session_state["selected_cliente_id"] = cliente["id"]
            st.session_state["prefill_name"] = cliente["name"] or ""
            st.session_state["prefill_business"] = cliente["business_name"] or ""
            st.session_state["prefill_phone"] = cliente["phone"] or ""
            st.session_state["prefill_zone"] = cliente["zone"] or ""
            st.session_state["prefill_address"] = cliente["address"] or ""
            st.session_state["prefill_notes"] = cliente["notes"] or ""
            # actualizar el texto del buscador para mostrar la etiqueta seleccionada
            st.session_state["buscar_cliente_text"] = sel
            # opcional: limpiar la selección para que si se vuelve a abrir no quede seleccionado
            # st.session_state["sugerencias"] = "--"

# Mostrar selectbox solo si hay opciones filtradas
if opciones_filtradas:
    st.selectbox(
        "Sugerencias:",
        options=opciones_para_select,
        key="sugerencias",
        index=0,
        on_change=on_select_sugerencia
    )
else:
    st.write("")  # espacio cuando no hay sugerencias


st.markdown("---")

# =========================
# FORMULARIO CLIENTE + SERVICIO (usa los valores prefijados si hay selección)
# =========================
st.subheader("Nuevo servicio / Guardar cliente y agendar")

with st.form("form_servicio_cliente", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)

    # -------- DATOS DEL CLIENTE --------
    with col1:
        name = st.text_input(
            "Nombre de la persona / contacto",
            value=st.session_state.get("prefill_name", ""),
            key="form_name"
        )
        business_name = st.text_input(
            "Nombre del negocio",
            value=st.session_state.get("prefill_business", ""),
            key="form_business"
        )

    with col2:
        phone = st.text_input(
            "Teléfono",
            value=st.session_state.get("prefill_phone", ""),
            key="form_phone"
        )
        zone = st.text_input(
            "Colonia / zona",
            value=st.session_state.get("prefill_zone", ""),
            key="form_zone"
        )
        address = st.text_input(
            "Dirección",
            value=st.session_state.get("prefill_address", ""),
            key="form_address"
        )

    with col3:
        # -------- DATOS DEL SERVICIO --------
        hoy = date.today()
        service_date = st.date_input("Fecha del servicio", value=hoy, key="form_date")
        service_time = st.time_input("Hora del servicio", key="form_time")
        price = st.number_input("Precio del servicio ($)", min_value=0.0, step=50.0, key="form_price")
        status = st.selectbox(
            "Estado del servicio",
            ["Pendiente", "Confirmado", "Realizado", "Cobrado"],
            key="form_status"
        )

    pest_type = st.text_input("Tipo de plaga (cucaracha, garrapata, termita, etc.)", key="form_pest")
    notes = st.text_area("Notas (referencias, paquete, observaciones, etc.)",
                         value=st.session_state.get("prefill_notes", ""),
                         key="form_notes")

    is_monthly_service = st.checkbox("Servicio mensual", value=False, key="form_is_monthly")

    guardar_cliente_servicio = st.form_submit_button("🟩 Guardar cliente y agendar servicio")

    if guardar_cliente_servicio:
        # Validaciones mínimas
        if not name and not business_name:
            st.error("Pon al menos el nombre de la persona o del negocio.")
        else:
            # Si el cliente ya existía (se seleccionó), actualizamos sus datos guardados
            sel_id = st.session_state.get("selected_cliente_id")
            if sel_id:
                # actualizar cliente existente
                update_client(
                    client_id=sel_id,
                    name=name or (business_name or "Cliente sin nombre"),
                    business_name=business_name,
                    address=address,
                    zone=zone,
                    phone=phone,
                    notes=notes,
                )
            else:
                # crear nuevo cliente
                add_client(
                    name=name or (business_name or "Cliente sin nombre"),
                    business_name=business_name,
                    address=address,
                    zone=zone,
                    phone=phone,
                    notes=notes,
                    is_monthly=False,
                    monthly_day=None,
                )

            # Agendar el servicio con el nombre mostrado (negocio o nombre)
            nombre_mostrar = business_name or name
            add_appointment(
                client_name=nombre_mostrar,
                service_type="Negocio" if business_name else "Casa",
                pest_type=pest_type,
                address=address,
                zone=zone,
                phone=phone,
                fecha=str(service_date),
                hora=str(service_time)[:5],
                price=price if price > 0 else None,
                status=status,
                notes=notes,
                is_monthly_service=is_monthly_service,
            )

            st.success("✅ Servicio agendado. (Cliente guardado/actualizado si aplica)")
            # Limpiar prefill y selección
            st.session_state["selected_cliente_id"] = None
            st.session_state["prefill_name"] = ""
            st.session_state["prefill_business"] = ""
            st.session_state["prefill_phone"] = ""
            st.session_state["prefill_zone"] = ""
            st.session_state["prefill_address"] = ""
            st.session_state["prefill_notes"] = ""
            st.session_state["buscar_cliente_text"] = ""
            st.session_state["sugerencias"] = "--"
            st.experimental_rerun()

# ===== resto de tu app (tablas, edición, etc.) =====
# Aquí puedes seguir integrando la parte de "Servicios agendados" y "Buscar / editar cliente"
# usando las mismas funciones DB que ya están definidas (get_appointments, update_appointment_full, delete_appointment, etc.).
# Por ahora dejo fuera el resto para centrar la respuesta en el autocompletado y llenado automático del formulario.
