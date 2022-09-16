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

import os
import threading
import time
###############################################################
# NB: Need the Docker image to be compiled with "ml" argument #
###############################################################
from dataclasses import dataclass
from enum import Enum

from dechainy.plugins import Probe


class TestType(Enum):
    COMPILATION_NORMAL = "COMPILATION_NORMAL"
    COMPILATION_SWAP = "COMPILATION_SWAP"
    THROUGHPUT_NORMAL = "THROUGHPUT_NORMAL"
    THROUGHPUT_SWAP = "THROUGHPUT_SWAP"


@dataclass
class Swap(Probe):
    nmaps: int = 0
    test_type: TestType = TestType.COMPILATION_NORMAL
    time_window: float = 0.0
    comp_time: float = 0.0
    stopped: bool = False

    def __post_init__(self):
        self.ingress.required = True
        with open(os.path.join(os.path.dirname(__file__), "ebpf.c"), "r") as fp:
            self.ingress.code = fp.read()
        if self.test_type.value in [TestType.COMPILATION_NORMAL.value, TestType.COMPILATION_SWAP.value]:
            self.ingress.code = self.ingress.code.replace("DECL_PLACEHOLDER", '\n'.join(
                ['BPF_TABLE("array", int, int, A{}, 1){};'.format(
                    i, "__attributes__((SWAP))" if self.test_type.value == TestType.COMPILATION_SWAP.value else "")
                 for i in range(self.nmaps)]))
        else:
            self.ingress.code = self.ingress.code.replace(
                "DECL_PLACEHOLDER", 'BPF_TABLE("array", int, u64, PACKETS, 1){};'.format(
                    "__attributes__((SWAP))" if self.test_type.value in
                    [TestType.COMPILATION_SWAP.value, TestType.THROUGHPUT_SWAP.value] else ""))
        with open(os.path.join(os.path.dirname(__file__), "ingress.c"), "w") as fp:
            fp.write(self.ingress.code)
        self.ingress.cflags = ["-D{}=1".format(self.test_type.value)]
        self.comp_time = time.time_ns()
        super().__post_init__(path=__file__)
        self.comp_time = time.time_ns() - self.comp_time
        if self.test_type.value == TestType.THROUGHPUT_SWAP.value:
            self.t = threading.Thread(target=self.throughput_swap)
            self.t.start()

    def throughput_swap(self):
        while not self.stopped:
            time.sleep(self.time_window)
            if not self.stopped:
                self["ingress"].trigger_read()
            else:
                return

    def retrieve(self):
        self.stopped = True
        if self.test_type.value in [TestType.THROUGHPUT_NORMAL.value, TestType.THROUGHPUT_SWAP.value]:
            ret = self["ingress"]["PACKETS"][0]  # retrieving metric
            if self.test_type.value == TestType.THROUGHPUT_SWAP.value:
                self.t.join()
                self["ingress"].trigger_read()
                ret.value += self["ingress"]["PACKETS"][0].value
            return ret.value
        elif self.test_type.value == TestType.COMPILATION_SWAP.value:
            return self.comp_time
        elif self.test_type.value == TestType.COMPILATION_NORMAL.value:
            return self.comp_time
