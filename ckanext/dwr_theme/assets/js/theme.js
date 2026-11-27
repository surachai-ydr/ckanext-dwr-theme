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
      // showModal() focuses the first button (Close), which then looks
      // selected; focus the dialog itself so Tab still reaches the button.
      dialog.setAttribute("tabindex", "-1");
      dialog.focus();
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

/* Opens a <dialog> (data-module-target) as a modal when clicked; a click on
 * its backdrop closes it. A dialog with data-dwr-open opens on page load,
 * e.g. a form returned with validation errors. showModal() would focus the
 * close button, so focus goes to the first field with an error, or the first
 * field (data-dwr-focus-field), or else the dialog itself.
 *
 * Usage: <button type="button" data-module="dwr-theme-dialog" data-module-target="#my-dialog">
 */
ckan.module("dwr-theme-dialog", function ($) {
  "use strict";

  return {
    options: {
      target: null,
    },

    initialize: function () {
      $.proxyAll(this, /_on/);
      this.dialog = $(this.options.target)[0];
      if (!this.dialog || typeof this.dialog.showModal !== "function") {
        return;
      }
      this.el.on("click", this._onClick);
      // Bind the backdrop handler once, however many buttons open this dialog
      if (!this.dialog.hasAttribute("data-dwr-bound")) {
        this.dialog.setAttribute("data-dwr-bound", "");
        this.dialog.addEventListener("click", this._onBackdropClick);
        if (this.dialog.hasAttribute("data-dwr-open")) {
          this._open();
        }
      }
    },

    _open: function () {
      var dialog = this.dialog;
      dialog.showModal();
      var field =
        dialog.querySelector(".dwr-field--error .form-control") ||
        (dialog.hasAttribute("data-dwr-focus-field") && dialog.querySelector(".dwr-field .form-control"));
      if (field) {
        field.focus();
      } else {
        dialog.setAttribute("tabindex", "-1");
        dialog.focus();
      }
    },

    _onClick: function () {
      this._open();
    },

    // A click on the dialog element itself (not its content) is on the backdrop.
    _onBackdropClick: function (event) {
      if (event.target === event.currentTarget) {
        event.currentTarget.close();
      }
    },
  };
});

/* Image slideshow in the homepage dialog: shows one .dwr-slides__slide at a
 * time and moves on every `interval` ms, pausing while hovered or focused.
 * Buttons with data-slide="prev" / "next" / <index> move to a slide.
 *
 * Usage: <div data-module="dwr-theme-slides" data-module-interval="5000">
 *          <div class="dwr-slides__slide is-active">...</div> ...
 *          <button type="button" class="dwr-slides__dot" data-slide="0"></button> ...
 *        </div>
 */
ckan.module("dwr-theme-slides", function ($) {
  "use strict";

  return {
    options: {
      interval: 5000,
    },

    initialize: function () {
      $.proxyAll(this, /_on/);
      this.slides = this.el.find(".dwr-slides__slide");
      this.dots = this.el.find(".dwr-slides__dot");
      this.index = 0;
      this.paused = false;
      this.el.on("click", "[data-slide]", this._onNavClick);
      this.el.on("mouseenter focusin", this._onPause);
      this.el.on("mouseleave focusout", this._onResume);
      this._start();
    },

    _start: function () {
      window.clearInterval(this.timer);
      this.timer = window.setInterval(this._onTick, Number(this.options.interval) || 5000);
    },

    _show: function (index) {
      var count = this.slides.length;
      this.index = (index + count) % count;
      this.slides.removeClass("is-active").eq(this.index).addClass("is-active");
      this.dots.removeAttr("aria-current").eq(this.index).attr("aria-current", "true");
    },

    _onTick: function () {
      // Skip while hovered/focused, or while the dialog is closed or the tab hidden
      if (!this.paused && !document.hidden && this.el.closest("dialog[open]").length) {
        this._show(this.index + 1);
      }
    },

    _onNavClick: function (event) {
      var target = event.currentTarget.getAttribute("data-slide");
      if (target === "prev") {
        this._show(this.index - 1);
      } else if (target === "next") {
        this._show(this.index + 1);
      } else {
        this._show(parseInt(target, 10));
      }
      // Restart the countdown so a manual move gets a full interval
      this._start();
    },

    _onPause: function () {
      this.paused = true;
    },

    _onResume: function () {
      this.paused = false;
    },
  };
});

/* Homepage "Load more" button under the organization/group grids: fetches
 * the next page of cards from dwr_theme.home_cards and appends it to the
 * grid. The element is a link to the full listing page, followed if JS is
 * off or the request fails.
 *
 * Usage: <a href="/group/" data-module="dwr-theme-load-more"
 *           data-module-url="/dwr-theme/home/group" data-module-offset="10"
 *           data-module-target="#grid" data-module-loading="Loading...">Load more</a>
 */
ckan.module("dwr-theme-load-more", function ($) {
  "use strict";

  return {
    options: {
      url: null,
      offset: 0,
      target: null,
      loading: "Loading...",
    },

    initialize: function () {
      $.proxyAll(this, /_on/);
      this.grid = $(this.options.target);
      this.wrapper = this.el.closest(".dwr-load-more");
      this.label = this.el.text();
      this.el.on("click", this._onClick);
    },

    _onClick: function (event) {
      event.preventDefault();
      if (this.busy) {
        return;
      }
      this.busy = true;
      this.el.attr("aria-busy", "true").addClass("is-loading").text(this.options.loading);
      $.getJSON(this.options.url, { offset: this.options.offset })
        .done(this._onLoaded)
        .fail(this._onFailed);
    },

    _onLoaded: function (data) {
      var first = this.grid.children().length;
      this.grid.append(data.html);
      this.busy = false;
      this.el.removeAttr("aria-busy").removeClass("is-loading").text(this.label);
      if (data.next_offset) {
        this.options.offset = data.next_offset;
        this.wrapper.find("[data-shown]").text(data.next_offset);
      } else {
        // The button goes away, so move keyboard focus to the first new card.
        this.wrapper.remove();
        this.grid.children().eq(first).find("a").first().trigger("focus");
      }
    },

    _onFailed: function () {
      window.location.href = this.el.attr("href");
    },
  };
});
