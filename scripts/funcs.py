import os
import sys

import git
import psutil


def restart_program():
    """
    Restarts the current program, with file objects and descriptors cleanup.
    https://stackoverflow.com/a/33334183
    """
    try:
        p = psutil.Process(os.getpid())
        for handler in p.open_files() + p.connections():
            os.close(handler.fd)
    except Exception as e:
        print('Could not restart Automated FBI Reporter after update.')
        print(e)
        sys.exit(1)
    python = sys.executable
    os.execl(python, python, *sys.argv)


def git_pull_changed(path):
    """
    https://github.com/jamesgeddes/pullcheck/blob/master/main.py#L10
    """
    repo = git.Repo(path)
    current = repo.head.commit
    repo.remotes.origin.pull()
    return current != repo.head.commit


def concat(input_obj) -> list:
    """
    Used to turn a machine hardware signature into a string.
    Makes it easy to quickly compare machines and determine which one
    the criminal used to generate unsafe images.
    """
    out = []
    if isinstance(input_obj, dict):
        for k, v in input_obj.items():
            out = out + concat(v)
    elif isinstance(input_obj, list) or isinstance(input_obj, tuple):
        for item in input_obj:
            out = out + concat(item)
    else:
        out.append(input_obj)
    return out
