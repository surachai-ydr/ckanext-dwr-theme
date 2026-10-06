/* ckanext-dwr-theme JavaScript module.
 *
 * Usage: <button data-module="dwr-theme-greeting" data-module-name="CKAN"></button>
 * Clicking the element calls the dwr_theme_hello API action and shows the result.
 */
ckan.module("dwr-theme-greeting", function ($) {
  "use strict";

  return {
    options: {
      name: null,
    },

    initialize: function () {
      $.proxyAll(this, /_on/);
      this.el.on("click", this._onClick);
    },

    _onClick: function () {
      var name = this.options.name || "World";
      this.sandbox.client.call(
        "GET",
        "dwr_theme_hello",
        "?name=" + encodeURIComponent(name),
        this._onSuccess
      );
    },

    _onSuccess: function (response) {
      this.el.text(response.result.message);
    },
  };
});
