from quart import (
    websocket,
    url_for,
    render_template,
    make_response,
    send_from_directory,
)
import matplotlib as mpl
from matplotlib.backends.backend_webagg import (
    FigureManagerWebAgg,
    new_figure_manager_given_figure,
)
import json
import os.path
import io

image_mimetypes = {
    'eps': 'application/postscript',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'pdf': 'application/pdf',
    'pgf': 'application/x-latex',
    'png': 'image/png',
    'ps': 'application/postscript',
    'svg': 'image/svg+xml',
    'svgz': 'image/svg+xml',
    'tif': 'image/tiff',
    'tiff': 'image/tiff',
    'webp': 'image/webp',
}

class Sculptor:
    def __init__(self, app):
        self.app = app
        self.app.add_url_rule(
            '/_static/<path:path>',
            'webagg_static',
            self.handle_webagg_static,
        )
        self.app.add_url_rule(
            '/_images/<path:path>',
            'webagg_images',
            self.handle_webagg_images,
        )
        self.app.add_url_rule(
            '/mpl.js',
            'mpl_js',
            self.handle_mpl_js,
        )
        self.app.add_url_rule(
            '/mpl_figure.js',
            'mpl_figure_js',
            self.handle_mpl_figure_js,
        )

    async def handle_webagg_static(self, path):
        webagg_static_path = FigureManagerWebAgg.get_static_file_path()
        return await send_from_directory(webagg_static_path, path)

    async def handle_webagg_images(self, path):
        webagg_image_path = os.path.join(mpl.get_data_path(), 'images')
        return await send_from_directory(webagg_image_path, path)

    async def handle_mpl_js(self):
        js = FigureManagerWebAgg.get_javascript()
        response = await make_response(js)
        response.mimetype = 'text/javascript'
        return response

    async def handle_mpl_figure_js(self):
        js = await render_template(
            'mpl_figure.js',
            sock_uri=url_for('ws'),
            fig_id=1,
            elt_id='figure1'
        )
        response = await make_response(js)
        response.mimetype = 'text/javascript'
        return response

class FigWrapper:
    def __init__(self, fig_id, fig, app):
        self.fig_id = fig_id
        self.fig = fig
        self.app = app
        self.task_group = None
        self.manager = new_figure_manager_given_figure(fig_id, fig)
        self.supports_binary = True
        self.app.add_url_rule(
            '/download.<fmt>',
            'download',
            self.handle_download,
        )

    def register_callbacks(self, task_group):
        self.task_group = task_group
        self.manager.add_web_socket(self)

    def send_json(self, content):
        self.task_group.create_task(websocket.send_json(content))

    def send_binary(self, blob):
        if self.supports_binary:
            self.task_group.create_task(websocket.send(blob))
        else:
            data_uri = "data:image/png;base64,{0}".format(
                blob.encode('base64').replace('\n', ''))
            self.task_group.create_task(websocket.send(data_uri))

    async def receive_messages(self):
        while True:
            message = await websocket.receive_json()
            if message['type'] == 'supports_binary':
                self.supports_binary = message['value']
            else:
                self.manager.handle_json(message)

    async def handle_download(self, fmt):
        buff = io.BytesIO()
        self.manager.canvas.figure.savefig(buff, format=fmt)
        response = await make_response(buff.getvalue())
        try:
            response.mimetype = image_mimetypes[fmt]
        except KeyError:
            response.mimetype = 'application/octet-stream'
        return response
