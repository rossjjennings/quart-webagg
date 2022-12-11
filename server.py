from quart import (
    Quart,
    render_template,
    make_response,
    request,
    url_for,
    send_from_directory,
    websocket,
    g,
)
import numpy as np
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_webagg import FigureManagerWebAgg
import os.path
import asyncio
import io

from figure import FigWrapper

app = Quart(__name__)

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
        global fw
        fw = FigWrapper(tg, 1, fig)

@app.route('/download.<fmt>')
async def download(fmt):
    buff = io.BytesIO()
    fw.manager.canvas.figure.savefig(buff, format=fmt)
    response = await make_response(buff.getvalue())
    try:
        response.mimetype = image_mimetypes[fmt]
    except KeyError:
        response.mimetype = 'application/octet-stream'
    return response

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
