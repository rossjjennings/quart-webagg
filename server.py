from quart import (
    Quart,
    render_template,
    make_response,
    request,
    url_for,
    websocket,
)
import numpy as np
import matplotlib as mpl
from matplotlib.figure import Figure
import asyncio
import io

from sculptor import Sculptor, FigWrapper

app = Quart(__name__)
sc = Sculptor(app)

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
        fw = FigWrapper(1, fig, app, tg)
        tg.create_task(fw.receive_messages())

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

if __name__ == '__main__':
    app.run()
