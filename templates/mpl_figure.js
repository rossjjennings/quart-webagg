/* script for loading matplotlib figure */

document.addEventListener("DOMContentLoaded", () => {
  var websocket_type = mpl.get_websocket_type();
  var websocket = new websocket_type("{{ sock_uri }}");
  {% for fig in figures %}
  var {{ fig.name }} = new mpl.figure(
      {{ fig.fig_id }},
      websocket,
      (figure, format) => {
        window.open('{{ fig.name }}.' + format, '_blank');
      },
      document.getElementById("{{ fig.name }}")
  );
  {% endfor %}
});
