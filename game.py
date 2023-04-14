# -*- coding: utf-8 -*-

import os
import json
import random
import logging
from collections import OrderedDict
from collections import namedtuple
from gensim.models import KeyedVectors
from apscheduler.schedulers.background import BackgroundScheduler
from itertools import islice

from environ import *


Stats = namedtuple('Stats', ['num', 'solvers'])
Score = namedtuple('Score', ['error', 'num', 'percentile', 'score', 'solvers'])


class Game:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    def __init__(self, lexique,lexique_words, model):
        self.lexique = lexique
        self.pool_attempt_set = lexique_words
        self.model = model

        if not os.path.exists(WORD_FILE):
            self.random_word()
            self.save_word()
        else:
            self.restore_word()
        self.logger.info(f'Le mot à deviner est: {self.word_to_guess}')

        if not os.path.exists(HIST_FILE):
            self.history = [[0, 0, '']]
        else:
            self.restore_history()

        # initialize global
        self.solvers = 0
        self.day_num = len(self.history)


    def start(self):
        scheduler = BackgroundScheduler(timezone='Europe/Paris')
        scheduler.add_job(self.game_over, 'cron', hour=0, minute=0)
        scheduler.start()


    def save_word(self):
        with open(WORD_FILE, 'w') as f:
            f.write(self.word_to_guess)


    def restore_word(self):
        with open(WORD_FILE, 'r') as f:
            self.word_to_guess = f.read()


    def random_word(self):
        self.word_to_guess = self.lexique[random.randrange(0, len(self.lexique))][0]


    def save_history(self):
        with open(HIST_FILE, 'w') as f:
            json.dump(self.history, f)


    def restore_history(self):
        with open(HIST_FILE, 'r') as f:
            self.history = json.load(f)


    def score(self, word):
        error_str = None
        percentile = None
        score = None

        if word is not None and word != '':
            try:
                if word not in self.pool_attempt_set:
                    error_str = f'Je ne connais pas le mot <i>{word}</i>.'
                else:
                    if word == self.word_to_guess:
                        # with gensim rank of word with itself is 1 and similarity can be 0.99999994
                        score = 1.0
                        rank = 0
                        self.solvers += 1
                    else:
                        score = float(self.model.similarity(word, self.word_to_guess))
                        top = {a:[b,c] for a,b,c in self.top(self.word_to_guess,1000)}
                        print(top)
                        if word in top.keys():
                            percentile = top[word][0]
                        else:
                            percentile = None
            except KeyError:
                error_str = f'Je ne connais pas le mot <i>{word}</i>.'
        else:
            error_str = 'Je ne connais pas ce mot.'

        return Score(error_str, self.day_num, percentile, score, self.solvers)


    def top(self, word, topn):
        result = []
        top = self.model.most_similar(word, topn=10000)
        real_rank = 0
        for rank,w in enumerate([(word, 1.0), *top]):
            if w[0] in self.pool_attempt_set:
                result.append((w[0], 1000 - real_rank, float(w[1] * 100)))
                real_rank+=1
            if real_rank >= topn:
                break
        return result


    def nearby(self, word):
        if word == self.word_to_guess:
            result = self.top(word, 999)
        elif word == self.history[1][2]:
            result = self.top(word, 100)
        else:
            result = ''
        return result

    def newWord(self):
        self.game_over()
        return self.word_to_guess
    
    def getClue(self,rank):
        rank = int(rank) - 1
        if rank >= 999:
            return self.top(self.word_to_guess,1000)[999]
        return self.top(self.word_to_guess,1000)[rank]
    
    def stats(self):
        return Stats(self.day_num, self.solvers)._asdict()


    def game_over(self):
        self.history[0] = [self.day_num, self.solvers, self.word_to_guess]
        self.day_num += 1
        self.solvers = 0
        self.history = [[self.day_num, 0, ''], *self.history]
        self.save_history()
        self.random_word()
        self.save_word()
        self.logger.info(f'Le nouveau mot à deviner est: {self.word_to_guess}')
        
        

