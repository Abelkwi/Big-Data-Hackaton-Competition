window.GoogleVerification = (() => {
  let credential = null;
  let initialized = false;

  function loadGoogleScript() {
    if (window.google?.accounts?.id) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const existing = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
      if (existing) {
        existing.addEventListener("load", resolve, { once: true });
        existing.addEventListener("error", reject, { once: true });
        return;
      }
      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  async function init({ buttonId, errorId, emailInputId }) {
    const button = document.getElementById(buttonId);
    const error = document.getElementById(errorId);
    const emailInput = document.getElementById(emailInputId);
    const showError = message => {
      error.textContent = message;
      error.hidden = false;
    };
    emailInput.addEventListener("input", () => {
      credential = null;
      button.textContent = "Verify with Google";
      error.hidden = true;
    });

    button.addEventListener("click", async () => {
      error.hidden = true;
      const email = document.getElementById(emailInputId).value.trim().toLowerCase();
      if (!email) {
        showError("Enter your registration email address before verifying.");
        return;
      }
      if (!window.GOOGLE_CLIENT_ID) {
        showError("Google verification is not configured. Please contact support.");
        return;
      }

      button.disabled = true;
      try {
        await loadGoogleScript();
        if (!initialized) {
          window.google.accounts.id.initialize({
            client_id: window.GOOGLE_CLIENT_ID,
            callback: async ({ credential: idToken }) => {
              try {
                const result = await API.verifyGoogleCredential(idToken);
                if (result.email.toLowerCase() !== email) {
                  credential = null;
                  showError("Use the same Google email address as your registration email.");
                  button.disabled = false;
                  return;
                }
                credential = idToken;
                button.textContent = "Google email verified";
                button.disabled = false;
                error.hidden = true;
              } catch (verificationError) {
                credential = null;
                showError(verificationError.message || "Google verification failed. Please try again.");
                button.disabled = false;
              }
            },
          });
          initialized = true;
        }
        window.google.accounts.id.prompt(notification => {
          if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
            showError("Google verification did not open. Check your browser settings and try again.");
            button.disabled = false;
          }
        });
      } catch (loadError) {
        showError("Google verification could not load. Check your connection and try again.");
        button.disabled = false;
      }
    });
  }

  return {
    init,
    getCredential() {
      return credential;
    },
  };
})();
