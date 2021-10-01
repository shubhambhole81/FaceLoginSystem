# -*- coding: utf-8 -*-
from flask import Flask, Response, render_template, request, redirect, url_for
import cv2
import mysql.connector
import face_recognition
from io import BytesIO

app = Flask(__name__)
cap = cv2.VideoCapture(0)

host = 'localhost'
user = 'root'
password = 'root'
database = 'face_recognition'
conn = mysql.connector.connect(host=host,user=user, password=password, database=database)
cur = conn.cursor()

                
def face():
    cur.execute("select labels,images from face")
    rows = cur.fetchall()

    known_face_names=[]
    known_face_encodings =[]

    for r in rows:
        known_face_encodings.append(face_recognition.face_encodings(face_recognition.load_image_file(BytesIO(r[1])))[0])
        known_face_names.append(r[0])
    while True:
        ret, frame = cap.read()

        rgb_frame = frame[:, :, ::-1]

        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # loop through each face in this frame of video
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

            global name
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255),2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/upload', methods =['GET', 'POST'])
def upload():
    msg = ''
    if request.method == 'POST':
        labels = request.form['labels']
        image = request.files['images']
        img = image.read()
        cur.execute('SELECT * FROM face WHERE labels =%s', (labels, ))
        face = cur.fetchone()
        if face:
            msg = 'Already Registered!'
        else:
            cur.execute('INSERT INTO face VALUES (%s,%s)', (labels, img,))
            conn.commit()
            msg = 'You are successfully registered !'
        return render_template('face_login.html', msg = msg)
    elif request.method == 'POST':
        msg = 'Register Yourself First!'
    return render_template('face_register.html', msg = msg)

@app.route('/logout')
def logout():
	return render_template('face_login.html')

@app.route('/face_register')
def face_register():
    return render_template('face_register.html')

@app.route('/')
def face_login():
    return render_template('face_login.html')

@app.route('/welcome')
def welcome():
    msg = ''
    if name == "Unknown":
        msg = 'you are not registered'
        return render_template('face_register.html', msg = msg)
    else:
        return render_template('welcome.html', user = name)

@app.route('/verify_face')
def verify_face():
    return Response(face(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(debug=True)
