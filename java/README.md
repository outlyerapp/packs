# Java Pack

*WARNING: This pack will only work with the latest version of the Dataloop.IO Agent, Version 1.3.11-1 or above.*

The plugin for this pack monitors java processes via JMX. You will need to set the JMX
URL to connect to the java process to pull out all the internal java metrics. **You will need
Java 1.5 or above installed for this integration to work**

To set the JMX URL edit the `java.py` plugin and change:

```
JMX_URL = 'service:jmx:rmi:///jndi/rmi://localhost:9090/jmxrmi'
JMX_USERNAME = ''
JMX_PASSWORD = ''
```

*NOTE: You only need to set the username and password if authentication is enabled for your JMX URL*

If you don't know the JMX_URL you can use the jmxquery.jar to list all the local JVM's with their connection
URLs by running the following command on your Linux server:

```
java -jar /opt/dataloop/embedded/lib/jmxquery.jar -list jvms
```

*NOTE: This will require you to run with a local JDK installed, replacing 'java' with the full path to the JDK if needed*

You can also modify what JVM metrics are collected by modifying the METRICS list. By default all the main standard metrics are collected.

