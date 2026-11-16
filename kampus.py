"""Alur 1: data kampus -> CSP -> 1 jadwal tetap (dosen, ruang, jam tiap kelas).

Hasilnya dipakai krs.KRS untuk alur 2 (mahasiswa memilih maks 3 kelas, AI ranking melengkapi sisanya).
"""
import random

from constraints import validate_schedule
from models import HARI, Lecturer, Problem, Room, Section, Slot
from solver import solve_with_stats

# (kode, nama, sks)
MATKUL = [
    ("TG", "Teori Graf", 3),
    ("MD", "Matematika Diskrit", 3),
    ("KKA", "KKA", 3),
    ("KPPL", "KPPL", 2),
    ("PW", "Pemrograman Web", 3),
    ("JK", "Jaringan Komputer", 4),
    ("PBO", "Pemrograman Berbasis Objek", 3),
]

# dosen bebas: (id, nama, mata kuliah yang boleh diajar)
DOSEN = [
    ("D1", "Pak Budi", ["KKA", "TG"]),
    ("D2", "Bu Siti", ["JK", "KPPL"]),
    ("D3", "Pak Andi", ["MD", "TG"]),
    ("D4", "Bu Rina", ["PW", "PBO"]),
    ("D5", "Pak Dedi", ["JK", "PBO", "PW"]),
    ("D6", "Bu Citra", ["KKA", "MD", "KPPL"]),
]
MAKS_KELAS_PER_HARI = 4

RUANGAN = [(f"R{n}", f"Ruang {n}", 50) for n in range(101, 113)] + [
    ("LAB", "Lab Pemrograman", 100),
    ("AULA", "Aula Handayani", 100),
]

JAM_MULAI, JAM_SELESAI = 7, 17     # Senin - Jumat
KELAS_PER_MATKUL = 3               # kelas A, B, C
UKURAN_KELAS = 40


def buat_problem(kelas_per_matkul=KELAS_PER_MATKUL):
    """1 sks = 1 jam. Slot dibuat untuk tiap durasi, kelas hanya boleh di slot yang lamanya = sks-nya."""
    durasi = sorted({sks for _, _, sks in MATKUL})
    slots = {}
    for hari in HARI:
        for d in durasi:
            for mulai in range(JAM_MULAI, JAM_SELESAI - d + 1):
                sid = f"{hari}-{mulai:02d}-{d}"
                slots[sid] = Slot(sid, hari, mulai, mulai + d)

    rooms = {rid: Room(rid, nama, kap) for rid, nama, kap in RUANGAN}
    semua_slot = frozenset(slots)
    lecturers = {did: Lecturer(did, nama, semua_slot, frozenset(), 99, MAKS_KELAS_PER_HARI)
                 for did, nama, _ in DOSEN}

    sections = {}
    for kode, nama, sks in MATKUL:
        boleh = tuple(did for did, _, mk in DOSEN if kode in mk)
        for i in range(kelas_per_matkul):
            huruf = chr(ord("A") + i)
            sid = f"{kode}-{huruf}"
            sections[sid] = Section(sid, f"{nama} {huruf}", sks, UKURAN_KELAS, boleh, "", kode)
    return Problem(lecturers, rooms, slots, sections, match_duration=True)


def buat_jadwal_tetap(problem=None, seed=0, max_coba=20):
    """Jalankan CSP (backtracking + MRV + FC). Diulang dengan seed berikutnya sampai jadwal yang
    didapat memungkinkan mahasiswa mengambil semua mata kuliah tanpa bentrok."""
    from krs import KRS

    problem = problem or buat_problem()
    for i in range(max_coba):
        jadwal, _ = solve_with_stats(problem, True, True, random.Random(seed + i))
        if jadwal is None:
            continue
        assert not validate_schedule(jadwal, problem)
        if KRS(jadwal, problem).lengkapi({}, limit=1)[0]:
            return jadwal
    return None


def tabel_jadwal(jadwal, problem):
    """Daftar kelas terurut hari/jam, siap ditampilkan sebagai tabel."""
    def urut(item):
        sl = problem.slots[item[1].slot_id]
        return HARI.index(sl.day), sl.start, item[0]

    baris = []
    for sid, a in sorted(jadwal.items(), key=urut):
        sec, sl = problem.sections[sid], problem.slots[a.slot_id]
        baris.append({
            "Kelas": sec.course,
            "SKS": sec.sks,
            "Dosen": problem.lecturers[a.lecturer_id].name,
            "Hari": sl.day,
            "Jam": f"{sl.start:02d}.00-{sl.end:02d}.00",
            "Ruang": problem.rooms[a.room_id].name,
        })
    return baris


if __name__ == "__main__":
    import time

    problem = buat_problem()
    t0 = time.perf_counter()
    jadwal = buat_jadwal_tetap(problem)
    print(f"{len(problem.sections)} kelas, selesai {time.perf_counter() - t0:.1f} detik")
    for b in tabel_jadwal(jadwal, problem):
        print(" | ".join(str(v) for v in b.values()))
