import json
import pip
import sqlite3

con = sqlite3.connect("con.db", check_same_thread=False)

try:
    from loguru import logger
except ImportError:
    pip.main(['install', 'loguru'])
    from loguru import logger
finally:
    logger.add("debug.log", rotation='1 day')

try:
    import TouchPortalAPI
except ImportError:
    pip.main(['install', 'TouchPortal-API'])
    import TouchPortalAPI


plugin_id = "com.github.Jabbey92.TouchPortal.PolyPop.TouchPortalPolyPopPlugin"
TPClient = TouchPortalAPI.Client(plugin_id)


def get_server_details(settings):
    address, port = None, None
    for d in settings:
        address = d.get('Address', address)
        port = d.get('Port', port)
    return address, port


def re_start_server(address, port):
    con.execute("insert into req(task, data) values (?, ?)", ['set_server', f'{address},{port}'])
    con.commit()


def send_message(data):
    con.execute("insert into req(task, data) values (?, ?)", ['message', json.dumps(data)])
    con.commit()


@TPClient.on(TouchPortalAPI.TYPES.onConnect)  # Or replace TYPES.onConnect with 'info'
def on_start(data):
    re_start_server(*get_server_details(data['settings']))


@TPClient.on(TouchPortalAPI.TYPES.onSettingUpdate)
def on_settings(data):
    re_start_server(*get_server_details(data['settings']))


@TPClient.on(TouchPortalAPI.TYPES.onAction)  # Or 'action'
def on_action(data):
    if data['actionId'] == f"{plugin_id}.TriggerAlert":
        title, arguments = "", ""
        for k, v in map(dict.values, data['data']):
            if k == f"{plugin_id}.TriggerAlert.data.AlertToRun":
                title = v
            if k == f"{plugin_id}.TriggerAlert.data.Arguments":
                arguments = dict(x.split('=') for x in v.split(',')) and {}
        payload = {
            "type": "ALERT",
            "title": title,
            "variables": {"text": arguments}
        }
        send_message(payload)


@TPClient.on(TouchPortalAPI.TYPES.onShutdown)  # or 'closePlugin'
def on_shutdown(data):
    con.execute("insert into req(task, data) values (?, ?)", ['shutdown', ''])
    con.commit()
    TPClient.disconnect()


TPClient.connect()
