/* ckanext-dwr-theme JavaScript modules. */

/* Header: mobile menu toggle, shadow on scroll, close user menu on outside click.
 *
 * Usage: <header data-module="dwr-theme-header">...</header>
 */
ckan.module("dwr-theme-header", function ($) {
  "use strict";

  return {
    initialize: function () {
      $.proxyAll(this, /_on/);
      this.toggle = this.el.find(".dwr-nav-toggle");
      this.toggle.on("click", this._onToggle);
      $(document).on("click", this._onDocumentClick);
      $(window).on("scroll", this._onScroll);
      this._onScroll();
    },

    _onToggle: function () {
      var open = this.el.toggleClass("is-open").hasClass("is-open");
      this.toggle.attr("aria-expanded", open ? "true" : "false");
    },

    _onDocumentClick: function (event) {
      this.el.find("details[open]").each(function () {
        if (!this.contains(event.target)) {
          this.removeAttribute("open");
        }
      });
    },

    _onScroll: function () {
      this.el.toggleClass("is-scrolled", window.scrollY > 8);
    },
  };
});

/* Demo module for the /dwr-theme page: calls the dwr_theme_hello API action.
 *
 * Usage: <button data-module="dwr-theme-greeting" data-module-name="CKAN"></button>
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
