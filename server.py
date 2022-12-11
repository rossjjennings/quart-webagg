from quart import (
    Quart,
    render_template,
    make_response,
    request,
    url_for,
    send_from_directory,
    websocket,
)
import numpy as np
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_webagg import (
    FigureManagerWebAgg,
    new_figure_manager_given_figure,
)
import os.path
import asyncio
import json

app = Quart(__name__)

class FigWrapper:
    def __init__(self, tg, fig_id, fig):
        self.tg = tg
        self.fig = fig
        self.manager = new_figure_manager_given_figure(fig_id, self.fig)
        self.supports_binary = True
        self.manager.add_web_socket(self)
        print(f"Toolbar is: {self.manager.toolbar}")
        tg.create_task(self.receive_messages())

    def send_message(self, message):
        self.tg.create_task(websocket.send(message))
        
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
        self.send_message(json.dumps(content))

    def send_binary(self, blob):
        print(f"Sending blob")
        if self.supports_binary:
            self.send_message(blob)
        else:
            data_uri = "data:image/png;base64,{0}".format(
                blob.encode('base64').replace('\n', ''))
            self.write_message(data_uri)

@app.route('/')
async def hello_world():
    return await render_template('index.html')

@app.websocket('/ws')
async def ws():
    fig = Figure()
    ax = fig.add_subplot()
    t = np.arange(0.0, 3.0, 0.01)
    s = np.sin(2 * np.pi * t)
    ax.plot(t, s)
    
    async with asyncio.TaskGroup() as tg:
        fw = FigWrapper(tg, 1, fig)

@app.route('/mpl.js')
async def mpl_js():
    js = FigureManagerWebAgg.get_javascript()
    response = await make_response(js)
    response.mimetype = 'text/javascript'
    return response

@app.route('/mpl_figure.js')
async def mpl_figure_js():
    js = await render_template('mpl_figure.js', sock_uri=url_for('ws'), fig_id=1, elt_id='figure1')
    response = await make_response(js)
    response.mimetype = 'text/javascript'
    return response

@app.route('/_static/<path:path>')
async def webagg_static(path):
    webagg_static_path = FigureManagerWebAgg.get_static_file_path()
    return await send_from_directory(webagg_static_path, path)

@app.route('/_images/<path:path>')
async def webagg_images(path):
    webagg_image_path = os.path.join(mpl.get_data_path(), 'images')
    return await send_from_directory(webagg_image_path, path)

if __name__ == '__main__':
    app.run()
