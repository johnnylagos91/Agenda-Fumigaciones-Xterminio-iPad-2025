import pandas as pd
from io import BytesIO

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
            created_at TEXT
        );
    """)

    # Asegurar columna para marcar servicio mensual
    try:
        c.execute("ALTER TABLE appointments ADD COLUMN is_monthly_service INTEGER DEFAULT 0;")
    except Exception:
        # Si ya existe, ignoramos el error
        pass

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
    """Actualiza los datos de un cliente existente."""
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
    """Elimina un cliente de la tabla clients."""
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

    # Nos aseguramos de que la columna exista
    try:
        c.execute("ALTER TABLE appointments ADD COLUMN is_monthly_service INTEGER DEFAULT 0;")
    except Exception:
        pass

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


def update_status(appointment_id, new_status):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE appointments SET status = ? WHERE id = ?",
        (new_status, appointment_id),
    )
    conn.commit()
    conn.close()


def delete_appointment(appointment_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
    conn.commit()
    conn.close()


def update_appointment_full(appointment_id, client_name, service_type, pest_type,
                            address, zone, phone, fecha, hora,
                            price, status, notes, is_monthly_service):
    """Actualiza todos los datos principales de un servicio."""
    conn = get_conn()
    c = conn.cursor()
    # asegurar columna
    try:
        c.execute("ALTER TABLE appointments ADD COLUMN is_monthly_service INTEGER DEFAULT 0;")
    except Exception:
        pass

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

# ==== CSS PERSONALIZADO PARA EL SELECTBOX ====
st.markdown("""
<style>

div[data-baseweb="select"] > div {
    background-color: #000000 !important;     /* Fondo negro */
    border: 2px solid #4CAF50 !important;     /* Borde verde marcado */
    border-radius: 6px !important;
    color: white !important;                  /* Texto blanco para que se vea */
}

div[data-baseweb="popover"] {
    background-color: #000000 !important;     /* Fondo del menú negro */
    border: 2px solid #4CAF50 !important;     /* Marca la cuadrícula */
    border-radius: 8px !important;
    color: white !important;
}

div[data-baseweb="menu"] ul {
    background: #000000 !important;           /* Fondo de la lista negro */
    border: 1px solid #4CAF50 !important;
    border-radius: 8px !important;
}

div[data-baseweb="menu-item"] {
    padding: 10px !important;
    border-bottom: 1px solid #333333 !important;  /* Línea separadora gris */
    color: white !important;
}

/* Highlight al pasar el mouse */
div[data-baseweb="menu-item"]:hover {
    background-color: #333333 !important;     /* Gris oscuro al pasar el mouse */
}

</style>
""", unsafe_allow_html=True)


# Estado para ediciones
if "cliente_edit_id" not in st.session_state:
    st.session_state["cliente_edit_id"] = None
if "servicio_edit_id" not in st.session_state:
    st.session_state["servicio_edit_id"] = None

# 🔄 Botón para limpiar todo y recargar
if st.button("🔄 Actualizar / limpiar pantalla"):
    st.session_state["cliente_edit_id"] = None
    st.session_state["servicio_edit_id"] = None
    
    # LIMPIAR la caja de búsqueda
    st.session_state["buscar_cliente"] = ""

    # LIMPIAR también la coincidencia seleccionada
    st.session_state["coincidencia_cliente"] = "-- Cliente nuevo --"
    
    st.rerun()

hoy = date.today()
dia_hoy = hoy.day

# =========================
# CARGAR CLIENTES
# =========================
clientes = get_clients()

# =========================
# FORMULARIO CLIENTE + SERVICIO
# =========================
st.subheader("Nuevo servicio / Guardar cliente y agendar")

# Lista de clientes guardados
opciones = ["-- Cliente nuevo --"]
mapa_clientes = {}
for c in clientes:
    etiqueta = c["business_name"] or c["name"]
    if c["business_name"] and c["name"]:
        etiqueta = f"{c['business_name']} ({c['name']})"
    opciones.append(etiqueta)
    mapa_clientes[etiqueta] = c

# =========================
# BUSCADOR DE CLIENTES
# =========================

texto_busqueda = st.text_input(
    "Buscar cliente",
    placeholder="Escribe el nombre: Juan, Jardines, Joyería...",
    key="buscar_cliente"
)

# Construcción de lista normal
opciones_completas = []
mapa_clientes = {}

for c in clientes:
    etiqueta = c["business_name"] or c["name"]
    if c["business_name"] and c["name"]:
        etiqueta = f"{c['business_name']} ({c['name']})"
    opciones_completas.append(etiqueta)
    mapa_clientes[etiqueta] = c

# Si hay texto → filtramos solo los que EMPIECEN con eso
if texto_busqueda.strip():
    opciones = ["-- Cliente nuevo --"] + [
        o for o in opciones_completas
        if o.lower().startswith(texto_busqueda.lower())
    ]
else:
    opciones = ["-- Cliente nuevo --"] + opciones_completas

# Selectbox final (ya filtrado)
seleccion = st.selectbox("Coincidencias", opciones, key="coincidencia_cliente")
cliente_sel = mapa_clientes.get(seleccion)

with st.form("form_servicio_cliente", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)

    # -------- DATOS DEL CLIENTE --------
    with col1:
        name = st.text_input(
            "Nombre de la persona / contacto",
            value=cliente_sel["name"] if cliente_sel else "",
        )
        business_name = st.text_input(
            "Nombre del negocio",
            value=cliente_sel["business_name"] if cliente_sel else "",
        )

    with col2:
        phone = st.text_input(
            "Teléfono",
            value=cliente_sel["phone"] if cliente_sel else "",
        )
        zone = st.text_input(
            "Colonia / zona",
            value=cliente_sel["zone"] if cliente_sel else "",
        )
        address = st.text_input(
            "Dirección",
            value=cliente_sel["address"] if cliente_sel else "",
        )

    with col3:
        # -------- DATOS DEL SERVICIO --------
        service_date = st.date_input("Fecha del servicio", value=hoy)
        service_time = st.time_input("Hora del servicio")
        price = st.number_input("Precio del servicio ($)", min_value=0.0, step=50.0)
        status = st.selectbox(
            "Estado del servicio",
            ["Pendiente", "Confirmado", "Realizado", "Cobrado"],
        )

    # Estos siempre empiezan en blanco aunque el cliente exista
    pest_type = st.text_input("Tipo de plaga (cucaracha, garrapata, termita, etc.)")
    notes = st.text_area("Notas (referencias, paquete, observaciones, etc.)")

    # Mensualidad por SERVICIO
    is_monthly_service = st.checkbox("Servicio mensual", value=False)

    # ---------- ÚNICO BOTÓN: GUARDAR CLIENTE Y AGENDAR SERVICIO ----------
    guardar_cliente_servicio = st.form_submit_button("🟩 Guardar cliente y agendar servicio")

    if guardar_cliente_servicio:
        if not name and not business_name:
            st.error("Pon al menos el nombre de la persona o del negocio.")
        else:
            # Si es cliente NUEVO (no seleccionado en "Buscar cliente") → guardar cliente
            if seleccion == "-- Cliente nuevo --":
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

            # Siempre agendar el servicio
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

            st.success(
                "✅ Servicio agendado."
                + (" Cliente guardado." if seleccion == "-- Cliente nuevo --" else "")
            )
            st.rerun()

# =========================
# TABLA SERVICIOS MENSUALES (EN EXPANDER)
# =========================
todos_servicios = get_appointments()
servicios_mensuales = [
    r for r in todos_servicios
    if "is_monthly_service" in r.keys() and r["is_monthly_service"] == 1
]

with st.expander("📌 Servicios marcados como mensuales", expanded=False):
    if not servicios_mensuales:
        st.info("Aún no tienes servicios marcados como mensuales.")
    else:
        tabla_mensuales = [
            {
                "ID": r["id"],
        "Fecha": r["date"],
        "Hora": r["time"],
        "Cliente/Negocio": r["client_name"],
        "Tipo servicio": r["service_type"],
        "Plaga": r["pest_type"],
        "Zona": r["zone"],
        "Dirección": r["address"],
        "Teléfono": r["phone"],
        "Precio": r["price"],
        "Estado": r["status"],
        "Notas": r["notes"],
            }
            for r in servicios_mensuales
        ]
        st.dataframe(tabla_mensuales, use_container_width=True)

# =========================
# SERVICIOS AGENDADOS (EN EXPANDER)
# =========================
with st.expander("📅 Servicios agendados", expanded=False):
    
    st.markdown("#### 📆 Seleccionar semana")

    fecha_semana = st.date_input(
        "Elige cualquier día de la semana",
        value=hoy,
        key="fecha_semana_manual"
    )

    lunes_semana = fecha_semana - timedelta(days=fecha_semana.weekday())
    domingo_semana = lunes_semana + timedelta(days=6)

    st.info(
        f"Mostrando servicios del **{lunes_semana.strftime('%d/%m/%Y')}** "
        f"al **{domingo_semana.strftime('%d/%m/%Y')}**"
    )
    
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        filtro_rango = st.selectbox(
            "Rango de fechas",
            ["Hoy", "Próximos 7 días", "Todos"],
            index=1,
            key="filtro_rango_serv",
        )

    with col_f2:
        filtro_estado = st.selectbox(
            "Estado",
            ["Todos", "Pendiente", "Confirmado", "Realizado", "Cobrado"],
            index=0,
            key="filtro_estado_serv",
        )

    with col_f3:
        st.write("")  # espacio
        st.write("")

    date_from = None
    date_to = None

    if filtro_rango == "Hoy":
        date_from = str(hoy)
        date_to = str(hoy)
    elif filtro_rango == "Próximos 7 días":
        date_from = str(hoy)
        date_to = str(hoy + timedelta(days=7))
        
        date_from = str(lunes_semana)
        date_to = str(domingo_semana)

    rows = get_appointments(date_from=date_from, date_to=date_to, status=filtro_estado)

    if not rows:
        st.info("No hay servicios con los filtros seleccionados.")
    else:
        data = [
            {
                "ID": r["id"],
        "Fecha": r["date"],
        "Hora": r["time"],
        "Cliente/Negocio": r["client_name"],
        "Tipo servicio": r["service_type"],
        "Plaga": r["pest_type"],
        "Zona": r["zone"],
        "Dirección": r["address"],
        "Teléfono": r["phone"],
        "Precio": r["price"],
        "Estado": r["status"],
        "Notas": r["notes"],
            }
            for r in rows
        ]

        st.dataframe(data, use_container_width=True)

        st.markdown("---")
        st.subheader("Buscar / editar servicio")

        # -------- BUSCAR SERVICIO POR ID O NOMBRE --------
        col_bs1, col_bs2, col_bs3 = st.columns([2, 2, 1])

        with col_bs1:
            opciones_ids_serv = ["--"] + [str(r["id"]) for r in rows]
            servicio_id_sel = st.selectbox("Buscar por ID de servicio", opciones_ids_serv)

        with col_bs2:
            opciones_nombres_serv = ["--"]
            etiqueta_a_servicio = {}
            for r in rows:
                etiqueta = f"{r['client_name']} ({r['date']} {r['time']})"
                opciones_nombres_serv.append(etiqueta)
                etiqueta_a_servicio[etiqueta] = r
            servicio_nombre_sel = st.selectbox("Buscar por cliente / negocio", opciones_nombres_serv)

        with col_bs3:
            buscar_servicio_btn = st.button("🔍 Buscar servicio")

        if buscar_servicio_btn:
            servicio_id = None

            # Preferimos búsqueda por ID si se eligió
            if servicio_id_sel != "--":
                try:
                    sid = int(servicio_id_sel)
                    for r in rows:
                        if r["id"] == sid:
                            servicio_id = r["id"]
                            break
                except ValueError:
                    servicio_id = None
            elif servicio_nombre_sel != "--":
                servicio = etiqueta_a_servicio.get(servicio_nombre_sel)
                if servicio:
                    servicio_id = servicio["id"]

            if servicio_id is None:
                st.error("No se encontró el servicio con los datos seleccionados.")
                st.session_state["servicio_edit_id"] = None
            else:
                st.session_state["servicio_edit_id"] = servicio_id

        servicio_edit_id = st.session_state.get("servicio_edit_id")

        # -------- EDITAR / ELIMINAR SERVICIO (solo si se buscó) --------
        if servicio_edit_id:
            selected_row = None
            for r in rows:
                if r["id"] == servicio_edit_id:
                    selected_row = r
                    break

            if selected_row:
                st.markdown("### ✏️ Editar servicio seleccionado")

                # Convertir fecha y hora desde texto
                try:
                    fecha_edit = dt.fromisoformat(selected_row["date"]).date()
                except Exception:
                    try:
                        fecha_edit = dt.strptime(selected_row["date"], "%Y-%m-%d").date()
                    except Exception:
                        fecha_edit = hoy

                try:
                    hora_edit = dt.strptime(selected_row["time"], "%H:%M").time()
                except Exception:
                    hora_edit = dt.now().time()

                is_monthly_service_current = False
                if "is_monthly_service" in selected_row.keys() and selected_row["is_monthly_service"] == 1:
                    is_monthly_service_current = True

                with st.form("form_editar_servicio"):
                    col_e1, col_e2, col_e3 = st.columns(3)

                    with col_e1:
                        client_name_edit = st.text_input(
                            "Cliente / Negocio",
                            value=selected_row["client_name"],
                        )
                        pest_type_edit = st.text_input(
                            "Tipo de plaga",
                            value=selected_row["pest_type"] or "",
                        )

                    with col_e2:
                        zone_edit = st.text_input(
                            "Colonia / zona",
                            value=selected_row["zone"] or "",
                        )
                        address_edit = st.text_input(
                            "Dirección",
                            value=selected_row["address"] or "",
                        )
                        phone_edit = st.text_input(
                            "Teléfono",
                            value=selected_row["phone"] or "",
                        )

                    with col_e3:
                        service_date_edit = st.date_input(
                            "Fecha del servicio (editar)",
                            value=fecha_edit,
                            key="fecha_edit",
                        )
                        service_time_edit = st.time_input(
                            "Hora del servicio (editar)",
                            value=hora_edit,
                            key="hora_edit",
                        )
                        price_edit = st.number_input(
                            "Precio ($) (editar)",
                            min_value=0.0,
                            step=50.0,
                            value=float(selected_row["price"]) if selected_row["price"] is not None else 0.0,
                            key="price_edit",
                        )
                        status_edit = st.selectbox(
                            "Estado (editar)",
                            ["Pendiente", "Confirmado", "Realizado", "Cobrado"],
                            index=["Pendiente", "Confirmado", "Realizado", "Cobrado"].index(selected_row["status"]) if selected_row["status"] in ["Pendiente", "Confirmado", "Realizado", "Cobrado"] else 0,
                            key="status_edit",
                        )

                    notes_edit = st.text_area(
                        "Notas (editar)",
                        value=selected_row["notes"] or "",
                    )

                    is_monthly_service_edit = st.checkbox(
                        "Servicio mensual (editar)",
                        value=is_monthly_service_current,
                    )

                    confirmar_eliminar_serv = st.checkbox(
                        "✅ Confirmar eliminación de este servicio",
                        key=f"confirm_del_serv_{servicio_edit_id}",
                    )

                    col_btn_s1, col_btn_s2 = st.columns(2)
                    with col_btn_s1:
                        guardar_cambios_serv = st.form_submit_button("💾 Guardar cambios del servicio")
                    with col_btn_s2:
                        eliminar_servicio_btn = st.form_submit_button("🗑️ Eliminar servicio")

                    if guardar_cambios_serv:
                        update_appointment_full(
                            appointment_id=servicio_edit_id,
                            client_name=client_name_edit,
                            service_type=selected_row["service_type"],
                            pest_type=pest_type_edit,
                            address=address_edit,
                            zone=zone_edit,
                            phone=phone_edit,
                            fecha=str(service_date_edit),
                            hora=str(service_time_edit)[:5],
                            price=price_edit if price_edit > 0 else None,
                            status=status_edit,
                            notes=notes_edit,
                            is_monthly_service=is_monthly_service_edit,
                        )
                        st.success("✅ Servicio actualizado correctamente.")
                        st.session_state["servicio_edit_id"] = None
                        st.rerun()

                    if eliminar_servicio_btn:
                        if confirmar_eliminar_serv:
                            delete_appointment(servicio_edit_id)
                            st.warning("🗑️ Servicio eliminado correctamente.")
                            st.session_state["servicio_edit_id"] = None
                            st.rerun()
                        else:
                            st.warning("Marca la casilla 'Confirmar eliminación de este servicio' para eliminar.")

# =========================
# BUSCAR Y EDITAR CLIENTE
# =========================
st.markdown("---")
st.subheader("Buscar y editar cliente")

clientes_all = get_clients()

if not clientes_all:
    st.info("Aún no tienes clientes guardados.")
else:
    col_c1, col_c2, col_c3 = st.columns([2, 2, 1])

    with col_c1:
        opciones_ids = ["--"] + [str(c["id"]) for c in clientes_all]
        cliente_id_sel = st.selectbox("Buscar por ID de cliente", opciones_ids)

    with col_c2:
        opciones_nombres = ["--"]
        etiqueta_a_cliente = {}
        for c in clientes_all:
            etiqueta = c["business_name"] or c["name"]
            if c["business_name"] and c["name"]:
                etiqueta = f"{c['business_name']} ({c['name']})"
            opciones_nombres.append(etiqueta)
            etiqueta_a_cliente[etiqueta] = c
        cliente_nombre_sel = st.selectbox("Buscar por nombre / negocio", opciones_nombres)

    with col_c3:
        buscar_cliente_btn = st.button("🔍 Buscar cliente")

    if buscar_cliente_btn:
        cliente_id = None

        if cliente_id_sel != "--":
            try:
                cid = int(cliente_id_sel)
                for c in clientes_all:
                    if c["id"] == cid:
                        cliente_id = c["id"]
                        break
            except ValueError:
                cliente_id = None
        elif cliente_nombre_sel != "--":
            cliente = etiqueta_a_cliente.get(cliente_nombre_sel)
            if cliente:
                cliente_id = cliente["id"]

        if cliente_id is None:
            st.error("No se encontró el cliente con los datos seleccionados.")
            st.session_state["cliente_edit_id"] = None
        else:
            st.session_state["cliente_edit_id"] = cliente_id

    cliente_edit_id = st.session_state.get("cliente_edit_id")

    if cliente_edit_id:
        cliente_encontrado = None
        for c in clientes_all:
            if c["id"] == cliente_edit_id:
                cliente_encontrado = c
                break

        if cliente_encontrado:
            st.markdown("### ✏️ Editar datos del cliente")

            with st.form("form_editar_cliente"):
                name_edit = st.text_input(
                    "Nombre de la persona / contacto",
                    value=cliente_encontrado["name"] or "",
                )
                business_name_edit = st.text_input(
                    "Nombre del negocio",
                    value=cliente_encontrado["business_name"] or "",
                )
                phone_edit = st.text_input(
                    "Teléfono",
                    value=cliente_encontrado["phone"] or "",
                )
                zone_edit = st.text_input(
                    "Colonia / zona",
                    value=cliente_encontrado["zone"] or "",
                )
                address_edit = st.text_input(
                    "Dirección",
                    value=cliente_encontrado["address"] or "",
                )
                notes_edit = st.text_area(
                    "Notas",
                    value=cliente_encontrado["notes"] or "",
                )

                confirmar_eliminar_cliente = st.checkbox(
                    "✅ Confirmar eliminación de este cliente",
                    key=f"confirm_del_cli_{cliente_edit_id}",
                )

                col_btn_c1, col_btn_c2 = st.columns(2)
                with col_btn_c1:
                    guardar_cliente_cambios = st.form_submit_button("💾 Guardar cambios del cliente")
                with col_btn_c2:
                    eliminar_cliente_btn = st.form_submit_button("🗑️ Eliminar cliente")

                if guardar_cliente_cambios:
                    if not name_edit and not business_name_edit:
                        st.error("Pon al menos el nombre de la persona o del negocio.")
                    else:
                        update_client(
                            client_id=cliente_edit_id,
                            name=name_edit or "Cliente sin nombre",
                            business_name=business_name_edit,
                            address=address_edit,
                            zone=zone_edit,
                            phone=phone_edit,
                            notes=notes_edit,
                        )
                        st.success("✅ Cliente actualizado correctamente.")
                        st.session_state["cliente_edit_id"] = None
                        st.rerun()

                if eliminar_cliente_btn:
                    if confirmar_eliminar_cliente:
                        delete_client(cliente_edit_id)
                        st.warning("🗑️ Cliente eliminado correctamente.")
                        st.session_state["cliente_edit_id"] = None
                        st.rerun()
                    else:
                        st.warning("Marca la casilla 'Confirmar eliminación de este cliente' para eliminar.")

# =========================
# IMPORTAR / EXPORTAR BASE DE DATOS
# =========================
st.markdown("### 📦 Importar / Exportar base de datos")

col_imp, col_exp, col_xls = st.columns(3)

# --- EXPORTAR BD (.db) ---
with col_exp:
    with open(DB_NAME, "rb") as f:
        st.download_button(
            label="⬇️ Exportar BD (.db)",
            data=f,
            file_name="agenda_respaldo.db",
            mime="application/octet-stream",
        )

# --- EXPORTAR A EXCEL (.xlsx) ---
with col_xls:
    if st.button("📊 Exportar a Excel"):
        conn = get_conn()

        df_clients = pd.read_sql("SELECT * FROM clients", conn)
        df_appointments = pd.read_sql("SELECT * FROM appointments", conn)

        conn.close()

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_clients.to_excel(writer, sheet_name="Clientes", index=False)
            df_appointments.to_excel(writer, sheet_name="Servicios", index=False)

        output.seek(0)

        st.download_button(
            label="📥 Descargar Excel",
            data=output,
            file_name="agenda_excel.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# --- IMPORTAR BD ---
with col_imp:
    archivo_subido = st.file_uploader(
        "Subir nueva base de datos (.db)",
        type=["db"],
        accept_multiple_files=False
    )

    if archivo_subido:
        with open(DB_NAME, "wb") as f:
            f.write(archivo_subido.read())
        st.success("✅ Base de datos importada correctamente. Recargando...")
        st.rerun()
