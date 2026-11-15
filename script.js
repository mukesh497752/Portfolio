(() => {
  const menuButton = document.querySelector(".menu-toggle");
  const navigation = document.querySelector("#primary-navigation");
  const contactForm = document.querySelector("#contact-form");
  const status = document.querySelector("#form-status");
  const configNote = document.querySelector("#form-config-note");
  const submitButton = contactForm.querySelector('button[type="submit"]');

  document.querySelector("#current-year").textContent = new Date().getFullYear();

  const closeMenu = () => {
    menuButton.setAttribute("aria-expanded", "false");
    navigation.classList.remove("is-open");
  };

  menuButton.addEventListener("click", () => {
    const isOpen = menuButton.getAttribute("aria-expanded") === "true";
    menuButton.setAttribute("aria-expanded", String(!isOpen));
    navigation.classList.toggle("is-open", !isOpen);
  });

  navigation.addEventListener("click", (event) => {
    if (event.target.closest("a")) closeMenu();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMenu();
  });

  const apiUrl = (window.PORTFOLIO_API_URL || "").replace(/\/+$/, "");
  if (!apiUrl) {
    configNote.hidden = false;
    submitButton.disabled = true;
    submitButton.setAttribute("aria-describedby", "form-config-note");
    submitButton.classList.add("is-disabled");
  }

  contactForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!apiUrl) return;

    status.textContent = "";
    submitButton.disabled = true;
    submitButton.querySelector("span:first-child").textContent = "Sending…";

    const formData = new FormData(contactForm);
    const payload = Object.fromEntries(formData.entries());

    try {
      const response = await fetch(`${apiUrl}/api/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => null);
        throw new Error(error?.detail || "Your message could not be sent. Please try again.");
      }

      contactForm.reset();
      status.textContent = "Thanks for reaching out. Your message has been sent.";
    } catch (error) {
      status.textContent = error.message || "Something went wrong. Please try again or email me directly.";
    } finally {
      submitButton.disabled = false;
      submitButton.querySelector("span:first-child").textContent = "Send message";
    }
  });
})();
