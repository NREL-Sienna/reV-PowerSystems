from rev_powersystems import SIIPTimeSeriesMetadata
import os

lookaheads = [
    "data/siip_example_simple_plant_builder_utc.h5",
    "data/siip_example_simple_plant_builder_lookahead_utc.h5",
]
time_series_csv = "data/lookahead_timeseries/{}_siip_timeseries.csv"
metadata_json_filename = "data/siip_lookahead_metadata.json"

directory = "data/lookahead_timeseries/"
if not os.path.exists(directory):
    os.makedirs(directory)

(
    SIIPTimeSeriesMetadata
    .from_rev(lookaheads[0])
    .add_rev_lookaheads(lookaheads, time_series_csv)
    .export_json(metadata_json_filename)
)
