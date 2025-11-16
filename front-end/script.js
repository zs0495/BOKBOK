// script.js
document.addEventListener("DOMContentLoaded", () => {
    // 슬라이더 요소 가져오기
    const sliderContainer = document.querySelector(".slider-container");
    const prevBtn = document.querySelector(".prev");
    const nextBtn = document.querySelector(".next");
    const dots = document.querySelectorAll(".dot");
    const slides = document.querySelectorAll(".slide");

    let currentIndex = 0;
    const totalSlides = slides.length; // 슬라이드 개수 (3개)

    // 슬라이드 위치 업데이트 함수
    function updateSlider() {
        // sliderContainer의 transform 속성을 변경하여 슬라이드를 이동시킵니다.
        // 현재 인덱스에 따라 -0%, -100%, -200% 등으로 이동
        sliderContainer.style.transform = `translateX(-${currentIndex * 100}%)`;

        // 인디케이터 업데이트
        dots.forEach((dot, index) => {
            if (index === currentIndex) {
                dot.classList.add("active");
            } else {
                dot.classList.remove("active");
            }
        });
    }

    // 다음 슬라이드 버튼 클릭
    nextBtn.addEventListener("click", () => {
        currentIndex = (currentIndex + 1) % totalSlides; // 다음 인덱스
        updateSlider();
    });

    // 이전 슬라이드 버튼 클릭
    prevBtn.addEventListener("click", () => {
        currentIndex = (currentIndex - 1 + totalSlides) % totalSlides; // 이전 인덱스
        updateSlider();
    });

    // 인디케이터 클릭
    dots.forEach((dot, index) => {
        dot.addEventListener("click", () => {
            currentIndex = index; // 클릭된 인디케이터에 해당하는 슬라이드로 이동
            updateSlider();
        });
    });

    // 초기 슬라이더 상태 설정 (첫 번째 슬라이드 활성화)
    updateSlider();
});
