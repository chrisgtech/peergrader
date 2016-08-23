# Process raw image files into useful properties
# This represents most of the changes for Project 4
# This module requires Pillow 2.6.1

# Import standard python libraries
import sys, operator, hashlib
from uuid import uuid4

# Import Pillow 2.6.1
from PIL import Image, ImageOps, ImageChops, ImageDraw, ImageFont

DISTINCT_COLORS = [(0x00, 0xFF, 0x00), (0x00, 0x00, 0xFF), (0xFF, 0x00, 0x00), (0x01, 0xFF, 0xFE), (0xFF, 0xA6, 0xFE), (0xFF, 0xDB, 0x66), (0x00, 0x64, 0x01), (0x01, 0x00, 0x67), (0x95, 0x00, 0x3A), (0x00, 0x7D, 0xB5), (0xFF, 0x00, 0xF6), (0xFF, 0xEE, 0xE8), (0x77, 0x4D, 0x00), (0x90, 0xFB, 0x92), (0x00, 0x76, 0xFF), (0xD5, 0xFF, 0x00), (0xFF, 0x93, 0x7E), (0x6A, 0x82, 0x6C), (0xFF, 0x02, 0x9D), (0xFE, 0x89, 0x00), (0x7A, 0x47, 0x82), (0x7E, 0x2D, 0xD2), (0x85, 0xA9, 0x00), (0xFF, 0x00, 0x56), (0xA4, 0x24, 0x00), (0x00, 0xAE, 0x7E), (0x68, 0x3D, 0x3B), (0xBD, 0xC6, 0xFF), (0x26, 0x34, 0x00), (0xBD, 0xD3, 0x93), (0x00, 0xB9, 0x17), (0x9E, 0x00, 0x8E), (0x00, 0x15, 0x44), (0xC2, 0x8C, 0x9F), (0xFF, 0x74, 0xA3), (0x01, 0xD0, 0xFF), (0x00, 0x47, 0x54), (0xE5, 0x6F, 0xFE), (0x78, 0x82, 0x31), (0x0E, 0x4C, 0xA1), (0x91, 0xD0, 0xCB), (0xBE, 0x99, 0x70), (0x96, 0x8A, 0xE8), (0xBB, 0x88, 0x00), (0x43, 0x00, 0x2C), (0xDE, 0xFF, 0x74), (0x00, 0xFF, 0xC6), (0xFF, 0xE5, 0x02), (0x62, 0x0E, 0x00), (0x00, 0x8F, 0x9C), (0x98, 0xFF, 0x52), (0x75, 0x44, 0xB1), (0xB5, 0x00, 0xFF), (0x00, 0xFF, 0x78), (0xFF, 0x6E, 0x41), (0x00, 0x5F, 0x39), (0x6B, 0x68, 0x82), (0x5F, 0xAD, 0x4E), (0xA7, 0x57, 0x40), (0xA5, 0xFF, 0xD2), (0xFF, 0xB1, 0x67), (0x00, 0x9B, 0xFF), (0xE8, 0x5E, 0xBE)]

hashdb = {}

def pasteoutline(image, paste, location, linesize=3, label=None):
    width, height = paste.size
    outline = (location[0] - linesize, location[1] - linesize, location[0] + width + linesize, location[1] + height + linesize)
    image.paste((0,0,0), outline)
    image.paste(paste, location)
    if label:
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("calibri.ttf", 36)
        draw.text((location[0], location[1]-35), label, (0,0,0), font=font)
        
def printproblem(figures):
    size = width, height = figures.values()[0]['image'].size
    problems = {}
    answers = {}
    for name in figures:
        dest = answers
        if name.lower() in 'abcdefghijklmnopqrstuvxyz':
            dest = problems
        dest[name] = figures[name]
        
    lastproblem = sorted(problems.keys())[-1]
    question = chr(ord(lastproblem) + 1)
    questimage = image = Image.new('RGB', size, 'white')
    font = ImageFont.truetype("calibri.ttf", 160)
    draw = ImageDraw.Draw(image)
    draw.text((50, 20), '?', (0,0,0), font=font)
    problems[question] = {'name':question, 'image':questimage}
    
    buffer = int(width * 0.2)
    totalwidth = len(answers) * (width + buffer) + buffer
    totalheight = 2 * (height + buffer*2) + buffer*2
    totalsize = (totalwidth, totalheight)
    image = Image.new('RGB', totalsize, 'white')
    for index, answer in enumerate(sorted(answers.keys())):
        top = (buffer + (buffer + width) * index, height + buffer*5)
        pasteoutline(image, answers[answer]['image'], top, label=answer)
    for index, problem in enumerate(sorted(problems.keys())):
        if index > 1:
            index += 1
        top = (buffer + (buffer + width) * index, buffer*2)
        pasteoutline(image, problems[problem]['image'], top, label=problem)
    return image
    
def printfigures(figures):
    print '** TESTING **'
    image = printproblem(figures)
    image.save('problem.png')
    colored = {}
    colors = DISTINCT_COLORS
    for name, figure in figures.items():
        colored[name] = dict(figure)
        oldimage = colored[name]['image']
        newimage = blackandwhite(oldimage)
        newimage, usedcolors = colorize(newimage, colors)
        print len(usedcolors)
        for usedcolor in usedcolors:
            colors.remove(usedcolor)
        colored[name]['image'] = newimage
    image = printproblem(colored)
    image.save('detected.png')
    metrics = ['outsideness', 'darkness', 'connectedness']
    maxes = {}
    mins = {}
    splitted = {}
    for name, figure in figures.items():
        splits = colorsplit(figure['image'])
        for split in splits:
            details = analyzeobject(split)
            for metric in metrics:
                if not metric in maxes or maxes[metric] < details[metric]:
                    maxes[metric] = details[metric]
                if not metric in mins or mins[metric] > details[metric]:
                    mins[metric] = details[metric]
    for name, figure in figures.items():
        splitted[name] = dict(figure)
        splits = colorsplit(figure['image'])
        recolored = []
        for split in splits:
            details = analyzeobject(split)
            rgb = [0,0,0]
            for index, metric in enumerate(metrics):
                value = details[metric]
                value = value - mins[metric]
                range = maxes[metric] - mins[metric]
                if index < 1:
                    value = min(value*1.5, range)
                elif index < 2:
                    value = value * 0.35
                else:
                    value = value * 0.8
                print metric
                #print mins[metric]
                #print value
                #print maxes[metric]
                #print value
                #print range
                if range > 0.00001:
                    value = value * (1.0 / range)
                else:
                    value = 1.0
                value = int(value * 255)
                #if metric != 'connectedness':
                #    value = 1
                rgb[index] = value
                print value
            #rgb[0] = 0
            #rgb[2] = 0
            newcolor = tuple(rgb)
            newcolored, dummy = colorize(split, [newcolor, (0,0,0)])
            recolored.append(newcolored)
        combined = None
        for recolor in recolored:
            if not combined:
                combined = recolor
            else:
                combined = ImageChops.multiply(combined, recolor)
        splitted[name]['image'] = combined
    image = printproblem(splitted)
    image.save('analyzed.png')
    print '** DONE **'
    #exit()

# Crop an image to remove unneeded white space
def crop(image):
    # Invert the image so the bounding box calculation works
    inverted = ImageOps.invert(image.convert('L'))
    # Found a bounding box for the non-white parts of the image
    box = inverted.getbbox()
    # Return the cropped image and bounding box
    return image.crop(box), box

# Convert an image to pure black and white (not grayscale)
def blackandwhite(image):
    # Convert to grayscale first
    grayscale = image.convert('L')
    def filter(value):
        if value == 255:
            return 255 # White pixels stay white
        else:
            return 0 # All other pixels turn to pure black
    # Apply the filter
    blackwhite = grayscale.point(filter, '1')
    #Return the filtered image
    return blackwhite
    
# Walk through an image pixel by pixel
def walk(image):
    width, height = image.size
    # Go through each pixel sequentially
    for index, pixel in enumerate(image.getdata()):
        # Calculate the current position
        x = index % width
        y = index / width
        # Yield the current position and value
        yield (x,y,pixel)

# Colorize distinct objects in a black and white image
def colorize(blackandwhiteimage, colorset=DISTINCT_COLORS):
    # Convert the black and white image to RGB
    image = blackandwhiteimage.convert('RGB')
    width, height = image.size
    colorindex = 0
    colors = []
    # Color each connected section of black pixels
    while True:
        # Choose a new color
        color = colorset[colorindex]
        colorindex += 1
        # Find the first black pixel
        blackpixel = None
        for x, y, pixel in walk(image):
            # Found the first black pixel
            if pixel == (0, 0, 0):
                blackpixel = (x,y)
                break
        if not blackpixel:
            # No more black pixels, the image is fully colored
            break
        colors.append(color)
        
        # Keep track of neighboring black pixels
        neighbors = [blackpixel]
        # Keep finding neighbors until we don't find any more black pixels
        while len(neighbors) > 0:
            # Make a new list of the current neighbors
            processing = list(neighbors)
            # Clear the neighbors we are going to process from the list
            neighbors = []
            # Process each of the neighbors
            for x,y in processing:
                # Color this neighbor
                image.putpixel((x,y), color)
                # Find all of the neighboring pixels
                new = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
                # Go through the neighbors
                for x,y in new:
                    if (x,y) in neighbors:
                        # Already added, skip
                        continue
                    if x < 0 or x >= width:
                        # Invalid x value, skip
                        continue
                    if y < 0 or y >= height:
                        # Invalid y value, skip
                        continue
                    if image.getpixel((x,y)) != (0, 0, 0):
                        # Non-black pixel, skip
                        continue
                    # Add the neighboring black pixel to be processed
                    neighbors.append((x,y))
    #imagehash = hashlib.md5(image.tostring()).hexdigest()
    #image.save('temp//%s.png' % imagehash)
    return image, colors

# Split the image into distinct objects by colorizing it
def colorsplit(image):
    # Colorize the image
    image, colors = colorize(image)
    splitimages = []
    # Go through each colored object
    for color in colors:
        # Make a copy of the image for this object
        colorimage = image.copy()
        # Walk through every pixel
        for x,y, pixel in walk(colorimage):
            # Ignore this pixel by default and make it white
            newpixel = (255, 255, 255)
            if pixel == color:
                # This pixel is the correct color, make it black
                newpixel = (0, 0, 0)
            if pixel != newpixel:
                # Change the current pixel color to this new one
                colorimage.putpixel((x,y), newpixel)
        # Convert the image copy to grayscale
        colorimage = colorimage.convert('L')
        # Add this object's image to the list
        splitimages.append(colorimage)
    return splitimages
    
# Calculate what kind of symmetry (if any) this image/object has
def findsymmetry(image):
    # This process is expensive to calculate
    # Check to see if we have already analyzed this same object/image
    imagehash = hashlib.md5(image.tostring()).hexdigest()
    if imagehash in hashdb and 'findsymmetry' in hashdb[imagehash]:
        # Return the previously calculated values
        return hashdb[imagehash]['findsymmetry']
    elif not imagehash in hashdb:
        hashdb[imagehash] = {}
        
    # Only check these specific angles
    angles = [45, 90, 120, 135, 180, 225, 240, 270, 280, 315]
    symmetries = []
    # Make an inverted copy of the image for processing
    inverted = ImageOps.invert(image)
    for angle in angles:
        # Rotate and re-crop the image
        rotated = inverted.rotate(angle, expand=True)
        rotated = ImageOps.invert(rotated)
        rotated, rotbox = crop(rotated)
        blackpixels = 0
        matchedpixels = 0
        # Check to see how many pixels are the same in this rotation
        for x,y,pixel in walk(image):
            # Ignore all white pixels in the original image
            if pixel > 0:
                continue
            # Keep track of the number of black pixels from the original image
            blackpixels += 1
            # Ignore pixels that are off the sides of the new image
            if x >= rotated.size[0] or y >= rotated.size[1]:
                continue
            # Check if the new pixel is also black
            if rotated.getpixel((x,y)) < 1:
                # Keep track of how many black pixel matches there have been
                matchedpixels += 1
        # Calculate the ratio of matched black pixels
        matched = matchedpixels / float(blackpixels)
        # Check if this is above the threshold for a rotation match
        if matched > 0.75:
            # Add this angle to the list of symmetrical angles
            symmetries.append(angle)
    symmetry = 'Unknown'
    # Figure out the specific type of symmetry from the list of symmetric angles
    if len(symmetries) > len(angles) - 3:
        symmetry = 'Full'
    elif len(symmetries) == 0:
        symmetry = 'None'
    elif 45 in symmetries and  135 in symmetries and  225 in symmetries and  315 in symmetries:
        symmetry = 'Eighth'
    elif 90 in symmetries and  180 in symmetries and  270 in symmetries:
        symmetry = 'Quarter'
    # Equilateral triangles should be Third symmetry but in practice they
    # are not detected as being symmetrical at all
    #elif 120 in symmetries and 240 in symmetries:
    #    symmetry = 'Third'
    elif 180 in symmetries:
        symmetry = 'Half'
        
    # Store this result so that we don't re-calculate it later
    hashdb[imagehash]['findsymmetry'] = (symmetry, symmetries)
    # Return the symmetry type and the symmetrical angles
    return symmetry, symmetries
    
# Find this image/object's angle offset from the "ideal" angle
# This is needed because we know objects will be rotated but we
# aren't comparing them against each other directly
# Instead we arbitarily define conditions for the ideal angle
# and rotate until we find it
# An object's offset from the ideal angle tells us its relative angle
# compared to any other object of the same shape
def findangleoffset(image, symmetry, symmetries):
    # This process is expensive to calculate
    # Check to see if we have already analyzed this same object/image
    imagehash = hashlib.md5(image.tostring()).hexdigest()
    if imagehash in hashdb and 'findangleoffset' in hashdb[imagehash]:
        # Return the previously calculated values
        return hashdb[imagehash]['findangleoffset']
    elif not imagehash in hashdb:
        hashdb[imagehash] = {}
        
    angleoffset = -1
    lastangle = 360
    # If this object has rotational symmetry, only check up to the next symmetrical angle
    if symmetries and symmetry != 'None' and symmetry != 'Unknown':
        lastangle = symmetries[0]
    # Check any kind of object other than full symmetry (circle)
    if symmetry != 'Full':
        rotangles = {}
        lowestsize = None
        lowestimage = None
        secondlowestsize = None
        lowestangle = None
        # Look for the "ideal" angle
        # Go through angles 5 degrees at a time
        for angle in range(0, lastangle/5):
            angle = angle * 5
            # Rotate and crop by the current angle
            rotated = ImageOps.invert(image).rotate(angle, expand=True)
            rotated = ImageOps.invert(rotated)
            rotated, rotbox = crop(rotated)
            newwidth, newheight = rotated.size
            # Use a size check that is heavily-weighted 
            newpixels = newwidth + newheight*.05
            # Check if this angle resulted in the lowest size
            if not lowestsize or newpixels < lowestsize:
                # If there was a previous lowest, save this as the second lowest
                if lowestsize:
                    secondlowestsize = lowestsize
                lowestsize = newpixels
                lowestangle = angle
                lowestimage = rotated
            # Otherwise check if this is the second lowest
            elif not secondlowestsize or newpixels < secondlowestsize:
                secondlowestsize = newpixels
            rotangles[angle] = rotated
        
        angleoffset = 0
        if lowestsize:
            # Set the "ideal" angle as the lowest size
            angleoffset = lowestangle
            image = lowestimage
        
        # If this is a non-symmetrical shape, do more analysis
        if symmetry == 'None' or symmetry == 'Unknown':
            if not secondlowestsize:
                secondlowestsize = lowestsize
                
            # Look for local minima angles in terms of size
            peakangles = {}
            for angle in list(sorted(rotangles.keys())):
                anglewidth, angleheight = rotangles[angle].size
                anglesize = anglewidth + angleheight*.05
                # Check if the counter-clockwise neighbor is lower
                neighborwidth, neighborheight = rotangles[(angle - 5) % 360].size
                neighborsize = neighborwidth * neighborheight
                if anglesize > neighborsize:
                    continue
                # Check if the clockwise neighbor is lower
                neighborwidth, neighborheight = rotangles[(angle + 5) % 360].size
                neighborsize = neighborwidth * neighborheight
                if anglesize > neighborsize:
                    continue
                # Lower than both neighbors, this is a local minimum angle
                peakangles[angle] = rotangles[angle]
                
            # Look for angles that are close to the second-lowest angle
            closeangles = {}
            for angle in list(sorted(peakangles.keys())):
                anglewidth, angleheight = peakangles[angle].size
                anglesize = anglewidth + angleheight*.05
                if anglesize < secondlowestsize * 1.01:
                    # Close enough to the second-lowest to be counted
                    closeangles[angle] = peakangles[angle]
            
            # Look for the actual best angle from the filtered list
            # The point of this is to arbitrarily prefer one configuration
            # of pixels over any other
            # This way no matter what the starting angle, we should rotate
            # to the same actual image
            bestangle = None
            bestscore = 1.1
            for angle in list(sorted(closeangles.keys())):
                anglewidth, angleheight = closeangles[angle].size
                left = anglewidth / 2
                up = angleheight / 2
                moreleft = anglewidth / 4
                moreup = angleheight / 4
                score = 1
                maxscore = 1
                
                # Walk through each pixel of this object angle
                for newx, newy, pixel in walk(closeangles[angle]):
                    if pixel == 0:
                        continue
                    # Assign a score to each pixel base on its location
                    mod = 1
                    if newx > moreleft:
                        mod += 2
                    if newx > left:
                        mod += 2
                    if newy > moreup:
                        mod += 1
                    if newy > up:
                        mod += 1
                    # Pixels further to the right and down are scored higher
                    maxscore += 7
                    score += mod
                
                # Check if this score is the lowest
                score = score / float(maxscore)
                if score < bestscore:
                    # This is the best angle so far
                    bestscore = score
                    bestangle = angle
                    
            # Save the best angle as the angle offset
            if not closeangles:
                angleoffset = 0
            else:
                angleoffset = bestangle
                image = closeangles[bestangle]
                
    # Store this result so that we don't re-calculate it later
    hashdb[imagehash]['findangleoffset'] = (angleoffset, image)
    return angleoffset, image
    
# Analyze a black and white image of a single object
def analyzeobject(image):
    # Store some basic details about this object/image
    details = {}
    details['id'] = id = uuid4().hex
    cropped, box = crop(image)
    details['box'] = box
    details['size'] = width, height = cropped.size
    details['rotsize'] = cropped.size
    totalpixels = width * height
    
    # Find the type of rotational symmetry (if any) and the symmetrical angles
    symmetry, symmetries = findsymmetry(cropped)
        
    # Find the object's absolute roation compared to the "ideal" angle for this shape
    angleoffset, cropped = findangleoffset(cropped, symmetry, symmetries)
    
    # Keep track of various stats for this object
    width, height = cropped.size
    details['rotsize'] = cropped.size
    totalpixels = width * height
    darkpixels = 0
    connectedpixels = 0
    outsidepixels = 0
    currenty = 0
    firstdark = 999999999
    lastdark = -1
    
    # Go through all of the pixels
    for x,y,pixel in walk(cropped):
        # Check if this is a new line
        if currenty != y:
            currenty = y
            # Check if there any black pixels
            if firstdark < 999999999 and lastdark > -1:
                # Add the number of white pixels before the first black one
                outsidepixels += firstdark
                # Add the number of white pixels after the last black one
                outsidepixels += width - lastdark - 1
            # Reset the first/last markers for this new line
            firstdark = 999999999
            lastdark = -1
            
        # Check if this is a black pixel
        if pixel != 255:
            # Keep track of the total number of black pixels
            darkpixels += 1
            
            # Keep track of the first/last black pixels for this line
            if firstdark > x:
                firstdark = x
            if lastdark < x:
                lastdark = x
            
            # Check if any neighboring pixels are black
            neighbors = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
            for x2, y2 in neighbors:
                if x2 < 0 or x2 >= width:
                    continue
                if y2 < 0 or y2 >= height:
                    continue
                if cropped.getpixel((x2, y2)) != 255:
                    connectedpixels += 0.25
    
    # Add the last line's outside white pixels
    if firstdark < 999999999 and lastdark > -1:
        outsidepixels += firstdark
        outsidepixels += width - lastdark - 1
            
    # Calculate that metrics for this object
    details['darkness'] = darkpixels / float(totalpixels)
    details['connectedness'] = connectedpixels / float(darkpixels)
    details['outsideness'] = outsidepixels / float(totalpixels)
    details['symmetry'] = symmetry
    details['aspect'] = width / float(height)
    if angleoffset > -1:
        details['angleoffset'] = angleoffset
        
    # Return all of the calculations
    return details
    
# Find the relationships between two boundary boxes
def compareboxes(box, otherbox):
    relationships = []
    # Find the corners and centers
    boxupx, boxupy, boxdownx, boxdowny = box
    oboxupx, oboxupy, oboxdownx, oboxdowny = otherbox
    boxcenterx, boxcentery = boxupx + (boxdownx - boxupx)/2.0, boxupy + (boxdowny - boxupy)/2.0
    oboxcenterx, oboxcentery = oboxupx + (oboxdownx - oboxupx)/2.0, oboxupy + (oboxdowny - oboxupy)/2.0
    
    # Check to see if the box is inside the other box
    if boxupx > oboxupx and boxupy > oboxupy and boxdownx < oboxdownx and boxupy < oboxdowny:
        relationships.append('inside')
        
    # Check to see if the box is left of the other box
    if boxcenterx < oboxupx:
        relationships.append('left-of')
        
    # Check to see if the box is above the other box
    if boxcentery < oboxupy:
        relationships.append('above')
        
    return relationships
    
# Analyze a set of figure images for a problem, and return the problem definition
def analyze(figureimages):
    # Process the figure images and split them into individual object images
    figures = {}
    for figurename, figurepath in list(sorted(figureimages.items())):
        image = Image.open(figurepath)
        image = blackandwhite(image)
        figure = {}
        figure['name'] = figurename
        figure['file'] = figurepath
        figure['image'] = image
        figure['splits'] = colorsplit(image)
        figures[figurename] = figure
        
    printfigures(figures)
    prob = {}
    objects = {}
    
    # Go through each figure's objects and check for angles and fills
    # If there are no fills or no angles, those details won't be added to the problem
    fillmin = 0.5
    anyfills = False
    anyangles = False
    for figurename, figure in list(sorted(figures.items())):
        prob[figurename] = {}
        for object in figure['splits']:
            details = analyzeobject(object)
            details['figure'] = figurename
            objects[details['id']] = details
            #imagehash = hashlib.md5(object.tostring()).hexdigest()
            #object.save('temp//%s.png' % imagehash)
            #import fileutils
            #fileutils.dump(details, 'temp//%s.txt' % imagehash)
            if details['darkness'] > fillmin:
                anyfills = True
            if 'angleoffset' in details and details['angleoffset'] > 0:
                anyangles = True
    
    # Partition the objects into distinct shapes
    shapes = {}
    used = []
    while True:
        # Give each shape an arbitrary name
        shapeindex = len(shapes) + 1
        shapename = 'shape' + str(shapeindex)
        # Go through each object
        shape = []
        for object in list(sorted(objects.values())):
            # Check if this object is already assigned to a shape
            if object['id'] in used:
                continue
            # Check if this shape has no objects yet
            if not shape:
                # Add this object by default as the first object of this shape
                shape.append(object)
                continue
            # Go through each existing object assigned to this shape
            for shapeobject in shape:
                # Check the difference in outside shape
                diff = abs(shapeobject['outsideness'] - object['outsideness'])
                # Check to see if the symmetry types are the same
                if 'symmetry' in shapeobject and 'symmetry' in object:
                    rotationmatch = (shapeobject['symmetry'] == object['symmetry'])
                    if rotationmatch:
                        # Reduce the difference somewhat to account for the similarity
                        diff -= 0.05
                if diff < 0.03:
                    # Close enough, add this object to the shape
                    shape.append(object)
                    break
        # Check if no objects were added to this shape
        if not shape:
            # Stop looking for new shapes, we are out of objects
            break
        # Mark all of the objects for this shape as used
        for object in shape:
            used.append(object['id'])
        # Save the objects of this shape
        shapes[shapename] = shape
        
    # Look for particular hard-coded named shapes
    newshapes = {}
    for shapename, shape in list(sorted(shapes.items())):
        # Calculate some average/mode values
        symmetries = {}
        aspecttotal = 0
        outsidetotal = 0
        for object in shape:
            outsidetotal += object['outsideness']
            aspecttotal += object['aspect']
            symmetry = object['symmetry']
            if not symmetry in symmetries:
                symmetries[symmetry] = 0
            symmetries[symmetry] += 1
        outsideaverage = outsidetotal / float(len(shape))
        aspectaverage = aspecttotal / float(len(shape))
        symmetry = max(symmetries.iteritems(), key=operator.itemgetter(1))[0]
        
        # Check the calculated average values against known shape types
        # This is optional but helps in some cases
        # For example, it's not possible to recognize a horizontal reflection
        # unless the shape is known, so that the "up" angle can be determined
        newshapename = shapename
        if symmetry == 'Full' and .15 < outsideaverage < .25 and 0.9 < aspectaverage < 1.1:
            newshapename = 'circle'
        elif symmetry == 'Quarter' and outsideaverage < .05 and 0.9 < aspectaverage < 1.1:
            newshapename = 'square'
        elif symmetry == 'Half' and outsideaverage < .05 and 1.2 < aspectaverage < 2.2:
            newshapename = 'rectangle'
        elif symmetry == 'Quarter' and .2 < outsideaverage < .3 and 0.9 < aspectaverage < 1.1:
            newshapename = 'plus'
        elif (symmetry == 'None' or symmetry == 'Unknown') and .4 < outsideaverage < .5 and 0.75 < aspectaverage < 0.85:
            newshapename = 'triangle'
            # Correct the symmetry value
            symmetry = 'Third'
            # Correct some common visual identifaction errors
            for object in shape:
                if 'angleoffset' in object and (object['angleoffset'] == 205 or object['angleoffset'] == 210):
                    object['angleoffset'] = 335
        elif (symmetry == 'None' or symmetry == 'Unknown') and .4 < outsideaverage < .5 and 0.4 < aspectaverage < .6:
            newshapename = 'right-triangle'
            symmetry = 'None'
        elif (symmetry == 'None' or symmetry == 'Unknown') and .25 < outsideaverage < .35 and 0.75 < aspectaverage < .95:
            newshapename = 'Pac-Man'
            symmetry = 'None'
        else:
            pass
            #print symmetry
            #print outsideaverage
            #print aspectaverage
            
        # Add this shape to the new shapes list
        if not newshapename in newshapes:
            newshapes[newshapename] = []
        for object in shape:
            object['symmetry'] = symmetry
            newshapes[newshapename].append(object)
        
    # Replace the old shape sets with the new one
    shapes = newshapes
        
    # Keep track of which shapes have more than one angle in this problem
    # If a shape has only one angle, the angle value won't be included in the problem
    angleshapes = []
    for shapename, objectlist in list(sorted(shapes.items())):
        # Keep track of a single angle
        uniqueangle = None
        for object in objectlist:
            if 'angleoffset' in object:
                angle = object['angleoffset']
                if uniqueangle != None and uniqueangle != angle:
                    # More than one angle for this shape, add it to the list
                    angleshapes.append(shapename)
                    break
                else:
                    # Mark this angle as the single angle found so far
                    uniqueangle = angle
                    
    # Keep track of all objects and their shapes
    allobjects = []
    for shapename, shape in list(sorted(shapes.items())):
        for object in shape:
            object['shape'] = shapename
            allobjects.append(object)
             
#    This code could be used to find how deep objects are embedded in other objects
#    In practice it did not end up being useful
#    depths = {}
#    for object in allobjects:
#        depth = 0
#        for otherobject in allobjects:
#            if object['id'] == otherobject['id']:
#                continue
#            if object['figure'] != otherobject['figure']:
#                continue
#            relationships = compareboxes(object['box'], otherobject['box'])
#            if 'inside' in relationships:
#                depth += 1
#        if not depth in depths:
#            depths[depth] = []
#        depths[depth].append(object)
        
    sizes = {'very-small':[], 'small':[], 'medium':[], 'large':[], 'very-large':[]}
    objectoffsets = {}
    shapesizes = {}
    # Find the relative size of each object within a shape
    for shapename, shape in list(sorted(shapes.items())):
        shapesizes[shapename] = {}
        # Partition the objects into size bins
        for object in shape:
            width, height = object['rotsize']
            # By default use the actual size of this object as a key
            size = width * height
            # Look through the existing sizes in the shape
            for existingsize in shapesizes[shapename]:
                bigsize, smallsize = size, existingsize
                if existingsize > size:
                    bigsize, smallsize = smallsize, bigsize
                # Figure out the difference between this size and the existing one
                diff = bigsize - smallsize
                if diff < bigsize * 0.25:
                    # Close enough, assign this object to the existing size value
                    size = existingsize
                    break
            # Add a slot for this size if it doesn't exist already
            if not size in shapesizes[shapename]:
                shapesizes[shapename][size] = []
            # Add this object to the chosen size
            shapesizes[shapename][size].append(object)
            
        # Calculate the English size word for each object given the size bins
        halfindex = len(shapesizes[shapename]) / 2
        for sizeindex, size in enumerate(list(sorted(shapesizes[shapename].keys()))):
            # The middle size is zero, negative and positive values are smaller and larger
            sizeoffset = sizeindex - halfindex
            sizename = 'unknown'
            if sizeoffset < -1:
                sizename = 'very-small'
            elif sizeoffset < 0:
                sizename = 'small'
            elif sizeoffset < 1:
                sizename = 'medium'
            elif sizeoffset < 2:
                sizename = 'large'
            else:
                sizename = 'very-large'
            # Assign this size word to each of the objects of this size
            for object in shapesizes[shapename][size]:
                sizes[sizename].append(object)
        
    # Give each object an arbitrary unique name
    for index, object in enumerate(list(sorted(objects.values()))):
        objectname = 'O' + str(index+1)
        object['name'] = objectname
    
    # Fill in the official properties of each object in the problem
    for index, object in enumerate(list(sorted(objects.values()))):
        description = {}
        figurename = object['figure']
        objectname = object['name']
        box = object['box']
        for shapename, shape in list(sorted(shapes.items())):
            if object in shape:
                description['shape'] = [shapename]
        for sizename, size in list(sorted(sizes.items())):
            if object in size:
                description['size'] = [sizename]
        if anyfills:
            # Check if the object is dark enough to be considered filled
            if object['darkness'] > fillmin:
                description['fill'] = ['yes']
            else:
                description['fill'] = ['no']
        # Check if there are any angles in this problem at all
        if anyangles and angleshapes and 'angleoffset' in object:
            # Angles are relevant, record the angle value
            description['angle'] = [object['angleoffset']]
        # Find the relative values compared to other objects
        for otherobject in list(sorted(objects.values())):
            if otherobject['id'] == object['id']:
                continue
            if otherobject['figure'] != figurename:
                continue
            othername = otherobject['name']
            otherbox = otherobject['box']
            # Find the relationships between this two objects
            relationships = compareboxes(box, otherbox)
            if relationships:
                for relationship in relationships:
                    if not relationship in description:
                        description[relationship] = []
                    # Add this relative relationship to the description
                    description[relationship].append(othername)
        # Check if adding a symmetry value would be redundant
        if description['shape'][0].startswith('shape') and 'symmetry' in object and object['symmetry'] != 'Unknown':
            # This shape needs a symmetry designation, so add it
            description['symmetry'] = [object['symmetry']]
            
        # Add the description of this object to the problem definition
        prob[figurename][objectname] = description
    return prob