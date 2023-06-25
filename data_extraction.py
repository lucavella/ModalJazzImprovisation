import sqlite3
import contextlib


def dict_factory(c, row):
    return {
        key: val 
        for key, val in zip(
            [col[0] for col in c.description],
            row
    )}


def get_db_solos():
    with sqlite3.connect('data/wjazzd.db') as db:
        db.row_factory = dict_factory
        with contextlib.closing(db.cursor()) as c:
            solo_q = '''
            SELECT 
                si.melid AS mid,
                ci.form AS form,
                si.key AS key
            FROM composition_info AS ci
            INNER JOIN solo_info AS si
            ON ci.compid = si.compid
            WHERE
                ci.tonalitytype = 'MODAL' AND
                si.instrument IN ('ts', 'as', 'ss', 'tp')
            ORDER BY
                ci.compid ASC,
                si.melid ASC
            '''
            c.execute(solo_q)
            solos = c.fetchall()

            for solo in solos:
                phrases_q = f'''
                SELECT start, end
                FROM sections
                WHERE type = 'PHRASE' AND melid = {solo['mid']}
                ORDER BY value
                '''
                c.execute(phrases_q)
                phrases = c.fetchall()

                solo['phrases'] = []
                for phrase in phrases:
                    notes_q = f'''
                    SELECT
                        s.value AS chord,
                        m.pitch AS pitch,
                        m.duration AS duration,
                        m.beatdur AS beatdur,
                        m.period AS period,
                        m.division AS division,
                        m.bar AS bar,
                        m.beat AS beat,
                        m.tatum AS tatum
                    FROM melody AS m
                    LEFT JOIN (
                        SELECT MIN(eventid) AS meventid
                        FROM melody
                        WHERE melid = {solo['mid']}
                    )
                    INNER JOIN sections AS s
                    ON 
                        m.melid = s.melid AND
                        m.eventid - meventid >= s.start AND
                        m.eventid - meventid <= s.end
                    WHERE
                        m.melid = {solo['mid']} AND
                        m.eventid - meventid >= {phrase['start']} AND
                        m.eventid - meventid <= {phrase['end']} AND
                        s.type = 'CHORD'
                    ORDER BY
                        m.eventid ASC
                    '''
                    c.execute(notes_q)
                    solo['phrases'].append(c.fetchall())

            return solos