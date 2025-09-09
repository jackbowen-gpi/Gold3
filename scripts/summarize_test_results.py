import glob
import os

out_dir = os.path.join(os.path.dirname(__file__), "..", "test_results")
out_dir = os.path.abspath(out_dir)
pattern = os.path.join(out_dir, "out_*_tests*.txt")
files = sorted(glob.glob(pattern))
summary = []
for f in files:
    name = os.path.basename(f)
    with open(f, "r", encoding="utf-8", errors="ignore") as fh:
        txt = fh.read()
    status = "OK"
    if "FAILED" in txt or "Traceback" in txt or "ERROR" in txt:
        status = "FAIL"
    if "NO TESTS RAN" in txt or "Found 0 test(s)." in txt:
        status = "NO TESTS"
    fallback = ".fallback" in name or ".fallback.txt" in f
    summary.append((name, status, fallback))
with open(
    os.path.join(out_dir, "test_results_summary.txt"), "w", encoding="utf-8"
) as sf:
    for n, s, f in summary:
        sf.write(f"{n}\t{s}\tfallback={f}\n")
print("Wrote", os.path.join(out_dir, "test_results_summary.txt"))
