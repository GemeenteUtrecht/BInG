Apache + mod-wsgi configuration
===============================

An example Apache2 vhost configuration follows::

    WSGIDaemonProcess bing-<target> threads=5 maximum-requests=1000 user=<user> group=staff
    WSGIRestrictStdout Off

    <VirtualHost *:80>
        ServerName my.domain.name

        ErrorLog "/srv/sites/bing/log/apache2/error.log"
        CustomLog "/srv/sites/bing/log/apache2/access.log" common

        WSGIProcessGroup bing-<target>

        Alias /media "/srv/sites/bing/media/"
        Alias /static "/srv/sites/bing/static/"

        WSGIScriptAlias / "/srv/sites/bing/src/bing/wsgi/wsgi_<target>.py"
    </VirtualHost>


Nginx + uwsgi + supervisor configuration
========================================

Supervisor/uwsgi:
-----------------

.. code::

    [program:uwsgi-bing-<target>]
    user = <user>
    command = /srv/sites/bing/env/bin/uwsgi --socket 127.0.0.1:8001 --wsgi-file /srv/sites/bing/src/bing/wsgi/wsgi_<target>.py
    home = /srv/sites/bing/env
    master = true
    processes = 8
    harakiri = 600
    autostart = true
    autorestart = true
    stderr_logfile = /srv/sites/bing/log/uwsgi_err.log
    stdout_logfile = /srv/sites/bing/log/uwsgi_out.log
    stopsignal = QUIT

Nginx
-----

.. code::

    upstream django_bing_<target> {
      ip_hash;
      server 127.0.0.1:8001;
    }

    server {
      listen :80;
      server_name  my.domain.name;

      access_log /srv/sites/bing/log/nginx-access.log;
      error_log /srv/sites/bing/log/nginx-error.log;

      location /500.html {
        root /srv/sites/bing/src/bing/templates/;
      }
      error_page 500 502 503 504 /500.html;

      location /static/ {
        alias /srv/sites/bing/static/;
        expires 30d;
      }

      location /media/ {
        alias /srv/sites/bing/media/;
        expires 30d;
      }

      location / {
        uwsgi_pass django_bing_<target>;
      }
    }
