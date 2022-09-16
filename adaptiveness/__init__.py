import ctypes as ct
import math
import os
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, OrderedDict

from dechainy.plugins import Probe


class AdaptivenessType(Enum):
    FULLY = "FULLY"
    TRADITIONAL = "TRADITIONAL"


@dataclass
class Adaptiveness(Probe):
    nfeatures: int = 0
    adaptiveness_type: AdaptivenessType = AdaptivenessType.FULLY

    SUPPORTED_FEATURES: ClassVar[OrderedDict] = OrderedDict(
        [(f"F_{i}", ct.c_uint32) for i in range(1, 101)])

    def __post_init__(self):
        self.ingress.required = True
        states = [0, 0, 0, 0]

        with open(os.path.join(os.path.dirname(__file__), "ebpf.c"), "r") as fp:
            self.ingress.code = fp.read()

        decl_code = fun_code = ""

        if self.adaptiveness_type.value == AdaptivenessType.TRADITIONAL.value:
            for i, k in enumerate(Adaptiveness.SUPPORTED_FEATURES):
                index = int(i/32)
                ii = i % 32
                decl_code += f"u32 {k};\n\t"
                fun_code += f"if(s->s[{index}] & (1 << {ii})) features->{k} += 1;\n\t"
                if i < self.nfeatures:
                    states[index] = states[index] | (1 << ii)
        elif self.adaptiveness_type.value == AdaptivenessType.FULLY.value:
            for i, k in enumerate(Adaptiveness.SUPPORTED_FEATURES):
                if i == self.nfeatures:
                    break
                decl_code += f"u32 {k};\n\t"
                fun_code += f"features->{k} += 1;\n\t"

        self.ingress.code = self.ingress.code.replace(
            "F_DECL_PLACEHOLDER", decl_code)
        self.ingress.code = self.ingress.code.replace(
            "F_FUN_PLACEHOLDER", fun_code)
        with open(os.path.join(os.path.dirname(__file__), "ingress.c"), "w") as fp:
            fp.write(self.ingress.code)

        self.ingress.cflags += ["-D{}=1".format(self.adaptiveness_type.value), "-DDIMENSION={}".format(
            math.ceil(len(Adaptiveness.SUPPORTED_FEATURES)/32))]

        super().__post_init__(path=__file__)

        if self.adaptiveness_type.value == AdaptivenessType.TRADITIONAL.value:
            tmp = self["ingress"]["APP_STATE"][0]
            for i in range(len(states)):
                tmp.s[i] = ct.c_uint32(states[i])
            self["ingress"]["APP_STATE"][0] = tmp

    def retrieve(self):
        return self["INGRESS"]["PACKETS"][0].value
