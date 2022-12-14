/* script for loading matplotlib figures */

document.addEventListener("DOMContentLoaded", () => {
  var websocket_type = mpl.get_websocket_type();
  {% for fig in figures %}
  var {{ fig.name }} = new mpl.figure(
      {{ fig.name }},
      new websocket_type("{{ fig.sock_uri }}"),
      (figure, format) => {
        window.open("{{ fig.name }}." + format, "_blank");
      },
      document.getElementById("{{ fig.name }}")
  );
  {% endfor %}
});
