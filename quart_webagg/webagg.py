from quart import (
    Blueprint,
    websocket,
    url_for,
    render_template,
    make_response,
    send_from_directory,
)
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_webagg import (
    FigureManagerWebAgg,
    new_figure_manager_given_figure,
)
import json
import os.path
import io
import asyncio

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

class WebAgg:
    def __init__(self):
        self.blueprint = Blueprint(
            'webagg',
            __name__,
            template_folder='templates'
        )
        self.blueprint.add_url_rule(
            '/_static/<path:path>',
            'webagg_static',
            self.handle_webagg_static,
        )
        self.blueprint.add_url_rule(
            '/_images/<path:path>',
            'webagg_images',
            self.handle_webagg_images,
        )
        self.blueprint.add_url_rule(
            '/mpl.js',
            'mpl_js',
            self.handle_mpl_js,
        )
        self.blueprint.add_url_rule(
            '/mpl_figure.js',
            'mpl_figure_js',
            self.handle_mpl_figure_js,
        )
        self.fig_blueprints = []

    def init_app(self, app):
        app.register_blueprint(self.blueprint)

    def figure(self, name):
        def inner(wrapped_func):
            fig_id = len(self.fig_blueprints) + 1
            fbp = FigureBlueprint(fig_id, name, wrapped_func, self.blueprint)
            self.fig_blueprints.append(fbp)
        return inner

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
        figures = [await fig.get_info() for fig in self.fig_blueprints]
        print(figures)
        js = await render_template(
            'mpl_figure.js',
            figures=figures,
        )
        response = await make_response(js)
        response.mimetype = 'text/javascript'
        return response

class FigureBlueprint:
    def __init__(self, fig_id, name, plot, parent):
        self.fig_id = fig_id
        self.name = name
        self.plot = plot
        self.parent = parent
        self.supports_binary = True
        self.parent.add_url_rule(
            f'/{self.name}.<fmt>',
            f'download_{self.name}',
            self.handle_download,
        )
        self.parent.add_websocket(
            f'/{self.name}.ws',
            f'websocket_{self.name}',
            self.handle_websocket,
        )

    async def handle_websocket(self):
        fig = Figure()
        fig = await self.plot(fig)
        ctx = FigureContext(self.fig_id, fig)
        async with asyncio.TaskGroup() as tg:
            ctx.register_callbacks(tg)

    async def handle_download(self, fmt):
        fig = Figure()
        fig = await self.plot(fig)
        manager = new_figure_manager_given_figure(self.fig_id, fig)
        buff = io.BytesIO()
        manager.canvas.figure.savefig(buff, format=fmt)
        response = await make_response(buff.getvalue())
        try:
            response.mimetype = image_mimetypes[fmt]
        except KeyError:
            response.mimetype = 'application/octet-stream'
        return response

    async def get_info(self):
        sock_name = f'{self.parent.name}.websocket_{self.name}'
        sock_uri = url_for(sock_name)
        return {'name': self.name, 'fig_id': self.fig_id, 'sock_uri': sock_uri}

class FigureContext:
    def __init__(self, fig_id, fig):
        self.fig = fig
        self.fig_id = fig_id
        self.manager = new_figure_manager_given_figure(self.fig_id, self.fig)
        self.task_group = None

    def register_callbacks(self, task_group):
        self.task_group = task_group
        self.manager.add_web_socket(self)
        task_group.create_task(self.receive_messages())

    def send_json(self, content):
        print(f"Figure {self.fig_id} sending JSON: {content}")
        self.task_group.create_task(websocket.send_json(content))

    def send_binary(self, blob):
        print(f"Figure {self.fig_id} sending blob")
        if self.supports_binary:
            self.task_group.create_task(websocket.send(blob))
        else:
            data_uri = "data:image/png;base64,{0}".format(
                blob.encode('base64').replace('\n', ''))
            self.task_group.create_task(websocket.send(data_uri))

    async def receive_messages(self):
        while True:
            message = await websocket.receive_json()
            print(f"Figure {self.fig_id} received JSON: {message}")
            if message['type'] == 'supports_binary':
                self.supports_binary = message['value']
            else:
                self.manager.handle_json(message)
