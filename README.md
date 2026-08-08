# bootstrap_GMM

```py
conda env create -f gmm_openblas_environment.yml

conda activate gmm_openblas

conda list | grep -E "libblas|openblas|mkl|intel-openmp"

python -c "import numpy, pandas, sklearn, joblib, matplotlib, openpyxl; print('All packages OK')"

python -c "from sklearn.mixture import GaussianMixture; print('GaussianMixture OK')"

conda install -c conda-forge ipykernel -y

python -m ipykernel install \
  --user \
  --name gmm_openblas \
  --display-name "Python (gmm_openblas)"


conda install -c conda-forge jupyterlab notebook ipykernel -y


jupyter kernelspec list


import sys
print(sys.executable)

import numpy as np
import pandas as pd
import sklearn
import joblib
import matplotlib
import openpyxl

from sklearn.mixture import GaussianMixture

print("NumPy:", np.__version__)
print("scikit-learn:", sklearn.__version__)
print("joblib:", joblib.__version__)
print("所有依赖正常")

import os
import sys
import subprocess
from pathlib import Path
```

# 1. 用户设置区：以后只修改这里

- 修改后的 Python 脚本
```py
script_path = Path(
    "/media/tigerwp/data/Xiehongsen/Illustrate of Yangtze data/"
    "bootstrap GMM/Supplemental_bootstrap_GMM_Jupyter_configurable.py"
)
```

- 输入 Excel 文件
```py
excel_path = Path(
    "/media/tigerwp/data/Xiehongsen/Illustrate of Yangtze data/"
    "baserock python data.xlsx"
)
```
- 输出文件夹
```py
output_dir = Path(
    "/media/tigerwp/data/Xiehongsen/Illustrate of Yangtze data/"
    "bootstrap GMM/Jinsha_results/"
)
```
- Excel中两个样品的 Sample_ID
```py
sample_a = "Zr-Jinsha"
sample_b = "Ar-Jinsha"
```
- 输出文件名前缀，不要加 .png 或 .xlsx 后缀
```py
output_name = "Jinsha-GMM"
```
- 计算参数
```py
n_bootstrap = 1000
n_jobs = 8
gmm_n_init = 3
```

# 2. 文件与参数检查
```py
if not script_path.is_file():
    raise FileNotFoundError(f"找不到 Python 脚本：\n{script_path}")

if not excel_path.is_file():
    raise FileNotFoundError(f"找不到 Excel 文件：\n{excel_path}")

if not sample_a.strip():
    raise ValueError("sample_a 不能为空")

if not sample_b.strip():
    raise ValueError("sample_b 不能为空")

if sample_a.strip() == sample_b.strip():
    raise ValueError("sample_a 和 sample_b 不能相同")

if n_bootstrap < 1:
    raise ValueError("n_bootstrap 必须大于 0")

if n_jobs == 0:
    raise ValueError("n_jobs 不能为 0")

if gmm_n_init < 1:
    raise ValueError("gmm_n_init 必须大于 0")

output_dir.mkdir(parents=True, exist_ok=True)
```

# 3. 将设置传递给 Python 脚本
```py
env = os.environ.copy()
```
- 路径、样品名和输出名称
```py
env["GMM_EXCEL_PATH"] = str(excel_path)
env["GMM_OUT_DIR"] = str(output_dir)
env["GMM_SAMPLE_A"] = sample_a.strip()
env["GMM_SAMPLE_B"] = sample_b.strip()
env["GMM_FNAME"] = output_name.strip()
```
- bootstrap 和并行设置
```py
env["GMM_N_BOOTSTRAP"] = str(n_bootstrap)
env["GMM_N_JOBS"] = str(n_jobs)
env["GMM_N_INIT"] = str(gmm_n_init)
```
- 每个并行进程内部只使用一个底层计算线程
```py
env["OMP_NUM_THREADS"] = "1"
env["MKL_NUM_THREADS"] = "1"
env["OPENBLAS_NUM_THREADS"] = "1"
env["NUMEXPR_NUM_THREADS"] = "1"
env["VECLIB_MAXIMUM_THREADS"] = "1"
env["BLIS_NUM_THREADS"] = "1"
```
- 防止服务器上图形窗口阻塞
```py
env["MPLBACKEND"] = "Agg"
```

# 4. 显示本次运行设置
```py
print("本次运行设置")
print("-" * 60)
print("Python：", sys.executable)
print("脚本：", script_path)
print("Excel：", excel_path)
print("输出目录：", output_dir)
print("样品 A：", sample_a)
print("样品 B：", sample_b)
print("输出名称：", output_name)
print("Bootstrap：", n_bootstrap)
print("并行进程：", n_jobs)
print("GMM n_init：", gmm_n_init)
print("-" * 60)
```

# 5. 运行完整脚本
```py
result = subprocess.run(
    [sys.executable, str(script_path)],
    env=env,
    check=False
)

print("-" * 60)
print("程序返回代码：", result.returncode)

if result.returncode == 0:
    print("计算正常完成。")
    print("结果保存在：", output_dir)
else:
    print("程序运行失败，请查看上方报错信息。")
```


