// script.js
document.addEventListener("DOMContentLoaded", function () {
  const container = document.querySelector(".slider-container");
  const slides = document.querySelectorAll(".slide");
  const slideCount = slides.length;

  let currentIndex = 0;
  const slideWidth = 100; // % 단위
  const intervalTime = 3000; // 3초

  function moveToNextSlide() {
    currentIndex++;

    if (currentIndex >= slideCount) {
      currentIndex = 0;
    }

    container.style.transform = `translateX(-${currentIndex * slideWidth}%)`;
  }

  setInterval(moveToNextSlide, intervalTime);
  // 초기 슬라이더 상태 설정 (첫 번째 슬라이드 활성화)
    updateSlider();
});


