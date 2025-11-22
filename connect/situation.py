@app.route('/match_welfare', methods=['POST'])
def match_welfare():
    if 'user_no' not in session:
        # 로그인 안 된 상태
        return jsonify({'error': 'Not logged in'}), 401

    try:
        data = request.get_json()

        user_name = data.get('username', '')
        birth_year = data.get('birth_year', '')  # 수정된 키 이름
        birth_month = data.get('birth_month', '')
        city = data.get('city', '')
        district = data.get('district', '')
        selected_keywords = data.get('keywords', [])
        situation_text = data.get('situation', '')  # 사용자의 상황 텍스트
        welfare_type = data.get('type', 'PUBLIC')

        user_no = session['user_no']

        # DB 연결
        db = get_db()
        cur = db.cursor()

        # 1) 사용자 상황 텍스트 DB에 저장
        cur.execute("UPDATE users SET situation = %s WHERE user_no = %s", (situation_text, user_no))
        db.commit()

        # 2) 나이 계산
        age = None
        if birth_year:
            age = 2025 - int(birth_year)

        # 3) 나이 기반 연령 키워드
        age_group_keywords = []
        if age:
            group = get_age_group_label(age)
            if group:
                age_group_keywords.append(group)

        # 4) 상황 텍스트 키워드 추출
        situation_keywords = extract_keywords_from_situation(situation_text)

        # 5) 모든 키워드 합치기
        all_keywords = list(set(selected_keywords + age_group_keywords + situation_keywords))

        # 6) 복지 매칭용 DB 조회 쿼리 작성
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
            WHERE b.site_id BETWEEN 8 AND 12
        """

        if city:
            query += " AND (c.city_name = %s OR b.is_nationwide = TRUE)"
            params.append(city)

        if all_keywords:
            placeholders = ",".join(["%s"] * len(all_keywords))
            query += f" AND k.keyword_content IN ({placeholders})"
            params.extend(all_keywords)

        query += " ORDER BY b.benefit_no LIMIT 20"

        cur.execute(query, params)
        results = cur.fetchall()

        # 7) 사용자가 찜한 목록 조회
        cur.execute("SELECT benefit_no FROM favorite_benefit WHERE user_no = %s", (user_no,))
        liked = {row['benefit_no'] for row in cur.fetchall()}

        # 8) 결과 정리
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

        # 9) JSON 응답 반환
        return jsonify({
            'success': True,
            'matched': len(matched) > 0,
            'welfare_type': welfare_type,
            'benefits': matched,
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
        print("Error:", e)
        return jsonify({'error': '서버 내부 오류가 발생했습니다.'}), 500
