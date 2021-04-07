/*
 * Copyright (c) 2015, SICS Swedish ICT.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the Institute nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE INSTITUTE AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE INSTITUTE OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 */
/**
 * \file
 *         A RPL+TSCH node able to act as either a simple node (6ln),
 *         DAG Root (6dr) or DAG Root with security (6dr-sec)
 *         Press use button at startup to configure.
 *
 * \author Simon Duquennoy <simonduq@sics.se>
 */

#include "contiki.h"
#include "custom_commands.h"
#include "net/ipv6/uip-ds6-route.h"
#include "net/ipv6/uip-sr.h"
#include "net/mac/tsch/tsch.h"
#include "net/routing/routing.h"
#include "random.h"
#include "sx1272.h"
#include "sys/energest.h"
#include "sys/log.h"
#include "sys/node-id.h"
#include "tsch/tsch-schedule.h"

#define DEBUG DEBUG_PRINT
#include "net/ipv6/uip-debug.h"

/*---------------------------------------------------------------------------*/
#include "net/ipv6/simple-udp.h"

#define LOG_MODULE "App"
#define LOG_LEVEL LOG_LEVEL_INFO

#define WITH_SERVER_REPLY 1
#define UDP_CLIENT_PORT 8765
#define UDP_SERVER_PORT 5678

#define SEND_INTERVAL (10 * CLOCK_SECOND)

PROCESS(node_process, "RPL Node");
AUTOSTART_PROCESSES(&node_process);

#if MAC_CONF_WITH_TSCH
static struct simple_udp_connection udp_conn;
/*---------------------------------------------------------------------------*/
static linkaddr_t node_1_address = {
    {0x00, 0x12, 0x4b, 0x00, 0x14, 0xd5, 0x2d, 0xbc}};
static linkaddr_t node_2_address = {
    {0x00, 0x12, 0x4b, 0x00, 0x14, 0xb5, 0xef, 0x0f}};
void tsch_schedule_custom(void) {
  struct tsch_slotframe *sf_custom;
  /* First, empty current schedule */
  tsch_schedule_remove_all_slotframes();
  /* Build 6TiSCH minimal schedule.
   * We pick a slotframe length of TSCH_SCHEDULE_DEFAULT_LENGTH */
  sf_custom = tsch_schedule_add_slotframe(0, TSCH_SCHEDULE_DEFAULT_LENGTH);
  /* Add a single Tx|Rx|Shared slot using broadcast address (i.e. usable for
   * unicast and broadcast). We set the link type to advertising, which is not
   * compliant with 6TiSCH minimal schedule but is required according to
   * 802.15.4e if also used for EB transmission.
   * Timeslot: 0, channel offset: 0. */
  tsch_schedule_add_link(sf_custom,
                         LINK_OPTION_RX | LINK_OPTION_TX | LINK_OPTION_SHARED |
                             LINK_OPTION_TIME_KEEPING,
                         LINK_TYPE_ADVERTISING, &tsch_broadcast_address, 0, 0,
                         0);

  if (linkaddr_node_addr.u8[7] == node_1_address.u8[7]) {
    tsch_schedule_add_link(sf_custom, LINK_OPTION_RX, LINK_TYPE_NORMAL,
                           &node_2_address, 1, 0, 0);
    tsch_schedule_add_link(sf_custom, LINK_OPTION_TX, LINK_TYPE_NORMAL,
                           &node_2_address, 2, 0, 0);
  } else if (linkaddr_node_addr.u8[7] == node_2_address.u8[7]) {
    tsch_schedule_add_link(sf_custom, LINK_OPTION_TX, LINK_TYPE_NORMAL,
                           &node_1_address, 1, 0, 0);
    tsch_schedule_add_link(sf_custom, LINK_OPTION_RX, LINK_TYPE_NORMAL,
                           &node_1_address, 2, 0, 0);
  }
}
/*---------------------------------------------------------------------------*/
static void udp_rx_callback(struct simple_udp_connection *c,
                            const uip_ipaddr_t *sender_addr,
                            uint16_t sender_port,
                            const uip_ipaddr_t *receiver_addr,
                            uint16_t receiver_port, const uint8_t *data,
                            uint16_t datalen) {

  LOG_INFO("Received response '%.*s' from ", datalen, (char *)data);
  LOG_INFO_6ADDR(sender_addr);
#if LLSEC802154_CONF_ENABLED
  LOG_INFO_(" LLSEC LV:%d", uipbuf_get_attr(UIPBUF_ATTR_LLSEC_LEVEL));
#endif
  LOG_INFO_("\n");
}
#endif
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(node_process, ev, data) {
  PROCESS_BEGIN();

  shell_custom_init();

#if MAC_CONF_WITH_TSCH
  static unsigned count;
  static char str[32];
  static struct etimer periodic_timer;
  uip_ipaddr_t dest_ipaddr;

  tsch_schedule_custom();

  NETSTACK_MAC.on();

  /* Initialize UDP connection */
  simple_udp_register(&udp_conn, UDP_CLIENT_PORT, NULL, UDP_SERVER_PORT,
                      udp_rx_callback);

  etimer_set(&periodic_timer, random_rand() % SEND_INTERVAL);
  while (1) {
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&periodic_timer));

    if (NETSTACK_ROUTING.node_is_reachable() &&
        NETSTACK_ROUTING.get_root_ipaddr(&dest_ipaddr)) {
      /* Send to DAG root */
      LOG_INFO("Sending request %u to ", count);
      LOG_INFO_6ADDR(&dest_ipaddr);
      LOG_INFO_("\n");
      snprintf(str, sizeof(str), "hello %d", count);
      simple_udp_sendto(&udp_conn, str, strlen(str), &dest_ipaddr);
      count++;
    } else {
      LOG_INFO("Not reachable yet\n");
    }

    /* Add some jitter */
    etimer_set(&periodic_timer, SEND_INTERVAL - CLOCK_SECOND +
                                    (random_rand() % (2 * CLOCK_SECOND)));
  }
#endif

#if WITH_PERIODIC_ROUTES_PRINT
  {
    static struct etimer et;
    /* Print out routing tables every minute */
    etimer_set(&et, CLOCK_SECOND * 60);
    while (1) {
/* Used for non-regression testing */
#if (UIP_MAX_ROUTES != 0)
      PRINTF("Routing entries: %u\n", uip_ds6_route_num_routes());
#endif
#if (UIP_SR_LINK_NUM != 0)
      PRINTF("Routing links: %u\n", uip_sr_num_nodes());
#endif
      PROCESS_YIELD_UNTIL(etimer_expired(&et));
      etimer_reset(&et);
    }
  }
#endif /* WITH_PERIODIC_ROUTES_PRINT */

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
