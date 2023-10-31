import threading

from nxtools import log_traceback, logging


class ServiceLog:
    def __init__(self, service_name: str, container):
        self.service_name = service_name
        self.container = container
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        logging.info(
            f"Starting log stream for {self.service_name}, last 10 lines were..."
        )
        for line in self.container.logs(stream=True, tail=10, stderr=True):
            print(line.decode().strip())

        # service exited
        # print the status code and free the container

        try:
            status_code = self.container.wait()["StatusCode"]
            logging.warning(f"{self.service_name} exited with code {status_code}")
        except Exception as e:
            logging.warning("Lost connection to the container:")
            log_traceback(e)
            self.container = None


class ServiceLogger:
    """
    Service logger collects the logs from the services and prints them to stdout
    That effectively proxies all the logs from the services to the ash logs.

    Service is responsible for the formatting of the logs. It SHOULD contain
    the service name.

    To maintain the same log format as the ash, you can use nxtools logging
    in the service:

    ```
    import os
    from nxtools import logging

    if service_name := os.environ.get("AYON_SERVICE_NAME"):
        logging.user = service_name
    ```
    """

    services: dict[str, ServiceLog] | None = None

    @classmethod
    def add(cls, service_name, container):
        if cls.services is None:
            cls.services = {}
        else:
            service = cls.services.get(service_name)
            if service and service.container:
                # ServiceLog for this service is already running
                return

        # Create new ServiceLog instance
        cls.services[service_name] = ServiceLog(service_name, container)
