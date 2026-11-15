(function(){const linksMap = {"recurring_5":{"link":"https://buy.stripe.com/fZe2997f69Ja90I4gm","currencies":["USD","EUR"]},"recurring_10":{"link":"https://buy.stripe.com/9AQaFFeHycVm7WE28f","currencies":["USD","EUR"]},"recurring_20":{"link":"https://buy.stripe.com/aEU6pp1UM5sU7WE7sA","currencies":["USD","EUR"]},"recurring_50":{"link":"https://buy.stripe.com/dR63ddbvmaNeel2eV3","currencies":["USD","EUR"]},"recurring_100":{"link":"https://buy.stripe.com/8wM011fLC3kMgtaeV4","currencies":["USD","EUR"]},"one_time_5":{"link":"https://donate.stripe.com/14k01142Uf3u3GobIJ","currencies":["USD","EUR"]},"one_time_10":{"link":"https://donate.stripe.com/bIY15542U9Ja6SAdQS","currencies":["USD","EUR"]},"one_time_20":{"link":"https://donate.stripe.com/9AQ8xxgPGcVma4M28b","currencies":["USD","EUR"]},"one_time_50":{"link":"https://donate.stripe.com/14k3dd8ja2gIa4McMQ","currencies":["USD","EUR"]},"one_time_100":{"link":"https://donate.stripe.com/7sI1557f61cE6SAdQV","currencies":["USD","EUR"]}};
const descriptionTemplates = {"recurring":"{amount} per month","one_time":"One-time {amount} donation"};
const customLinks = {"USD":"https://donate.stripe.com/3cs1559ne3kMa4M3cc","EUR":"https://buy.stripe.com/9B64gy7eO1X9d3Mftc1oI0b"};
const config = {"defaultCurrency":"USD","timezoneCurrencyMap":[{"pattern":"Europe/*","currency":"EUR"}]};
const defaultTypeId = "one_time";
const defaultAmount = 10;

(function() {
  var FREQ_BASE = "donation-freq-btn flex-1 py-2 px-4 text-sm font-medium text-center transition-colors";
  var AMT_BASE = "donation-amount-btn rounded-md border border-border py-2 text-sm font-medium text-text transition-colors hover:border-action";

  // Detect currency from timezone using the config map.
  // Patterns support a trailing wildcard: "Europe/*" matches any "Europe/..." timezone.
  function detectCurrency() {
    try {
      var tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      for (var i = 0; i < config.timezoneCurrencyMap.length; i++) {
        var entry = config.timezoneCurrencyMap[i];
        var pattern = entry.pattern;
        var match = pattern.endsWith("/*")
          ? tz.startsWith(pattern.slice(0, -1))  // "Europe/*" -> tz.startsWith("Europe/")
          : tz === pattern;
        if (match) return entry.currency;
      }
    } catch (e) {}
    return config.defaultCurrency;
  }

  // Resolve the payment URL, preferring the detected currency.
  function resolveLink(typeId, amount, currency, isCustom) {
    if (isCustom) {
      return customLinks[currency] || customLinks[config.defaultCurrency] || "";
    }
    var entry = linksMap[typeId + "_" + amount];
    if (!entry) return "";
    if (entry.links) {
      return entry.links[currency] || entry.links[config.defaultCurrency] || "";
    }
    return entry.link || "";
  }

  var detectedCurrency = detectCurrency();

  function formatAmount(amount) {
    try {
      return new Intl.NumberFormat(navigator.language, {
        style: "currency",
        currency: detectedCurrency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(amount);
    } catch (e) {
      return detectedCurrency + amount;
    }
  }

  // Format all amount button labels and tooltips using the user's locale and detected currency
  document.querySelectorAll(".donation-amount-btn").forEach(function(btn) {
    var amount = parseInt(btn.getAttribute("data-amount"), 10);
    var typeId = btn.getAttribute("data-type");
    var formatted = formatAmount(amount);

    var span = btn.querySelector(".amount-display");
    if (span) span.textContent = formatted;

    var template = descriptionTemplates[typeId] || "";
    if (template) btn.setAttribute("title", template.replace("{amount}", formatted));
  });

  var backdrop = document.getElementById("donation-modal-backdrop");
  var submitBtn = document.getElementById("donation-submit-btn");
  var dismissBtn = document.getElementById("donation-dismiss-btn");

  var CUSTOM_BASE = "donation-custom-btn text-xs text-action hover:underline cursor-pointer text-left bg-transparent border-0 p-0 -mt-1";

  var state = { type: defaultTypeId, amount: defaultAmount, isCustom: false };

  function updateFreqToggle() {
    document.querySelectorAll(".donation-freq-btn").forEach(function(btn) {
      var active = btn.getAttribute("data-type") === state.type;
      btn.className = FREQ_BASE + (active ? " bg-action text-white" : " bg-transparent text-text");
    });
  }

  function updateAmountGroups() {
    document.querySelectorAll(".donation-amounts-group").forEach(function(group) {
      group.style.display = group.getAttribute("data-type") === state.type ? "" : "none";
    });
  }

  function updateAmountBtns() {
    document.querySelectorAll(".donation-amount-btn").forEach(function(btn) {
      var selected = !state.isCustom &&
                     btn.getAttribute("data-type") === state.type &&
                     parseInt(btn.getAttribute("data-amount"), 10) === state.amount;
      btn.className = AMT_BASE + (selected ? " bg-action !text-white !border-action" : "");
    });
    document.querySelectorAll(".donation-custom-btn").forEach(function(btn) {
      btn.className = CUSTOM_BASE + (state.isCustom ? " font-semibold underline" : "");
    });
  }

  document.querySelectorAll(".donation-freq-btn").forEach(function(btn) {
    btn.addEventListener("click", function() {
      state.type = btn.getAttribute("data-type");
      // Keep same amount if it exists in the new type, otherwise pick first
      var group = document.querySelector('.donation-amounts-group[data-type="' + state.type + '"]');
      if (group && !group.querySelector('[data-amount="' + state.amount + '"]')) {
        var first = group.querySelector(".donation-amount-btn");
        if (first) state.amount = parseInt(first.getAttribute("data-amount"), 10);
      }
      updateFreqToggle();
      updateAmountGroups();
      updateAmountBtns();
    });
  });

  document.querySelectorAll(".donation-amount-btn").forEach(function(btn) {
    btn.addEventListener("click", function() {
      state.amount = parseInt(btn.getAttribute("data-amount"), 10);
      state.isCustom = false;
      updateAmountBtns();
    });
  });

  document.querySelectorAll(".donation-custom-btn").forEach(function(btn) {
    btn.addEventListener("click", function() {
      state.isCustom = true;
      updateAmountBtns();
    });
  });

  function closeModal() {
    backdrop.style.display = "none";
    document.body.style.overflow = "";
  }

  submitBtn.addEventListener("click", function() {
    var url = resolveLink(state.type, state.amount, detectedCurrency, state.isCustom);
    if (typeof gtag === "function") {
      gtag("event", "start_checkout", { amount: state.isCustom ? "custom" : state.amount, frequency: state.type, currency: detectedCurrency });
    }
    window.open(url, "_blank");
    closeModal();
  });

  dismissBtn.addEventListener("click", function() {
    if (typeof gtag === "function") { gtag("event", "donation_dismissed"); }
    closeModal();
  });

  backdrop.addEventListener("click", function(e) {
    if (e.target === backdrop) {
      if (typeof gtag === "function") { gtag("event", "donation_dismissed"); }
      closeModal();
    }
  });

  document.addEventListener("keydown", function(e) {
    if (e.key === "Escape" && backdrop.style.display !== "none") {
      if (typeof gtag === "function") { gtag("event", "donation_dismissed"); }
      closeModal();
    }
  });

  window.openDonationModal = function(downloadUrl) {
    state.type = defaultTypeId;
    state.amount = defaultAmount;
    state.isCustom = false;
    updateFreqToggle();
    updateAmountGroups();
    updateAmountBtns();

    var link = document.getElementById("donation-modal-manual-link");
    if (link) link.setAttribute("href", downloadUrl);

    backdrop.style.display = "flex";
    document.body.style.overflow = "hidden";

    if (typeof gtag === "function") {
      gtag("event", "generate_donation_intent", { location_id: "download_modal" });
      var fileName = downloadUrl.split("/").pop() || "";
      gtag("event", "file_download", {
        file_name: fileName,
        link_url: downloadUrl,
        file_extension: fileName.split(".").pop() || ""
      });
    }

    var a = document.createElement("a");
    a.href = downloadUrl;
    a.setAttribute("download", "");
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    setTimeout(function() { a.remove(); }, 1000);
  };
})();
})();