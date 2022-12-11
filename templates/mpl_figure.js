/* script for loading matplotlib figure */

function ondownload(figure, format) {
  window.open('download.' + format, '_blank');
};

document.addEventListener("DOMContentLoaded", () => {
  var websocket_type = mpl.get_websocket_type();
  var websocket = new websocket_type("{{ sock_uri }}");
  var fig = new mpl.figure(
      {{ fig_id }},
      websocket,
      ondownload,
      document.getElementById("{{ elt_id }}")
  );
});
