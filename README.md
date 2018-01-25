![Example for CMPE](https://raw.githubusercontent.com/ThoAppelsin/bu-prerequisite-tree/master/exampleCMPE.png)

In Boğaziçi University (BU), many departments have a lot of their courses as required,
and most of the time they are inter-dependent. If you are an irregular student,
or for some reason had to take your courses out-of-order, then these dependencies
(prerequisites and corequisites) become one of your major concerns.

# Quick Start

For a quick start, here is how to use. Explanations here are for Windows's PowerShell,
but should be very similar in other environments and OSes.
First, you need your Python environment prepared, for just once:

1) (optionally) Create a virtual environment for Python:
```powershell
# This creates a virtual environment folder called 'env'
python -m venv env

# This one activates the virtual environment
./env/Scripts/activate
```
2) Install the required packages listed under the [requirements.txt](https://github.com/ThoAppelsin/bu-prerequisite-tree/blob/master/requirements.txt):
```powershell
pip install -r requirements.txt
```

After that one-time-setup, you can just run the script as follows:

```powershell
# Make sure that your virtual environment is active first
./env/Scripts/activate

# Run the script
python PrerequisiteTree.py
```

The script should guide you from that point on. The final output will have red-ish arrows for
prerequisite relations, and green arrows for co-requisite relations.

**IMPORTANT:** The output is as reliable as the information on the BU Registration pages.
Unfortunately, they are occasionally incorrect/inaccurate. Regard the output as an overview,
and consult the syllabus of a course to make sure or when in doubt.

## Some glossary

Boğaziçi University students will mostly be very familiar with the terminology I am using here.
There could be, however, some others interested in what's going on with this project.
This brief glossary is for them.

- **Course A is a *prerequisite* of course B:** A student may enroll to course B now,
only if he/she has already successfully completed the course A before.
- **Course A is a *co-requisite* of course B:** A student may enroll to course B now,
only if he/she has already successfully completed the course A before,
or has already enrolled to course A now.
- **Irregular student:** A student who cannot take the courses on their corresponding semesters
prescribed in the curriculum. Reasons for being irregular includes, but are not limited to;
  - Not starting to the departmental education on a first semester of an educational year.
  - Changing departments.
  - Studying abroad for some semesters via exchange or Erasmus programs.

In Boğaziçi University, lectures are usually given in one of the two semesters, than in both semesters.
As it can be seen on the definition for being an irregular student, it is not so very uncommon,
even for a successful student to start getting concerned about these interdependencies.

This makes a knowledge of the dependence tree, what I like to call as the Prerequisite Tree,
a useful resource to many, and possibly even the majority of the Boğaziçi University.

## How to draw the tree by hand

1) Obtain a copy of your department's curriculum, either from your department's website, or through
[BU Registration - Departmental Programs](http://registration.boun.edu.tr/departmentalframe.asp).
2) For every course, check the dependencies of the course, either from the courses' syllabus, or through
[Bu Registration - Prerequisite Check](http://registration.boun.edu.tr/requisiteframe.htm).
3) Make a graph of courses, perhaps on a whiteboard.
4) For every dependency you have gathered, indicate the dependency, possibly via an arrow. Distinguish pre- and co-requisites.

Depending on the amount of inter-dependency in a curriculum, this could be a very easy, or a very messy task to do.
2nd step is usually the most time-consuming, because it requires one to individually check for ~40 courses.
4th step, on the other hand, is the most concerning, as it requires edges to be drawn on a ~40-node graph.

## How this program draws the tree

In the background, it essentially performs the exact same steps as described above.
On the 3rd step, where it makes a graph of courses, however, it acts rather intelligently by;

1) Preparing a dependency graph of the lectures internally.
2) Assigning hierarchical *ranks* to the lectures.
3) Grouping the lectures that share the same rank together.
4) Plot the lectures in a rank-ascending order, row by row, with same-rank lectures on the same row.

> **Course Rank:** A metric for the courses. A course with no prerequisite has the rank 0.
> Every other course has the lowest possible integer as its rank, with the constraint that a course
> must have greater rank than its prerequisites, and greater or equal rank than its co-requisites.

Rank-ordering has two advantages compared to the naive semester-ordering:

1) The edges tend to cross less over the irrelevant nodes.
2) The rank knowledge, also is very useful to a student, and now becomes clearly visible

## Future work

One thing to note here is that we did not encounter any transitive relations in the tree so far,
i.e. a relation from A to B, while there already are two other relations from A to X, and then X to B.
They would be redundant if they existed, and even if they did exist, we could reduce them out without any risk of information loss.

Given that property explained above, we think that a layout that places a prerequisite course on
a row right above the course with the prerequisite, should prevent all the multi-level crossings.

This will layout the courses in a reversed rank-order manner. This ordering could be useful, but I
believed it to be less interesting/useful. The difference is similar to the one between the
earliest and latest start plannings in project plans, where the rank-order would be analogous to
the earliest start.

The program could ask the user whether they would want the current layout, or the alternative described here.
Both have their advantages, and user could be given the choice to select one.

However, I thought and still think that the alternative is not interesting enough to make our users deal with
one further option.
