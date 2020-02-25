from scibook import app, lm
import os
import logging

logging.basicConfig(filename='access.log', level=logging.DEBUG)
watch_dirs = ['app/templates']
watch_files = watch_dirs[:]
for w_dir in watch_dirs:
    for dirname, dirs, files in os.walk(w_dir):
        for filename in files:
            filename = os.path.join(dirname, filename)
            if os.path.isfile(filename):
                watch_files.append(filename)
app.run('0.0.0.0', port=8080, extra_files=watch_files, threaded=True)
app.debug = True
# app.config['DEBUG'] = True
