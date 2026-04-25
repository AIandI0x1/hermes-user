(function () {
  "use strict";

  const SDK = window.__HERMES_PLUGIN_SDK__;
  const { React } = SDK;

  function MinimalDashboardPlugin() {
    return React.createElement(
      "main",
      { className: "mhp-page" },
      React.createElement("h1", null, "Minimal Dashboard Plugin"),
      React.createElement(
        "p",
        null,
        "This page is rendered from a self-contained Hermes user plugin.",
      ),
    );
  }

  window.__HERMES_PLUGINS__.register("minimal-dashboard-plugin", MinimalDashboardPlugin);
})();
