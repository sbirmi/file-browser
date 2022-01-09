import datetime

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

