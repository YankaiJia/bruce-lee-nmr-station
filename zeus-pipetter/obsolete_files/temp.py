import pprint
import pickle

with open('multicomponent_reaction\\event_list_chem.pickle', 'rb') as f:
    new = pickle.load(f)

for i in range(805, 810):
    print(new[i].is_event_conducted, new[i].event_label)
    print(new[i].event_finish_time, new[i].event_finish_time_datetime)

pprint.pprint(new[809])
aa = new[809]
bb = new[810]

print(aa.__dict__)