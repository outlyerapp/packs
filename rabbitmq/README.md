# RabbitMQ Pack

This pack requires the RabbitMQ management plugin to be enabled on your servers. You can read how to do that here:

https://www.rabbitmq.com/management.html

Once enabled you need to edit the `rabbitmq.py` plugin in Dataloop.

```
# Settings
HOST = "localhost"
USERNAME = "guest"
PASSWORD = "guest"
PORT = "15672"
PROTO = "http"

QUEUE_STATS = False
EXCHANGE_STATS = False
VERIFY_SSL = True
```

By default only overview statistics are collected. If you would like to collect per queue or per exchange metrics
then set `QUEUE_STATS` and `EXCHANGE_STATS` to `True`. Be warned that each queue will return approximately 32 metric
paths which may be a problem if you have thousands of queues.