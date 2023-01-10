from flask import Flask
import tweet_fetcher
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

application = Flask(__name__)

@application.route("/")
def index():
    return "Follow @midwitmeme!"

def job():
    tweet_fetcher.respondToTweet('tweet_ID.txt')
    print("Success")

scheduler = BackgroundScheduler()
scheduler.add_job(func=job, trigger="interval", seconds=6)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())


if __name__ == "__main__":
    application.run(port=5000, debug=True)