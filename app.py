from flask import Flask
from new_webhook import NewWebhook


app = Flask(__name__)
webhook = NewWebhook(app)


if __name__ == '__main__':
    app.run(port=5001)
