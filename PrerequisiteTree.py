from bs4 import BeautifulSoup
import requests
import regex
import math
import shutil
import sys
import os
import datetime
import pickle
from itertools import zip_longest

### Retrieve terminal dimensions
termcols, termrows = shutil.get_terminal_size()

class Course:

    def __init__(self, cidstring, cname, csem):
        self.id = Course.decompose_cidstring(cidstring)
        self.name = cname
        self.semester = csem
        self.requires = []
        self.requiredfor = []
        self.corequires = []
        self.corequiredfor = []
        self.location = None
        self.lvl = None

    @staticmethod
    def decompose_cidstring(cidstring):
        match = regex.match(r'(\p{L}+)\s*(\d+)', cidstring)
        if match:
            return (match.group(1), match.group(2))
        else:
            return (cidstring, '')

    def require(self, course):
        self.requires.append(course)
        course.requiredfor.append(self)

    def corequire(self, course):
        self.corequires.append(course)
        course.corequiredfor.append(self)

    def level(self):
        byreqs = max(c.level() for c in self.requires) + 1 if self.requires else 0
        bycoreqs = max(c.level() for c in self.corequires) if self.corequires else 0
        return max([byreqs, bycoreqs])

    def isolated(self):
        return not (self.requires or self.requiredfor or self.corequires)

    def descriptor(self, withName = False, withSem = False):
        desc = self.id[0]
        
        if self.id[1]:
            desc = desc + ' ' + self.id[1]
        if withName:
            desc = desc + ' (' + self.name + ')'
        if withSem:
            desc = desc + ' (' + self.semester + ')'
        return desc

    def descriptorlength(self, withName = False, withSem = False):
        return len(self.descriptor(withName, withSem))

    @staticmethod
    def retrieve_course_with_id(clist, cid):
        for c in clist:
            if c.id == cid:
                return c
        return None


###
### Definitions of retrieval functions
###
def retrievedepartments(loud=True):
    if loud: print('retrieving departments...', end=' ', flush=True)

    departmentsurl = r"http://registration.boun.edu.tr/departmentalframe.asp"

    departmentscontent = requests.get(departmentsurl).text
    soup = BeautifulSoup(departmentscontent, 'html.parser')
    departmentsselect = soup.find('select')

    deptoptions = departmentsselect.find_all('option')[1:]
    departments = [deptoption.get_text(strip=True) for deptoption in deptoptions]
    
    if loud: print('done')

    return departments

def retrieveversions(dept):
    departmentalurl = r"http://registration.boun.edu.tr/departmentalframe.asp"
    departmentalpostdata = {
        'department' : dept,
        'program' : 'UNDERGRADUATE'
        }

    departmentalcontent = requests.post(departmentalurl, data=departmentalpostdata).text
    soup = BeautifulSoup(departmentalcontent, 'html.parser')
    semesterselect = soup.find('select', { 'name' : 'semester' })

    versionoptions = semesterselect.find_all('option')
    versions = [str(versionoption['value']) for versionoption in versionoptions]
    
    return versions

versioncachefname = r'deptver.cache'
def cacheversions(departmentslist, loud=True):
    if loud: print('caching versions of departmental programs...', end=' ', flush=True)

    versionscache = { dept : retrieveversions(dept) for dept in departmentslist }
    
    filename = versioncachefname
    file = open(filename, 'wb')
    try:
        pickle.dump(versionscache, file)
        file.close()
        if loud: print('done')
    except:
        print(sys.exc_info()[0])
        file.close()
        if os.path.exists(filename):
            os.remove(filename)
        print('failed, error while dumping cache')

    return versionscache

def retrieveversionscache(derpartmentslist, loud=True):
    recommendedservicelife = datetime.timedelta(minutes = 15)
    absoluteservicelife = datetime.timedelta(days = 15)

    if not os.path.exists(versioncachefname):
        return cacheversions(departmentslist, loud)

    lastmodification = datetime.datetime.fromtimestamp(os.path.getmtime(versioncachefname))
    now = datetime.datetime.now()

    servicetime = now - lastmodification

    if servicetime > recommendedservicelife:
        if servicetime > absoluteservicelife:
            return cacheversions(departmentslist, loud)

        days = servicetime.days
        hours = servicetime.seconds // (60 * 60)
        minutes = servicetime.seconds // 60 % 60

        offerstring = r'Cached versions of departmental programs is '

        if days > 0:
            offerstring += str(days) + (' days ' if days > 1 else ' day ')

        if hours > 0:
            offerstring += str(hours) + (' hours ' if hours > 1 else ' hour ')

        if (days == 0 or hours == 0) and minutes > 0:
            offerstring += str(minutes) + (' minutes ' if minutes > 1 else ' minute ')
        
        offerstring += 'old. Would you like an update?'
        default = 'yes' if servicetime > (recommendedservicelife + absoluteservicelife) / 2 else 'no'

        if offeryesno(offerstring, default):
            return cacheversions(departmentslist, loud)

    filename = versioncachefname
    file = open(filename, 'rb')
    try:
        versioncache = pickle.load(file)
    except:
        print('error while reading from cache file')
        versioncache = cacheversions(departmentchoice, loud)

    file.close()

    return versioncache

def retrievecourses(dept, version, loud=True):
    if loud: print('retrieving courses...', end=' ', flush=True)

    coursesurl = r"http://registration.boun.edu.tr/scripts/departmentcourse.asp"
    coursespostdata = {
        'department' : dept,
        'program' : 'UNDERGRADUATE',
        'semester' : version
        }

    coursescontent = requests.post(coursesurl, data=coursespostdata).text
    soup = BeautifulSoup(coursescontent, 'html.parser')
    tables = soup.find_all('table')

    if len(tables) < 2:
        print('failed, this program has no courses')
        sys.exit()

    coursestable = tables[1]
    courserows = coursestable.find_all('tr')[1:]
    courses = [Course(cells[0].get_text(strip=True), cells[1].get_text(strip=True), int(cells[2].get_text(strip=True)))
               for cells in (row.find_all('td') for row in courserows)]

    if loud: print('done')

    return courses

###
### Definitions of the offering functions
###
def printlist(offerlist, columncount):
    rowcount = math.ceil(len(offerlist) / columncount)
    columnwid = (termcols - 1) // columncount

    columns = []
    for i in range(columncount):
        start = i * rowcount
        end = start + rowcount
        column = [offer for offer in offerlist[start:end]]

        longestnrwid = len(str(end))
        longestofferwid = max(len(offer) for offer in column)

        for idx, offer in enumerate(column):
            offernr = repr(start + idx + 1).rjust(longestnrwid)
            column[idx] = (offernr + ') ' + offer).ljust(columnwid)[:columnwid]

        columns.append(column)

    rowtuples = zip_longest(*columns, fillvalue='')
    
    print('\n'.join(''.join(rowtuple) for rowtuple in rowtuples))

def offerthelist(question, offerlist, columncount=1, default=False):
    printlist(offerlist, columncount)

    if default:
        question += ' (default: ' + str(default) + ')'

    while True:
        print(question)
        inp = input()

        if inp:
            if inp.isdigit():
                choice = int(inp)
            else:
                continue
        else:
            choice = default

        if 1 <= choice <= len(offerlist):
            break

    return choice - 1

def offeryesno(question, default="yes"):
    valid = { "yes": True, "y": True, "ye": True,
              "no": False, "n": False }

    if default is None:
        prompt = " [y/n]"
    elif default in valid:
        prompt = " [Y/n]" if valid[default] else " [y/N]"
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        print(question + prompt, end=' ', flush=True)
        choice = input().lower()

        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').")

################                     ################
################ Program Starts Here ################
################                     ################

###
### Retrieval of departments
###
departmentslist = retrievedepartments()

###
### Retrieval of versions (cached?)
###
versionscache = retrieveversionscache(departmentslist)
departmentslist[:] = [dept for dept in departmentslist
                      if dept in versionscache and versionscache[dept]]

### Offering the departments for selection
offerabledepartmentslist = [dept.replace(';', '') for dept in departmentslist]
departmentchoice = offerthelist('For which department would you like to have it?', offerabledepartmentslist, columncount=2)
versionslist = versionscache[departmentslist[departmentchoice]]

### Offering the versions for selection
offerableversionslist = [start + ' -- ' + end for (start, end) in zip(versionslist, ['ongoing'] + versionslist[:-1])]
versionchoice = offerthelist('And for which version of the curriculum?', offerableversionslist, default=1)

###
### Retrieval of courses
###
courseslist = retrievecourses(departmentslist[departmentchoice], versionslist[versionchoice])

###
### Retrieval of requisites
###
print('retrieving requisites...', end=' ', flush=True)
prereqstring = r'Course Prerequisites:'

# This has been removed due to update in the website.
# funkystring = r'GPA, Being Senior or Junior Student and Consent of Instructor Prerequisites:'

coreqstring = r'Corequisites:'

def extractcids(str):
    cidstrings = regex.findall(r'[A-Z]{2,4}\s*[1-9][0-9][A-Z0-9]', str)
    cids = (Course.decompose_cidstring(c) for c in cidstrings)
    return cids

# abbreviations are not allowed to be longer than 4
abbreviations = {course.id[0] for course in courseslist if len(course.id[0]) <= 4 and course.id[1]}
requisitedictionary = {}

requisitesurl = r"http://registration.boun.edu.tr/scripts/prerequisitecheck.asp"
for abbr in abbreviations:
    requisitespostdata = {
        'abbr' : abbr
        }
    requisitescontent = requests.post(requisitesurl, data=requisitespostdata).text

    soup = BeautifulSoup(requisitescontent, 'html.parser')

    coreqstringanchor = soup.find(text=coreqstring)

    prereqtables = [table for table in coreqstringanchor.find_all_previous('table') if table in soup.find(text=prereqstring).find_all_next('table')]
    for prereqtable in prereqtables:
        prereqrows = prereqtable.find_all('tr', bgcolor=False)

        for prereqrow in prereqrows:
            cells = prereqrow.find_all('td')
        
            course = Course.decompose_cidstring(cells[0].get_text(strip=True))
            prereqs = set(extractcids(cells[1].get_text(strip=True)))

            if course in requisitedictionary:
                if 'pre' in requisitedictionary[course]:
                    requisitedictionary[course]['pre'] |= prereqs
                else:
                    requisitedictionary[course]['pre'] = prereqs
            else:
                requisitedictionary[course] = {'pre': prereqs}

    coreqtables = [table for table in coreqstringanchor.find_all_next('table')]
    for coreqtable in coreqtables:
        coreqrows = coreqtable.find_all('tr', bgcolor=False)

        for coreqrow in coreqrows:
            cells = coreqrow.find_all('td')
        
            course = Course.decompose_cidstring(cells[0].get_text(strip=True))
            coreqs = set(extractcids(cells[1].get_text(strip=True)))

            if course in requisitedictionary:
                if 'co' in requisitedictionary[course]:
                    requisitedictionary[course]['co'] |= coreqs
                else:
                    requisitedictionary[course]['co'] = coreqs
            else:
                requisitedictionary[course] = {'co': coreqs}

print('done')


###
### Addition of requisites to courses
###
for course in courseslist:
    if course.id in requisitedictionary:
        requisites = requisitedictionary[course.id]
        
        if 'pre' in requisites:
            for reqcid in requisites['pre']:
                reqcourse = Course.retrieve_course_with_id(courseslist, reqcid)
                if reqcourse:
                    course.require(reqcourse)

        if 'co' in requisites:
            for coreqcid in requisites['co']:
                coreqcourse = Course.retrieve_course_with_id(courseslist, coreqcid)
                if coreqcourse:
                    course.corequire(coreqcourse)

###
### Classification of courses in requirement levels
###
levels = {}
for course in courseslist:
    level = course.level()
    if level in levels:
        levels[course.level()].append(course)
    else:
        levels[course.level()] = [course]

###
### Visualization
###
import turtle

def calculatesaturation(color):
    return (max(color) - min(color)) / max(color)

def changesaturation(color, saturation):
    currentsaturation = calculatesaturation(color)

    if currentsaturation == 0:
        return (color[0], color[0] * (1 - saturation), color[0] * (1 - saturation))

    factor = saturation / currentsaturation
    maxcolor = max(color)
    return tuple(map(lambda color: maxcolor - (maxcolor - color) * factor, color))

class Turt(turtle.Turtle):
    def goto(self, x, y):
        self.setheading(self.towards(x, y))
        super().goto(x, y)

    def setcolor(self, color, saturation=1):
        color = changesaturation(color, saturation)

        self.pencolor(color)
        self.fillcolor(color)

    def drawarrowhead(self, pos, heading, color, size=0.5):
        size *= self.pensize()

        arrowhead = turtle.Turtle(visible=False)
        arrowhead.resizemode('auto')
        arrowhead.pensize(size)
        arrowhead.color(color, color)
        arrowhead.penup()
        arrowhead.speed(0)
        arrowhead.setpos(*pos)
        arrowhead.setheading(heading)
        return arrowhead

    def drawline(self, end, start=None):
        if start:
            self.penup()
            self.goto(*start)
        
        self.pendown()
        self.goto(*end)
        self.penup()

    def drawarrow(self, end, start=None):
        startvec = turtle.Vec2D(*start) if start is not None else t.pos()
        endvec = turtle.Vec2D(*end)
        lineend = endvec + (startvec - endvec) * (self.pensize() / abs(startvec - endvec))
        
        self.drawline(lineend, start)
        arrowhead = self.drawarrowhead(end, self.heading(), self.pencolor())
        arrowhead.showturtle()

    def drawoutarrow(self, end, outdentation, outdirection, start):
        self.penup()
        self.goto(*start)

        # A for first corner
        # B for second corner

        if outdirection == 'r':
            [Ax, Bx] = [max(start[0], end[0]) + outdentation] * 2
        elif outdirection == 'l':
            [Ax, Bx] = [min(start[0], end[0]) - outdentation] * 2
        else:
            Ax, Bx = start[0], end[0]

        if outdirection == 'u':
            [Ay, By] = [max(start[1], end[1]) + outdentation] * 2
        elif outdirection == 'd':
            [Ay, By] = [min(start[1], end[1]) - outdentation] * 2
        else:
            Ay, By = start[1], end[1]

        self.pendown()

        self.goto(Ax, Ay)
        self.goto(Bx, By)
        self.drawarrow(end)


swid = 1300
shei = 850

screen = turtle.Screen()
screen.setup(swid, shei)
t = Turt()
t.speed(0)
t.resizemode('auto')

fsize = 10
color = (.1, .1, .1)
font = ('Consolas', fsize, 'normal')

fhei = fsize / 0.7
fwid = fsize

reqcolor = (.9, .5, .4)
coreqcolor = (.4, .8, .5)

t.penup()

def coursewidthforlist(courseslist):
    return min(16, max(9, max(course.descriptorlength() for course in courseslist)))

leveldistance = 60 + fhei
maxcoursedistance = fwid * coursewidthforlist(courseslist)
baseoutdentation = 18
basepensize = 1.25
pensizeincrement = 1.25
basesaturation = 0.8
saturationfactor = 0.7

t.pensize(basepensize)

maxcoursesinrow = (swid * 0.9) // maxcoursedistance
isolatedlevels = []

if len(levels[0]) > maxcoursesinrow:
    isolatedcourses = [c for c in levels[0] if c.isolated()]
    levels[0][:] = [c for c in levels[0] if not c.isolated()]

    while isolatedcourses:
        isolatedlevelcount = math.ceil(len(isolatedcourses) / maxcoursesinrow)
        coursesinrow = math.ceil(len(isolatedcourses) / isolatedlevelcount)

        isolatedlevels.append(isolatedcourses[:coursesinrow])
        isolatedcourses[:] = isolatedcourses[coursesinrow:]

maxlevel = max(levels.keys()) + len(isolatedlevels)
midlevel = maxlevel / 2

for level, courses in enumerate(isolatedlevels):
    coursecount = len(courses) - 1
    halfcount = coursecount / 2;

    coursedistance = fwid * coursewidthforlist(courses)

    for idx, course in enumerate(courses):
        t.goto((idx - halfcount) * coursedistance, (midlevel - level) * leveldistance)
        t.write(course.descriptor(), align='center', font=font)

for level, courses in levels.items():
    if not courses:
        continue

    pensize = basepensize + pensizeincrement * (len(levels) - level - 1)
    saturation = basesaturation * saturationfactor ** (len(levels) - level - 1)

    t.pensize(pensize)

    coursecount = len(courses) - 1
    halfcount = coursecount / 2

    coursedistance = fwid * coursewidthforlist(courses)

    for idx, course in enumerate(courses):
        t.setcolor(color)

        tx = (idx - halfcount) * coursedistance
        ty = (midlevel - (level + len(isolatedlevels))) * leveldistance
        
        course.location = (tx, ty)
        course.lvl = level

        t.goto(tx, ty)
        t.write(course.descriptor(), align='center', font=font)
        
        if course.requires:
            t.setcolor(reqcolor, saturation)
            for req in course.requires:
                start = (tx, ty + fhei)
                end = (req.location[0], req.location[1])

                t.drawarrow(end, start)

#                lvldifference = course.lvl - req.lvl
#
#                if lvldifference == 1:
#                    start = (tx, ty + fhei)
#                    end = (req.location[0], req.location[1])
#
#                    t.drawarrow(end, start)
#                else:
#                    meanatleft = (tx + req.location[0]) / 2 < 0
#                    
#                    outdirection = 'l' if meanatleft else 'r'
#                    start = (tx + course.descriptorlength() * fwid / 2 * (-1 if meanatleft else 1), ty + fhei / 2)
#                    end = (req.location[0] + req.descriptorlength() * fwid / 2 * (-1 if meanatleft else 1), req.location[1] + fhei / 2)
#
#                    t.drawoutarrow(end, baseoutdentation * ((lvldifference - 1) * 1.75 + 1), outdirection, start)

        if course.corequires:
            t.setcolor(coreqcolor, saturation)
            outdentix = 1
            for coreq in course.corequires:
                if coreq.location:
                    if coreq.location[1] == ty:
                        start = (tx - fhei, ty)
                        end = (coreq.location[0] + fhei, coreq.location[1])
                        outdentation = (outdentix) * baseoutdentation
                        outdentix = outdentix + 1

                        t.drawoutarrow(end, outdentation, 'd', start)
                    else:
                        start = (tx, ty + fhei)
                        end = (coreq.location[0], coreq.location[1])

                        t.drawarrow(end, start)

screen.mainloop()