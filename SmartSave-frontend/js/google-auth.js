window.GoogleAuth = {
  init({ buttonId, errorId, text, redirectUrl }) {
    const button = document.getElementById(buttonId);
    const error = document.getElementById(errorId);
    const showError = (message) => {
      error.textContent = message;
      error.classList.add('show');
    };

    if (!window.GOOGLE_CLIENT_ID) {
      showError('Google sign-in needs a Google OAuth client ID in js/config.js.');
      return;
    }

    const renderButton = () => {
      if (!window.google?.accounts?.id) {
        showError('Google sign-in could not load. Check your connection and try again.');
        return;
      }

      window.google.accounts.id.initialize({
        client_id: window.GOOGLE_CLIENT_ID,
        callback: async ({ credential }) => {
          error.classList.remove('show');
          button.setAttribute('aria-busy', 'true');
          try {
            await API.loginWithGoogle(credential);
            window.location.href = redirectUrl;
          } catch (err) {
            showError(err.message || 'Google sign-in failed. Please try again.');
            button.removeAttribute('aria-busy');
          }
        },
      });
      window.google.accounts.id.renderButton(button, {
        theme: 'outline',
        size: 'large',
        shape: 'pill',
        text,
        width: Math.min(button.parentElement.clientWidth, 400),
      });
    };

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = renderButton;
    script.onerror = () => showError('Google sign-in could not load. Check your connection and try again.');
    document.head.appendChild(script);
  },
};
