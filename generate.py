import sys
import copy

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == variable.DOWN else 0)
                j = variable.j + (k if direction == variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """

        for var in self.domains:
            for word in self.domains[var].copy():
                if len(word) != var.length:
                    self.domains[var].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        remove = set()
        revised = False
        if self.crossword.overlaps[x, y]:
            m, n = self.crossword.overlaps[x, y][0], self.crossword.overlaps[x, y][1]
            for i in self.domains[x]:
                if not any(i[m] == y_element[n] for y_element in self.domains[y]):
                    remove.add(i)
                    revised = True
        self.domains[x] -= remove
        return revised

    def ac3(self, arcs=None, dom = None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs == None:
            arcs = [i for i in self.crossword.overlaps if self.crossword.overlaps[i] is not None]
        for arc in arcs:
            x, y = arc
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                if not dom:
                    for z in self.crossword.neighbors(x)-{y}:
                        arcs.append((z, x))
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        if len(assignment) == len(self.crossword.variables):
            return all(assignment.values())
        return False

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        seen_values = []
        for i in assignment:
            if assignment[i]:
                if len(assignment[i]) != i.length:
                    return False
                if assignment[i] in seen_values:
                    return False
                seen_values.append(assignment[i])
                neighbors = self.crossword.neighbors(i)
                if neighbors:
                    for n in neighbors:
                        if n in assignment and assignment[n]:
                            x, y = self.crossword.overlaps[n,
                                                           i][0], self.crossword.overlaps[n, i][1]
                            if assignment[n][x] != assignment[i][y]:
                                return False
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        v_new = 0
        domain = []
        values = []
        original_var_domain = self.domains[var].copy()
        list_neighbor = self.crossword.neighbors(var)
        original_neighbor_domain = dict()
        neighbor = []
        for i in list_neighbor:
            original_neighbor_domain[i] = self.domains[i].copy()
            neighbor.append((i, var))
        for i in original_var_domain:
            self.domains[var] = {i}
            if self.ac3(neighbor,dom=True):
                for j in list_neighbor:
                    if not (j in assignment and assignment[j]):
                        v_new += len(original_neighbor_domain[j])-len(self.domains[j])
                domain.append(i)
                values.append(v_new)
                v_new = 0
        for i in list_neighbor:
            self.domains[i] = original_neighbor_domain[i].copy()
        self.domains[var] = original_var_domain.copy()
        sorted_elements = [element for _, element in sorted(zip(values, domain))]
        return sorted_elements

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        length = float('inf')
        chosen_variable = None
        length_neigh = 0
        for i in self.crossword.variables:
            if assignment and i in assignment and assignment[i]:
                continue
            else:
                Len = len(self.domains[i])
                if Len < length:
                    chosen_variable = i
                    length = Len
                    length_neigh = len(self.crossword.neighbors(i))
                elif Len == length:
                    neighbor = len(self.crossword.neighbors(i))
                    if length_neigh < neighbor:
                        chosen_variable = i
        return chosen_variable

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        assignment1 = assignment.copy()
        if self.assignment_complete(assignment):
            return assignment
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            assignment[var] = value
            if self.consistent(assignment):
                domain = copy.deepcopy(self.domains)
                self.domains[var] = {assignment[var]}
                list_neighbor = self.crossword.neighbors(var)
                neighbor = []
                for i in list_neighbor:
                    neighbor.append((i, var))
                if not self.ac3(neighbor):
                    return False
                result = self.backtrack(assignment)
                if result:
                    return result
                assignment = assignment1.copy()
                self.domains = copy.deepcopy(domain)
            else:
                assignment = assignment1.copy()
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
