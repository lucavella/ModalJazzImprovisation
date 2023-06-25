from scipy import stats
import random
import pickle
from models import *


def sample_melody(phrases, beats, max_rest, phrase_mutation_prob):
    fallthrough_dist = stats.geom(1 - phrase_mutation_prob)

    ph_start_idx = random.choice(phrases.start)
    ph_start = phrases.all[ph_start_idx]

    ph_prev = ph_start
    melody = [ph_start]
    beats -= max_rest
    beats -= ph_start.length

    while beats > 0:
        ph_next_sim_idx = (fallthrough_dist.rvs() - 1) % len(ph_prev.similar_next)
        ph_next_idx = ph_prev.similar_next[ph_next_sim_idx]
        ph_next = phrases.all[ph_next_idx]
        
        ph_prev = ph_next
        melody.append(ph_next)

        beats -= ph_next.length

    melody.pop()
    ph_prev = melody[-1]
    ph_last_sim_idx = (fallthrough_dist.rvs() - 1) % len(ph_prev.similar_next_end)
    ph_last_idx = ph_prev.similar_next_end[ph_last_sim_idx]
    ph_last = phrases.all[ph_last_idx]
    melody.append(ph_last)
    
    rest_split = np.array(sorted([
        random.randrange(0, max_rest + 1, 1)
        for _ in melody
    ]))

    rest_split[1:] = rest_split[1:] - rest_split[:-1]

    melody_res = list(sum([
        (
            list(map(
                lambda d: Note(NoteTone.REST, d),
                NoteDuration.fill_beats(rest_dur)
            )),
            ph.notes
        )
        for ph, rest_dur in zip(melody, rest_split)
    ], ()))

    return [n for ns in melody_res for n in ns]


def select_pitch(tone, prev_tone, chord, scale, tone_mutation_prob, pitch_range, std):
    if tone == NoteTone.REST:
        return -1

    elif random.uniform(0, 1) <= tone_mutation_prob:
        match tone:
            case NoteTone.CHORD:
                tone = NoteTone.HELPFUL
            case NoteTone.COLOR:
                tone = NoteTone.HELPFUL
            case NoteTone.HELPFUL:
                tone = NoteTone.ARBITRARY
            case NoteTone.SCALE:
                tone = NoteTone.ARBITRARY
            case NoteTone.ARBITRARY:
                tone = NoteTone.HELPFUL

    stv = np.empty(0)
    if tone == NoteTone.CHORD:
        if chord != 'NC':
            chord_offs, gen_chord = note_offset(chord)
            stv = chord_st(gen_chord) + chord_offs
    elif tone == NoteTone.COLOR:
        if chord != 'NC':
            chord_offs, gen_chord = note_offset(chord)
            stv = color_st(gen_chord) + chord_offs
        if len(stv) == 0:
            stv = chord_st(gen_chord) + chord_offs
    elif tone == NoteTone.HELPFUL:
        if chord != 'NC':
            chord_offs, gen_chord = note_offset(chord)
            stv = helpful_st(gen_chord) + chord_offs
    elif tone == NoteTone.SCALE:
        if scale != '':
            scale_offs, gen_scale = note_offset(scale)
            stv = helpful_st(gen_scale) + scale_offs
    elif tone == NoteTone.ARBITRARY:
        if chord != 'NC':
            chord_offs, gen_chord = note_offset(chord)
            chord_stv = helpful_st(gen_chord) + chord_offs
        else:
            chord_stv = np.empty(0)

        if scale != '':
            scale_offs, gen_scale = note_offset(scale)
            scale_stv = helpful_st(gen_scale) + scale_offs
        else:
            scale_stv = np.empty(0)

        stv = np.setdiff1d(
            np.arange(0, 12),
            np.union1d(chord_stv, scale_stv)
        )
    if len(stv) == 0:
        stv = np.arange(0, 12)


    prev_pitch = prev_tone
    next_pitch = stats.norm(prev_pitch, std).rvs()
    next_octave = next_pitch // 12

    min_pitch, max_pitch = pitch_range
    stv_padded = np.append(stv, (stv[-1] - 12, stv[0] + 12))
    stv_allowed = []
    for st in stv_padded:
        nst = st + next_octave * 12
        if nst > max_pitch:
            rm_octave = (nst - max_pitch) // 12 + 1
            nst -= rm_octave * 12
        elif nst < min_pitch:
            add_octave = (min_pitch - nst) // 12 + 1
            nst += add_octave * 12

        stv_allowed.append(nst)
        
    next_pitch = sorted(stv_allowed, key=lambda st: np.abs(next_pitch - st))[0]

    return int(next_pitch)


def select_notes(abs_melody, chords, scale, init_pitch, tone_mutation_prob, pitch_range, std):
    melody = []
    chord, dur = chords.pop(0)
    prev_pitch = init_pitch

    for note in abs_melody:
        pitch = select_pitch(note.tone, prev_pitch, chord, scale, tone_mutation_prob, pitch_range, std)
        prev_pitch = pitch
        melody.append(Note(pitch, note.duration))

        dur -= note.duration.value
        if dur <= 0:
            try:
                chord, next_dur = chords.pop(0)
                dur = next_dur + dur
            except IndexError:
                dur = np.inf

    return melody


def improvise_melody(phrases, chords, scale, out_file=None, phrase_mutation_prob=0.5, init_pitch=75, tone_mutation_prob=0.05, pitch_range=(54, 86), std=5):
    beats = reduce(lambda acc, c: acc + c[1], chords, 0)
    max_rest = beats // 10

    while True:
        abs_melody = sample_melody(phrases, beats, max_rest, phrase_mutation_prob)
        dur = Phrase(abs_melody).length
        if dur <= beats + 5 and dur >= beats - 5:
            break
        
    melody = select_notes(abs_melody, chords, scale, init_pitch, tone_mutation_prob, pitch_range, std)

    if out_file:
        with open(out_file, 'wb') as fh:
            pickle.dump(melody, fh)

    return melody


def load_melody(in_file):
    with open(in_file, 'rb') as fh:
        return pickle.load(fh)
    

if __name__ == '__main__':
    from learning import load_phrases


    phrases = load_phrases('./data/modal_phrases_all.pickle')

    so_what_chords = [('Dm7', 16 * 4), ('Ebm7', 8 * 4), ('Dm7', 8 * 4)]
    so_what_scale = 'D-maj'
    improvise_melody(
        phrases,
        so_what_chords,
        so_what_scale,
        out_file='./data/improv/so_what.pickle'
    )

    little_sunflower_chords = [('Dm7', 16 * 4), ('Ebj7', 4 * 4), ('Dj7', 4 * 4), ('Ebj7', 4 * 4), ('Dj7', 4 * 4), ('Dm7', 4 * 4)]
    little_sunflower_scale = 'D-maj'
    improvise_melody(
        phrases,
        little_sunflower_chords,
        little_sunflower_scale,
        out_file='./data/improv/little_sunflower.pickle'
    )