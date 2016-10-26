# Java Pack

The plugin for this pack monitors java processes via JMX. You will need to set the JMX
URL to connect to the java process to pull out all the internal java metrics.

To set the JMX URL edit the `java.py` plugin and change:

```
JMX_URL = 'service:jmx:rmi:///jndi/rmi://localhost:9090/jmxrmi'
```

If you don't know the JMX_URL you can use the jmxquery.jar to list all the local JVM's with their connection
URLs by running the following command on your Linux server:

```
java -jar /opt/dataloop/embedded/lib/jmxquery.jar -list jvms
```

*NOTE: This will require you to run with a local JDK installed, replacing 'java' with the full path to the JDK if needed*

You can also modify what JVM metrics are collected by modifying the METRICS list. By default all the main standard metrics are collected.

