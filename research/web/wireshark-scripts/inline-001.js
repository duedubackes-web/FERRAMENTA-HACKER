
            window.dataLayer = window.dataLayer || [];
            function gtag() {
                dataLayer.push(arguments);
            }
            gtag("js", new Date());

            gtag("config", "G-YLHRKD6LH6");

            // Track donation intent clicks
            document.addEventListener("DOMContentLoaded", function() {
                // Header donate button
                const headerDonate = document.getElementById("donate-button");
                if (headerDonate) {
                    headerDonate.addEventListener("click", function() {
                        gtag("event", "generate_donation_intent", { location_id: "header" });
                    });
                }

                // Footer and sidebar donate links
                document.querySelectorAll('a[href*="wiresharkfoundation.org/donate"]').forEach(function(link) {
                    if (link.id === "donate-button") return; // Skip header button (already handled)

                    let location_id = "sidebar";
                    if (link.closest("footer")) {
                        location_id = "footer";
                    }

                    link.addEventListener("click", function() {
                        gtag("event", "generate_donation_intent", { location_id: location_id });
                    });
                });
            });
        