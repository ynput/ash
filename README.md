AYON service host a.k.a. ASH
===

ASH is a small process that handles spawning services as specified by the administrator in the services page. It periodically checks the services declared in the Ayon server database and starts them if they are not running. It also provides a simple API for services to report their status and to receive configuration.

Running
-------

Use `poetry run -m ash` (Python 3.10 is required) or the included Dockerfile to run ash.


### Docker

Run `docker build -t ynput/ayon-ash:latest .` to build the image.

When running, don't forget to mount `/var/run/docker.sock` into the container.
You should also force a container hostname to avoid unpredictable Docker hashes.

For example:

```
docker run --rm -ti \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --hostname worker01 \
  --env AYON_API_KEY=verysecureapikey \
  --env AYON_SERVER_URL="http://172.18.0.1:5000" \
  ynput/ayon-ash
```


Configuration
-------------

Use the following environment variables to configure ash (`.env` file is supported):

### AYON_SERVER_URL

Path to the API server including the schema (for example `https://ayon.cloud`).

### AYON_API_KEY

API Key of the user. Only service accounts are allowed. By default, this API key (as well as
the server url) will be passed to the spawned services.

### AYON_HOSTNAME

Optional setting to override the hostname.
