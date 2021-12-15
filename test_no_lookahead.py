from reVX.handlers.outputs import Outputs
from revx_output_siip import save_time_series_and_metadata

with Outputs("data/siip_example_simple_plant_builder.h5", "r") as f:
    save_time_series_and_metadata(
        f, "data/siip_timeseries.csv", "data/siip_timeseries_metadata.json"
    )
