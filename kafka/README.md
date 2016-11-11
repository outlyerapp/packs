Start Kafka with JMX enabled on port 55555 using the environment variable JMX_PORT

```
JMX_PORT=55555 nohup ~/kafka/bin/kafka-server-start.sh ~/kafka/config/server.properties > ~/kafka/kafka.log 2>&1 &
```
