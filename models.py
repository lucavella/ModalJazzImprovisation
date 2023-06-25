from enum import Enum
from fractions import Fraction
from functools import reduce
from notes import *


class NoteTone(Enum):
    CHORD = 1
    COLOR = 2
    HELPFUL = 3
    SCALE = 4
    ARBITRARY = 5
    REST = 6

    def from_pitch(pitch, chord, scale):
        if chord != 'NC': # no chord
            chord_offs, gen_chord = note_offset(chord)
            rel_chord_st = (pitch - chord_offs) % 12 # semitones above root chord note

            if rel_chord_st in chord_st(gen_chord):
                return NoteTone.CHORD
            elif rel_chord_st in color_st(gen_chord):
                return NoteTone.COLOR
            
        if scale != '':
            scale_offs, gen_scale = note_offset(scale)
            rel_scale_st = (pitch - scale_offs) % 12 # semitones above scale root note
            
            if rel_scale_st in scale_mode(gen_scale[1:]):
                return NoteTone.SCALE

        return NoteTone.ARBITRARY
    

# https://jazzomat.hfm-weimar.de/melospy/metrical_system.html

class NoteDuration(Enum):
    WHOLE = Fraction(4)
    HALF = Fraction(2)
    QUARTER = Fraction(1)
    EIGHTH = Fraction(1, 2)
    SIXTEENTH = Fraction(1, 4)
    THIRTYSECOND = Fraction(1, 8)

    def from_metric(duration, beatdur):
        rel_dur = duration / beatdur
        
        if rel_dur <= 1 / 16:
            return []
        elif rel_dur <= NoteDuration.THIRTYSECOND.value:
            return [NoteDuration.THIRTYSECOND]
        elif rel_dur <= NoteDuration.SIXTEENTH.value:
            return [NoteDuration.SIXTEENTH]
        elif rel_dur <= NoteDuration.EIGHTH.value:
            return [NoteDuration.EIGHTH]
        else:
            n_whole = rel_dur // 4
            n_half = (rel_dur - 4 * n_whole) // 2
            n_quarter = rel_dur - 4 * n_whole - 2 * n_half
            return [NoteDuration.WHOLE] * int(n_whole) + \
                   [NoteDuration.HALF] * int(n_half) + \
                   [NoteDuration.QUARTER] * int(n_quarter)
        
    def fill_beats(duration):
        durs = []
        for dur in NoteDuration:
            n_dur = duration // dur.value
            durs += [dur] * n_dur
            duration -= n_dur * dur.value

        return durs

    def get_rest(currnote, currdurs, nextnote):
        dur_beats = reduce(lambda acc, d: acc + d.value, currdurs, Fraction(0))
        bar_beats = (nextnote['bar'] - currnote['bar']) * currnote['period']
        beats = nextnote['beat'] - currnote['beat']
        tatums = Fraction(nextnote['tatum'], nextnote['division']) - \
                 Fraction(currnote['tatum'], currnote['division'])

        beats_diff = bar_beats + beats + tatums
        if beats_diff <= 0:
            raise ValueError('Notes in wrong order')
        rest_beats = beats_diff - dur_beats
        if rest_beats <= 0:
            return []
        
        return NoteDuration.fill_beats(rest_beats)
    

class Note:
    def __init__(self, tone, duration):
        self.tone = tone
        self.duration = duration

    def to_tuple(self):
        return (self.tone, self.duration)


class Phrase:
    def __init__(self, notes, is_first=False):
        self.notes = notes
        self.next = None
        self.is_first = is_first
        self.similar_next = []
        self.similar_next_end = []

    @property
    def length(self):
        n, d = reduce(lambda acc, n: acc + n.duration.value, self.notes, Fraction(0)).as_integer_ratio()
        return n / d

    def get_beat(self, idx):
        res_notes = []
        beat_c = 0
        filling = False

        for note in self.notes:
            if filling:
                if beat_c < idx + 1:
                    to_add_dur = min(note.duration.value, idx + 1 - beat_c)
                    durs = NoteDuration.fill_beats(to_add_dur)
                    res_notes += list(map(lambda d: Note(note.tone, d), durs))
                else:
                    return Phrase(res_notes)
                beat_c += note.duration.value
            else:
                beat_cn = beat_c + note.duration.value
                if beat_cn >= idx:
                    to_add_dur = min(beat_cn - idx, 1)
                    filling = True
                    durs = NoteDuration.fill_beats(to_add_dur)
                    res_notes += list(map(lambda d: Note(note.tone, d), durs))
                beat_c = beat_cn

        rest_to_add = min(idx + 1 - beat_c, 1)
        if rest_to_add > 0:
            durs = NoteDuration.fill_beats(rest_to_add)
            res_notes += list(map(lambda d: Note(NoteTone.REST, d), durs))

        return Phrase(res_notes)
    
    def get_tone_duration(self, tone):
        tone_f = filter(lambda n: n.tone == tone, self.notes)
        return Phrase(tone_f).length
    
    def to_list(self):
        return list(map(lambda n: n.to_tuple(), self.notes))


class PhraseSeqSimilar:
    def __init__(self):
        self.all = []
        self.start = []
        self.end = []

    def add_phrase(self, idx, phrase):
        self.all.append(phrase)
        if phrase.is_first:
            self.start.append(idx)
        if phrase.next == None:
            self.end.append(idx)

    def to_list(self):
        return list(map(lambda ph: ph.to_list(), self.all))