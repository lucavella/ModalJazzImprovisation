import random
import pickle
import multiprocessing as mp
from models import *


def preprocess(solos):
    phrases = PhraseSeqSimilar()
    ph_idx = 0

    for solo in solos:
        ph = Phrase([], is_first=True)
        for phrase in solo['phrases']:
            for i, curr in enumerate(phrase):
                tone = NoteTone.from_pitch(curr['pitch'], curr['chord'], solo['key'])
                durs = NoteDuration.from_metric(curr['duration'], curr['beatdur'])

                for dur in durs:
                    ph.notes.append(Note(tone, dur))

                if i < len(phrase) - 1:
                    next = phrase[i + 1]
                    rests = NoteDuration.get_rest(curr, durs, next)

                    for dur in rests:
                        ph.notes.append(Note(NoteTone.REST, dur))

            ph.next = ph_idx + 1
            phrases.add_phrase(ph_idx, ph)
            ph = Phrase([])
            ph_idx += 1

        last_ph = phrases.all[-1]
        last_ph.next = -1
        phrases.end.append(ph_idx - 1)

    return phrases


# difference between phrases heuristic
def phrase_diff(phrase1, phrase2):
    discount = 0.8
    weight = 1

    diff = 0
    max_len = np.ceil(max(phrase2.length, phrase1.length))
    
    for i in range(int(max_len)):
        phrase1_b = phrase1.get_beat(i)
        phrase2_b = phrase2.get_beat(i)
        phrase1_bn = phrase1_b.length # actual lengths
        phrase2_bn = phrase2_b.length

        p1_cn = phrase1_b.get_tone_duration(NoteTone.CHORD) / phrase1_bn
        p2_cn = phrase2_b.get_tone_duration(NoteTone.CHORD) / phrase2_bn
        p1_ln = phrase1_b.get_tone_duration(NoteTone.COLOR) / phrase1_bn
        p2_ln = phrase2_b.get_tone_duration(NoteTone.COLOR) / phrase2_bn
        p1_sn = phrase1_b.get_tone_duration(NoteTone.SCALE) / phrase1_bn
        p2_sn = phrase2_b.get_tone_duration(NoteTone.SCALE) / phrase2_bn
        p1_an = phrase1_b.get_tone_duration(NoteTone.ARBITRARY) / phrase1_bn
        p2_an = phrase2_b.get_tone_duration(NoteTone.ARBITRARY) / phrase2_bn
        p1_rn = phrase1_b.get_tone_duration(NoteTone.REST) / phrase1_bn
        p2_rn = phrase2_b.get_tone_duration(NoteTone.REST) / phrase2_bn

        diff += weight * np.abs(p2_cn - p1_cn) / 2
        diff += weight * np.abs(p2_ln - p1_ln) / 2
        diff += weight * np.abs(p2_cn + p2_ln - p1_cn - p1_ln) / 2
        diff += weight * np.abs(p2_sn - p1_sn)
        diff += weight * np.abs(p2_an - p1_an)
        diff += weight * np.abs(p2_rn - p1_rn)

        weight *= discount

    return diff


def get_similar_next(phrase_idx, phrases, limit=None):
    ph_next_n = phrases.all[phrase_idx].next
    if ph_next_n == -1:
        return ([], [])

    ph_next = phrases.all[ph_next_n]
    all_ph_s = list(filter(lambda ph_n: phrases.all[ph_n].next != -1, range(len(phrases.all))))
    end_ph_s = range(len(phrases.end))

    if not limit:
        all_k = len(all_ph_s)
        end_k = len(end_ph_s)
    else:
        all_k = min(len(all_ph_s), limit)
        end_k = min(len(end_ph_s), limit)

    if ph_next.next == -1:
        all_ph_s = random.sample(all_ph_s, k=all_k)

        end_f = list(filter(lambda ph_n: ph_n != ph_next_n, end_ph_s))
        end_ph_s = random.sample(end_f, k=end_k - 1)
        end_ph_s.append(ph_next_n)
    else:
        all_f = list(filter(lambda ph_n: ph_n != ph_next_n, all_ph_s))
        all_ph_s = random.sample(all_f, k=all_k - 1)
        all_ph_s.append(ph_next_n)
        
        end_ph_s = random.sample(end_ph_s, k=end_k)

    ph_key = lambda ph_n: phrase_diff(phrases.all[ph_n], ph_next)

    return (
        sorted(all_ph_s, key=ph_key),
        sorted(end_ph_s, key=ph_key)
    )


def get_similar_next_batch(phrase_n_batch, phrases, limit=None):
    return {
        ph_idx: get_similar_next(ph_idx, phrases, limit)
        for ph_idx in phrase_n_batch
    }


def learn_phrases(solos, out_file=None, max_workers=10, limit_similar=None):
    phrases = preprocess(solos)

    next_results = {}
    def store_results(res):
        next_results.update(res)

    phrases_n = range(len(phrases.all))
    with mp.Pool(processes=max_workers) as pool:
        results = [
            pool.apply_async(
                get_similar_next_batch,
                args=(phrase_batch, phrases, limit_similar),
                callback=store_results,
                error_callback=print
            )
            for phrase_batch in np.array_split(phrases_n, max_workers)
        ]

        for r in results:
            r.wait()

    for ph_idx, (ph_next, ph_next_end) in next_results.items():
        phrase = phrases.all[ph_idx]
        phrase.similar_next = ph_next
        phrase.similar_next_end = ph_next_end

    if out_file:
        with open(out_file, 'wb') as fh:
            pickle.dump(phrases, fh)

    return phrases


def load_phrases(in_file):
    with open(in_file, 'rb') as fh:
        return pickle.load(fh)
    

if __name__ == '__main__':
    from data_extraction import get_db_solos


    solos = get_db_solos()
    learn_phrases(
        solos,
        out_file='./data/modal_phrases_all.pickle',
        max_workers=mp.cpu_count()
    )