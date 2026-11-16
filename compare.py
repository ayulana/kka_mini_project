import random
import statistics

from data import load_problem
from models import Lecturer, Problem, Room, Section, Slot
from solver import solve_with_stats

VARIAN = [
    ("BT biasa", False, False),
    ("BT + MRV", True, False),
    ("BT + FC", False, True),
    ("BT + MRV + FC", True, True),
]

MAX_NODES = 20000


def buat_soal_acak(n_kelas, n_slot, n_ruang, n_dosen, p_tersedia, seed):
    r = random.Random(seed)
    slots = {f"T{i}": Slot(f"T{i}", "Sen", 8 + i, 9 + i) for i in range(n_slot)}
    rooms = {f"R{i}": Room(f"R{i}", f"R{i}", r.choice([30, 40, 50, 70])) for i in range(n_ruang)}
    lecturers = {}
    for i in range(n_dosen):
        tersedia = frozenset(s for s in slots if r.random() < p_tersedia) or frozenset(["T0"])
        lecturers[f"D{i}"] = Lecturer(f"D{i}", f"D{i}", tersedia, frozenset(), n_kelas // n_dosen + 1)
    sections = {
        f"S{i}": Section(f"S{i}", f"S{i}", 3, r.randint(25, 65), tuple(r.sample(list(lecturers), 2)))
        for i in range(n_kelas)
    }
    return Problem(lecturers, rooms, slots, sections)


def kumpulkan_soal_punya_solusi(jumlah, **cfg):
    soal, seed = [], 0
    while len(soal) < jumlah and seed < 2000:
        p = buat_soal_acak(seed=seed, **cfg)
        sol, _ = solve_with_stats(p, True, True, random.Random(seed), 100000)
        if sol is not None:
            soal.append((seed, p))
        seed += 1
    return soal


def benchmark(daftar_soal):
    rows = []
    for nama, mrv, fc in VARIAN:
        hasil = []
        for seed, p in daftar_soal:
            sol, st = solve_with_stats(p, mrv, fc, random.Random(seed), MAX_NODES)
            hasil.append((sol is not None, st))
        rows.append({
            "varian": nama,
            "selesai": sum(1 for ok, _ in hasil if ok),
            "total": len(hasil),
            "nodes": statistics.mean(st["nodes"] for _, st in hasil),
            "backtracks": statistics.mean(st["backtracks"] for _, st in hasil),
            "checks": statistics.mean(st["checks"] for _, st in hasil),
            "ms": statistics.mean(st["ms"] for _, st in hasil),
        })
    return rows


def cetak(judul, rows):
    print(f"\n### {judul}")
    print("| Varian | Soal selesai | Rata2 node | Rata2 backtrack | Rata2 cek konstrain | Rata2 waktu (ms) |")
    print("| --- | --- | --- | --- | --- | --- |")
    for r in rows:
        print(f"| {r['varian']} | {r['selesai']}/{r['total']} | {r['nodes']:.0f} | {r['backtracks']:.0f} "
              f"| {r['checks']:.0f} | {r['ms']:.1f} |")


if __name__ == "__main__":
    cetak("Skenario 1: dataset proyek (8 kelas, longgar), 30 urutan acak",
          benchmark([(s, load_problem()) for s in range(30)]))

    soal2 = kumpulkan_soal_punya_solusi(20, n_kelas=14, n_slot=7, n_ruang=3, n_dosen=6, p_tersedia=0.5)
    cetak("Skenario 2: soal acak ketat (14 kelas, 7 slot, 3 ruang, 6 dosen), 20 soal", benchmark(soal2))

    soal3 = kumpulkan_soal_punya_solusi(20, n_kelas=16, n_slot=7, n_ruang=3, n_dosen=7, p_tersedia=0.5)
    cetak("Skenario 3: soal acak lebih besar (16 kelas, 7 slot, 3 ruang, 7 dosen), 20 soal", benchmark(soal3))

    print(f"\nBatas node per pencarian = {MAX_NODES}. 'Soal selesai' < total berarti varian itu "
          f"menyerah (batas node tercapai) pada sebagian soal.")
