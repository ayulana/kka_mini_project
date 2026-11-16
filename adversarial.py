import random

from constraints import overlap

INF = float("inf")


def buat_preferensi(section_ids, seed):
    rng = random.Random(seed)
    return {sid: rng.randint(1, 10) for sid in sorted(section_ids)}


class WarGame:
    def __init__(self, schedule, pref_a, pref_b, seats=None, max_pick=3, problem=None):
        self.problem = problem  # kalau diisi, bentrok dicek dengan jam yang tumpang tindih
        self.ids = sorted(schedule)
        self.index = {sid: i for i, sid in enumerate(self.ids)}
        self.slot = {sid: schedule[sid].slot_id for sid in self.ids}
        self.pref = (pref_a, pref_b)
        self.seats0 = tuple((seats or {}).get(sid, 1) for sid in self.ids)
        self.max_pick = max_pick

    def initial(self):
        return ((), (), self.seats0, 0)

    def legal(self, state, player):
        picks, seats = state[player], state[2]
        if len(picks) >= self.max_pick:
            return []
        moves = [sid for sid in self.ids
                 if seats[self.index[sid]] > 0 and sid not in picks
                 and not any(self._bentrok(sid, p) for p in picks)]
        moves.sort(key=lambda s: (-self.pref[player][s], s))
        return moves

    def _bentrok(self, a, b):
        if self.problem is None:
            return self.slot[a] == self.slot[b]
        return overlap(self.problem, self.slot[a], self.slot[b])

    def apply(self, state, sid):
        player = state[3]
        picks = [state[0], state[1]]
        picks[player] = picks[player] + (sid,)
        seats = list(state[2])
        seats[self.index[sid]] -= 1
        return (picks[0], picks[1], tuple(seats), 1 - player)

    def successors(self, state):
        player = state[3]
        moves = self.legal(state, player)
        if moves:
            return [(m, self.apply(state, m)) for m in moves]
        if self.legal(state, 1 - player):
            return [(None, (state[0], state[1], state[2], 1 - player))]
        return []

    def utility(self, state):
        return (sum(self.pref[0][s] for s in state[0]) -
                sum(self.pref[1][s] for s in state[1]))


def minimax(game, state, counter):
    counter[0] += 1
    succ = game.successors(state)
    if not succ:
        return game.utility(state), None
    maximizing = state[3] == 0
    best_val, best_move = (-INF if maximizing else INF), None
    for move, nxt in succ:
        v, _ = minimax(game, nxt, counter)
        if (maximizing and v > best_val) or (not maximizing and v < best_val):
            best_val, best_move = v, move
    return best_val, best_move


def alphabeta(game, state, counter, alpha=-INF, beta=INF):
    counter[0] += 1
    succ = game.successors(state)
    if not succ:
        return game.utility(state), None
    maximizing = state[3] == 0
    best_val, best_move = (-INF if maximizing else INF), None
    for move, nxt in succ:
        v, _ = alphabeta(game, nxt, counter, alpha, beta)
        if maximizing:
            if v > best_val:
                best_val, best_move = v, move
            alpha = max(alpha, best_val)
        else:
            if v < best_val:
                best_val, best_move = v, move
            beta = min(beta, best_val)
        if alpha >= beta:
            break
    return best_val, best_move


def pilih_langkah(game, state, strategi):
    succ = game.successors(state)
    if strategi == "greedy":
        return succ[0] 
    _, best = alphabeta(game, state, [0])
    for move, nxt in succ:
        if move == best:
            return move, nxt
    return succ[0]


def simulasi(game, strategi_a, strategi_b):
    state = game.initial()
    strategi = (strategi_a, strategi_b)
    while game.successors(state):
        _, state = pilih_langkah(game, state, strategi[state[3]])
    return {"kelas_a": list(state[0]), "kelas_b": list(state[1]), "nilai": game.utility(state)}


def bandingkan(game):
    c_mm, c_ab = [0], [0]
    v_mm, _ = minimax(game, game.initial(), c_mm)
    v_ab, langkah = alphabeta(game, game.initial(), c_ab)
    kombinasi = {}
    for sa in ("greedy", "minimax"):
        for sb in ("greedy", "minimax"):
            kombinasi[(sa, sb)] = simulasi(game, sa, sb)
    return {
        "nilai_optimal": v_ab,
        "nilai_sama": v_mm == v_ab,
        "node_minimax": c_mm[0],
        "node_alphabeta": c_ab[0],
        "langkah_pertama_a": langkah,
        "kombinasi": kombinasi,
    }


def jalankan_skenario(schedule, seed_a=1, seed_b=2, max_pick=3, kuota=1, problem=None):
    ids = list(schedule)
    game = WarGame(schedule, buat_preferensi(ids, seed_a), buat_preferensi(ids, seed_b),
                   seats={sid: kuota for sid in ids}, max_pick=max_pick, problem=problem)
    return game, bandingkan(game)
