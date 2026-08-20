/**
 * Shared page-load and MkDocs Material instant-navigation helpers.
 */

(() => {
  "use strict";

  /**
   * Run once the document is ready.
   *
   * @param {() => void} fn
   */
  const onDocumentReady = (fn) => {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn, {
        once: true,
      });
    } else {
      fn();
    }
  };

  /**
   * Subscribe to MkDocs Material instant navigation when available.
   *
   * @param {() => void} fn
   */
  const onInstantNavigation = (fn) => {
    if (typeof document$ !== "undefined") {
      document$.subscribe(() => {
        requestAnimationFrame(fn);
      });
    }
  };

  /**
   * Run on first paint and again after Material instant navigation.
   *
   * @param {() => void} fn
   */
  const onPageRender = (fn) => {
    onDocumentReady(fn);
    onInstantNavigation(fn);
  };

  window.LupaxaPageLifecycle = {
    onDocumentReady,
    onInstantNavigation,
    onPageRender,
  };

  /**
   * Resolve footer © years in the browser so the range stays current
   * without rebuilding the site each January.
   *
   * Uses extra.start_year from the markup (data-start-year):
   * - start < current  → "start-current"
   * - otherwise        → current year
   */
  const initFooterYears = () => {
    const current = new Date().getFullYear();
    document.querySelectorAll(".footer-years").forEach((el) => {
      const raw = el.getAttribute("data-start-year");
      const start = raw ? Number.parseInt(raw, 10) : Number.NaN;
      el.textContent =
        Number.isFinite(start) && start < current
          ? `${start}-${current}`
          : String(current);
    });
  };

  onPageRender(initFooterYears);
})();
