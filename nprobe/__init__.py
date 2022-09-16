import ctypes as ct
from dataclasses import dataclass
from typing import ClassVar, OrderedDict

from dechainy.plugins import Probe


@dataclass
class Nprobe(Probe):
    nfeatures: int = 0

    NPROBE_FEATURES: ClassVar[OrderedDict] = OrderedDict([
        ("input_snmp", ct.c_uint32),
        ("output_snmp", ct.c_uint32),
        ("src_as", ct.c_uint32),
        ("dst_as", ct.c_uint32),
        ("in_pkts", ct.c_uint64),
        ("in_bytes", ct.c_uint64),
        ("ipv4_src_addr", ct.c_uint32),
        ("ipv4_dst_addr", ct.c_uint32),
        ("protocol", ct.c_uint8),
        ("src_tos", ct.c_uint8),
        ("l4_src_port", ct.c_uint16),
        ("l4_dst_port", ct.c_uint16),
        ("tcp_flags", ct.c_uint16),
        ("first_switched", ct.c_uint64),
        ("last_switched", ct.c_uint64)
    ])

    def __post_init__(self):
        self.ingress.required = True
        self.ingress.cflags = [
            "-D{}=1".format(x.upper()) for x in list(Nprobe.NPROBE_FEATURES.keys())[:self.nfeatures]]
        super().__post_init__(path=__file__)

    def retrieve(self):
        return self["INGRESS"]["PACKETS"][0].value
