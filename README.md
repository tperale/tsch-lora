# Contiki LoRa TSCH Project

Repository containing exemple of usage of TSCH with LoRa in contiki-ng.

This repository is based on a [modified version of contiki-ng](https://github.com/tperale/contiki-ng) 
that allow to use longer timeslot with TSCH.

## Usage

In the `/src` folder you can use the `compile.sh` script.

```
> ./compile.sh 0 # compile the coordinator
> ./compile.sh 1 # compile the joining node
```

## Command line settings

The following command line options are available:
* `MAKE_WITH_ORCHESTRA` - use the Contiki-NG Orchestra scheduler.
* `MAKE_WITH_SECURITY` - enable link-layer security from the IEEE 802.15.4 standard.
* `MAKE_WITH_PERIODIC_ROUTES_PRINT` -  print routes periodically. Useful for testing and debugging.
* `MAKE_WITH_STORING_ROUTING` - use storing mode of the RPL routing protocol.
* `MAKE_WITH_LINK_BASED_ORCHESTRA` - use the link-based rule of the Orchestra shheduler. This requires that both Orchestra and storing mode routing are enabled.
