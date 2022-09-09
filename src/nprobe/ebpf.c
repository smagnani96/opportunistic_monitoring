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

/*Features to be exported*/
struct features {
#ifdef INPUT_SNMP
  uint32_t input_snmp;
#endif
#ifdef OUTPUT_SNMP
  uint32_t output_snmp;
#endif
#ifdef SRC_AS
  uint32_t src_as;
#endif
#ifdef DST_AS
  uint32_t dst_as;
#endif
#ifdef IN_PKTS
  uint64_t in_pkts;
#endif
#ifdef IN_BYTES
  uint64_t in_bytes;
#endif
#ifdef IPV4_SRC_ADDR
  uint32_t ipv4_src_addr;
#endif
#ifdef IPV4_DST_ADDR
  uint32_t ipv4_dst_addr;
#endif
#ifdef PROTOCOL
  uint8_t protocol;
#endif
#ifdef SRC_TOS
  uint8_t src_tos;
#endif
#ifdef L4_SRC_PORT
  uint16_t l4_src_port;
#endif
#ifdef L4_DST_PORT
  uint16_t l4_dst_port;
#endif
#ifdef TCP_FLAGS
  uint16_t tcp_flags;
#endif    
#ifdef FIRST_SWITCHED
  uint64_t first_switched;
#endif
#ifdef LAST_SWITCHED
  uint64_t last_switched;
#endif
};

BPF_TABLE("array", int, struct features, FEATURES_ARRAY, 1);
BPF_TABLE("array", int, u64, PACKETS, 1);

/*Default function called at each packet on interface*/
static __always_inline int handler(struct CTXTYPE *ctx, struct pkt_metadata *md) {
  int zero = 0;
  
  u64 *value = PACKETS.lookup(&zero);
  if(!value) {
    return DROP;
  }
  *value += 1;

  struct features empty = {0};
  struct features *features = FEATURES_ARRAY.lookup_or_try_init(&zero, &empty);
  if(!features) {
    return DROP;
  }

#ifdef INPUT_SNMP
  if(*value == 1) features->input_snmp = 1;
#endif
#ifdef OUTPUT_SNMP
  if(*value == 1) features->output_snmp = 1;
#endif
#ifdef SRC_AS
  if(*value == 1) features->src_as = 1;
#endif
#ifdef DST_AS
  if(*value == 1) features->dst_as = 1;
#endif

#ifdef IN_PKTS
  features->in_pkts +=1;
#endif


#ifdef IN_BYTES
  features->in_bytes += (long) ctx->data_end - (long) ctx->data;
#endif

#ifdef IPV4_SRC_ADDR
  void *data = (void *) (long) ctx->data;
  void *data_end = (void *) (long) ctx->data_end;
  size_t sizes = sizeof(struct eth_hdr);

  /*Parsing L2*/
  struct eth_hdr *ethernet = data;
  if (data + sizes > data_end || ethernet->proto != bpf_htons(ETH_P_IP))
    return DROP;

  /*Parsing L3*/
  struct iphdr *ip = data + sizes;
  if (data + sizes + sizeof(struct iphdr) > data_end || (int) ip->version != 4)
    return DROP;
  
  features->ipv4_src_addr = ip->saddr;

#ifdef IPV4_DST_ADDR
  features->ipv4_dst_addr = ip->daddr;
#endif

#ifdef PROTOCOL
  features->protocol = ip->protocol;
#endif

#ifdef SRC_TOS
  features->src_tos |= ip->tos;
#endif

#ifdef L4_SRC_PORT
  sizes += ip->ihl << 2;
  switch(ip->protocol){
    case IPPROTO_TCP: {
      struct tcphdr *tcp = data + sizes;
      if ((void *) tcp + sizeof(struct tcphdr) > data_end) {
        return DROP;
      }
      features->l4_src_port = tcp->source;
#ifdef L4_DST_PORT
      features->l4_dst_port = tcp->dest;
#endif
#ifdef TCP_FLAGS
      features->tcp_flags |= (tcp->cwr << 7) | (tcp->ece << 6) | (tcp->urg << 5) | (tcp->ack << 4) | (tcp->psh << 3)| (tcp->rst << 2) | (tcp->syn << 1) | tcp->fin;
#endif
      break;
    }
    case IPPROTO_UDP: {
      struct udphdr *udp = data + sizes;
      if ((void *) udp + sizeof(struct udphdr) > data_end) {
        return DROP;
      }
      features->l4_src_port = udp->source;
#ifdef L4_DST_PORT
      features->l4_dst_port = udp->dest;
#endif

      break;
    }
    default: {
      break;
    }
  }

#endif

#ifdef FIRST_SWITCHED
  if (!features->first_switched) {
    uint64_t curr_time = get_time_epoch(ctx);
    features->first_switched = curr_time;
#ifdef LAST_SWITCHED
  features->last_switched = curr_time;
#endif
  }else {
#ifdef LAST_SWITCHED
  features->last_switched = get_time_epoch(ctx);
#endif
  }
#endif

#endif
  
  return DROP;
}