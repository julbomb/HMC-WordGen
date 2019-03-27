French city name generator

How to use it:
    run 'python webNameGen.py'
    options:
		* -ngram <number> Set ngram for learning (default value is 10 ngram)
        * -save <filname> Saves the learning in JSON files
        * -load <filname> Load learning data from json
        * -noweb does not start webservice
        * -gen <count> Generates count names and output in stdin, only if -noweb is specified