"""Limit native thread pools to the container's real CPU quota.

On Apify the container sees all host cores (os.cpu_count()) but only gets a fraction of a CPU
(1 CPU per 4 GB of memory). ONNX Runtime / BLAS then spawn dozens of threads and thrash.
Must be imported before onnxruntime, numpy, pymupdf or rapidocr.
"""
import math
import os


def cpu_quota() -> int:
    try:
        quota, period = open("/sys/fs/cgroup/cpu.max").read().split()[:2]
        if quota != "max":
            return max(1, math.ceil(int(quota) / int(period)))
    except Exception:  # noqa: BLE001
        pass
    try:
        q = int(open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us").read())
        p = int(open("/sys/fs/cgroup/cpu/cpu.cfs_period_us").read())
        if q > 0:
            return max(1, math.ceil(q / p))
    except Exception:  # noqa: BLE001
        pass
    mem_mb = int(os.environ.get("ACTOR_MEMORY_MBYTES", "0") or 0)
    if mem_mb:
        return max(1, mem_mb // 4096)
    return os.cpu_count() or 1


N_THREADS = cpu_quota()
for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(var, str(N_THREADS))

import onnxruntime as _ort  # noqa: E402

_Orig = _ort.SessionOptions


class _LimitedSessionOptions(_Orig):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.intra_op_num_threads = N_THREADS
        self.inter_op_num_threads = 1


_ort.SessionOptions = _LimitedSessionOptions
_OrigSession = _ort.InferenceSession


class _LimitedSession(_OrigSession):
    def __init__(self, path_or_bytes, sess_options=None, *a, **k):
        super().__init__(path_or_bytes, sess_options or _LimitedSessionOptions(), *a, **k)


_ort.InferenceSession = _LimitedSession
