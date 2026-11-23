// Site settings. Edit this file to switch on email sign-up and Google AdSense ads.
// Nothing here is secret: it is read by visitors' browsers.
window.SITE_CONFIG = {
  // ---- Email updates -------------------------------------------------------
  // Buttondown (https://buttondown.com) is the default. Put your Buttondown username here,
  // e.g. "biotechjobs". Sign-ups are tagged "daily", "weekly" or "monthly", and
  // crawler/publish.py sends each group its own digest (see README).
  newsletter: {
    provider: "buttondown",      // "buttondown" or "custom"
    username: "",                // Buttondown username; leave blank until you have one
    // For another service, set provider: "custom" and give its form address and field names:
    action: "",                  // e.g. "https://example.com/subscribe"
    emailField: "email",
    frequencyField: "tag"
  },

  // ---- Google AdSense: small text ads ---------------------------------------
  // Google no longer offers "text only" display units. Small text ads now come from
  // native In-feed ad units styled with the "Text only" template. In AdSense:
  //   Ads > By ad unit > In-feed ads > "Manual" style > template "Text only"
  // Create one unit per spot below and copy its data-ad-slot and data-ad-layout-key here.
  // After approval, paste your publisher ID ("ca-pub-…") and copy ads.txt.example to ads.txt.
  adsense: {
    client: "",                  // e.g. "ca-pub-1234567890123456"
    slots: {
      top:  { slot: "", layoutKey: "" },   // 3rd item in the job list
      feed: { slot: "", layoutKey: "" },   // repeats inside the job list
      side: { slot: "", layoutKey: "" }    // under the sign-up box in the sidebar (desktop)
    },
    feedEvery: 25,               // a text ad after every N jobs
    showPlaceholders: true,      // while client is blank, show outlines where the ads will go
    disableOnGithubPages: true   // no ads (or outlines) when the site is served from *.github.io
  }
};
