const form = document.getElementById("loginForm");
const statusEl = document.getElementById("status");

form.addEventListener("submit", (event) => {
    event.preventDefault();

    const formData = new FormData(form);
    const email = String(formData.get("email") || "").trim();
    const password = String(formData.get("password") || "").trim();

    if (!email || !email.includes("@")) {
        statusEl.textContent = "Please enter a valid email address.";
        statusEl.className = "status error";
        return;
    }

    if (password.length < 8) {
        statusEl.textContent = "Password must be at least 8 characters.";
        statusEl.className = "status error";
        return;
    }

    statusEl.textContent = "Signed in successfully (demo mode).";
    statusEl.className = "status success";
});
