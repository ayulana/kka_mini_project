# AI University Timetable Generator

Sistem penyusun jadwal kuliah (dosen, kelas, ruang, waktu) dengan **CSP** di Python, dibantu
**AI ranking** untuk memilih opsi terbaik, plus skenario tambahan **adversarial search** (war berebut kelas).
Tugas kelompok 5 orang, deadline 3 November 2026.

## Yang dibangun

1. **CSP**: tiap kelas = variabel, domain = (dosen, ruang, slot waktu). Aturan wajib (hard constraint):
   tidak ada bentrok dosen, ruang, atau kelompok mahasiswa; kapasitas ruang cukup; dosen hanya di jam tersedia;
   beban dosen tidak melebihi batas.
2. **Perbandingan algoritma CSP** (`compare.py`): Backtracking biasa vs +MRV vs +Forward Checking vs +MRV+FC.
3. **AI ranking** (`ranking.py`): jadwal valid dinilai dengan soft constraint (preferensi dosen, jeda, sebaran hari,
   hindari sore, kecocokan ruang), lalu diurutkan.
4. **Adversarial search** (`adversarial.py`): dua mahasiswa berebut kelas, diselesaikan dengan minimax dan
   alpha-beta, dibandingkan dengan greedy.
5. **Antarmuka web** (`app.py`, Streamlit).

## Alur sistem (versi kampus)

1. **Input data** (`kampus.py`): 7 mata kuliah beserta SKS, 6 dosen (maks 4 kelas per hari), ruang 101-112 (50 orang),
   Lab Pemrograman dan Aula Handayani (100 orang), Senin-Jumat 07.00-17.00. Tiap mata kuliah punya kelas A, B, C.
2. **CSP** menghasilkan 1 jadwal tetap: tiap kelas sudah punya dosen, ruang, dan jam (1 SKS = 1 jam berturut-turut).
3. **Mahasiswa** memilih maksimal 3 kelas dari jadwal tetap itu.
4. **AI ranking** (`krs.py`) memilih kelas untuk mata kuliah sisanya, menghasilkan kombinasi utuh tanpa bentrok, diurutkan dengan skor.

Jalankan `python kampus.py` untuk melihat jadwal tetap, atau `streamlit run app.py` untuk alur lengkap.

## Struktur file

| File | Isi |
| --- | --- | 
| `models.py` | Struktur data (Section, Lecturer, Room, Slot, Assignment, Problem) |
| `solver.py` | Solver CSP, 4 varian lewat `solve_with_stats(problem, use_mrv, use_fc)` |
| `compare.py` | Benchmark perbandingan 4 varian solver |
| `dataset.json`, `data.py` | Data dummy dan pemuatnya |
| `constraints.py` | Semua hard constraint dan validator jadwal |
| `ranking.py` | Scoring dan pengurutan jadwal (AI ranking) |
| `adversarial.py` | Minimax, alpha-beta, greedy untuk skenario war |
| `main.py` | Alur utama (CLI) dan aturan war mahasiswa |
| `kampus.py` | Data kampus dan pembuatan jadwal tetap lewat CSP |
| `krs.py` | Pilihan mahasiswa dan AI ranking untuk melengkapi jadwal |
| `app.py` | UI Streamlit |
| `tests_scenarios.py` | Skenario uji |

## Cara menjalankan

```
pip install -r requirements.txt
python main.py                
python tests_scenarios.py     
python compare.py        
streamlit run app.py    
```

## Deploy ke web (Streamlit Community Cloud)

1. Taruh semua file di **root** repo GitHub (bukan di dalam subfolder).
2. Buka share.streamlit.io, masuk dengan akun GitHub, klik **New app**.
3. Pilih repo, branch `main`, main file `app.py`, lalu **Deploy**.
4. Tunggu build beberapa menit. Link publik bisa dimasukkan ke PPT.

Catatan: aplikasi gratis bisa "tidur" kalau lama tidak dibuka, jadi buka linknya sebelum presentasi
dan siapkan screenshot cadangan. Jangan jalankan `compare.py` lewat web (butuh sekitar 1 menit).

## Aturan kerja bersama

- Satu orang satu file (lihat tabel). Jangan ubah nama/bentuk fungsi yang dipakai modul lain.
- Kontrak antarmodul:
  - `load_problem(path=None) -> Problem`
  - `build_domain(section, problem) -> list[Assignment]`
  - `is_consistent(section_id, assignment, partial, problem) -> bool`
  - `solve_with_stats(problem, use_mrv, use_fc, rng, max_nodes) -> (Schedule | None, stats)`
  - `solve_all(problem, limit) -> list[Schedule]`
  - `rank(schedules, problem, top_k) -> list[Ranked]`, `explain(ranked, problem) -> str`
  - `jalankan_skenario(schedule, seed_a, seed_b, max_pick, kuota) -> (game, hasil)`
- `Schedule` adalah dict `{section_id: Assignment(lecturer_id, room_id, slot_id)}`.
- Sebelum push: `python tests_scenarios.py` harus semua OK.

## Catatan untuk asisten AI

Proyek ini tugas kuliah (mata kuliah Kecerdasan Buatan). Tujuan penilaiannya: CSP dimodelkan dengan benar,
ada perbandingan antaralgoritma CSP, ada skenario adversarial search, dan sistem bisa didemokan. Kerjakan hanya
file milik orang yang meminta bantuan, pertahankan kontrak fungsi di atas, dan jalankan
`python tests_scenarios.py` setelah mengubah kode.
