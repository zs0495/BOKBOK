// auth.js 파일 내용

document.addEventListener('DOMContentLoaded', function() {
    const authMenu = document.querySelector('.auth');

    // 1. 로그인 상태 확인: localStorage의 'isLoggedIn' 값을 사용
    let isLoggedIn = localStorage.getItem('isLoggedIn') === 'true'; 

    function handleLogout(e) {
        e.preventDefault();
        
        // 2. 로그아웃 처리: localStorage 상태 변경
        localStorage.setItem('isLoggedIn', 'false');
        
        alert('로그아웃 되었습니다. 초기화면으로 돌아갑니다.');
        
        // 3. 페이지 새로고침 또는 메뉴를 로그아웃 상태로 다시 렌더링
        // 메인 페이지(index.html)로 이동하는 것이 일반적입니다.
        window.location.href = 'index.html'; // 예시: index.html로 이동
    }

    function renderAuthMenu() {
        if (isLoggedIn) {
            // 로그인 상태: 마이페이지 | 로그아웃
            authMenu.innerHTML = `
                <a href="mypage.html">마이페이지</a> | <a href="#" id="logout-link">로그아웃</a>
            `;
            
            // 로그아웃 이벤트 리스너 연결
            const logoutLink = document.getElementById('logout-link');
            if (logoutLink) {
                logoutLink.addEventListener('click', handleLogout);
            }

        } else {
            // 로그아웃 상태: 회원가입 | 로그인
            authMenu.innerHTML = `
                <a href="signup.html">회원가입</a> | <a href="login.html" id="loginBtn">로그인</a>
            `;
        }
    }
    
    // 초기 메뉴 렌더링 실행
    renderAuthMenu();
});