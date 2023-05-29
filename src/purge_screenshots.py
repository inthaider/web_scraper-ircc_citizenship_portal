"""
This module contains a function to purge old screenshots from the screenshots directory.

This function can be called by the main script in check_ircc_updates.py at the end of each update check.

Functions
---------
purge_old_screenshots(dir_path, num_to_keep=10)
    Deletes the oldest screenshots in the specified directory if there are more than num_to_keep files (default 10).

"""
import os


def purge_old_screenshots(dir_path, num_to_keep=10):
    """Deletes the oldest screenshots in the specified directory if there are more than num_to_keep files (default 10).

    Parameters
    ----------
    dir_path : str
        The path to the directory containing the screenshots.
    num_to_keep : int, optional
        The number of screenshots to keep. The default is 10.

    Returns
    -------
    None

    Notes
    -----
    This function should be called by the main script in
    check_ircc_updates.py at the end of each update check.
    """
    # List all files in the directory along with their timestamps
    files = [
        (f, os.path.getmtime(os.path.join(dir_path, f)))
        for f in os.listdir(dir_path)
        if os.path.isfile(os.path.join(dir_path, f))
    ]

    # Sort the files by timestamp, oldest first
    files.sort(key=lambda x: x[1])

    # If there are more than num_to_keep files, delete the oldest ones.
    # The -1 is there because we have a .gitkeep file in the screenshots directory.
    while (len(files) - 1) > num_to_keep:
        oldest_file = files.pop(0)
        os.remove(os.path.join(dir_path, oldest_file[0]))
