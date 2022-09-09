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

#ifdef TRADITIONAL
struct state {
  uint s[DIMENSION];
};
BPF_TABLE("array", int, struct state, APP_STATE, 1);
#endif

/*Features to be exported*/
struct features {
F_DECL_PLACEHOLDER
};

BPF_TABLE("array", int, u64, PACKETS, 1);
BPF_TABLE("array", int, struct features, FEATURES_ARRAY, 1);

/*Default function called at each packet on interface*/
static __always_inline int handler(struct CTXTYPE *ctx, struct pkt_metadata *md) {
  int zero = 0;
  
  u64 *value = PACKETS.lookup(&zero);
  if(!value) {
    return DROP;
  }
  *value += 1;

#ifdef TRADITIONAL
  struct state *s = APP_STATE.lookup(&zero);
  if (!s) {
    return DROP;
  }
#endif

  struct features empty = {};
  struct features *features = FEATURES_ARRAY.lookup_or_try_init(&zero, &empty);
  if(!features) {
    return DROP;
  }

F_FUN_PLACEHOLDER

  return DROP;
}