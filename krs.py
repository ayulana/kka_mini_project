from pathlib import Path

from constraints import overlap
from data import load_problem
from models import HARI

DATASET_KRS = Path(__file__).resolve().parent / "dataset_krs.json"

BOBOT = {
    "dosen_favorit": 0.40,
    "jeda_sedikit": 0.25,
    "hari_sedikit": 0.20,
    "hindari_sore": 0.15,
    "hari_kosong": 0.25, 
}

LABEL = {
    "dosen_favorit": "kelasnya diajar dosen favorit",
    "jeda_sedikit": "jeda kosong antar kelas sedikit",
    "hari_sedikit": "kuliah terkumpul di sedikit hari",
    "hindari_sore": "tidak ada kelas sore",
    "hari_kosong": "hari yang diminta kosong terpenuhi",
}


def muat_problem_krs():
    return load_problem(DATASET_KRS)


class KRS:
    def __init__(self, schedule, problem, wanted=None, max_sks=24, enrolled=None):
        self.schedule = schedule
        self.problem = problem
        self.max_sks = max_sks
        self.enrolled = enrolled or {}

        self.by_course = {}
        for sid in problem.sections:
            if sid in schedule:
                self.by_course.setdefault(self.kode(sid), []).append(sid)
        self.wanted = tuple(wanted) if wanted else tuple(self.by_course)
        unknown = [c for c in self.wanted if c not in self.by_course]
        if unknown:
            raise ValueError(f"Mata kuliah tidak ada di jadwal: {unknown}")

    def kode(self, sid):
        sec = self.problem.sections[sid]
        return sec.course_code or sec.course

    def nama_matkul(self, code):
        nama = self.problem.sections[self.by_course[code][0]].course
        kepala, _, ekor = nama.rpartition(" ")
        return kepala if kepala and len(ekor) == 1 and ekor.isupper() else nama

    def slot(self, sid):
        return self.schedule[sid].slot_id

    def deskripsi(self, sid):
        a = self.schedule[sid]
        sec = self.problem.sections[sid]
        sl = self.problem.slots[a.slot_id]
        return (f"{sec.course} | {self.problem.lecturers[a.lecturer_id].name} | "
                f"{sl.day} {sl.start:02d}.00-{sl.end:02d}.00 | {self.problem.rooms[a.room_id].name}")

    def sisa_kuota(self, sid):
        kapasitas = self.problem.rooms[self.schedule[sid].room_id].capacity
        return kapasitas - self.enrolled.get(sid, 0)

    def _cek(self, sid, assign):
        if self.sisa_kuota(sid) <= 0:
            return "penuh", "kuota kelas sudah penuh"
        total = self.problem.sections[sid].sks
        for code, other in assign.items():
            if code == self.kode(sid):
                continue
            if overlap(self.problem, self.slot(other), self.slot(sid)):
                return "bentrok", f"bentrok dengan {self.problem.sections[other].course} ({self.slot(sid)})"
            total += self.problem.sections[other].sks
        if total > self.max_sks:
            return "sks", f"melebihi batas {self.max_sks} SKS"
        return None

    def domain_awal(self):
        return {c: [s for s in self.by_course[c] if self.sisa_kuota(s) > 0] for c in self.wanted}

    def lengkapi(self, picks, method="fc", limit=None):
        use_fc = method == "fc"
        stats = {"nodes": 0, "checks": 0, "backtracks": 0}
        solutions = []

        assign = {}
        for code, sid in picks.items():
            if self._cek(sid, assign) is not None:
                return [], stats
            assign[code] = sid

        domains = {c: list(self.by_course[c]) for c in self.wanted if c not in picks}

        def rec(doms):
            stats["nodes"] += 1
            if limit and len(solutions) >= limit:
                return
            if not doms:
                solutions.append(dict(assign))
                return
            code = min(doms, key=lambda c: len(doms[c])) if use_fc else next(iter(doms))
            for sid in doms[code]:
                if not use_fc: 
                    stats["checks"] += 1
                    if self._cek(sid, assign) is not None:
                        stats["backtracks"] += 1
                        continue
                assign[code] = sid
                rest = {c: d for c, d in doms.items() if c != code}
                ok = True
                if use_fc: 
                    filtered = {}
                    for other, d in rest.items():
                        kept = []
                        for s in d:
                            stats["checks"] += 1
                            if self._cek(s, assign) is None:
                                kept.append(s)
                        if not kept:
                            ok = False
                            break
                        filtered[other] = kept
                    rest = filtered
                if ok:
                    rec(rest)
                else:
                    stats["backtracks"] += 1
                del assign[code]

        if use_fc: 
            pre = {}
            for code, d in domains.items():
                kept = [s for s in d if self._cek(s, assign) is None]
                if not kept:
                    return [], stats
                pre[code] = kept
            domains = pre
        rec(domains)
        return solutions, stats

    def status_opsi(self, picks, method="fc"):
        hasil = {}
        for code in self.wanted:
            lain = {c: s for c, s in picks.items() if c != code}
            baris = []
            for sid in self.by_course[code]:
                masalah = self._cek(sid, lain)
                if masalah:
                    status, alasan = masalah
                elif not self.lengkapi({**lain, code: sid}, method, limit=1)[0]:
                    status, alasan = "buntu", "membuat mata kuliah lain tidak bisa diambil"
                else:
                    status, alasan = "bisa", ""
                baris.append({"sid": sid, "status": status, "alasan": alasan})
            hasil[code] = baris
        return hasil

    def opsi_tersisa(self, picks, method="fc"):
        st = self.status_opsi(picks, method)
        return {c: [b["sid"] for b in st[c] if b["status"] == "bisa"]
                for c in self.wanted if c not in picks}

    def _komponen(self, pilihan, preferensi):
        sids = list(pilihan.values())
        n = len(sids)
        slots = self.problem.slots
        per_hari = {}
        for s in sids:
            sl = slots[self.slot(s)]
            per_hari.setdefault(sl.day, []).append((sl.start, sl.end))

        jeda = 0  # total jam kosong di antara kelas pada hari yang sama
        for jam in per_hari.values():
            jam.sort()
            jeda += sum(max(0, b[0] - a[1]) for a, b in zip(jam, jam[1:]))

        hari_total = len({sl.day for sl in slots.values()})
        komp = {
            "jeda_sedikit": max(0.0, 1 - jeda / n),
            "hari_sedikit": 1 - (len(per_hari) - 1) / max(1, hari_total - 1),
            "hindari_sore": 1 - sum(1 for s in sids if slots[self.slot(s)].end > 15) / n,
        }
        fav = set(preferensi.get("dosen_favorit", ()))
        if fav:
            komp["dosen_favorit"] = sum(1 for s in sids if self.schedule[s].lecturer_id in fav) / n
        kosong = preferensi.get("hari_kosong")
        if kosong:
            komp["hari_kosong"] = 0.0 if kosong in per_hari else 1.0
        return komp

    def skor(self, pilihan, preferensi=None):
        komp = self._komponen(pilihan, preferensi or {})
        total_bobot = sum(BOBOT[k] for k in komp)
        nilai = 100 * sum(BOBOT[k] * v for k, v in komp.items()) / total_bobot
        return round(nilai, 2), komp

    def rekomendasi(self, picks, preferensi=None, top_k=3, method="fc"):
        jadwal, _ = self.lengkapi(picks, method)
        hasil = []
        for p in jadwal:
            s, komp = self.skor(p, preferensi)
            hasil.append({"skor": s, "pilihan": p, "rincian": komp})
        hasil.sort(key=lambda r: (-r["skor"], sorted(r["pilihan"].items())))
        return hasil[:top_k]

    def jelaskan(self, rekom):
        komp = rekom["rincian"]
        terbaik = max(komp, key=komp.get)
        terlemah = min(komp, key=komp.get)
        return (f"Skor {rekom['skor']}/100. Kelebihan: {LABEL[terbaik]}. "
                f"Titik terlemah: {LABEL[terlemah].replace('kelasnya ', '')} ({komp[terlemah]:.0%}).")

    def tampilkan(self, pilihan):
        slots = self.problem.slots
        urut = sorted(pilihan.values(), key=lambda s: (HARI.index(slots[self.slot(s)].day)
                                                       if slots[self.slot(s)].day in HARI else 9,
                                                       slots[self.slot(s)].start))
        return "\n".join(self.deskripsi(s) for s in urut)


if __name__ == "__main__":
    from main import run_pipeline

    problem = muat_problem_krs()
    _, ranked = run_pipeline(DATASET_KRS)
    if not ranked:
        raise SystemExit("Tidak ada jadwal kampus yang valid untuk dataset_krs.json")
    krs = KRS(ranked[0].schedule, problem)

    print("=== Jadwal kampus (peringkat 1) ===")
    for code in krs.wanted:
        for sid in krs.by_course[code]:
            print(f"{krs.nama_matkul(code):20} | {krs.deskripsi(sid)}")

    picks = {}
    print("\n=== Langkah 1: belum ada pilihan, semua opsi ===")
    for code, baris in krs.status_opsi(picks).items():
        print(code, [(b["sid"], b["status"]) for b in baris])

    pertama = krs.status_opsi(picks)[krs.wanted[0]]
    sid = next(b["sid"] for b in pertama if b["status"] == "bisa")
    picks[krs.kode(sid)] = sid
    print(f"\n=== Langkah 2: mahasiswa memilih {krs.deskripsi(sid)} ===")
    for code, baris in krs.status_opsi(picks).items():
        if code in picks:
            continue
        for b in baris:
            ket = f" ({b['alasan']})" if b["alasan"] else ""
            print(f"{code:5} {b['sid']:4} {b['status']:7}{ket}")

    print("\n=== Rekomendasi jadwal lengkap (dosen favorit: Bu Sari) ===")
    for i, r in enumerate(krs.rekomendasi(picks, {"dosen_favorit": {"D2"}}), 1):
        print(f"\nPeringkat {i}")
        print(krs.tampilkan(r["pilihan"]))
        print(krs.jelaskan(r))

    for metode in ("basic", "fc"):
        sol, st = krs.lengkapi({}, metode)
        print(f"\nmetode {metode:5}: {len(sol)} jadwal lengkap, {st}")
