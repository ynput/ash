import psutil


def get_health():
    mem = psutil.virtual_memory()
    mem_usage = 100 * ((mem.total - mem.free - mem.buffers - mem.cached) / mem.total)
    return {"cpu": psutil.cpu_percent(), "mem": mem_usage,}
