from flask import Flask, render_template, request, session, redirect, jsonify
import pymysql

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

# 1. 자료실 페이지 렌더링
@app.route('/library')
def library():
    """자료실 메인 페이지"""
    return render_template('library.html')

# 2. 공공/민간 복지 기관 목록 API
@app.route('/api/get_resources', methods=['GET'])
def get_resources():
    """
    공공 또는 민간 복지 기관 및 혜택 목록 반환
    Query Parameter: type (PUBLIC 또는 PRIVATE)
    """
    resource_type = request.args.get('type', 'PUBLIC')  # 기본값: 공공
    
    db = get_db()
    try:
        cur = db.cursor(pymysql.cursors.DictCursor)
        
        if resource_type == 'PUBLIC':
            # 공공 복지 기관 및 혜택 조회
            cur.execute("""
                SELECT 
                    s.site_name,
                    b.title,
                    b.benefit_no,
                    b.required_documents,
                FROM benefits b
                JOIN sites s ON b.site_id = s.site_id
                WHERE site_id BETWEEN 1 AND 7
                ORDER BY s.site_name, b.title
            """)
        else:  # PRIVATE
            # 민간 복지 기관 및 혜택 조회
            cur.execute("""
                SELECT 
                    s.site_name,
                    b.title,
                    b.benefit_no,
                    b.required_documents,
                FROM benefits b
                JOIN sites s ON b.site_id = s.site_id
                WHERE site_id BETWEEN 8 AND 12
                ORDER BY s.site_name, b.title
            """)
        
        resources = cur.fetchall()
        
        return jsonify({
            'success': True,
            'type': resource_type,
            'resources': resources
        })
        
    finally:
        db.close()

# 3. 특정 혜택 상세 정보 API
@app.route('/api/get_benefit_detail/<int:benefit_no>', methods=['GET'])
def get_benefit_detail(benefit_no):
    """
    특정 혜택의 상세 정보 반환 (필수 서류 목록 포함)
    """
    db = get_db()
    try:
        cur = db.cursor(pymysql.cursors.DictCursor)
        
        cur.execute("""
            SELECT 
                b.title,
                b.required_documents,
                s.site_name,
            FROM benefits b
            JOIN sites s ON b.site_id = s.site_id
            WHERE b.benefit_no = %s
        """, (benefit_no,))
        
        benefit = cur.fetchone()
        
        if benefit:
            # 필수 서류를 리스트로 변환
            if benefit['required_documents']:
                benefit['required_documents'] = [
                    doc.strip() for doc in benefit['required_documents'].split(',')
                ]
            else:
                benefit['required_documents'] = []
            
            return jsonify({
                'success': True,
                'benefit': benefit
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Benefit not found'
            }), 404
            
    finally:
        db.close()

\
if __name__ == '__main__':
    app.run(debug=True)
