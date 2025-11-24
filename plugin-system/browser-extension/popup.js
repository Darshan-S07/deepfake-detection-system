document.addEventListener('DOMContentLoaded', async () => {
    const status = document.getElementById('status');
    const risk = document.getElementById('risk');
    chrome.storage.local.get('lastRisk', data => {
      risk.textContent = 'Risk: ' + (data.lastRisk || '-');
    });
    const [tab] = await chrome.tabs.query({active: true, lastFocusedWindow: true});
    status.textContent = `Active tab: ${tab?.title || '-'}`;
    document.getElementById('clear').onclick = () => {
      chrome.storage.local.remove('lastRisk', () => {
        risk.textContent = 'Risk: -';
        chrome.action.setBadgeText({text: ''});
      });
    };
  });
  document.addEventListener("DOMContentLoaded", () => {
  const loginBtn = document.getElementById("login-btn");

  loginBtn.addEventListener("click", async () => {
      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;

      const form = new URLSearchParams();
      form.append("username", username);
      form.append("password", password);

      try {
          const res = await fetch("http://localhost:8000/auth/login", {
              method: "POST",
              body: form
          });

          const data = await res.json();

          if (data.access_token) {
              chrome.storage.local.set({
                  token: data.access_token,
                  username: data.username,
                  user_id: data.user_id
              });

              alert("Logged in successfully!");
          } else {
              alert("Login failed: " + data.detail);
          }
      } catch (err) {
          alert("Server connection error. Is backend running?");
      }
  });
});
