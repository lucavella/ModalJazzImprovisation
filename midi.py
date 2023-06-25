from midiutil import MIDIFile


def melody_to_midi(melody, bpm, out_file):
    midi = MIDIFile()
    midi.addTempo(0, 0, bpm)

    time = 0

    for note in melody:
        pitch = note.tone
        dur = note.duration.value
        if pitch != -1: # not a rest
            midi.addNote(0, 0, pitch, time, dur * 0.9, 100)

        time += dur

    with open(out_file, 'wb') as fh:
        midi.writeFile(fh)


if __name__ == '__main__':
    from generating import load_melody


    so_what_melody = load_melody('./data/improv/so_what.pickle')
    melody_to_midi(so_what_melody, 130, './data/survey/so_what.mid')

    little_sunflower_melody = load_melody('./data/improv/little_sunflower.pickle')
    melody_to_midi(little_sunflower_melody, 135, './data/survey/little_sunflower.mid')