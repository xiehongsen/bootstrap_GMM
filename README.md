# Bootstrap Gaussian Mixture Modeling of Geochronologic Age Distributions

This repository contains the Python workflow used for bootstrap Gaussian mixture modeling (GMM) of geochronologic age distributions.

The workflow was developed to identify and evaluate major age components in compiled geochronologic datasets, including zircon U–Pb and Ar-system ages. Gaussian mixture models are fitted to log-transformed age distributions, alternative model complexities are evaluated using the Bayesian information criterion (BIC), and bootstrap resampling is used to evaluate the recurrence and stability of the inferred age components.

The workflow consists of three files:

```text
bootstrap_GMM.py
bootstrap_GMM.ipynb
gmm_openblas_environment(1).yml
```

`bootstrap_GMM.py` contains the core numerical analysis, `bootstrap_GMM.ipynb` provides a configurable Jupyter interface for running the analysis, and `gmm_openblas_environment(1).yml` defines the Conda environment required for reproducibility.

---

## 1. Repository files

### `bootstrap_GMM.py`

Core Python script for bootstrap Gaussian mixture modeling.

The script performs the following operations:

1. Reads geochronologic age data from an Excel workbook.
2. Selects two datasets according to their `Sample_ID` values.
3. Transforms positive ages to log10(age).
4. Fits Gaussian mixture models with different numbers of components.
5. Selects the preferred number of components using the Bayesian information criterion (BIC).
6. Generates bootstrap resamples of the observed ages.
7. Fits a new BIC-selected GMM to each bootstrap replicate.
8. Groups recurrent Gaussian components into stable age peaks.
9. Calculates bootstrap support and age ranges for the stable components.
10. Exports numerical peak tables.
11. Plots empirical cumulative distribution functions (ECDFs) and identified stable GMM peaks.
12. Saves figures in PNG, PDF, and SVG formats.

The script can be run directly from the command line or launched through `bootstrap_GMM.ipynb`.

---

### `bootstrap_GMM.ipynb`

Jupyter Notebook used as the user interface for the analysis.

The notebook allows the user to specify:

- the path to `bootstrap_GMM.py`;
- the input Excel workbook;
- the output directory;
- the two `Sample_ID` values;
- the output filename prefix;
- the number of bootstrap replicates;
- the number of parallel workers;
- the number of GMM initializations.

These settings are passed to `bootstrap_GMM.py` through environment variables, allowing different datasets to be analyzed without modifying the core Python script.

---

### `gmm_openblas_environment(1).yml`

Conda environment file containing the software dependencies required to reproduce the analysis.

The environment uses:

```text
Python 3.11
NumPy
SciPy
pandas
Matplotlib
scikit-learn
joblib
openpyxl
OpenBLAS
```

OpenBLAS is used as the numerical linear-algebra backend.

---

## 2. Installation

A dedicated Conda environment is recommended.

Open a terminal in the directory containing the three repository files.

Because the environment filename contains parentheses, the filename should be placed inside quotation marks when used in shell commands.

Create the environment using:

```bash
conda env create -f "gmm_openblas_environment(1).yml"
```

Activate the environment:

```bash
conda activate gmm_openblas
```

Check the numerical backend:

```bash
conda list | grep -E "libblas|openblas|mkl|intel-openmp"
```

The environment should use OpenBLAS rather than MKL as the primary BLAS implementation.

---

## 3. Verify the Python environment

Check that the required packages are available:

```bash
python -c "import numpy, pandas, sklearn, joblib, matplotlib, openpyxl; print('All packages OK')"
```

Check that the Gaussian mixture model implementation can be imported:

```bash
python -c "from sklearn.mixture import GaussianMixture; print('GaussianMixture OK')"
```

---

## 4. Jupyter setup

Install Jupyter kernel support if necessary:

```bash
conda install -c conda-forge ipykernel -y
```

Register the environment as a Jupyter kernel:

```bash
python -m ipykernel install \
  --user \
  --name gmm_openblas \
  --display-name "Python (gmm_openblas)"
```

If JupyterLab or Jupyter Notebook is not installed, install them using:

```bash
conda install -c conda-forge jupyterlab notebook ipykernel -y
```

Check the available kernels:

```bash
jupyter kernelspec list
```

Launch JupyterLab:

```bash
jupyter lab
```

or the classic Jupyter Notebook interface:

```bash
jupyter notebook
```

Open:

```text
bootstrap_GMM.ipynb
```

and select:

```text
Python (gmm_openblas)
```

as the active kernel.

---

## 5. Verify the active environment in Jupyter

The Python interpreter used by the notebook can be checked using:

```python
import sys

print(sys.executable)
```

The reported executable should belong to the `gmm_openblas` Conda environment.

The principal package versions can be checked using:

```python
import numpy as np
import pandas as pd
import sklearn
import joblib
import matplotlib
import openpyxl

from sklearn.mixture import GaussianMixture

print("NumPy:", np.__version__)
print("pandas:", pd.__version__)
print("scikit-learn:", sklearn.__version__)
print("joblib:", joblib.__version__)
print("Matplotlib:", matplotlib.__version__)
print("openpyxl:", openpyxl.__version__)

print("All required dependencies are available.")
```

---

## 6. Input data requirements

The input data must be provided as an Excel workbook.

The current version of `bootstrap_GMM.py` requires at least the following columns:

```text
Sample_ID
BestAge
```

### `Sample_ID`

Identifier used to distinguish different geochronologic datasets.

Example:

```text
Zr-Jinsha
Ar-Jinsha
```

### `BestAge`

Numerical age used in the GMM analysis.

Only finite positive ages are retained.

Rows containing missing or invalid `BestAge` values are excluded automatically.

Analytical age uncertainties are not propagated in the current bootstrap procedure.

The bootstrap analysis resamples the observed ages directly with replacement.

---

## 7. Configure `bootstrap_GMM.ipynb`

For normal use, only the user-configuration section of `bootstrap_GMM.ipynb` needs to be modified.

The core file `bootstrap_GMM.py` does not normally need to be edited.

Import the required modules:

```python
import os
import sys
import subprocess

from pathlib import Path
```

---

## 8. Set the path to `bootstrap_GMM.py`

If `bootstrap_GMM.py` and `bootstrap_GMM.ipynb` are stored in the same directory, use:

```python
script_path = Path("bootstrap_GMM.py")
```

This relative path is recommended for the GitHub version because it does not depend on the directory structure of a specific computer.

Absolute paths can also be used for local analyses.

For example:

```python
script_path = Path(
    "/path/to/bootstrap_GMM.py"
)
```

---

## 9. Set the input Excel file

Specify the path to the Excel workbook containing the geochronologic age data.

For example:

```python
excel_path = Path(
    "/path/to/baserock_data.xlsx"
)
```

The Excel workbook is not required to be stored in the same directory as the GitHub repository.

If the input data are stored in a subdirectory named `data`, a relative path can be used:

```python
excel_path = Path(
    "data/baserock_data.xlsx"
)
```

---

## 10. Set the output directory

Specify the directory in which numerical and graphical outputs will be saved.

For example:

```python
output_dir = Path(
    "results"
)
```

or:

```python
output_dir = Path(
    "results/Lower_Yangtze"
)
```

The directory is created automatically if it does not already exist.

---

## 11. Select the two datasets

Specify the two `Sample_ID` values that will be analyzed.

For example:

```python
sample_a = "Zr-Lower Yangtze"
sample_b = "Ar-Lower Yangtze"
```

or:

```python
sample_a = "Zr-Jinsha"
sample_b = "Ar-Jinsha"
```

The strings must exactly match values in the `Sample_ID` column of the input Excel workbook.

The two identifiers must not be identical.

---

## 12. Set the output filename prefix

Specify the prefix used for all output files:

```python
output_name = "Lower Yangtze-GMM"
```

Do not include a file extension.

For example, do not use:

```text
Lower Yangtze-GMM.png
```

because extensions are added automatically by `bootstrap_GMM.py`.

---

## 13. Set computational parameters

The three principal computational parameters exposed by `bootstrap_GMM.ipynb` are:

```python
n_bootstrap = 5000
n_jobs = 64
gmm_n_init = 10
```

### `n_bootstrap`

Number of bootstrap replicates.

```python
n_bootstrap = 5000
```

Each bootstrap replicate is generated by resampling the observed ages with replacement.

A larger number of replicates provides a more stable estimate of peak recurrence but requires more computational time.

For quick testing, a smaller value can be used, for example:

```python
n_bootstrap = 50
```

For the final analysis, the current workflow uses:

```python
n_bootstrap = 5000
```

---

### `n_jobs`

Number of parallel worker processes:

```python
n_jobs = 64
```

This should be adjusted according to the CPU resources available on the workstation or computing server.

For example:

```python
n_jobs = 8
```

or:

```python
n_jobs = 16
```

Users should not request more workers than the number of CPU cores allocated to the analysis.

---

### `gmm_n_init`

Number of independent initializations for each Gaussian mixture model:

```python
gmm_n_init = 10
```

Gaussian mixture fitting involves numerical optimization and can converge to different local solutions depending on initialization.

Multiple initializations reduce sensitivity to the starting parameters.

For each candidate GMM, `scikit-learn` retains the best solution among the independent initializations.

---

## 14. Example notebook configuration

A complete configuration block can be written as:

```python
import os
import sys
import subprocess

from pathlib import Path


# ============================================================
# User configuration
# ============================================================

# Core bootstrap GMM Python script.
script_path = Path("bootstrap_GMM.py")

# Input Excel workbook.
excel_path = Path(
    "/path/to/baserock_data.xlsx"
)

# Output directory.
output_dir = Path(
    "results/Lower_Yangtze"
)

# Sample_ID values.
sample_a = "Zr-Lower Yangtze"
sample_b = "Ar-Lower Yangtze"

# Output filename prefix.
output_name = "Lower Yangtze-GMM"

# Computational parameters.
n_bootstrap = 5000
n_jobs = 64
gmm_n_init = 10
```

---

## 15. Validate files and parameters

Before the main calculation starts, the notebook should check the specified files and settings.

```python
if not script_path.is_file():
    raise FileNotFoundError(
        f"Python script not found:\n{script_path}"
    )

if not excel_path.is_file():
    raise FileNotFoundError(
        f"Input Excel file not found:\n{excel_path}"
    )

if not sample_a.strip():
    raise ValueError(
        "sample_a cannot be empty."
    )

if not sample_b.strip():
    raise ValueError(
        "sample_b cannot be empty."
    )

if sample_a.strip() == sample_b.strip():
    raise ValueError(
        "sample_a and sample_b must be different."
    )

if n_bootstrap < 1:
    raise ValueError(
        "n_bootstrap must be greater than 0."
    )

if n_jobs == 0:
    raise ValueError(
        "n_jobs cannot be 0."
    )

if gmm_n_init < 1:
    raise ValueError(
        "gmm_n_init must be greater than 0."
    )

output_dir.mkdir(
    parents=True,
    exist_ok=True
)

print("Configuration validation completed successfully.")
```

---

## 16. Pass settings to `bootstrap_GMM.py`

The notebook passes its settings to `bootstrap_GMM.py` through environment variables.

Start by copying the current environment:

```python
env = os.environ.copy()
```

Pass the input, output, and sample settings:

```python
env["GMM_EXCEL_PATH"] = str(excel_path)
env["GMM_OUT_DIR"] = str(output_dir)

env["GMM_SAMPLE_A"] = sample_a.strip()
env["GMM_SAMPLE_B"] = sample_b.strip()

env["GMM_FNAME"] = output_name.strip()
```

Pass the bootstrap and GMM settings:

```python
env["GMM_N_BOOTSTRAP"] = str(n_bootstrap)
env["GMM_N_JOBS"] = str(n_jobs)
env["GMM_N_INIT"] = str(gmm_n_init)
```

The environment variables recognized by `bootstrap_GMM.py` are therefore:

| Environment variable | Description |
|---|---|
| `GMM_EXCEL_PATH` | Input Excel workbook |
| `GMM_OUT_DIR` | Output directory |
| `GMM_SAMPLE_A` | First `Sample_ID` |
| `GMM_SAMPLE_B` | Second `Sample_ID` |
| `GMM_FNAME` | Output filename prefix |
| `GMM_N_BOOTSTRAP` | Number of bootstrap replicates |
| `GMM_N_JOBS` | Number of parallel workers |
| `GMM_N_INIT` | Number of GMM initializations |

---

## 17. Control nested parallelism

Bootstrap replicates are parallelized at the Python/joblib level.

Numerical libraries such as OpenBLAS, MKL, NumExpr, BLIS, and OpenMP may otherwise create additional threads inside each parallel worker.

This can produce nested parallelism.

For example:

```text
64 Python workers × 8 BLAS threads
= 512 computational threads
```

Such oversubscription can substantially reduce computational efficiency and increase memory consumption.

The workflow therefore restricts each low-level numerical backend to one thread:

```python
env["OMP_NUM_THREADS"] = "1"
env["MKL_NUM_THREADS"] = "1"
env["OPENBLAS_NUM_THREADS"] = "1"
env["NUMEXPR_NUM_THREADS"] = "1"
env["VECLIB_MAXIMUM_THREADS"] = "1"
env["BLIS_NUM_THREADS"] = "1"
```

Parallelism is controlled primarily through:

```python
n_jobs
```

at the Python/joblib level.

The same thread restrictions are also defined at the beginning of `bootstrap_GMM.py` before NumPy and scikit-learn are imported.

---

## 18. Non-interactive figure generation

For execution on remote servers or headless Linux systems, use a non-interactive Matplotlib backend:

```python
env["MPLBACKEND"] = "Agg"
```

This prevents graphical windows from interrupting execution while still allowing figures to be saved.

---

## 19. Display the current configuration

Before starting the calculation, it is useful to print the settings used for the current run:

```python
print("Bootstrap GMM analysis configuration")
print("-" * 70)

print("Python executable :", sys.executable)
print("Analysis script   :", script_path)
print("Input Excel file  :", excel_path)
print("Output directory  :", output_dir)

print("Sample A          :", sample_a)
print("Sample B          :", sample_b)
print("Output prefix     :", output_name)

print("Bootstrap runs    :", n_bootstrap)
print("Parallel workers  :", n_jobs)
print("GMM n_init        :", gmm_n_init)

print("-" * 70)
```

---

## 20. Run `bootstrap_GMM.py`

Execute the complete analysis using:

```python
result = subprocess.run(
    [sys.executable, str(script_path)],
    env=env,
    check=False
)
```

Using:

```python
sys.executable
```

ensures that `bootstrap_GMM.py` is executed with the same Python interpreter and Conda environment as `bootstrap_GMM.ipynb`.

---

## 21. Check the execution status

After the Python script finishes, inspect its return code:

```python
print("-" * 70)
print("Process return code:", result.returncode)

if result.returncode == 0:
    print("Bootstrap GMM analysis completed successfully.")
    print("Results were saved to:")
    print(output_dir)

else:
    print("Bootstrap GMM analysis failed.")
    print(
        "Please inspect the error messages printed above "
        "for diagnostic information."
    )
```

A return code of:

```text
0
```

normally indicates successful execution.

---

# 22. Gaussian mixture modeling

Before model fitting, the observed positive ages are transformed using:

```text
log10(age)
```

The GMM is therefore fitted in log-age space rather than directly in linear age space.

For each bootstrap replicate, candidate Gaussian mixture models containing different numbers of components are fitted.

The current implementation evaluates:

```text
K = 1–10
```

Gaussian components.

For each value of `K`, the model is fitted using `GaussianMixture` from `scikit-learn`.

The covariance type is:

```text
full
```

and a small covariance regularization term is included to improve numerical stability.

---

# 23. BIC model selection

For each bootstrap replicate, models containing different numbers of Gaussian components are compared using the Bayesian information criterion (BIC).

The model with the lowest BIC is retained.

BIC provides a balance between:

- goodness of fit; and
- model complexity.

Thus, increasing the number of Gaussian components is only favored when the improvement in fit is sufficient to offset the additional model complexity.

The number of Gaussian components is therefore not fixed in advance for every bootstrap replicate.

---

# 24. Bootstrap resampling

The workflow uses nonparametric bootstrap resampling of the observed ages.

For each bootstrap replicate:

1. the original positive ages are transformed to log10(age);
2. observations are sampled with replacement;
3. the bootstrap sample size is equal to the original dataset size unless otherwise specified;
4. candidate GMMs are fitted;
5. BIC selects the preferred GMM;
6. the component means, weights, and variances are recorded.

The current workflow resamples the observed ages only.

Analytical age uncertainties are **not** propagated by generating new ages from individual age-error distributions.

---

# 25. Reproducible random sampling

The default random seed in `bootstrap_GMM.py` is:

```text
42
```

Independent random seeds are generated for individual bootstrap replicates.

The second analyzed dataset uses an offset seed relative to the first dataset so that the two bootstrap sequences are independent.

---

# 26. Parallel bootstrap computation

Individual bootstrap replicates are independent and can therefore be calculated in parallel.

`bootstrap_GMM.py` uses:

```text
joblib
```

with the:

```text
loky
```

multiprocessing backend.

The number of worker processes is controlled by:

```text
GMM_N_JOBS
```

or, from the notebook:

```python
n_jobs
```

Within each worker, low-level BLAS/OpenMP threading is restricted to one thread.

This allows computational resources to be managed at the process level and minimizes nested parallelism.

---

# 27. Stable peak identification

Every bootstrap GMM produces one or more candidate Gaussian components.

Components from different bootstrap replicates must therefore be grouped before their recurrence can be evaluated.

The current implementation groups components when their log-age positions differ by no more than the equivalent of a:

```text
10%
```

relative age difference.

The default setting is:

```python
MAX_RELATIVE_PEAK_DIFFERENCE = 0.10
```

This corresponds to:

```python
MERGE_DISTANCE_LOG = np.log10(1.0 + 0.10)
```

Components falling within this tolerance are assigned to the same bootstrap peak cluster.

---

# 28. Bootstrap support

For each peak cluster, bootstrap support is calculated as:

```text
number of bootstrap replicates containing the peak
--------------------------------------------------
total number of bootstrap replicates
```

The current analysis retains only peaks appearing in at least:

```text
60%
```

of bootstrap replicates.

The default setting is:

```python
MIN_SUPPORT = 0.6
```

The number of stable peaks is therefore determined by bootstrap recurrence rather than being forced to a predetermined number.

---

# 29. Stable peak age

For each cluster of recurrent components, the representative peak position is calculated in log-age space using component weights.

The resulting log-age center is then transformed back to age in Ma.

The workflow additionally reports the distribution of component ages across bootstrap replicates.

---

# 30. Bootstrap age range

For each stable peak, the script calculates:

```text
2.5th percentile
97.5th percentile
```

of the component ages assigned to that peak cluster.

These values are reported as the bootstrap 95% age range:

```text
CI95_low_Ma
CI95_high_Ma
```

This interval describes variation in the fitted component position among bootstrap resamples.

It should not be interpreted as propagation of individual analytical age uncertainties, because those uncertainties are not resampled in the current workflow.

---

# 31. Component weight

The relative abundance of a Gaussian component within an individual mixture model is represented by its model weight.

For each stable bootstrap peak, the script reports:

```text
Mean_component_weight
Median_component_weight
```

across all candidate components assigned to that peak cluster.

---

# 32. Additional peak statistics

The output peak table includes the following fields:

| Column | Description |
|---|---|
| `Sample_ID` | Dataset identifier |
| `Peak_rank_by_age` | Peak order from youngest to oldest |
| `Peak_age_Ma` | Representative stable peak age |
| `CI95_low_Ma` | 2.5th percentile of bootstrap component ages |
| `CI95_high_Ma` | 97.5th percentile of bootstrap component ages |
| `Bootstrap_support` | Fraction of bootstrap replicates containing the peak |
| `Mean_component_weight` | Mean GMM component weight |
| `Median_component_weight` | Median GMM component weight |
| `Mean_sigma_log10_age` | Mean Gaussian width in log10(age) space |
| `Median_selected_K` | Median number of GMM components selected by BIC |
| `Score` | Internal peak summary score |
| `N_boot_support` | Number of bootstrap replicates containing the peak |
| `N_candidates_in_cluster` | Number of component candidates grouped into the peak |
| `ECDF_y` | ECDF position corresponding to the peak age |

---

# 33. Numerical outputs

For an output prefix defined as:

```python
output_name = "Lower Yangtze-GMM"
```

the stable peak tables are written as:

```text
Lower Yangtze-GMM_GMM_bootstrap_peaks.csv
Lower Yangtze-GMM_GMM_bootstrap_peaks.xlsx
```

The CSV file is written using UTF-8 encoding.

---

# 34. ECDF visualization

The script also calculates empirical cumulative distribution functions for the two selected age datasets.

The ECDF is plotted against age using a logarithmic x-axis.

Stable GMM peaks are superimposed on the ECDF plot using:

- vertical dashed lines;
- point markers at the corresponding ECDF positions;
- age labels.

This allows the modeled stable age components to be visually compared with the observed cumulative age distributions.

---

# 35. Figure output

Figures are exported in three formats:

```text
PNG
PDF
SVG
```

The corresponding settings in `bootstrap_GMM.py` are:

```python
EXPORT_FORMATS = ["png", "pdf", "svg"]
```

Raster output uses:

```text
1200 dpi
```

through:

```python
DPI = 1200
```

PDF and SVG outputs are also generated to facilitate publication-quality figure editing.

---

# 36. Example output files

For:

```python
output_name = "Lower Yangtze-GMM"
```

the graphical outputs are:

```text
Lower Yangtze-GMM.png
Lower Yangtze-GMM.pdf
Lower Yangtze-GMM.svg
```

and the numerical peak tables are:

```text
Lower Yangtze-GMM_GMM_bootstrap_peaks.csv
Lower Yangtze-GMM_GMM_bootstrap_peaks.xlsx
```

---

# 37. Recommended quick test

Before running a full 5000-replicate analysis, it is useful to perform a short test run.

For example, in `bootstrap_GMM.ipynb`:

```python
n_bootstrap = 50
n_jobs = 2
gmm_n_init = 3
```

After confirming that:

- the input file is read correctly;
- both `Sample_ID` values are recognized;
- the script completes successfully;
- figures and tables are generated;

the parameters can be returned to the final values.

For example:

```python
n_bootstrap = 5000
n_jobs = 64
gmm_n_init = 10
```

provided that sufficient CPU resources are available.

---

# 38. Running `bootstrap_GMM.py` without Jupyter

The Python script can also be executed directly from a terminal.

For example:

```bash
export GMM_EXCEL_PATH="/path/to/baserock_data.xlsx"
export GMM_OUT_DIR="/path/to/results"
export GMM_SAMPLE_A="Zr-Jinsha"
export GMM_SAMPLE_B="Ar-Jinsha"
export GMM_FNAME="Jinsha-GMM"
export GMM_N_BOOTSTRAP="5000"
export GMM_N_JOBS="8"
export GMM_N_INIT="10"

python bootstrap_GMM.py
```

A short test can be run using:

```bash
export GMM_N_BOOTSTRAP="50"
export GMM_N_JOBS="2"

python bootstrap_GMM.py
```

---

# 39. Default settings in `bootstrap_GMM.py`

If no environment-variable overrides are supplied, the current script uses the following principal GMM settings:

```text
Bootstrap replicates       = 5000
Minimum GMM components     = 1
Maximum GMM components     = 10
Peak merge tolerance       = 10%
Minimum bootstrap support  = 60%
GMM initializations        = 10
Random seed                = 42
```

The default number of parallel workers is automatically limited according to the available CPU count, with a maximum default of eight workers.

Settings supplied through `bootstrap_GMM.ipynb` override these defaults.

---

# 40. Reproducibility

For reproducible analyses, the following should be archived together:

- `bootstrap_GMM.py`;
- `bootstrap_GMM.ipynb`;
- `gmm_openblas_environment(1).yml`;
- the original input Excel workbook;
- the `Sample_ID` values analyzed;
- the number of bootstrap replicates;
- the number of worker processes;
- the number of GMM initializations;
- the output files;
- the software versions used for the final calculation.

The supplied Conda environment file provides the principal software dependencies required by the workflow.

---

# 41. Numerical reproducibility

Small numerical differences can occur among computing systems because Gaussian mixture fitting involves iterative floating-point optimization.

Potential sources include:

- CPU architecture;
- operating system;
- NumPy version;
- scikit-learn version;
- BLAS implementation;
- floating-point operation ordering;
- parallel execution.

Using the supplied OpenBLAS Conda environment and retaining the random-seed configuration helps improve reproducibility.

---

# 42. Methodological notes

This workflow is intended to identify recurrent components in geochronologic age distributions rather than to assign a geological interpretation automatically to every fitted Gaussian component.

The statistical stability of a modeled age component does not by itself establish its geological origin.

Interpretation should therefore consider independent geological constraints, including:

- regional bedrock geochronology;
- tectonic setting;
- mineral provenance;
- sediment transport;
- analytical sampling;
- potential sediment recycling.

---

# 43. Methodological references

The bootstrap procedure follows the general statistical framework introduced by:

> Efron, B., 1979, Bootstrap methods: Another look at the jackknife: *The Annals of Statistics*, v. 7, p. 1–26. https://doi.org/10.1214/aos/1176344552

The Bayesian information criterion used for GMM model selection follows:

> Schwarz, G., 1978, Estimating the dimension of a model: *The Annals of Statistics*, v. 6, p. 461–464. https://doi.org/10.1214/aos/1176344136

Gaussian mixture models are implemented using:

```python
sklearn.mixture.GaussianMixture
```

from `scikit-learn`.

---

# 44. Application to the associated study

This workflow was developed for analysis of compiled zircon U–Pb and Ar-system age distributions associated with a study of mineral-specific geochronologic signals in the Yangtze River system.

The same workflow can be applied to other geochronologic datasets provided that the input workbook contains compatible `Sample_ID` and `BestAge` columns.

---

# 45. Associated study

The code accompanies the study:

> Xie, H., et al., *Zircon versus muscovite: Decoupled detrital geochronologic signals in large-river fingerprinting.*

The complete bibliographic information should be added after publication.

---

# 46. Citation

If this code is used in another study, please cite the associated publication together with the relevant methodological references.

A permanent citation for this repository can be added if the GitHub release is archived through a repository such as Zenodo.

---

# 47. Data availability

The geochronologic input dataset is not embedded directly in the three computational files.

Users must specify the appropriate Excel workbook in `bootstrap_GMM.ipynb` or through the `GMM_EXCEL_PATH` environment variable.

Data availability should follow the data-access statement of the associated publication.

---

# 48. Code availability

The computational workflow required for the bootstrap GMM analysis is contained in:

```text
bootstrap_GMM.py
bootstrap_GMM.ipynb
gmm_openblas_environment(1).yml
```

Together, these files provide:

- the numerical implementation;
- the user interface;
- the reproducible software environment.

---

# 49. License

A software license should be selected before public release.

For academic research code intended for reuse, the MIT License is a commonly used permissive option.

If the MIT License is selected, add a file named:

```text
LICENSE
```

to the repository.

---

# 50. Contact

For questions regarding the bootstrap GMM workflow or the associated geochronologic analysis, please contact the authors of the associated study.
