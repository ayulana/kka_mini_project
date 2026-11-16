import json
from pathlib import Path

from models import Lecturer, Problem, Room, Section, Slot

DEFAULT_PATH = Path(__file__).resolve().parent / "dataset.json"

def load_problem(path=None) -> Problem:
    with open(path or DEFAULT_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    slots = {s["id"]: Slot(s["id"], s["day"], s["start"], s["end"]) for s in raw["slots"]}
    rooms = {r["id"]: Room(r["id"], r["name"], r["capacity"]) for r in raw["rooms"]}
    lecturers = {
        d["id"]: Lecturer(
            d["id"],
            d["name"],
            frozenset(d["available_slots"]),
            frozenset(d["preferred_slots"]),
            d["max_load"],
        )
        for d in raw["lecturers"]
    }
    sections = {
        s["id"]: Section(s["id"], s["course"], s["sks"], s["size"],
                         tuple(s["eligible_lecturers"]), s.get("group", ""), s.get("course_code", ""))
        for s in raw["sections"]
    }
    return Problem(lecturers=lecturers, rooms=rooms, slots=slots, sections=sections)
