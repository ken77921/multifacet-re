import re

en = open('/Users/macpro/Documents/TAC/scripts/en-freebase_to_wiki_with_types.txt', "r")
es = open('/Users/macpro/Documents/TAC/scripts/es-freebase_to_wiki_with_types.txt', "r")
enes =  open('/Users/macpro/Documents/TAC/scripts/freebase_to_english_to_spanish.txt', "w")
names = open('/Users/macpro/Documents/TAC/scripts/FirstandLast', "r")
anchor = open('/Users/macpro/Documents/TAC/scripts/en-es-wiki.linktext.counts', "r")
listEN = dict()
listES = dict()
diff = dict()
countsame = 0
countdiff = 0
for line in en:
    if "people.person" in line:
        separated = line.split("\t")
        iD = separated[0]
        temp = separated[1][0:len(separated[1])-1].split("_")
        entity = " ".join(temp[2:len(temp)-1])
     #   entity = re.split("\s\((.+?)\)", entity)[0]
        listEN.update({iD:entity})
for line in es:
    if "people.person" in line:
        separated = line.split("\t")
        iD = separated[0]
        temp = separated[1][0:len(separated[1])-1].split("_")
        entity = " ".join(temp[2:len(temp)-1])
        #entity = re.split("\s\((.+?)\)", entity)[0]
        listES.update({iD:entity})
for key in listEN:
    if listES.has_key(key):
        if listES[key] == listEN[key]:
            countsame += 1
        else:
            diff.update({listEN[key]:listES[key]})
            countdiff += 1
            enes.write(key + "\t" + listEN[key] + "\t" + listES[key] + "\n")
print "Number of times iD has same entity between english and spanish " + str(countsame)
print "Number of times iD has different entity between english and spanish " + str(countdiff)

anc = dict()
for line in anchor:
    parts = line.split(" ", 2)
    if len(parts) < 3:
        parts.append(" ")
    anc.update({parts[2].strip():(parts[1].replace("_", " "), parts[0])})
cnt = 0
cnt1 = 0
eng = set(diff.keys())
esp = set(diff.values())
for line in names:
    line = line.strip()
    if line in anc:
      #  v = re.split("\s\((.+?)\)", anc[line][0])[0]
        if anc[line][0] in eng:
            cnt += 1
            print line
        if anc[line][0] in esp:
            cnt += 1
            print line
print "Number of overlapped freebase names in query set: " + str(cnt)

en.close()
es.close()
enes.close()
names.close()
anchor.close()
