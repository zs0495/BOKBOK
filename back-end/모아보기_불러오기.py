from flask import Flask, render_template, request, session, redirect, jsonify
import pymysql
import re

app = Flask(__name__)
app.secret_key = "SECRET_KEY"

# MySQL 연결 함수
def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='PASSWORD',
        db='welfaredb',
        charset='utf8mb4',
        autocommit=True
    )

# 나이 구간 정의: (최소, 최대, 라벨)
AGE_RANGES = [
    (0, 6, "아동"),
    (7, 18, "학생(청소년)"),
    (19, 45, "청년"),
    (60, 100, "노인")
]

# 키워드 매칭을 위한 사전 (상황 텍스트 → 복지 키워드 매핑)
SITUATION_KEYWORDS = {
    '국가유공자': ['독립유공자', '유공자', '국가', '독립', '보훈'],
    '아동': ['보육', '아이', '아기', '자녀', '어린', '양육', '딸', '아들'],
    '자영업': ['장사', '기업', '단체'],
    '학생(청소년)': ['중학생', '중학교', '고등학교', '고등학생', '초등학생' , '초등학교', '자녀', '아이', '딸', '아들'],
    '청년': ['성인'],
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
    """
    텍스트에서 나이 범위 추출
    "20~50세", "30-40세", "40세", "40살" 등 다양한 패턴 지원
    """
    # 범위 패턴: "20~50세", "30-40살"
    matches = re.findall(r'(\d{1,2})\s*[\~\-]\s*(\d{1,2})\s*(?:세|살)', text)
    if matches:
        return tuple(int(x) for x in matches[0])
    
    # 단일 나이 패턴: "40세", "40살"
    match = re.search(r'(\d{1,2})\s*(?:세|살)', text)
    if match:
        age = int(match.group(1))
        return (age, age)
    
    return None

def get_age_group_label(age):
    """
    나이를 입력받아 해당하는 연령 그룹 라벨 반환
    예: 25세 → "청년"
    """
    if age is None:
        return None
    
    for min_age, max_age, label in AGE_RANGES:
        if min_age <= age <= max_age:
            return label
    
    return None

# 텍스트에서 키워드 추출 함수
def extract_keywords_from_situation(situation_text):
    """
    사용자가 입력한 '나의 상황' 텍스트에서 복지 관련 키워드를 추출
    """
    keywords = set()
    situation_lower = situation_text.lower()
    
     # 1. 기본 키워드 매칭
    for keyword, benefit_types in SITUATION_KEYWORDS.items():
        if keyword in situation_lower:
            keywords.update(benefit_types)

    # 2. 나이 정보 추출 및 연령 그룹 라벨 추가
    age_range = extract_age_range(situation_text)
    if age_range:
        # 범위의 중간값으로 그룹 결정
        middle_age = (age_range[0] + age_range[1]) // 2
        age_label = get_age_group_label(middle_age)
        if age_label:
            keywords.add(age_label)

    return list(keywords)

# 복지 혜택 매칭 라우트 (공공/민간)
@app.route('/match_welfare', methods=['POST'])
def match_welfare():
    """
    사용자 입력 정보를 기반으로 복지 혜택 매칭
    """
    if 'user_no' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        # 프론트엔드에서 전송된 데이터
        data = request.get_json()
        
       user_name = data.get('userName', '')
        birth_year = data.get('birthYear', '')
        birth_month = data.get('birthMonth', '')
        city = data.get('city', '')
        district = data.get('district', '')
        selected_keywords = data.get('keywords', [])  # 사용자가 선택한 키워드
        situation_text = data.get('situation', '')  # 나의 상황 텍스트
        welfare_type = data.get('type', 'PUBLIC')  # PUBLIC 또는 PRIVATE
        
        # 1. 나이 계산
        current_year = 2025
        if birth_year:
            age = current_year - int(birth_year)
        
        # 2. 생년월일로 연령 그룹 라벨 추가
        age_group_keywords = []
        if age:
            age_label = get_age_group_label(age)
            if age_label:
                age_group_keywords.append(age_label)
        
# 3. 상황 텍스트에서 키워드 추출 (나이 정보 포함)
  situation_keywords = extract_keywords_from_situation(situation_text)
        
# 4. 모든 키워드 통합 (중복 제거)
  all_keywords = list(set(selected_keywords + age_group_keywords + situation_keywords))
        
 # 5. DB에서 복지 혜택 검색
  db = get_db()
  cur = db.cursor(pymysql.cursors.DictCursor)
             
   # 기본 쿼리 (공공)
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
        WHERE b.site_id BETWEEN 8 AND 12

        """
  # JOIN 조건 추가 (지역 또는 전국 대상)
        if city:
            query += """
                LEFT JOIN ben_address ba ON b.benefit_no = ba.benefit_no
                LEFT JOIN city c ON ba.city_id = c.city_id
            """
                
        query += " AND (c.city_name = %s OR b.is_nationwide = TRUE)"
        params.append(city)
        
        # 키워드 조건 (OR 조건으로 검색)
        if all_keywords:
            keyword_placeholders = ','.join(['%s'] * len(all_keywords))
            query += f" AND k.keyword_content IN ({keyword_placeholders})"
            params.extend(all_keywords)
        
        query += " ORDER BY b.benefit_no LIMIT 20"
        
        # 쿼리 실행
        cur.execute(query, params)
        results = cur.fetchall()
        
        # 6. 찜한 혜택 확인
        user_no = session['user_no']
        cur.execute("""
            SELECT benefit_no FROM favorite_benefit WHERE user_no = %s
        """, (user_no,))
        liked_benefits = {row['benefit_no'] for row in cur.fetchall()}
        
        # 6. 결과 가공
        matched_benefits = []
        for row in results:
            matched_benefits.append({
                'benefit_no': row['benefit_no'],
                'site_name': row['site_name'],
                'benefit_title': row['benefit_title'],
                'description': row['description'],
                'eligibility': row['eligibility'],
                'appl_method': row['appl_method'],
                'required_documents': row['required_documents'].split(',') if row['required_documents'] else [],
                'link': row['link'],
                'is_nationwide': row['is_nationwide'],
                'is_liked': row['benefit_no'] in liked_benefits

            })
        
        db.close()
        
        return jsonify({
            'success': True,
            'matched': len(matched_benefits) > 0,
            'welfare_type': welfare_type,
            'benefits': matched_benefits,
            'extracted_keywords': situation_keywords,
            'age_keywords': age_group_keywords,
            'all_keywords': all_keywords,
            'user_info': {
                'name': user_name,
                'age': age,
                'age_group': get_age_group_label(age) if age else None,
                'location': f"{city} {district}".strip()
            }
        })
        
    except Exception as e:
        print(f"Error in match_welfare: {e}")
        return jsonify({'error': str(e)}), 500

# 마이페이지에서 사용자 정보 불러오기
@app.route('/get_user_info', methods=['GET'])
def get_user_info():
    """
    마이페이지에 저장된 사용자 정보 반환
    """
    if 'user_no' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_no = session['user_no']
    db = get_db()
    
    try:
        cur = db.cursor(pymysql.cursors.DictCursor)
        cur.execute("""
            SELECT name, birth_date, address, situation
            FROM users
            WHERE user_no = %s
        """, (user_no,))
        
        user_info = cur.fetchone()
        
        if user_info:
            # 생년월일을 년, 월로 분리
            birth_year = None
            birth_month = None
            if user_info['birth_date']:
                birth_parts = user_info['birth_date'].split('년')
                if len(birth_parts) > 0:
                    birth_year = birth_parts[0].strip()
                if len(birth_parts) > 1:
                    birth_month = birth_parts[1].replace('월', '').replace('일', '').strip().split()[0]
            
            # 주소를 도/시와 시/군/구로 분리
            city = ''
            district = ''
            if user_info['address']:
                address_parts = user_info['address'].split()
                if len(address_parts) > 0:
                    city = address_parts[0]
                if len(address_parts) > 1:
                    district = address_parts[1]
            
            return jsonify({
                'success': True,
                'name': user_info['name'],
                'birth_year': birth_year,
                'birth_month': birth_month,
                'city': city,
                'district': district,
                'situation': user_info['situation']
            })
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
    finally:

        db.close()
