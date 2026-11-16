import json
import random
from pathlib import Path

HARI = ["Sen", "Sel", "Rab", "Kam", "Jum"]
JAM = [(8, 10), (10, 12)]
NAMA_DOSEN = ["Andi", "Sari", "Budi", "Citra", "Dedi", "Eka", "Fajar", "Gita", "Hadi", "Indah",
              "Joko", "Kiki"]
NAMA_MK = ["Basis Data", "Algoritma", "Jaringan Komputer", "Kecerdasan Buatan", "Pemrograman Web",
           "Teori Graf", "Sistem Operasi", "Struktur Data", "Rekayasa Perangkat Lunak",
           "Matematika Diskrit", "Keamanan Informasi", "Pemrograman Mobile"]

UKURAN = {
    "small": (8, 5, 4, 3, 1),
    "medium": (30, 8, 6, 6, 1),
    "large": (60, 12, 10, 12, 1),
}

def buat(nama, seed=2026):
    n_kelas, n_dosen, n_ruang, n_grup, slack = UKURAN[nama]
    rng = random.Random(seed)
    slots = [{"id": f"{h}-{a:02d}", "day": h, "start": a, "end": b} for h in HARI for a, b in JAM]
    slot_ids = [s["id"] for s in slots]
    kapasitas = [30, 40, 50, 70]
    rooms = [{"id": f"R{i+1}", "name": f"Ruang {i+1}", "capacity": kapasitas[i % 4]} for i in range(n_ruang)]
    dosen_ids = [f"D{i+1}" for i in range(n_dosen)]
    grup_ids = [f"G{i+1}" for i in range(n_grup)]

    pakai_ruang, pakai_dosen, pakai_grup = set(), set(), set()   
    beban = {d: 0 for d in dosen_ids}
    batas_beban = -(-n_kelas // n_dosen)                         
    tanam = []
    for i in range(n_kelas):
        grup = grup_ids[i % n_grup]
        for _ in range(10000):
            sl = rng.choice(slot_ids)
            rm = rng.choice(rooms)["id"]
            dn = rng.choice(dosen_ids)
            if ((rm, sl) in pakai_ruang or (dn, sl) in pakai_dosen or (grup, sl) in pakai_grup
                    or beban[dn] >= batas_beban):
                continue
            break
        else:
            raise RuntimeError("gagal menanam jadwal; ubah UKURAN")
        pakai_ruang.add((rm, sl)); pakai_dosen.add((dn, sl)); pakai_grup.add((grup, sl))
        beban[dn] += 1
        tanam.append((grup, sl, rm, dn))

    kap = {r["id"]: r["capacity"] for r in rooms}
    sections = []
    for i, (grup, sl, rm, dn) in enumerate(tanam):
        ukuran = rng.randint(20, kap[rm])
        elig = {dn} | set(rng.sample(dosen_ids, rng.randint(0, 2)))
        sections.append({
            "id": f"S{i+1}",
            "course": f"{NAMA_MK[i % len(NAMA_MK)]} {chr(65 + i // len(NAMA_MK))}",
            "sks": rng.choice([2, 3]),
            "size": ukuran,
            "eligible_lecturers": sorted(elig),
            "group": grup,
        })
    lecturers = []
    for d in dosen_ids:
        wajib = {sl for (_, sl, _, dn) in tanam if dn == d} 
        tambahan = set(rng.sample(slot_ids, rng.randint(3, 6)))
        avail = sorted(wajib | tambahan, key=slot_ids.index)
        pref = sorted(rng.sample(avail, min(2, len(avail))), key=slot_ids.index)
        lecturers.append({
            "id": d, "name": NAMA_DOSEN[dosen_ids.index(d) % len(NAMA_DOSEN)],
            "max_load": beban[d] + slack, "available_slots": avail, "preferred_slots": pref,
        })
    return {"slots": slots, "rooms": rooms, "lecturers": lecturers, "sections": sections}


if __name__ == "__main__":
    folder = Path(__file__).resolve().parent
    for nama in UKURAN:
        data = buat(nama)
        (folder / f"dataset_{nama}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"dataset_{nama}.json: {len(data['sections'])} kelas, {len(data['lecturers'])} dosen, "
              f"{len(data['rooms'])} ruang, {len(data['slots'])} slot")
