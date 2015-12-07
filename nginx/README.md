# Nginx


This pack deploys a plugin called nginx.py that reads through an access log file and extracts a count of http status codes.

To enable calculation of response times you need to enable more logging in Nginx. Add this to `nginx.conf` in the http block:

```
log_format timed_combined '$remote_addr - $remote_user [$time_local] '
                          '"$request" $status $body_bytes_sent '
                          '"$http_referer" "$http_user_agent" '
                          '"$request_time"';
```

Then in your log directives use time_combined. For example:

```
access_log /var/log/nginx/access.log timed_combined;
```

You also need to ensure that the LOGFILE variable in the plugins matches the path to your access log file. By default this
is set to `/var/log/nginx/access.log` so if that is different then edit the plugin to match the correct path.

