from reVX.handlers.outputs import Outputs
from rev_powersystems import SIIPTimeSeriesMetadata

with Outputs("data/siip_example_simple_plant_builder.h5", "r") as f:
    (
        SIIPTimeSeriesMetadata
        .from_rev(f)
        .add_rev_timeseries(f, "data/siip_timeseries.csv")
        .export_json("data/siip_timeseries_metadata.json")
    )
