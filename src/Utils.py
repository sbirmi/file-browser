import datetime
import subprocess

def now():
    return datetime.datetime.now()

def handle():
    if not hasattr(handle, "handle"):
        setattr(handle, "handle", open("trace.log", "a+"))
    return getattr(handle, "handle")

def trace(*msg):
    ts = now().strftime("%Y-%m-%d %H:%M:%S")
    print(ts, *msg)

    writeFn = handle().write
    writeFn(ts)
    for tok in msg:
        writeFn(" ")
        writeFn(str(tok))
    writeFn("\n")

def run(cmd):
    try:
        result = subprocess.call(cmd)
    except Exception as exc:
        return None
    return True

def check_output(cmd):
    try:
        return subprocess.check_output(cmd).decode("utf8")
    except:
        return None
