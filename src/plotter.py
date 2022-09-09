# Copyright 2021 Opportunistic Monitoring
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import ctypes
import os
import json
import argparse
import multiprocessing

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from typing import Dict
from swap import TestType

from nprobe import Nprobe
from erase import MapType
from adaptiveness import Adaptiveness, AdaptivenessType
from bcc import BPF

plt.style.use(['science', 'ieee'])
plt.rcParams['xtick.minor.size'] = 0
plt.rcParams['ytick.minor.size'] = 0

SIZE = 10**6
DURATION = 10 * SIZE

def plot_swap_overhead():
    with open(os.path.join("results", "swap", "results_compilation.json"), "r") as fp1, \
        open(os.path.join("results", "swap", "results_throughput.json"), "r") as fp2:
        compilation = json.load(fp1)
        throughput = json.load(fp2)
    
    ticks = list(range(1, len(compilation[TestType.COMPILATION_NORMAL.value])+1))

    fig, ax = plt.subplots()
    fig1, ax1 = plt.subplots()
    for i, (tt, name) in enumerate([(TestType.COMPILATION_NORMAL.value, "Baseline"), (TestType.COMPILATION_SWAP.value, "Atomic Retrieval")]):
        y = [np.array(v)/10**9 for v in compilation[tt].values()]
        y_ci = [1.96 * np.std(k)/(len(k)**(1/2)) for k in y]
        y = [np.mean(k) for k in y]
        ax.bar([(k - 0.15) if i == 0 else (k + 0.15) for k in ticks], y, yerr=y_ci, width=0.3, label=name)
        ax.set_xticklabels(list(compilation[tt].keys()) )
    ax.set_xticks(ticks)
    ax.set_ylim(top=1.4)
    _do_set_and_store(fig, ax, 'N° maps', 'Time (s)', os.path.join("results", "swap", "chartswapcompilation"))

    ticks = list(range(1, len(throughput[TestType.THROUGHPUT_NORMAL.value])+1))
    for i, (tt, name) in enumerate([(TestType.THROUGHPUT_NORMAL.value, "Baseline"), (TestType.THROUGHPUT_SWAP.value, "Atomic Retrieval")]):
        y = [np.array(v)/DURATION for v in throughput[tt].values()]
        y_ci = [1.96 * np.std(k)/(len(k)**(1/2)) for k in y]
        y = [np.mean(k) for k in y]
        ax1.bar([(k - 0.15) if i == 0 else (k + 0.15) for k in ticks], y, yerr=y_ci, width=0.3, label=name)
        ax1.set_xticklabels(list(throughput[tt].keys()))
    ax1.set_xticks(ticks)
    ax1.set_ylim(bottom=30, top=34.5)
    _do_set_and_store(fig1, ax1, 'Swap Frequency (s)', 'Throughput (Mpps)', os.path.join("results", "swap", "chartswapthroughput"))



def plot_adaptiveness_comp():
    with open(os.path.join("results", "adaptiveness", "results.json"), "r") as fp1:
        adaptiveness = json.load(fp1)
    
    ticks = list(range(1, 1+ len(adaptiveness[str(BPF.XDP)][AdaptivenessType.FULLY.value])))
    
    non_ad_cost = 25000/10**6* sum(ctypes.sizeof(v) for v in Adaptiveness.SUPPORTED_FEATURES.values())
    ad_cost = [25000/10**6*sum(ctypes.sizeof(v) for i, v in enumerate(Adaptiveness.SUPPORTED_FEATURES.values()) if i < int(ii) ) for ii in adaptiveness[str(BPF.XDP)][AdaptivenessType.FULLY.value]]
    fig0, ax0 = plt.subplots()
    ax0.bar([k - 0.25 for k in ticks], ad_cost, width=0.25, label="Fully-Adaptive")
    ax0.bar(ticks, [non_ad_cost]*len(ticks), width=0.25,  label="Non-Adaptive")
    ax0.bar([k + 0.25 for k in ticks], [non_ad_cost]*len(ticks), width=0.25,  label="Adaptive")
    ax0.set_xticks(ticks)
    ax0.set_xticklabels(list(adaptiveness[str(BPF.XDP)][AdaptivenessType.FULLY.value].keys()) )
    ax0.set_ylim(top=non_ad_cost + 4)    
    _do_set_and_store(fig0, ax0, 'N° Features', 'Memory (MB)', os.path.join("results", "adaptiveness", "chartadaptivenessmemory"))

    fig, ax = plt.subplots()
    ss = -0.4
    for mode, mname in [(BPF.XDP, "XDP"), (BPF.SCHED_CLS, "TC")]:
        for at, name in [(AdaptivenessType.FULLY.value, "Fully-Adaptive"), ("NON", "Non-Adaptive"), (AdaptivenessType.TRADITIONAL.value, "Adaptive")]:
            fict = False
            if at == "NON":
                at = AdaptivenessType.FULLY.value
                fict = True
            vals = [np.array(x)/DURATION for x in adaptiveness[str(mode)][at].values()]
            ci = [1.96 * np.std(x)/(len(x)**(1/2)) for x in vals]
            vals = [np.mean(x) for x in vals]
            vals = vals if not fict else [vals[-1]]*len(vals)
            color = None
            if mode == BPF.SCHED_CLS and fict:
                color = "orange"
            elif mode == BPF.SCHED_CLS and at == AdaptivenessType.TRADITIONAL.value:
                color = "darkmagenta"
            ax.bar([k + ss for k in ticks], vals, yerr=ci, label="{} {}".format(name, mname), width=0.2, color=color)
            ss += 0.15
    ax.set_xticklabels(list(adaptiveness[str(BPF.XDP)][AdaptivenessType.FULLY.value].keys()) )
    ax.set_xticks(ticks)
    ax.set_ylim(top=43)
    _do_set_and_store(fig, ax, 'N° Features', 'Throughput (Mpps)', os.path.join("results", "adaptiveness", "chartadaptivenessthroughput"))
    

def plot_erase():
    with open(os.path.join("results", "erase", "results.json"), "r") as fp1:
        erase = json.load(fp1)

    ticks = list(range(len(erase[MapType.HASH.value])))
    for mt in MapType:
        fig, ax = plt.subplots()
        for i, name, ss in [(0, "Populate Normal", -0.3), (1, "Erase Normal", -0.1), (2, "Populate Batch", +0.1), (3, "Erase Batch", +0.3)]:
            y = [[vv[i] for vv in v] for v in erase[mt.value].values()]
            y = [np.array(v)/10**6 for v in y]
            y_ci = [1.96 * np.std(k)/(len(k)**(1/2)) for k in y]
            y = [np.mean(k) for k in y]
            ax.bar([k+ss for k in ticks], y, yerr=y_ci, width=0.2, label=name)
            ax.set_xticklabels(list(erase[mt.value].keys()) )

        ax.set_xticks(ticks)
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(mticker.StrMethodFormatter('{x:.2f}'))

        _do_set_and_store(fig, ax, 'N° Entries', 'Time (ms)', os.path.join("results", "erase", "charterase{}".format(mt.value)))

        
def plot_netflow_comp():
    with open(os.path.join("results", "nprobe", "results.json"), "r") as fp1:
        nprobe = json.load(fp1)

    real_nprobe = []
    for f in [x for x in os.listdir(os.path.join("results", "nprobe")) if ".flows" in x]:
        tmp = 0
        with open(os.path.join("results", "nprobe", f), "r") as fp:
            for line in fp.readlines()[1:]:
                tmp += int(line.split("|")[4])
        real_nprobe.append(tmp)
    real_nprobe = np.mean(np.array(real_nprobe)) / DURATION
    fig, ax = plt.subplots()

    ticks = list(range(1, 1+ len(Nprobe.NPROBE_FEATURES)))
    ax.bar([k - 0.3 for k in ticks], [real_nprobe]*len(ticks), label="nProbe", width=0.3)
    for mode, name, ss in [(BPF.SCHED_CLS, "TC", 0), (BPF.XDP, "XDP", 0.3)]:
        vals = [np.array(x)/DURATION for x in nprobe[str(mode)].values()]
        ci = [1.96 * np.std(x)/(len(x)**(1/2)) for x in vals]
        vals = [np.mean(x) for x in vals]
        ax.bar([k + ss for k in ticks], vals, yerr=ci, label="Fully-Adaptive {}".format(name), width=0.3)
    ax.set_xticks(ticks)
    _do_set_and_store(fig, ax, 'Feature ID', 'Throughput (Mpps)', os.path.join("results", "nprobe", "chartnprobethroughput"))
    
    netflow_cost = 25000/10**6* sum(ctypes.sizeof(v) for v in Nprobe.NPROBE_FEATURES.values())
    netflow_ad_cost = [25000/10**6*sum(ctypes.sizeof(v) for i, v in enumerate(Nprobe.NPROBE_FEATURES.values()) if i < ii ) for ii in ticks]
    fig0, ax0 = plt.subplots()
    ax0.bar([k - 0.15 for k in ticks], [netflow_cost]*len(ticks), width=0.3,  label="nProbe")
    ax0.bar([k + 0.15 for k in ticks], netflow_ad_cost, width=0.3, label="Fully-Adaptive")
    ax0.set_xticks(ticks)
    ax0.set_ylim(top=netflow_cost + 0.5)    
    _do_set_and_store(fig0, ax0, 'Feature ID', 'Memory (MB)', os.path.join("results", "nprobe", "chartnprobememory"))


def _do_set_and_store(fig, ax, xlabel, ylabel, path):
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.tick_params(bottom=False, top=False)
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{path}.pdf")
    plt.close(fig)


def _parse_arguments() -> Dict[str, any]:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-n', '--netflow', help='netflow plot', action='store_true')
    parser.add_argument(
        '-w', '--swap', help='swap plot', action='store_true')
    parser.add_argument(
        '-a', '--adaptiveness', help='adaptiveness plot', action='store_true')
    parser.add_argument(
        '-e', '--erase', help='erase plot', action='store_true')
    args = parser.parse_args().__dict__
    if not args["netflow"] and not args["swap"] and not args["adaptiveness"] and not args["erase"]:
        args["netflow"] = True
        args["swap"] = True
        args["adaptiveness"] = True
        args["erase"] = True
    return args


def main():
    args = _parse_arguments()

    with multiprocessing.Pool() as pool:
        tasks = []
        if args["netflow"]:
            tasks.append(pool.apply_async(plot_netflow_comp))
        if args["swap"]:
            tasks.append(pool.apply_async(plot_swap_overhead))
        if args["adaptiveness"]:
            tasks.append(pool.apply_async(plot_adaptiveness_comp))
        if args["erase"]:
            tasks.append(pool.apply_async(plot_erase))
        for t in tasks:
            t.get()


if __name__ == '__main__':
    main()
