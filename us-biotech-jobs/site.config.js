// Site settings. Edit this file to switch on email sign-up and Google AdSense ads.
// Nothing here is secret: it is read by visitors' browsers.
window.SITE_CONFIG = {
  // ---- Email updates (Brevo) ------------------------------------------------
  // In Brevo, make three contact lists (daily, weekly, monthly) and one sign-up form for each
  // list (Contacts > Forms > Create a subscription form; send to that list). For each form,
  // open Share > "HTML code" and copy the form's action address, which looks like
  //   https://xxxxxxxx.sibforms.com/serve/MUIFA...
  // and paste it below. Visitors' choice of daily / weekly / monthly picks the form.
  newsletter: {
    provider: "brevo",           // "brevo", "buttondown" or "custom"
    brevoForms: { daily: "", weekly: "", monthly: "" },
    // Buttondown instead: provider "buttondown" and your username here
    username: "",
    // Another service: provider "custom", its form address and field names
    action: "",
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
