
  document.addEventListener("click", function(e) {
    var anchor = e.target.closest("a[data-download-link]");
    if (!anchor) return;
    var href = anchor.getAttribute("href");
    if (!href) return;
    e.preventDefault();
    if (typeof window.openDonationModal === "function") {
      window.openDonationModal(href);
    }
  });

  // Shuffle sponsor logos within each level on every page load
  document.querySelectorAll(".sponsor-level").forEach(function(container) {
    var items = Array.from(container.querySelectorAll(".sponsor-logo"));
    for (var i = items.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      container.appendChild(items[j]);
      items.splice(j, 1, items[i]);
    }
  });
