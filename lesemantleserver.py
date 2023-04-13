#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import json
import logging
import re
from flask import Flask
from flask import request
from gensim.models import KeyedVectors


from environ import *
from game import Game


# configure the logger
logging.basicConfig(format='%(asctime)s - %(name)s::%(funcName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# load the model
model = KeyedVectors.load_word2vec_format(WORD2VEC_MODEL, binary=True, unicode_errors="ignore")

regex= re.compile('[@_!#$%^&*()<>?/\|}{~:]')

# load the dictionary
csv_reader = csv.reader(open(LEXIQUE_CSV), delimiter='\t')
lexique = list(filter(lambda c: ((c[3] == 'NOM' or c[3] == 'ADJ' or c[3] == 'VER') and
                                    (c[4] == '' or c[4] == 'm') and
                                    (c[5] == '' or c[5] == 's') and
                                    (float(c[6]) >= 5.0) and
                                    (c[10] == '' or c[10][:3] == 'inf') and regex.search(c[0]) == None and
                                    (c[0] in model.key_to_index)),
                        csv_reader))

game = Game(lexique, model)

app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    game.start()


def convert_namedtuple_to_dict(nt):
    return dict(filter(lambda item: item[1] is not None, nt._asdict().items()))


@app.route('/score', methods=['POST'])
def score():
    form = request.form

    result = game.score(form.get('word'))

    return convert_namedtuple_to_dict(result)


@app.route('/nearby', methods=['POST'])
def nearby():
    form = request.form

    result = game.nearby(form.get('word'))

    return result


@app.route('/stats', methods=['GET'])
def stats():
    return game.stats()


@app.route('/history', methods=['GET'])
def hist():
    return game.history

@app.route('/newWord', methods=['GET'])
def newWord():
    return [game.newWord()]

@app.route('/getClue', methods=['POST'])
def getClue():
    form = request.form
    return [game.getClue(form.get('rank'))]