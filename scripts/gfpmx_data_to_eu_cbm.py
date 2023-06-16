"""Copy GFTMX data to the eu_cbm_data repository

Note:

- The first version copies the gftmx input.
- The second version copies the gftmx output.

In the SSP2 scenario, the GFTMX input should be identical to the output if
cobwood.GFTMX fully reproduces the simulation.

"""

from pathlib import Path
import shutil

import cobwood

# gfpmx_data_b2018 = GFPMXData(data_dir="gfpmx_8_6_2021")
# gfpmx_data_b2020 = GFPMXData(data_dir="gfpmx_base2020")
# gfpmx_data_b2021 = GFPMXData(data_dir="gfpmx_base2021")


def copy_from_gftmx_input_to_eu_cbm(orig_dir, dest_dir):
    """Copy from the GFTMX model output to the EU CBM model input"""
    gfpmx_data_dir = cobwood.data_dir / orig_dir
    # Paste files to libcbm_data for the forest dynamics model
    dest_dir = Path.home() / "repos/eu_cbm/eu_cbm_data/domestic_harvest/cobwood"
    dest_dir.mkdir(exist_ok=True)
    # Renames those primary product files to "harvest"
    shutil.copy(gfpmx_data_dir / "fuelprod.csv", dest_dir / "fw_harvest.csv")
    shutil.copy(gfpmx_data_dir / "indroundprod.csv", dest_dir / "irw_harvest.csv")
    # Copy secondary product files
    production_files = [
        "panelprod.csv",
        "paperprod.csv",
        "pulpprod.csv",
        "roundprod.csv",
        "sawnprod.csv",
    ]
    for prod_file in production_files:
        shutil.copy(gfpmx_data_dir / prod_file, dest_dir / prod_file)

    print(f"Copied from {gfpmx_data_dir} to {dest_dir}")


# copy_from_gftmx_to_eu_cbm
