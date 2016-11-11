# Kafka Pack


This pack assumes that you have started Kafka with JMX enabled on port 55555 using the environment variable JMX_PORT.

```
JMX_PORT=55555 \
nohup ~/kafka/bin/kafka-server-start.sh ~/kafka/config/server.properties \
> ~/kafka/kafka.log 2>&1 &
```

If you already have Kafka setup with JMX listening on another port open the kafka.py plugin and edit the following line:

```
JMX_URL = 'service:jmx:rmi:///jndi/rmi://localhost:55555/jmxrmi'
```

Change 55555 to whatever port you have open.
