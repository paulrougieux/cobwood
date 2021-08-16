import os

# Where is the data, default case #
gftmx_data_dir = "~/repos/gftmx_data/"

# But you can override that with an environment variable #
if os.environ.get("GFTMX_DATA"):
    gftmx_data_dir = os.environ['GFTMX_DATA']
