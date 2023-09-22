# expectedformat: 
    # Metrics:.... next line will contain the decription of the experiment
    # reading begins: contains the date of the experiment
    # data, #,#,#.... metrics.

import re
import json

rwPath = ''

# the next three variables compose the file name, the expected format is:
# 'PowData filename ###.txt
rFileName = 'PowData '
expName = ""
expNr = 0 #numero dell'esperimento, per identificare il file da usare
UserIDs = [] #["M28","F44",...]
emotivToJson = {}


for expNr in range(22):
    file = open(rwPath+'\\'+ rFileName + str(expNr).zfill(3) + ".txt","r")

    lineNr = 0

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
                    }
                emotivToJson[str(expNr).zfill(3)]["Readings"][str(lineNr).zfill(6)]["AF3"] = {
                        "Theta": splitValues[1].lstrip(),
                        "Alpha": splitValues[2],
                        "BetaL": splitValues[3],
                        "BetaH": splitValues[4],
                        "Gamma": splitValues[5],
                }
                emotivToJson[str(expNr).zfill(3)]["Readings"][str(lineNr).zfill(6)]["T7"] = {
                        "Theta": splitValues[6],
                        "Alpha": splitValues[7],
                        "BetaL": splitValues[8],
                        "BetaH": splitValues[9],
                        "Gamma": splitValues[10],
                }
                emotivToJson[str(expNr).zfill(3)]["Readings"][str(lineNr).zfill(6)]["Pz"] = {
                        "Theta": splitValues[11],
                        "Alpha": splitValues[12],
                        "BetaL": splitValues[13],
                        "BetaH": splitValues[14],
                        "Gamma": splitValues[15],
                }
                emotivToJson[str(expNr).zfill(3)]["Readings"][str(lineNr).zfill(6)]["T8"] = {
                        "Theta": splitValues[16],
                        "Alpha": splitValues[17],
                        "BetaL": splitValues[18],
                        "BetaH": splitValues[19],
                        "Gamma": splitValues[20],
                }
                emotivToJson[str(expNr).zfill(3)]["Readings"][str(lineNr).zfill(6)]["AF4"] = {
                        "Theta": splitValues[21],
                        "Alpha": splitValues[22],
                        "BetaL": splitValues[23],
                        "BetaH": splitValues[24],
                        "Gamma": splitValues[25].replace('\n',''),
                }
                lineNr = lineNr+1
        else:
            if  "begins" not in line and "Waves:" not in line:
                expName = line[0:len(line)-1]

# Serializing json
json_object = json.dumps(emotivToJson, indent=4)
 
# Writing to sample.json
with open("PowData.json", "w") as outfile:
    outfile.write(json_object)

print('finito')
