from reVX.handlers.outputs import Outputs
import pandas as pd
import json
import os
import datetime


def save_siip_time_series_csv(df, csv_filename):
    """Save time series dataframe with correct date formatting

    Parameters
    ----------
    df : pd.DataFrame
        Must contain datetime index
    csv_filename : str
    """
    df.to_csv(csv_filename, index_label="DateTime", date_format="%Y-%m-%dT%H:%M:%S")


def save_all_lookahead(
    lookaheads,
    time_series_csv,
    metadata_json_filename,
    resolution=datetime.timedelta(hours=1),
):
    if len(lookaheads) == 0:
        return
    with Outputs(lookaheads[0], "r") as output:
        components = output["meta"]["component_name"]
        metadata = create_initial_siip_metadata(output, resolution)
        time_index = output["time_index"]

    data_files = []
    for index, component in enumerate(components):
        timeseries = pd.DataFrame(index=time_index)
        for count, lookahead_file in enumerate(lookaheads):
            with Outputs(lookahead_file, "r") as output:
                df = pd.DataFrame(
                    {count: output["plant_profiles", :, index]},
                    index=output["time_index"],
                )
                timeseries = timeseries.join(df)
        csv_filename = time_series_csv.format(component)
        data_files.append(
            os.path.relpath(csv_filename, os.path.dirname(metadata_json_filename))
        )
        save_siip_time_series_csv(timeseries, csv_filename)
    metadata["data_file"] = data_files
    metadata["module"] = "InfrastructureSystems"
    metadata["type"] = "Deterministic"

    json_metadata = list(map(lambda row: row[1].to_dict(), metadata.iterrows()))
    with open(metadata_json_filename, "w") as f:
        json.dump(json_metadata, f)


def copy_with_default(source, target, column, default):
    "Copy column from source to target with a default."
    if column in source:
        target[column] = source[column]
    else:
        target[column] = default


def create_initial_siip_metadata(outputs, resolution=None):
    """
    Create SIIP metadata from outputs

    Parameters
    ----------
    outputs : reVX.handlers.output.Outputs
        Output from reVX plant builder
    resolution : datetime.timedelta, optional
        Filepath to csv time series

    Returns
    -------
    List of dictionaries containing SIIP metadata
    """
    metadata = outputs["meta"]
    siip_metadata = metadata.loc[:, ["component_name"]]
    if resolution is None:
        resolution = outputs["time_index"][1] - outputs["time_index"][0]
    siip_metadata["resolution"] = resolution.total_seconds()
    copy_with_default(metadata, siip_metadata, "normalization_factor", 1)
    copy_with_default(metadata, siip_metadata, "category", "Generator")
    copy_with_default(metadata, siip_metadata, "simulation", "")
    copy_with_default(metadata, siip_metadata, "name", "max_active_power")

    return siip_metadata


def validate_siip_columns(metadata):
    "Validate metadata coming from reVX output"
    component_name = "component_name" in metadata
    series_module = "module" in metadata
    series_type = "type" in metadata
    module_and_type = (series_module and series_type) or (
        not series_module and not series_type
    )
    return component_name and module_and_type


def save_time_series_and_metadata(
    outputs, timeseries_csv_filename, metadata_json_filename, name="component_name"
):
    """Save time series to csv with columns of `name`

    Parameters
    ----------
    outputs : reVX.handlers.output.Outputs
        Output from reVX plant builder
    timeseries_csv_filename : str
        Filename to save output time series to
    metadata_json_filename : str
        Filename to save SIIP metadata to
    name : str, default="name"
        Column in reVX metadata to serve as column names
    """
    if not validate_siip_columns(outputs["meta"]):
        raise RuntimeError("Missing SIIP columns in metadata")
    df = pd.DataFrame(
        outputs["plant_profiles", :, :],
        index=outputs["time_index"],
        columns=outputs["meta"][name],
    )

    siip_metadata = create_initial_siip_metadata(outputs)
    siip_metadata["data_file"] = os.path.relpath(
        timeseries_csv_filename, os.path.dirname(metadata_json_filename)
    )
    save_siip_time_series_csv(df, timeseries_csv_filename)
    json_metadata = list(map(lambda row: row[1].to_dict(), siip_metadata.iterrows()))
    with open(metadata_json_filename, "w") as f:
        json.dump(json_metadata, f)
