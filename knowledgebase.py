# Some methods for keeping track of knowledge across problems

# Load the attributes of the current problem into the knowledge base
def scanattributes(knowledgebase, prob):
    # Get a list of object labels (used later to figure out if values are referring to objects)
    objectnames = []
    for figure in list(prob['figures'].values()):
        for objectname in list(figure.keys()):
            if not objectname in objectnames:
                objectnames.append(objectname)
                
    # Create the attributes section if it doesn't exist
    if not 'attributes' in knowledgebase:
        knowledgebase['attributes'] = {}
    attributes = knowledgebase['attributes']
    
    # Process every attribute
    for figure in list(prob['figures'].values()):
        for object in list(figure.values()):
            for attribute, subvalues in list(object.items()):
                # Get or create the entry for this attribute
                if not attribute in attributes:
                    attributes[attribute] = {}
                info = attributes[attribute]
                if not 'values' in info:
                    info['values'] = []
                if not 'relative' in info:
                    info['relative'] = 'unknown'
                if not 'multi' in info:
                    info['multi'] = 'unknown'
                if not 'count' in info:
                    info['count'] = 0
                
                # Keep track of how many times this attribute was processed
                info['count'] += 1
                
                # Update whether or not this attribute has multiple sub values
                if len(subvalues) > 1:
                    if info['multi'] == 'unknown':
                        info['multi'] = 'always'
                    elif info['multi'] == 'never':
                        info['multi'] = 'sometimes'
                else:
                    if info['multi'] == 'unknown':
                        info['multi'] = 'never'
                    elif info['multi'] == 'always':
                        info['multi'] = 'sometimes'
                
                # Process each subvalue
                values = attributes[attribute]['values']
                for subvalue in subvalues:
                    # Update whether or not this attribute refers to other objects
                    relative = False
                    if subvalue in objectnames:
                        relative = True
                        if info['relative'] == 'unknown':
                            info['relative'] = 'always'
                        elif info['relative'] == 'never':
                            info['relative'] = 'sometimes'
                    else:
                        if info['relative'] == 'unknown':
                            info['relative'] = 'never'
                        elif info['relative'] == 'always':
                            info['relative'] = 'sometimes'
                            
                    # Add this value to the list if it isn't in it already
                    # Ingore the value if it's just an object label
                    if not relative and not subvalue in values:
                        values.append(subvalue)

# Analyze the answer to this problem, to help with future problems  
def analyzeanswer(knowledgebase, prob, answer, differ):
    # Create a diffs section if it doesn't already exist
    if not 'diffs' in knowledgebase:
        knowledgebase['diffs'] = {'transpose':{}, 'transform':{}}
    diffs = knowledgebase['diffs']
    
    # Calculate all of the high-level transpose and transform diffs
    basetranspose = differ(prob['figures']['A'], prob['figures']['C'])
    answertranspose = differ(prob['figures']['B'], prob['figures'][answer])
    basetransform = differ(prob['figures']['A'], prob['figures']['B'])
    answertransform = differ(prob['figures']['C'], prob['figures'][answer])
    
    # Save this information if it's a 2x1 problem
    # This will help later when we analyze 2x2 problems
    if prob['type'] == '2x1':
        # Record all of the transpose features
        for diff in basetranspose+answertranspose:
            type = diff['type']
            attribute = diff['feature']['attribute']
            description = (type, attribute)
            if not description in diffs['transpose']:
                # This feature wasn't seen before, add it
                diffs['transpose'][description] = 1
            else:
                # This feature as already seen, update the count
                diffs['transpose'][description] += 1
                
        # Record all of the transform features
        for diff in basetransform+answertransform:
            type = diff['type']
            attribute = diff['feature']['attribute']
            description = (type, attribute)
            if not description in diffs['transform']:
                diffs['transform'][description] = 1
                # This feature wasn't seen before, add it
            else:
                # This feature as already seen, update the count
                diffs['transform'][description] += 1
    

# Update the knowledge base to account for the latest information
def updateknowledge(knowledgebase):
    # Sort the attributes by the count of how many times they have been seen
    attributepriority = []
    attributes = knowledgebase['attributes']
    for _ in range(len(attributes)):
        highest = -1
        attribute = None
        for name, info in list(attributes.items()):
            if name in attributepriority:
                continue
            count = info['count']
            if count > highest:
                highest = count
                attribute = name
        attributepriority.append(attribute)
    knowledgebase['attributepriorities'] = attributepriority
    
    # Calculate the probability that a given feature is part of a transpose
    if 'diffs' in knowledgebase:
        transposepercentages = {}
        transposediffs = knowledgebase['diffs']['transpose']
        transformdiffs = knowledgebase['diffs']['transform']
        for description in list(transposediffs.keys())+list(transformdiffs.keys()):
            if description in transposepercentages:
                # Ignore duplicates
                continue
                
            # Start with one in each category to avoid infinite ratios
            transposecount = 1.0
            transformcount = 1.0
            
            # Update the counts using the info from the knowledge base
            if description in transposediffs:
                transposecount += transposediffs[description]
            if description in transformdiffs:
                transformcount += transformdiffs[description]
                
            # Calculate the ratio of transpose to transform counts
            transposepercentages[(description[0], description[1])] = transposecount / (transposecount+transformcount)
        knowledgebase['transposepercentages'] = transposepercentages

# Find friendly human-readable names for objects
# This isn't really necessary other than to make debugging more pleasant
def findobjectnames(knowledgebase, prob):
    priorities = knowledgebase['attributepriorities']
    # Find a unique name for each object in a figure
    allnames = {}
    for figurename, objects in list(prob['figures'].items()):
        allnames[figurename] = figurenames = {}
        # Keep track of how many objects we couldn't find a unique name for
        nonunique = 1
        for objectname, attributes in list(objects.items()):
            uniquename = ''
            unique = False
            usedattributes = []
            # Check attributes in priority order
            for priority in priorities:
                if not priority in attributes:
                    # This priority isn't in this object
                    continue
                    
                # Make a name out of the attributes we've found so far
                uniquename = '%s %s:%s' % (uniquename, priority, ','.join(attributes[priority]))
                usedattributes.append(priority)
                
                # Check to see if this set of attribute values is unique
                unique = True
                for otherobjectname, otherattributes in list(objects.items()):
                    if otherobjectname == objectname:
                        # This is the same object, ignore
                        continue
                    same = True
                    for attribute in usedattributes:
                        if not attribute in otherattributes:
                            # This attribute isn't in the other object
                            # Stop checking this object and move on
                            same = False
                            break
                        allmatched = True
                        for subvalue in attributes[attribute]:
                            if not subvalue in otherattributes[attribute]:
                                # A subvalue doesn't match, so move on
                                allmatched = False
                                break
                        if not allmatched:
                            # A subvalue didn't match
                            same = False
                            break
                    if same:
                        # Another object completely matched on this set of attributes
                        # Set as non-unique and stop checking objects
                        unique = False
                        break
                if unique:
                    # We found a unique name, stop adding more attributes
                    break
            if not unique:
                # We didn't find a unique name, even after checking all attributes
                # (This means two objects in the same figure are identical)
                nonuniquename = uniquename
                # Give it a unique number
                while uniquename.strip() in list(figurenames.values()):
                    nonunique += 1
                    uniquename = '%s %s' % (nonuniquename, nonunique)
            figurenames[objectname] = uniquename.strip()
    return allnames