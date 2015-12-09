# Couchbase Pack

You will need to edit the `couchbase.py` plugin to set some variables specific to your Couchbase servers.

```
# settings

USER = ''
PASSWORD = ''
URL = 'http://localhost:8091'
```

Specify the user and password that you set during installation of Couchbase. The dashboard will then display basic
cluster metrics.

To create bucket specific dashboards the metrics are available under `couchbase.bucket.<bucket name>` in the metric
browser.