import sqlite3
import random
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Telemetria • Empilhadeira #04", layout="wide")

DB_NAME = "telemetria.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetria_empilhadeira (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipamento_id TEXT NOT NULL,
            estado_ligado INTEGER NOT NULL,
            odometro_km REAL NOT NULL,
            odometro_meta_km REAL DEFAULT 80.0,
            temperatura_motor_c REAL NOT NULL,
            peso_carga_g INTEGER NOT NULL,
            capacidade_max_g INTEGER DEFAULT 1000,
            umidade_percent INTEGER NOT NULL,
            tempo_uso_minutos INTEGER NOT NULL,
            turno_max_minutos INTEGER DEFAULT 480,
            wifi_status TEXT,
            wifi_rede TEXT,
            bluetooth_status TEXT,
            bluetooth_dispositivo TEXT,
            buzzer_db INTEGER NOT NULL,
            buzzer_silenciado INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_comandos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipamento_id TEXT NOT NULL,
            comando TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Remove registros corrompidos com valores nulos, se existirem
    cursor.execute("DELETE FROM telemetria_empilhadeira WHERE peso_carga_g IS NULL")
    
    cursor.execute("SELECT COUNT(*) FROM telemetria_empilhadeira")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO telemetria_empilhadeira (
                equipamento_id, estado_ligado, odometro_km, temperatura_motor_c,
                peso_carga_g, umidade_percent, tempo_uso_minutos,
                wifi_status, wifi_rede, bluetooth_status, bluetooth_dispositivo, buzzer_db
            ) VALUES ('EMP-04', 1, 14.82, 23.5, 300, 58, 272, 'Conectado', 'OPERACAO-IOT', 'Pareado', 'EMP-04', 85)
        """)
    conn.commit()
    conn.close()

def get_latest_telemetry():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(
        "SELECT * FROM telemetria_empilhadeira WHERE equipamento_id = 'EMP-04' ORDER BY id DESC LIMIT 1",
        conn
    )
    conn.close()
    return df.iloc[0]

def registrar_comando_e_atualizar(comando, **kwargs):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO log_comandos (equipamento_id, comando) VALUES (?, ?)",
        ('EMP-04', comando)
    )
    atual = get_latest_telemetry()
    cursor.execute("""
        INSERT INTO telemetria_empilhadeira (
            equipamento_id, estado_ligado, odometro_km, temperatura_motor_c,
            peso_carga_g, umidade_percent, tempo_uso_minutos,
            wifi_status, wifi_rede, bluetooth_status, bluetooth_dispositivo,
            buzzer_db, buzzer_silenciado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'EMP-04',
        int(kwargs.get('estado_ligado', atual['estado_ligado'])),
        float(kwargs.get('odometro_km', atual['odometro_km'])),
        float(kwargs.get('temperatura_motor_c', atual['temperatura_motor_c'])),
        int(kwargs.get('peso_carga_g', atual['peso_carga_g'])),
        int(kwargs.get('umidade_percent', atual['umidade_percent'])),
        int(kwargs.get('tempo_uso_minutos', atual['tempo_uso_minutos'])),
        atual['wifi_status'],
        atual['wifi_rede'],
        atual['bluetooth_status'],
        atual['bluetooth_dispositivo'],
        int(kwargs.get('buzzer_db', atual['buzzer_db'])),
        int(kwargs.get('buzzer_silenciado', atual['buzzer_silenciado']))
    ))
    conn.commit()
    conn.close()

init_db()
dados = get_latest_telemetry()

# --- CABEÇALHO ---
col_top1, col_top2 = st.columns([3, 1])
with col_top1:
    st.caption("EMPRESA ELAS & O INTRUSO • MONITORAMENTO INDUSTRIAL")
    st.title("🚜 EMPILHADEIRA - ELÉTRICA 1 KG")
    st.caption("PAINEL EM TEMPO REAL • UNIDADE LOGÍSTICA / GALPÃO 05")

with col_top2:
    st.write("")
    status_badge = "🟢 AO VIVO" if int(dados['estado_ligado']) == 1 else "🔴 STANDBY"
    st.subheader(status_badge)
    if st.button("🔄 Simular Leitura", use_container_width=True, type="primary"):
        if int(dados['estado_ligado']) == 1:
            registrar_comando_e_atualizar(
                "TELEMETRIA_AUTO",
                odometro_km=round(float(dados['odometro_km']) + random.uniform(0.05, 0.25), 2),
                temperatura_motor_c=round(float(dados['temperatura_motor_c']) + random.uniform(-0.4, 0.7), 1),
                peso_carga_g=random.randint(150, 950),
                umidade_percent=random.randint(52, 64),
                tempo_uso_minutos=int(dados['tempo_uso_minutos']) + 5
            )
            st.rerun()
        else:
            st.toast("Ligue a empilhadeira para receber novas leituras.")

st.divider()

# --- VISÃO GERAL DA OPERAÇÃO ---
st.subheader("Visão geral da operação")

odometro = float(dados['odometro_km'])
meta_km = float(dados['odometro_meta_km'])
temp_motor = float(dados['temperatura_motor_c'])
peso_carga = int(dados['peso_carga_g'])
cap_max = int(dados['capacidade_max_g'])
umidade = int(dados['umidade_percent'])
tempo_uso = int(dados['tempo_uso_minutos'])
turno_max = int(dados['turno_max_minutos'])

pct_odometro = min(1.0, max(0.0, odometro / meta_km))
pct_temp = min(1.0, max(0.0, temp_motor / 90.0))
pct_carga = min(1.0, max(0.0, peso_carga / cap_max))
pct_tempo = min(1.0, max(0.0, tempo_uso / turno_max))
horas = tempo_uso // 60
minutos = tempo_uso % 60

c1, c2, c3 = st.columns(3)

with c1:
    with st.container(border=True):
        ligado_bool = bool(int(dados['estado_ligado']))
        st.metric("Estado do equipamento", "Ligado" if ligado_bool else "Desligado")
        st.progress(1.0 if ligado_bool else 0.0)
        ligado_toggle = st.toggle("Chave Geral (Ligar / Desligar)", value=ligado_bool)
        if ligado_toggle != ligado_bool:
            registrar_comando_e_atualizar(
                "LIGAR_EQUIPAMENTO" if ligado_toggle else "DESLIGAR_EQUIPAMENTO",
                estado_ligado=1 if ligado_toggle else 0
            )
            st.rerun()

with c2:
    with st.container(border=True):
        st.metric("Odômetro Digital", f"{str(odometro).replace('.', ',')} km")
        st.progress(pct_odometro)
        st.caption(f"Percurso acumulado no turno ({round(pct_odometro * 100, 1)}% de 80 km)")

with c3:
    with st.container(border=True):
        status_temp = "Normal" if temp_motor <= 65 else "Atenção"
        st.metric("Temperatura do Motor", f"{temp_motor} °C", delta=status_temp)
        st.progress(pct_temp)
        st.caption("Faixa segura até 90 °C")

c4, c5, c6 = st.columns(3)

with c4:
    with st.container(border=True):
        st.metric("Peso da Carga Atual", f"{peso_carga} g / 1 kg")
        st.progress(pct_carga)
        st.caption(f"Capacidade utilizada: {int(pct_carga * 100)}%")

with c5:
    with st.container(border=True):
        st.metric("Umidade", f"{umidade} %")
        st.progress(min(1.0, umidade / 100.0))
        st.caption("Umidade relativa do ambiente: Estável")

with c6:
    with st.container(border=True):
        st.metric("Tempo de Uso", f"{horas:02d}h {minutos:02d}m")
        st.progress(pct_tempo)
        st.caption(f"Tempo ativo no turno de 8h ({round(pct_tempo * 100, 1)}%)")

st.divider()

# --- CONECTIVIDADE E SINALIZAÇÃO ---
st.subheader("Conectividade e sinalização")

col_wifi, col_bt, col_buzzer = st.columns([1, 1, 2])

with col_wifi:
    with st.container(border=True):
        st.metric("Wi-Fi", f"• {dados['wifi_status']}")
        st.caption(f"Rede: {dados['wifi_rede']} | Sinal excelente")

with col_bt:
    with st.container(border=True):
        st.metric("Bluetooth", f"• {dados['bluetooth_status']}")
        st.caption(f"Dispositivo: {dados['bluetooth_dispositivo']} | Canal ativo")

with col_buzzer:
    with st.container(border=True):
        silenciado = int(dados['buzzer_silenciado']) == 1
        db_exibido = 0 if silenciado else int(dados['buzzer_db'])
        status_som = "Silenciado" if silenciado else "Intensidade configurada"
        st.metric("Buzzer", f"{db_exibido} dB", delta=status_som, delta_color="off")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🔊 Testar Som", use_container_width=True, type="primary"):
                registrar_comando_e_atualizar("TESTAR_SOM", buzzer_silenciado=0, buzzer_db=85)
                st.toast("Alerta sonoro acionado na EMP-04 (85 dB)!")
                st.rerun()
        with b2:
            if st.button("🔇 Silenciar", use_container_width=True):
                registrar_comando_e_atualizar("SILENCIAR_BUZZER", buzzer_silenciado=1)
                st.toast("Buzzer silenciado.")
                st.rerun()

# --- AUDITORIA SQL ---
with st.expander("📋 Ver histórico de comandos gravados no banco SQL"):
    conn = sqlite3.connect(DB_NAME)
    df_logs = pd.read_sql_query(
        "SELECT id, equipamento_id, comando, timestamp FROM log_comandos ORDER BY id DESC LIMIT 10",
        conn
    )
    conn.close()
    st.dataframe(df_logs, use_container_width=True, hide_index=True)
