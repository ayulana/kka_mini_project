import csv
import random
import statistics
from pathlib import Path

from constraints import build_domain, is_consistent, validate_schedule
from data import load_problem
from solver import solve_with_stats

FOLDER = Path(__file__).resolve().parent
DATASETS = ["small", "medium", "large"]
SOLVERS = {"A: BT biasa": (False, False), "B: MRV + FC": (True, True)}
ULANGAN = 5           
BATAS_NODE = 50000    

def jalankan():
    baris = []
    for nama in DATASETS:
        problem = load_problem(FOLDER / f"dataset_{nama}.json")
        for label, (mrv, fc) in SOLVERS.items():
            hasil = []
            for seed in range(ULANGAN):
                sol, st = solve_with_stats(problem, mrv, fc, random.Random(seed), BATAS_NODE)
                if sol is not None:
                    assert not validate_schedule(sol, problem), "solver menghasilkan jadwal tidak valid!"
                hasil.append((sol is not None, st))
            sukses = [st for ok, st in hasil if ok]
            baris.append({
                "dataset": nama,
                "kelas": len(problem.sections),
                "solver": label,
                "sukses": f"{len(sukses)}/{ULANGAN}",
                "waktu_ms": round(statistics.mean(st["ms"] for st in sukses), 1) if sukses else "TIMEOUT",
                "node": round(statistics.mean(st["nodes"] for st in sukses)) if sukses else "TIMEOUT",
                "backtrack": round(statistics.mean(st["backtracks"] for st in sukses)) if sukses else "TIMEOUT",
                "cek_konstrain": round(statistics.mean(st["checks"] for st in sukses)) if sukses else "TIMEOUT",
            })
    return baris

def hitung_semua_solusi(problem, mrv, fc):
    domains = {sid: build_domain(sec, problem) for sid, sec in problem.sections.items()}
    partial, ditemukan = {}, set()

    def bt(doms):
        if not doms:
            ditemukan.add(tuple(sorted(partial.items())))
            return
        sid = min(doms, key=lambda s: len(doms[s])) if mrv else next(iter(doms))
        for v in doms[sid]:
            if not fc and not is_consistent(sid, v, partial, problem):
                continue
            partial[sid] = v
            rest = {k: d for k, d in doms.items() if k != sid}
            if fc:
                rest = {o: [x for x in d if is_consistent(o, x, partial, problem)] for o, d in rest.items()}
                if any(not d for d in rest.values()):
                    del partial[sid]
                    continue
            bt(rest)
            del partial[sid]

    bt(domains)
    return ditemukan

def cek_kesetaraan():
    from data import load_problem as lp
    import gen_dataset
    gen_dataset.UKURAN["mini"] = (4, 3, 2, 2, 1)
    import json
    tmp = FOLDER / "_mini.json"
    tmp.write_text(json.dumps(gen_dataset.buat("mini")), encoding="utf-8")
    try:
        p = lp(tmp)
        a = hitung_semua_solusi(p, False, False)
        b = hitung_semua_solusi(p, True, True)
    finally:
        tmp.unlink()
    return len(a), len(b), a == b

def cetak(baris):
    kolom = ["dataset", "kelas", "solver", "sukses", "waktu_ms", "node", "backtrack", "cek_konstrain"]
    print(" | ".join(f"{k:>13}" for k in kolom))
    for b in baris:
        print(" | ".join(f"{str(b[k]):>13}" for k in kolom))

if __name__ == "__main__":
    n_a, n_b, sama = cek_kesetaraan()
    print(f"Uji kesetaraan (soal mini): A menemukan {n_a} jadwal, B menemukan {n_b} jadwal, sama = {sama}\n")
    assert sama, "Solver A dan B tidak setara - ada bug!"
    baris = jalankan()
    cetak(baris)
    with open(FOLDER / "benchmark_hasil.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(baris[0]))
        w.writeheader()
        w.writerows(baris)
    print("\nTersimpan: benchmark_hasil.csv")
