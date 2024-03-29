from github_webhook import Webhook
from github_webhook.webhook import EVENT_DESCRIPTIONS
import yaml
from yaml import SafeLoader
import os
import hmac


import six
from flask import abort, request

payloads = yaml.load(open("commands.yaml").read(), SafeLoader)

def handle_event(event_type,data):
    print("Got event {} with data: {}".format(event_type, data))
    try:
        if event_type not in payloads: return
        command = payloads.get(event_type).format(**data)
        print("Running {}".format(command))
        os.system(command)
    except Exception as e:
        print(e)

def _format_event(event_type, data):
    try:
        return EVENT_DESCRIPTIONS[event_type].format(**data)
    except KeyError:
        return event_type

def _get_header(key):
    """Return message header"""

    try:
        return request.headers[key]
    except KeyError:
        abort(400, 'Missing header: ' + key)

class NewWebhook(Webhook):
    def __init__(self, *args, **kwargs):
        super(NewWebhook, self).__init__(*args, **kwargs)
        for event_type in EVENT_DESCRIPTIONS:
            self._hooks[event_type].append(lambda data,et: handle_event(et, data))

    def _postreceive(self):
        """Callback from Flask"""

        digest = self._get_digest()

        if digest is not None:
            sig_parts = _get_header('X-Hub-Signature').split('=', 1)
            if not isinstance(digest, six.text_type):
                digest = six.text_type(digest)

            if (len(sig_parts) < 2 or sig_parts[0] != 'sha1'
                    or not hmac.compare_digest(sig_parts[1], digest)):
                abort(400, 'Invalid signature')

        event_type = _get_header('X-Github-Event')
        data = request.get_json()

        if data is None:
            abort(400, 'Request body must contain json')

        self._logger.info(
            '%s (%s)', _format_event(event_type, data), _get_header('X-Github-Delivery'))

        for hook in self._hooks.get(event_type, []):
            hook(data, event_type)

        return '', 204

