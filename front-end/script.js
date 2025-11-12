// script.js
document.addEventListener("DOMContentLoaded", () => {
    const loginBtn = document.getElementById("loginBtn");
    const loginModal = document.getElementById("loginModal");
    const closeBtn = document.querySelector('.close-btn');


    loginBtn.addEventListener("click", (e) => {
        e.preventDefault();
        loginModal.style.display = "flex";
    });

    loginModal.addEventListener("click", (e) => {
        if (e.target === loginModal) {
        loginModal.style.display = "none";
        }
    });

    // 닫기 버튼 클릭 시 팝업 닫기
    closeBtn.addEventListener('click', () => {
        loginModal.style.display = 'none';
    });

    // 배경(모달 바깥) 클릭 시 닫기
    window.addEventListener('click', (e) => {
        if (e.target === loginModal) {
        loginModal.style.display = 'none';
        }
    });
});
