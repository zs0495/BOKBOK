// script.js
document.addEventListener("DOMContentLoaded", () => {
  const loginBtn = document.getElementById("loginBtn");
  const loginModal = document.getElementById("loginModal");

  loginBtn.addEventListener("click", (e) => {
    e.preventDefault();
    loginModal.style.display = "flex";
  });

  loginModal.addEventListener("click", (e) => {
    if (e.target === loginModal) {
      loginModal.style.display = "none";
    }
  });
});
