
    document.addEventListener("DOMContentLoaded", () => {
        const banners = document.querySelectorAll(".banner-ad-link");
        banners.forEach((banner) => {
            banner.addEventListener("click", (e) => {
                let url = banner.getAttribute("href");

                if (!url) {
                    const anchor = banner.querySelector("a");
                    if (anchor) url = anchor.getAttribute("href");
                }

                if (url && typeof window.gtag === "function") {
                    console.log("Sending GA4 event", { url });
                    window.gtag("event", "banner_click", {
                        event_category: "engagement",
                        event_label: url,
                        transport_type: "beacon",
                        debug_mode: true,
                    });
                }
            });
        });
    });
