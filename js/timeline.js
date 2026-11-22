/* The project time line: move "now" to today. styles.css holds a fallback
   date for browsers without JavaScript. */
(function () {
  "use strict";
  var d = new Date();
  var y = d.getFullYear();
  var start = new Date(y, 0, 1);
  var end = new Date(y + 1, 0, 1);
  var now = (y + (d - start) / (end - start)).toFixed(3);
  var els = document.querySelectorAll(".pj-wrap");
  for (var i = 0; i < els.length; i++) els[i].style.setProperty("--now", now);
})();
