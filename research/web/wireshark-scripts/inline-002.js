(function(){const siteLinks = [{"name":"Download","url":"/download.html","subLinks":[{"name":"Source Code","url":"https://gitlab.com/wireshark/wireshark/"},{"name":"Release Notes","url":"/docs/relnotes/"},{"name":"Stratoshark","url":"https://stratoshark.org"}]},{"name":"Learn","url":"/learn","subLinks":[{"name":"User's Guide","url":"/docs/wsug_html_chunked/"},{"name":"Certifications","url":"/certifications"},{"name":"FAQ","url":"/faq"},{"name":"SharkFest YouTube","url":"https://www.youtube.com/@WireSharkFest"},{"name":"About","url":"/about"}]},{"name":"Resources","url":"/resources","subLinks":[{"name":"Documentation","url":"/docs/"},{"name":"Wiki","url":"https://wiki.wireshark.org/"},{"name":"Sample Captures","url":"/resources#sample-captures"}]},{"name":"Tools","url":"/tools/","subLinks":[{"name":"OUI Lookup","url":"/tools#oui-lookup"},{"name":"WPA PSK Generator","url":"/tools/wpa-psk"},{"name":"IPv4/IPv6 Test","url":"/tools/v46status"},{"name":"Modeline Generator","url":"/tools/modelines"},{"name":"Capture Filter Generator","url":"/tools/string-cf"}]},{"name":"Community","url":"/community","subLinks":[{"name":"Mailing Lists","url":"https://lists.wireshark.org/"},{"name":"SharkFest","url":"https://sharkfest.wireshark.org"},{"name":"Podcast","url":"https://sharkbytes.transistor.fm/"},{"name":"Blog","url":"/blog"},{"name":"Ask Wireshark","url":"https://ask.wireshark.org/"},{"name":"Discord","url":"https://discord.com/invite/fT2jvkawGj"}]},{"name":"Develop","url":"/develop","subLinks":[{"name":"Get Involved","url":"/develop"},{"name":"Issue Tracker","url":"https://gitlab.com/wireshark/wireshark/-/issues"},{"name":"Developer's Guide","url":"/docs/wsdg_html_chunked/"}]},{"name":"Members","url":"/members"},{"name":"Certifications","url":"/certifications"}];

    // Responsive mobile menu toggle
    document.addEventListener("DOMContentLoaded", () => {
        const menuButton = document.getElementById("mobile-menu-button");
        const mobileMenu = document.getElementById("mobile-menu-content");
        const mobileMenuCloseButton =
            document.getElementById("mobile-menu-close");

        menuButton?.addEventListener("click", () => {
            const isExpanded =
                menuButton.getAttribute("aria-expanded") === "true";
            menuButton.setAttribute("aria-expanded", (!isExpanded).toString());
            mobileMenu?.classList.toggle("hidden");
            mobileMenu?.setAttribute("aria-hidden", isExpanded.toString());
        });

        mobileMenuCloseButton?.addEventListener("click", () => {
            menuButton?.click(); // Simulate click to close
        });

        // Optional: Close on Escape key
        document.addEventListener("keydown", (event) => {
            if (
                event.key === "Escape" &&
                menuButton?.getAttribute("aria-expanded") === "true"
            ) {
                menuButton?.click(); // Simulate click to close
            }
        });

        siteLinks.forEach((item) => {
            const subLinks = item.subLinks;
            if (subLinks) {
                const subMenu = document.getElementById(
                    `${item.name}-subLinks`,
                );
                const parentItem = document.getElementById(item.name);

                parentItem?.addEventListener("click", () => {
                    const isVisible =
                        subMenu?.classList.contains("hidden") === false;
                    subMenu?.classList.toggle("hidden", isVisible);
                    subMenu?.setAttribute("aria-hidden", isVisible.toString());
                });
            }
        });
    });
})();