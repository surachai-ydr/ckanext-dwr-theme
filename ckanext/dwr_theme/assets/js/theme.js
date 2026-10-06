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

/* Text size switcher. Sets data-dwr-font-size on <html> (lg/xl; none for
 * normal), which scales --dwr-font-scale in theme.css, and remembers the
 * choice. base.html re-applies the saved size before the page renders.
 *
 * Usage: <div data-module="dwr-theme-font-size">
 *          <button data-size="md">A</button> <button data-size="lg">A</button> ...
 *        </div>
 */
ckan.module("dwr-theme-font-size", function ($) {
  "use strict";

  var STORAGE_KEY = "dwr-font-size";

  return {
    initialize: function () {
      $.proxyAll(this, /_on/);
      this.buttons = this.el.find("[data-size]");
      this.buttons.on("click", this._onClick);
      this._update(document.documentElement.getAttribute("data-dwr-font-size") || "md");
    },

    _onClick: function (event) {
      var size = $(event.currentTarget).data("size");
      if (size === "md") {
        document.documentElement.removeAttribute("data-dwr-font-size");
      } else {
        document.documentElement.setAttribute("data-dwr-font-size", size);
      }
      try {
        localStorage.setItem(STORAGE_KEY, size);
      } catch (e) {
        // Storage blocked (private mode etc.): the size still applies to this page.
      }
      this._update(size);
    },

    _update: function (size) {
      this.buttons.each(function () {
        this.setAttribute("aria-pressed", this.getAttribute("data-size") === size ? "true" : "false");
      });
    },
  };
});

/* Homepage welcome dialog. Opens once per browser session; ticking
 * "Don't show this again" hides it until its content (data-module-key) changes.
 *
 * Usage: <dialog data-module="dwr-theme-home-modal" data-module-key="abc123">
 *          <form method="dialog">... <input type="checkbox" name="dismiss"> ...</form>
 *        </dialog>
 */
ckan.module("dwr-theme-home-modal", function ($) {
  "use strict";

  var DISMISSED_KEY = "dwr-modal-dismissed";
  var SEEN_KEY = "dwr-modal-seen";

  function read(storage, key) {
    try {
      return window[storage].getItem(key);
    } catch (e) {
      return null;
    }
  }

  function write(storage, key, value) {
    try {
      window[storage].setItem(key, value);
    } catch (e) {
      // Storage blocked: the dialog will just show again next time.
    }
  }

  return {
    options: {
      key: "",
    },

    initialize: function () {
      $.proxyAll(this, /_on/);
      var dialog = this.el[0];
      var key = String(this.options.key);
      if (typeof dialog.showModal !== "function") {
        return;
      }
      if (read("localStorage", DISMISSED_KEY) === key || read("sessionStorage", SEEN_KEY) === key) {
        return;
      }
      this.el.on("close", this._onClose);
      this.el.on("click", this._onBackdropClick);
      dialog.showModal();
      write("sessionStorage", SEEN_KEY, key);
    },

    _onClose: function () {
      if (this.el.find("input[name=dismiss]").prop("checked")) {
        write("localStorage", DISMISSED_KEY, String(this.options.key));
      }
    },

    // A click on the dialog element itself (not its content) is on the backdrop.
    _onBackdropClick: function (event) {
      if (event.target === this.el[0]) {
        this.el[0].close();
      }
    },
  };
});
