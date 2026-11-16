from typing import NamedTuple

WEIGHTS = {
    "preferensi_dosen": 0.30, 
    "jeda_dosen": 0.25, 
    "sebaran_hari": 0.15, 
    "hindari_sore": 0.15,  
    "kecocokan_ruang": 0.15,
}

class Ranked(NamedTuple):
    score: float 
    schedule: dict
    breakdown: dict

def _slot_order(problem):
    by_day = {}
    for s in problem.slots.values():
        by_day.setdefault(s.day, []).append(s)
    return {d: [s.id for s in sorted(v, key=lambda x: x.start)] for d, v in by_day.items()}

def breakdown(schedule, problem):
    n = len(schedule)
    order = _slot_order(problem)

    hits = sum(1 for a in schedule.values()
               if a.slot_id in problem.lecturers[a.lecturer_id].preferred_slots)
    preferensi = hits / n

    gaps = 0
    per_lecturer_day = {}
    for a in schedule.values():
        day = problem.slots[a.slot_id].day
        per_lecturer_day.setdefault((a.lecturer_id, day), []).append(order[day].index(a.slot_id))
    for idxs in per_lecturer_day.values():
        gaps += (max(idxs) - min(idxs) + 1) - len(idxs)
    jeda = max(0.0, 1 - gaps / n)

    days_used = len({problem.slots[a.slot_id].day for a in schedule.values()})
    days_total = len({s.day for s in problem.slots.values()})
    sebaran = days_used / min(n, days_total)

    late = sum(1 for a in schedule.values() if problem.slots[a.slot_id].start >= 16)
    sore = 1 - late / n

    fit = sum(problem.sections[sid].size / problem.rooms[a.room_id].capacity
              for sid, a in schedule.items()) / n

    return {
        "preferensi_dosen": preferensi,
        "jeda_dosen": jeda,
        "sebaran_hari": sebaran,
        "hindari_sore": sore,
        "kecocokan_ruang": fit,
    }


def score(schedule, problem):
    bd = breakdown(schedule, problem)
    return 100 * sum(WEIGHTS[k] * v for k, v in bd.items()), bd


def rank(schedules, problem, top_k=5):
    ranked = []
    for sch in schedules:
        s, bd = score(sch, problem)
        ranked.append(Ranked(round(s, 2), sch, bd))
    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked[:top_k]


def explain(ranked, problem):
    labels = {
        "preferensi_dosen": "banyak kelas jatuh di jam favorit dosen",
        "jeda_dosen": "jeda kosong dosen sedikit",
        "sebaran_hari": "kelas tersebar ke beberapa hari",
        "hindari_sore": "tidak ada kelas sore",
        "kecocokan_ruang": "ukuran ruang pas dengan jumlah mahasiswa",
    }
    top = sorted(ranked.breakdown.items(), key=lambda kv: kv[1], reverse=True)[:2]
    weak = min(ranked.breakdown.items(), key=lambda kv: kv[1])
    return (f"Skor {ranked.score}/100. Kelebihan: {labels[top[0][0]]} dan {labels[top[1][0]]}. "
            f"Titik terlemah: {weak[0].replace('_', ' ')} (nilai {weak[1]:.0%}).")
