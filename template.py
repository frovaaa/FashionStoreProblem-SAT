#!/usr/bin/env python3

## Default executable of a SAT solver (do not change this)
defSATsolver="z3"

## Change this to an executable SAT solver if z3 is not in your PATH or else
## Example (Linux): SATsolver="/home/user/z3-4.13/bin/z3"
## You can also include command-line options if necessary
SATsolver=defSATsolver

import sys
from subprocess import Popen
from subprocess import PIPE
import re
import random
import os
import shutil

gVarNumberToName = ["invalid"]
gVarNameToNumber = {}

def closed_range(start, stop, step=1):
    dir = 1 if (step > 0) else -1
    return range(start, stop + dir, step)

def varCount():
    global gVarNumberToName
    return len(gVarNumberToName) - 1

def allVarNumbers():
    return closed_range(1, varCount())

def varNumberToName(num):
    global gVarNumberToName
    return gVarNumberToName[num]

def varNameToNumber(name):
    global gVarNameToNumber
    return gVarNameToNumber[name]

def addVarName(name):
    global gVarNumberToName
    global gVarNameToNumber
    gVarNumberToName.append(name)
    gVarNameToNumber[name] = varCount()

# def printClause(clause):
#     print(map(lambda x: "%s%s" % (x < 0 and eval("'-'") or eval ("''"), varNumberToName(abs(x))) , clause))

def getVarNumber(**kwargs):
    return varNameToNumber(getVarName(**kwargs))

def getVarName(**kwargs):
    ##+ Insert here the code to define a variable name based on your application-specific parameters
    pass

    # example:
    # idx = kwargs['idx']
    # return "myVar(%d)" % (idx)

def genVarNames(**kwargs):
    ##+ Insert here the code to generate the variable names
    pass

    # example:
    # count = kwargs['count']
    # for i in closed_range(1, count):
    #     name = getVarName(idx=i)
    #     addVarName(name)

def genClauses(**kwargs):
    clauses = []

    ##+ Insert here the code to add constraints in the form of clauses
    # example:
    # count = kwargs['count']
    # ## exactly one of our variables must be true:
    # clauses.append([getVarNumber(idx=i) for i in closed_range(1, count)])
    # for i in closed_range(1, count):
    #     for j in closed_range(i+1, count):
    #         clauses.append([-getVarNumber(idx=i), -getVarNumber(idx=j)])
    ##+ End of code insertion

    return clauses

## A helper function to print the cnf header (do not modify)
def getDimacsHeader(clauses):
    cnt = varCount()
    n = len(clauses)
    str = ""
    for num in allVarNumbers():
        varName = varNumberToName(num)
        str += "c %d ~ %s\n" % (num, varName)
    for cl in clauses:
        print("c ", end='')
        for l in cl:
            print(("!" if (l < 0) else " ") + varNumberToName(abs(l)), "", end='')
        print("")
    print("")
    str += "p cnf %d %d" % (cnt, n)
    return str

## A helper function to print a set of clauses in CNF (do not modify)
def toDimacsCnf(clauses):
    return "\n".join(map(lambda x: "%s 0" % " ".join(map(str, x)), clauses))

## A helper function to print only the satisfied variables in human-readable format (do not modify)
def printResult(res):
    print(res)
    res = res.strip().split('\n')

    # If it was satisfiable, we want to have the assignment printed out
    if res[0] != "s SATISFIABLE":
        return

    # First get the assignment, which is on the second line of the file, and split it on spaces
    # Read the solution
    asgn = map(int, res[1].split()[1:])
    # Then get the variables that are positive, and get their names.
    # This way we know that everything not printed is false.
    # The last element in asgn is the trailing zero and we can ignore it

    # Convert the solution to our names
    facts = map(lambda x: varNumberToName(abs(x)), filter(lambda x: x > 0, asgn))

    # Print the solution
    print("c SOLUTION:")
    for f in facts:
        print("c", f)

## This function is invoked when the python script is run directly and not imported
if __name__ == '__main__':
    path = shutil.which(SATsolver.split()[0])
    if path is None:
        if SATsolver == defSATsolver:
            print("Set the path to a SAT solver via SATsolver variable on line 9 of this file (%s)" % sys.argv[0])
        else:
            print("Path '%s' does not exist or is not executable." % SATsolver)
        sys.exit(1)

    kwargs = {}

    ##+ Insert here the code to read the arguments of your application and fill them into 'kwargs'
    # example:
    # if len(sys.argv) != 2:
    #     print("Usage: %s <count>" % sys.argv[0])
    #     sys.exit(1)

    # kwargs['count'] = int(sys.argv[1])
    ##+ End of code insertion

    genVarNames(**kwargs)
    clauses = genClauses(**kwargs)

    head = getDimacsHeader(clauses)
    cnf = toDimacsCnf(clauses)

    # Here we create a temporary cnf file for SATsolver
    fl = open("tmp_prob.cnf", "w")
    fl.write("\n".join([head, cnf]) + "\n")
    fl.close()

    # Run the SATsolver
    solverOutput = Popen([SATsolver + " tmp_prob.cnf"], stdout=PIPE, shell=True).communicate()[0]
    res = solverOutput.decode('utf-8')
    printResult(res)
