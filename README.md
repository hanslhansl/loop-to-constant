# loop-to-constant
This project implements an algorithm which optimizes certain for-loops by transforming them into equivalent code of constant time complexity. This allows for speed-ups of several orders of magnitude.
Currently, it can parse Python code and output the transformed code in Python and C++.

## Development with uv
This project is configured for uv-based dependency and environment management.

### Install from Git
```bash
python -m pip install "git+https://github.com/hanslhansl/loop-to-constant.git"
```

### Setup with uv
```bash
uv sync
```

## Motivation
Both in mathematics

$r = \sum_{i=a}^{b-1} 1$

as well as in programming 
```Python
for i in range(a, b):
    r += 1
```
it is sometimes necessary to compute a sum over a constant. A trained eye will see that these sums can be replaced with  $r = b - a$.

What happens with sums over the index itself?
```Python
for i in range(a, b):
    r += i
```
With a bit of mathematical finesse one can come up with $r = (b^2 - b + a - a^2) / 2$.

What about $i^2$, $e^i$, ...? The complexity of the summand can of course be increased indefinitely but finding closed form formulas for mathematical sums isn't what this project aims to do.

Instead, consider another "type" of complexity:
```Python
for i in range(a, b):
    if c < i:
        r += x
```
A bit more complex:
```Python
for i in range(a, b):
    for j in range(c, d):
        r += i + j
```
Even more complex:
```Python
for i in range(a, b):
    for j in range(c, i): # <- note: the upper border for j is  now the index i of the enclosing loop
        r += j
```
Way more complex:
```Python
for i in range(a, b):
    for j in range(c, max(f, i)):
        if e < max(g, i):
            result += min(h, i) + j
```
And so on and so forth.

These (nested) loops have in common that they are the programmatic representation of mathematical sums extended with some basic control structures (and `min()`/`max()`). This algorithm finds closed form solutions to loops of this kind, i.e. transforms them into code without any loops.
## How it works
The examples above (except the last one) consist of 3 types of expressions: for-loops, if-statements and summands. The goal is to eliminate all for-loops. It is therefor necessary to find universal transformation rules:
#### Transforming a for-loop over an arithmetic expression
As mentioned above this project's goal isn't to reinvent the wheel. Instead, it uses [Sympy](https://www.sympy.org/en/index.html), a Python library for symbolic mathematics, to transform for-loops over an arithmetic expression.
#### Merging an if-statement into a for-loop
```Python
for i in range(a, b):
    if c < i:
        r += i
```
In words: Sum all integers from `a` (inclusive) to `b` (exclusive) if they are greater than `c`.

Rephrased: Sum all integers which are `>= a`, `< b` and `> c`.

`> c` can be transformed to `>= c + 1` because all values are integers, therefor the integers must be both `>= a` as well as `>= c + 1` meaning they need to be `>= max(a, c + 1)`. The example becomes
```Python
for i in range(max(a, c + 1), b):
    r += i
```
That's a for-loop over an arithmetic expression and as mentioned before Sympy can handle this.

Using the general formula provided for the secondmotivating example it can be transformed manually too:
```Python
r = (b**2 - b + max(a, c + 1) - max(a, c + 1)**2) / 2
```
#### What to do with min/max?
The last motivating example contains calls to `min()` and `max()` and, as shown above, such terms are also the result of merging if statements into for-loops.

Unfortunatelly, dealing with `min()` and `max()` isn't exactly straight forward. A closer look at the code reveals how this is achieved, particularly through the `eliminate_symbol_from_max_min()` methods and the `SympyMaxMinSplitter` class.

## Installation
```bash
python -m pip install "git+https://github.com/hanslhansl/loop-to-constant.git"
```

## Usage
See [examples/example1.py](examples/example1.py) and [examples/example2.py](examples/example2.py) for examples.

The module offers a few settings defined at the top of the `__init__.py` file. Changing them might affect both the result as well as execution time.

Note: The provided examples increment variables (e.g. `r += ...`) which were never defined. That is intentional. The algorithm expects that and assumes these variables to have an initial value of 0.

## A real world example
Finding a closed form formula for loops is all well and good, but what is it actually needed for? The problem that led to the development of this algorithm went something like this:

Imagine you have $n$ apples to give away and you have $5$ friends who are in need of apples. In what and in how many ways can you distribute your apples across your friends?
If $n = 0$, there is $p = 1$ possibility. Everyone gets 0 apples.
If $n = 1$, $p = 5$ because you can give your apple to friend $1$, $2$, $3$, $4$ or $5$. The others get 0 apples.
If $n = 2$, $p = 15$, and so on and so forth.

The problem is complicated by imposing a maximum and minimum number of apples per friend.

The function in [examples/example1_original_function.cpp](examples/example1_original_function.cpp) returns a `std::vector` of all possible apple distributions (not just the number of possibilities). Depending on the parameters there might be millions of possibilities resulting in millions of calls to `std::vector::push_back` resulting in many, many, many reallocations. Not millions, but still a lot. Reallocations are expensive.

The solution: Using this algorithm to calculate the number of possibilities first. Once this number is known a single call to `std::vector::reserve` reserves just as much memory as needed resulting in just a single allocation and no reallocations. (By the way, no, a linked list wouldn't have solved the problem. A linked list doesn't require reallocations, yes, but it requires one small allocation per element which is way more expensive than just a single big allocation)

[examples/example1_naive.py](examples/example1_naive.py) and [examples/example1_transformed.py](examples/example1_transformed.py) contain the naive and transformed implementation of a function that returns the number of possibilities in Python.
## Performance
### Time complexity
The complexity of a simple for-loop
```Python
for i in range(n):
    ...
```
is $\mathcal{O}(n)$.
The complexity of a nested for-loop
```Python
for i in range(n_1):
    for j in range(n_2):
        ...
```
is $\mathcal{O}(n_1⋅n_2)$.

Generally speaking, the complexity of an m-fold for-loop is $\mathcal{O}(n_1⋅...⋅n_m)$ which can be written as $\mathcal{O}(n^m)$. If-statements and `min()`/`max()` terms affect the value of $n$ but the exponent $m$ stays the same.

The transformed code doesn't contain any loops, only if-statements and arithmetic statements. Therefor the transformed code is of $\mathcal{O}(1)$ complexity.
### Runtime
Trying to predict the performance gain isn't straight forward because of the different time complexities. Yes, the transformed code only consists of constant terms but potentially a lot of them.

The example provided under [A real world example](#a-real-world-example) is an extreme case: The transformed code has 6000 lines whereas the original code has only 14. Even if $n = 0$ those 6000 lines will get executed every time the function is called. If the original code with 4 nested loops gets called with $n = 0$ only a single condition is executed which is obviously much faster. On my machine for $n \lt 3$ the original code is faster and for $n \ge 3$ the transformed code is faster. For $n = 50$ the transformed code is already thousands of times faster.

Executing [examples/example1_plot.py](examples/example1_plot.py) runs these tests and plots the results.
### TL;DR
For a very small number of iterations the normal code will be faster. For more than *a very small number of iterations* the transformed code will be orders of magnitude faster. The more iterations the greater the speed-up.
## Performance of the algorithm itself
It is slow. Very slow. The [real world example](#a-real-world-example) takes more than 10 minutes to transform. The main problem is Sympy which is written in pure Python and there doesn't seem to be a faster symbolic math library. [Symengine](https://github.com/symengine/symengine) looks promising but doesn't provide the necessary features (handling of inequalities) yet.
## Downsides
- Slow in case of few iterations. Explained under [Runtime](#runtime).
- Maintainability: 6000 lines for a computation that can be done with 14? That's aweful. A transformed function should probably be accompanied by a comment containing an explanation and the original code.
- Transformation is very slow. Explained under [Performance of the algorithm itself](#performance-of-the-algorithm-itself).
- The transformed code operates on floats instead of integers because certain transformations require divisions. In theory, it should be possible to solve this issue but that hasn't happened just yet.
