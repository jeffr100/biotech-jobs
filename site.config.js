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
    brevoForms: {
      daily:   "https://8361b465.sibforms.com/serve/MUIFADjWMa1K2BS1cHjGXyoawA4nDXo0TXp4bhXBiwYGbq3eaCnKgwtYqynkk-pfdpD4OlHN8DKu4jW0TUUvbVi7Vz6sOrLP1i6NWbsa9CQZo91RCUuZT9rHtynjn_fPLAvYmxvfd8JsawT_UvgE_h0vT6uKSCYkz324dhiMZ6vwjOEMbt8m46Ij9kSQduPSkmxgY9GQlpem2UMgzg",
      weekly:  "https://8361b465.sibforms.com/serve/MUIFAAGT9UvXfAzDpNBE1dvu9lftqKC_ZI-JMXSwWdDbm-0O2586ELUlu2cTGROAEv0Q0TTte8VIKMArWsO23fQ1iX9jabYBxBGvvIt0fqJ7PA4EQJaVhxRQBYsDmVO2zSlBRhHb5KTb52HL9KDxQqE6NEokF_6HHFNnFm3EbGMbaeosiqZ5tPf9GWQ4lFTVWJ1lpaczSgd8hLuVfA",
      monthly: "https://8361b465.sibforms.com/serve/MUIFAPLV9CS1D_3Bv6wu079sJWwNWkdKOEbpjTeW-RDGt9XZyAs-n64R6j4bAv5nNhlsUaqzxV5rKQrnK1vwCybGeNiqZrCkN9aS0YKUHBZpFkyJrZnJSG1vviUrNuI_rBRCTKXITzMzjTRAuya_RvziVbFualkQg3q63clctDWBRi0KgF8F3c07H1qrSF21iGUUI3WHHSdinHZn_g"
    },
    // Personal job alerts: a Brevo form that saves the visitor's filters on their contact.
    // Fill in the form address once that form exists (see crawler/alerts.py).
    alerts: { form: "", filtersField: "BIO_ALERT", freqField: "BIO_ALERT_FREQ" },
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
