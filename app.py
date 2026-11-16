import streamlit as st

from adversarial import jalankan_skenario
from kampus import (DOSEN, MAKS_KELAS_PER_HARI, MATKUL, buat_jadwal_tetap, buat_problem,
                    tabel_jadwal)
from krs import KRS
from models import HARI

MAKS_PILIHAN = 3          # mahasiswa boleh memilih maksimal 3 kelas, sisanya dipilihkan AI
AI = "(serahkan ke AI)"

st.set_page_config(page_title="Jadwal Kuliah CSP", layout="wide")
st.title("AI University Timetable Generator")
st.caption("CSP (backtracking + MRV + forward checking) menyusun jadwal tetap seluruh kelas, "
           "lalu AI ranking melengkapi pilihan mahasiswa menjadi satu jadwal utuh tanpa bentrok.")

if "problem" not in st.session_state:
    st.session_state.problem = buat_problem()
    st.session_state.seed = 0
    st.session_state.jadwal = buat_jadwal_tetap(st.session_state.problem, 0)

if st.button("Generate ulang jadwal CSP"):
    st.session_state.seed += 100
    st.session_state.jadwal = buat_jadwal_tetap(st.session_state.problem, st.session_state.seed)
    st.rerun()

problem = st.session_state.problem
jadwal = st.session_state.jadwal

if not jadwal:
    st.error("Tidak ada jadwal valid untuk data ini.")
    st.stop()

krs = KRS(jadwal, problem)
tab_data, tab_pilih, tab_adv = st.tabs(["1. Data dan jadwal CSP", "2. Pilih kelas dan AI ranking",
                                        "Skenario adversarial"])

with tab_data:
    st.subheader("Data masukan")
    c1, c2 = st.columns(2)
    c1.markdown("**Mata kuliah**")
    c1.table([{"Mata kuliah": n, "SKS": s, "Jumlah kelas": sum(1 for x in problem.sections.values() if x.course_code == k)}
              for k, n, s in MATKUL])
    c2.markdown(f"**Dosen** (maks {MAKS_KELAS_PER_HARI} kelas per hari)")
    c2.table([{"Dosen": n, "Boleh mengajar": ", ".join(mk)} for _, n, mk in DOSEN])
    st.caption("Ruangan: Ruang 101 sampai 112 (50 orang), Lab Pemrograman dan Aula Handayani (100 orang). "
               "Waktu: Senin sampai Jumat pukul 07.00 sampai 17.00, 1 SKS = 1 jam.")

    st.subheader("Jadwal tetap hasil CSP")
    st.caption(f"{len(jadwal)} kelas, setiap kelas sudah punya dosen, ruang, dan jam yang pasti.")
    st.dataframe(tabel_jadwal(jadwal, problem), use_container_width=True, hide_index=True)

with tab_pilih:
    st.subheader(f"Pilih maksimal {MAKS_PILIHAN} kelas yang kamu mau")
    st.write("Mata kuliah yang tidak kamu pilih akan dicarikan kelasnya oleh AI ranking, "
             "sehingga jadwal akhir lengkap dan tidak bentrok.")

    picks = {}
    cols = st.columns(2)
    for i, code in enumerate(krs.wanted):
        pilihan = cols[i % 2].selectbox(krs.nama_matkul(code), [AI] + krs.by_course[code],
                                        format_func=lambda s: s if s == AI else krs.deskripsi(s),
                                        key=f"pilih_{code}")
        if pilihan != AI:
            picks[code] = pilihan

    with st.expander("Preferensi tambahan (opsional)"):
        favorit = st.multiselect("Dosen favorit", [d for d, _, _ in DOSEN],
                                 format_func=lambda d: problem.lecturers[d].name)
        kosong = st.selectbox("Hari yang ingin kosong", ["(bebas)"] + HARI)
    preferensi = {}
    if favorit:
        preferensi["dosen_favorit"] = set(favorit)
    if kosong != "(bebas)":
        preferensi["hari_kosong"] = kosong

    if st.button("Cari jadwal terbaik"):
        hasil = krs.rekomendasi(picks, preferensi, top_k=3) if len(picks) <= MAKS_PILIHAN else []
        if len(picks) > MAKS_PILIHAN:
            st.error(f"Kamu memilih {len(picks)} kelas, maksimal {MAKS_PILIHAN}.")
        elif not hasil:
            st.error("Tidak ada kombinasi lengkap tanpa bentrok untuk pilihanmu.")
            for code, sid in picks.items():
                masalah = krs._cek(sid, {c: s for c, s in picks.items() if c != code})
                if masalah:
                    st.warning(f"{krs.deskripsi(sid)}: {masalah[1]}")
        for rank, r in enumerate(hasil, 1):
            with st.expander(f"Peringkat {rank} (skor {r['skor']})", expanded=rank == 1):
                baris = []
                for code, sid in sorted(r["pilihan"].items(),
                                        key=lambda kv: (HARI.index(problem.slots[krs.slot(kv[1])].day),
                                                        problem.slots[krs.slot(kv[1])].start)):
                    a, sl = jadwal[sid], problem.slots[krs.slot(sid)]
                    baris.append({"Kelas": problem.sections[sid].course,
                                  "Dosen": problem.lecturers[a.lecturer_id].name,
                                  "Hari": sl.day, "Jam": f"{sl.start:02d}.00-{sl.end:02d}.00",
                                  "Ruang": problem.rooms[a.room_id].name,
                                  "Dipilih oleh": "kamu" if code in picks else "AI"})
                st.dataframe(baris, use_container_width=True, hide_index=True)
                st.info(krs.jelaskan(r))

with tab_adv:
    st.subheader("Dua mahasiswa berebut kelas (minimax + alpha-beta)")
    st.write("Mahasiswa A dan B bergiliran memilih kelas dari jadwal tetap hasil CSP. "
             "Kuota kelas terbatas, jadi kelas yang diambil A bisa hilang untuk B. "
             "Nilai akhir = total kesukaan A dikurangi total kesukaan B.")
    c1, c2, c3 = st.columns(3)
    max_pick = c1.slider("Kelas per mahasiswa", 1, 4, 3)
    kuota = c2.slider("Kuota tiap kelas", 1, 2, 1)
    seed = c3.number_input("Seed preferensi", 0, 999, 1)

    if st.button("Jalankan skenario"):
        _, h = jalankan_skenario(jadwal, int(seed), int(seed) + 1, max_pick, kuota, problem)
        st.metric("Nilai permainan optimal (A - B)", h["nilai_optimal"])
        m1, m2 = st.columns(2)
        m1.metric("Node minimax", h["node_minimax"])
        m2.metric("Node alpha-beta", h["node_alphabeta"])
        baris = [{"Strategi A": sa, "Strategi B": sb, "Nilai (A - B)": r["nilai"],
                  "Kelas A": ", ".join(r["kelas_a"]), "Kelas B": ", ".join(r["kelas_b"])}
                 for (sa, sb), r in h["kombinasi"].items()]
        st.table(baris)
        st.caption("Minimax menjamin hasil terburuk terbaik; greedy cepat tetapi tidak melihat langkah lawan.")
