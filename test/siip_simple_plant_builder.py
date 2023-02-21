#!/usr/bin/env python3

import pandas as pd
import json
from reVX.plexos.simple_plant_builder import SimplePlantBuilder


plant_meta = "data/siip_meta.csv"

cf_fpath = "data/naris_rev_wtk_gen_colorado_2007.h5"

sc_fpath = "data/wtk_coe_2017_cem_v3_wind_conus_multiyear_colorado.csv"

def read_sc(filepath):
    rev_sc = pd.read_csv(filepath)
    rev_sc = rev_sc.rename(
        {
            "gid": "sc_gid",
            "resource_ids": "res_gids",
            "resource_ids_cnts": "gid_counts",
            "lat": "latitude",
            "lon": "longitude",
            "ncf": "mean_cf",
        },
        axis=1,
    )
    # test that it can handle some of these columns as loaded lists
    rev_sc["res_gids"] = rev_sc["res_gids"].apply(json.loads)
    return rev_sc

out_fpath = "data/siip_example_simple_plant_builder.h5"
out_lookahead_fpath = "data/siip_example_simple_plant_builder_lookahead.h5"

if __name__ == "__main__":
    print("Reading rev supply curve csv")
    rev_sc = read_sc(sc_fpath)
    print(f"Writing {out_fpath}")
    SimplePlantBuilder.run(plant_meta, rev_sc, cf_fpath, out_fpath=out_fpath)
    print(f"Writing {out_lookahead_fpath}")
    SimplePlantBuilder.run(plant_meta, rev_sc, cf_fpath, out_fpath=out_lookahead_fpath)
