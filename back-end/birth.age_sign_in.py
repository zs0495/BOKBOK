from flask import Flask, request, jsonify
from datetime import date

app = Flask(__name__)

@app.route('/submit_birthday', methods=['POST'])
def submit_birthday():
    year = request.form.get('year')
    month = request.form.get('month')
    day = request.form.get('day')
    
    # Build a date object
    try:
        birthday = date(int(year), int(month), int(day))
    except ValueError:
        return jsonify({'error': 'Invalid date'}), 400
    
    today = date.today()
    
    # Calculate age
    age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
    
   
    # Example insertion (using a cursor and parameterized query)
    # cursor.execute("INSERT INTO personal_info (birthday, age) VALUES (%s, %s)", (birthday, age))
    
    return jsonify({'birthday': birthday.isoformat(), 'age': age})

if __name__ == '__main__':
    app.run()


  #create table in SQL
  CREATE TABLE personal_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    birthday DATE NOT NULL,
    age INT NOT NULL
);

