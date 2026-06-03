import os
import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from models import SessionLocal, User, Match, Prediction, init_db, SystemConfig
from auth import hash_password, check_password
import base64
from fpdf import FPDF
 
# Inicializar BD
init_db()
db_init = SessionLocal()
try:
    if db_init.query(Match).count() == 0:
        from reset_db import reset_and_seed
        reset_and_seed()
except Exception as e:
    pass
finally:
    db_init.close()
 
def is_tournament_locked():
    db = SessionLocal()
    locked = False
    try:
        conf = db.query(SystemConfig).filter_by(key="tournament_locked").first()
        if conf and conf.value == "true":
            locked = True
    finally:
        db.close()
    return locked
 
# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Prode Mundial 2026", page_icon="⚽", layout="wide")
 
# --- CARGAR ESTILOS CSS ---
def load_css():
    try:
        with open("styles.css", "r") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass
 
load_css()
 
# --- MANEJO DE ESTADO (SESSION STATE) ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
 
# --- BASE DE DATOS ---
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass # Streamlit caches might cause issues if we close too early, but we should manage per request.
 
# --- TEXTO DE TÉRMINOS Y CONDICIONES ---
TERMS_AND_CONDITIONS = """
🏆 REGLAMENTO OFICIAL: PRODE MUNDIAL 2026 🏆
 
¡Bienvenidos al Prode! Para que todo sea transparente, competitivo y, sobre todo, divertido, establecemos las siguientes bases y condiciones que todos los participantes aceptan al ingresar.
 
1. Costo de Inscripción y Validación
• Valor: El costo para participar es de $10.000.
• Fecha límite de pago: Se recibe el dinero hasta el 05/06 inclusive.
• Fecha límite de carga: Los pronósticos se pueden cargar/modificar hasta el día anterior al comienzo del partido inaugural.
• Cierre estricto: Una vez cumplidas estas fechas, el Prode se "cierra". Solo participarán quienes hayan abonado en término. Si alguien pagó pero olvidó completar sus pronósticos, es su total responsabilidad y no habrá excepciones.
 
2. Transparencia Total 👁️
Para garantizar la máxima transparencia y evitar suspicacias, el Prode de todos los participantes estará visible públicamente a partir del pitazo inicial del partido inaugural.
De esta manera, todos podrán ir controlando los puntos y los pronósticos de los demás en tiempo real.
 
3. Alcance del Torneo y Sistema de Puntuación
El Prode aplica únicamente para la Fase de Grupos (los primeros 72 partidos del torneo). Los partidos se puntúan de la siguiente manera:
• 1 Punto: Por acertar el resultado básico (si gana el Local, hay Empate, o gana el Visitante).
• 2 Puntos Extra: Por acertar el resultado exacto en goles (ej: pronosticaste 2-1 y el partido termina 2-1).
Ejemplo: Si apostás que gana el Local 2-1 y el partido termina 2-1, sumás 3 puntos en total (1 por el ganador + 2 por el resultado exacto). Si el partido termina 1-0, sumás solo 1 punto.
 
4. Reparto de Premios y Criterio de Desempate 💰
Finalizado el último partido de la Fase de Grupos, se calculará la tabla final. Todo lo recaudado se distribuirá de la siguiente manera:
• 1° Puesto: 50% de la recaudación total.
• 2° Puesto: 30% de la recaudación total.
• 3° Puesto: 20% de la recaudación total.
Cláusula de Empates: Si dos o más participantes empatan en puntos en alguna de las posiciones de premio, se dividirá el dinero en partes iguales, pero afectando únicamente el porcentaje asignado a ese puesto.
Ejemplo: Si hay un único 1° Puesto (se lleva el 50%) y un único 2° Puesto (se lleva el 30%), pero hay dos personas empatadas en el 3° Puesto, ese 20% se divide en partes iguales entre esos dos participantes (10% para cada uno).
(Nota: Si el empate ocurre en el 1° puesto entre dos personas, se fusionan los premios del 1° y 2° puesto [50%+30% = 80%] y se divide 40% para cada uno, quedando el de atrás como 3°).
 
5. Política de Reembolso
Sin derecho a réplica: No hay reembolso de dinero bajo ninguna circunstancia. Si tus predicciones son malas, la pelota no entra o la suerte no te acompaña... a "llorar al campito". El dinero ya forma parte del pozo de premios.
 
⚠️ Puntos extra (¡Para tener en cuenta!)
 
6. Partidos Suspendidos o Postergados: Si un partido de la fase de grupos se suspende, se posterga o se cancela oficialmente por la FIFA y no se juega dentro de las 48 horas posteriores a su fecha original, dicho partido quedará anulado para el Prode y nadie sumará puntos por él.
 
7. Resultados Oficiales: Los resultados válidos para la puntuación serán los oficiales determinados por la FIFA al finalizar el partido. Cualquier escritorio, reclamo posterior o sanción que cambie el resultado días después no será tenido en cuenta para el conteo del Prode.
 
8. Modificaciones: El administrador se reserva el derecho de resolver cualquier situación gris o vacío legal no contemplado en este reglamento, siempre actuando bajo el principio de la buena fe y la justicia para el grupo.
"""
 
# --- PANTALLA DE LOGIN / REGISTRO ---
def login_screen():
    st.markdown("<h1 style='text-align: center; color: #00f2fe;'>🏆 Prode Mundial 2026</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Ingresar", "Registrarse"])
        
        with tab1:
            st.subheader("Iniciar Sesión")
            with st.form("login_form"):
                username = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("Ingresar")
                
                if submit:
                    db = SessionLocal()
                    user = db.query(User).filter(User.username == username).first()
                    if user and check_password(password, user.password_hash):
                        st.session_state.user_id = user.id
                        st.session_state.username = user.username
                        st.session_state.is_admin = user.is_admin
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")
                    db.close()
        
        with tab2:
            st.subheader("Crear Cuenta")
            with st.form("signup_form"):
                new_username = st.text_input("Nuevo Usuario")
                new_password = st.text_input("Contraseña", type="password")
                # El primer usuario que se registre será admin por defecto para pruebas
                accept_terms = st.checkbox("Acepto el Reglamento Oficial del Prode Mundial 2026")
                submit_reg = st.form_submit_button("Registrarse")
                
                if submit_reg:
                    if not accept_terms:
                        st.error("Debes aceptar el Reglamento Oficial para registrarte.")
                    elif len(new_username) < 3 or len(new_password) < 4:
                        st.error("Usuario (>3) y contraseña (>4) deben ser más largos.")
                    else:
                        db = SessionLocal()
                        existing = db.query(User).filter(User.username == new_username).first()
                        if existing:
                            st.error("El usuario ya existe.")
                        else:
                            is_first_user = db.query(User).count() == 0
                            hashed_pw = hash_password(new_password)
                            new_user = User(username=new_username, password_hash=hashed_pw, is_admin=is_first_user)
                            db.add(new_user)
                            db.commit()
                            st.success("Cuenta creada exitosamente. Ya puedes ingresar.")
                        db.close()
 
            # Link para ver el reglamento completo debajo del formulario
            with st.expander("📋 Ver Reglamento Oficial completo"):
                st.text(TERMS_AND_CONDITIONS)
 
# --- LÓGICA DE PUNTOS ---
def calculate_points(pred_a, pred_b, res_a, res_b):
    if pred_a == res_a and pred_b == res_b:
        return 3
    
    pred_trend = "A" if pred_a > pred_b else "B" if pred_b > pred_a else "TIE"
    res_trend = "A" if res_a > res_b else "B" if res_b > res_a else "TIE"
    
    if pred_trend == res_trend:
        return 1
    return 0
 
# --- PANTALLAS PRINCIPALES ---
def dashboard_screen():
    st.header("🏅 Ranking en Vivo")
    db = SessionLocal()
    
    # Obtener usuarios y sus puntos
    users = db.query(User).all()
    ranking_data = []
    
    for u in users:
        total_points = 0
        exact_matches = 0
        predictions = db.query(Prediction).filter(Prediction.user_id == u.id).all()
        for p in predictions:
            total_points += p.points
            if p.points == 3:
                exact_matches += 1
        ranking_data.append({"Usuario": u.username, "Puntos": total_points, "Aciertos Exactos": exact_matches})
    
    db.close()
    
    if ranking_data:
        df = pd.DataFrame(ranking_data).sort_values(by=["Puntos", "Aciertos Exactos", "Usuario"], ascending=[False, False, True]).reset_index(drop=True)
        df.index += 1
        
        # Podio
        if len(df) > 0:
            st.markdown("<h3 style='text-align: center; margin-bottom: 0;'>🏆 El Podio</h3>", unsafe_allow_html=True)
            p1_name = df.iloc[0]["Usuario"]
            p1_pts = df.iloc[0]["Puntos"]
            p2_name = df.iloc[1]["Usuario"] if len(df) > 1 else ""
            p2_pts = df.iloc[1]["Puntos"] if len(df) > 1 else ""
            p3_name = df.iloc[2]["Usuario"] if len(df) > 2 else ""
            p3_pts = df.iloc[2]["Puntos"] if len(df) > 2 else ""
            
            podium_html = f"""
            <div class="podium-container">
                <div class="podium-step step-2" style="visibility: {'visible' if p2_name else 'hidden'}">
                    <div class="medal">🥈</div>
                    <div class="name">{p2_name}</div>
                    <div class="points">{p2_pts} pts</div>
                </div>
                <div class="podium-step step-1">
                    <div class="medal">🥇</div>
                    <div class="name">{p1_name}</div>
                    <div class="points">{p1_pts} pts</div>
                </div>
                <div class="podium-step step-3" style="visibility: {'visible' if p3_name else 'hidden'}">
                    <div class="medal">🥉</div>
                    <div class="name">{p3_name}</div>
                    <div class="points">{p3_pts} pts</div>
                </div>
            </div>
            """
            st.markdown(podium_html, unsafe_allow_html=True)
        
        st.markdown("### 📋 Tabla Completa")
        st.dataframe(df, use_container_width=True)
        
        if is_tournament_locked():
            st.markdown("---")
            st.markdown("### 🔍 Ver pronósticos de otros participantes")
            st.write("El torneo ha comenzado. Ahora puedes ver las predicciones de todos los jugadores.")
            
            usernames = sorted([u.username for u in users])
            selected_username = st.selectbox("Selecciona un participante:", ["-- Seleccionar --"] + usernames)
            
            if selected_username and selected_username != "-- Seleccionar --":
                target_user = next((u for u in users if u.username == selected_username), None)
                if target_user:
                    target_preds = db.query(Prediction).filter(Prediction.user_id == target_user.id).all()
                    target_preds_dict = {p.match_id: p for p in target_preds}
                    matches = db.query(Match).order_by(Match.date).all()
                    
                    pred_data = []
                    for m in matches:
                        p = target_preds_dict.get(m.id)
                        pred_a = p.pred_a if p else 0
                        pred_b = p.pred_b if p else 0
                        puntos = p.points if p else 0
                        
                        resultado_real = f"{m.result_a} - {m.result_b}" if m.status == 'finished' else "Pendiente"
                        pred_data.append({
                            "Fecha": m.date.strftime('%d/%m'),
                            "Grupo": m.group,
                            "Partido": f"{m.team_a} vs {m.team_b}",
                            "Su Pronóstico": f"{pred_a} - {pred_b}",
                            "Resultado Real": resultado_real,
                            "Puntos": puntos
                        })
                    
                    st.dataframe(pd.DataFrame(pred_data), use_container_width=True)
 
    else:
        st.info("Aún no hay participantes en el ranking.")
 
def predictions_screen():
    st.header("📝 Mis Pronósticos")
    locked = is_tournament_locked()
    if locked:
        st.error("🚨 El torneo ha comenzado. Los pronósticos están BLOQUEADOS y ya no pueden modificarse.")
    else:
        st.write("Carga tus predicciones para la fase de grupos. Una vez que el partido inicie, no podrás modificarlos.")
    
    db = SessionLocal()
    matches = db.query(Match).order_by(Match.date).all()
    user_preds = db.query(Prediction).filter(Prediction.user_id == st.session_state.user_id).all()
    preds_dict = {p.match_id: p for p in user_preds}
    
    groups = {}
    for m in matches:
        if m.group not in groups:
            groups[m.group] = []
        groups[m.group].append(m)
    
    tabs = st.tabs([f"Grupo {g}" for g in sorted(groups.keys())])
    
    for i, group_name in enumerate(sorted(groups.keys())):
        with tabs[i]:
            for m in groups[group_name]:
                # Verificar si el partido ya inició (mock: asume status) o si el torneo está bloqueado globalmente
                is_disabled = m.status == "finished" or locked
                
                existing_pred = preds_dict.get(m.id)
                default_a = existing_pred.pred_a if existing_pred else 0
                default_b = existing_pred.pred_b if existing_pred else 0
                
                with st.container():
                    st.markdown(f"""
                    <div style="text-align: center; color: #a0aec0; font-size: 0.85rem; margin-bottom: 10px; margin-top: 15px;">
                        📅 {m.date.strftime('%d/%m/%Y')} &nbsp;•&nbsp; ⏰ {m.time} &nbsp;•&nbsp; 🏟️ {m.stadium}
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f'<div class="match-card">', unsafe_allow_html=True)
                    cols = st.columns([3, 1, 1, 1, 3])
                    cols[0].markdown(f"<div style='text-align: right;' class='team-name'>{m.team_a} <span style='font-size:0.75rem; color:#888; font-weight:normal;'>({m.flag_a})</span></div>", unsafe_allow_html=True)
                    
                    val_a = cols[1].number_input("##", min_value=0, max_value=20, value=default_a, key=f"a_{m.id}", disabled=is_disabled, label_visibility="collapsed")
                    cols[2].markdown("<div style='text-align: center; font-size: 24px; font-weight: bold;'>-</div>", unsafe_allow_html=True)
                    val_b = cols[3].number_input("##", min_value=0, max_value=20, value=default_b, key=f"b_{m.id}", disabled=is_disabled, label_visibility="collapsed")
                    
                    cols[4].markdown(f"<div style='text-align: left;' class='team-name'><span style='font-size:0.75rem; color:#888; font-weight:normal;'>({m.flag_b})</span> {m.team_b}</div>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Guardar automáticamente al cambiar (en un entorno real, mejor usar un botón de guardado por grupo)
                    if not is_disabled:
                        if existing_pred:
                            if existing_pred.pred_a != val_a or existing_pred.pred_b != val_b:
                                existing_pred.pred_a = val_a
                                existing_pred.pred_b = val_b
                                db.commit()
                        else:
                            # Se elimino el control del 0 a 0 - Para no guardar todos los 0-0 automáticamente
                            new_pred = Prediction(user_id=st.session_state.user_id, match_id=m.id, pred_a=val_a, pred_b=val_b)
                            db.add(new_pred)
                            db.commit()
                            preds_dict[m.id] = new_pred
    
    st.markdown("---")
    st.subheader("📄 Descargar Mis Pronósticos")
    st.write("Genera un archivo PDF con todos los pronósticos que has cargado hasta ahora.")
    
    # We create the PDF when the user asks
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, f"Pronosticos de {st.session_state.username} - Prode Mundial 2026", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    pdf.set_font("helvetica", "", 12)
    for m in matches:
        p = preds_dict.get(m.id)
        pred_text = f"{p.pred_a} - {p.pred_b}" if p else "No cargado"
        line = f"{m.date.strftime('%d/%m')} | Grupo {m.group} | {m.team_a} vs {m.team_b} -> Pronostico: {pred_text}"
        pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
        
    pdf_bytes = bytes(pdf.output())
    
    st.download_button(
        label="⬇️ Descargar Archivo PDF",
        data=pdf_bytes,
        file_name=f"pronosticos_{st.session_state.username}.pdf",
        mime="application/pdf"
    )
 
    db.close()
 
def admin_screen():
    st.header("⚙️ Panel de Administrador")
    
    st.markdown("### Control del Torneo")
    locked = is_tournament_locked()
    if locked:
        st.warning("🔒 El torneo está actualmente BLOQUEADO. Nadie puede editar sus pronósticos.")
        if st.button("🔓 Desbloquear Torneo (Permitir Edición)"):
            db = SessionLocal()
            conf = db.query(SystemConfig).filter_by(key="tournament_locked").first()
            if conf:
                conf.value = "false"
            db.commit()
            db.close()
            st.rerun()
    else:
        st.success("🔓 El torneo está ABIERTO. Los usuarios pueden editar sus pronósticos.")
        if st.button("🔒 Bloquear Torneo (Cerrar Pronósticos)"):
            db = SessionLocal()
            conf = db.query(SystemConfig).filter_by(key="tournament_locked").first()
            if not conf:
                conf = SystemConfig(key="tournament_locked", value="true")
                db.add(conf)
            else:
                conf.value = "true"
            db.commit()
            db.close()
            st.rerun()
 
    st.markdown("---")
    st.markdown("### 🗑️ Dar de Baja a un Participante")
    st.write("Elimina un usuario y todos sus pronósticos. Esta acción es irreversible.")
    
    db = SessionLocal()
    all_users = db.query(User).order_by(User.username).all()
    # No permitir eliminar al propio admin logueado
    deletable_users = [u for u in all_users if u.id != st.session_state.user_id]
    delete_names = [u.username for u in deletable_users]
 
    selected_user_to_delete = st.selectbox("Seleccionar usuario a dar de baja", ["-- Seleccionar --"] + delete_names, key="delete_user_select")
    
    if selected_user_to_delete != "-- Seleccionar --":
        st.warning(f"⚠️ ¿Estás seguro que querés eliminar a **{selected_user_to_delete}** y todos sus pronósticos?")
        if st.button("🗑️ Confirmar Baja", type="primary"):
            user_to_delete = db.query(User).filter_by(username=selected_user_to_delete).first()
            if user_to_delete:
                # Primero eliminar todos sus pronósticos
                db.query(Prediction).filter_by(user_id=user_to_delete.id).delete()
                # Luego eliminar el usuario
                db.delete(user_to_delete)
                db.commit()
                st.success(f"✅ Usuario {selected_user_to_delete} y sus pronósticos fueron eliminados correctamente.")
                st.rerun()
    db.close()
 
    st.markdown("---")
    st.markdown("### Reseteo de Contraseña")
    st.write("Si un usuario olvidó su contraseña, puedes asignarle una nueva.")
    db = SessionLocal()
    all_users = db.query(User).order_by(User.username).all()
    user_names = [u.username for u in all_users]
    selected_user_to_reset = st.selectbox("Seleccionar Usuario", ["-- Seleccionar --"] + user_names)
    new_pwd = st.text_input("Nueva Contraseña", type="password")
    if st.button("Resetear Contraseña"):
        if selected_user_to_reset != "-- Seleccionar --" and len(new_pwd) >= 4:
            user_to_mod = db.query(User).filter_by(username=selected_user_to_reset).first()
            if user_to_mod:
                user_to_mod.password_hash = hash_password(new_pwd)
                db.commit()
                st.success(f"Contraseña de {selected_user_to_reset} actualizada.")
        else:
            st.error("Selecciona un usuario y una contraseña de al menos 4 caracteres.")
    db.close()
            
    st.markdown("---")
    st.markdown("### Cargar Resultados")
    st.write("Carga los resultados reales de los partidos para actualizar el ranking.")
    
    db = SessionLocal()
    matches = db.query(Match).order_by(Match.date).all()
    
    for m in matches:
        with st.expander(f"[{m.group}] {m.team_a} {m.flag_a} vs {m.flag_b} {m.team_b} - Estado: {m.status}"):
            with st.form(f"form_match_{m.id}"):
                cols = st.columns(2)
                res_a = cols[0].number_input(m.team_a, min_value=0, value=m.result_a if m.result_a is not None else 0)
                res_b = cols[1].number_input(m.team_b, min_value=0, value=m.result_b if m.result_b is not None else 0)
                
                submitted = st.form_submit_button("Guardar Resultado FInal")
                if submitted:
                    m.result_a = res_a
                    m.result_b = res_b
                    m.status = "finished"
                    
                    # Actualizar puntos de todos los usuarios
                    users = db.query(User).all()
                    predictions = db.query(Prediction).filter(Prediction.match_id == m.id).all()
                    pred_dict = {p.user_id: p for p in predictions}
                    
                    for u in users:
                        p = pred_dict.get(u.id)
                        if p:
                            p.points = calculate_points(p.pred_a, p.pred_b, res_a, res_b)
                        else:
                            # Crear predicción implícita de 0-0 si no la habían guardado
                            pts = calculate_points(0, 0, res_a, res_b)
                            new_p = Prediction(user_id=u.id, match_id=m.id, pred_a=0, pred_b=0, points=pts)
                            db.add(new_p)
                    
                    db.commit()
                    st.success("Resultado guardado y puntos actualizados.")
                    st.rerun()
    db.close()
 
# --- FOOTER CON LINK A TÉRMINOS Y CONDICIONES ---
def show_footer():
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.85rem;'>⚽ Prode Mundial 2026</div>",
        unsafe_allow_html=True
    )
    with st.expander("📋 Ver Reglamento Oficial"):
        st.text(TERMS_AND_CONDITIONS)
 
# --- NAVEGACIÓN PRINCIPAL ---
if st.session_state.user_id is None:
    login_screen()
    show_footer()
else:
    # Header minimalista con logout
    col1, col2 = st.columns([8, 1])
    col1.markdown(f"**Bienvenido, {st.session_state.username}**")
    if col2.button("Salir"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.is_admin = False
        st.rerun()
    
    st.markdown("---")
    
    tabs_names = ["🏅 Dashboard", "📝 Mis Pronósticos"]
    if st.session_state.is_admin:
        tabs_names.append("⚙️ Admin")
        
    app_tabs = st.tabs(tabs_names)
    
    with app_tabs[0]:
        dashboard_screen()
    with app_tabs[1]:
        predictions_screen()
    if st.session_state.is_admin:
        with app_tabs[2]:
            admin_screen()
    
    show_footer()
