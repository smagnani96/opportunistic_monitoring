import argparse
import json
import os
import pwd
from bcc import BPF

from dechainy.controller import Controller

from . import MapType

def create_dir(name):
    try:
        os.makedirs(name)
    except FileExistsError:
        pass
    uid = pwd.getpwnam(os.getlogin()).pw_uid
    os.chown(name, uid, uid)


def _parse_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'ntimes', help='numbers of tests', type=int)
    parser.add_argument(
        'nentries', help='numbers of entries to test', type=int, nargs="+")
    return parser.parse_args().__dict__


if __name__ == '__main__':
    ctr = Controller()
    ctr.create_plugin(os.path.dirname(__file__), update=True)
    args = _parse_arguments()
    create_dir(os.path.join("results", "erase"))

    results = {}
    for mapt in MapType:
        results[mapt.value] = {}
        for i in [int(x) for x in args["nentries"]]:
            vals = []
            for _ in range(args["ntimes"]):
                ctr.create_probe(__package__, "probe", interface="lo",
                                 mode=BPF.XDP, n_entries=i, map_type=mapt)
                p = ctr.get_probe(__package__, "probe")
                print("{} {}".format(mapt.value, i))
                vals.append(p.retrieve())
                del p
                ctr.delete_probe(__package__, "probe")
            results[mapt.value][i] = vals

    with open(os.path.join("results", "erase", "results.json"), "w") as fp:
        json.dump(results, fp, indent=2)
