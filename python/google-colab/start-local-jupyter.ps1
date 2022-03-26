#
# This script starts a local Jupyter server that google CoLab can connect to.
# See: https://research.google.com/colaboratory/local-runtimes.html
#
# It assume it is being run in a python environment that has all
# 1. Jupyter installed
# 2. jupyter_http_over_ws extension installed
# 3. All other python modules e.g. Tensor flow loaded - required by this Python project
#
# See the file python/conda/activity_monitor_conda_env.yml in this project which defines this full
# environment as a conda export.
#
jupyter notebook --NotebookApp.allow_origin='https://colab.research.google.com' --port=8888 --NotebookApp.port_retries=0