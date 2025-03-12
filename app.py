import multiprocessing
import pandas as pd
import platform
import psutil
import subprocess
import sys

from shiny import App, reactive, render, ui
from urllib.parse import urlparse

app_ui = ui.page_fluid(
    ui.h2("System details:"),
    ui.output_table("system"),
    ui.h2("Request details:"),
    ui.output_text_verbatim("request_output"),
    ui.input_text_area("cmd", "Command to run", placeholder="Enter text"),
    ui.output_text_verbatim("cmd_output"),
    ui.input_text_area("logme", "Text to log", placeholder="Enter text"),
    ui.input_checkbox("stderr", "log to stderr", False),
    ui.input_action_button("log_button", "Log"),
    ui.output_text_verbatim("logged"),
)


def server(input, output, session):
    @output
    @render.table
    def system():
        host_total = psutil.virtual_memory().total
        host_mem = f"{int(host_total / 1024 / 1024 / 1024)} GiB ({host_total} bytes)"
        cpu_max = run(["cat", "/sys/fs/cgroup/cpu.max"])
        parts = cpu_max.split()
        if len(parts) == 2:
            cpu_limit = int(parts[0]) / int(parts[1])
        else:
            cpu_limit = cpu_max
        memory_max=int(run(["cat", "/sys/fs/cgroup/memory.max"]))
        pod_mem = f"{int(memory_max / 1024 / 1024 / 1024)} GiB ({memory_max} bytes)"
        return pd.DataFrame([
            {"name":"python version","value":platform.python_version()},
            {"name":"host cpu count","value":multiprocessing.cpu_count()},
            {"name":"host memory","value":host_mem},
            {"name":"cpu limit","value":cpu_limit},
            {"name":"memory limit","value":pod_mem},
        ])

    @output
    @render.text
    def cmd_output():
        cmd=input.cmd()
        try:
            return subprocess.check_output(cmd, shell=True).decode()
        except Exception as e:
            return f"Error: {e}"

    @output
    @render.text
    def request_output():
        search = session.input[".clientdata_url_search"]()
        return urlparse(search)

    @output
    @render.text()
    @reactive.event(input.log_button)
    def logged():
        l = input.logme()
        if input.stderr():
            print(l, file=sys.stderr)
        else:
            print(l)
        return l

app = App(app_ui, server)

def run(input: list[str]) -> str:
    try:
        return subprocess.check_output(input).decode("utf-8").strip()
    except Exception as e:
        return f"Error: {e}"
