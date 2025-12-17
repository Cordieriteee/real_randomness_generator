import multiprocessing
import os
import time
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from scipy.stats import chi2_contingency
from scipy.stats import chisquare

def write_zero(shared_val, running):
    """write 0 to shared_val in a loop"""
    try:
        os.sched_setaffinity(0, {0}) 
    except:
        pass
        
    while running.value:
        shared_val.value = 0

def write_one(shared_val, running):
    """write 1 to shared_val in a loop"""
    try:
        os.sched_setaffinity(0, {1}) 
    except:
        pass
        
    while running.value:
        shared_val.value = 1

#read
def read_raw_data(shared_val, samples):
    raw_data = []

    # von Neumann extractor
    while len(raw_data) < samples:
        b1 = shared_val.value
        time.sleep(0.00002)
        b2 = shared_val.value
        
        if b1 == 0 and b2 == 1:
            raw_data.append(0)
        if b1 == 1 and b2 == 0:
            raw_data.append(1)  

    return raw_data
    

# distribution plot
def plot_result(raw_data):
    print("Plotting results...")
    matplotlib.use('Agg')

    plt.figure(figsize=(6, 4))
    plt.hist(raw_data, bins=[-0.5, 0.5, 1.5], rwidth=0.8, color='skyblue', edgecolor='black')
    plt.title('Histogram of 0 and 1 Counts')
    plt.xlabel('Value')
    plt.ylabel('Count')
    plt.xticks([0, 1])
    plt.grid(axis='y')
    plt.savefig('randomness_hist.png')
    print("Histogram saved as 'randomness_hist.png'")

# chi-squared test of independence
def check_independence_chi2(data):
    print("Performing Chi-squared test of independence...")
    
    # counting pairs (00, 01, 10, 11)
    count_00 = 0
    count_01 = 0
    count_10 = 0
    count_11 = 0
    
    for i in range(len(data) - 1):
        curr = data[i]
        next_val = data[i+1]
        
        if curr == 0 and next_val == 0: count_00 += 1
        elif curr == 0 and next_val == 1: count_01 += 1
        elif curr == 1 and next_val == 0: count_10 += 1
        elif curr == 1 and next_val == 1: count_11 += 1

    # create contingency table    
    obs = np.array([[count_00, count_01], 
                    [count_10, count_11]])
    
    print(f"Contingency Table:\n{obs}")

    # test of independence
    chi2, p_value, dof, expected = chi2_contingency(obs, correction=False)

    print(f"P-Value: {p_value:.4f}")
    alpha = 0.05
    if p_value < alpha:
        print(f"reject the null hypothesis (P < {alpha})")
        print("data may be dependent")

    else:
        print(f"fail to reject the null hypothesis (P > {alpha})")
        print("data is statistically independent!")


if __name__ == "__main__":
    shared_data = multiprocessing.Value('i', 0, lock=False)
    keep_running = multiprocessing.Value('b', True, lock=False)

    p1 = multiprocessing.Process(target=write_zero, args=(shared_data, keep_running))
    p2 = multiprocessing.Process(target=write_one, args=(shared_data, keep_running))
    
    p1.start()
    p2.start()

    try:
        raw_data = read_raw_data(shared_data, samples=10000)
        plot_result(raw_data)
        print(raw_data[:100])
        check_independence_chi2(raw_data)
        
    finally:
        keep_running.value = False
        p1.join()
        p2.join()
