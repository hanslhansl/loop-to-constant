import loop_to_constant as ltc

python_string = """
for x in range(a + 1, b + 1):
    if c < x:
        r += 2
    if c < x:
        r += x + 1
        r2 += 2 + x
        r += 3*x + 7
        if c < y:
            k = y * 7
            r += max(k, x + 1)
            r += k
            for z in range(q + 1, max(500, x + 1)):
                r += 5
    else:
        r2 += x * 10
        r += x * 2
"""
    
cse = ltc.Python.parse(python_string).resolve().cse()
print(f"equivalent python code:\n\n{cse.dump_python()}")
# print(f"equivalent c++ code:\n\n{cse.dump_cpp()}")