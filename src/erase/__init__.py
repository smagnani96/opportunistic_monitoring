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

###############################################################
# NB: Need the Docker image to be compiled with "ml" argument #
###############################################################
from dataclasses import dataclass
from enum import Enum
import time
import ctypes as ct

from dechainy.plugins import Probe

class MapType(Enum):
    HASH = "HASH"
    ARRAY = "ARRAY"
    QUEUE = "QUEUE"


@dataclass
class Erase(Probe):
    n_entries: int = 0
    map_type: MapType = MapType.HASH

    def __post_init__(self):
        self.ingress.required = True
        self.ingress.cflags = ["-D{}=1".format(self.map_type.value), "-DN_ENTRIES={}".format(self.n_entries)]
        super().__post_init__(path=__file__)

    def _populate(self):
        t = time.time_ns()
        if self.map_type.value == MapType.QUEUE.value:
            for i in range(self.n_entries):
                tmp = ct.c_int32(i)
                self["INGRESS"]["TABLE"].push(tmp)
        else:
            for i in range(self.n_entries):
                tmp = ct.c_int32(i)
                self["INGRESS"]["TABLE"][tmp] = tmp
        return time.time_ns() - t

    def _populate_batch(self):
        t = time.time_ns()
        if self.map_type.value == MapType.QUEUE.value:
            return 0
        else:
            _, keys, values = self["INGRESS"]["TABLE"]._alloc_keys_values(alloc_k=True, alloc_v=True, count=self.n_entries)
            self["INGRESS"]["TABLE"].items_update_batch(keys, values)
        return time.time_ns() - t

    def _batch_erase(self):
        t = time.time_ns()
        if self.map_type.value == "ARRAY":
            _, keys, values = self["INGRESS"]["TABLE"]._alloc_keys_values(alloc_k=True, alloc_v=True, count=self.n_entries)
            self["INGRESS"]["TABLE"].items_update_batch(keys, values)
        elif self.map_type.value == "HASH":
            self["INGRESS"]["TABLE"].items_delete_batch()
        elif self.map_type.value == "QUEUE":
            return 0
        return time.time_ns() - t
    
    def _normal_erase(self):
        t = time.time_ns()
        if self.map_type.value == MapType.QUEUE.value:
            for _ in range(self.n_entries):
                self["INGRESS"]["TABLE"].pop()
        else:
            for i in range(self.n_entries):
                del self["INGRESS"]["TABLE"][ct.c_int32(i)]
        return time.time_ns() - t

    def retrieve(self):
        t1 = self._populate()
        t2 = self._normal_erase()
        t3 = self._populate_batch()
        t4 = self._batch_erase()
        return t1, t2, t3, t4


