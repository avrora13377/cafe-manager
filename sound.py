import winsound
import threading


def _beep(freq, duration):
    winsound.Beep(freq, duration)


def play_async(func, *args):
    t = threading.Thread(target=func, args=args, daemon=True)
    t.start()


# ---- Public sound effects ----

def order_placed():
    play_async(_order_placed_sync)


def status_changed():
    play_async(_status_changed_sync)


def item_added():
    play_async(_item_added_sync)


def error():
    play_async(_error_sync)


def cancel():
    play_async(_cancel_sync)


# ---- Sync implementations ----

def _order_placed_sync():
    _beep(800, 100)
    _beep(1000, 100)
    _beep(1200, 150)


def _status_changed_sync():
    _beep(880, 120)
    _beep(1100, 180)


def _item_added_sync():
    _beep(900, 80)
    _beep(1100, 80)


def _error_sync():
    _beep(200, 300)


def _cancel_sync():
    _beep(400, 150)
    _beep(300, 200)
