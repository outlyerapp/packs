# Apache2 Pack


This pack deploys a plugin called apache2.py that queries '/server-status' from the Apache module [mod_status](https://httpd.apache.org/docs/2.4/mod/mod_status.html)


## Configure mod_status

Load the module in your Apache http.conf file:

```
LoadModule status_module modules/mod_status.so
```

Enable access to server status uri and enable the [ExtendedStatus](https://httpd.apache.org/docs/2.4/mod/core.html#extendedstatus)

Ensure that access is granted to the uri from where the plugin will run. Usually this will be localhost/127/0/0/1

```
ExtendedStatus On

<IfModule mod_status.c>
  <Location /server-status>
    SetHandler server-status
    Require local
    Require ip 127.0.0.1
  </Location>
</IfModule>
```

Restart Apache and test the plugin

```
service apache2 restart
```
