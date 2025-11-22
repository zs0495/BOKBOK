#찜하기 찜하기 취소하기 코드
from flask import Flask, render_template, session, redirect, url_for
import pymysql

app = Flask(__name__)
app.secret_key = "SECRET_KEY"

#MYSQL 연결함수
def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='PASSWORD',
        db='welfaredb',
        charset='utf8mb4',
        autocommit=True
    )

#마이페이지 라우트
@app.route('/mypage')
def mypage():
    if 'user_no' not in session:
        return redirect('/login')

    user_id = session['user_no']
    db = get_db()
    try:
        cur = db.cursor(pymysql.cursors.DictCursor)

        #전체 혜택 목록
        cur.execute("SELECT s.site_name, b.title AS benefit_title
            FROM benefits b
            JOIN sites s ON s.site_id = b.site_id
            ORDER BY b.benefit_no ")
        benefits = cur.fetchall()

       
       
       #찜한 항목
@app.route('/liked')
def liked():
    if 'user_no' not in session:
        return redirect('/login')

    user_id = session['user_no']
    db = get_db()
    try:
        cur = db.cursor(pymysql.cursors.DictCursor)

        cur.execute("SELECT fb.user_no, s.site_name, b.title AS benefit_title, b.description
            FROM favorite_benefit fb
            JOIN sites s ON fb.site_id = s.site_id
            JOIN benefits b ON fb.benefit_no = b.benefit_no
            WHERE fb.user_no = %s
            ORDER BY fb.benefit_no", (user_id,))
        liked_raw = cur.fetchall()
        liked_set = {row['benefit_no'] for row in liked_raw}
    finally:
        db.close()
        
    #프론트엔드 (임시)mypage.html 만들면 연결하기 -> 마이페이지
    return render_template("mypage.html", benefits=benefits, liked_set=liked_set)





#찜하기 라우트
@app.route('/like/<int:benefit_no>')
def like(benefit_no):
    if 'user_no' not in session:
        return redirect('/login')
    user_no = session['user_no']
    db = get_db()

    
    try:
    
    # benefit_no로 site_id 조회
     cur.execute("SELECT site_id FROM benefits WHERE benefit_no=%s", (benefit_no,))
        result = cur.fetchone()
        if not result:
            # 혜택이 DB에 없을 경우 예외처리
            return redirect('/mypage')
        site_id = result[0]
        cur = db.cursor()

        # 이미 찜한 상태인지 확인
        cur.execute("SELECT * FROM favorite_benefits WHERE user_no=%s AND benefit_no=%s",
                    (user_no, benefit_no))
        exists = cur.fetchone()

        if not exists: #찜한 상태가 아니라면
            # 찜하기 목록에 추가
            cur.execute("INSERT INTO favorite_benefit(user_no, benefit_no, site_id)
                VALUES(%s, %s, %s)", (user_no, benefit_no, site_id))

    finally:
        db.close()

    return redirect('/mypage')


#찜하기 취소 라우트
@app.route('/unlike/<int:benefit_no>')
def unlike(benefit_no):
    if 'user_no' not in session:
        return redirect('/login')

    user_no = session['user_no']

    db = get_db()
    try:
        cur = db.cursor()

        #이미 찜했으면 찜하기 취소
        cur.execute("DELETE FROM favorite_benefit WHERE user_no=%s AND benefit_no=%s",
                    (user_no, benefit_no))

    finally:
        db.close()

    return redirect('/mypage')




if __name__ == '__main__':
    app.run(debug=True)




