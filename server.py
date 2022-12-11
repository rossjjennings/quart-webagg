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

fig = Figure()
ax = fig.add_subplot()
t = np.arange(0.0, 3.0, 0.01)
s = np.sin(2 * np.pi * t)
ax.plot(t, s)

fw = FigWrapper(1, fig, app)

@app.route('/')
async def hello_world():
    return await render_template('index.html')

@app.websocket('/ws')
async def ws():
    async with asyncio.TaskGroup() as tg:
        fw.register_callbacks(tg)
        tg.create_task(fw.receive_messages())

if __name__ == '__main__':
    app.run()
