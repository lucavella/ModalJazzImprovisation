import numpy as np


def note_offset(note):
    match note[0]:
        case 'C':
            offset = 0
        case 'D':
            offset = 2
        case 'E':
            offset = 4
        case 'F':
            offset = 5
        case 'G':
            offset = 7
        case 'A':
            offset = 9
        case 'B':
            offset = 11
    
    if len(note) > 1 and note[1] == 'b':
        return (offset - 1, note[2:])
    elif len(note) > 1 and note[1] == '#':
        return (offset + 1, note[2:])
    else:
        return (offset, note[1:])
    

# https://jazzomat.hfm-weimar.de/melospy/annotations.html#chords

def chord_st(chord):
    stv = np.array([0, 4, 7]) # 1 M3 P5

    if len(chord) >= 1:
        if chord[0] == 'm' or chord[0] == '-':
            stv[1] -= 1 # m3
        elif chord[0] == '+':
            stv[2] += 1 # A5
        elif chord[0] == 'o':
            stv[1] -= 1 # m3
            stv[2] -= 1 # d5
        elif chord.startswith('sus'):
            stv[1] += 1 # P4

    if 'j7' in chord:
        stv = np.append(stv, 11) # M7
    elif '7' in chord:
        stv = np.append(stv, 10) # m7

    return stv


def color_st(chord):
    stv = np.empty(0)

    if '6' in chord:
        stv = np.append(stv, 9) # M6

    if '9#' in chord:
        stv = np.append(stv, 3) # A9
    elif '9b' in chord:
        stv = np.append(stv, 1) # m9
    elif '9' in chord:
        stv = np.append(stv, 2) # M9


    if '11#' in chord:
        stv = np.append(stv, 6) # A11
    elif '11' in chord:
        stv = np.append(stv, 5) # P11

    return stv


def helpful_st(chord):
    chord_stv = chord_st(chord)
    color_stv = color_st(chord)

    return np.union1d(chord_stv, color_stv)


def scale_mode(key):
    match key:
        case 'maj':
            return np.array([0, 2, 4, 5, 7, 9, 11])
        case 'min':
            return np.array([0, 2, 3, 5, 7, 8, 10])
        case 'ion':
            return np.array([0, 2, 4, 5, 7, 9, 11])
        case 'dor':
            return np.array([0, 2, 3, 5, 7, 9, 10])
        case 'phr':
            return np.array([0, 1, 3, 5, 7, 8, 10])
        case 'lyd':
            return np.array([0, 2, 4, 6, 7, 9, 11])
        case 'mix':
            return np.array([0, 2, 4, 5, 7, 9, 10])
        case 'aeol':
            return np.array([0, 2, 3, 5, 7, 8, 10])
        case 'lok':
            return np.array([0, 1, 3, 5, 6, 8, 10])
        case 'chrom':
            return np.arange(0, 12, 1)
        case _:
            return np.empty(0)