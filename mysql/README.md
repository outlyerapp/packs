# MySQL Pack

The plugin for this pack runs `mysql show global status` on the command line with some options. By default it will use
the user name root with a blank password.

To set the user name and password edit the `mysql.py` plugin and change:

```
MYSQL_USER = 'root'
MYSQL_PASSWORD = ''
```

To create a new user specifically for Dataloop with a minimum set of privileges use the following command:

```
GRANT USAGE ON *.* TO 'dataloop'@'localhost' IDENTIFIED BY PASSWORD 'password'
```

Then set the user name and password in the script to match.

