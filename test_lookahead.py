from revx_output_siip import save_all_lookahead
import os

lookaheads = [
    'data/siip_example_simple_plant_builder.h5',
    'data/siip_example_simple_plant_builder_lookahead.h5'
]
time_series_csv = 'data/lookahead_timeseries/{}_siip_timeseries.csv'
metadata_json_filename = 'data/siip_lookahead_metadata.json'

directory = 'data/lookahead_timeseries/'
if not os.path.exists(directory):
    os.makedirs(directory)

save_all_lookahead(lookaheads, time_series_csv, metadata_json_filename)
