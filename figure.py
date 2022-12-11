from quart import websocket
from matplotlib.backends.backend_webagg import new_figure_manager_given_figure
import json

class FigWrapper:
    def __init__(self, tg, fig_id, fig):
        self.tg = tg
        self.fig = fig
        self.manager = new_figure_manager_given_figure(fig_id, self.fig)
        self.supports_binary = True
        self.manager.add_web_socket(self)
        print(f"Toolbar is: {self.manager.toolbar}")
        tg.create_task(self.receive_messages())

    async def receive_messages(self):
        while True:
            message = await websocket.receive_json()
            if message['type'] == 'supports_binary':
                self.supports_binary = message['value']
            else:
                print(f"Received {message}")
                self.manager.handle_json(message)

    def send_json(self, content):
        print(f"Sending JSON {content}")
        self.tg.create_task(websocket.send_json(content))

    def send_binary(self, blob):
        print(f"Sending blob")
        if self.supports_binary:
            self.tg.create_task(websocket.send(blob))
        else:
            data_uri = "data:image/png;base64,{0}".format(
                blob.encode('base64').replace('\n', ''))
            self.tg.create_task(websocket.send(data_uri))
