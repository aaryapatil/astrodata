"""Tests for the GMOS imaging mode.

.. _DRAGONS_GMOSIMG_TUTORIAL: https://dragons.readthedocs.io/\
projects/gmosimg-drtutorial/en/v3.2.0/ex1_gmosim_starfield_api.html
"""

import importlib

import pytest

import astrodata
from astrodata.testing import (
    expand_file_range,
    download_multiple_files,
)


@pytest.fixture(scope="session")
def gmos_imaging_data_star_field_files():
    """Retrieve GMOS imaging data for the star field tutorial."""
    files = [
        "N20170614S0201-205",
        "N20170615S0534-538",
        "N20170702S0178-182",
        "bpm_20170306_gmos-n_Ham_22_full_12amp.fits",
    ]

    expanded_files = []

    for file in files:
        if not file.startswith("bpm"):
            expanded_files += expand_file_range(file)
            continue

        expanded_files += [file]

    return expanded_files


@pytest.fixture(scope="session")
def _downloaded_gmos_imaging_data_star_field(
    tmpdir_factory, gmos_imaging_data_star_field_files
):
    """Download GMOS imaging data for the star field tutorial."""
    tmpdir = tmpdir_factory.mktemp("gmos_imaging_data_star_field")

    data = download_multiple_files(
        gmos_imaging_data_star_field_files,
        path=tmpdir,
        sub_path="",
    )

    return data


@pytest.fixture
def gmos_imaging_data_star_field(
    tmp_path, _downloaded_gmos_imaging_data_star_field
):
    # Copy the files from the temporary directory to the test directory instead
    # of re-downlaoding them.
    data = {}

    for file, path in _downloaded_gmos_imaging_data_star_field.items():
        data[file] = tmp_path / file

        with open(data[file], "wb") as f:
            with open(path, "rb") as f2:
                f.write(f2.read())

    return data


@pytest.mark.dragons
def test_correct_astrodata():
    """Test if the astrodata package is being tested."""
    assert astrodata.from_file


@pytest.mark.filterwarnings("ignore:use 'astrodata.from_file'")
@pytest.mark.filterwarnings("ignore:Renamed to 'as_iraf_section'")
@pytest.mark.filterwarnings("ignore:Renamed to add_class")
@pytest.mark.filterwarnings("ignore:Deprecated API features detected!")
@pytest.mark.dragons
def test_gmos_imaging_tutorial_star_field(
    tmp_path, gmos_imaging_data_star_field
):
    """Test based on the DRAGONS GMOS imaging tutorial.

    This does **not** follow the tutorial directly. It is just testing based on
    the tutorial, and should be updated if the tutorial changes.

    Notably, importing is a bit different, and the tutorial uses a different
    method to get the data.

    Link: `DRAGONS_GMOSIMG_TUTORIAL`_
    """
    data = gmos_imaging_data_star_field

    # Import required modules
    # ruff: noqa: F841
    gemini_instruments = importlib.import_module("gemini_instruments")
    Reduce = importlib.import_module(
        "recipe_system.reduction.coreReduce"
    ).Reduce
    dataselect = importlib.import_module("gempy.adlibrary.dataselect")
    cal_service = importlib.import_module("recipe_system.cal_service")

    all_files = sorted(list(data.values()))

    # Sifting through teh data with data_select
    list_of_biases = dataselect.select_data(
        all_files,
        ["BIAS"],
        [],
    )

    list_of_flats = dataselect.select_data(
        all_files,
        ["FLAT"],
        [],
        dataselect.expr_parser(
            'filter_name=="i"',
        ),
    )

    list_of_science = dataselect.select_data(
        all_files,
        [],
        ["CAL"],
        dataselect.expr_parser(
            '(observation_class=="science" and filter_name=="i")'
        ),
    )

    caldb = cal_service.LocalDB(tmp_path / "calibration.db")
    caldb.init()

    for bpm in dataselect.select_data(all_files, ["BPM"]):
        caldb.add_cal(bpm)
