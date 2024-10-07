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
        r += x
```
In words: Sum all integers from $a$ (inclusive) to $b$ (exclusive) if they are greater than $c$.

Rephrased: Sum all integers which are $\ge a$, $\lt b$ and $\gt c$.

$\gt c$ can be transformed to $\ge c + 1$ because we are dealing with integers.

So we are looking at integers which are greater than or equal than both $a$ as well as $c + 1$ meaning they need to be $\ge max(a, c + 1)$.
Therefor, the example becomes
```
for i in range(max(a, c + 1), b):
    r += x
```
The formula for the [second example](#motivation)
## A real world example
## Performance
### Time complexity
### Runtime
## Performance of the algorithm itself
