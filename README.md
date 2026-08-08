# Bootstrap GMM Analysis of Geochronologic Age Distributions

This repository contains the Python workflow used for bootstrap Gaussian mixture modeling (GMM) of geochronologic age distributions in our study.

The workflow combines Gaussian mixture modeling, Bayesian information criterion (BIC) model selection, and bootstrap resampling to identify stable age components in geochronologic datasets.

## Files

- `bootstrap_GMM.py`  
  Main Python script for GMM fitting, BIC model selection, bootstrap resampling, stable peak identification, and figure generation.

- `bootstrap_GMM.ipynb`  
  Jupyter Notebook used to configure and run `bootstrap_GMM.py`.

- `gmm_openblas_environment.yml`  
  Conda environment used for the analysis.

## Method

Positive ages are transformed to log10(age) before Gaussian mixture modeling.

For each bootstrap replicate, Gaussian mixture models containing 1–10 components are fitted, and the preferred number of components is selected using the Bayesian information criterion (BIC).

Bootstrap resampling is performed by sampling the observed ages with replacement. The bootstrap sample size is equal to the original sample size.

Gaussian components identified among different bootstrap replicates are grouped when their peak ages differ by no more than 10%. A peak is retained as a stable component when it occurs in at least 60% of the bootstrap replicates.

For each stable peak, the workflow reports the representative peak age, bootstrap support, component weight, and the 2.5th–97.5th percentile range of bootstrap peak ages.

The current analysis resamples the observed ages only; analytical age uncertainties are not propagated during bootstrap resampling.

## Default settings

The principal settings used in the analysis are:

```text
Number of bootstrap replicates: 5000
Minimum number of GMM components: 1
Maximum number of GMM components: 10
GMM initializations (n_init): 10
Peak merge tolerance: 10%
Minimum bootstrap support: 60%
Random seed: 42
```

Bootstrap calculations are parallelized using `joblib` with the `loky` backend. Each worker is restricted to one BLAS/OpenMP thread to avoid nested parallelism.

## Input

The analysis requires an Excel file containing at least:

```text
Sample_ID
BestAge
```

Only finite and positive `BestAge` values are used in the analysis.

Input paths, output paths, sample IDs, and computational settings can be specified in `bootstrap_GMM.ipynb`.

## Installation

Create the Conda environment:

```bash
conda env create -f gmm_openblas_environment.yml
```

Activate the environment:

```bash
conda activate gmm_openblas
```

Check the numerical backend:

```bash
conda list | grep -E "libblas|openblas|mkl|intel-openmp"
```

Verify the required Python packages:

```bash
python -c "import numpy, pandas, sklearn, joblib, matplotlib, openpyxl; print('All packages OK')"
```

Verify the Gaussian mixture model implementation:

```bash
python -c "from sklearn.mixture import GaussianMixture; print('GaussianMixture OK')"
```

Install Jupyter support if required:

```bash
conda install -c conda-forge jupyterlab notebook ipykernel -y
```

Register the environment as a Jupyter kernel:

```bash
python -m ipykernel install \
  --user \
  --name gmm_openblas \
  --display-name "Python (gmm_openblas)"
```

## Usage

Open:

```text
bootstrap_GMM.ipynb
```

and select:

```text
Python (gmm_openblas)
```

as the Jupyter kernel.

Specify the required file paths, sample IDs, output name, and computational parameters in the configuration section of the notebook.

The main computational parameters are:

```python
n_bootstrap = 5000
n_jobs = 8
gmm_n_init = 10
```

`n_jobs` can be adjusted according to the available CPU resources.

Run the notebook cells sequentially to execute `bootstrap_GMM.py`.

## Stable peak identification

Candidate GMM components from all bootstrap replicates are grouped in log-age space using a maximum relative peak-age difference of 10%.

For each resulting peak cluster, bootstrap support is calculated as:

```text
number of bootstrap replicates containing the peak
--------------------------------------------------
total number of bootstrap replicates
```

Only peaks with bootstrap support ≥60% are retained as stable peaks.

The representative age of each stable peak is calculated from the grouped component positions in log-age space using the component weights.

The reported 95% bootstrap range corresponds to the 2.5th and 97.5th percentiles of the component ages assigned to each stable peak.

## Output

Stable GMM peak statistics are exported as:

```text
*_GMM_bootstrap_peaks.csv
*_GMM_bootstrap_peaks.xlsx
```

The output table includes:

```text
Sample_ID
Peak_rank_by_age
Peak_age_Ma
CI95_low_Ma
CI95_high_Ma
Bootstrap_support
Mean_component_weight
Median_component_weight
Mean_sigma_log10_age
Median_selected_K
Score
N_boot_support
N_candidates_in_cluster
ECDF_y
```

The workflow also plots empirical cumulative distribution functions (ECDFs) together with the identified stable GMM peaks.

Figures are exported as:

```text
*.png
*.pdf
*.svg
```

with PNG output at 1200 dpi.

## Notes

- GMM fitting is performed in log10(age) space.
- The number of Gaussian components is selected independently for each bootstrap replicate using BIC.
- Bootstrap resampling is performed on the observed ages with replacement.
- Analytical age uncertainties are not propagated.
- The number of stable peaks is not fixed in advance.
- Only peaks reaching the minimum bootstrap-support threshold are retained.
- Parallel calculations use independent processes with one BLAS/OpenMP thread per worker.

## References

Efron, B., 1979, Bootstrap methods: Another look at the jackknife: *The Annals of Statistics*, v. 7, p. 1–26. https://doi.org/10.1214/aos/1176344552

Schwarz, G., 1978, Estimating the dimension of a model: *The Annals of Statistics*, v. 6, p. 461–464. https://doi.org/10.1214/aos/1176344136
