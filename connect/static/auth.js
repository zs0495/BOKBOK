document.addEventListener('DOMContentLoaded', async function() {
    const authMenu = document.querySelector('.auth');

    // 로그인 상태 확인
    const checkLogin = async () => {
        try {
            const res = await fetch('/api/check-login');
            const data = await res.json();
            return data.isLoggedIn;
        } catch (err) {
            console.error('로그인 상태 확인 오류:', err);
            return false;
        }
    };

    // 로그아웃 처리
    const handleLogout = async (e) => {
        e.preventDefault();
        const res = await fetch('/logout', { method: 'POST' });
        if (res.ok) {
            alert('로그아웃 되었습니다.');
            renderAuthMenu(); // 메뉴 다시 렌더링
        } else {
            alert('로그아웃 실패');
        }
    };

    // 메뉴 렌더링
    const renderAuthMenu = async () => {
        const isLoggedIn = await checkLogin();

        if (isLoggedIn) {
            authMenu.innerHTML = `
                <a href="/mypage">마이페이지</a> |
                <a href="#" id="logout-link">로그아웃</a>
            `;
            document.getElementById('logout-link').addEventListener('click', handleLogout);
        } else {
            authMenu.innerHTML = `
                <a href="/signup">회원가입</a> |
                <a href="/login" id="loginBtn">로그인</a>
            `;
            // 동적으로 생성된 로그인 버튼에 클릭 이벤트 연결
            const loginBtn = document.getElementById('loginBtn');
            if (loginBtn) {
                loginBtn.addEventListener('click', () => {
                    window.location.href = '/login';
                });
            }
        }
    };

    renderAuthMenu();
});
