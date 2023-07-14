import importlib
from distutils import dir_util
import pandas as pd
from pytest import fixture
import os

organize_run_results = importlib.import_module("misc-scripts.organize_run_results")


@fixture
def datadir(tmpdir, request):
    '''
    Fixture responsible for searching a folder with the same name of test module and, if available, moving all
    contents to a temporary directory so tests can use them freely.
    '''
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmpdir))

    return tmpdir


def test_load_df_from_run_info(datadir):
    """
    Test uses a fixture that copies all structure from `tests/test_organize_run_results` directory into a temporary
    directory, which is later treated as the data_folder (that is normally in the Dropbox, but not for tests). Test
    loads the run_info from respective locations in the `multicomp-reactions/2023-06-20-run01/` in the temporary
    folder and then checks the results against an expected dataframe loaded from `expected_outputs/run_info.pkl`.

    Parameters
    ----------
    datadir: pytest fixture
        Temporary directory with the same structure as `tests/test_organize_run_results` directory.
    """
    data_folder = ''
    with datadir.as_cwd():
        experiment_name = 'multicomp-reactions/2023-06-20-run01/'
        pd.testing.assert_frame_equal(
            organize_run_results.load_df_from_run_info(experiment_name + 'pipetter_io/run_info.csv'),
            pd.read_pickle('expected_outputs/run_info.pkl'))


def test_load_df_from_dilution_info(datadir):
    """
    Test uses a fixture that copies all structure from `tests/test_organize_run_results` directory into a temporary
    directory, which is later treated as the data_folder (that is normally in the Dropbox, but not for tests). Test
    loads the dataframw eith information about dilution from respective locations in the
    `multicomp-reactions/2023-06-20-run01/` in the temporary folder and then checks the results against an expected
    dataframe loaded from `expected_outputs/dilution_info.pkl`.

    Parameters
    ----------
    datadir: pytest fixture
        Temporary directory with the same structure as `tests/test_organize_run_results` directory.
    """
    data_folder = ''
    with datadir.as_cwd():
        pd.testing.assert_frame_equal(
            organize_run_results.load_df_from_dilution_info('multicomp-reactions/2023-06-20-run01/'),
            pd.read_pickle('expected_outputs/dilution_info.pkl'))
