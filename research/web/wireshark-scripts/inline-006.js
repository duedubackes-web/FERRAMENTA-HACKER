(function(){const placement = "homepage";

    document.querySelectorAll('.partner-link').forEach(function(link) {
        link.addEventListener('click', function() {
            const partnerName = link.getAttribute('data-partner') || 'unknown';
            if (typeof gtag !== 'undefined') {
                gtag('event', 'partner_click', {
                    partner_name: partnerName,
                    placement: placement
                });
            }
        });
    });
})();