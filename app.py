import streamlit as st
import random
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Simulasi Piket IT Del", layout="wide")

st.title("🚀 Simulasi Sistem Piket IT Del (7 Petugas)")
st.markdown("Simulasi berbasis antrian waktu nyata dengan visualisasi dashboard modern.")

# =============================
# KONSTANTA SISTEM
# =============================

JUMLAH_MEJA = 60
PETUGAS_LAUK = 3
PETUGAS_ANGKAT = 2
PETUGAS_NASI = 2

start_time = datetime.strptime("07:00:00", "%H:%M:%S")

st.info("""
Struktur:
• 3 Petugas Isi Lauk  
• 2 Petugas Angkat (1 trip = 2 meja = 6 ompreng)  
• 2 Petugas Isi Nasi  
• 60 meja, mulai pukul 07.00  
• Setiap pekerjaan 30–60 detik per meja
""")

# =============================
# FUNGSI SIMULASI
# =============================

def simulate():

    meja_list = list(range(1, JUMLAH_MEJA + 1))

    lauk_time = [start_time for _ in range(PETUGAS_LAUK)]
    angkat_time = [start_time for _ in range(PETUGAS_ANGKAT)]
    nasi_time = [start_time for _ in range(PETUGAS_NASI)]

    records = []

    # -------------------------
    # TAHAP 1: ISI LAUK
    # -------------------------
    selesai_lauk = {}

    for meja in meja_list:
        idx = lauk_time.index(min(lauk_time))
        start = lauk_time[idx]
        dur = random.randint(30, 60)
        finish = start + timedelta(seconds=dur)

        lauk_time[idx] = finish
        selesai_lauk[meja] = finish

        records.append(dict(Task="Isi Lauk",
                            Meja=f"Meja {meja}",
                            Start=start,
                            Finish=finish,
                            Petugas=f"Lauk-{idx+1}"))

    # -------------------------
    # TAHAP 2: ANGKAT (2 MEJA PER TRIP)
    # -------------------------
    meja_ready = sorted(selesai_lauk.items(), key=lambda x: x[1])
    queue = [m[0] for m in meja_ready]

    selesai_angkat = {}

    while queue:

        batch = queue[:2]
        queue = queue[2:]

        idx = angkat_time.index(min(angkat_time))
        ready_time = max([selesai_lauk[m] for m in batch])
        start = max(ready_time, angkat_time[idx])

        dur = sum([random.randint(30, 60) for _ in batch])
        finish = start + timedelta(seconds=dur)

        angkat_time[idx] = finish

        for meja in batch:
            selesai_angkat[meja] = finish
            records.append(dict(Task="Angkat Ompreng",
                                Meja=f"Meja {meja}",
                                Start=start,
                                Finish=finish,
                                Petugas=f"Angkat-{idx+1}"))

    # -------------------------
    # TAHAP 3: ISI NASI
    # -------------------------
    for meja in meja_list:
        idx = nasi_time.index(min(nasi_time))
        start = max(selesai_angkat[meja], nasi_time[idx])
        dur = random.randint(30, 60)
        finish = start + timedelta(seconds=dur)

        nasi_time[idx] = finish

        records.append(dict(Task="Isi Nasi",
                            Meja=f"Meja {meja}",
                            Start=start,
                            Finish=finish,
                            Petugas=f"Nasi-{idx+1}"))

    df = pd.DataFrame(records)
    selesai = df["Finish"].max()

    return df, selesai


# =============================
# JALANKAN SIMULASI
# =============================

if st.button("🔥 Jalankan Simulasi"):

    df, waktu_selesai = simulate()

    total_detik = (waktu_selesai - start_time).total_seconds()

    st.success("Simulasi Selesai!")

    # =============================
    # KPI CARD
    # =============================

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Meja", JUMLAH_MEJA)
    col2.metric("Waktu Selesai", waktu_selesai.strftime("%H:%M:%S"))
    col3.metric("Durasi Total (menit)", round(total_detik / 60, 2))

    st.divider()

    # =============================
    # DASHBOARD VISUALISASI
    # =============================

    st.subheader("📊 Dashboard Analisis")

    df["Durasi"] = (df["Finish"] - df["Start"]).dt.total_seconds()

    # 1️⃣ Total Waktu per Tahap
    ringkasan_tahap = df.groupby("Task")["Durasi"].sum().reset_index()

    fig1 = px.bar(
        ringkasan_tahap,
        x="Task",
        y="Durasi",
        text_auto=True,
        title="Total Waktu Kerja per Tahap (detik)"
    )

    st.plotly_chart(fig1, use_container_width=True)

    # 2️⃣ Utilisasi Petugas
    beban_petugas = df.groupby("Petugas")["Durasi"].sum().reset_index()
    beban_petugas["Utilisasi (%)"] = (beban_petugas["Durasi"] / total_detik) * 100

    fig2 = px.bar(
        beban_petugas,
        x="Petugas",
        y="Utilisasi (%)",
        text_auto=".2f",
        title="Utilisasi Petugas (%)"
    )

    st.plotly_chart(fig2, use_container_width=True)

    # 3️⃣ Progress Penyelesaian Meja
    selesai_nasi = df[df["Task"] == "Isi Nasi"].sort_values("Finish")
    selesai_nasi["Jumlah Meja Selesai"] = range(1, len(selesai_nasi) + 1)

    fig3 = px.line(
        selesai_nasi,
        x="Finish",
        y="Jumlah Meja Selesai",
        markers=True,
        title="Progress Penyelesaian 60 Meja"
    )

    st.plotly_chart(fig3, use_container_width=True)

    # 4️⃣ Bottleneck
    tahap_terlama = ringkasan_tahap.sort_values("Durasi", ascending=False).iloc[0]

    st.info(f"""
Tahap paling lama adalah **{tahap_terlama['Task']}**
dengan total {int(tahap_terlama['Durasi'])} detik.
Tahap ini menjadi bottleneck sistem.
""")

    st.balloons()