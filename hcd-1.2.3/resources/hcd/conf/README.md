HCD Configuration
=================

These files configure HCD.
Please note that since HCD is based on Cassandra, to a large extent the
configuration for Cassandra will govern the behavior of HCD.
The Cassandra configuration of HCD is located in the `resources/cassandra/conf`
directory of the HCD installation.
The primary configuration file for Cassandra is [`cassandra.yaml`](cassandra.yaml),
for which you can refer to the [Cassandra documentation](https://cassandra.apache.org/doc/4.0/cassandra/configuration/cass_yaml_file.html).

Configuration for features of HCD that extend beyond Cassandra is primarily
governed by the [`hcd.yaml`](hcd.yaml) file.

The configuration files have been pre-configured with default values that should work for most use cases.
