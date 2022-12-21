# Quart-WebAgg
Quart-WebbAgg is an extension for [Quart](https://github.com/pallets/quart) which makes it easy to add interactive plots using [Matplotlib](https://github.com/matplotlib/matplotlib)'s [WebAgg](https://matplotlib.org/stable/api/backend_webagg_api.html#module-matplotlib.backends.backend_webagg) backend.

The WebAgg backend is the technology underlying interactive plotting using Matplotlib in [Jupyter](https://jupyter.org/) notebooks.
Under the hood, the WebAgg backend uses a WebSocket to manage communication between the client and server.
This means that Quart's native support for WebSockets is crucial for interfacing with WebAgg.

Quart-WebAgg relies on [`asyncio.TaskGroup`](https://docs.python.org/3/library/asyncio-task.html#asyncio.TaskGroup) objects in an essential way, so it has a hard dependence on Python 3.11.

## Usage
A simple example of using Quart-WebAgg is below:
```python
from quart import Quart
import numpy as np
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

webagg.init_app(app)

if __name__ == '__main__':
    app.run()
```
Plotting functions should accept a Matplotlib `Figure` object, do all plotting within that `Figure`, and return the same `Figure`.
Note that `webagg.init_app(app)` must be run after all plotting functions are declared.
To place a plot on a webpage, create a `div` element whose `id` property matches the name passed to the `webagg.figure` decorator (here, `'sinusoid'`).
Pages containing figures should include the template `webagg_head.html` in their `<head>` section.
The `index.html` template accompanying the above example should therefore look like
```jinja
<!DOCTYPE html>
<html>
  <head>
    {% include 'webagg_head.html' %}
    <title>Quart-WebAgg example</title>
  </head>
  <body>
    <div id="sinusoid" style="width: 640px; margin: auto"></div>
  </body>
</html>
```

A complete example application can be found in `example_server/`.

## Don't block the event loop

Quart-WebAgg runs plotting functions within Quart's event loop. This makes it possible for the plotting functions to call asynchronous code using the `await` keyword, but it also makes it possible for plotting code to block the event loop, preventing other asynchronous code from executing while the plot is being constructed. To avoid this, it is advisable to run CPU-bound computations in a separate thread or process, for example using [`asyncio.run_in_executor()`](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor) together with the `ThreadPoolExecutor` or `ProcessPoolExecutor` provided by [`concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html#module-concurrent.futures). This might look like:

```python
from quart_webagg import WebAgg
import asyncio
import concurrent.futures

webagg = WebAgg()

def get_data():
    t = np.arange(0.0, 3.0, 0.01)
    s = np.sin(2 * np.pi * t)
    return t, s

@webagg.figure('sinusoid')
async def plot_sinusoid(fig):
    ax = fig.add_subplot()
    loop = asyncio.get_running_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        t, s = await loop.run_in_executor(pool, get_data)
    ax.plot(t, s)
    return fig
```
The work done by `get_data()` in this example is most likely too small to make running it in a separate process worthwhile, but in many cases, much more involved computations may be necessary to produce a plot.
