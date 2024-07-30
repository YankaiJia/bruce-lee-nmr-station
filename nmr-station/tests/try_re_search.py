import re

message = "TubeId=01, SampleId=1"
ids = re.search(r'TubeId=(\d+), SampleId=(\d+)', message)

print(int(ids.group(1)), int(ids.group(2)))
print(re.search(r'a=(\d+), b=(\d+), c=(\d+)', "a=11, b=22, c=33").group(3))
print(re.search(r'a=(\d+), b=(\d+), c=(\d+)', "a=11, b=22, c=33").group(0))

"""
result:
1 1
33
a=11, b=22, c=33
"""