# PHP-FPM Pack

The php-fpm status page needs to be enabled in your configuration for this pack to collect the data.

In file `/etc/php5/fpm/pool.d/www.conf` find the `pm.status_path` variable. Uncomment and set to /status.

```
pm.status_path = /fpm-status
```

Then create a location in nginx in one of our enabled sites.

```
location ~ ^/(fpm-status)$ {
    access_log off;
    allow 127.0.0.1;
    deny all;
    fastcgi_param SCRIPT_FILENAME $fastcgi_script_name;
    include fastcgi_params;
    fastcgi_pass 127.0.0.1:9000;
}
```

Reload php-fpm and nginx. Then to test it works curl the location.

```
curl http://www.example.com/fpm-status
```

This should return the status output.

Finally, edit `php-fpm.py` to specify the HOST variable to match the site you added the fpm-status location to.

```
# settings
HOST = 'www.example.com'
PORT = 80
URL = "http://%s:%s/fpm-status" % (HOST, PORT)
```