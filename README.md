# loop-to-constant
This repository provides an algorithm for transforming certain for loops into equivalent code with constant time complexity.
Currently, it can parse Python code and output the transformed code in Python and C++.
## Motivation
Both in mathematics

$r = \sum_{i=a}^{b-1} 1$

as well as in programming 
```
for i in range(a, b):
    r += 1
```
it is sometimes necessary to compute a sum over a constant.

A trained eye will see that these sums can be replaced by  `r = b - a`.
What happens with sums over the index itself?
```
for i in range(a, b):
    r += i
```
With a bit of mathematical finesse one can come with `r = (b**2 - b + a - a**2) / 2`.

What about `i**2`, `e**i`, ...? The complexity of the summand can of course be increased indefinitely but finding closed form formulas for mathematical sums isn't what this project aims to do.

Instead, consider another "type" of complexity:
```
for i in range(a, b):
    if c < i:
        r += x
```
A bit more complex:
```
for i in range(a, b):
    for j in range(c, d):
        r += i + j
```
Even more complex:
```
for i in range(a, b):
    for j in range(c, i):
        r += j
```
Note that the upper border for `j` is  now the index `i` of the enclosing for loop.

But we can go way further:
```
for i in range(a, b):
    for j in range(c, max(f, i)):
        if e < max(g, i):
            result += min(h, i) + j
```
And so on and so forth.

These (nested) for loops have in common that they are the programmatic representation of mathematical sums. This project aims at finding closed form solutions to this kind of for loops, that is, transforming them into code without any for loops.
## How it works
The examples above (except the last one) consist of 3 types of expressions: for loops, if clauses and summands. The goal is to eliminate all for loops. If we find universal transformation rules for these 3 types of expressions we can let a computer do the rest.
#### Transforming a for loop over a summand
As mentioned above this project's goal isn't to solve mathematical problems. Mathematicians have been doing that for hundreds of years. This project uses Sympy, a Python library for symbolic mathematics, to solve these problems.

Now we can transform for loops over a summand. What if there is an if clause inbetween though?
#### Merging an if clause into a for loop
```
for i in range(a, b):
    if c < i:
        r += i
```
In words: Sum all integers from $a$ (inclusive) to $b$ (exclusive) if they are greater than $c$.

Rephrased: Sum all integers which are $\ge a$, $\lt b$ and $\gt c$.

$\gt c$ can be transformed to $\ge c + 1$ because we are dealing with integers.

So we are looking at integers which are greater than or equal than both $a$ as well as $c + 1$ meaning they need to be $\ge max(a, c + 1)$.
Therefor, the example becomes
```
for i in range(max(a, c + 1), b):
    r += i
```
That's a for loop over a summand and as mentioned in [Merging an if clause into a for loop](#transforming-a-for-loop-over-a-summand) we can let Sympy do the rest.

With the formula for the [second example](#motivation) it can be done manually too:
```
r = (b**2 - b + max(a, c + 1) - max(a, c + 1)**2) / 2
```
#### What to do with min/max?
The last example contains calls to `min()` and `max()`. As shown above, merging if clauses into for loops also creates such terms.

Unfortunatelly, dealing with `min()` and `max()` isn't exactly straight forward. If you want to understand how it is done take a look at the code, specifically at the `eliminate_symbol_from_max_min()` methods and the `SympyMaxMinSplitter` class.
## Usage
Download [loop_to_constant.py](loop_to_constant.py). At the very end of the file you will find the variable `python_string`. Set it to your Python code (or try the provided example). Execute.

The transformed Python code will be printed to the console. C++ is supported as well: Just below `python_string` change `.dump_python()` to `.dump_cpp()`.

Just above `python_string` there are a few settings. Try manipulating them and see whether/how it affects the result.

Note that the provided examples increment variables (e.g. `r+=...`) which were never defined. That's intentional. The algorithm expects that and assumes these variables to have an initial value of 0.
### Dependencies
- [Sympy](https://www.sympy.org/en/index.html)
## A real world example
Finding a closed from formula for for loops is all well and good, but what do we actually need that for? 

Imagine you have $n$ apples to give away and there are $5$ people in need of apples. How many possibilities to distribute your apples to the $5$ people are there?
If $n = 0$, there are $p = 0$ possibilities.
If $n = 1$, $p = 5$ because you can give your apple to person $1$, $2$, $3$, $4$ or $5$.
If $n = 2$, $p = 15$. There actually exists a mathematical formula for this.

In my situation there were additional constraints: There was a maximum and minimum number of apples per person. The maximum was the same for all persons, the minimum values varied. No formula exists for this modified problem.

The function in [real_world_example.cpp](real_world_example.cpp) returns a `std::vector` of all possible apple distributions (not just the number of possibilities). Depending on the parameters there might be millions of possibilities resulting in millions of calls to `std::vector::push_back` resulting in many, many, many reallocations. Not millions, but still a lot. Reallocations are expensive.

The solution: Using this algorithm to calculate the number of possibilities first. Once you know this number you can reserve just as much memory as necessary resulting in just a single allocation and no reallocations. (Btw., no, a linked list wouldn't have solved the problem. A linked list doesn't require reallocations, yes, but it requires one small allocation per element which is way more expensive than just a single big allocation)
## Performance
### Time complexity
### Runtime
## Performance of the algorithm itself
