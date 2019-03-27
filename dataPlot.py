#!/usr/bin/env python3
import matplotlib.pyplot as plt
import json
from matplotlib.widgets import TextBox
from webNameGen import *

ng = None

def formatCoord(x,y):
    return str(y)

def inputCB(text):
    global ng

    nGramToSearch = len(text)-1

    print("Searching for "+text+" in "+str(nGramToSearch))

    freqMapToDraw = ng.freqHolders[nGramToSearch].freqMap

    for i in range(len(text)):
        if text[i] not in freqMapToDraw:
            print("Warning, "+text[i]+" is not a valid key, frequency is 0 for this pattern "+text)
            return
        freqMapToDraw = freqMapToDraw[text[i]]

    print(json.dumps(freqMapToDraw,indent=4,sort_keys=True))

    fig = plt.figure()
    plt.bar(list(freqMapToDraw.keys()),list(freqMapToDraw.values()))
    fig.get_axes()[0].format_coord = formatCoord

    plt.show(block=False)

if __name__ == '__main__':
    # Load data
    ng = NameGen(10)
    ng.loadFromFile("data/frtown-10-0")

    # pyplot setup
    texBox = TextBox(plt.gca(),"Search:")
    texBox.on_submit(inputCB)

    plt.show()