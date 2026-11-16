import random
import time

from constraints import build_domain, is_consistent


def solve_with_stats(problem, use_mrv=True, use_fc=True, rng=None, max_nodes=200000):
    rng = rng or random.Random()
    t0 = time.perf_counter()
    stats = {"nodes": 0, "backtracks": 0, "checks": 0, "ms": 0.0, "aborted": False}

    domains = {sid: build_domain(sec, problem) for sid, sec in problem.sections.items()}
    if any(not d for d in domains.values()):
        stats["ms"] = (time.perf_counter() - t0) * 1000
        return None, stats
    for d in domains.values():
        rng.shuffle(d)

    partial = {}

    def backtrack(doms):
        if not doms:
            return dict(partial)
        stats["nodes"] += 1
        if stats["nodes"] > max_nodes:
            stats["aborted"] = True
            return None

        sid = min(doms, key=lambda s: len(doms[s])) if use_mrv else next(iter(doms))

        for value in doms[sid]:
            if stats["aborted"]:
                return None
            if not use_fc: 
                stats["checks"] += 1
                if not is_consistent(sid, value, partial, problem):
                    continue
            partial[sid] = value

            rest = {k: v for k, v in doms.items() if k != sid}
            ok = True
            if use_fc: 
                filtered_rest = {}
                for other, d in rest.items():
                    kept = []
                    for v in d:
                        stats["checks"] += 1
                        if is_consistent(other, v, partial, problem):
                            kept.append(v)
                    if not kept:
                        ok = False
                        break
                    filtered_rest[other] = kept
                rest = filtered_rest

            if ok:
                result = backtrack(rest)
                if result is not None:
                    return result
            del partial[sid]
            stats["backtracks"] += 1
        return None

    solution = backtrack(domains)
    stats["ms"] = (time.perf_counter() - t0) * 1000
    return solution, stats


def solve_one(problem, rng=None, max_nodes=20000):
    solution, _ = solve_with_stats(problem, True, True, rng, max_nodes)
    return solution


def solve_all(problem, limit=30, attempts=300, seed=0):
    rng = random.Random(seed)
    found = {}
    misses = 0
    for _ in range(attempts):
        if len(found) >= limit:
            break
        sol = solve_one(problem, rng)
        if sol is None:
            misses += 1
            if misses >= 5 and not found:
                return []
            continue
        found[tuple(sorted(sol.items()))] = sol
    return list(found.values())
