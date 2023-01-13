from flask import Flask, render_template, flash, redirect, url_for, session, request, logging

app = Flask(__name__)


@app.route('/')
def index():
    return 'Go!'


if __name__ == '__main__':
    app.run(debug=True)
