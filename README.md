# Quart-WebAgg
Quart-WebbAgg is an extension for [Quart](https://github.com/pallets/quart) which makes it easy to add interactive plots using [Matplotlib](https://github.com/matplotlib/matplotlib)'s [WebAgg](https://matplotlib.org/stable/api/backend_webagg_api.html#module-matplotlib.backends.backend_webagg) backend.

The WebAgg backend is the technology underlying interactive plotting using Matplotlib in [Jupyter](https://jupyter.org/) notebooks.
Although it is intended to be usable this way, the WebAgg backend has rarely been used to embed plots in third-party web applications.
As such, Quart-WebAgg also represents a proof of concept that such embedding is possible.

Quart-WebAgg relies on [`asyncio.TaskGroup`](https://docs.python.org/3/library/asyncio-task.html#asyncio.TaskGroup) objects in an essential way, so there is a hard dependence on Python 3.11.

## Usage
A simple example of using Quart-WebAgg is below:
```python
from quart import Quart
from quart_webagg import WebAgg

app = Quart(__name__)
webagg = WebAgg()

@app.route('/')
async def index():
    return await render_template('index.html')

@webagg.figure('sinusoid')
async def plot_sinusoid(fig):
    ax = fig.add_subplot()
    t = np.arange(0.0, 3.0, 0.01)
    s = np.sin(2 * np.pi * t)
    ax.plot(t, s)
    return fig

if __name__ == '__main__':
    webagg.init_app(app)
    app.run()
```
Plotting functions should accept a Matplotlib `Figure` object, do all plotting within that `Figure`, and return the same `Figure`.
Note that `webagg.init_app(app)` must be run after all plotting functions are declared.
To place a plot on a webpage, create a `div` element whose `id` property matches the name passed to the `webagg.figure` decorator (here, `'sinusoid'`).

A complete example application can be found in `example_server/`.
