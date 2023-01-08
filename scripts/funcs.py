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
