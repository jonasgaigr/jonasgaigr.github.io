/* The transect: the navbar follows the water (light in the air, dark below).
   Optional; without JavaScript the navbar is the dark one of the inner pages. */
(function () {
  "use strict";
  var under = document.getElementById("under");
  if (!under) return;
  var sed = under.querySelector(".sediment");
  var body = document.body;
  function top(el) { return el.getBoundingClientRect().top + window.scrollY; }
  var ticking = false;
  function update() {
    ticking = false;
    var nav = document.querySelector(".navbar");
    var y = window.scrollY + (nav ? nav.offsetHeight : 60);
    body.setAttribute("data-depth", y < top(under) ? "air" : (y < top(sed) ? "water" : "silt"));
  }
  function req() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }
  window.addEventListener("scroll", req, { passive: true });
  window.addEventListener("resize", req);
  update();
})();
