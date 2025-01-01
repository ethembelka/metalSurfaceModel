from flask import Flask, jsonify, Response, request
from flask_cors import CORS
import logging
from camera_service import CameraService
from functools import wraps

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

camera_service = CameraService()

def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({
                "error": "Internal server error",
                "message": str(e)
            }), 500
    return decorated_function

@app.route('/detection/status')
@handle_errors
def get_status():
    return jsonify(camera_service.get_status())

@app.route('/detection/start', methods=['POST'])
@handle_errors
def start_detection():
    success = camera_service.start_scanning()
    if success:
        return jsonify({'success': True, 'message': 'Detection started'})
    return jsonify({'success': False, 'message': 'Failed to start detection'}), 400

@app.route('/detection/stop', methods=['POST'])
@handle_errors
def stop_detection():
    success = camera_service.stop_scanning()
    if success:
        return jsonify({'success': True, 'message': 'Detection stopped'})
    return jsonify({'success': False, 'message': 'Failed to stop detection'}), 400

@app.route('/detection/start_stream', methods=['POST'])
@handle_errors
def start_stream():
    success = camera_service.start_streaming()
    if success:
        return jsonify({'success': True, 'message': 'Streaming started'})
    return jsonify({'success': False, 'message': 'Failed to start streaming'}), 400

@app.route('/detection/stop_stream', methods=['POST'])
@handle_errors
def stop_stream():
    success = camera_service.stop_streaming()
    if success:
        return jsonify({'success': True, 'message': 'Streaming stopped'})
    return jsonify({'success': False, 'message': 'Failed to stop streaming'}), 400

@app.route('/detection/stream')
@handle_errors
def video_feed():
    if not camera_service.is_streaming:
        return jsonify({"error": "Streaming is not active"}), 400
    return Response(
        camera_service.get_frame(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/detection/take_photo', methods=['GET'])
@handle_errors
def take_photo():
    success = camera_service.take_photo()
    if success:
        return jsonify({"success": True, "message": "Photo captured successfully"})
    return jsonify({"success": False, "message": "Failed to capture photo"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise