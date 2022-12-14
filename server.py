from quart import Quart, render_template
import numpy as np
import matplotlib as mpl
import asyncio

from sculptor import Sculptor

app = Quart(__name__)
sc = Sculptor(app)

@app.route('/')
async def index():
    return await render_template('index.html')

@sc.figure('figure1')
def make_figure(fig):
    ax = fig.add_subplot()
    t = np.arange(0.0, 3.0, 0.01)
    s = np.sin(2 * np.pi * t)
    ax.plot(t, s)
    return fig

@sc.figure('figure2')
def make_figure(fig):
    ax = fig.add_subplot()
    t = np.arange(-1.0, 1.0, 0.01)
    s = np.sin(t**2)
    ax.plot(t, s)
    return fig

if __name__ == '__main__':
    app.run()
