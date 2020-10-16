CONTIKI_PROJECT = node coordinator
all: $(CONTIKI_PROJECT)

TARGET = zoul
BOARD = remote-revb

ROOT = ..
CONTIKI = $(ROOT)/contiki-ng

include $(CONTIKI)/Makefile.dir-variables
MODULES += $(CONTIKI_NG_SERVICES_DIR)/shell
MODULES += $(ROOT)/sx127x/src # SX127X Driver
MODULES += $(ROOT)/src/include
CFLAGS += -I/usr/arm-none-eabi/include

 # force Orchestra from command line
MAKE_WITH_ORCHESTRA ?= 0
# force Security from command line
MAKE_WITH_SECURITY ?= 0
 # print #routes periodically, used for regression tests
MAKE_WITH_PERIODIC_ROUTES_PRINT ?= 0
# RPL storing mode?
MAKE_WITH_STORING_ROUTING ?= 0
# Orchestra link-based rule? (Works only if Orchestra & storing mode routing is enabled)
MAKE_WITH_LINK_BASED_ORCHESTRA ?= 0

ifeq ($(MAKE_WITH_TSCH),1)
  MAKE_MAC = MAKE_MAC_TSCH
  MAKE_ROUTING = MAKE_ROUTING_RPL_LITE
else
  MAKE_MAC = MAKE_MAC_NULLMAC
  MAKE_NET = MAKE_NET_NULLNET
endif

ifeq ($(MAKE_WITH_ORCHESTRA),1)
  MODULES += $(CONTIKI_NG_SERVICES_DIR)/orchestra

  ifeq ($(MAKE_WITH_STORING_ROUTING),1)
    ifeq ($(MAKE_WITH_LINK_BASED_ORCHESTRA),1)
      # enable the `link_based` rule
      CFLAGS += -DORCHESTRA_CONF_RULES="{&eb_per_time_source,&unicast_per_neighbor_link_based,&default_common}"
    else
      # enable the `rpl_storing` rule
      CFLAGS += -DORCHESTRA_CONF_RULES="{&eb_per_time_source,&unicast_per_neighbor_rpl_storing,&default_common}"
    endif
  else
    ifeq ($(MAKE_WITH_LINK_BASED_ORCHESTRA),1)
      $(error "Inconsistent configuration")
    endif
  endif
endif

# ifeq ($(MAKE_WITH_STORING_ROUTING),1)
#   MAKE_ROUTING = MAKE_ROUTING_RPL_CLASSIC
#   CFLAGS += -DRPL_CONF_MOP=RPL_MOP_STORING_NO_MULTICAST
# endif

ifeq ($(MAKE_WITH_SECURITY),1)
CFLAGS += -DWITH_SECURITY=1
endif

ifeq ($(MAKE_WITH_PERIODIC_ROUTES_PRINT),1)
CFLAGS += -DWITH_PERIODIC_ROUTES_PRINT=1
endif

ifeq ($(MAKE_AS_COORDINATOR),1)
CFLAGS += -DISCOORDINATOR=1
endif 

include $(CONTIKI)/Makefile.include
