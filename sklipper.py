import sys
import cv2
import sqlite3
import argparse
import math

# TODO document
# TODO fix spacing/indentation
# TODO put on github?
# TODO save clips as new video file


def init_db():
    db = sqlite3.connect("sklipper.db")
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    #cursor.execute("DROP TABLE clips")
    cursor.execute('''CREATE TABLE IF NOT EXISTS
            clips (event integer, start integer, end integer)''')
    db.commit()
    return db


def play_clips(db, video, clips):
    for clip in clips:
        video.set(cv2.CAP_PROP_POS_FRAMES, clip["start"])
        while video.get(cv2.CAP_PROP_POS_FRAMES) < clip["end"]:
            ret, frame = video.read()
            if frame is None:
                break
            cv2.imshow('sklipper', frame)
            key = cv2.waitKey(1) & 0xFF
            if process_keypress(db, video, key) is False:
                break
    return


def play_video(db, video, event):
    if event:
        cursor = db.cursor()
        clips = cursor.execute("SELECT * FROM clips where event = ?",
                [event])
    else:
        clips = [{"start":0, "end":video.get(cv2.CAP_PROP_FRAME_COUNT)}]
    play_clips(db, video, clips)


def save_event_clip(db, video, event):
    position = video.get(cv2.CAP_PROP_POS_FRAMES)
    fps = video.get(cv2.CAP_PROP_FPS)
    cursor = db.cursor()
    # TODO adjust start and end based on event type
    start = math.floor(position - (2 * fps))
    if start < 0:
        start = 0
    end = math.floor(position + (5 * fps))
    cursor.execute('''INSERT INTO clips (event, start, end)
            VALUES (?, ?, ?)''', [event, start, end])
    db.commit()


def process_keypress(db, video, key):
    if key == ord('q'):
        return False
    elif key >= ord('1') and key <= ord('9'):
        print key - 48
        save_event_clip(db, video, key - 48)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("--event", type=int,
            help="play only events of this type")
    args = parser.parse_args()

    db = init_db()

    video = cv2.VideoCapture(args.filename)

    if not video.isOpened():
        print "failed to open video"
        sys.exit(1)
    
    play_video(db, video, args.event)

    # dump the database to stdout for debugging
    cursor1 = db.cursor()
    for row in cursor1.execute("SELECT * FROM clips"):
        print row

    video.release()
    cv2.destroyAllWindows()

# vim: set ts=4 sw=4 hlsearch expandtab :
