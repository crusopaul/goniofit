#!/usr/bin/env python3
# coding: utf-8

# Import sys for argument handling
import sys
# Import xml handling
import xml.etree.ElementTree as ET
# Import MathPlotLib for plotting
import matplotlib.pyplot as plt
# Import scipy for curve fitting
from scipy.optimize import curve_fit
# Import numpy for large sets of data, gaussian, and RMSE
import numpy as np

# Assuming valid arguments, get filename and set it up for reading
file = sys.argv[1]
file = ET.parse(file).getroot()

# Populate Intensities from xrdml
y = file.find('{http://www.xrdml.com/XRDMeasurement/1.5}xrdMeasurement').find('{http://www.xrdml.com/XRDMeasurement/1.5}scan').find('{http://www.xrdml.com/XRDMeasurement/1.5}dataPoints').find('{http://www.xrdml.com/XRDMeasurement/1.5}intensities').text.split(' ')

# Get data size
dataSize = len(y)

# Get step size from start and end positions
startPos = float(file.find('{http://www.xrdml.com/XRDMeasurement/1.5}xrdMeasurement').find('{http://www.xrdml.com/XRDMeasurement/1.5}scan').find('{http://www.xrdml.com/XRDMeasurement/1.5}dataPoints').findall('{http://www.xrdml.com/XRDMeasurement/1.5}positions')[0][0].text)
endPos = float(file.find('{http://www.xrdml.com/XRDMeasurement/1.5}xrdMeasurement').find('{http://www.xrdml.com/XRDMeasurement/1.5}scan').find('{http://www.xrdml.com/XRDMeasurement/1.5}dataPoints').findall('{http://www.xrdml.com/XRDMeasurement/1.5}positions')[0][1].text)
stepSize = (endPos - startPos)/dataSize

# Find 2theta from xrdml
x = []
for i in np.arange(0, dataSize):
    x.append(startPos + i*stepSize)

# Now let's define N-point smoothing
def smooth(x, y, N):
    ret = []
    nWid = int((N - 1)/2)
    for i in np.arange(nWid, len(x) - nWid):
        sum = 0
        for j in np.arange(i - nWid, i + nWid + 1):
            sum += float(y[j])
        ret.append([x[i], sum/N])
    return ret

# Now let's use user input to determine new smoothed dataset
flag = False
while not flag:
    N = 0
    while int(N) % 2 == 0:
        N = int(input("How many points would you like to smooth over? Entry must be odd (1, 3, 5, 7, ...) "))
    # Lists for smooth return
    sx = []
    sy = []
    temp = smooth(x, y, N)
    for i in np.arange(0, len(temp)):
        sx.append(temp[i][0])
        sy.append(temp[i][1])
    del temp
    
    # Check to see if the data is sufficently smooth
    print("Data is about to be plotted. Please check to see if it is sufficiently smooth.")
    fig1 = plt.subplot(121)
    fig1.plot(x, y)
    fig2 = plt.subplot(122)
    fig2.plot(sx, sy)
    plt.show()
    while flag not in ["y", "n"]:
        flag = input("Was data sufficiently smooth? (y or n) ")
    if flag == "y":
        flag = True
    else:
        flag = False

# Let's free up our old x and y
x = sx
y = sy
del sx, sy

# Now to do some fitting...
# First, let's define our Gaussian
def f(x, a, c, w, b):
    return a*np.exp(-(((x - c)/w)**2)/2) + b

# Input checking while loop
flag = False
while not flag:
    # Let's get an initial guess
    print("Now, before you try to make an initial guess, a plot of the smoothed data is going to be displayed. Try to accurately estimate the amplitude, center, width, and height of the peak you're trying to fit then type each value delimited by newlines. Also enter the range of data that you'd like to fit. Specific x and y values can be seen by hovering the mouse over the graph. After typing the values, close the plot to see the generated fit.")
    
    # Plot the data again
    plt.plot(x, y)
    plt.show()
    a = float(input())
    c = float(input())
    w = float(input())
    b = float(input())
    # Fit limits
    low = float(input())
    high = float(input())
    
    # Find index values of range
    i = 0
    it = 0
    while low > x[i]:
        it = i
        i += 1
    low = it
    i = len(x) - 1
    it = 0
    while high < x[i]:
        it = i
        i -= 1
    high = it
    del i, it

    # Now to fit
    print("Fit is about to be plotted, please check to see if it is the desired fit.")
    p = np.array([a, c, w, b])
    p, covar = curve_fit(f, x[low:high + 1], y[low:high + 1], p)
    plt.plot(x, y, x, f(x, p[0], p[1], p[2], p[3]))
    plt.show()
    while flag not in ['y', 'n']:
        flag = input("Is this your fit? (y or n) ")
    if flag == 'y':
        flag = True
    else:
        flag = False

# Let's get the RMSE for the fit
def rmse(y, f, low, high):
    ret = 0
    for i in np.arange(low, high + 1):
        ret += (f[i] - y[i])**2
    return np.sqrt(ret/(high + 1 - low))

# Print fit parameters and RMSE
print('{:^44}'.format('Fit Parameters'))
print('{:^14} {:^30}'.format('RMSE', rmse(y, f(x, p[0], p[1], p[2], p[3]), low, high)))
print('{:^14} {:^30}'.format('Amplitude', p[0]))
print('{:^14} {:^30}'.format('Center', p[1]))
print('{:^14} {:^30}'.format('Std. Dev.', p[2]))
print('{:^14} {:^30}'.format('Height', p[3]))
print('{:^14} {:^30}'.format('Lower Range', x[low]))
print('{:^14} {:^30}'.format('Upper Range', x[high]))

# Let's prepare for proper graphing
print("\nA plot of the data is going to be displayed, please note the upper limit of the range that you'd like to include in a final plot.")
plt.plot(x, y, x, f(x, p[0], p[1], p[2], p[3]))
plt.show()
top = float(input("What is the upper limit for your range? "))

# Make a proper graph for use elsewhere
plt.plot(x, y, x, f(x, p[0], p[1], p[2], p[3]))
plt.legend((str(N) + "-Point Smoothed Data", "Curve Fit"))
plt.ylabel('Counts')
plt.xlabel('2-Theta')
plt.axis([x[0], x[len(x) - 1], 0, top])
plt.show()
