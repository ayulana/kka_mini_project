from models import Assignment

def overlap(problem, slot_a, slot_b):
    if slot_a == slot_b:
        return True
    a, b = problem.slots[slot_a], problem.slots[slot_b]
    return a.day == b.day and a.start < b.end and b.start < a.end


def build_domain(section, problem):
    domain = []
    for lid in section.eligible_lecturers:
        lec = problem.lecturers[lid]
        for room in problem.rooms.values():
            if room.capacity < section.size:
                continue
            for slot_id in sorted(lec.available_slots):
                if slot_id not in problem.slots:
                    continue
                sl = problem.slots[slot_id]
                if problem.match_duration and sl.end - sl.start != section.sks:
                    continue
                domain.append(Assignment(lid, room.id, slot_id))
    return domain

def is_consistent(section_id, assignment, partial, problem):
    load = 1
    load_hari = 1
    group = problem.sections[section_id].group
    hari = problem.slots[assignment.slot_id].day
    for other_id, other in partial.items():
        if other_id == section_id:
            continue
        if overlap(problem, other.slot_id, assignment.slot_id):
            if other.lecturer_id == assignment.lecturer_id:
                return False
            if other.room_id == assignment.room_id:
                return False
            if group and problem.sections[other_id].group == group:
                return False
        if other.lecturer_id == assignment.lecturer_id:
            load += 1
            if problem.slots[other.slot_id].day == hari:
                load_hari += 1
    lec = problem.lecturers[assignment.lecturer_id]
    return load <= lec.max_load and load_hari <= lec.max_per_day


def validate_schedule(schedule, problem):
    errors = []
    for sid, a in schedule.items():
        sec = problem.sections[sid]
        lec = problem.lecturers[a.lecturer_id]
        room = problem.rooms[a.room_id]
        if a.lecturer_id not in sec.eligible_lecturers:
            errors.append(f"{sid}: {lec.name} tidak boleh mengajar {sec.course}")
        if room.capacity < sec.size:
            errors.append(f"{sid}: kapasitas {room.name} ({room.capacity}) < {sec.size}")
        if a.slot_id not in lec.available_slots:
            errors.append(f"{sid}: {lec.name} tidak tersedia di {a.slot_id}")

    ids = list(schedule)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = schedule[ids[i]], schedule[ids[j]]
            if overlap(problem, a.slot_id, b.slot_id):
                if a.lecturer_id == b.lecturer_id:
                    errors.append(f"{ids[i]} & {ids[j]}: dosen {a.lecturer_id} bentrok di {a.slot_id}")
                if a.room_id == b.room_id:
                    errors.append(f"{ids[i]} & {ids[j]}: ruang {a.room_id} bentrok di {a.slot_id}")
                ga, gb = problem.sections[ids[i]].group, problem.sections[ids[j]].group
                if ga and ga == gb:
                    errors.append(f"{ids[i]} & {ids[j]}: mahasiswa kelompok {ga} bentrok di {a.slot_id}")

    for lid, lec in problem.lecturers.items():
        n = sum(1 for a in schedule.values() if a.lecturer_id == lid)
        if n > lec.max_load:
            errors.append(f"{lec.name} mengajar {n} kelas (maks {lec.max_load})")
        per_hari = {}
        for a in schedule.values():
            if a.lecturer_id == lid:
                d = problem.slots[a.slot_id].day
                per_hari[d] = per_hari.get(d, 0) + 1
        for d, n in per_hari.items():
            if n > lec.max_per_day:
                errors.append(f"{lec.name} mengajar {n} kelas di hari {d} (maks {lec.max_per_day}/hari)")
    return errors
