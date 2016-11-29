# HAProxy Pack

Add the following line to haproxy.cfg under the global section (and restart haproxy):

```
stats socket /var/run/haproxy.sock user dataloop group root level operator
```

The plugin will collect additional metrics that you can use on dashboards & alerts from HAProxy 1.5 and above such as
qtime, ctime, rtime and ttime.