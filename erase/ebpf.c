// Copyright 2021 Opportunistic Monitoring
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


#if defined(HASH)
BPF_TABLE("hash", int, int, TABLE, N_ENTRIES);
#elif defined(ARRAY)
BPF_TABLE("array", int, int, TABLE, N_ENTRIES);
#elif defined(QUEUE)
BPF_QUEUESTACK("queue", TABLE, int, N_ENTRIES, 0);
#endif

/*Default function called at each packet on interface*/
static __always_inline int handler(struct CTXTYPE *ctx, struct pkt_metadata *md) {
    return PASS;
}