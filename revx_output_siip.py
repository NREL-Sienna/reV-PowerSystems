from reVX.handlers.outputs import Outputs
import pandas as pd
import json
import os


def create_time_series_dataframe(outputs, name="component_name"):
    """Create time series dataframe for all nodes in outputs

    Parameters
    ----------
    outputs : reVX.handlers.output.Outputs
        Output from reVX plant builder
    name : str, default="component_name"
        Column in reVX metadata to serve as column names

    Returns
    -------
    pd.DataFrame
        containing times as index, columns of `name`.
    """
    return pd.DataFrame(outputs["plant_profiles", :, :],
                 index=outputs["time_index"],
                 columns=outputs["meta"][name])


def copy_with_default(source, target, column, default):
    "Copy column from source to target with a default."
    if column in source:
        target[column] = source[column]
    else:
        target[column] = default


def create_siip_metadata(outputs, csv_output):
    """
    Create SIIP metadata from outputs

    Parameters
    ----------
    outputs : reVX.handlers.output.Outputs
        Output from reVX plant builder
    csv_output : str
        Filepath to csv time series

    Returns
    -------
    List of dictionaries containing SIIP metadata
    """
    metadata = outputs["meta"]
    siip_metadata = metadata.loc[:, ["component_name"]]
    time_delta = (outputs["time_index"][1] - outputs["time_index"][0]).total_seconds()
    siip_metadata["resolution"] = time_delta
    copy_with_default(metadata, siip_metadata, "normalization_factor", 1)
    copy_with_default(metadata, siip_metadata, "module", "InfrastructureSystems")
    copy_with_default(metadata, siip_metadata, "type", "SingleTimeSeries")
    copy_with_default(metadata, siip_metadata, "category", "Generator")
    copy_with_default(metadata, siip_metadata, "simulation", "")
    copy_with_default(metadata, siip_metadata, "name", "max_active_power")
    copy_with_default(
        metadata,
        siip_metadata,
        "scaling_factor_multiplier",
        "1" # reV should already do this
    )

    siip_metadata["data_file"] = csv_output
    return list(map(lambda row: row[1].to_dict(), siip_metadata.iterrows()))


def validate_siip_columns(metadata):
    "Validate metadata coming from reVX output"
    component_name = "component_name" in metadata
    series_module = "module" in metadata
    series_type = "type" in metadata
    module_and_type = ((series_module and series_type) or
                       (not series_module and not series_type))
    return component_name and module_and_type


def save_time_series_and_metadata(
        outputs,
        timeseries_csv_filename,
        metadata_json_filename,
        name="component_name"):
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
    df = create_time_series_dataframe(outputs, name)
    df.to_csv(timeseries_csv_filename, index_label="DateTime")

    siip_metadata = create_siip_metadata(
            outputs,
            os.path.relpath(timeseries_csv_filename,
                os.path.dirname(metadata_json_filename))
            )
    with open(metadata_json_filename, 'w') as f:
        json.dump(siip_metadata, f)


with Outputs("data/siip_example_simple_plant_builder.h5", "r") as f:
    save_time_series_and_metadata(
        f,
        'data/siip_timeseries.csv',
        'data/siip_timeseries_metadata.json'
    )

# We want to create a CSV where every component has it's own column
