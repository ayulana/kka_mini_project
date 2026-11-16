# Penyusun Jadwal Kuliah dengan CSP dan AI Ranking

Proyek kelompok mata kuliah Kecerdasan Buatan (KKA). Program ini menyusun jadwal kuliah satu kampus,
lalu membantu mahasiswa menyusun jadwal pribadinya tanpa bentrok.

## Cara kerjanya

Ada tiga tahap. Hasil tahap sebelumnya jadi bahan tahap berikutnya.

**Tahap 1: Menyusun jadwal kampus (CSP)**

Data masukan ada di `kampus.py`:

| Data | Isi |
| --- | --- |
| Mata kuliah | Teori Graf (3 SKS), Matematika Diskrit (3), KKA (3), KPPL (2), Pemrograman Web (3), Jaringan Komputer (4), PBO (3) |
| Kelas | Tiap mata kuliah punya kelas A, B, dan C, jadi ada 21 kelas |
| Dosen | 6 dosen, masing-masing hanya boleh mengajar mata kuliah tertentu, maksimal 4 kelas per hari |
| Ruangan | Ruang 101 sampai 112 (muat 50 orang), Lab Pemrograman dan Aula Handayani (muat 100 orang) |
| Waktu | Senin sampai Jumat, pukul 07.00 sampai 17.00 |

Satu SKS dihitung satu jam, jadi kelas 3 SKS berlangsung 3 jam berturut-turut dalam satu pertemuan.

CSP memilihkan **dosen, ruang, dan jam** untuk setiap kelas. Aturan yang harus dipenuhi:

- dosen tidak mengajar dua kelas yang jamnya tumpang tindih
- satu ruang tidak dipakai dua kelas pada jam yang tumpang tindih
- kapasitas ruang cukup untuk jumlah mahasiswa
- dosen hanya mengajar mata kuliah yang boleh ia ajar
- dosen mengajar maksimal 4 kelas dalam sehari

Hasilnya satu jadwal tetap, misalnya: *KKA B diajar Pak Budi, Jumat 11.00-14.00, di Ruang 106*.
Solvernya memakai backtracking dengan MRV dan forward checking.

**Tahap 2: Mahasiswa memilih kelas**

Dari jadwal tetap tadi, mahasiswa memilih kelas yang ia inginkan, **maksimal 3 kelas**
(satu kelas untuk tiap mata kuliah yang dipilih). Mata kuliah lainnya dibiarkan kosong.

**Tahap 3: AI ranking melengkapi jadwal**

Untuk mata kuliah yang belum dipilih, program mencari semua kombinasi kelas yang tidak bentrok
dengan pilihan mahasiswa, lalu memberi skor dan mengurutkannya. Tiga kombinasi terbaik ditampilkan.
Skor dihitung dari:

- jeda kosong antar kelas (makin sedikit makin bagus)
- jumlah hari kuliah (makin sedikit makin bagus)
- kelas sore (kelas yang selesai lewat jam 15.00 mengurangi skor)
- dosen favorit (opsional, diisi mahasiswa)
- hari kosong yang diminta (opsional, diisi mahasiswa)

Contoh: mahasiswa memilih KKA A, Jaringan Komputer B, dan Pemrograman Web C. Program akan mengisi
4 mata kuliah sisanya (Teori Graf, Matematika Diskrit, KPPL, PBO) dengan kelas yang jamnya tidak bentrok.

## Cara menjalankan

```
pip install -r requirements.txt
python kampus.py              # lihat jadwal tetap hasil CSP di terminal
streamlit run app.py          # aplikasi web lengkap
python tests_scenarios.py     # jalankan semua tes
```

Aplikasi web punya tiga tab: data dan jadwal CSP, pilih kelas dan AI ranking, dan skenario adversarial.
Tombol "Generate ulang jadwal CSP" membuat jadwal tetap yang baru.

## Isi file

| File | Fungsi |
| --- | --- |
| `kampus.py` | Data kampus dan pembuatan jadwal tetap lewat CSP (tahap 1) |
| `krs.py` | Pilihan mahasiswa dan AI ranking (tahap 2 dan 3) |
| `app.py` | Tampilan web dengan Streamlit |
| `solver.py` | Solver CSP, empat varian lewat `solve_with_stats(problem, use_mrv, use_fc)` |
| `constraints.py` | Semua aturan wajib dan validator jadwal |
| `models.py` | Struktur data (Section, Lecturer, Room, Slot, Assignment, Problem) |
| `ranking.py` | Skor dan urutan jadwal untuk dataset lama |
| `compare.py`, `benchmark.py` | Perbandingan Backtracking biasa, +MRV, +Forward Checking, dan +MRV+FC |
| `adversarial.py` | Skenario dua mahasiswa berebut kelas (minimax, alpha-beta, greedy) |
| `main.py`, `data.py`, `dataset*.json` | Alur CLI dan dataset contoh yang lebih kecil, dipakai untuk pengujian dan perbandingan |
| `gen_dataset.py` | Pembuat dataset acak untuk benchmark |
| `tests_scenarios.py` | Skenario uji |

## Mengubah data

Semua data kampus ada di bagian atas `kampus.py`: daftar `MATKUL`, `DOSEN`, `RUANGAN`, jam kuliah,
dan `KELAS_PER_MATKUL`. Ubah di sana, lalu jalankan ulang. Batas 3 pilihan mahasiswa
ada di `MAKS_PILIHAN` pada `app.py`.

## Deploy ke web (Streamlit Community Cloud)

1. Taruh semua file di **root** repo GitHub, bukan di dalam subfolder.
2. Buka share.streamlit.io, masuk dengan akun GitHub, lalu klik **New app**.
3. Pilih repo, branch `main`, main file `app.py`, lalu **Deploy**.
4. Tunggu build beberapa menit. Link publiknya bisa dimasukkan ke PPT.

Aplikasi gratis bisa "tidur" kalau lama tidak dibuka, jadi buka linknya sebelum presentasi
dan siapkan screenshot cadangan. Jangan jalankan `compare.py` lewat web karena butuh sekitar 1 menit.

## Aturan kerja bersama

- Satu orang satu file. Jangan ubah nama atau bentuk fungsi yang dipakai modul lain.
- Fungsi yang dipakai antarmodul:
  - `load_problem(path=None) -> Problem`
  - `build_domain(section, problem) -> list[Assignment]`
  - `is_consistent(section_id, assignment, partial, problem) -> bool`
  - `solve_with_stats(problem, use_mrv, use_fc, rng, max_nodes) -> (Schedule | None, stats)`
  - `jalankan_skenario(schedule, seed_a, seed_b, max_pick, kuota, problem) -> (game, hasil)`
- `Schedule` adalah dict `{section_id: Assignment(lecturer_id, room_id, slot_id)}`.
- Sebelum push, jalankan `python tests_scenarios.py` dan pastikan semuanya OK.
