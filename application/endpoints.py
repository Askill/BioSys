from flask_restful import Resource, reqparse
import flask
import requests
import application.config as config
import json
import cv2
import base64
from application.db import Session, Person, Fingerprint

lastImage = ""

class PersonList(Resource):
    def post(self, id = None):
        """  """
        try:
            jsonData = flask.request.get_json(force=True)
            personJSON = jsonData["person"]
            print(personJSON)
            session = Session()

            # get Fingerprints with Middleware
            fingerprintsObj = []
            if "fingerprints" in personJSON:
                for fingerprint in personJSON["fingerprints"]:
                    fingerprint["fingerprint"] = fingerprint["fingerprint"].encode('utf-8')
                    fp = Fingerprint(**fingerprint) # ** Operator converts DICT/JSON to initializable 
                    fingerprintsObj.append(fp)  
                    session.add(fp)

            personJSON["fingerprints"] = fingerprintsObj
            personJSON["face"] = ("data:image/png;base64,"+str(lastImage)).encode('utf-8')
            person = Person(**personJSON)
            session.add(person)
            session.commit()

            data = list(session.query(Person).filter_by(person_id=person.person_id))
            arr = []
            for x in data:
                arr.append(x.serialize())

            return flask.make_response(flask.jsonify({'data': arr}), 201)

        except Exception as e:
            print("error: -", e)
            return flask.make_response(flask.jsonify({'error': str(e)}), 400)

    def get(self, id = None):
        """  """
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('useFace', type=bool, required=False)
            args = parser.parse_args()

            session = Session()

            # this indicates that the captured face should be use for identification / validation
            if "useFace" in args and args["useFace"]:
                if id is not None:
                    # validate
                    data = list(session.query(Person).filter_by(person_id=id))[0].serialize()
                    data["matching_score"] = 0.95
                    # return identified person object + matching score
                    return flask.make_response(flask.jsonify({'data': data}), 200)
                else:
                    # replace by Biometric function
                    # identify
                    # return identified person object + matching score
                    data = list(session.query(Person).all())[1].serialize()
                    data["matching_score"] = 0.95
                    return flask.make_response(flask.jsonify({'data': data}), 200)

            if id is None:
                data = list(session.query(Person).all())
            else:
                data = list(session.query(Person).filter_by(person_id=id))
            arr = []
            for x in data:
                arr.append(x.serialize())

            return flask.make_response(flask.jsonify({'data': arr}), 200)
        except Exception as e:
            print("error: -", e)
            return flask.make_response(flask.jsonify({'error': str(e)}), 400)

    def put(self, id = None):
        """  """
        try:
            data = ""
            return flask.make_response(flask.jsonify({'data': data}), 200)
        except Exception as e:
            print("error: -", e)
            return flask.make_response(flask.jsonify({'error': str(e)}), 400)

    def delete(self, id = None):
        """  """
        try:
            if id is None:
                return flask.make_response(flask.jsonify({'error': "No ID given"}), 404) 

            session = Session()
            data = session.query(Person).filter_by(person_id=id).delete()
            session.commit()
            
            return flask.make_response(flask.jsonify({'data': data}), 204)

        except Exception as e:
            print("error: -", e)
            return flask.make_response(flask.jsonify({'error': str(e)}), 404)

class Camera(Resource):

    

    # provides th function used for the live streams
    class VideoCamera(object):
        """Video stream object"""
        url = "https://webcam1.lpl.org/axis-cgi/mjpg/video.cgi"
        def __init__(self):
            self.video = cv2.VideoCapture(self.url)

        def __del__(self):
            self.video.release()
        
        def get_frame(self, ending):
            success, image = self.video.read()
            ret, jpeg = cv2.imencode(ending, image)
            return jpeg


    def gen(self, camera):
        """Video streaming generator function."""
        while True:
            frame = camera.get_frame('.jpg').tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def get(self, type = "stream"):
        global lastImage
        try:
            if type == "stream":
                return flask.Response(self.gen(self.VideoCamera()), mimetype='multipart/x-mixed-replace; boundary=frame')
            
            elif type == "still":
                lastImage1 = base64.b64decode(lastImage.encode())
                return flask.Response(lastImage1,  mimetype='image/png')

            return flask.make_response(flask.jsonify({'error': "No idea how you got here"}), 404)
        except Exception as e:
            print("error: -", e)
            return flask.make_response(flask.jsonify({'error': str(e)}), 404)

    def post(self):
        global lastImage
        try:
            lastImage = base64.b64encode(self.VideoCamera().get_frame('.png')).decode()
        except Exception as e:
            print("error: -", e)
            return flask.make_response(flask.jsonify({'error': str(e)}), 404)