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
Still to simple?
```
for x in range(a, b):
    for y in range(c, d):
        result += x + y
```
## Performance
### Time complexity
### Runtime
## Performance of the algorithm itself
