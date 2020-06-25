import os, re
from flask import Flask, send_file, request, flash, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import deepspeech
from .transcribers.youtube import YouTube
from .transcribers.flix import FlixExtractor
from .transcribers.file import FileExtractor


UPLOAD_FOLDER = './transcribers/uploadedFiles'
ALLOWED_EXTENSIONS = {'wav'}
MODEL = deepspeech.Model('./transcribers/deepspeech-0.7.4-models.pbmm')
MODEL.enableExternalScorer('./transcribers/deepspeech-0.7.4-models.scorer')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def ytVidId(url):
    ytRegEx = re.compile('(?:\/|%3D|v=|vi=)([0-9A-z-_]{11})(?:[%#?&]|$)')
    valid = ytRegEx.search(url)
    if valid:
        return valid.group(1)
    return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def render_index():
    return render_template('searchPage.html')

@app.route('/results', methods=['POST'])
def return_results():
    quote = request.form['quote']
    
    # =============YouTube=============
    if request.form['search_src'] == 'yt':
        source = request.form['yt_source']
        if ytVidId(source):
            transcriber = YouTube(ytVidId(source))
            results = "Quote: " + quote + "<br>YouTube Video ID: " + ytVidId(source) + "<br>Results: <br>" + str(transcriber.getTranscript())
            transcriber.convertToJSON("jsonTranscripts/transcript.json")
        else:
            results = "ERROR: Invalid YouTube link"
    # =============Netflix==============
    elif request.form['search_src'] == 'flix':
        title = request.form['flix_title']
        szn = request.form['flix_szn']
        ep = request.form['flix_ep']
        try:
            transcriber = FlixExtractor(title, int(szn), int(ep))
            results = "Title: " + title + "<br>Season #: " + szn + "<br>Episode #: " + ep + "<br>Results: <br>" + str(transcriber.getTranscript())
            transcriber.convertToJSON("jsonTranscripts/transcript.json")
        except(ValueError):
            results = "ERROR: Netflix show " + title + " not found"
        except(IndexError):
            results = "ERROR:" + title +" season " + szn + " episode " + ep + " not found"
    # ============File Upload===========
    elif request.form['search_src'] == 'file':
        # check if the post request has the file part
        if 'vid_upload' not in request.files:
            results = 'ERROR: No file part'
            return render_template("results.html", result=results)
        file = request.files['vid_upload']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            results = 'ERROR: No file selected'
            return render_template("results.html", result=results)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            audioPath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(audioPath)
            # while not os.path.exists(audioPath):
            #     pass
            transcriber = FileExtractor(audioPath, MODEL)
            results = "Quote: " + quote + "<br>File: " + filename + "<br>Results: <br>" + str(transcriber.getTranscript())
            os.remove(audioPath)

        else:
            results = 'ERROR: incorrect file format'

    else:
        results = "ERROR: Invalid searchsearch_src"

    return render_template("results.html", result=results)


