"""Subprocess side of IsolatedVerifier.

The parent sends this file's source to `python -I -c`, so the child has no
__file__ pointing back into the repo. It runs in a temp dir holding only the
declared source files.

Protocol: stdin carries {"modules": [...], "cases": [{"function", "args", "time_limit"?}]}
with args in the tagged encoding below. Expected values are never sent. stdout
carries one JSON list with, per case, {"result"} or {"raised"}, plus "elapsed"
and "args_after". Everything the submission prints goes to stderr.
"""
import importlib
import json
import sys
import time


def encode(v):
    """Tag every value with its exact type, so subclasses and fakes can't pass as the real thing."""
    t = type(v)
    if v is None:
        return {"t": "NoneType"}
    if t in (bool, int, float, str):
        return {"t": t.__name__, "v": v}
    if t in (list, tuple):
        return {"t": t.__name__, "v": [encode(x) for x in v]}
    if t in (set, frozenset):
        return {"t": t.__name__, "v": sorted((encode(x) for x in v), key=json.dumps)}
    if t is dict:
        return {"t": "dict", "v": sorted(([encode(k), encode(x)] for k, x in v.items()), key=json.dumps)}
    return {"t": f"{t.__module__}.{t.__qualname__}", "unsupported": True}


def decode(e):
    t, v = e["t"], e.get("v")
    if t == "NoneType":
        return None
    if t in ("bool", "int", "float", "str"):
        return v
    if t in ("list", "tuple", "set", "frozenset"):
        return {"list": list, "tuple": tuple, "set": set, "frozenset": frozenset}[t](decode(x) for x in v)
    if t == "dict":
        return {decode(k): decode(x) for k, x in v}
    raise ValueError(f"cannot decode {t}")


def main():
    # Read all input and bind what we need before any submitted code runs.
    request = json.loads(sys.stdin.read())
    out, clock, dumps = sys.stdout, time.perf_counter, json.dumps
    sys.stdout = sys.stderr
    sys.path.insert(0, ".")

    funcs, results = {}, []
    try:
        for name in request["modules"]:
            mod = importlib.import_module(name)
            for attr, value in vars(mod).items():
                funcs.setdefault(attr, value)
    except BaseException as exc:
        out.write(dumps({"import_error": f"{type(exc).__name__}: {exc}"}))
        return

    for case in request["cases"]:
        args = [decode(a) for a in case["args"]]
        row = {}
        start = clock()
        try:
            row["result"] = encode(funcs[case["function"]](*args))
        except BaseException as exc:
            kind = type(exc)
            row["raised"] = kind.__qualname__ if kind.__module__ == "builtins" else f"{kind.__module__}.{kind.__qualname__}"
        row["elapsed"] = clock() - start
        row["args_after"] = [encode(a) for a in args]
        results.append(row)
    out.write(dumps(results))


main()
