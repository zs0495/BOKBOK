from flask import Flask, render_template, request, session, jsonify
import pymysql
import re

app = Flask(__name__)
app.secret_key = "SECRET_KEY"

def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='PASSWORD',
        db='welfaredb',
        charset='utf8mb4',
        autocommit=True
    )

AGE_RANGES = [
    (0, 6, "아동"),
    (7, 18, "학생(청소년)"),
    (19, 45, "청년"),
    (46, 59, "중년"),
    (60, 100, "노인")
]

SITUATION_KEYWORDS = {
    '국가유공자': ['독립유공자', '유공자', '국가', '독립', '보훈'],
    '아동': ['보육', '아이', '아기', '자녀', '어린', '양육', '딸', '아들'],
    '자영업': ['장사', '기업', '단체'],
    '학생(청소년)': ['중학생', '중학교', '고등학교', '고등학생', '초등학생' , '초등학교', '자녀', '아이', '딸', '아들'],
    '청년': ['성인', '대학', '대학생'],
    '질병': ['병', '병원', '치료', '의료'],
    '한부모가정': ['한부모', '한 부모', '이혼','3분위', '2분위', '1분위', '3 분위', '2 분위', '1 분위'],
    '취업': ['취직', '일', '자격증', '회사', '입사', '교육', '배움', '배우', '수업', '실직'],
    '장학금': ['장학금', '등록금 지원', '교육비', '교육 지원', '금전', '돈', '등록금', '학비'],
    '차상위/저소득': ['기초생활', '차상위', '저소득', '3분위', '2분위', '1분위', '3 분위', '2 분위', '1 분위'],
    '장애인': ['장애'],
    '교육': ['학교', '배우', '공부', '수업'],
    '임산부': ['출산', '임신', '임산', '아이를 낳'],
    '금융': ['대출', '통장', '자금', '금전', '월세', '전세', '생활비'],
    '노인': ['어르신', '할머니', '할아버지'],
    '거주': ['주거', '집', '전세', '월세', '임대', '주택'],
    '(신혼)부부': ['부부', '신혼', '가족', '결혼', '혼인'],
}

def extract_age_range(text):
    matches = re.findall(r'(\d{1,2})\s*[\~\-]\s*(\d{1,2})\s*(?:세|살)', text)
    if matches:
        return tuple(int(x) for x in matches[0])
    match = re.search(r'(\d{1,2})\s*(?:세|살)', text)
    if match:
        age = int(match.group(1))
        return (age, age)
    return None

def get_age_group_label(age):
    if age is None:
        return None
    for min_age, max_age, label in AGE_RANGES:
        if min_age <= age <= max_age:
            return label
    return None

def extract_keywords_from_situation(situation_text):
    situation_lower = situation_text.lower()
    matched_keys = set()
    for key, synonyms in SITUATION_KEYWORDS.items():
        for word in synonyms:
            if word in situation_lower:
                matched_keys.add(key)
                break
    age_range = extract_age_range(situation_text)
    if age_range:
        mid_age = (age_range[0] + age_range[1]) // 2
        age_label = get_age_group_label(mid_age)
        if age_label:
            matched_keys.add(age_label)
    return list(matched_keys)

@app.route('/gong')
def gong():
    return render_template('gong.html')

@app.route('/get_user_info', methods=['GET'])
def get_user_info():
    if 'user_no' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user_no = session['user_no']
    db = get_db()
    try:
        cur = db.cursor(pymysql.cursors.DictCursor)
        cur.execute("SELECT username, birth_year, birth_month, city_name, district_name, situation FROM users WHERE user_no = %s", (user_no,))
        user = cur.fetchone()
        if not user:
            return jsonify({'success': False}), 404
        birth_year, birth_month, city, district = None, None, '', ''
        return jsonify({
            'success': True,
            'username': username,
            'birth_year': birth_year,
            'birth_month': birth_month,
            'city': city,
            'district': district,
            'situation': user['situation'] or ''
        })
    finally:
        db.close()

@app.route('/match_welfare', methods=['POST'])
def match_welfare():
    if 'user_no' not in session:
        return jsonify({'error': 'Not logged in. Please log in first'}), 401

    try:
        data = request.get_json()
        user_no = session['user_no']
        username = data.get('username', '')
        birth_year = data.get('birth_year', '')
        birth_month = data.get('birth_month', '')
        city = data.get('city', '')
        district = data.get('district', '')
        selected_keywords = data.get('keywords', [])
        situation_text = data.get('situation', '')  # 사용자 입력 상황
        welfare_type = data.get('type', 'PUBLIC')

        db = get_db()
        cur = db.cursor()

        # 상황 텍스트 DB 저장 (업데이트)
        cur.execute("UPDATE users SET situation = %s WHERE user_no = %s", (situation_text, user_no))
        db.commit()

        # 나이 계산
        age = None
        if birth_year:
            age = 2025 - int(birth_year)

        # 나이 그룹 키워드
        age_group_keywords = []
        if age:
            label = get_age_group_label(age)
            if label:
                age_group_keywords.append(label)

        # 상황으로부터 대표 키워드 추출
        situation_keywords = extract_keywords_from_situation(situation_text)

        # 전체 키워드 통합
        all_keywords = list(set(selected_keywords + age_group_keywords + situation_keywords))

        # 복지 혜택 조회 쿼리 및 조건
        cur = db.cursor(pymysql.cursors.DictCursor)
        params = []
        query = """
            SELECT DISTINCT 
                b.benefit_no,
                b.title AS benefit_title,
                b.description,
                b.eligibility,
                b.appl_method,
                b.required_doc,
                b.ben_url,
                s.site_name,
                b.is_nationwide
            FROM benefits b
            JOIN sites s ON b.site_id = s.site_id
            LEFT JOIN ben_address ba ON b.benefit_no = ba.benefit_no
            LEFT JOIN city c ON ba.city_id = c.city_id
            LEFT JOIN ben_keyword bk ON b.benefit_no = bk.benefit_no
            LEFT JOIN keyword k ON bk.keyword_id = k.keyword_id
            WHERE b.site_id BETWEEN 1 AND 7
        """
        if city:
            query += " AND (c.city_name = %s OR b.is_nationwide = TRUE)"
            params.append(city)

        if all_keywords:
            placeholders = ','.join(['%s'] * len(all_keywords))
            query += f" AND k.keyword_content IN ({placeholders})"
            params.extend(all_keywords)
            query += " ORDER BY b.benefit_no LIMIT 20"
            cur.execute(query, params)
            results = cur.fetchall()

        # 사용자가 찜한 목록 조회
            cur.execute("SELECT benefit_no FROM favorite_benefit WHERE user_no = %s", (user_no,))
            liked = {row['benefit_no'] for row in cur.fetchall()}

            matched = []
            for row in results:
                matched.append({
                'benefit_no': row['benefit_no'],
                'site_name': row['site_name'],
                'benefit_title': row['benefit_title'],
                'description': row['description'],
                'eligibility': row['eligibility'],
                'appl_method': row['appl_method'],
                'required_documents': row['required_doc'].split(',') if row['required_doc'] else [],
                'link': row['ben_url'],
                'is_nationwide': row['is_nationwide'],
                'is_liked': row['benefit_no'] in liked
            })

            db.close()
            return jsonify({
            'success': True,
            'matched': len(matched) > 0,
            'welfare_type': welfare_type,
            'benefits': matched,
            'extracted_keywords': situation_keywords,
            'age_keywords': age_group_keywords,
            'all_keywords': all_keywords,
            'user_info': {
                'name': username,
                'age': age,
                'age_group': get_age_group_label(age) if age else None,
                'location': f"{city} {district}".strip()
            }
        })

            except Exception as e:
                print("Error:", e)
                return jsonify({'error': '서버 내부 오류가 발생했습니다.'}), 500


    if __name__ == '__main__':
        app.run(debug=True)
