# Some random helper utilities
# Avoids cluttering up the main Agent module

# Import Python library modules
import random

# Just for keeping track of scores between problems
# The agent isn't considered correct unless it ranks
# the correct answer the highest (no ties)
class ScoreKeeper(object):

    def __init__(self):
        self.problems = {}
        self.count = 0
        self.times = {}
    
    # Add an individual score for one choice in one problem    
    def addscore(self, problemname, scorename, choicename, score):
        if not problemname in self.problems:
            self.problems[problemname] = {}
        if not 'scores' in self.problems[problemname]:
            self.problems[problemname]['scores'] = {}
        scores = self.problems[problemname]['scores']
        if not scorename in scores:
            scores[scorename] = {}
        scores[scorename][choicename] = score
        
    # Add the correct choice for this problem
    def addcorrect(self, problemname, correct):
        if not problemname in self.problems:
            self.problems[problemname] = {}
        self.problems[problemname]['correct'] = correct
        self.calculateranks(problemname)
        self.count += 1
        
    def addtime(self, problemname, problemtime):
        self.times[problemname] = problemtime
        
    # Calculate the score rank of each choice in a problem
    def calculateranks(self, problemname):
        problem = self.problems[problemname]
        correct = problem['correct']
        ranks = problem['ranks'] = {}
        for scorename, scores in list(problem['scores'].items()):
            correctscore = scores[correct]
            rank = 0
            for score in list(scores.values()):
                if score >= correctscore:
                    rank += 1
            ranks[scorename] = rank
            
    # Calculate the total correct answers for each scoring method
    def calculatetotals(self):
        totals = {'overall':len(self.problems)}
        for problemname, problem in list(self.problems.items()):
            for scorename, rank in list(problem['ranks'].items()):
                if not scorename in totals:
                    totals[scorename] = 0
                if rank == 1:
                    totals[scorename] += 1
        return totals
        
    # Calculate the total and per answer times
    def calculatetimes(self):
        totalmilliseconds = 0
        for calctime in list(self.times.values()):
            totalmilliseconds += calctime.microseconds / 1000.0
        averagemilliseconds = 0
        if self.times:
            averagemilliseconds = totalmilliseconds / float(len(self.times))
        return 'Calculated %s answers in %s milliseconds (%s ms per problem)' % (len(self.times), totalmilliseconds, averagemilliseconds)
    
    # Save the scores to a file
    def save(self):
        # Removed, only needed for debugging
        #from utils import fileutils
        #fileutils.dump(self.problems, 'scores')
        print(self.calculatetotals())
        print(self.calculatetimes())
        
# Give every object a random label
# This is only used for debugging purposes
def randomizelabels(prob, remapper):
    figures = prob['figures']
    for figurename, objects in list(figures.items()):
        # Generate a list of uppercase letters
        lettercodes = list(range(ord('A'), ord('Z')))
        # Randomly remap the object labels to new letters
        randomremaps = {}
        for objectname, attributes in list(objects.items()):
            randomcode = random.choice(lettercodes)
            lettercodes.remove(randomcode)
            randomletter = chr(randomcode)
            randomremaps[objectname] = randomletter
        # Apply the remaps
        figures[figurename] = remapper(objects, randomremaps)
        
# Convert the standard problem structure to nested dicts
def pythonizeproblem(problem):
    pythonized = {}
    pythonized['type'] = problem.getProblemType()
    pythonized['name'] = problem.getName()
    if pythonized['type'].endswith('(Image)'):
        pythonized['images'] = images = {}
        for figure in list(problem.getFigures().values()):
            name = figure.getName()
            path = figure.getPath()
            images[name] = path
        return pythonized
        
    pythonized['figures'] = figures = {}
    for figure in list(problem.getFigures().values()):
        name = figure.getName()
        figures[name] = objects = {}
        for object in figure.getObjects():
            objectname = object.getName()
            objects[objectname] = attributes = {}
            for attribute in object.getAttributes():
                attributename = attribute.getName()
                value = attribute.getValue()
                values = [value]
                if ',' in value:
                    values = value.split(',')
                attributes[attributename] = values
    return pythonized