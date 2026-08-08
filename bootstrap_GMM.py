# -*- coding: utf-8 -*-

import os

# 必须在导入 NumPy、SciPy 和 scikit-learn 之前限制底层线程数。
# 外层由 joblib 多进程并行，每个进程内部只使用 1 个 BLAS/OpenMP 线程。
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["BLIS_NUM_THREADS"] = "1"

from pathlib import Path
import re
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, NullFormatter
from sklearn.mixture import GaussianMixture
from joblib import Parallel, delayed, parallel_config


# =========================
# 1. 路径与样品选择
# =========================

# 下列参数均可通过环境变量从 Jupyter 单元格或终端覆盖，
# 因而不需要反复修改本 .py 文件。
DEFAULT_EXCEL_PATH = r"/media/tigerwp/data/Xiehongsen/Illustrate of Yangtze data/baserock python data.xlsx"
DEFAULT_OUT_DIR = r"/media/tigerwp/data/Xiehongsen/Illustrate of Yangtze data/bootstrap GMM/"
DEFAULT_SAMPLE_A = "Zr-Jinsha"
DEFAULT_SAMPLE_B = "Ar-Jinsha"
DEFAULT_FNAME = "Jinsha-GMM"

excel_path = Path(os.environ.get("GMM_EXCEL_PATH", DEFAULT_EXCEL_PATH)).expanduser()
out_dir = Path(os.environ.get("GMM_OUT_DIR", DEFAULT_OUT_DIR)).expanduser()

SAMPLE_A = os.environ.get("GMM_SAMPLE_A", DEFAULT_SAMPLE_A).strip() or DEFAULT_SAMPLE_A
SAMPLE_B = os.environ.get("GMM_SAMPLE_B", DEFAULT_SAMPLE_B).strip() or DEFAULT_SAMPLE_B
fname = os.environ.get("GMM_FNAME", DEFAULT_FNAME).strip() or DEFAULT_FNAME

out_dir.mkdir(parents=True, exist_ok=True)

EXPORT_FORMATS = ["png", "pdf", "svg"]
DPI = 1200


# =========================
# 2. GMM + bootstrap 峰值识别设置
# =========================

ANNOTATE_PEAKS = True

# 正式运行默认 5000 次；测试时可在终端临时覆盖：
# GMM_N_BOOTSTRAP=50 GMM_N_JOBS=2 python Supplemental_bootstrap_GMM_OpenBLAS.py
N_BOOTSTRAP = int(os.environ.get("GMM_N_BOOTSTRAP", "5000"))

K_MIN = 1
K_MAX = 10

# 不同 bootstrap 重复中，峰年龄相差不超过 10% 时归并为同一峰
MAX_RELATIVE_PEAK_DIFFERENCE = 0.10
MERGE_DISTANCE_LOG = np.log10(1.0 + MAX_RELATIVE_PEAK_DIFFERENCE)

# 仅保留在至少 60% bootstrap 重复中出现的稳定峰
MIN_SUPPORT = 0.6

MAX_BOOTSTRAP_N = None
GMM_N_INIT = int(os.environ.get("GMM_N_INIT", "10"))
RANDOM_SEED = 42

# 默认最多使用 8 个独立进程，避免占满服务器。
# 也可在终端通过 GMM_N_JOBS 临时指定，例如 GMM_N_JOBS=4。
DEFAULT_N_JOBS = max(1, min(8, os.cpu_count() or 1))
N_JOBS = int(os.environ.get("GMM_N_JOBS", str(DEFAULT_N_JOBS)))
if N_JOBS == 0:
    raise ValueError("GMM_N_JOBS 不能为 0。")

SHOW_PEAK_DOTS = True
LABEL_WITH_SUPPORT = False


# =========================
# 3. 基础工具函数
# =========================

def clean_name(x):
    return str(x).strip().replace("–", "-").replace("—", "-").replace("－", "-")


def safe_filename(name):
    return re.sub(r"[^\w\-.]+", "_", clean_name(name))


def format_peak_age(age):
    if age >= 100:
        return f"{age:.0f} Ma"
    elif age >= 10:
        return f"{age:.1f} Ma"
    return f"{age:.2f} Ma"


def get_sample_ages(df, sample_id):
    sample_id = clean_name(sample_id)
    sub = df[df["Sample_ID"] == sample_id]

    if sub.empty:
        available = "\n".join(sorted(df["Sample_ID"].unique()))
        raise ValueError(f"找不到样品：{sample_id}\n\n当前可用样品：\n{available}")

    ages = pd.to_numeric(sub["BestAge"], errors="coerce").dropna().to_numpy(dtype=float)
    ages = ages[np.isfinite(ages)]
    ages = ages[ages > 0]

    if len(ages) == 0:
        raise ValueError(f"{sample_id} 没有有效年龄数据。")

    return np.sort(ages)


def ecdf_xy(ages):
    x = np.sort(np.asarray(ages, dtype=float))
    y = np.arange(1, len(x) + 1) / len(x)

    x = np.r_[x[0], x]
    y = np.r_[0, y]

    return x, y


# =========================
# 4. GMM + BIC + bootstrap
# =========================

def fit_best_gmm_bic(log_values, k_min=1, k_max=10, n_init=10, random_state=None):
    x = np.asarray(log_values, dtype=float).reshape(-1, 1)
    n = len(x)

    if n < 3:
        return None

    unique_n = len(np.unique(np.round(log_values, 8)))
    k_max_eff = min(k_max, n - 1, unique_n)

    if k_max_eff < k_min:
        return None

    best_model = None
    best_bic = np.inf

    for k in range(k_min, k_max_eff + 1):
        try:
            model = GaussianMixture(
                n_components=k,
                covariance_type="full",
                n_init=n_init,
                random_state=random_state,
                reg_covar=1e-6
            )
            model.fit(x)
            bic = model.bic(x)

            if bic < best_bic:
                best_bic = bic
                best_model = model

        except Exception:
            continue

    return best_model


def run_one_bootstrap_gmm(
    b,
    log_ages,
    boot_n,
    seed,
    k_min,
    k_max,
    n_init
):
    """
    单次 bootstrap GMM。
    仅对观测年龄进行有放回抽样，不根据 BestAge_err 重新生成年龄。
    这个函数会被 joblib 并行调用。
    """
    rng = np.random.default_rng(seed)
    sample_log = rng.choice(log_ages, size=boot_n, replace=True)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = fit_best_gmm_bic(
            sample_log,
            k_min=k_min,
            k_max=k_max,
            n_init=n_init,
            random_state=int(rng.integers(0, 1_000_000))
        )

    if model is None:
        return []

    means = model.means_.ravel()
    weights = model.weights_.ravel()
    sigmas = np.sqrt(model.covariances_.reshape(-1))

    order = np.argsort(means)

    candidates = []
    for m, w, s in zip(means[order], weights[order], sigmas[order]):
        candidates.append({
            "boot_id": b,
            "log_age": float(m),
            "age": float(10 ** m),
            "weight": float(w),
            "sigma_log": float(s),
            "k_selected": int(model.n_components)
        })

    return candidates


def bootstrap_gmm_candidates(
    ages,
    sample_name,
    n_bootstrap=2000,
    k_min=1,
    k_max=10,
    max_bootstrap_n=None,
    n_init=10,
    random_seed=42,
    n_jobs=-1
):
    ages = np.asarray(ages, dtype=float)
    ages = ages[np.isfinite(ages)]
    ages = ages[ages > 0]

    log_ages = np.log10(ages)
    n_total = len(log_ages)

    if n_total < 5:
        return []

    boot_n = n_total if max_bootstrap_n is None else min(n_total, int(max_bootstrap_n))

    print(f"\nRunning parallel bootstrap GMM for {sample_name}:")
    print(f"  original n = {n_total}")
    print(f"  bootstrap n per iteration = {boot_n}")
    print(f"  n_bootstrap = {n_bootstrap}")
    print(f"  GMM_N_INIT = {n_init}")
    print(f"  n_jobs = {n_jobs}")

    rng = np.random.default_rng(random_seed)
    seeds = rng.integers(0, 2**32 - 1, size=n_bootstrap, dtype=np.uint32)

    # 使用 loky 多进程；每个 worker 内部只允许 1 个 BLAS/OpenMP 线程，
    # 避免多进程与底层多线程叠加造成过度并行。
    with parallel_config(
        backend="loky",
        n_jobs=n_jobs,
        inner_max_num_threads=1
    ):
        results = Parallel(
            verbose=10,
            batch_size="auto",
            pre_dispatch="2*n_jobs"
        )(
            delayed(run_one_bootstrap_gmm)(
                b=b,
                log_ages=log_ages,
                boot_n=boot_n,
                seed=int(seeds[b]),
                k_min=k_min,
                k_max=k_max,
                n_init=n_init
            )
            for b in range(n_bootstrap)
        )

    candidates = [cand for sublist in results for cand in sublist]

    print(f"  collected candidate components = {len(candidates)}")

    return candidates


def merge_bootstrap_peaks(
    candidates,
    n_bootstrap,
    merge_distance_log=np.log10(1.10),
    min_support=0.80
):
    if not candidates:
        return []

    candidates = sorted(candidates, key=lambda p: p["log_age"])
    clusters = []

    for cand in candidates:
        for cluster in clusters:
            if abs(cand["log_age"] - cluster["center_log"]) <= merge_distance_log:
                cluster["items"].append(cand)

                logs = np.array([i["log_age"] for i in cluster["items"]])
                weights = np.array([i["weight"] for i in cluster["items"]])

                cluster["center_log"] = np.average(logs, weights=weights) if weights.sum() > 0 else logs.mean()
                cluster["center_age"] = 10 ** cluster["center_log"]
                break
        else:
            clusters.append({
                "center_log": cand["log_age"],
                "center_age": cand["age"],
                "items": [cand]
            })

    all_peaks = []

    for cluster in clusters:
        items = cluster["items"]

        boot_ids = {i["boot_id"] for i in items}
        support = len(boot_ids) / n_bootstrap

        log_values = np.array([i["log_age"] for i in items])
        age_values = 10 ** log_values
        weights = np.array([i["weight"] for i in items])
        sigmas = np.array([i["sigma_log"] for i in items])
        ks = np.array([i["k_selected"] for i in items])

        center_log = np.average(log_values, weights=weights) if weights.sum() > 0 else log_values.mean()
        center_age = 10 ** center_log

        mean_weight = weights.mean()
        score = support * (0.5 + mean_weight)

        all_peaks.append({
            "age": center_age,
            "log_age": center_log,
            "support": support,
            "ci_low": np.percentile(age_values, 2.5),
            "ci_high": np.percentile(age_values, 97.5),
            "mean_weight": mean_weight,
            "median_weight": np.median(weights),
            "mean_sigma_log": sigmas.mean(),
            "median_k": np.median(ks),
            "score": score,
            "n_candidates": len(items),
            "n_boot_support": len(boot_ids)
        })

    # 仅保留达到支持率阈值的稳定峰，不强制输出峰的数量
    stable_peaks = [p for p in all_peaks if p["support"] >= min_support]
    return sorted(stable_peaks, key=lambda p: p["age"])


def find_stable_gmm_peaks(
    ages,
    sample_name,
    n_bootstrap=2000,
    k_min=1,
    k_max=10,
    merge_distance_log=np.log10(1.10),
    min_support=0.80,
    max_bootstrap_n=None,
    n_init=10,
    random_seed=42,
    n_jobs=-1
):
    candidates = bootstrap_gmm_candidates(
        ages=ages,
        sample_name=sample_name,
        n_bootstrap=n_bootstrap,
        k_min=k_min,
        k_max=k_max,
        max_bootstrap_n=max_bootstrap_n,
        n_init=n_init,
        random_seed=random_seed,
        n_jobs=n_jobs
    )

    return merge_bootstrap_peaks(
        candidates=candidates,
        n_bootstrap=n_bootstrap,
        merge_distance_log=merge_distance_log,
        min_support=min_support
    )


def add_ecdf_y_to_peaks(peaks, ages):
    ages_sorted = np.sort(np.asarray(ages, dtype=float))
    n = len(ages_sorted)

    for p in peaks:
        p["ecdf_y"] = np.searchsorted(ages_sorted, p["age"], side="right") / n

    return peaks


def save_peak_table(peaks_a, peaks_b, sample_a, sample_b, out_dir, fname):
    rows = []

    for sample_name, peaks in [(sample_a, peaks_a), (sample_b, peaks_b)]:
        for i, p in enumerate(peaks, start=1):
            rows.append({
                "Sample_ID": sample_name,
                "Peak_rank_by_age": i,
                "Peak_age_Ma": p["age"],
                "CI95_low_Ma": p["ci_low"],
                "CI95_high_Ma": p["ci_high"],
                "Bootstrap_support": p["support"],
                "Mean_component_weight": p["mean_weight"],
                "Median_component_weight": p["median_weight"],
                "Mean_sigma_log10_age": p["mean_sigma_log"],
                "Median_selected_K": p["median_k"],
                "Score": p["score"],
                "N_boot_support": p["n_boot_support"],
                "N_candidates_in_cluster": p["n_candidates"],
                "ECDF_y": p.get("ecdf_y", np.nan)
            })

    peak_df = pd.DataFrame(rows)

    csv_path = out_dir / f"{fname}_GMM_bootstrap_peaks.csv"
    xlsx_path = out_dir / f"{fname}_GMM_bootstrap_peaks.xlsx"

    peak_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    peak_df.to_excel(xlsx_path, index=False)

    print("\nPeak table saved:")
    print(f"  {csv_path}")
    print(f"  {xlsx_path}")

    return peak_df


# =========================
# 5. 绘图标注函数
# =========================

def annotate_gmm_peaks(
    ax,
    peaks,
    sample_name,
    color,
    label_y,
    label_rotation=90,
    show_dots=True,
    label_with_support=False
):
    print(f"\n{sample_name} stable GMM peaks:")

    if not peaks:
        print("  No stable peaks identified.")
        return

    for p in peaks:
        print(
            f"  peak age ≈ {p['age']:.2f} Ma; "
            f"95% range = {p['ci_low']:.2f}–{p['ci_high']:.2f} Ma; "
            f"support = {p['support']:.2%}; "
            f"mean weight = {p['mean_weight']:.3f}; "
            f"score = {p['score']:.4f}"
        )

        ax.axvline(
            p["age"],
            color=color,
            linestyle=(0, (2.5, 2.5)),
            linewidth=1.3,
            alpha=0.60,
            zorder=1
        )

        if show_dots:
            ax.plot(
                p["age"],
                p["ecdf_y"],
                marker="o",
                markersize=5.0,
                color=color,
                markeredgecolor="white",
                markeredgewidth=0.5,
                zorder=6
            )

        label = f"{format_peak_age(p['age'])}\n{p['support']:.0%}" if label_with_support else format_peak_age(p["age"])

        ax.text(
            p["age"],
            label_y,
            label,
            color=color,
            fontsize=7.5,
            ha="center",
            va="bottom",
            rotation=label_rotation,
            rotation_mode="anchor",
            zorder=10
        )


# =========================
# 6. 读取数据
# =========================

print("Runtime settings:")
print(f"  Excel path = {excel_path}")
print(f"  Output directory = {out_dir}")
print(f"  Sample A = {SAMPLE_A}")
print(f"  Sample B = {SAMPLE_B}")
print(f"  Output filename prefix = {fname}")
print(f"  Python process count = {N_JOBS}")
print("  BLAS/OpenMP threads per process = 1")
print(f"  Bootstrap replicates = {N_BOOTSTRAP}")
print(f"  GMM n_init = {GMM_N_INIT}")
print(f"  Stable peak threshold = {MIN_SUPPORT:.0%}")
print(f"  Peak merge tolerance = {MAX_RELATIVE_PEAK_DIFFERENCE:.0%}")
print("  Analytical age errors are not propagated.")

if not excel_path.is_file():
    raise FileNotFoundError(f"找不到 Excel 文件：{excel_path}")

df = pd.read_excel(excel_path)
df.columns = [str(c).strip() for c in df.columns]

# 本分析仅对观测年龄进行有放回抽样，不传播单颗粒分析误差
required_cols = ["Sample_ID", "BestAge"]
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Excel 缺少必要列：{col}")

df["Sample_ID"] = df["Sample_ID"].apply(clean_name)
df["BestAge"] = pd.to_numeric(df["BestAge"], errors="coerce")
df = df.dropna(subset=["Sample_ID", "BestAge"])
df = df[df["BestAge"] > 0].copy()

print("当前识别到的样品：")
for s in sorted(df["Sample_ID"].unique()):
    print("  ", s)

print("\nBootstrap setting: resample observed ages only; analytical age errors are not propagated.")
print(f"Stable peak threshold = {MIN_SUPPORT:.0%}")
print(f"Peak merge tolerance = {MAX_RELATIVE_PEAK_DIFFERENCE:.0%}")


# =========================
# 7. 取样品数据
# =========================

ages_a = get_sample_ages(df, SAMPLE_A)
ages_b = get_sample_ages(df, SAMPLE_B)

x1, y1 = ecdf_xy(ages_a)
x2, y2 = ecdf_xy(ages_b)


# =========================
# 8. GMM + bootstrap 识别稳定峰
# =========================

if ANNOTATE_PEAKS:
    peaks_a = find_stable_gmm_peaks(
        ages=ages_a,
        sample_name=SAMPLE_A,
        n_bootstrap=N_BOOTSTRAP,
        k_min=K_MIN,
        k_max=K_MAX,
        merge_distance_log=MERGE_DISTANCE_LOG,
        min_support=MIN_SUPPORT,
        max_bootstrap_n=MAX_BOOTSTRAP_N,
        n_init=GMM_N_INIT,
        random_seed=RANDOM_SEED,
        n_jobs=N_JOBS
    )

    peaks_b = find_stable_gmm_peaks(
        ages=ages_b,
        sample_name=SAMPLE_B,
        n_bootstrap=N_BOOTSTRAP,
        k_min=K_MIN,
        k_max=K_MAX,
        merge_distance_log=MERGE_DISTANCE_LOG,
        min_support=MIN_SUPPORT,
        max_bootstrap_n=MAX_BOOTSTRAP_N,
        n_init=GMM_N_INIT,
        random_seed=RANDOM_SEED + 1,
        n_jobs=N_JOBS
    )

    peaks_a = add_ecdf_y_to_peaks(peaks_a, ages_a)
    peaks_b = add_ecdf_y_to_peaks(peaks_b, ages_b)

    peak_df = save_peak_table(
        peaks_a=peaks_a,
        peaks_b=peaks_b,
        sample_a=SAMPLE_A,
        sample_b=SAMPLE_B,
        out_dir=out_dir,
        fname=fname
    )
else:
    peaks_a, peaks_b = [], []


# =========================
# 9. 绘图
# =========================

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [
    "Arial",
    "Liberation Sans",
    "DejaVu Sans"
]

plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42
plt.rcParams["svg.fonttype"] = "none"

fig, ax = plt.subplots(figsize=(7.0, 4.5))

color_zr_ecdf = "#8B1A1A"
color_ar_ecdf = "#1F4E79"

l1, = ax.step(
    x1, y1,
    where="post",
    color=color_zr_ecdf,
    linewidth=2.5,
    label=f"{SAMPLE_A} ECDF (n = {len(ages_a)})",
    zorder=4
)

l2, = ax.step(
    x2, y2,
    where="post",
    color=color_ar_ecdf,
    linewidth=2.5,
    label=f"{SAMPLE_B} ECDF (n = {len(ages_b)})",
    zorder=4
)


# =========================
# 10. 坐标轴与格式
# =========================

all_ages = np.concatenate([ages_a, ages_b])

xmin = all_ages.min() * 0.90
xmax = all_ages.max() * 1.10

ax.set_xscale("log")
ax.set_xlim(xmin, xmax)
ax.set_ylim(0, 1.12)

ax.set_xlabel("Age (Ma)", fontsize=11)
ax.set_ylabel("Cumulative proportion", fontsize=11)

candidate_ticks = [1, 3, 10, 30, 100, 300, 1000, 3000, 4500]
xticks = [t for t in candidate_ticks if xmin <= t <= xmax]
ax.set_xticks(xticks)

formatter = ScalarFormatter()
formatter.set_scientific(False)
ax.xaxis.set_major_formatter(formatter)
ax.xaxis.set_minor_formatter(NullFormatter())

ax.set_yticks(np.linspace(0, 1, 6))

ax.grid(
    True,
    which="major",
    axis="x",
    linestyle=":",
    linewidth=0.7,
    alpha=0.30
)

ax.grid(False, axis="y")
ax.tick_params(axis="both", which="both", direction="out", length=4, width=0.8)
ax.spines["top"].set_visible(True)


# =========================
# 11. 峰值标注
# =========================

if ANNOTATE_PEAKS:
    annotate_gmm_peaks(
        ax=ax,
        peaks=peaks_a,
        sample_name=SAMPLE_A,
        color=color_zr_ecdf,
        label_y=1.085,
        label_rotation=90,
        show_dots=SHOW_PEAK_DOTS,
        label_with_support=LABEL_WITH_SUPPORT
    )

    annotate_gmm_peaks(
        ax=ax,
        peaks=peaks_b,
        sample_name=SAMPLE_B,
        color=color_ar_ecdf,
        label_y=1.015,
        label_rotation=90,
        show_dots=SHOW_PEAK_DOTS,
        label_with_support=LABEL_WITH_SUPPORT
    )


# =========================
# 12. 图例与保存
# =========================

ax.legend(
    [l1, l2],
    [l1.get_label(), l2.get_label()],
    loc="lower right",
    fontsize=8.5,
    frameon=False,
    handlelength=2.8,
    borderpad=0.2,
    labelspacing=0.45
)

plt.tight_layout()

for ext in EXPORT_FORMATS:
    fig.savefig(out_dir / f"{fname}.{ext}", dpi=DPI, bbox_inches="tight")

plt.show()
