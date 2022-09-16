import argparse
import json
import logging
import os
import pwd
import subprocess

from bcc import BPF, XDPFlags
from dechainy.controller import Controller

from . import TestType


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

    sub_parsers = parser.add_subparsers(
        title="Operation",
        description="Select the operation to perform",
        dest="operation",
        required=True)
    cp = sub_parsers.add_parser(
        "compile", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    cp.add_argument(
        'nmaps', help='numbers of maps to be used for compilation', type=int, nargs="+")

    tp = sub_parsers.add_parser(
        "throughput", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    tp.add_argument(
        'interface', help='local interface to receive the remote attacks', type=str)
    tp.add_argument('ssh_login', help='ssh remote login', type=str)
    tp.add_argument(
        'timeout', help='test duration', type=int)
    tp.add_argument('retrieval_frequencies',
                    help='metric retrieval frequencies', type=float, nargs="+")

    return parser.parse_args().__dict__


def test_swap_compilation(ctr, nmaps, ntimes):
    results = {}
    for test_type in [TestType.COMPILATION_NORMAL, TestType.COMPILATION_SWAP]:
        results[test_type.value] = {}
        for i in [int(x) for x in nmaps]:
            vals = []
            for _ in range(ntimes):
                ctr.create_probe(__package__, "probe", interface="lo",
                                 mode=BPF.XDP, nmaps=i, test_type=test_type)
                p = ctr.get_probe(__package__, "probe")
                print(f"{i} {test_type.value} ... ", end="", flush=True)
                vals.append(p.retrieve())
                del p
                ctr.delete_probe(__package__, "probe")
                print("Finished")
            results[test_type.value][i] = vals
    with open(os.path.join("results", "swap", "results_compilation.json"), "w") as fp:
        json.dump(results, fp, indent=2)


def test_swap_throughput(ctr, interface, ssh_login, frequencies, ntimes, duration):
    results = {}
    for test_type in [TestType.THROUGHPUT_NORMAL, TestType.THROUGHPUT_SWAP]:
        results[test_type.value] = {}
        for i in [float(x) for x in frequencies]:
            vals = []
            for _ in range(ntimes):
                ctr.create_probe(__package__, "probe", interface=interface,
                                 mode=BPF.XDP, flags=XDPFlags.DRV_MODE, test_type=test_type, time_window=i)
                p = ctr.get_probe(__package__, "probe")
                print(f"{i} {test_type.value} ... ", end="", flush=True)
                subprocess.check_call(
                    f'ssh -i /home/{os.getlogin()}/.ssh/id_rsa1 {args["ssh_login"]} "cd MoonGen && \
                        sudo ./build/MoonGen moongen.lua 1 --core 7 --timeout {duration} \
                            --ipsnum 256 --portsnum 97"',
                    shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                vals.append(p.retrieve())
                del p
                ctr.delete_probe(__package__, "probe")
                print("Finished")
            results[test_type.value][i] = vals

    with open(os.path.join("results", "swap", "results_throughput.json"), "w") as fp:
        json.dump(results, fp, indent=2)


if __name__ == '__main__':
    ctr = Controller(log_level=logging.NOTSET)
    ctr.create_plugin(os.path.dirname(__file__), update=True)

    args = _parse_arguments()
    create_dir(os.path.join("results", "swap"))

    if args["operation"] == "throughput":
        test_swap_throughput(
            ctr, args["interface"], args["ssh_login"], args["retrieval_frequencies"], args["ntimes"], args["timeout"])
    else:
        test_swap_compilation(ctr, args["nmaps"], args["ntimes"])
