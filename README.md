ash
===

Running
-------

Use `poetry run -m ash` (Python 3.10 is required) or the included Dockerfile to run ash.


### Docker

Run `docker build -t openpype/ash:latest .` to build the image.

When running, don't forget to mount `/var/run/docker.sock` into the container.
You should also force a container hostname to avoid unpredictable Docker hashes.

For example:

```
docker run --rm -ti \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --hostname worker01 \
  --env AY_API_KEY=verysecureapikey \
  --env AY_SERVER_URL="http://172.18.0.1:5000" \
  openpype/ash
```


Configuration
-------------

Use the following environment variables to configure ash (`.env` file is supported):

### AY_SERVER_URL

Path to the API server including the schema (for example `https://ayon.cloud`).

### AY_API_KEY

API Key of the user. Only service accounts are allowed. By default, this API key (as well as
the server url) will be passed to the spawned services.

### AY_HOSTNAME

Optional setting to override the hostname.
