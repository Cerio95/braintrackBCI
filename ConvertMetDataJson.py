# expectedformat: 
    # Metrics:.... next line will contain the decription of the experiment
    # reading begins: contains the date of the experiment
    # data, #,#,#.... metrics.

import re
import json

rwPath = '' #file path
# the next three variables compose the file name, the expected format is:
# 'MetData filename ###.txt
rFileName = 'MetData ' 
expName = "" 
expNr = 0
#ID degli utenti, molto sbatti leggerlo altrimenti
UserIDs = ["M28","F44","F25","M23","F24","F20","F23","M21","M22","M25","M28","F28","M29","M26","M22","F26","M26","M27","F27","F60","M28","M30"]
emotivToJson = {} #inizializzo  libreria

#leggo tutti i file, da 0 a 21
for expNr in range(22):
    file = open(rwPath+'\\'+ rFileName + str(expNr).zfill(3) + ".txt","r") 

    lineNr = 0 #line counter

    emotivToJson[str(expNr).zfill(3)] ={
                "UserID": UserIDs[expNr],
                "Readings": {}
                }

    for line in file:
        if re.match("[0-9][0-9]:[0-9][0-9]:[0-9][0-9]+", line):
                splitValues = line.split(',')
                emotivToJson[str(expNr).zfill(3)]["Readings"][str(lineNr).zfill(6)] = {
                        "Phase": expName,
                        "Time": splitValues[0][0:len(splitValues[0])-1],
                        "Engagement": splitValues[1],
                        "Excitement": splitValues[2],
                        "Stress": splitValues[4],
                        "Relaxation": splitValues[5],
                        "Interest": splitValues[6],
                        "Focus": splitValues[7][0:len(splitValues[7])-1]
                    }
                lineNr = lineNr+1
        else:
            if  "begins" not in line and "Metrics:" not in line:
                expName = line[0:len(line)-1]


"""
Recording = {"000":{ 
            "userData": 'M30',
            "readings": {"22.00": {'Phase': 'B', 'Alpha': '1', 'Beta': '2'},
                         "22.01": {'Phase': 'B', 'Alpha': '2', 'Beta': '3'}}
             }}
"""
# Serializing json
json_object = json.dumps(emotivToJson, indent=4)
 
# Writing to sample.json
with open("metData.json", "w") as outfile:
    outfile.write(json_object)

print('finished!')






