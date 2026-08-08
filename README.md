# Bootstrap GMM Analysis of Geochronologic Age Distributions

This repository contains the Python workflow used for bootstrap Gaussian mixture modeling (GMM) of geochronologic age distributions in the associated study.

The workflow combines Gaussian mixture modeling, Bayesian information criterion (BIC) model selection, and bootstrap resampling to identify stable age components in geochronologic datasets.

## Files

The repository contains three files:

- `bootstrap_GMM.py`  
  Main Python script for Gaussian mixture modeling, bootstrap resampling, stable peak identification, and figure generation.

- `bootstrap_GMM.ipynb`  
  Jupyter Notebook used to configure the analysis and run `bootstrap_GMM.py`.

- `gmm_openblas_environment.yml`  
  Conda environment used for the analysis.

## Method

Positive ages are transformed to log10(age) before Gaussian mixture modeling.

For each age dataset, Gaussian mixture models containing 1–10 components are evaluated, and the preferred model is selected using the Bayesian information criterion (BIC).

Bootstrap resampling is then performed by sampling the observed ages with replacement. A new BIC-selected GMM is fitted independently to each bootstrap replicate.

Gaussian components identified in different bootstrap replicates are grouped when their peak ages differ by no more than 10%. A component is retained as a stable age peak when it occurs in at least 60% of the bootstrap replicates.

The reported 95% bootstrap age range corresponds to the 2.5th–97.5th percentile range of component ages within each stable peak cluster.

The current implementation resamples the observed ages only; analytical age uncertainties are not propagated during bootstrap resampling.

## Input data

The input Excel file must contain at least the following columns:

```text
Sample_ID
BestAge
```

`Sample_ID` identifies individual age datasets, and `BestAge` contains the ages used for GMM analysis.

The Excel file may contain one or multiple datasets distinguished by different `Sample_ID` values.

Users should specify their own input file, output directory, and `Sample_ID` values in `bootstrap_GMM.ipynb`.

## Number of datasets

The statistical core of the workflow operates on one age dataset at a time and is not intrinsically restricted to two datasets.

The supplied `bootstrap_GMM.py` and `bootstrap_GMM.ipynb` are configured to analyze and plot two datasets in each run because this configuration was used in the associated study.

For a single dataset, the bootstrap GMM procedure can be applied only to the selected `Sample_ID`, and the second-dataset calculation and plotting steps can be omitted.

For multiple datasets, the same procedure can be applied independently to each `Sample_ID`. For example:

```python
sample_ids = [
    "Sample-1",
    "Sample-2",
    "Sample-3"
]
```

The core analysis can then be repeated for each dataset using `find_stable_gmm_peaks()`.

For example:

```python
for sample_id in sample_ids:
    ages = get_sample_ages(df, sample_id)

    peaks = find_stable_gmm_peaks(
        ages=ages,
        sample_name=sample_id,
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
```

Thus, one, two, or multiple age datasets can be analyzed using the same bootstrap GMM procedure. The plotting and output sections can be adapted according to the number of datasets being analyzed.

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

Verify `GaussianMixture`:

```bash
python -c "from sklearn.mixture import GaussianMixture; print('GaussianMixture OK')"
```

If necessary, install Jupyter:

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

In the user-configuration section of the notebook, specify:

- the path to `bootstrap_GMM.py`;
- the input Excel file;
- the output directory;
- the `Sample_ID` value(s) to be analyzed;
- the output filename;
- the number of bootstrap replicates;
- the number of parallel workers;
- the number of GMM initializations.

The supplied notebook is configured for two datasets per run. The underlying bootstrap GMM functions can also be applied to a single dataset or repeated for multiple datasets.

The principal computational parameters used in the associated study are:

```python
n_bootstrap = 5000
n_jobs = 8
gmm_n_init = 10
```

The number of parallel workers (`n_jobs`) can be adjusted according to the available computational resources.

For a quick test before the full calculation, a smaller number of bootstrap replicates can be used, for example:

```python
n_bootstrap = 50
n_jobs = 2
gmm_n_init = 3
```

## Default analysis settings

The principal settings in `bootstrap_GMM.py` are:

```text
GMM component range:       1–10
Bootstrap replicates:      5000
Peak merge tolerance:      10%
Minimum bootstrap support: 60%
GMM n_init:                10
Random seed:               42
```

Bootstrap calculations are parallelized using `joblib`.

Each parallel worker is restricted to one BLAS/OpenMP thread to avoid nested parallelism and CPU oversubscription.

## Output

The analysis exports stable GMM peak statistics as:

```text
*_GMM_bootstrap_peaks.csv
*_GMM_bootstrap_peaks.xlsx
```

The output table includes:

- stable peak age;
- 95% bootstrap age range;
- bootstrap support;
- mean and median component weights;
- Gaussian width in log10(age) space;
- median number of GMM components selected by BIC;
- number of bootstrap replicates supporting each peak;
- ECDF position of each peak.

The script also generates empirical cumulative distribution function (ECDF) plots with the identified stable GMM peaks.

Figures are exported as:

```text
*.png
*.pdf
*.svg
```

## Notes

The bootstrap procedure resamples observed ages with replacement.

Individual analytical age uncertainties are not propagated in the current implementation.

The 95% range reported for each stable peak therefore represents variation in the fitted peak position among bootstrap resamples rather than analytical uncertainty on individual ages.

Stable GMM components represent statistically recurrent features of the age distribution. Geological interpretation of these components should be based on independent geological and geochronological constraints.

## References

Efron, B., 1979, Bootstrap methods: Another look at the jackknife: *The Annals of Statistics*, v. 7, p. 1–26. https://doi.org/10.1214/aos/1176344552

Schwarz, G., 1978, Estimating the dimension of a model: *The Annals of Statistics*, v. 6, p. 461–464. https://doi.org/10.1214/aos/1176344136
