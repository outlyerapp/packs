# Wordpress Pack

Remote polling of a Wordpress server via the rest api.

This module requires the Wordpress Rest API V2 Module installed on your Wordpress Site to work. You can download
it here: http://v2.wp-api.org/

Once installed you will need to edit the `wordpress.py` plugin and set the HOST variable

```
# settings
HOST = ''          # e.g. https://blog.company.com
```

As this pack / plugin does remote polling you should only assign the wordpress tag to a single agent responsible for
monitoring Wordpress. A good one to use is the `dataloop` agent.