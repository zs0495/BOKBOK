# mypage.py

# Flask 웰페어 애플리케이션 - 마이페이지 및 찜하기 통합 버전 (외부 인증 및 기본 페이지 라우트 제외)
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import pymysql 
import pymysql.cursors
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# Flask 애플리케이션 초기화
app = Flask(__name__)

# 세션 사용을 위한 secret_key 필수
app.secret_key = "your_secret_key_here_1234" 

# ==========================================================
# 데이터베이스 연결
# ==========================================================
def get_db():
    """MySQL 데이터베이스 연결을 설정하고 DictCursor를 반환"""
    try:
        db = pymysql.connect(
            host='localhost', 
            port=3306,
            user='root', 
            password='Aa0205!!?',  # 실제 MySQL 비밀번호
            db='welfaredb', 
            charset='utf8mb4', 
            autocommit=False,
            cursorclass=pymysql.cursors.DictCursor
        )
        return db
    except Exception as e:
        logging.error(f"데이터베이스 연결 실패: {e}")
        return None

# ==========================================================
# API - 로그인 상태 확인 및 로그아웃
# ==========================================================
@app.route('/api/check-login')
def check_login():
    return jsonify({
        'isLoggedIn': session.get('logged_in', False),
        'username': session.get('username', None)
    })

# 로그아웃 (이 파일에 유지)
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

# ==========================================================
# 마이페이지 (찜한 복지 목록 포함)
# ==========================================================
@app.route('/mypage')
def mypage():
    # 로그인 확인 및 외부 로그인 폼으로 리다이렉트 (main.py에 login_form이 있다고 가정)
    # 'login_form'은 main_integrated.py에 정의된 라우트 이름입니다.
    if not session.get('logged_in'):
        return redirect(url_for('login_form', message='로그인이 필요한 서비스입니다.'))
    
    username = session.get('username')
    user_no = session.get('user_no') # ⭐ 필수: 외부 로그인 로직이 이 값을 세션에 설정해야 함
    
    # user_no가 세션에 없는 경우 (외부 로그인 로직 오류 또는 세션 문제)
    if not user_no:
        session.clear()
        return redirect(url_for('login_form', message='세션 정보가 부족합니다. 다시 로그인해주세요.'))

    db = get_db()
    if not db:
        return render_template('mypage.html', username=username, user_info={}, favorites=[], error="DB 연결 오류")

    try:
        cur = db.cursor()

        # 1. 사용자 기본 정보 읽기 (user_no 사용)
        sql_info = """
        SELECT name, birth_year, birth_month, city, district, situation 
        FROM personal_info 
        WHERE user_no=%s
        """
        cur.execute(sql_info, (user_no,))
        user_info = cur.fetchone()

        # 2. 찜한 복지 정보 읽기 (JOIN 사용)
        sql_fav = """
        SELECT b.benefit_name, s.site_name AS institution
        FROM favorite_benefit fb
        JOIN benefits b ON fb.benefit_no = b.benefit_no
        JOIN sites s ON fb.site_id = s.site_id
        WHERE fb.user_no = %s
        """
        cur.execute(sql_fav, (user_no,))
        favorites = cur.fetchall()

        return render_template('mypage.html', 
            username=username, 
            user_info=user_info if user_info else {}, 
            favorites=favorites)

    except Exception as e:
        logging.error(f"마이페이지 오류: {e}")
        return render_template('mypage.html', username=username, user_info={}, favorites=[], error="데이터 조회 중 오류 발생")
    finally:
        if db:
            db.close()

@app.route('/edit-profile')
def edit_profile():
    if not session.get('logged_in'):
        return redirect(url_for('login_form', message='로그인이 필요한 서비스입니다.'))
    return "정보 수정 페이지 (준비중)"

# ==========================================================
# 찜하기/취소 API
# ==========================================================
@app.route('/api/favorite', methods=['POST'])
def handle_favorite():
    # 1. 로그인 확인 및 user_no 가져오기
    if not session.get('logged_in') or 'user_no' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    user_no = session['user_no'] # ⭐ 필수: 외부 로그인 로직이 이 값을 세션에 설정해야 함
    
    # 2. 요청 데이터 파싱 및 유효성 검사
    data = request.json
    benefit_no = data.get('benefit_no')
    site_id = data.get('site_id')
    
    try:
        benefit_no = int(benefit_no)
        site_id = int(site_id)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '유효하지 않은 복지 번호 또는 사이트 ID입니다.'}), 400

    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'DB 연결 실패'}), 500

    cur = db.cursor()
    
    try:
        # 3. 찜 상태 확인
        sql_check = """
        SELECT user_no FROM favorite_benefit 
        WHERE user_no=%s AND benefit_no=%s AND site_id=%s
        """
        cur.execute(sql_check, (user_no, benefit_no, site_id))
        is_favorited = cur.fetchone()
        
        message = ""

        if is_favorited:
            # 4. 이미 찜한 경우: 찜하기 취소 (DELETE)
            sql_delete = """
            DELETE FROM favorite_benefit 
            WHERE user_no=%s AND benefit_no=%s AND site_id=%s
            """
            cur.execute(sql_delete, (user_no, benefit_no, site_id))
            db.commit()
            message = "찜하기가 취소되었습니다."
            action = "unfavorited"
        else:
            # 5. 찜하지 않은 경우: 찜하기 저장 (INSERT)
            sql_insert = """
            INSERT INTO favorite_benefit (user_no, benefit_no, site_id) 
            VALUES (%s, %s, %s)
            """
            cur.execute(sql_insert, (user_no, benefit_no, site_id))
            db.commit()
            message = "찜하기가 저장되었습니다."
            action = "favorited"
            
        return jsonify({
            'success': True, 
            'message': message, 
            'action': action,
            'is_favorited': not is_favorited # 최종 상태: 찜하기 취소 시 False, 저장 시 True
        })
        
    except Exception as e:
        db.rollback()
        logging.exception(f"찜하기 처리 중 예외 발생: {e}")
        return jsonify({'success': False, 'message': '찜하기 처리 중 오류가 발생했습니다.'}), 500
    finally:
        if db:
            db.close()

# ==========================================================
# 실행
# ==========================================================
if __name__ == '__main__':
    app.run(debug=True)
