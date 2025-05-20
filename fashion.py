#!/usr/bin/env python3

SATsolver="/home/edoardo/Desktop/z3-4.12.4-x64-glibc-2.31/bin/z3"

import sys
from subprocess import Popen, PIPE
from itertools import combinations

# Data structures for garments and colors
garments = {}
colors = set()

# Constraints configuration
MIN_G, MAX_G = 3, 6
MIN_C, MAX_C = 2, 4
color_clashes = [("red", "pink")]
layering = [("coat", "top")]
one_per_body_part = ["hat", "coat", "top", "bottom", "shoes", "gloves"]

# SAT variables and mappings
gVarNumberToName = ["invalid"]
gVarNameToNumber = {}

# Helper functions
def varCount():
    return len(gVarNumberToName) - 1

def varNameToNumber(name):
    return gVarNameToNumber[name]

def addVarName(name):
    gVarNumberToName.append(name)
    gVarNameToNumber[name] = varCount()

def getVarName(garment, color):
    return f"{garment}_{color}"

def genVarNames():
    for garment in garments:
        for color in garments[garment]:
            addVarName(getVarName(garment, color))

def genClauses():
    clauses = []

    # A: Outfit size constraints (MIN_G to MAX_G)
    all_vars = [varNameToNumber(getVarName(g, c)) for g in garments for c in garments[g]]

    clauses.append(all_vars)  # At least one garment
    for comb in combinations(all_vars, MAX_G + 1):  # At most MAX_G garments
        clauses.append([-x for x in comb])

    # At least MIN_G garments
    for comb in combinations(all_vars, len(all_vars) - MIN_G + 1):
        clauses.append([x for x in comb])

    # B: Type Coverage (at least one garment per type)
    for garment_type in garments:
        clauses.append([varNameToNumber(getVarName(garment_type, c)) for c in garments[garment_type]])

    # C: Palette size constraints
    color_vars = {}
    for color in colors:
        color_vars[color] = [varNameToNumber(getVarName(g, color)) for g in garments if color in garments[g]]

    # At least MIN_C colors
    clauses.append([var for color_group in color_vars.values() for var in color_group])

    # At most MAX_C colors
    for comb in combinations(colors, MAX_C + 1):
        color_comb_vars = [var for color in comb for var in color_vars[color]]
        clauses.append([-var for var in color_comb_vars])

    # D: Color Clashes
    for c1, c2 in color_clashes:
        for g1 in garments:
            if c1 in garments[g1]:
                for g2 in garments:
                    if c2 in garments[g2]:
                        clauses.append([-varNameToNumber(getVarName(g1, c1)), -varNameToNumber(getVarName(g2, c2))])

    # F: Layering Order
    for upper, lower in layering:
        if upper in garments and lower in garments:
            for upper_color in garments[upper]:
                clauses.append([-varNameToNumber(getVarName(upper, upper_color))] + [varNameToNumber(getVarName(lower, lower_color)) for lower_color in garments[lower]])

    # G: One-Per-Body-Part
    for part in one_per_body_part:
        if part in garments:
            part_vars = [varNameToNumber(getVarName(part, c)) for c in garments[part]]
            for comb in combinations(part_vars, 2):
                clauses.append([-x for x in comb])

    return clauses

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: script.py <input_file>")
        sys.exit(1)

    with open(sys.argv[1]) as file:
        for line in file:
            garment, color = line.strip().split()
            colors.add(color)
            garments.setdefault(garment, set()).add(color)

    genVarNames()
    clauses = genClauses()

    header = f"p cnf {varCount()} {len(clauses)}\n"
    cnf = "\n".join([" ".join(map(str, clause)) + " 0" for clause in clauses])

    with open("tmp_prob.cnf", "w") as f:
        f.write(header + cnf)

    solverOutput = Popen([SATsolver, "tmp_prob.cnf"], stdout=PIPE).communicate()[0]
    res = solverOutput.decode('utf-8')
    print(res)