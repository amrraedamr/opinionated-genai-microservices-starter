from base.tools.webserver import run_webserver


def start():
    run_webserver(app_path="base.main:app")
