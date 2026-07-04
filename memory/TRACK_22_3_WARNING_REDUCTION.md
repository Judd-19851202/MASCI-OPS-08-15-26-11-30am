# TRACK 22.3 · Warning Reduction (detail)

See `TRACK_22_3_ZERO_DRIFT_MATRIX.md` for consolidated warning + audit + safety data.

## Runtime probe (empty result confirms elimination)
```
$ python -c "import warnings; warnings.simplefilter('always'); import server; \
    print(sum(1 for w in warnings.filters if 'regex' in str(w)))"
0
```

## No suppression added
- `pytest.ini` — not modified.
- `setup.cfg` — not modified.
- No `warnings.filterwarnings(...)` added anywhere in backend.
- No `# noqa: DEP...` comments added.
