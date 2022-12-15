/* script for loading matplotlib figures */
const image_mimetypes = {
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

document.addEventListener("DOMContentLoaded", () => {
  var websocket_type = mpl.get_websocket_type();
  {% for fig in figures %}
  var websocket{{ fig.fig_id }} = new websocket_type("{{ fig.sock_uri }}")
  var figure{{ fig.fig_id }} = new mpl.figure(
    {{ fig.fig_id }},
    websocket{{ fig.fig_id }},
    (figure, format) => {
      websocket{{ fig.fig_id }}.send(JSON.stringify({"type": "savefig", "format": format}))
    },
    document.getElementById("{{ fig.name }}")
  );
  websocket{{ fig.fig_id }}.addEventListener("message", (event) => {
    try {
      message = JSON.parse(event.data)
    } catch (e) {
      if (e instanceof SyntaxError) {
        // ignore it
      } else {
        throw e;
      }
    }
    if (message.type == "savefig") {
      data_url = "data:" + image_mimetypes[message.format] + ";base64,"
      data_url += message.data;
      var element = document.createElement("a");
      element.setAttribute("href", data_url);
      element.setAttribute("download", "{{ fig.name }}." + message.format);
      element.style.display = 'none';
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    }
  });
  {% endfor %}
});
