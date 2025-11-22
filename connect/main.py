# Flask 웰페어 애플리케이션 - 통합 버전
from flask import Flask, request, render_template, redirect, url_for
import pymysql 
import pymysql.cursors
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# Flask 애플리케이션 초기화
app = Flask(__name__)

# ==========================================================
# 데이터베이스 연결
# ==========================================================
def get_db():
    """MySQL 데이터베이스 연결을 설정하고 DictCursor를 반환"""
    try:
        db = pymysql.connect(
            host='localhost', 
            port=3308,
            user='root', 
            password='Aa0205!!?',  # 실제 MySQL 비밀번호
            db='welfaredb', 
            charset='utf8mb4', 
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor
        )
        return db
    except Exception as e:
        logging.error(f"데이터베이스 연결 실패: {e}")
        return None

# ==========================================================
# 인증 관련 라우트 (로그인/회원가입)
# ==========================================================
# 로그인 폼
@app.route('/login', methods=['GET'])
def login_form():
    """로그인 폼 페이지를 렌더링합니다."""
    message = request.args.get('message', '아이디와 비밀번호를 입력해주세요.')
    return render_template("login.html", message=message)

# 로그인 처리
@app.route('/login', methods=['POST'])
def login():
    """로그인 요청을 처리하고, 성공/실패 여부에 따라 리다이렉트합니다."""
    username = request.form['username']
    password = request.form['password']
    db = get_db()
    
    if not db:
        return redirect(url_for('login_form', message="시스템 오류: DB 연결 실패"))
    
    cur = db.cursor()
    
    try:
        sql = "SELECT username, password FROM personal_info WHERE username=%s"
        cur.execute(sql, (username,))
        user = cur.fetchone()

        if user and check_password_hash(user['password'], password):
            # 로그인 성공
            return redirect(url_for('index', message=f"'{username}'님, 로그인 성공!"))
        else:
            # 로그인 실패
            return redirect(url_for('login_form', message="로그인 실패 - 아이디 또는 비밀번호를 확인하세요."))

    except Exception as e:
        logging.error(f"로그인 처리 중 오류 발생: {e}")
        return redirect(url_for('login_form', message="로그인 처리 중 시스템 오류가 발생했습니다."))
    finally:
        if db:
            db.close()

# 회원가입 폼
@app.route('/signup', methods=['GET'])
def signup_form():
    """회원가입 폼을 렌더링합니다."""
    message = request.args.get('message', '모든 정보를 입력해주세요.')
    return render_template('signup.html', message=message)
    
# 회원가입 처리
@app.route('/signup', methods=['POST'])
def signup():
    """회원가입 데이터를 처리하고 데이터베이스에 저장합니다."""
    username = request.form.get('username')
    password = request.form.get('password')
    name = request.form.get('name')
    birth_year = request.form.get('birth_year')
    birth_month = request.form.get('birth_month')
    phone = request.form.get('phone')
    city = request.form.get('city')
    district = request.form.get('district')
    situation = request.form.get('situation')

    # 1. 데이터 유효성 검사
    if not password or len(password) < 8:
        return redirect(url_for('signup_form', message="비밀번호는 최소 8자 이상이어야 합니다."))
    
    if not all([username, password, name, birth_year, birth_month, city, district]):
        return redirect(url_for('signup_form', message="필수 항목을 모두 입력해주세요."))
    
    # 생년월 유효성 검사
    try:
        birth_year = int(birth_year)
        birth_month = int(birth_month)
        
        if birth_year < 1900 or birth_year > date.today().year:
            return redirect(url_for('signup_form', message="올바른 생년을 입력해주세요."))
        
        if birth_month < 1 or birth_month > 12:
            return redirect(url_for('signup_form', message="생월은 1-12 사이여야 합니다."))
            
    except ValueError:
        return redirect(url_for('signup_form', message="생년월을 숫자로 입력해주세요."))
 
    # 2. 비밀번호 해싱 및 DB 연결
    hashed_password = generate_password_hash(password)
    
    db = get_db()
    if not db:
        return redirect(url_for('signup_form', message="시스템 오류: DB 연결 실패."))
    
    cur = db.cursor()

    try:
        # 중복 체크
        cur.execute("SELECT username FROM personal_info WHERE username=%s", (username,))
        if cur.fetchone():
            return redirect(url_for('signup_form', message="이미 존재하는 아이디입니다."))

        # personal_info table에 삽입
        sql = """
        INSERT INTO personal_info 
        (username, password, name, birth_year, birth_month, phone, city, district, situation) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(sql, (
            username, 
            hashed_password, 
            name, 
            birth_year, 
            birth_month, 
            phone, 
            city, 
            district,
            situation
        ))
            
        return redirect(url_for('login_form', message="회원가입 성공! 이제 로그인 해주세요."))

    except pymysql.Error as e:
        logging.error(f"MySQL 오류 발생: {e}")
        return redirect(url_for('signup_form', message=f"DB 오류 발생: {e}"))
    except Exception as e:
        logging.error(f"회원가입 처리 중 오류 발생: {e}")
        return redirect(url_for('signup_form', message="회원가입 처리 중 시스템 오류가 발생했습니다."))
    finally:
        if db:
            db.close()

# ==========================================================
# 메인 페이지 라우트
# ==========================================================
@app.route('/')
def index():
    """메인 페이지 (index.html)를 렌더링합니다."""
    message = request.args.get('message', None)
    return render_template('index.html', message=message)

# ==========================================================
# 네비게이션 메뉴 라우트
# ==========================================================
@app.route('/service')
def service_page():
    """서비스 개요 페이지 (service.html)를 렌더링합니다."""
    return render_template('service.html')

@app.route('/team')
def team_page():
    """팀 소개 페이지 (team.html)를 렌더링합니다."""
    return render_template('team.html')

@app.route('/public')
def public_page():
    """공공 복지 검색 페이지 (public.html)를 렌더링합니다."""
    return render_template('public.html')

@app.route('/private')
def private_page():
    """민간 복지 검색 페이지 (private.html)를 렌더링합니다."""
    return render_template('private.html')

@app.route('/library')
def library_page():
    """자료실 페이지 (library.html)를 렌더링합니다."""
    return render_template('library.html')

@app.route('/guide')
def guide_page():
    """이용 가이드 페이지 (guide.html)를 렌더링합니다."""
    return render_template('guide.html')

@app.route('/faq')
def faq_page():
    """FAQ 페이지 (faq.html)를 렌더링합니다."""
    return render_template('faq.html')

# ==========================================================
# 피처 섹션 (Feature Section) 라우트
# ==========================================================
@app.route('/gong')
def gong_benefits_page():
    """공공 복지 혜택 페이지 (gong.html)를 렌더링합니다."""
    return render_template('gong.html')

@app.route('/min')
def min_benefits_page():
    """민간 복지 혜택 페이지 (min.html)를 렌더링합니다."""
    return render_template('min.html')

# ==========================================================
# 애플리케이션 실행
# ==========================================================
if __name__ == '__main__':
    # 디버그 모드로 애플리케이션 실행
    app.run(debug=True)