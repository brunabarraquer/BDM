import psutil
import time
import threading

stop_monitoring = False

def get_process_usage(process_name):
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == process_name:
            with process.oneshot():
                cpu_usage = process.cpu_percent(interval=1)
                memory_info = process.memory_info()
                memory_usage = memory_info.rss / (1024 ** 2)  # Convert to MB
            return {
                'pid': process.info['pid'],
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage
            }
    return None

def monitor_system():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_usage = memory.used / (1024 ** 2)  # Convert to MB
    memory_total = memory.total / (1024 ** 2)  # Convert to MB
    disk_usage = psutil.disk_usage('/').percent

    return {
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'memory_total': memory_total,
        'disk_usage': disk_usage
    }

def run_monitor(output_func, process_name=None, interval=1):
    global stop_monitoring
    while not stop_monitoring:
        system_stats = monitor_system()
        output_func(f"Sistema - CPU: {system_stats['cpu_usage']}%, "
                    f"Memoria: {system_stats['memory_usage']}MB/{system_stats['memory_total']}MB, "
                    f"Disco: {system_stats['disk_usage']}%")

        if process_name:
            process_stats = get_process_usage(process_name)
            if process_stats:
                output_func(f"Proceso '{process_name}' - PID: {process_stats['pid']}, "
                            f"CPU: {process_stats['cpu_usage']}%, "
                            f"Memoria: {process_stats['memory_usage']}MB")
            else:
                output_func(f"Proceso '{process_name}' no encontrado.")

        output_func("-" * 50)
        time.sleep(interval)

def start_monitoring_thread(output_func, process_name=None, interval=1):
    global stop_monitoring
    stop_monitoring = False
    monitor_thread = threading.Thread(target=run_monitor, args=(output_func, process_name, interval))
    monitor_thread.start()
    return monitor_thread

def stop_monitoring_thread():
    global stop_monitoring
    stop_monitoring = True