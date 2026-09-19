(function () {
  const roastLayout = document.querySelector(".roast-layout");
  const roastForm = document.querySelector(".roast-form");
  const desktopQuery = window.matchMedia("(min-width: 641px)");

  function sizeRoastLayout() {
    if (!desktopQuery.matches) {
      roastLayout.style.height = "";
      return;
    }
    const top = roastLayout.getBoundingClientRect().top;
    roastLayout.style.height = Math.max(300, window.innerHeight - top - 24) + "px";
  }

  sizeRoastLayout();
  window.addEventListener("resize", sizeRoastLayout);

  // The right pane (graph/timer) stays put; only the left form
  // scrolls. The wheel always drives that scroll no matter which half
  // the cursor is over - deliberately not the hover-dependent
  // split-scroll some sites use.
  window.addEventListener(
    "wheel",
    (event) => {
      if (!desktopQuery.matches) return;
      event.preventDefault();
      roastForm.scrollTop += event.deltaY;
    },
    { passive: false }
  );
})();
