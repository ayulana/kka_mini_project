from constraints import validate_schedule
from data import load_problem
from ranking import explain, rank
from solver import solve_all


def run_pipeline(path=None, limit=30, top_k=5):
    problem = load_problem(path)
    schedules = solve_all(problem, limit=limit)
    return problem, rank(schedules, problem, top_k=top_k)


def format_schedule(schedule, problem):
    rows = []
    for sid, a in sorted(schedule.items(), key=lambda kv: (problem.slots[kv[1].slot_id].day,
                                                           problem.slots[kv[1].slot_id].start)):
        sec = problem.sections[sid]
        rows.append(f"{a.slot_id:7} | {sec.course:20} | {problem.lecturers[a.lecturer_id].name:10} "
                    f"| {problem.rooms[a.room_id].name}")
    return "\n".join(rows)


def check_student_selection(selected_ids, schedule, problem, max_sks=24, enrolled=None):
    enrolled = enrolled or {}
    errors = []

    seen_slots = {}
    for sid in selected_ids:
        slot = schedule[sid].slot_id
        if slot in seen_slots:
            errors.append(f"Bentrok: {problem.sections[sid].course} dan "
                          f"{problem.sections[seen_slots[slot]].course} sama-sama di {slot}")
        seen_slots[slot] = sid

    total_sks = sum(problem.sections[s].sks for s in selected_ids)
    if total_sks > max_sks:
        errors.append(f"Total SKS {total_sks} melebihi batas {max_sks}")

    for sid in selected_ids:
        quota = problem.rooms[schedule[sid].room_id].capacity
        if enrolled.get(sid, 0) >= quota:
            errors.append(f"Kuota {problem.sections[sid].course} sudah penuh")
    return errors


if __name__ == "__main__":
    problem, ranked = run_pipeline()
    if not ranked:
        print("Tidak ada jadwal valid untuk data ini.")
    for i, r in enumerate(ranked, 1):
        print(f"\n=== Peringkat {i} ===")
        print(format_schedule(r.schedule, problem))
        print(explain(r, problem))
        assert not validate_schedule(r.schedule, problem)

    if ranked:
        best = ranked[0].schedule
        pilihan = list(best)[:3]
        print("\n--- Simulasi war mahasiswa (3 kelas pertama) ---")
        masalah = check_student_selection(pilihan, best, problem)
        print("Pilihan valid" if not masalah else "\n".join(masalah))

        from adversarial import jalankan_skenario
        _, h = jalankan_skenario(best)
        print("\n--- Skenario adversarial: dua mahasiswa berebut kelas ---")
        print(f"Nilai optimal (A - B): {h['nilai_optimal']}")
        print(f"Node minimax: {h['node_minimax']}, node alpha-beta: {h['node_alphabeta']}")
        for (sa, sb), r in h["kombinasi"].items():
            print(f"A={sa:8} B={sb:8} -> nilai {r['nilai']:>3} | A {r['kelas_a']} | B {r['kelas_b']}")
