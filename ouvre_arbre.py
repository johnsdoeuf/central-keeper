import sauv

f_arbre = "H:/Temp/historique.sauv"
with  open(f_arbre, 'r', encoding='utf8') as f:
	try:
		donnees = sauv.my_decoder().decode(f.read())
	
	except sauv.json.decoder.JSONDecodeError as exception:
		raise SyntaxError("le fichier historique n'est pas un format json: {}".format(exception))

if type(donnees) != dict:
	raise SyntaxError("le fichier historique n'est pas au format 'dictionnaire'")

if not 'arbre' in donnees:
	raise SyntaxError("le fichier historique ne contient pas d'arbre'")
else:
	arbre = donnees['arbre']

if 'rappel' in donnees:
	rappel = donnees['rappel']
else:
	rappel = {}

if 'err_prec' in donnees:
	err_prec = donnees['err_prec']
else:
	err_prec = {}



# Pour toutes les sauvegardes
for clef, sauv in arbre.items():
	
	# Vérification du format
	if type(sauv) != list:
		raise SyntaxError("le fichier historique de '{}' n'est pas au format 'list'".format(clef))
	
	# Vérification du nombre d'élément
	if len(sauv) != 3:
		raise SyntaxError("le fichier historique de '{}' ne comporte pas le bon nombre de niveau".format(clef))
	
	# # Vérification du contenu
	# for niveau in sauv:
	# 	for hsauv in niveau:
	# 		if type(hsauv) != sauv.Cliche:
	# 			raise SyntaxError(
	# 				"Au moins un élément d'historique de '{0}' n'est pas valide : {1}".format(hsauv, clef))



