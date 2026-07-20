import time, numpy as np, matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor

import example1_naive
import example1_transformed


def measure(f, *x, target_time=0.2):
    repeats = 1

    while True:
        start = time.perf_counter()
        for _ in range(repeats):
            f(*x)
        elapsed = time.perf_counter() - start

        if elapsed >= target_time:
            return elapsed / repeats

        repeats *= 2

def measure_naive(args):
    return measure(example1_naive.naive, *args)
def measure_transformed(args):
    return measure(example1_transformed.transformed, *args)

if __name__ == '__main__':
    # Create integer n values from 0 to ...
    n = list(range(0, 101))
    args = [(i * 4, 0, 0, 0, 0, 0, 99) for i in n]

    # Calculate y values for each function
    with ProcessPoolExecutor() as executor:
        t_naive = np.array(list(executor.map(measure_naive, args)))

    t_transformed = np.array([measure_transformed(arg) for arg in args])
    transformed_mean = np.mean(t_transformed)
    transformed_mean = [transformed_mean for _ in n]

    # Plot the functions
    plt.plot(n, t_naive, label=f'naive, total={np.sum(t_naive)}s')
    plt.plot(n, t_transformed, label=f'transformed, total={np.sum(t_transformed)}s')
    plt.plot(n, transformed_mean, label=f'transformed mean={transformed_mean}')

    # Add a legend
    plt.legend()

    # Add grid, title, and labels
    plt.grid(True)
    plt.title('Plot of naive and transformed runtime')
    plt.xlabel('n')
    plt.ylabel('t [s]')

    # Show the plot
    plt.show()