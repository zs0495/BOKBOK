document.addEventListener("DOMContentLoaded", () => {
    const tbody = document.getElementById("resourceTableBody");
    const filterButtons = document.querySelectorAll(".library-filter");

    // 테이블 화면에 표시
    function renderResources(list) {
        tbody.innerHTML = ""; // 첫 시작 초기화 

        list.forEach((item) => {
          const tr = document.createElement("tr");

          const orgTd = document.createElement("td");
          orgTd.textContent = item.orgName;

          const benefitTd = document.createElement("td");
          benefitTd.textContent = item.benefitName;

          tr.appendChild(orgTd);
          tr.appendChild(benefitTd);
          tbody.appendChild(tr);
        });
    }

    // 테이블 가져오기
    // type: PUBLIC PRIVATE 중 인자 받기
    function loadResources(type) {
    fetch("test.php?type=${type}") // php 파일 연결
      .then((res) => {
        if (!res.ok) throw new Error("서버 응답 오류");
        return res.json();
      })
      .then((data) => {
        renderResources(data); // 표로 출력
      })
      .catch((err) => {
        console.error(err);

        // 테스트 데이터(임시)
        const dummyPublic = [
          { orgName: "서울시청", benefitName: "청년 월세 지원" },
          { orgName: "보건복지부", benefitName: "기초생활 수급자 지원" }
        ];
        const dummyPrivate = [
          { orgName: "사회복지공동모금회", benefitName: "긴급 생계비 지원" },
          { orgName: "○○장학재단", benefitName: "저소득층 장학금" }
        ];

        renderResources(type === "PUBLIC" ? dummyPublic : dummyPrivate);
        // 여기까지 임시
      });
    }

  // 공공 <-> 민간 선택에 따라
  filterButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const type = btn.dataset.type;

      // active 변경
      filterButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      loadResources(type); // 공공/민간에 따라서 데이터 불러오는 함수 추후 추가필요
    });
  });

  // 페이지 처음 들어왔을 때는 공공 복지 기준으로 로딩
  loadResources("PUBLIC");
});