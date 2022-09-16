import argparse
import json
import os
import pwd
import subprocess

from bcc import BPF, XDPFlags
from dechainy.controller import Controller

from . import AdaptivenessType


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
        'interface', help='local interface to receive the remote attacks', type=str)
    parser.add_argument('ssh_login', help='ssh remote login', type=str)
    parser.add_argument(
        'timeout', help='timeout to wait before stopping the test', type=int)
    parser.add_argument('ntimes', help='number of tests', type=int)

    return parser.parse_args().__dict__


if __name__ == '__main__':
    ctr = Controller()
    ctr.create_plugin(os.path.dirname(__file__), update=True)

    args = _parse_arguments()

    create_dir(os.path.join("results", "adaptiveness"))
    results = {}

    for mode in [BPF.XDP, BPF.SCHED_CLS]:
        results[mode] = {}
        for at in AdaptivenessType:
            if at.value != AdaptivenessType.TRADITIONAL.value:
                continue
            results[mode][at.value] = {}
            for i in [1, 5, 10, 50, 100]:
                vals = []
                for _ in range(args["ntimes"]):
                    ctr.create_probe(
                        __package__, "probe", interface=args["interface"],
                        mode=mode, flags=XDPFlags.DRV_MODE, nfeatures=i, adaptiveness_type=at)
                    p = ctr.get_probe(__package__, "probe")
                    print(f"{at} {i} ... ", end="", flush=True)
                    subprocess.check_call(
                        f'ssh -i /home/{os.getlogin()}/.ssh/id_rsa1 {args["ssh_login"]} "cd MoonGen && \
                            sudo ./build/MoonGen moongen.lua 1 --core 7 --timeout {args["timeout"]} \
                                --ipsnum 256 --portsnum 97"',
                        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    vals.append(p.retrieve())
                    del p
                    ctr.delete_probe(__package__, "probe")
                    print("Finished")
                results[mode][at.value][i] = vals

    with open(os.path.join("results", "adaptiveness", "results.json"), "w") as fp:
        json.dump(results, fp, indent=2)
