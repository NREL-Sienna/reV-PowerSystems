from reVX.handlers.outputs import Outputs
import scipy.spatial
import pandas as pd
import numpy as np
import json
import os
import datetime
from typing import List, Union
from collections import defaultdict


def nrows(array):
    return array.shape[0]


def preimage(array):
    finverse = defaultdict(list)
    for i, v in enumerate(array):
        finverse[v].append(i)
    return finverse


def max_fiber_size(
        source_points,
        index_array,
        size_function=nrows
):
    """This function computes how far apart points are that
    map to the same thing.

    Formally, given a collection of points $X$ and a mapping $f : X -> Y$,
    compute $\mathrm{max}(\{\mathrm{size}(f^{-1}(y)) : y \in Y\})$.
    In other words, we compute the max size of each fiber.

    Parameters
    ----------
    source_points : array_like dimensions (m, n)
    index_array : array_like of int (k,)
    size_function : nonnegative function taking array and returning the size

    Returns
    -------
    max_size
    """
    max_size = 0
    for source_indices in preimage(index_array).values():
        max_size = max(max_size,
                       size_function(source_points[source_indices,:]))
    return max_size


def match_points(source_metadata, target_metadata, max_size=5):
    """Match source to target
    For each source_point, we find the index of the nearest target point.

    Parameters
    ----------
    source_metadata : pd.DataFrame
        Array containing lattitude and longitude
    target_metadata : pd.DataFrame
        Array containing lattitude and longitude
    max_size: float = 5
        Maximum size of each "fiber"

    Returns
    -------
    index_array : array of integers
    """
    assert 'latitude' in source_metadata and 'longitude' in source_metadata
    assert 'latitude' in target_metadata and 'longitude' in target_metadata
    source_points = source_metadata.loc[:, ['latitude', 'longitude']].to_numpy()
    target_points = target_metadata.loc[:, ['latitude', 'longitude']].to_numpy()
    _, index_array = scipy.spatial.KDTree(target_points).query(source_points)
    fiber_size = max_fiber_size(source_points, index_array)
    assert max_size >= fiber_size, f"fiber's have size {fiber_size}"
    return index_array


class SIIPTimeSeriesMetadata:
    """Class for constructing SIIP Time Series from reV

    Examples
    --------
    > (
        SIIPTimeSeries
        .from_rev(outputs)
        .add_rev_timeseries(outputs, "timeseries.csv")
        .export_json(path)
    )
    """
    def __init__(self, metadata=None):
        if metadata is None:
            self.siip_metadata = pd.DataFrame()
        else:
            self.siip_metadata = metadata.copy()
            (
                self
                .add_from(metadata, "normalization_factor", 1)
                .add_from(metadata, "category", "Generator")
                .add_from(metadata, "simulation", "")
                .add_from(metadata, "name", "max_active_power")
            )

    def add_from(self, source, column, default=None):
        "Copy column from source if metadata does not have column"
        if column not in self.siip_metadata:
            self.set_from(source, column, default)
        return self

    def set_from(self, source, column, default=None):
        "Copy column from source to metadata with a default."
        if column in source:
            self.siip_metadata[column] = source[column]
        elif default is not None:
            self.siip_metadata[column] = default
        return self

    def add(self, column, value):
        "Adds value at column only if metadata does not have column"
        if column not in self.siip_metadata:
            self.set(column, value)
        return self

    def set(self, column, value):
        self.siip_metadata[column] = value
        return self

    @classmethod
    def from_csv(cls, filename, id_column: str = "component_name"):
        metadata = pd.read_csv(filename).set_index(id_column)
        return cls(metadata)

    @classmethod
    def from_rev(cls, outputs: Union[str, Outputs],
                 id_column="component_name"):
        """Create initial SIIP metadata from reV output

        Parameters
        ----------
        outputs: Outputs or filename to Outputs
        id_names = "component_name"
            Column(s) of id names to use. Can be None.

        Returns
        -------
        SIIPTimeSeries
        """
        if isinstance(outputs, str):
            with Outputs(outputs, "r") as real_output:
                return cls.from_rev(real_output, id_column)
        metadata = outputs["meta"].copy()
        if id_column in metadata:
            metadata = metadata.set_index(id_column)
        siip = cls(metadata)
        resolution = outputs["time_index"][1] - outputs["time_index"][0]
        return (
            siip
            .set_resolution(resolution)
        )

    def set_resolution(self, resolution: datetime.timedelta):
        self.set("resolution", resolution.total_seconds())
        return self

    def add_rev_lookaheads(
            self,
            lookaheads: List[str],
            time_series_csv: str,
    ):
        """Set forecast by unwrapping each lookahead
        into "looking ahead" by `resolution` each time.

        Parameters
        ----------
        lookaheads : List[str]
            List of paths to lookahead files
        time_series_csv : str
            String containing one {} for lookahead index formatting
        """
        if len(lookaheads) == 0:
            return
        with Outputs(lookaheads[0], "r") as output:
            time_index = output["time_index"]

        data_files = []
        # For each component, we'll add the lookaheads to the time series
        for index, component in enumerate(self.siip_metadata.index):
            timeseries = pd.DataFrame(index=time_index)
            for count, lookahead_file in enumerate(lookaheads):
                with Outputs(lookahead_file, "r") as output:
                    df = pd.DataFrame(
                        {count: output["plant_profiles", :, index]},
                        index=output["time_index"],
                    )
                    timeseries = timeseries.join(df)
            csv_filename = time_series_csv.format(component)
            data_files.append(csv_filename)
            self.save_csv(timeseries, csv_filename)
        self.set("data_file", data_files)
        self.add("module", "InfrastructureSystems")
        self.add("type", "Deterministic")
        return self

    def add_all_timeseries(
            self,
            array,
            times,
            timeseries_csv_filename: str,
    ):
        """Save time series to csv with columns of initial ids.

        Parameters
        ----------
        array : array_like of size (m, n)
        times : table of time-index
        timeseries_csv_filename : str
            Filename to save output time series to
        """
        df = pd.DataFrame(
            array,
            index=times,
            columns=self.siip_metadata.index
        )
        self.set("data_file", timeseries_csv_filename)
        self.save_csv(df, timeseries_csv_filename)
        return self

    REQUIRED_COLUMNS=["resolution","normalization_factor","category","simulation","name","data_file"]
    OPTIONAL_COLUMNS=["module","type","scaling_factor_multiplier","scaling_factor_multiplier_module"]
    COLUMNS=REQUIRED_COLUMNS+OPTIONAL_COLUMNS

    def necessary_columns(self):
        columns = list(filter(lambda c: c in self.COLUMNS,
                              self.siip_metadata.columns))
        siip_data = self.siip_metadata.loc[:, columns].copy()
        siip_data["component_name"] = siip_data.index
        return siip_data

    def export_json(self, metadata_path):
        """Save json metadata to metadata_path"""
        self.validate_siip_columns()

        siip_data = self.necessary_columns()
        siip_data["data_file"] = siip_data["data_file"].map(
            lambda timeseries_csv: os.path.relpath(
                timeseries_csv, os.path.dirname(metadata_path)
            )
        )
        json_metadata = list(map(
            lambda row: row[1].to_dict(),
            siip_data.iterrows()
        ))

        with open(metadata_path, "w") as f:
            json.dump(json_metadata, f)

    @classmethod
    def save_csv(cls, df, csv_filename: str):
        """Save time series dataframe with correct date formatting

        Parameters
        ----------
        df : pd.DataFrame
            Must contain datetime index
        csv_filename : str
        """
        df.to_csv(csv_filename, index_label="DateTime", date_format="%Y-%m-%dT%H:%M:%S")

    def validate_siip_columns(self):
        "Validate metadata coming from reVX output"
        for c in self.REQUIRED_COLUMNS:
            assert c in self.siip_metadata, f"Missing column {c}"
        series_module = "module" in self.siip_metadata
        series_type = "type" in self.siip_metadata
        assert (series_module and series_type) or (
            not series_module and not series_type
        ), "Only module or type in metadata"


def concat(metadatas: List[SIIPTimeSeriesMetadata], **kwargs):
    "Concatenate SIIPTimeSeriesMetadata. Useful for adding multiple resolutions"
    return SIIPTimeSeriesMetadata(pd.concat(map(lambda x: x.siip_metadata, metadatas), **kwargs))
