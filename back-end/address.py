from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/submit_address', methods=['POST'])
def submit_address():
    city = request.form.get('도시')
    gu = request.form.get('군구')

    if not 도시 or not 군구:
        return jsonify({'error': '도/시와 군/구를 선택해주세요.'}), 400

    # Example: Save to MySQL DB here:
    # cursor.execute("INSERT INTO users_address (도시, 군구) VALUES (%s, %s)", (도시, 군구))

    return jsonify({'message': 'Address saved', 'city': city, 'gu': gu})

if __name__ == '__main__':
    app.run()


#create table in SQL

CREATE TABLE users_address (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(50) NOT NULL,
    gu VARCHAR(50) NOT NULL
);


