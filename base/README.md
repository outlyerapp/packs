# Base Pack

The base pack collects operating system metrics for cpu, disk, network and memory.

## Known Issues

If disk performance counters are missing on Windows agents you may need to turn on disk stats by running `diskperf -y`

## Extended Base Pack

Metrics for each filesystem and network interface are now reported by the 
Extended Base Pack. Customers who need those metrics should manually install
the Extended Base Pack.

