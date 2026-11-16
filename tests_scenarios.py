from dataclasses import replace
from constraints import validate_schedule
from data import load_problem
from main import check_student_selection
from models import Assignment, Room
from ranking import rank
from solver import solve_all


def test_semua_jadwal_valid():
    problem = load_problem()
    schedules = solve_all(problem, limit=10)
    assert schedules, "solver harus menemukan minimal 1 jadwal"
    for sch in schedules:
        assert validate_schedule(sch, problem) == []


def test_ranking_terurut_menurun():
    problem = load_problem()
    ranked = rank(solve_all(problem, limit=20), problem, top_k=5)
    scores = [r.score for r in ranked]
    assert scores == sorted(scores, reverse=True)


def test_tanpa_solusi_kapasitas_kurang():
    problem = load_problem()
    kecil = {rid: Room(rid, r.name, 10) for rid, r in problem.rooms.items()}
    assert solve_all(replace(problem, rooms=kecil)) == []


def test_validator_mendeteksi_bentrok_dosen():
    problem = load_problem()
    sch = {
        "S1": Assignment("D1", "R2", "Sen-08"),
        "S2": Assignment("D1", "R1", "Sen-08"), 
    }
    assert any("bentrok" in e for e in validate_schedule(sch, problem))


def test_war_mahasiswa_bentrok_slot():
    problem = load_problem()
    sch = {
        "S1": Assignment("D1", "R2", "Sen-08"),
        "S5": Assignment("D5", "R1", "Sen-08"),
    }
    assert check_student_selection(["S1", "S5"], sch, problem) != []


def test_war_mahasiswa_batas_sks():
    problem = load_problem()
    sch = {"S1": Assignment("D1", "R2", "Sen-08"), "S3": Assignment("D3", "R3", "Sel-08")}
    assert check_student_selection(["S1", "S3"], sch, problem, max_sks=4) != []


def test_semua_varian_solver_menghasilkan_jadwal_valid():
    import random
    from solver import solve_with_stats
    problem = load_problem()
    for mrv in (False, True):
        for fc in (False, True):
            sol, stats = solve_with_stats(problem, mrv, fc, random.Random(0))
            assert sol is not None, f"varian mrv={mrv} fc={fc} harus menemukan solusi"
            assert validate_schedule(sol, problem) == []
            assert stats["nodes"] >= len(problem.sections)


def test_bentrok_kelompok_mahasiswa_terdeteksi():
    problem = load_problem()
    sch = {
        "S1": Assignment("D1", "R2", "Sen-08"),
        "S3": Assignment("D3", "R3", "Sen-08"),
    }
    assert any("mahasiswa" in e for e in validate_schedule(sch, problem))


def test_solver_tidak_menaruh_kelompok_sama_di_slot_sama():
    problem = load_problem()
    for sch in solve_all(problem, limit=10):
        for a in sch:
            for b in sch:
                if a < b and problem.sections[a].group == problem.sections[b].group:
                    assert sch[a].slot_id != sch[b].slot_id


def _game_demo(max_pick=3, kuota=1):
    from adversarial import jalankan_skenario
    from solver import solve_one
    import random
    problem = load_problem()
    jadwal = solve_one(problem, random.Random(0))
    return jalankan_skenario(jadwal, 1, 2, max_pick, kuota)


def test_alphabeta_nilai_sama_dengan_minimax_tapi_lebih_sedikit_node():
    _, h = _game_demo()
    assert h["nilai_sama"]
    assert h["node_alphabeta"] < h["node_minimax"]


def test_minimax_menjamin_hasil_minimal_nilai_optimal():
    _, h = _game_demo()
    v = h["nilai_optimal"]
    assert h["kombinasi"][("minimax", "greedy")]["nilai"] >= v
    assert h["kombinasi"][("greedy", "minimax")]["nilai"] <= v


def test_war_adversarial_aturan_pilih_kelas():
    game, _ = _game_demo(max_pick=2)
    state = game.initial()
    langkah, state = game.successors(state)[0]
    assert langkah not in game.legal(state, 0)                    
    assert langkah not in game.legal(state, 1)                    
    for sid in game.legal(state, 1):                              
        assert game.slot[sid] not in {game.slot[s] for s in state[1]}

def _krs(**kw):
    from krs import KRS, DATASET_KRS, muat_problem_krs
    from main import run_pipeline
    problem = muat_problem_krs()
    _, ranked = run_pipeline(DATASET_KRS)
    assert ranked, "dataset_krs.json harus punya jadwal kampus valid"
    return KRS(ranked[0].schedule, problem, **kw)

def _isi_penuh(krs, code):
    return {sid: krs.problem.rooms[krs.schedule[sid].room_id].capacity for sid in krs.by_course[code]}

def test_war_kuota_penuh_ditolak():
    problem = load_problem()
    sch = {"S1": Assignment("D1", "R2", "Sen-08")}
    kapasitas = problem.rooms["R2"].capacity
    assert any("penuh" in e for e in check_student_selection(["S1"], sch, problem, enrolled={"S1": kapasitas}))
    assert check_student_selection(["S1"], sch, problem, enrolled={"S1": kapasitas - 1}) == []

def test_krs_kelas_penuh_tidak_ditawarkan():
    base = _krs()
    code = base.wanted[0]
    sid = base.by_course[code][0]
    kapasitas = base.problem.rooms[base.schedule[sid].room_id].capacity
    krs = _krs(enrolled={sid: kapasitas})
    assert krs.sisa_kuota(sid) == 0
    status = {b["sid"]: b["status"] for b in krs.status_opsi({})[code]}
    assert status[sid] == "penuh"
    assert sid not in krs.opsi_tersisa({})[code]

def test_krs_batas_sks_menolak_semua_opsi():
    krs = _krs(max_sks=0)
    for baris in krs.status_opsi({}).values():
        assert all(b["status"] == "sks" for b in baris)

def test_krs_bentrok_slot_terdeteksi():
    krs = _krs()
    sids = [s for c in krs.wanted for s in krs.by_course[c]]
    for a in sids:
        for b in sids:
            if krs.kode(a) != krs.kode(b) and krs.slot(a) == krs.slot(b):
                status = {x["sid"]: x["status"] for x in krs.status_opsi({krs.kode(a): a})[krs.kode(b)]}
                assert status[b] == "bentrok"
                return
    print("   (dilewati)")

def test_krs_pilihan_lanjutan_tidak_tersedia():
    base = _krs()
    assert len(base.wanted) >= 2
    assert any(b["status"] == "bisa" for baris in base.status_opsi({}).values() for b in baris)
    code = base.wanted[0]
    krs = _krs(enrolled=_isi_penuh(base, code))
    for metode in ("basic", "fc"):
        assert krs.lengkapi({}, metode)[0] == []
    status = krs.status_opsi({})
    assert all(b["status"] == "penuh" for b in status[code])
    for c in krs.wanted[1:]:
        assert all(b["status"] == "buntu" for b in status[c])
    assert all(v == [] for v in krs.opsi_tersisa({}).values())

def test_krs_status_bisa_konsisten_dengan_lengkapi():
    krs = _krs()
    for code, baris in krs.status_opsi({}).items():
        for b in baris:
            ada = bool(krs.lengkapi({code: b["sid"]}, "fc", limit=1)[0])
            assert ada == (b["status"] == "bisa")

def test_krs_basic_dan_fc_menghasilkan_himpunan_jadwal_sama():
    krs = _krs()
    kunci = lambda sol: sorted(tuple(sorted(p.items())) for p in sol)
    assert kunci(krs.lengkapi({}, "basic")[0]) == kunci(krs.lengkapi({}, "fc")[0])

def _kampus():
    from kampus import buat_jadwal_tetap, buat_problem
    problem = buat_problem()
    jadwal = buat_jadwal_tetap(problem)
    assert jadwal, "CSP kampus harus menemukan jadwal tetap"
    return problem, jadwal

def test_kampus_jadwal_tetap_valid_dan_lengkap():
    problem, jadwal = _kampus()
    assert len(jadwal) == len(problem.sections) == 21
    assert validate_schedule(jadwal, problem) == []
    for sid, a in jadwal.items():
        sl = problem.slots[a.slot_id]
        assert sl.end - sl.start == problem.sections[sid].sks
        assert 7 <= sl.start and sl.end <= 17

def test_kampus_dosen_maks_4_kelas_per_hari():
    problem, jadwal = _kampus()
    hitung = {}
    for a in jadwal.values():
        kunci = (a.lecturer_id, problem.slots[a.slot_id].day)
        hitung[kunci] = hitung.get(kunci, 0) + 1
    assert max(hitung.values()) <= 4

def test_bentrok_jam_tumpang_tindih_terdeteksi():
    problem, _ = _kampus()
    sch = {"TG-A": Assignment("D3", "R101", "Sen-07-3"),
           "MD-A": Assignment("D3", "R102", "Sen-09-3")}
    assert any("dosen" in e for e in validate_schedule(sch, problem))

def test_kampus_ai_ranking_lengkapi_pilihan_mahasiswa():
    from krs import KRS
    problem, jadwal = _kampus()
    krs = KRS(jadwal, problem)
    picks = {"KKA": "KKA-A", "JK": "JK-B", "PW": "PW-C"}
    hasil = krs.rekomendasi(picks)
    assert hasil
    for r in hasil:
        p = r["pilihan"]
        assert set(p) == set(krs.wanted)
        assert all(p[c] == s for c, s in picks.items())
        for c1 in p:
            for c2 in p:
                if c1 < c2:
                    assert krs._cek(p[c1], {c2: p[c2]}) is None

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("OK  ", name)
