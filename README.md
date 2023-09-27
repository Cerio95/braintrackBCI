# braintrackBCI
We used the headset "EMOTIV Insight" to use the user's focus to drive slot cars

The file "BraintrackBCI" uses input from two channels (the most correlated with the user's attention) to evaluate the user's focus and send an output accordingly.
The UI is quite terrible at the moment and shows the basics of what's needed to understand what is going on.
An ideal experimental run right now would look like this:
1- Start the program and record a baseline (type 1), the subject is supposed to relax and stand still with the eyes open (blinking introduces noise but it's okay).
2- after x seconds (from 30 to a couple of minutes) press "P" to pause and "N" to start a new phase, you'll be asked if you want to keep the calculated baseline or if you prefer to lower it
3- Press "P" again to resume the experimentation, this time the program will compare the new inputs with the calculated baseline and act accordingly to the code contained in the function "on new pow data"

// UNDER CONSTRUCTION //
