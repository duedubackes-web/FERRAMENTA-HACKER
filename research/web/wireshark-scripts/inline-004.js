(function(){const placeholderId = "yt-r292mofwzh";
const linkUrl = "https://www.youtube.com/embed/p0aAt3iB398";

    {/* // This script is used to create a YouTube video placeholder that loads the video when clicked. */}
    {/* // setTimeout is used to ensure that the DOM is fully loaded before adding the event listener. */}
    setTimeout(() => {
      document
        .getElementById(placeholderId)
        .addEventListener("click", function () {
          const container = this;
          let url = linkUrl;
          // Add autoplay=1 to the YouTube URL
          if (url && url.includes("youtube.com")) {
            const hasQuery = url.includes("?");
            url += (hasQuery ? "&" : "?") + "autoplay=1";
          } else if (url && url.includes("youtu.be")) {
            // Convert youtu.be short URL to embed and add autoplay
            const videoId = url.split("/").pop();
            url = `https://www.youtube.com/embed/${videoId}?autoplay=1`;
          }
          const iframe = document.createElement("iframe");
          iframe.src = url;
          iframe.className = "w-full h-full top-0 left-0 absolute";
          iframe.allow =
            "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
          iframe.allowFullscreen = true;
          container.innerHTML = "";
          container.appendChild(iframe);
        });
    }, 0);
  })();