# loop-to-constant
This repository provides an algorithm for optimizing certain for loops by transforming them into equivalent code with constant time complexity. This allows for speed-ups of several orders of magnitude.
Currently, it can parse Python code and output the transformed code in Python and C++.
## Motivation
Both in mathematics

$r = \sum_{i=a}^{b-1} 1$

as well as in programming 
```
for i in range(a, b):
    r += 1
```
it is sometimes necessary to compute a sum over a constant. A trained eye will see that these sums can be replaced with  $r = b - a$.

What happens with sums over the index itself?
```
for i in range(a, b):
    r += i
```
With a bit of mathematical finesse one can come with $r = (b^2 - b + a - a^2) / 2$.

What about $i^2$, $e^i$, ...? The complexity of the summand can of course be increased indefinitely but finding closed form formulas for mathematical sums isn't what this project aims to do.

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
Note that the upper border for `j` is  now the index `i` of the enclosing loop.

But we can go way further:
```
for i in range(a, b):
    for j in range(c, max(f, i)):
        if e < max(g, i):
            result += min(h, i) + j
```
And so on and so forth.

These (nested) loops have in common that they are the programmatic representation of mathematical sums. This project aims at finding closed form solutions to loops of this kind, that is, transforming them into code without any loops.
## How it works
The examples above (except the last one) consist of 3 types of expressions: for loops, if statements and summands. The goal is to eliminate all for loops. If we find universal transformation rules for these 3 types of expressions we can let a computer do the rest.
#### Transforming a for loop over an arithmetic expression
As mentioned above this project's goal isn't to reinvent the wheel. Instead, it uses [Sympy](https://www.sympy.org/en/index.html), a Python library for symbolic mathematics, to solve these problems.

[Sympy](https://www.sympy.org/en/index.html) can transform for loops over an arithmetic expression. What if there is an if statement inbetween though?
#### Merging an if statement into a for loop
```
for i in range(a, b):
    if c < i:
        r += i
```
In words: Sum all integers from $a$ (inclusive) to $b$ (exclusive) if they are greater than $c$.

Rephrased: Sum all integers which are $\ge a$, $\lt b$ and $\gt c$.

$\gt c$ can be transformed to $\ge c + 1$ because we are dealing with integers.

So we are looking at integers which are greater than or equal to both $a$ as well as $c + 1$ meaning they need to be $\ge max(a, c + 1)$. Therefor, the example becomes
```
for i in range(max(a, c + 1), b):
    r += i
```
That's a for loop over an arithmetic expression and as mentioned [before](#transforming-a-for-loop-over-an-arithmetic-expression) [Sympy](https://www.sympy.org/en/index.html) can do the rest of the work.

Using the formula for the [second example](#motivation) it can be done manually too:
```
r = (b**2 - b + max(a, c + 1) - max(a, c + 1)**2) / 2
```
#### What to do with min/max?
The last example contains calls to `min()` and `max()` and, as shown above, such terms are also the result of merging if statements into for loops.

Unfortunatelly, dealing with `min()` and `max()` isn't exactly straight forward. If you want to understand how it is done take a look at the code, specifically at the `eliminate_symbol_from_max_min()` methods and the `SympyMaxMinSplitter` class.
## Usage
Download [loop_to_constant.py](loop_to_constant.py). At the very end of the file you will find the variable `python_string`. Set it to your Python code (or try the provided example). Execute. The transformed Python code will be printed to the console. Output in C++ is supported as well: Just below `python_string` change `.dump_python()` to `.dump_cpp()`.

Just above `python_string` there are a few settings. Try manipulating them and see whether/how it affects the result.

Note that the provided examples increment variables (e.g. `r+=...`) which were never defined. That's intentional. The algorithm expects that and assumes these variables to have an initial value of 0.
#### Dependencies
- Python
- [Sympy](https://www.sympy.org/en/index.html)
## A real world example
Finding a closed from formula for loops is all well and good, but what do we actually need that for? The problem that led me to write this algorithm was something like this:

Imagine you have $n$ apples to give away and you have $5$ friends who are in need of apples. In what and in how many ways can you distribute your apples across your friends?
If $n = 0$, there is $p = 1$ possibility. Everyone gets 0 apples.
If $n = 1$, $p = 5$ because you can give your apple to friend $1$, $2$, $3$, $4$ or $5$. The others get 0 apples.
If $n = 2$, $p = 15$.

Let us complicate the problem a bit further by imposing a maximum and minimum number of apples per friend.

The function in [real_world_example.cpp](real_world_example.cpp) returns a `std::vector` of all possible apple distributions (not just the number of possibilities). Depending on the parameters there might be millions of possibilities resulting in millions of calls to `std::vector::push_back` resulting in many, many, many reallocations. Not millions, but still a lot. Reallocations are expensive.

The solution: Using this algorithm to calculate the number of possibilities first. Once you know this number you can reserve just as much memory as necessary resulting in just a single allocation and no reallocations. (Btw., no, a linked list wouldn't have solved the problem. A linked list doesn't require reallocations, yes, but it requires one small allocation per element which is way more expensive than just a single big allocation)

[real_world_example_solution.py](real_world_example_solution.py) contains the naive and the transformed implementation of a function that returns the number of possibilities.
## Performance
### Time complexity
The complexity of a simple for loop
```
for i in range(n):
    ...
```
is $\mathcal{O}(n)$.
For a nested for loop
```
for i in range(n_1):
    for j in range(n_2):
        ...
```
the complexity is $\mathcal{O}(n_1*n_2)$.

Generally speaking, the complexity of a m-fold for loop is $\mathcal{O}(n_1*...*n_m)$ which can written as $\mathcal{O}(n^m)$. If statements and `min()/max()` terms affect the value of $n$ but the exponent $m$ stays the same.

The transformed code doesn't contain any loops, only if and arithmetic statements. Therefor the transformed code is of $\mathcal{O}(1)$ complexity.
### Runtime
Trying to predict the performance gain isn't straight forward because of the different time complexities. Yes, the transformed code only consists of constant terms but potentially a lot of them.

Just to give you a feeling, the transformed code in [real_world_example_solution.py](real_world_example_solution.py) has 6000 lines (whereas the original code has 12).

Even if $n_1,...,n_4$ are all $0$ those lines will get executed every time the function is called. If the original code with 4 nested loops gets called with $n_1,...,n_4$ equal to $0$ only a single condition is executed which is obviously much faster.

On my machine for $n_1,...,n_4 \lt 4$ the original code is faster and for $n_1,...,n_4 \ge 4$ the transformed code is faster.

For $n_1,...,n_4 = 50$ the transformed code is already thousands of times faster.

Execute [real_world_example_solution.py](real_world_example_solution.py) to run these tests on your machine.
#### Roundup
For a very small number of iterations the normal code will be faster. For more than *a very small number of iterations* the transformed code will be orders of magnitude faster. The more iterations the greater the speed-up.
## Performance of the algorithm itself
It is slow. Very slow. E.g. [real_world_example_solution.py](real_world_example_solution.py) took more than 10 minutes to transform. I tried to optimize my code as much as possible (altough I don't know much about optimizing Python) but the main problem is [Sympy](https://www.sympy.org/en/index.html) which is written in pure Python. I did some research but I couldn't find any suitable symbolic math library written in a faster language. [Symengine](https://github.com/symengine/symengine) looks promising but doesn't provide the necessary features (handling of inequalities) yet.
## Downsides
- Slow in case of few iterations: As explained [here](#runtime).
- Maintainability: 6000 lines for a computation that can be done with 12? That's aweful. A transformed function should be always be accompanied by a comment containing an explanation and the original code.
- Transformation is very slow: As explained [here](#performance_of_the_algorithm_itself).




