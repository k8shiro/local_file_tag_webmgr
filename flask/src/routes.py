from file_list import MP4Files
from flask import Flask, render_template, request
import random

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello World!"


@app.route('/home/', methods=['GET', 'POST'])
def home():
    files, tags = MP4Files().search()
    print("search")
    files_tags = list(zip(files[:], tags))

    if request.method == 'POST':
      tags = request.form["tags"]
      tags = tags.split()
      files_tags_tmp = []
      for f, t in files_tags:
          sub_tag = set(tags)
          if sub_tag.issubset(set(t.split(','))):
              files_tags_tmp.append((f, t))
      files_tags = files_tags_tmp

    random.shuffle(files_tags)

    return render_template('home.html', files_tags=files_tags)


@app.route('/no_tag/', methods=['GET', 'POST'])
def no_tag():
    files, tags = MP4Files().search()
    files_tags = list(zip(files[:], tags))
    files_no_tags = []
    for f, t in files_tags:
        if not t:
            files_no_tags.append((f, t))
    return render_template('home.html', files_tags=files_no_tags)



@app.route('/crawl/', methods=['GET', 'POST'])
def crawl():
    MP4Files().crawl()
    return 'OK'


@app.route('/edit/<path:file_id>', methods=['GET', 'POST'])
def edit(file_id):
    if request.method == 'GET': 
        pass
    if request.method == 'POST':
        tags = request.form["tags"]   
        import logging
        gunicorn_logger = logging.getLogger('gunicorn.error')
        gunicorn_logger.debug(tags)  
        MP4Files().set_tags(file_id, tags)

    file, tags = MP4Files().get_fileinfo(file_id)
    tags = ','.join(tags)
    return render_template('edit.html', file=file, tags=tags)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080,  threaded=True)
