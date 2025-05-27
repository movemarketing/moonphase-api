from flask import Flask, request, jsonify
from flask_cors import CORS
from skyfield.api import load, Topos, utc
from datetime import datetime
import math
from geopy.geocoders import Nominatim

app = Flask(__name__)
CORS(app)

@app.route('/moonphase', methods=['GET'])
def moon_phase():
    date = request.args.get('date')
    time = request.args.get('time')
    city = request.args.get('city')

    if not (date and time and city):
        return jsonify({"error": "Missing parameters"}), 400

    try:
        geolocator = Nominatim(user_agent="moon_api")
        location = geolocator.geocode(city)
        if not location:
            return jsonify({"error": "City not found"}), 404

        eph = load('de421.bsp')
        ts = load.timescale()
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(tzinfo=utc)
        t = ts.utc(dt)

        observer = Topos(latitude_degrees=location.latitude, longitude_degrees=location.longitude)
        observer_at = eph['earth'] + observer

        moon = observer_at.at(t).observe(eph['moon']).apparent()
        sun = observer_at.at(t).observe(eph['sun']).apparent()

        phase_angle = sun.separation_from(moon).degrees
        illumination = (1 + math.cos(math.radians(phase_angle))) / 2 * 100

        if phase_angle < 10:
            phase = "Nymåne"
        elif phase_angle < 90:
            phase = "Tiltagende måne"
        elif abs(phase_angle - 180) < 10:
            phase = "Fuldmåne"
        elif phase_angle > 90:
            phase = "Aftagende måne"
        else:
            phase = "Ukendt"

        return jsonify({
            "city": location.address,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "phase": phase,
            "illumination": round(illumination, 1),
            "phase_angle": round(phase_angle, 1)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
