from flask import Flask, jsonify, request, render_template
from tc_manager import NetworkInterfaces
import sys
import logging

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/interfaces', methods=['GET'])
def get_interfaces():
    return jsonify({'interfaces': list(interfaces_dict.keys())})


@app.route('/api/interfaces/<interface_name>', methods=['GET'])
def get_interface(interface_name):
    if interface_name in interfaces_dict:
        return jsonify(interfaces_dict[interface_name].as_dict())
    else:
        return 'Interface {} not found'.format(interface_name), 404


@app.route('/api/interfaces/<interface_name>/default_rate', methods=['PUT', 'DELETE'])
def set_default_rate(interface_name):
    if interface_name in interfaces_dict:
        interface = interfaces_dict[interface_name]
        if request.method == 'DELETE':
            default_rate = None
        else:
            default_rate = request.get_json()
        interface.default_rate = default_rate
        return "", 200
    else:
        return 'Interface {} not found'.format(interface_name), 404


@app.route('/api/interfaces/<interface_name>/policies', methods=['POST'])
def post_policy(interface_name):
    if interface_name in interfaces_dict:
        interface = interfaces_dict[interface_name]
        json_request = request.get_json()
        logging.debug('post policy -> {}'.format(json_request))
        policy = interface.post_policy(json_request['match'], json_request['action'])
        return jsonify(policy)
    else:
        return 'Interface {} not found'.format(interface_name), 404


@app.route('/api/interfaces/<interface_name>/policies/<policy_id>', methods=['DELETE'])
def delete_policy(interface_name, policy_id):
    policy_id = int(policy_id)
    if interface_name in interfaces_dict:
        interface = interfaces_dict[interface_name]
        interface.delete_policy(policy_id)
        return '', 200
    else:
        return 'Interface {} not found'.format(interface_name), 404


@app.route('/api/interfaces/policies', methods=['POST'])
def post_policy_all():
    json_request = request.get_json()
    logging.debug('post policy -> {}'.format(json_request))
    interfaces.post_policy(json_request['match'], json_request['action'])
    return '', 200


@app.route('/api/interfaces/policies', methods=['DELETE'])
def delete_policy_all():
    json_request = request.get_json()
    interfaces.delete_policy_by_match(json_request['match'])
    return '', 200


@app.route('/api/interfaces/default_rate', methods=['PUT', 'DELETE'])
def set_default_rate_all():

    if request.method == 'DELETE':
        default_rate = None
    else:
        default_rate = request.get_json()
    interfaces.set_default_rate(default_rate)
    return "", 200


logging.basicConfig(format='%(asctime)s %(levelname)s:%(name)s:%(message)s', level=logging.getLevelName('DEBUG'))

if __name__ == '__main__':
    interface_names = sys.argv
    print(interface_names)
    interfaces = NetworkInterfaces(whitelist=interface_names[1:])
    interfaces_dict = interfaces.interfaces

    app.run(host='0.0.0.0', port=5000, debug=True)





