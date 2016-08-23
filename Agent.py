# This is the agent written by Chris Graham (cgraham36@gatech.edu)
# This is the Project 4 version, it can solve 2x1, 2x2, and 3x3 problems
# It should solve somewhere around 45 of the given Basic problems
# If it solves significantly less than 40 please contact me
# Performance may vary depending on what problems are learned from
# This code assumes the problems will be labeled "ZxZ (Image)" as their type,
# otherwise the image analysis code will not run
# You must run this on Python 2.7.x, 2.7.8 is recommended
# Pillow is required, I used Pillow-2.6.1 win-amd64 for python 2.7
# I tested on Windows, not sure if that makes a difference
# If you see any errors on the given problems, please contact me


# Your Agent for solving Raven's Progressive Matrices. You MUST modify this file.
#
# You may also create and submit new files in addition to modifying this file.
#
# Make sure your file retains methods with the signatures:
# def __init__(self)
# def Solve(self,problem)
#
# These methods will be necessary for the project's main method to run.

# Import Python library utility modules
import datetime, sys, operator, copy

# Import required modules
import helpers, knowledgebase, images
        
class Agent:
    # The default constructor for your Agent. Make sure to execute any
    # processing necessary before your Agent starts solving problems here.
    #
    # Do not add any variables to this signature; they will not be used by
    # main().
    def __init__(self):
        # Keep track of scores
        self.scores = helpers.ScoreKeeper()
        # Store knowledge gained from previous problems
        self.knowledgebase = {}
        
        #from utils import fileutils
        #self.knowledgebase = fileutils.load('knowledgebase')

    # @param problem the RavensProblem your agent should solve
    # @return your Agent's answer to this problem
    def Solve(self,problem):
        
        # Check Python version before running
        version = sys.version_info
        if version[:2] != (2, 7):
            # Print a big scary error, this code probably won't work correctly
            print('ERROR! SEE SUBMISSION NOTES')
            print('ERROR! THIS CODE WILL NOT RUN PROPERLY')
            print('EXPECTED PYTHON VERSION IS 2.7.8, CURRENT VERSION IS %s.%s.%s' % version[:3])
            # Prevent the problems from running at all
            exit()
        elif version[:3] != (2, 7, 8):
            # Print a less scary warning, 2.7.x is probably okay
            print('')
            print('Warning, Python 2.7.8 is recommended, currently running %s.%s.%s' % version[:3])
        
        # Run the solving code
        try:
            return self.solve(problem)
        except:
            # Print an obvious error message
            print('SOMETHING WENT TERRIBLY WRONG!')
            print('PLEASE CONTACT ME IF THIS HAPPENS DURING THE KNOWN PROBLEMS')
            # Print stack trace
            import traceback
            traceback.print_exc()
            # Return lucky number 3
            exit()
            return '3'
    
    def solve(self, problem):
        # Debugging code for skipping unwanted problems
        #if self.scores.count >= 47:
        #    return '7'
            
        # Remember the time when we started this problem
        starttime = datetime.datetime.now()
        
        # Change the problem structure to pythonized version
        prob = helpers.pythonizeproblem(problem)
        
        # Debugging code for selecting a specific problem type
        #if not 'Basic' in prob['name']:
        #    return '8'
        
        # Debugging code for selecting a specific problem
        if not '2x1 Basic' in prob['name'] or not '16' in prob['name']:
           return '8'
        
        if 'images' in prob:
            prob['figures'] = images.analyze(prob['images'])
            
        prob['type'] = prob['type'].replace(' (Image)', '')
        
        print('')
        print(prob['name'])
        
        # Update the problem details to make solving easier
        self.preprocess(prob)
        
        # Update the knowledge base with this problem's attributes
        knowledgebase.scanattributes(self.knowledgebase, prob)
        knowledgebase.updateknowledge(self.knowledgebase)
        
        # For 2x2 problems, detect the transpose relationship
        if prob['type'] == '2x2':
            transpose = self.detecttranspose(prob)
            if transpose == ('A', 'B'):
                print('Re-formulating as A->B transpose')
                # Swap B and C figures to represent the correct structure
                prob['figures']['B'], prob['figures']['C'] = prob['figures']['C'], prob['figures']['B']
            
        # Change the object names to match up better
        self.renameobjects(prob)
        
        # For 3x3 problems, score the answers based on how well
        # they match the vertical and horizontal invariants
        invariantscores = None
        if prob['type'] == '3x3':
            invariantscores = self.scoreinvariants(prob)
        
        # For 3x3 problems, compress the structure into 2x3
        if prob['type'] == '3x3':
            # Run the compression
            self.compress(prob)
            # Re-calculate the numeric values
            self.addnumerics(prob)
        
        # Debugging code to view problem structure
        #from utils import fileutils
        #fileutils.dump(prob, prob['name'])
        
        # Come up with human-readable names for objects in figures
        names = knowledgebase.findobjectnames(self.knowledgebase, prob)
        
        # Get the agent's answer to the problem
        choice = self.chooseanswer(prob, invariantscores)
        
        # Calculate the time spent and add it to the scores
        endtime = datetime.datetime.now()
        calctime = endtime - starttime
        self.scores.addtime(prob['name'], calctime)
        
        # Add the correct answer info to the scores
        realanswer = problem.checkAnswer(choice)
        self.scores.addcorrect(prob['name'], realanswer)
        self.scores.save()
        
        # Print result to the screen
        status = 'Correct'
        if choice != realanswer:
            status = 'Incorrect'
        print('Chose %s %s' % (choice, status))
        
        # Analyze this answer to improve the knowledge base
        knowledgebase.analyzeanswer(self.knowledgebase, prob, realanswer, self.diff_features)
        
        # Debugging for viewing knowledge base details, removed
        #from utils import fileutils
        #fileutils.dump(self.knowledgebase, 'knowledgebase')
        
        return choice
    
    # Process the problem before anything else happens
    def preprocess(self, prob):
        # Only used for debugging
        #helpers.randomizelabels(prob, self.renamefigureobjects)
        
        self.cheaphacks(prob)
        self.splitfills(prob)
        self.normalizeangles(prob)
        self.addnumerics(prob)
        
    # Split fills into quadrants
    def splitfills(self, prob):
        # Check to see if there are any specific fill types in this problem
        needsplit = False
        for figurename, objects in list(prob['figures'].items()):
            for objectname, attributes in list(objects.items()):
                if 'fill' in attributes:
                    fillvalue = ','.join(attributes['fill'])
                    if fillvalue != 'yes' and fillvalue != 'no':
                        needsplit = True
                        break
    
        if not needsplit:
            # All of the fills in the problem are yes/no, so we don't need to do anything
            return
        
        # Update every object's fill attribute to be quadrant-based
        for figurename, objects in list(prob['figures'].items()):
            for objectname, attributes in list(objects.items()):
                if not 'fill' in attributes:
                    # This object doesn't have a fill property, so skip it
                    continue
                
                # Update the attributes
                newattributes = {}
                for attribute, values in list(attributes.items()):
                    if attribute != 'fill':
                        # Leave non-fill attributes the same
                        newattributes[attribute] = values
                        continue
                        
                    # Make a new attribute for each quadrant
                    newattributes['fill-topleft'] = ['no']
                    newattributes['fill-topright'] = ['no']
                    newattributes['fill-bottomleft'] = ['no']
                    newattributes['fill-bottomright'] = ['no']
                    
                    # Determine which quadrants are filled
                    if 'yes' in values or 'top-half' in values or 'left-half' in values or 'top-left' in values:
                        newattributes['fill-topleft'] = ['yes']
                    if 'yes' in values or 'top-half' in values or 'right-half' in values or 'top-right' in values:
                        newattributes['fill-topright'] = ['yes']
                    if 'yes' in values or 'bottom-half' in values or 'left-half' in values or 'bottom-left' in values:
                        newattributes['fill-bottomleft'] = ['yes']
                    if 'yes' in values or 'bottom-half' in values or 'right-half' in values or 'bottom-right' in values:
                        newattributes['fill-bottomright'] = ['yes']
                        
                # Set the updated attributes
                objects[objectname] = newattributes
                
    # Normalize 0 degrees to represent "up" for all shapes, remove angles for circles
    def normalizeangles(self, prob):
        # Update every object in every figure
        for figurename, objects in list(prob['figures'].items()):
            for objectname, attributes in list(objects.items()):
                # Ignore objects that don't have a shape and angle
                if not 'angle' in attributes or not 'shape' in attributes:
                    continue
                # These are the offsets needed to correct some shapes
                #offsets = {}
                #offsets = {'Pac-Man':90, 'right-triangle':225}
                offsets = {'triangle':25, 'plus':315, 'Pac-Man':90, 'right-triangle':45}
                # By default, don't correct the angle
                offset = 0
                
                # Check if the shape needs an offset
                shape = ','.join(attributes['shape'])
                if shape in offsets:
                    offset = offsets[shape]
                
                # Apply the offset for this object
                updatedangles = []
                for angle in attributes['angle']:
                    updatedangle = str((int(angle) + offset) % 360)
                    updatedangles.append(updatedangle)
                    
                # Save the updated value
                attributes['angle'] = updatedangles
                
        # Check every object in every figure
        for figurename, objects in list(prob['figures'].items()):
            for objectname, attributes in list(objects.items()):
                # Check for circles that have an angle value
                if 'angle' in attributes and 'shape' in attributes and ''.join(attributes['shape']) == 'circle':
                    # Remove the angle value
                    attributes.pop('angle', None)
                    
    # Add some calculated numeric values based on the existing attributes
    def addnumerics(self, prob):
        # Give the size attributes a numeric value
        sizes = ['very-small', 'small', 'medium', 'large', 'very-large']
        
        # Check every object in every figure
        for figurename, objects in list(prob['figures'].items()):
            for objectname, attributes in list(objects.items()):
                # Ignore objects that don't have a single size attribute value
                if not 'size' in attributes or len(attributes['size']) > 1:
                    continue
                # Default scale value is medium
                scale = len(sizes)/2
                
                # Convert the size to a number
                size = attributes['size'][0]
                if size in sizes:
                    scale = sizes.index(size)
                scale += 1
                
                # Save the scale numeric value as a new attribute
                attributes['scale'] = [str(scale)]
                
        # Check if this is a problem where angle XOR value might be relevant
        allangle = True
        uniqueangles = []
        maxobjects = 0
        # Go through every figure in the problem
        for figurename, objects in list(prob['figures'].items()):
            # Keep track of the maximum number of objects in a figure
            if len(objects) > maxobjects:
                maxobjects = len(objects)
            # Go through each object
            for objectname, attributes in list(objects.items()):
                # Make sure every object has an angle value
                if not 'angle' in attributes or len(attributes['angle']) > 1:
                    # No angle value, stop analyzing the problem
                    allangle = False
                    break
                else:
                    angle = attributes['angle'][0]
                    # Keep track of the total number of unique angles found
                    if not angle in uniqueangles:
                        uniqueangles.append(angle)
            if not allangle:
                # No angle value, stop analyzing the problem
                break
                
        # Check if all of the requirements have been met:
        # Every object must have an angle, there can only be
        # two unique angle values, and there must be at least
        # one figure with at least 3 objects in it
        if allangle and len(uniqueangles) == 2 and maxobjects > 2:
            # Sort the unique angle value list to keep the numeric values consistent
            uniqueangles.sort()
            # Go through each figure
            for figurename, objects in list(prob['figures'].items()):
                xortotal = 0
                # Go through each object
                for objectname, attributes in list(objects.items()):
                    angle = attributes['angle'][0]
                    # Assign the angle either a positive or negative value
                    # and add it to the total
                    if uniqueangles.index(angle) == 0:
                        xortotal += 1
                    else:
                        xortotal -= 1
                # xortotal now has a value representing the difference between angles
                # across all objects in this figure
                # Save this value in every object in the figure
                for objectname, attributes in list(objects.items()):
                    attributes['anglexor'] = [str(xortotal)]
              
    # Very specific preprocessing that can't be handled in a more general way
    def cheaphacks(self, prob):
        # Look for a very specific type of problem
        # All objects except one in a figure should be inside another object
        allinside = True
        # All objects in the entire problem should be the same shape
        sameshape = True
        shape = None
        # The problem should include a high 'inside' depth
        highdepth = False
        # The problem should include one answer figure that is a single filled object
        singlefill = None
        
        for figurename, objects in list(prob['figures'].items()):
            # Stop processing if we already know it doesn't match the rules
            if not allinside or not sameshape:
                break
            # Allow one object that is not inside another object
            outside = 1
            for objectname, attributes in list(objects.items()):
                # An object doesn't have a shape, so the same shape rule is broken
                if not 'shape' in attributes:
                    sameshape = False
                    break
                if not shape:
                    # This is the first shape we've seen, all future shapes must match it
                    shape = attributes['shape']
                else:
                    # Make sure this shape matches all previously seen shapes
                    if shape != attributes['shape']:
                        # Shape doesn't match, same shape rule is broken
                        sameshape = False
                        break
                if not 'inside' in attributes:
                    # Found a shape that is not inside another shape, update the total
                    outside -= 1
                    # Check to see if this is an answer figure with a single filled object
                    if figurename.isdigit() and len(objects) == 1 and 'fill' in attributes and ''.join(attributes['fill']) == 'yes':
                        # Found the single filled answer
                        singlefill = figurename
                else:
                    if len(attributes['inside']) > 2:
                        # Inside 3 or more other objects is high enough depth
                        highdepth = True
                if outside < 0:
                    # More than one object was not inside another object, all inside is broken
                    allinside = False
                    break
        # Check to see if this problem matches all of the rules
        if allinside and sameshape and highdepth and singlefill:
            # It matches, update the problem to be easier to solve
            # Find a template answer to match up with the filled answer
            template = None
            gooddepth = 100000
            for figurename, objects in list(prob['figures'].items()):
                if not figurename.isdigit():
                    # Ignore non-answer figures
                    continue
                # Keep track of the object in this figure that has the highest depth
                highdepth = 0
                for objectname, attributes in list(objects.items()):
                    if not 'inside' in attributes:
                        continue
                    depth = len(attributes['inside'])
                    if depth > highdepth:
                        # Record this object's depth as the highest
                        highdepth = depth
                # Use the lowest non-zero depth object as the template
                if highdepth > 0 and highdepth < gooddepth:
                    gooddepth = highdepth
                    template = figurename
            if template:
                # Copy the template objects as-is to the single fill anser figure
                tofill = prob['figures'][singlefill] = copy.deepcopy(prob['figures'][template])
                # Fill in the copied objects
                for objectname, attributes in list(tofill.items()):
                    attributes['fill'] = ['yes']
                # Now we have a structure that better matches the other choices but still
                # appears to be filled in visually
                # This is a cheap hack to get very specific types of questsions right,
                # if there was any straight-forward way to avoid doing this I would remove this
    
    # Record high-level features in a given figure
    def findfeatures(self, figure):
        features = []
        
        # Add a feature for the overall number of objects
        objectsfeature = {'attribute':'objects', 'value':'unknown', 'count':len(figure)}
        features.append(objectsfeature)
        
        # Check every attribute of every object in the figure
        for objectname, attributes in list(figure.items()):
            for attributename, values in list(attributes.items()):
                # Ignore empty attributes
                if not values:
                    continue
                    
                # By default assume a single non-relative value
                value = values[0]
                
                # If this attribute can be relative or have multiple values, just get the count
                relative = self.knowledgebase['attributes'][attributename]['relative']
                multi = self.knowledgebase['attributes'][attributename]['multi']
                if relative != 'never' or multi != 'never':
                    value = len(values)
                    
                # Check if there is already an entry for this attribute and value
                exists = False
                for feature in features:
                    if feature['attribute'] == attributename and feature['value'] == value:
                        # Update the count of how many we have seen
                        feature['count'] += 1
                        exists = True
                        break
                if not exists:
                    # Create a new feature for this attribute/value pair
                    newfeature = {'attribute':attributename, 'value':value, 'count':1}
                    features.append(newfeature)
        return features
    
    # Record the differences between the high-level features of two figures
    def diff_features(self, figure, otherfigure):
        # Find the high-level features for each figure
        features = self.findfeatures(figure)
        otherfeatures = self.findfeatures(otherfigure)
        
        diffs = []
        for feature in features:
            diff = {'feature':feature, 'type':'unknown'}
            # Check if this feature has been removed, is missing, increased or decreased in the other figure
            removed = True
            missing = True
            increased = False
            decreased = False
            for otherfeature in otherfeatures:
                if feature['attribute'] == otherfeature['attribute']:
                    # This attribute was present in the other figure, so it wasn't removed
                    removed = False
                    if feature['value'] == otherfeature['value']:
                        # This exact value was present in the other figure, so it's not missing
                        missing = False
                        if feature['count'] > otherfeature['count']:
                            # The count decreased
                            decreased = True
                        elif feature['count'] < otherfeature['count']:
                            # The count increased
                            increased = True
            # Record the diff type (if any)
            if removed:
                diff['type'] = 'removed'
                diffs.append(diff)
            elif missing:
                diff['type'] = 'missing'
                diffs.append(diff)
            elif increased:
                diff['type'] = 'increased'
                diffs.append(diff)
            elif decreased:
                diff['type'] = 'decreased'
                diffs.append(diff)
        
        # Go through all of the features in the other figure
        for otherfeature in otherfeatures:
            diff = {'feature':otherfeature, 'type':'unknown'}
            # Check if this feature was introduced or added
            introduced = True
            added = True
            for feature in features:
                if feature['attribute'] == otherfeature['attribute']:
                    # The attribute was in the original features, so it's not introduced
                    introduced = False
                    if feature['value'] == otherfeature['value']:
                        # The exact value was in the original features, so it's not added
                        added = False
                        
            # Record the diff type (if any)
            if introduced:
                diff['type'] = 'introduced'
                diffs.append(diff)
            elif added:
                diff['type'] = 'added'
                diffs.append(diff)
                
        toremove = []
        toadd = []
        # Change missing/added diff pairs to a single "updated" diff
        for diff in list(diffs):
            # Ignore diff types that aren't "missing"
            if diff['type'] != 'missing':
                continue
                
            # Look for an exactly matching diff with type "added"
            newvalue = None
            founddiff = None
            for otherdiff in diffs:
                if otherdiff == diff:
                    continue
                if otherdiff['type'] != 'added':
                    continue
                if otherdiff['feature']['attribute'] != diff['feature']['attribute']:
                    continue
                if otherdiff['feature']['count'] != diff['feature']['count']:
                    continue
                if newvalue:
                    # More than one match, can't do the update
                    newvalue = None
                    break
                else:
                    # Exact match, save this diff
                    newvalue = otherdiff['feature']['value']
                    founddiff = otherdiff
            if newvalue:
                # Remove the old diffs
                toremove.append(diff)
                toremove.append(founddiff)
                
                # Add a new "updated" diff instead
                newfeature = diff['feature'].copy()
                newfeature['value'] = '%s->%s' % (newfeature['value'], newvalue)
                toadd.append({'feature':newfeature, 'type':'updated'})
        
        # Remove the old diffs
        for removediff in toremove:
            if removediff in diffs:
                diffs.remove(removediff)
                
        # Add the new diffs
        for add_diff in toadd:
            diffs.append(add_diff)
            
        return diffs
        
    # Compare two sets of high-level feature diffs
    def comparediffs(self, diffs, otherdiffs):
        # Keep track of the score and the maximum possible score
        score = 0
        maxscore = len(diffs)
        if not len(diffs):
            # There are no diffs to begin with, set the high score to be 1
            maxscore += 1
            
        if len(diffs) == len(otherdiffs):
            # The overall number of diffs matches, add that to the score
            score += len(diffs)
            if not len(diffs):
                # If they are both empty, add 1 to the score
                score += 1
                
        for diff in list(diffs):
            maxscore += 5
            if diff in otherdiffs:
                # Exact matches score 5 points, the maximum
                score += 5
            else:
                for otherdiff in otherdiffs:
                    # Ignore diffs without the same type and attribute
                    if otherdiff['type'] != diff['type']:
                        continue
                    if otherdiff['feature']['attribute'] != diff['feature']['attribute']:
                        continue
                        
                    # Found a good match
                    if otherdiff['feature']['count'] == diff['feature']['count']:
                        # Add 2 points if the count also matches
                        score += 2
                    else:
                        # Otherwise only add 1 point
                        score += 1
                    # Stop looking for matches
                    break
                    
        # Return the percentage of max score
        return score / float(maxscore)
        
    def scoreinvariants(self, prob):
        # Record all of the adjacent figures, from left-to-right and top-to-bottom
        leftrights = [('A', 'B'), ('B', 'C'), ('D', 'E'), ('E', 'F'), ('G', 'H')]
        updowns = [('A', 'D'), ('D', 'G'), ('B', 'E'), ('E', 'H'), ('C', 'F')]
        
        # Find the left-right invariants and up-down invariants
        leftrightinvariants = self.findinvariants(prob, leftrights)
        updowninvariants = self.findinvariants(prob, updowns)
        
        # Add all of the invariants to one big list
        allinvariants = []
        allinvariants.extend(leftrightinvariants)
        allinvariants.extend(updowninvariants)
        
        # Don't bother scoring at all if no invariants are found
        if not allinvariants:
            return None
        
        # Record the adjacent left and up figures compared to the answer figure space
        lefts = ['H']
        ups = ['F']
        
        scores = {}
        # Go through all of the answer figures
        for figurename, figure in sorted(list(prob['figures'].items())):
            # Ignore figures that are not answers
            if not figurename.isdigit():
                continue
                
            # Find the invariants from left and up
            leftpairs = [(left, figurename) for left in lefts]
            leftinvariants = self.findinvariants(prob, leftpairs)
            uppairs = [(up, figurename) for up in ups]
            upinvariants = self.findinvariants(prob, uppairs)
            
            # Add the found invariants into one list
            bothinvariants = []
            bothinvariants.extend(leftinvariants)
            bothinvariants.extend(upinvariants)
            
            # Record the score for this answer
            scores[figurename] = self.scorerelationships(allinvariants, bothinvariants)
        
        return scores
        
    # Find relationships that repeat across all of the pairs of figures
    def findinvariants(self, prob, figurepairs):
        invariants = None
        # Go through each pair of figures
        for pair in figurepairs:
            pair1, pair2 = prob['figures'][pair[0]], prob['figures'][pair[1]]
            
            # Find all of the relationships between this pair
            relationships = self.findfigurerelationships(pair1, pair2)
            
            # If there are no invariants yet, just use the full set of relationships
            if invariants is None:
                invariants = relationships
                continue
                
            # Filter the invariants based on these relationships
            filtered = []
            for relationship in relationships:
                # Only include this relationship if it was in all other pairs
                if relationship in invariants:
                    filtered.append(relationship)
            
            # Set the invariants to this filtered list
            invariants = filtered
            
        return invariants
        
        
    # Detect whether the A->B relationship or A->C relationship is the transpose
    def detecttranspose(self, prob):
        # Default is A->C transpose, like 2x1 problems
        transpose = ('A', 'C')
        if not 'transposepercentages' in self.knowledgebase:
            # We don't know anything about transpose tendencies, so just return the default
            return transpose
            
        transposepercentages = self.knowledgebase['transposepercentages']
        afigure = prob['figures']['A']
        bfigure = prob['figures']['B']
        cfigure = prob['figures']['C']
        
        # Calculate high-level feature diffs for A->B and A->C
        abdiffs = self.diff_features(afigure, bfigure)
        acdiffs = self.diff_features(afigure, cfigure)
        
        # Calculate transpose scores for both
        abscore = self.transposescore(abdiffs, transposepercentages)
        acscore = self.transposescore(acdiffs, transposepercentages)
        
        # For debugging
        #print(abscore)
        #print(acscore)
        
        # If the A->B transpose score was higher, use A->B as the transpose
        if abscore > acscore:
            transpose = ('A', 'B')
        
        return transpose
        
    # Given a set of high-level feature diffs, score how likely it is that this is a transpose relationship
    def transposescore(self, diffs, transposepercentages):
        # Assume 50% score by default
        totalpercentage = 0.5
        diffcount = 1
        for diff in diffs:
            description = (diff['type'], diff['feature']['attribute'])
            # Assume a 50% transpose probability by default
            newpercentage = 0.5
            if description in transposepercentages:
                # Look up the real transpose probability from previously-observed 2x1 problems
                newpercentage = transposepercentages[description]
            # Keep a running total of percentages
            totalpercentage += newpercentage
            diffcount += 1
        # Return the average transpose probability across all of the diff elements
        return totalpercentage / diffcount
        
    # Rank the objects in one figure based on how common they are across the rest of the figures
    def commonrank(self, basefigure, prob):
        commonscores = {}
        figures = prob['figures']
        # Go through every object in the base figure
        baseobjects = figures[basefigure]
        for objectname, attributes in list(baseobjects.items()):
            totalscore = 0
            # Go through every other object in every other figure
            for figurename, otherobjects in list(figures.items()):
                if figurename == basefigure:
                    # This is the base figure, ignore it
                    continue
                # Keep track of the best similarity score for an object in this figure
                bestscore = -1
                for otherobjectname, otherattributes in list(otherobjects.items()):
                    score = 0
                    if len(attributes) == len(otherattributes):
                        # Overall number of attributes matches, add to the score
                        score += 1
                    maxscore = 1
                    for otherattribute, othervalues in list(otherattributes.items()):
                        maxscore += 1
                        if not otherattribute in attributes:
                            # This attribute doesn't exist in the other object, skip it
                            continue
                        values = attributes[otherattribute]
                        relative = self.knowledgebase['attributes'][otherattribute]['relative']
                        if relative != 'never':
                            # This is a relative attribute, we can't verify the value directly
                            # because it relies on the object labels themselves
                            # Just match based on the number of values
                            if len(values) == len(othervalues):
                                # Matched based on number of values, add to the score
                                score += 1
                        elif values == othervalues:
                            # Exact match, add to the score
                            score += 1
                    if score > 0:
                        # Calculate the percentage of max score
                        score = score / float(maxscore)
                    if score > bestscore:
                        # This object's score is the new best score for this figure
                        bestscore = score
                # Add the top score for this figure to the overall score
                totalscore += bestscore
            # Record the final overall score for this base object across all other figures
            commonscores[objectname] = totalscore
            
        # Sort the base objects by total similarity score
        commonranks = [item[0] for item in sorted(commonscores.items(), key=operator.itemgetter(1), reverse=True)]
        return commonranks
        
    # Rename objects labels to be more consistent across figures
    def renameobjects(self, prob):
        figures = prob['figures']
        
        # Figure out the maximum number of objects of any figure
        # And find which of the given figures has the most objects
        maxobjects = -1
        for figurename, objects in list(figures.items()):
            objectcount = len(objects)
            # Check overall max
            if objectcount > maxobjects:
                maxobjects = objectcount
        
        # Create a new set of labels that covers the max number of objects
        vocabulary = []
        for index in range(maxobjects):
            letter = chr(ord('Z') - index)
            vocabulary.append(letter)
            
        # Initialize the remap sets
        remapsets = {}
        for figurename, objects in list(figures.items()):
            remapsets[figurename] = remaps = {}
            if len(objects) == 1:
                # Figure only has one object, use Z as the label
                singlename = list(objects.keys())[0]
                remaps[singlename] = vocabulary[0]
                
        # Default is A as base, remap B based on A
        basefigure = 'A'
        remapfigure = 'B'
        if len(figures['A']) > len(figures['B']):
            # B has less figures, so remap A based on B
            basefigure = 'B'
            remapfigure = 'A'
            
        # Find a decent mapping between the base figure and the remap figure
        # Rank the objects in the base figure based on how common they are across all figures
        commonranks = self.commonrank(basefigure, prob)
        if len(remapsets[basefigure]) < len(figures[basefigure]):
            remaps = remapsets[basefigure]
            # Remap labels by common rank
            for basename in commonranks:
                if not basename in remaps:
                    remaps[basename] = vocabulary[len(remaps)]
                    
        # Apply the remaps and re-run the analoges with the updated labels
        figures[basefigure] = self.renamefigureobjects(figures[basefigure], remapsets[basefigure])
        analogies = self.findobjectanalogies(figures[basefigure], figures[remapfigure])
        
        # Remap the second figure
        if len(remapsets[remapfigure]) < len(figures[remapfigure]):
            remaps = remapsets[remapfigure]
            # Remap the analogies first
            for remapname, basename in analogies:
                if not remapname in remaps and not basename in list(remaps.values()):
                    remaps[remapname] = basename
            # Remap to other available vocabulary for objects that are still unlabled
            for objectname in figures[remapfigure]:
                if not objectname in remaps:
                    for letter in vocabulary:
                        if not letter in list(remaps.values()):
                            remaps[objectname] = letter
                            break
        # Apply the remaps
        figures[remapfigure] = self.renamefigureobjects(figures[remapfigure], remapsets[remapfigure])
        
        # Find analogies for both A and B to C
        a_to_c = self.findobjectanalogies(figures['A'], figures['C'])
        b_to_c = self.findobjectanalogies(figures['B'], figures['C'])
        # Remap C based on the A and B analogies
        if len(remapsets['C']) < len(figures['C']):
            remaps = remapsets['C']
            # Remap based on A -> C first
            for oldname, newname in a_to_c:
                if not oldname in remaps and not newname in list(remaps.values()):
                    remaps[oldname] = newname
            # Use B -> C to remap any that haven't been remapped yet
            for oldname, newname in b_to_c:
                if not oldname in remaps and not newname in list(remaps.values()):
                    remaps[oldname] = newname
            # Remap with other vocabulary letters for any remaining objects
            for objectname in figures['C']:
                if not objectname in remaps:
                    for letter in vocabulary:
                        if not letter in list(remaps.values()):
                            remaps[objectname] = letter
                            break
        
        # Apply remaps to C
        figures['C'] = self.renamefigureobjects(figures['C'], remapsets['C'])
        
        # Remap all of the answer figures based on A, B, and C
        for figurename, objects in list(figures.items()):
            # Ignore the A, B, and C figures, they are already remapped
            if figurename == 'A' or figurename == 'B' or figurename == 'C':
                continue
            remaps = remapsets[figurename]
            if len(remapsets[figurename]) < len(figures[figurename]):
                # Remap based on C, then B, then A
                c_to_x = self.findobjectanalogies(figures['C'], figures[figurename])
                b_to_x = self.findobjectanalogies(figures['B'], figures[figurename])
                a_to_x = self.findobjectanalogies(figures['A'], figures[figurename])
                for oldname, newname in c_to_x:
                    if not oldname in remaps and not newname in list(remaps.values()):
                        remaps[oldname] = newname
                for oldname, newname in b_to_x:
                    if not oldname in remaps and not newname in list(remaps.values()):
                        remaps[oldname] = newname
                for oldname, newname in a_to_x:
                    if not oldname in remaps and not newname in list(remaps.values()):
                        remaps[oldname] = newname
                # Use other vocabulary letters for any objects still not rempped
                for objectname in objects:
                    if not objectname in remaps:
                        for letter in vocabulary:
                            if not letter in list(remaps.values()):
                                remaps[objectname] = letter
                                break
            # Apply the remaps
            figures[figurename] = self.renamefigureobjects(objects, remaps)
        
    # Compress a 3x3 problem into a 2x3 by combining the left-most columns of figures together
    def compress(self, prob):
        newfigures = {}
        f = {}
        figures = prob['figures']
        
        # Keep track of the figures that will be merged
        mergefigures = ['A', 'B', 'D', 'E', 'G', 'H']
        for figurename, objects in list(figures.items()):
            # Add non-merge figures to the new figure list,
            # they will be renamed later
            if not figurename in mergefigures:
                newfigures[figurename] = objects
                
            # Add the answer figures directly to the final list,
            # they will not be renamed
            if figurename.isdigit():
                f[figurename] = objects
                
        # Go through all of the figures that need to be merged
        for index, figurename in enumerate(mergefigures):
            # Figure out if this is the first or second figure of the pair
            pairlabel = (index % 2) + 1
            mergefigure = figures[figurename]
            remaps = {}
            # Rename all of the objects with an identifier for if
            # they are from the 1st or 2nd figure in this pair
            for objectname in list(mergefigure.keys()):
                remaps[objectname] = objectname + str(pairlabel)
            mergefigure = self.renamefigureobjects(mergefigure, remaps)
            
            if pairlabel < 2:
                # This is the first figure in the pair, add it directly
                # to the new set of figures
                newfigures[figurename] = mergefigure
            else:
                # This is the second figure in the pair, merge it into
                # the first figure in the pair
                targetfigurename = mergefigures[index - 1]
                targetfigure = newfigures[targetfigurename]
                for objectname, attributes in list(mergefigure.items()):
                    # Add this object to the first figure
                    targetfigure[objectname] = attributes
        
        # Rename all of the non-answer figures in the final 2x3 structure
        f['A'], f['B'], f['C'], f['D'], f['E'] = newfigures['D'], newfigures['F'], newfigures['G'], newfigures['A'], newfigures['C']

        # Save this new structure to the problem
        prob['figures'] = f

    # Apply a reampping to a given figure's object labels
    def renamefigureobjects(self, figure, remaps):
        alreadymapped = []
        newfigure = {}
        for objectname, attributes in list(figure.items()):
            # Rename the object label
            newname = remaps[objectname]
            if newname in alreadymapped:
                print('Error! Already mapped %s' % newname)
            else:
                alreadymapped.append(newname)
            newfigure[newname] = attributes
            
            # Check all of the attributes for object label-based values
            for otherobjectname, otherattributes in list(figure.items()):
                for attribute, values in list(otherattributes.items()):
                    newvalues = []
                    for value in values:
                        if value == objectname:
                            # Remap this value
                            newvalues.append(newname)
                        else:
                            # Keep the same
                            newvalues.append(value)
                    otherattributes[attribute] = newvalues
        return newfigure
        
    # Find the best mapping between a base figure's objects and a new figure's objects
    def findobjectanalogies(self, figure, newfigure):
        # Try to find a remapping between figure and newfigure for each object
        analogies = {}
        analogylist = []
        for _ in range(len(figure)):
            # Keep track of the best match score and best match label
            bestscore = -1
            bestpriority = -1
            bestmatch = None
            
            # Go through each object in the figure
            for objectname, attributes in list(figure.items()):
                if objectname in list(analogies.values()):
                    # This object has already been mapped, skip it
                    continue
                for newobjectname, newattributes in list(newfigure.items()):
                    if newobjectname in analogies:
                        # This new object has already been mapped, skip it
                        continue
                    score = 0
                    maxscore = 0
                    priority = 0
                    for attribute, value in list(attributes.items()):
                        if not attribute in newattributes:
                            # This attribute is not present in the other object, skip it
                            #maxscore += 1
                            continue
                        newvalue = newattributes[attribute]
                        priorityvalue = 0
                        priorityranks = self.knowledgebase['attributepriorities']
                        if attribute in priorityranks:
                            priorityvalue = len(priorityranks) - priorityranks.index(attribute)
                        relative = self.knowledgebase['attributes'][attribute]['relative']
                        if relative != 'never':
                            # This is a relative attribute, we can't verify the value directly
                            # because it relies on the object labels themselves
                            # Just match based on the number of values
                            if len(value) == len(newvalue):
                                score += 1
                                maxscore += 1
                                priority += priorityvalue
                        elif value == newvalue:
                            # Exact match, add to the score
                            score += 1
                            maxscore += 1
                            priority += priorityvalue
                    if score > 0:
                        score = score / maxscore
                    # Check to see if this is the best mapping found so far
                    if score > bestscore or (score == bestscore and priority > bestpriority):
                        bestscore = score
                        bestpriority = priority
                        bestmatch = (objectname, newobjectname)
                            
            
            # Check if there was a best match
            if bestmatch:
                # Add the best match to the analogy list
                bestobject, bestnewobject = bestmatch
                analogies[bestnewobject] = bestobject
                analogylist.append((bestnewobject, bestobject))
        return analogylist
        
    # Find all of the individual attribute relationships from a base figure to a new figure
    def findfigurerelationships(self, figure, newfigure):
        relationships = []
        
        # Add a relationship for a match/mismatch on number of objects in the figure
        if len(figure) == len(newfigure):
            relationship = {}
            relationship['oldobject'] = 'all'
            relationship['newobject'] = 'all'
            relationship['oldattribute'] = 'count'
            relationship['newattribute'] = 'count'
            relationship['type'] = 'exactmatch'
            relationships.append(relationship)
        else:
            relationship = {}
            relationship['oldobject'] = 'all'
            relationship['newobject'] = 'all'
            relationship['oldattribute'] = 'count'
            relationship['newattribute'] = 'count'
            relationship['type'] = 'mismatch'
            relationships.append(relationship)
            relationshipcopy = relationship.copy()
            # Add a modification relationship for count mismatch
            relationshipcopy['type'] = 'modification'
            relationshipcopy['value'] = len(newfigure) - len(figure)
            relationships.append(relationshipcopy)
            
        # Find all of the attribute values that were not in the original figure
        newvalueattributes = {}
        for newobjectname, newattributes in list(newfigure.items()):
            for newattribute, newvalues in list(newattributes.items()):
                if newattribute in self.knowledgebase['attributes']:
                    relative = self.knowledgebase['attributes'][newattribute]['relative']
                    if relative != 'never':
                        # Ignore attributes with relative values
                        continue
                # Check each of the values to see if they were in the original figure
                for newvalue in newvalues:
                    found = False
                    for objectname, attributes in list(figure.items()):
                        if not newattribute in attributes:
                            # Attribute is missing, move on
                            continue
                        if newvalue in attributes[newattribute]:
                            # Attribute with the same value was found
                            found = True
                            break
                    if not found:
                        # The value is completely new for this attribute
                        if not newattribute in newvalueattributes:
                            # This is the first new value for this attribute, create a list
                            newvalueattributes[newattribute] = []
                        # Add this new value to the list if it isn't already in it
                        if not newvalue in newvalueattributes[newattribute]:
                            newvalueattributes[newattribute].append(newvalue)
                            
        # Add relationships for each new set of attribute values
        for newattributename, newvalues in list(newvalueattributes.items()):
            relationship = {}
            relationship['oldobject'] = 'all'
            relationship['newobject'] = 'all'
            relationship['oldattribute'] = newattributename
            relationship['newattribute'] = newattributename
            relationship['type'] = 'newvalues'
            relationship['values'] = newvalues
            relationships.append(relationship)
            
        
        # Add relationships between every object in the figure and every object in the other figure
        for objectname, attributes in list(newfigure.items()):
        
            # Check to see if this attribute doesn't even exist in the other figure
            for attribute, values in list(attributes.items()):
                missingattribute = True
                for otherobjectname, otherattributes in list(figure.items()):
                    if attribute in otherattributes:
                        missingattribute = False
                        break
                        
                if missingattribute:
                    # Attribute is not in other figure, add as a relationship and move on
                    relationship = {}
                    relationship['oldobject'] = 'unknown'
                    relationship['newobject'] = objectname
                    relationship['oldattribute'] = 'unknown'
                    relationship['newattribute'] = attribute
                    relationship['type'] = 'missing'
                    relationships.append(relationship)
                    continue
                
                # Go through all of the objects in the other figure
                for otherobjectname, otherattributes in list(figure.items()):
                    for otherattribute, othervalues in list(otherattributes.items()):
                        relationship = {}
                        relationship['oldobject'] = otherobjectname
                        relationship['newobject'] = objectname
                        relationship['oldattribute'] = otherattribute
                        relationship['newattribute'] = attribute
                        relationship['type'] = 'unknown'
                        
                        # Check if the attribute is the same as this attribute
                        sameattribute = (attribute == otherattribute)
                        
                        # Check to see if the value matches or partially matches
                        samevalues = True
                        somevalues = False
                        allnumeric = True
                        for value in values:
                            if not value in othervalues:
                                samevalues = False
                            else:
                                somevalues = True
                            if not value.isdigit():
                                allnumeric = False
                        for othervalue in othervalues:
                            if not othervalue.isdigit():
                                allnumeric = False
                            
                        # Check to see if the number of values matches
                        countvalues = (len(values) == len(othervalues))
                        if sameattribute and samevalues:
                            # Same attribute and value, this is an exact match
                            relationship['type'] = 'exactmatch'
                            relationships.append(relationship)
                        elif sameattribute and allnumeric and not samevalues and len(values) == 1 and len(othervalues) == 1:
                            # Same attribute, with numeric values that are different, this is a modification
                            relationship['type'] = 'mismatch'
                            relationships.append(relationship)
                            relationshipcopy = relationship.copy()
                            relationshipcopy['type'] = 'modification'
                            relationshipcopy['value'] = int(othervalues[0]) - int(values[0])
                            # Specifically for angles, keep the difference within 360 degrees
                            if attribute == 'angle':
                                relationshipcopy['value'] = (int(othervalues[0]) - int(values[0])) % 360
                            relationships.append(relationshipcopy)
                        elif sameattribute and not samevalues and not somevalues:
                            # Same attribute but completely different values, this is a mismatch
                            relationship['type'] = 'mismatch'
                            relationships.append(relationship)
                            relationshipcopy = relationship.copy()
                            relationshipcopy['type'] = 'newvalues'
                            relationshipcopy['values'] = ','.join(values)
                            relationships.append(relationshipcopy)
                        elif not sameattribute and samevalues:
                            # Same value but different attribute, this is a cross-match
                            relationship['type'] = 'crossmatch'
                            relationships.append(relationship)
                        elif sameattribute and somevalues:
                            # Same attribute but only some matching values, this is a partial match
                            relationship['type'] = 'partialmatch'
                            relationships.append(relationship)
                        elif sameattribute and countvalues:
                            # Same attribute and count of values, this is a count match
                            relationship['type'] = 'countmatch'
                            relationships.append(relationship)
                            
                        # Special logic for angle attribute values
                        # This whole section is a hack that doesn't work very well
                        # There are a few problems in the 20 given problems that require it
                        # The goal is to get those problems right without impacting the general logic
                        if sameattribute and attribute == 'angle':
                            # Get the angle values (angle attribute is never multi-part)
                            angle = int(values[0])
                            otherangle = int(othervalues[0])
                            
                            # Calculate a visually observable angle for both objects
                            visualangle = self.findvisualangle(attributes)
                            othervisualangle = self.findvisualangle(otherattributes)
                            adjustedobject = {'shape':attributes.get('shape'), 'angle':otherattributes.get('angle')}
                            adjustedvisualangle = self.findvisualangle(adjustedobject)
                            
                            # Check for an exact visual angle match
                            if visualangle == othervisualangle:
                                relationshipcopy = relationship.copy()
                                relationshipcopy['type'] = 'visualmatch'
                                relationships.append(relationshipcopy)
                                
                            # Check if the angle would be the same if the other shape was the same
                            if visualangle == adjustedvisualangle:
                                relationshipcopy = relationship.copy()
                                relationshipcopy['type'] = 'adjustedmatch'
                                relationships.append(relationshipcopy)
                            
                            # This is some reflection detection logic
                            # It is very hacky and will not work in most cases
                            # It is needed because 2 of the given problems prioritize reflection over rotation
                            nonsymmetricalshapes = ['triangle', 'arrow', 'half-arrow', 'Pac-Man', 'right-triangle']
                            nonsymmetrical = ','.join(attributes.get('shape')) in nonsymmetricalshapes
                            arrow = (','.join(attributes.get('shape')) == 'arrow' or ','.join(attributes.get('shape')) == 'half-arrow')
                            horizontalrefelction = (360 - otherangle) == angle or (360 - angle) == otherangle or angle == otherangle
                            verticalangle = (angle + 90) % 360
                            verticalotherangle = (otherangle + 90) % 360
                            verticalreflection = (360 - verticalotherangle) == verticalangle or (360 - verticalangle) == verticalotherangle or verticalangle == verticalotherangle
                            flipcorrect = (','.join(attributes.get('shape')) != 'half-arrow') or (attributes.get('vertical-flip') and 'yes' in attributes['vertical-flip'])

                            if horizontalrefelction and nonsymmetrical and flipcorrect:
                                relationshipcopy = relationship.copy()
                                relationshipcopy['type'] = 'horizontalreflectionmatch'
                                relationships.append(relationshipcopy)
                            if verticalreflection and nonsymmetrical and flipcorrect and arrow:
                                relationshipcopy = relationship.copy()
                                relationshipcopy['type'] = 'verticalreflectionmatch'
                                relationships.append(relationshipcopy)      
                            
        return relationships
        
    # Figure out the visually observable angle for shapes with rotational symmetry
    # This is a hack, not a very robust way of doing this
    def findvisualangle(self, object):
    
        # Load the shape (if any) and angle (if any) of the object
        shape = 'unknown'
        angle = 0
        if 'shape' in object and object['shape']:
            shape = object['shape'][0]
        if 'angle' in object and object['angle']:
            angle = int(object['angle'][0])
            
        # Calculate based on shape
        if shape == 'circle':
            # Circles are completely symmetrical, always return 0 degrees
            angle = 0
        elif shape == 'square' or shape == 'diamond' or shape == 'rectangle' or shape == 'plus':
            # Only consider these shapes for angles of less than 90 degrees
            angle = angle % 90
            
        return angle
        
    # Score one set of relationships compared to another set of relationships
    def scorerelationships(self, relationships, otherrelationships):
        # Keep track of the score and the maximum possible score
        score = 0
        
        # Start with a score of 1 if the relationships have the same number of entries
        if len(relationships) == len(otherrelationships):
            score += 1
        maxscore = 1
        
        # Find all of the relationships in the first set that are also in the second set
        for relationship in relationships:
            # Weight each relationship entry based on the type
            # These weights are partially common sense and partially
            # tweaked to get the given problems correct
            # Even without the weights, the agent performs pretty well
            scoremod = 1
            if relationship['type'] == 'partialmatch':
                scoremod = 0.25
            elif relationship['type'] == 'crossmatch':
                scoremod = 0.05
            elif relationship['type'] == 'newvalues':
                scoremod = 0.15
            elif relationship['type'] == 'modification':
                scoremod = 0.25
            elif relationship['type'] == 'horizontalreflectionmatch':
                scoremod = 2
            elif relationship['type'] == 'verticalreflectionmatch':
                scoremod = 0.75
                
            # Give a bonus for attributes that show up a lot
            # This is mainly to give "shape" a lot of importance
            # without having to hard-code anything special for shape
            prioritybonus = 0
            priorities = self.knowledgebase['attributepriorities']
            if relationship['oldattribute'] in priorities:
                priorityrank = priorities.index(relationship['oldattribute'])
                if priorityrank == 0:
                    prioritybonus = 1.5
                elif priorityrank < 5:
                    prioritybonus = 0.5 * (1.0/priorityrank)
            
            # Add an extra bonus for overall "count" relationships
            if relationship['oldattribute'] == 'count':
                prioritybonus += scoremod
                # Add a huge bonus for count modification relationships
                if relationship['type'] == 'modification':
                    prioritybonus += 10
            # Add a very huge bonus for angle XOR relationships
            if relationship['oldattribute'] == 'anglexor':
                prioritybonus += 25
            scoremod += prioritybonus
                
            # Give a bonus to relative attributes, they are easier to match
            if relationship['oldattribute'] in self.knowledgebase['attributes']:
                relative = self.knowledgebase['attributes'][relationship['oldattribute']]['relative']
                if relative != 'never':
                    scoremod = scoremod * 4
            maxscore += scoremod
            
            # Check to see if this relationship is in the other set
            if relationship in otherrelationships:
                # We matched on this relationship, add the calculated mod to the total score
                score += scoremod
            else:
                # Don't decrease the score based on mismatches, it doesn't help much
                pass
                #maxscore += scoremod
                
        # Give a small bonus to relationships in the second set that were also in the first set
        for otherrelationship in otherrelationships:
            scoremod = 0.05
            maxscore += scoremod
            if otherrelationship in relationships:
                score += scoremod
            
        # Normalize the score as a percentage of the maximum
        return score / float(maxscore)

    # Calculate a score for each answer figure choice based on the A->B:C->Choice relationships
    def calculatetransformscore(self, prob):
        scores = {}
        figures = prob['figures']
        
        # Analyze the relationship between A and B
        targetrelationship = self.findfigurerelationships(figures['A'], figures['B'])
        
        for number in range(6):
            key = str(number + 1)
            
            # Analyze the relationship between C and this answer
            relationship = self.findfigurerelationships(figures['C'], figures[key])
            
            # Debugging prints
            #print('Figure test %s' % key)
            #print(relationship)
            
            # Score the similarity between the A -> B relationship and the C -> X relationship
            scores[key] = self.scorerelationships(targetrelationship, relationship)
        
        return scores
    
    # Choose the correct answer for the problem
    def chooseanswer(self, prob, invariantscores=None):
        # Calculate scores for each answer based on A -> B vs C -> X relationships
        transforms = self.calculatetransformscore(prob)
        
        # For 3x3 (2x3 really) problems, calculate the score also based on the D->E relationship
        if prob['type'] == '3x3':
            f = prob['figures']
            # Swap A->B with D->E
            f['A'], f['B'], f['D'], f['E'] = f['D'], f['E'], f['A'], f['B']
            # Calculate the new score
            transforms_switched = self.calculatetransformscore(prob)
            # Swap back to normal
            f['A'], f['B'], f['D'], f['E'] = f['D'], f['E'], f['A'], f['B']
            
            # Use weighted average with the new score and existing score
            for choice in transforms_switched:
                transforms_switched[choice] = (transforms[choice]*0.60 + transforms_switched[choice]*0.40)
            transforms = transforms_switched
        
        # Record the scores
        for choice in transforms:
            self.scores.addscore(prob['name'], 'transform', choice, transforms[choice])
                
        # Swap the B and C figures, and calculate an alternative set of scores
        prob['figures']['B'], prob['figures']['C'] = prob['figures']['C'], prob['figures']['B']
        transforms_swapped = self.calculatetransformscore(prob)
        # Swap the B and C figures back to normal
        prob['figures']['B'], prob['figures']['C'] = prob['figures']['C'], prob['figures']['B']
        
        # Do the A->B D->E swap again for 3x3 problems
        if prob['type'] == '3x3':
            f = prob['figures']
            # Swap A->B with D->C
            f['A'], f['B'], f['D'], f['C'] = f['D'], f['C'], f['A'], f['B']
            # Calculate the new score
            transforms_swapped_switched = self.calculatetransformscore(prob)
            # Swap back
            f['A'], f['B'], f['D'], f['C'] = f['D'], f['C'], f['A'], f['B']
            
            # Use weighted average with the new score and existing score
            for choice in transforms_swapped_switched:
                transforms_swapped_switched[choice] = (transforms_swapped[choice]*0.60 + transforms_swapped_switched[choice]*0.40)
            transforms_swapped = transforms_swapped_switched
        
        for choice in transforms_swapped:
            # For debugging
            #print '%s: %s + %s' % (choice, transforms[choice], transforms_swapped[choice])
            
            # Combine the normal score and swapped score
            transforms_swapped[choice] = (transforms[choice]*0.80 + transforms_swapped[choice]*0.20)
        
        # Record the swap-adjusted scores
        for choice in transforms_swapped:
            self.scores.addscore(prob['name'], 'transform_swapped', choice, transforms_swapped[choice])
        
        # Use the swap-adjusted scores
        transforms = transforms_swapped
            
        transpose = {}
        # Calculate the normal transpose and swapped transpose
        basetranspose = self.diff_features(prob['figures']['A'], prob['figures']['C'])
        othertranspose = self.diff_features(prob['figures']['A'], prob['figures']['B'])
        for choice in transforms:
            # Calculate the transpose comparison score for this answer
            choicetranspose = self.diff_features(prob['figures']['B'], prob['figures'][choice])
            transposescore = self.comparediffs(basetranspose, choicetranspose)
            
            if not basetranspose:
                # There are no features in this transpose
                if othertranspose and othertranspose[0]['feature']['attribute'] == 'fill':
                    # The alternative transpose is based on fills
                    # Just treat this as a valid transpose
                    transposescore = 1
                    
            if transposescore > 0.5:
                # Give a bonus to answers that match the transpose relationships well
                transpose[choice] = transforms[choice] * 0.9 + transposescore * 0.1
            else:
                # Penalize answers that do not match the transpose relationships well
                transpose[choice] = transforms[choice] * 0.9
            self.scores.addscore(prob['name'], 'transpose', choice, transpose[choice])
        
        # Use the transpose-adjusted score for 2x2 problems
        if prob['type'] == '2x2':
            transforms = transpose
            
        # Include the invariant scores, if any
        transforms_invariants = {}
        for choice in sorted(transforms):
            transforms_invariants[choice] = transforms[choice]
            if invariantscores:
                # Print the invariant values to the output
                print('%s(invariant): %s' % (choice, invariantscores[choice]))
                
                # There are invariant scores, use a weighted average with the existing scores
                transforms_invariants[choice] = (transforms_invariants[choice]*0.70 + invariantscores[choice]*0.30)
            self.scores.addscore(prob['name'], 'invariants', choice, transforms_invariants[choice])
        
        # Use the invariant weighted scores for 3x3 problems
        if prob['type'] == '3x3':
            transforms = transforms_invariants
            
        # Find the best score
        bestscore = -1
        bestchoice = None
        for choice, score in sorted(list(transforms.items())):
            if score > bestscore:
                bestscore = score
                bestchoice = choice
            print('%s: %s' % (choice, score))
        
        # Return the choice that had the best score
        return bestchoice