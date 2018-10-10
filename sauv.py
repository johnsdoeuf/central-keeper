# -*- coding: UTF-8 -*-
""" sauvegarde de
	"""
#version 0.1 du 26-04-2017
#version = 0.11 # 26-04-2017 correction de pas_de_sauv pour allez chercher les dates dans tous les niveaux de sauvegarde
#version = 0.12 # 30-04-2017 Inversion date et niveau dans les noms de répertoire
				# Ajout de la gestion des sommes de contrôle
#version = 0.13   Copie dans un répertoire temp puis renomme
#version = 0.14   Lance le montage aussi si la source est vide
				#ajout paramètre temp de sauvegade temporaire et le traite de manière particulière lorsque trouvé dans le répertoire
				# Les info de Lancement de fonction passe de info à debug
#version = 0.15 # Améliore Log
				# préserve au moins une sauvegarde malgré quota
#version = 0.16 # ajout d'une capture d'erreur générale
				# suppression boucle infinie lorsque erreur dans manipulation des répertoires de sauvegarde
#version = 0.17 # correction du bug avec les protocoles rsync
#version = 0.18 # Le paramètre "verb" de commande_ext masque aussi les erreurs
				# étend les recherches de reférence à tous les niveaux au lieu de seulement le premier
#version = 0.19 # corrrection du bug sur la gestion du md5 ligne 299
#version = 0.20 # Remplacement de taille_réelle par la classe Taille
				# Ajout de la fonction "bilan"
#version = 0.21 # Correction non démontage de sauvegarde
				# Distinction entre source et destination pour le montage
				# Ajout d'une fonction pour intercepter les signaux de fermeture

#version = 0.22 # L'interception des signaux de fermeture est étendu
# 06-06-2017     Ajouté lors de l'interception: démonte les volumes, termine le processus fils si il est en cours.

#version = 0.23 # Ajout de séparateur de millier dans les affichage de volume de données
# 11-06-2017    # Regroupement de des log d'erreur et critique en vue de l'envoi par mail
				# Ajout de l'écriture de la taille totale dans le bilan
				# Révision des messsages de warning pour afficher la sauvegarde concernée

#version = 0.24 # supression de --ignore-missing-args des paramètres par défaut
# 14-06-2017    #supprime le bug de double écriture de la taille des sauvegardes

#version = 0.25 # definition de chemin absolus pour le répertoire conteneur
# 19-06-2017    # Definition d'un logger par defaut

#version = 0.26 # Ajout du multisource
# 09-01-2018    # réduction du délai de reprise sauvegarde à 1 jour
				# Modification du calcul de taille des sauvegardes

#version = 0.27 # Correction bug en cas d'erreur de d'initialisation du log
# 10-01-2018	# supression du code obsolète

#version = 0.30 # ajout de l'effacement avant de renommer dans fusion_rep
# 15-01-2018

version = 0.31 # suppression log de fusion et verifie_arbre
# 20-01-2018

#version = 0.32 # modifie hiérarchie log
#				# détecte la suppression de sauvegarde dans la période de conservation
				# le verrou par fichier est remplacé par une variable d'environnement qui sera perdu à chaque coupure électrique


	# clé du fichier de configuration (en minucule)
per1='periode1'
per2='periode2'
per3='periode3'
cons1='conservation1'
cons2='conservation2'
cons3='conservation3'
src='source'
dest='dest'
qta='quota'
mntsrc='monte_source'
umntsrc='demonte_source'
mntdst='monte_destination'
umntdst='demonte_destination'
para='parametre'
md5='md5'
permd5='periodemd5'
filt='filtre'
bilan='bilan'
	# sépara
src_separateur = ';'
	# liste de clé
l_clenum = [per1, per2, per3, cons1, cons2, cons3, qta, md5, permd5]
l_cle = [src, dest, mntsrc, umntsrc, mntdst, umntdst, para,  filt, bilan] +l_clenum

	# tableaux pour fonction monte
rep = [src, dest]
mnt = [mntsrc, mntdst]
umnt = [umntsrc, umntdst]

	# declaration de constante
formatdate="%Y-%m-%d %H-%M"     # Format de date des répertoires de sauvegarde
temp = 'temp'         #répertoire temporaire de sauvegarde"
format_bilan = "\n{:%Y-%m-%d %H:%M:%S} {:>16} {:>15d} {:>15d} {:>10.2f} {:>4}"

	# fichier de données
conf_log='log.conf'
conf_sauv='sauv.conf'
	# variable de lock
var_env_verrou = "SAUV_VERROU"
	# fichier d'enregistrement de l'historique des sauvegardes
f_arbre='historique.sauv'
	#définit un variable globale pour conserver la trace des processus extérieur lancé et les fermer si nécessaire
process_en_cours = None

class init_erreur(Exception):
	def __init__(self, valeur):
		self.valeur = valeur
	def __str__(self):
		return self.valeur


class rep_sauv():
	def __init__(self,dat, che):
		if type(dat)==datetime.datetime:
			self.date=dat
		else:
			raise init_erreur("Type de donnée incorrecte pour la date")

		if type(che)==str:
			self.chemin=che
		else:
			raise init_erreur("Type de donnée incorrecte pour le chemin")

		self.lnoeud = {}
		self.taille = 0
		self.stat = {}

		#définit opérateur d'égalité
	def __eq__(self, other):
		if self.date  != other.date:
			return False
		else:
			if self.chemin != other.chemin:
				return False
			else:
				if self.taille != other.taille:
					return False
				else:
					if len(self.lnoeud) != len(other.lnoeud):
						return False
					else:
						for clef,val in other.lnoeud.items():
							if self.lnoeud[clef] != val:
								return False

		return True

		#définit la méthode d'affichage
	def __repr__(self):
		return "<objet rep_sauv date:{}, chemin:{}, taille:{}, noeud:{}>".format(self.date.strftime(formatdate),self.chemin, self.taille, self.lnoeud )


	def analyse(self):
		""" analyse le disque et complète l'element self
				crée un dictionnaire des couples Numéro de noeuds: taille en octet appelé lnoeud
		"""
		che_path = Path(self.chemin)
		logger.info("analyse de {}".format(che_path))

		if not che_path.exists():
			raise init_erreur("Répertoire inexistant: {}".format(che_path))

		id_incr = {}
		nv_taille = 0
		# scan tous les fichiers et créé un dictionnaire inode: taille
		for dossier, sous_dossiers, fichiers in os.walk(str(che_path)):
			for fich in fichiers:
				try:
					info = Path(dossier, fich).stat()
				except FileNotFoundError:
					continue

				id_incr[str(info.st_ino)] = info.st_size
				nv_taille += info.st_size

		self.taille = nv_taille
		self.lnoeud = id_incr


	# définition du decodeur et du codeur json pour l'objet rep_sauv
	# Appel par:
	# res=my_encoder().encode(objet)
	# obj2=my_decoder().decode(res)

import json    
class my_encoder(json.JSONEncoder):

	def default(self, obj):
		# Convert objects to a dictionary of their representation

		if isinstance(obj, rep_sauv):
			res={'date':obj.date.strftime(formatdate)}
			res['chemin'] = obj.chemin
			res['lnoeud'] = obj.lnoeud
			res['taille'] = obj.taille
			res['__class__'] = 'rep_sauv'
			return res

		return json.JSONEncoder.default(self, obj)

class my_decoder(json.JSONDecoder):
	def __init__(self):
		json.JSONDecoder.__init__(self, object_hook=self.dict_to_object)

	def dict_to_object(self, d):
		if '__class__' in d:
			if d['__class__']=='rep_sauv':
				try:
					dat = datetime.datetime.strptime(d['date'], formatdate)
					inst = rep_sauv(dat, d['chemin'])
					inst.taille = d['taille']
					inst.lnoeud = d['lnoeud']
				except (init_erreur, ValueError, KeyError)  as exception:
					raise json.decoder.JSONDecodeError("rep_sauv n'est pas correct: {}".format(exception),"inconnu",0)
			else:
				inst = d
		else:
			inst = d
		return inst

import configparser    
class My_configparser(configparser.ConfigParser):
	def __eq__(self, conf):
		""" Définit une fonction de comparaison item par item des objet configparser
		Retourne True si le contenu des deux objets est égal et False sinon
		"""
			#liste les sections de objet1
		lsect1=[sect for sect in self]
			#liste les sections de objet2
		lsect2=[sect for sect in conf]
			#compare les liste de section
		if not lsect1==lsect2:
				#sinon objet pas egaux
			return False
			#test une à une le contenu des sections			
		for sect in lsect1:
				#liste les clés de la section pour les deux objets
			lcle1=[cle for cle in self[sect]]
			lcle2=[cle for cle in conf[sect]]
				#teste si les listes ne sont pas égale
			if lcle1!=lcle2:
				return False
				#pour toute les clés de l'objet 1
			for cle in lcle1:
					# teste si la valeur est égale entre les objets
				if self[sect][cle].strip()!=conf[sect][cle].strip():
					return False
		return True

	def __str__(self):
		""" définit une représentation sous forme de chaine de la forme
		section1 {
			clé = valeur 
			... 
		}
		section2 ...
		La méthode renvoi un string multiligne représentant l'objet configparser"""
		res=''
		lsect1=[sect for sect in self]
 
		for sect in lsect1:
			res +="{} {{\n".format(sect)
			lcle1=[cle for cle in self[sect]]

			for cle in lcle1:
				res+= "   {0} = {1} \n".format(cle, self[sect][cle])
			res+="}\n"
		return res


def attrape_exceptions(typ, value, tback):
	""" interception générale des erreurs non gérées
	cette fonction doit être initialisée dans main
	"""
	import traceback
	l_tb = traceback.format_tb(tback, limit=None)
	logger.critical( "{}\n{}: {} \nFin anormale du programme".format(l_tb,type(typ),value))

	print("Fin anormale du programme")


def fermer_programme(signal, frame):

	"""
	Fonction appelée quand un apple de fermeture du programme est lancé par ctrl-C par exemple
	cette fonction doit être connectée dans main
	"""


	logger.info("fermeture du programme demandée" )
		# arrête le processus extérieur en cours
		# la variable globale est maj dans commande_ext
	if process_en_cours:
		process_en_cours.terminate()
		# déverrouille
	deverrouille()
		# démonte les volumes
	demonte(a_demonter)

	logger.info("--------------------------- fin du programme de sauvegarde ---------------------------")
	sys.exit(0)


def init_para(chemin):
	logger.debug("Lancement de 'init_para'")
	logger.info("Début de lecture du fichier de configuration " + conf_sauv)

	config = My_configparser()
	# charge le fichier paramètre
	try:
		config.read(chemin)
	# si erreur au chargement
	except configparser.MissingSectionHeaderError as exception:
		logger.error("Le fichier de configuration ""{}""est erroné \n{}".format(chemin, exception))

		raise init_erreur(exception)

	if len(config.sections()) == 0:
		raise init_erreur("fichier d'initialisation vide ou absent")

	for sauv in config.sections():

		# teste la validité de la destination
		if not src in config[sauv]:
			logger.error("{}-La source de n'existe pas. La sauvegarde est abandonnée".format(sauv))
			del config[sauv]
			continue
		else:
			if config[sauv][src].strip() == '':
				logger.error("{}-La source est vide. La sauvegarde est abandonnée".format(sauv))
				del config[sauv]
				continue
			# teste la validité de la destination
		if not dest in config[sauv]:
			logger.error("{}-La destination de n'existe pas. La sauvegarde est abandonnée".format(sauv))
			del config[sauv]
			continue
		else:
			if config[sauv][dest].strip() == '':
				logger.error("{}-La destination est vide. La sauvegarde est abandonnée".format(sauv))
				del config[sauv]
				continue
			# teste la validité des constante de temps
		rester = True
		for para in l_clenum:
			if para in config[sauv]:
				try:
					config[sauv].getfloat(para)
				except ValueError:
					logger.error("{}-La clé '{}' n'est pas un nombre. La sauvegarde est abandonnée".format(sauv, para))
					del config[sauv]
					rester = False
					break
				# permet de sortir de la boucle principale aussi
		if not rester:
			continue

		for cle in config[sauv]:
			if not cle in l_cle:
				del config[sauv][cle]
				logger.warning("{}-La clé {} n'est pas autorisée, elle est supprimée".format(sauv, cle))
				rester = False
				break
		if not rester:
			continue

			# analyse de la(des) source(s)
			# sépare les chemins dans une liste
		l_src = config[sauv][src].split(src_separateur)
		l2_src = []
			# test indépendament la validité des chemins
		for source in l_src:
			if not chemin_invalide(source):
				# les valides sont ajoutés à l2_src
				l2_src.append(source)

		if len(l2_src) == 0:
			# si aucun n'est valide, supprime la sauvegarde
			logger.warning(
				"Le chemin '{0} n'est pas n'est pas reconnu comme valide, la sauvegarde '{1}' est supprimée".format(
					config[sauv][src], sauv))
			del config[sauv]
			continue
		else:
			# reconstitue la clé src
			config[sauv][src] = src_separateur.join(l2_src)

		if chemin_invalide(config[sauv][dest]):
			del config[sauv]
			logger.warning(
				"Le chemin '{0} n'est pas n'est pas reconnu comme valide, la sauvegarde '{1}' est supprimée".format(
					config[sauv][dest], sauv))
			continue
		# renvoi le fichier config validé
		logger.info("Sortie normale de l'analyse des paramètres de sauvegarde '{}'".format(sauv))


	return config


#        regarde si la forme du chemin correspond à une forme connue
def chemin_invalide(che):
	logger.debug("Lancement de 'chemin_invalide'")
	if che == '-':
		return True
	else:
		return False


def verifie_arbre(config, branche):
	logger.debug("Lancement de 'verifie_arbre'")
	logger.debug("début d'analyse de l'historique des sauvegardes de {}".format(config.name) )

	arbre=[[], [], []]

		# si la destination n'existe pas
	if not os.path.isdir(config[dest]):
		logger.warning("""{}-Le répertoire de destination '{}' n'existe pas,
			L'arbre n'est pas rempli  """.format(config.name, config[dest]))
		return arbre

	for rep in os.scandir(config[dest]):
		logger.debug("Analyse du répertoire'{}'".format(rep.name))
		if rep.is_dir():
				# si un répertoire temporaire est trouvé
			if rep.name == temp:
				logger.warning("{}-Un répertoire {} est trouvé, l'ancienne sauvegarde ne s'est pas bien terminée".format(config.name, temp) )
				continue

			rep_split=rep.name.split('_')
			cas=len(rep_split)
			if cas!=2 and cas !=3:
				logger.warning("{}-le répertoire '{}' n'est pas conforme; il est ignoré".format(config.name,rep.name))
				continue

			try:
				lvl=int(rep_split[1])-1
			except ValueError:
				logger.warning("{}-le répertoire '{}' n'est pas conforme; il est ignoré".format(config.name, rep.name))
				continue
			if lvl<0 or lvl>2:
				logger.warning("{}-le répertoire '{}' n'est pas conforme; il est ignoré".format(config.name, rep.name))
				continue
			try:
				dat=datetime.datetime.strptime(rep_split[0], formatdate)
			except ValueError:
				logger.warning("{}-le répertoire '{}' n'est pas conforme; il est ignoré".format(config.name, rep.name))
				continue
			if cas == 3:
				try:
					int(rep_split[2])
				except TypeError:
					logger.warning(
						"{}-la troisième partie du répertoire '{}' n'est pas un entier; il est ignoré".format(config.name, rep.name))

				else:
					if md5 in config:
						if config[md5] < rep_split[2]:
							config[md5] = rep_split[2]
							logger.debug("config[md5] : {}".format(config[md5]))
							logger.info("sauvegarde avec verification des sommes de contrôle détectée en date du: {}"
										.format(ref_md5 + datetime.timedelta(days=int(config[md5]))))
					else:
						config[md5] = rep_split[2]

			logger.info("Répertoire '{}' validé".format(rep.name))

			item = rep_sauv(dat, os.path.join(config[dest], rep.name))
			logger.debug(item)

			# Insertion dans l'arbre pour obtenir une liste triée par date
			a = 0
			trouvé = False

			while len(arbre[lvl]) > a:
				if arbre[lvl][a].date < dat:
					arbre[lvl].insert(a, item)
					trouvé = True
					break
				a += 1
				# si pas d'insertion dans la boucle alors, insertion à la fin
			if not trouvé:
				arbre[lvl].append(item)
	# vérifie l'ordre des dates
# todo - améliorer la programation de ce test
	old_date = datetime.datetime(1990,1,1)
	iterateur = iterateur_arbre(arbre)
	for incr in iterateur:
		if incr.date <= old_date:
			logger.warning("un increment de sauvegarde est mal daté ou pas dans le bon niveau :{}, il est supprimé ".format(incr))
			try:
				arbre[0].remove(incr)
			except ValueError:
				pass
			try:
				arbre[1].remove(incr)
			except ValueError:
				pass
			try:
				arbre[2].remove(incr)
			except ValueError:
				pass
		else:
			old_date = incr.date

	#compare la partie date et répertoire des rep sauv
	if not comparaison_arbre(arbre, branche):
		logger.warning(
			"{}-Le fichier d'historique ne correspond pas au répertoires trouvé avec 'verifie_arbre'".format(config.name))

		# complète la sauvegarde avec les données de taille
		logger.info("commence la reconstruction de la taille des sauvegardes")
		iterateur = iterateur_arbre( arbre)
		for incr in iterateur:
			incr.analyse()

		reduit_inode(arbre)

		# retourne l'arbre créé
		return arbre
	else:


		return branche

def comparaison_arbre(branche1, branche2):
	# vérifie la taille du premier niveau
	if len(branche1) != len(branche2):
		logger.warning("Les sauvegardes en mémoire et sur disques sont différentes dans leur taille")
		return False

	for lnv, lenr in zip(branche1, branche2):
		# vérifie la taille du second niveau
		if len(lnv) != len(lenr):
			logger.warning("Les sauvegardes en mémoire et sur disques sont différentes dans leur taille")
			return False

		for sauv_nv, sauv_enr in zip(lnv, lenr):
			# compare les dates
			if sauv_nv.date != sauv_enr.date:
				logger.warning("Les sauvegardes en mémoire et sur disques sont différentes: date {} != {}".format(sauv_nv.date, sauv_enr.date))
				return False
			# compare les chemins
			if sauv_nv.chemin != sauv_enr.chemin:
				logger.warning("Les sauvegardes en mémoire et sur disques sont différentes: chemin {} != {}".format(sauv_nv.chemin, sauv_enr.chemin))
				return False
			#teste la validité de la taille et du dictionnaire
			try:
				sauv_enr.taille + 1
				len(sauv_enr.lnoeud)
			except TypeError:
				logger.warning("Les données de taille de la sauvegarde ne sont pas conformes")
				return False
# todo - A tester
	logger.info("Les sauvegardes en mémoire et sur disques sont identiques ")
	return True

def iterateur_arbre( sauv):
	# itérateur pour parcourir arbre[sauv] linéairement du plus ancien au plus récent
	for lvl in reversed(sauv):
		for incr in reversed(lvl):
			yield incr


def reduit_inode(branche):
	# ne conserve les inodes que de la dernière sauvegarde
	it = iterateur_arbre( branche)
	première = True

	for incr in it:


		if not première:
			# vérification de l'ordre
			logger.debug("Test de date: {} >= {}".format(date, incr.date))
			if date > incr.date:
				raise SyntaxError("L'ordre des sauvegardes est incorrect")



			anc_id_incr = précédent.lnoeud
			if len(anc_id_incr):

				taille = 0
				# cherche les id seulement dans anc_id_incr
				for id, ta in anc_id_incr.items():
					if not id in incr.lnoeud:
						taille += ta
				# mise à jour du précédent
				précédent.taille = taille
				précédent.lnoeud = {}

		première = False
		date = incr.date
		précédent = incr



def charge_arbre(f_arbre):
	logger.debug("Lancement de 'charge_arbre'")

	if os.path.exists(f_arbre):
		with  open(f_arbre,'r',  encoding='utf8') as f:
			try:
				arbre=my_decoder().decode(f.read())

			except json.decoder.JSONDecodeError as exception:
				raise SyntaxError("le fichier historique n'est pas un format json: {}".format(exception))

		if type(arbre)!=dict:
			raise SyntaxError("le fichier historique n'est pas au format 'dictionnaire'")

			# Pour toutes les sauvegardes
		for clef,sauv in arbre.items():

				#Vérification du format
			if type(sauv)!=list:
				raise SyntaxError("le fichier historique de '{}' n'est pas au format 'list'".format(clef))


				#Vérification du nombre d'élément
			if len(sauv)!=3:
				raise SyntaxError("le fichier historique de '{}' ne comporte pas le bon nombre de niveau".format(clef))


				#Vérification du contenu
			for niveau in sauv:
				for hsauv in niveau:
					if type(hsauv)!=rep_sauv:
						raise SyntaxError("Au moins un élément d'historique de '{0}' n'est pas valide : {1}".format(hsauv, clef))

			# renvoi l'arbre valide
		return arbre

	else:
		raise init_erreur("historique non trouvé")

# todo - compléter avec les tests de validité de taille et inodes

# todo - créer tests
def taille_arbre(arbre):
	iterateur = iterateur_arbre(arbre)
	taille = 0

	for incr in iterateur:
		taille += incr.taille

	return taille


def sauv_arbre(f_arbre, arbre):
	logger.debug("Lancement de 'sauv_arbre'")

	if arbre==None:
		raise SyntaxError("l'arbre est vide")

	if os.path.exists(os.path.split(f_arbre)[0]):
		with  open(f_arbre,'w',  encoding='utf8') as f:
			try:
				f.write(my_encoder().encode(arbre))

			except json.decoder.JSONDecodeError as exception:
				raise SyntaxError("l'arbre des historiques ne peut pas être traduit: {}".format(exception))
	else:
		raise SyntaxError("le chemin n'existe pas")

def commande_ext(commande, verb):
	logger.debug("Lancement de 'commande_ext' avec {}".format(commande))
	if type(commande)!=list:
		raise SyntaxError("Le paramètre doit être une liste")
	process_erreur=b''

	try:
		process = subprocess.Popen(
			commande,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE
		)
		process_en_cours = process
		process_output, process_erreur =  process.communicate()
		process_en_cours = None
	except (OSError) as exception:
		if verb:
			logger.error("Retour de la commande: \n {}".format(process_erreur.decode('utf8')))
		raise OSError(exception)
	else:
			#écriture du message de stdout
		sortie_normale = process_output.decode('utf8').split('\n')

		if verb:
			logger.info("Retour de la commande:")
			for lig in sortie_normale:
				logger.info( lig)
			#écriture du message de stderr
		if process_erreur!=b'':
			if verb:
				logger.error(process_erreur.decode('utf8'))


			raise OSError("Commande ou paramètres invalides")

		return sortie_normale

def copie(config, arbre ):
	logger.debug("Lancement de 'copie'")

	source=config[src]
	if not repertoire_accessible(source):
#            Si la source n'existe pas
		logger.warning ("{}-La source '{}' est introuvable ".format(config.name, source))
		raise OSError("La source est introuvable ")


	if para in config:
		parametre=config[para]     # si les paramètres de rsync sont définis, les utilise
	else:
		parametre='rsync -rv --delete'    #paramètres par défaut

		#défini la sauvegarde de référence
	ref_chemin = ""
		# écrit les différents chemins possible dans l'ordre inverse de priorité
	for nro in range(2,-1,-1):
		try:
			ref_chemin = arbre[nro][0].chemin
		except IndexError:
			pass

	if ref_chemin == "":
			#        si pas de sauvegarde trouvée
		reference=''
	else:
			# si un autre sauvegarde est trouvée, s'en sert de référence
		if not repertoire_accessible(ref_chemin):
			#Si la reference n'existe pas
			logger.warning ("{}-La référence est introuvable ".format(config.name))
			reference=''
		else:
			reference=' --link-dest="' + ref_chemin + '"'

	maintenant = datetime.datetime.now()
	para_md5 = ''
	nom_md5 = ''
	sauv_md5=False
		# si le parametre periondemd5 est défini force la vérification de tous les fichiers
	if permd5 in config:
		if md5 in config:
			dern_md5 = (ref_md5 + datetime.timedelta(days=int(config[md5])))
			logger.debug("dernière sauvegarde avec MD5: {}".format(dern_md5) )
			if (maintenant - dern_md5
					> datetime.timedelta(days=int(config[permd5])) ):
				para_md5 = '--checksum'
				nom_md5 = '_{}'.format((maintenant - ref_md5).days)
				logger.info("cette sauvegarde base la comparaison sur la somme de controle (MD5)")
				sauv_md5=True
		else:
			para_md5 = '--checksum'
			nom_md5 = '_{}'.format((maintenant - ref_md5).days)
			logger.info("cette sauvegarde base la comparaison sur la somme de controle (MD5)")


	filtre=''
	if filt in config:
		f_filter=os.path.join(os.path.split(__file__)[0],config[filt])
		if not os.path.exists(f_filter):
			logger.warning("{}-fichier de filtre introuvable,  il est ignoré".format(config.name))
		else:
			filtre="--filter='. {}'".format(f_filter)


	destination_temp=os.path.join(config[dest], temp )
	destination = os.path.join(config[dest], maintenant.strftime(formatdate) + '_1' + nom_md5)

	logger.info("copie de {0} vers {1}".format(source ,  destination) )
	commande=shlex.split(parametre +' '+ para_md5 + ' '+filtre+ ' '+ reference + ' "'+source+'" "'+destination_temp+'"')
	logger.debug("Commande:"+str(commande))

	sortie = commande_ext(commande, verb=True)
		# si bilan est configuré
	if bilan in config:
		fbilan=config[bilan]
			# ouvre le fichier
		ret = extrait_bilan(sortie, config.name, sauv_md5 )
		logger.debug("Ecriture dans le fichier bilan: {}".format(ret))
		with open (fbilan, 'a', encoding='utf8') as f:
			try:
					#écrit la ligne générée par extrait_bilan
				f.write( ret)
			except OSError:
				logger.warning("{}-Impossible de compléter le fichier bilan : {}".format(config.name, fbilan))


	logger.info("renomme {} en {}".format(destination_temp,destination) )
	try:
		os.rename(destination_temp,destination)
	except OSError as exception:
		logger.warrning("renommer {} en {} a causé une erreur".format(destination_temp,destination))
		logger.warnning(exception)

	# met à jour la taille des sauvegardes
	# t = Taille_Increment()
	# t.Ajout(config[dest], destination)
	retour = rep_sauv(maintenant, destination)
	retour.analyse()

	return retour


def extrait_bilan(lignes, sauv, md5):
	"""
	à partir d'une liste des lignes renvoyées par rsync, extrait les valeurs intéressantes
	et les mets en forme pour former une seule ligne prête à écrire dans un fichier
	le formatage se trouve dans la chaine constante format_bilan
	:param lignes: liste des lignes
			sauv: le nom de la sauvegarde
			md5 : booléen si la sauvegarde est avec vérification md5
	:return: str formaté par la chaîne format_bilan
	"""
		# prépare les deux expressions régulières
	regex1 = re.compile(r"sent (?P<sent>[0-9,]*) bytes.*received (?P<received>[0-9,]*) bytes")
	regex2 = re.compile(r"total size is (?P<stot>[0-9,]*) .*speedup is (?P<speed>[0-9.]*)")
	bechanges = 0
	btot = 0
	speed = 0

	for l in lignes:
		result = regex1.search(l)
		if result:
			bechanges = int(re.sub(",", "", result.group("sent"))) + int(re.sub(",", "", result.group("received")))
			logger.debug("Ligne 'sent received' trouvée ")

		result = regex2.search(l)
		if result:
			btot = int(re.sub(",", "", result.group("stot")))
			speed = float(result.group("speed"))
			logger.debug("Ligne total size' trouvée ")

	d = datetime.datetime.now()

	if md5:
		return format_bilan.format(d, sauv, bechanges, btot, speed, "md5")
	else:
		return format_bilan.format(d, sauv, bechanges, btot, speed, "")

def analyse_repertoire(config, arbre):
	logger.debug("Lancement de 'analyse_repertoire'")

		# Regroupement du niveau 1
	if cons1 in config and per2 in config and len(arbre[0])>0:
		cons=config.getfloat(cons1)
		per_suiv=config.getfloat(per2)
		offset_arbre=0
		ref=datetime.datetime.now()
		regroupe(cons, per_suiv, arbre, offset_arbre, ref)

		# Regroupement du niveau 2
	if cons2 in config and per3 in config and len(arbre[1])>0:
		cons=config.getfloat(cons2)
		per_suiv=config.getfloat(per3)
		offset_arbre=1
		ref=datetime.datetime.now()
		regroupe(cons, per_suiv, arbre, offset_arbre, ref)

	reduction(config,arbre)


	return arbre

def regroupe(cons, per_suiv, arbre, offset_arbre, ref):
	logger.debug("Lancement de 'regroupe'")
	saute=0

	# si la date est au delà de la conservation
	while arbre[offset_arbre][-1-saute].date < ref-datetime.timedelta(days=cons) and len(arbre[offset_arbre]) >= 2 + saute:
		src = arbre[offset_arbre][-1-saute].chemin
		dst = arbre[offset_arbre][-2-saute].chemin

		# si md5 dans source mais pas dans la destination
		try:
			src_split = src.split('_')
			dst_split = dst.split('_')
		except IndexError:
			pass
		else:
			if len(src_split) == 3 and len(dst_split) == 2:
					# Ajoute à la destination
				dst_old = dst
				dst = dst + '_' + src_split[2]
				arbre[offset_arbre][-2 - saute].chemin = dst
				os.renames(dst_old, dst)


		logger.debug("Déplacement de {} dans {}".format(src, dst))

		# fusionne les répertoires (déplace le contenu de src dans dst)
		try:
			l_a_depl = os.listdir(src)
		except FileNotFoundError:
			saute += 1
			logger.warning("Le répertoir à déplacer {} n'existe pas:".format(src))

		else:	# si la liste est valide
			#for a_depl in l_a_depl:
			try:
				fusion_rep(Path(src), Path(dst))
			except OSError as exception:
				logger.warning("Le déplacement de {} a déclenché une erreur:".format(src))
				logger.warning(exception)
				saute+=1
					#break
			else:

				# augmente la valeur de taille de dst de src
				arbre[offset_arbre][-2 - saute].taille += arbre[offset_arbre][-1 - saute].taille
				# supprime l'élément
				del arbre[offset_arbre][-1 -saute]



	# regarde si le dernier élément du niveau courant est bien plus loin que la période de conservation
	dern_sauv = arbre[offset_arbre][-1].date
#    if ref+datetime.timedelta(days=cons)<dern_sauv:
			# vérifie si il n'y a pas de sauv au niveau supérieur ou si assez éloignée
	cond = True
	if len(arbre[offset_arbre+1]) > 0:
		if dern_sauv < arbre[offset_arbre+1][0].date + datetime.timedelta(days = per_suiv):
			cond = False

	if cond:
		# change le niveau de sauvegarde
		che_sauv,src_sauv = os.path.split( arbre[offset_arbre][-1].chemin )

		# définit le nouveau nom de répertoire
		try:
			src_split = src_sauv.split('_')
		except IndexError:
				# pas de _ dans le nom de répertoire
			dst_sauv = src_sauv+'_'+str(offset_arbre+2)
		else:
			if len(src_split) >= 2:
				# si le second élément est 1 ou 2
				if  (src_split[1] == '1' or src_split[1] == '2'):
					# remplace le niveau par le nouveau niveau
					dst_sauv = src_sauv.split('_')[0] + '_' + str(offset_arbre+2)
				else:   # ajoute niveau derrière
					dst_sauv =src_sauv+'_'+str( offset_arbre+2 )
				# ajoute le md5 s'il existe
				if len(src_split) == 3:
					dst_sauv = dst_sauv + '_' + src_split[2]

			# renomme
		logger.info("Renomme le répertoire {} ".format(src_sauv))
		logger.info("en {} ".format(dst_sauv))

		dst_sauv = os.path.join( che_sauv, dst_sauv )
		src_sauv = os.path.join( che_sauv, src_sauv )

		logger.debug( "renomme {} en {}".format( src_sauv, dst_sauv ) )

		try:
			os.renames( src_sauv, dst_sauv )
		except OSError as exception:
			logger.warning( "Le renommage de {} a déclenché une erreur:".format( src_sauv ) )
			logger.warning(exception)
		else:
				# récupère l'ancien élément
			nv_sauv = arbre[offset_arbre][-1]
				# met à jour le répertoire
			nv_sauv.chemin = dst_sauv

				# l'ajoute en premier du niveau supérieur
			arbre[offset_arbre+1].insert( 0, nv_sauv )
				# supprime l'élément du niveau courant
			del arbre[offset_arbre][-1]



def fusion_rep(src, dst):
	""" Deplace le contenu de la source dans la destination, La source est effacée
		Paramètres:
	 		src = source (path)
	 		dst = destination (path)
	"""
	#logger.debug("fusion de '{}' dans '{}".format(src,dst))
	try:
		liste = src.iterdir()
		dst.name
	except AttributeError:
		raise ValueError("La source n'est pas du type Path")

	for élém in liste:

		#logger.debug("boucle de traitement de : '{}'".format(élém))
		liste_aff = src.iterdir()
		for a in liste_aff:
			logger.debug("     {}".format(a))


		sdst = dst / élém.name
		if élém.is_dir():
			if sdst.exists():
				# regarde le niveau supérieur
				fusion_rep(élém,sdst)
			else:
				# déplace le répertoire
				try:
					os.renames(str(élém),str(sdst) )
				except OSError as exception:
					logger.error("erreur de déplacement du répertoire: {} dans '{}'".format(str(élém), str(sdst)))
					logger.error("erreur: {}".format(exception))
					raise OSError("erreur de déplacement du répertoire: {}".format(exception))

		else:
			# déplace le fichier
			#logger.debug("déplacement du fichier: {} dans '{}'".format(str(élém), str(sdst)))
			if sdst.exists():
				try:
					os.remove(str(sdst))
				except OSError as exception:
					logger.error("erreur de supression du fichier: {} ".format( str(sdst)))
					logger.error("erreur: {}".format(exception))
					raise OSError("erreur de supression du fichier: {}".format(exception))
			try:

				os.rename(str(élém),str(sdst))
			except OSError as exception:
				logger.error("erreur de déplacement du fichier: {} dans '{}'".format(str(élém),str(sdst)))
				logger.error("erreur: {}".format(exception))
				raise OSError("erreur de déplacement du fichier: {}".format(exception))
	#supprime le répertoire vidé
	try:
		os.rmdir(str(src))
	except FileNotFoundError:
		pass

# supprime les dernières sauvegarde pour rentrer dans le quota
def reduction(config,arbre):

		# calcule la taille de la sauvegarde
	taille_sauvegarde = taille_arbre(arbre)

	if qta in config:
		# teste si le quota est atteint
		objectif = config.getfloat(qta) * 0.95 * 1000000000
		logger.info("Objectif: {:,}".format(int(config.getfloat(qta) * 1000000000)))
		if objectif > taille_sauvegarde:
			logger.info("Pas besoin de réduction")
			ecriture_taille_sauv(config,taille_sauvegarde)
			return

	else:
	# si le quota n'est pas définit, signale que le disque est presque plein
		disque_pr = shutil.disk_usage(config[dest])
		if disque_pr.free < disque_pr.total * .05:
			logger.warning("{}-Le disque de destination de capacité {0} est presque plein, il reste {1} ".format(config.name,
																						disque_pr.total, disque_pr.free))
			ecriture_taille_sauv(config, taille_sauvegarde)
			return

	logger.info("réduction nécessaire")
	nbrsauv = 0

	for l_niv in arbre:
		nbrsauv += len(l_niv)

	erreur=False

	# recherche la date de la dernière sauvegarde
	for l_niv in arbre:
		if len(l_niv) != 0:
			doldest_sav = dlast_sav = l_niv[0].date
			break
	# dlast_sav = datetime.datetime.today()
	# for a in range(0,2):
	# 	try:
	# 		if arbre[a][0].date < dlast_sav:
	# 			dlast_sav = arbre[a][0].date
	# 	except IndexError:
	# 		None
	# doldest_sav = dlast_sav


	# regarde dans tous les niveaux en commençant par le 3
	for niv in range(3,0,-1):

		# si l'objectif est déjà atteint
		if objectif > taille_arbre(arbre):
			break

			# préserve le niveau 1 si une erreur s'est produite
		if erreur and niv == 1:
			continue
			# définit la durée de conservation
		limite_cons=10000.0
		try:
			if niv == 3:
				limite_cons=config.getfloat(cons3)
			else:
				if niv == 2:
					limite_cons = config.getfloat(cons2)
				else:
					if niv == 1:
						limite_cons = config.getfloat(cons1)
		except NameError:
			pass
		# évite les valeurs à none
		if limite_cons == None:
			limite_cons = 10000.0

		# pour toutes les sauvegardes
		for sav in range(len(arbre[niv-1])-1,-1,-1):

			# tant que la taille n'est pas atteinte
			if objectif < taille_arbre(arbre):

				rep = arbre[niv - 1][sav]
				nbrsauv -= 1
				if nbrsauv <= 0:
					logger.warning("{}-'{}' est la dernière sauvegarde, elle ne peut être effacée ".format(config.name,rep))
					logger.warning("{}-Le quota est inadapté".format(config.name))

				else:
					logger.info("effacement du répertoire '{}'".format(rep.chemin) )
						# effacement du répertoire
					try:
						shutil.rmtree(rep.chemin)
					except OSError as exception:
						logger.warning("{}-Erreur lors de l'effacement du répertoire '{}'\n{}".format(config.name, rep.chemin, exception))

						erreur = True
					else:
						# si la durée de conservation ne peut être respectée
						# calcul le temps entre la première sauvegarde et celle en traitement converti en jour
						ecart_cons = ( arbre[niv-1][0].date - rep.date ).total_seconds()/86400
						if ecart_cons - limite_cons*0.75 < 0:
							# message si la conservation est réduite à moins de 75%
							logger.error("{}-Le répertoire '{}' aurait du être conservé,\n le quota ne permet pas de respecter 75% du critère de conservation CONSERVATION{}".format(config.name, rep.chemin, niv))
						else:
							if  ecart_cons - limite_cons < 0:
								# message si la conservation est réduite entre 75% et 100%
								logger.warning("{}-Le répertoire '{}' aurait du être conservé,\n le quota ne permet pas de respecter le critère de conservation CONSERVATION{}".format(config.name, rep.chemin, niv))

						# effacement dans le tableau arbre
						del (arbre[niv-1][sav])



			else:
				logger.info("Objectif de taille atteint")

				break

	# recherche la sauvegarde la plus ancienne
	for l_niv in reversed(arbre):
		if len(l_niv) != 0:
			doldest_sav  = l_niv[-1].date
			break
	# if doldest_sav > rep.date:
	# 	doldest_sav = rep.date
	# ecrit la taille dans bilan
	ecriture_taille_sauv(config, taille_arbre(arbre))


def ecriture_taille_sauv(config, taille):
	""" ecrit la taille dans le bilan """

	if bilan in config:
		fbilan = config[bilan]
		# ouvre le fichier
		logger.debug("Ecriture dans le fichier bilan: {}".format(taille))
		with open(fbilan, 'a', encoding='utf8') as f:
			try:
				# écrit la ligne générée par extrait_bilan
				f.write("{:>15}".format(taille))
			except OSError:
				logger.warning("{}-Impossible de compléter le fichier bilan : {}".format(config.name, fbilan))


def init_logging(fichier):

	# si le fichier n'existe pas
	if not os.path.exists(fichier):
		logger = logging.getLogger()
		logger.warning("fichier de configuration {0} ne se trouve pas dans {1}".format(conf_log,os.path.split(os.path.abspath(__file__))[0] ))
		return logger

	# ouvre le fichier de configuration du journal
	with open(fichier, 'r',  encoding='utf8') as f:
		try:
			logging_config=json.load(f)
		except json.decoder.JSONDecodeError:
			raise init_erreur("fichier de configuration erroné" )

	# interprète le fichier de configuration
	try:
		dictConfig(logging_config)
	except (ValueError, TypeError, AttributeError , ImportError,  KeyError) as err:
		raise init_erreur("Le ficher de configuration du journal est erronée - {0}".format(err))
	if 'loggers' in logging_config:
		for a in logging_config['loggers']:pass
	else:
		raise init_erreur("La clé 'loggers' ne se trouve pas dans la configuration")

	logger = logging.getLogger(a)
	if not logger.hasHandlers():
		raise init_erreur("Le journal d'événement n'est pas configuré")
	return logger


def verrouille():
	logger.debug("Lancement de 'verrouille'")

	if var_env_verrou in os.environ:
		# calcule le temps en heure depuis sa création. un décalage de une heure apparait en fonction des décalages
		délai_h = ((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds() - float(
			os.environ[var_env_verrou])) / 3600
		# si une autre sauvegarde n'est pas terminée
		if délai_h < 14:
			logger.info("une sauvegarde est déjà en cours depuis {0:.1f} heures".format(délai_h))
			return False
		else:
			# si une autre sauvegarde date de plus d'un jour
			if délai_h > 2 * 24:
				logger.error("Un verrou de plus de deux jours est détecté. force la sauvegarde")
				deverrouille()
				return verrouille()
			else:
				logger.warning("sauvegarde déjà verrouillée - sauvegarde annulée")
				return False
	else:
		try:  # nombre de seconde depuis 1970
			os.environ[var_env_verrou] = str((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds())
		except OSError:
			logger.error("Impossible de créer le fichier de verrou")
			return False
		return True


def deverrouille():
	logger.debug("Lancement de 'deverrouille'")

	if var_env_verrou in os.environ:
		logger.info("suppression du verrou de la sauvegarde")
		try:
			del (os.environ[var_env_verrou])
		except (OSError, KeyError):
			logger.error("Suppression du verrou impossible")
	else:
		logger.info("le fichier verrou n'existe pas")


def monte(sens, config):
	""" monte le répertoire source ou destination et retourne l'opération de démontage correpondante
		fonctionne aussi pour des répertoires multiples séparé par src_separateur (;)
		si le répertoire de base est accessible, regarde si il contient des données
		si non ou si il est vide, tente de le monter
		Si le répertoire n'est toujours pas accessible (ou toujours vide) renvoi OSerror
		Sinon retourne une chaine représentant la commande de démontage associée
		ou none si rien n'est à démonter

		sens: 0->source 1-> destination
		config: section "configparser" correspondant à la sauvegarde concernée
	"""
	# regarde si sens est bien un int de 0 ou 1
	if sens != 0 and sens != 1:
		raise ValueError("Le paramètre 'sens' n'est pas conforme")

	logger.debug("Lancement de 'monte' {}".format(config[rep[sens]]))

	l_rep = config[rep[sens]].split(src_separateur)

	for repertoire in l_rep:
		# regarde si rep est accessible
		if repertoire_accessible(repertoire):
			logger.debug("{} est trouvé ".format(repertoire))

			# essai d'acceder au contenu du répertoire
			commande = 'rsync ' + repertoire
			# ajoute un / à la fin si il n'existe pas
			if commande[-1] != '/':
				commande += '/'

			retour = commande_ext(shlex.split(commande), verb=False)
			# compte le nombre de ligne en sortie
			logger.debug(retour)
			try:
				nbr_rep = len(retour)
			except OSError:
				logger.debug("Le nombre de sous-répertoire de {} ne peut être déterminé".format(repertoire))
				nbr_rep = 0
			# si le nombre de fichier/répertoire est non nul
			if nbr_rep > 2:
				logger.debug("{} est trouvé avec {} sous-répertoires ou fichiers".format(repertoire, nbr_rep))
				# affecte LE repertoire qui est accessible à la config pour les utilisations ultérieures
				config[rep[sens]] = repertoire
				return
		else:
			logger.debug("Le répertoire {} n'est pas accessible".format(repertoire))

		# si les répertoires ne sont pas accessible en direct
	retour = None
	# si le paramètre monte est configuré
	if mnt[sens] in config:
		# tente de monter le répertoire
		commande = shlex.split(config[mnt[sens]])
		logger.debug(commande)

		commande_ext(commande, verb=False)
		# enregistre l'instruction de démontage associée
		if umnt[sens] in config:
			retour = config[umnt[sens]]
		else:
			logger.warning("{}-Une commande de montage a été utilisée sans que le démontage soit configuré".format(config.name))

		# teste à nouveau la réponse des répertoires
		for repertoire in l_rep:
			# regarde si rep est accessible
			if repertoire_accessible(repertoire):
				# essai d'acceder au contenu
				try:
					nbr_rep = len(os.listdir(repertoire))
				except OSError:
					logger.debug("Le nombre de sous-répertoire de {} ne peut être déterminé".format(repertoire))
				else:
					logger.info("Répertoire '{}' montée avec succès".format(repertoire))
					# affecte LE repertoire qui est accessible à la config pour les utilisations ultérieures
					config[rep[sens]] = repertoire
					return retour
			else:
				logger.debug("Le répertoire {} n'est pas accessible".format(repertoire))
	else:
		raise OSError("""{}-Le répertoire '{}' n'est pas accessible et aucune instruction de montage
			n'est disponible""".format(config.name,config[rep[sens]]))

		# si rien n'a fonctionné
		# démonte le répertoire
	commande_ext(retour, verb=False)
	raise OSError("{}-Le(s) répertoire(s) '{}' n'est pas accessible(s)".format(config.name, config[rep[sens]]))


def demonte(a_demonter):
	logger.debug("Lancement de 'demonte'")
	logger.debug(a_demonter)
	if type(a_demonter)!=set:
		logger.warning("L'objet retourné n'est pas du type attendu")
		return

	for commande in a_demonter:
		if type(commande) == str:
			if commande != "":
				logger.info("commande de démontage '{}'".format(commande))
				try:
					commande_ext(shlex.split(commande), verb=True)
				except OSError:
					logger.warning("Une erreur est apparue lors du démontage '{}'".format(commande))


def repertoire_accessible(rep):
	logger.debug("Lancement de 'repertoire_accessible' {}".format(rep))

	commande = shlex.split('rsync --list-only "{0}" "{1}"'.format(rep, os.path.split(__file__)[0] ))
	logger.debug(commande)

	try:
		commande_ext(commande, verb=False)
	except OSError:
		logger.debug("Répertoire '{}' non trouvé".format(rep))
		return False
	else:
		logger.debug("Répertoire '{}' trouvé".format(rep))
		return True


def init_args():
	logger.debug("Lancement de 'init_args'")
	parser = argparse.ArgumentParser(description='Script de sauvegarde.')
	parser.add_argument('-f', '--force', action="store_true",  help='force la sauvegarde, ne tient pas compte du paramètre PERIODE1')
	parser.add_argument('-i', '--ignore-verrou', action="store_true", help='outrepasse le verrou')

	args = parser.parse_args()

	logger.debug("résultat des arguments")
	logger.debug(args)
	return args


def pas_de_sauv(config,  arbre,  force):  
		# teste si une sauvegarde est nécessaire,
		logger.debug("Lancement de 'pas_de_sauv'")

		# teste si l'arbre est rempli
		# Si l'arbre n'est pas défini, laisse passer pour refaire le calcul après la création de l'arbre
		if len(arbre[0])+len(arbre[1])+len(arbre[2]) == 0:
			logger.info("L'arbre est vide")
			return False

		if force:
			logger.info("sauvegarde forcée")
			return False

			# trouve un niveau non vide
		for niv in range(0,3):
			if len(arbre[niv]) > 0:
				break

		logger.debug("niveau:{}".format(niv))

		# saute cette sauvegarde si  periode1 définie et délai entre deux sauvegardes pas atteint
		if per1 in config:
			limite=arbre[niv][0].date+datetime.timedelta(hours=config.getfloat(per1)*24*.9)
			if datetime.datetime.now() < limite:
				logger.info("La sauvegarde est sautée car il est trop tôt" )
				logger.debug("limite:{}".format(limite))
				return True
			else:
				logger.info("la sauvegarde est nécessaire")
				logger.debug("limite:{}".format(limite))
		else:
			logger.info("La période {} n'est pas définie".format(niv))


		return False

import dbf

bl_date = "datecliche"
bl_job = "job"
bl_voltransfere ="vtransfere"
bl_volcli = "vcliche"
bl_voljob = "vsauvegard"
bl_voljobobj = "ovsauvegar"
bl_debit = "debit"
bl_md5 = "avec_hash"
bl_md5dern = "duree_hash"
bl_md5dernobj = "odureehash"
bl_cons1 = "duree1"
bl_cons1obj = "oduree1"
bl_cons2 = "duree2"
bl_cons2obj = "oduree2"
bl_cons3 = "duree3"
bl_cons3obj = "oduree3"
bl_cons = "dureeg"
bl_consobj = "odureeg"

dbf_structure = """{} C(19);{} C(18);
	{} N(15,0);{} N(15,0);{} N(15,0);{} N(15,0);
	{} N(8,2);{} L;{} N(5,0);{} N(5,0);
	{} N(5,0);{} N(5,0);
	{} N(5,0);{} N(5,0);
	{} N(5,0);{} N(5,0);
	{} N(5,0);{} N(5,0);""".format(
	bl_date, bl_job,
	bl_voltransfere, bl_volcli, bl_voljob, bl_voljobobj,
	bl_debit, bl_md5, bl_md5dern, bl_md5dernobj,
	bl_cons1, bl_cons1obj,
	bl_cons2, bl_cons2obj,
	bl_cons3, bl_cons3obj,
	bl_cons, bl_consobj
)


def ecriture_bilan(config, cli):
	""" ecrit le données du cliché courant dans la base de donnée dbase
		créé le fichier si inexistant
		supprime le dictionnaire prop
		
		entrée:
		Config, objet configparser
		cli, objet rep_sauv avec un dictionnaire de statistique à écrire
		
		retour:
		FileNotFoundError si l'écriture n'est pas possible
		dbf.DbfError si le ficher est corrompu, ou l'enregistrement à écrire mal formé
	"""
	print(dbf_structure)

	if bilan in config:
		fbilan = config[bilan]
		if not os.path.exists(fbilan):
			dbf.Table(fbilan, dbf_structure)

		with dbf.Table(fbilan) as db:
			db.open(mode=dbf.READ_WRITE)
			db.append(cli.stat)
			
def calcul_retention(cli, arbre, config):
	stat = cli.stat
	cons = 0
	# création des objectifs
	# if cons1 in config:
	# 	stat[bl_consobj1] = config[cons1]
	# 	cons += config[cons1]
	# if cons2 in config:
	# 	stat[bl_consobj2] = config[cons2]
	# 	cons += config[cons2]
	# if cons3 in config:
	# 	stat[bl_consobj3] = config[cons3]
	# 	cons += config[cons3]
	
	cle_conf = (cons1, cons2, cons3)
	cle_stat = (bl_cons1obj, bl_cons2obj, bl_cons3obj)
	maintenant = datetime.datetime.now()
	cons = 0
	for a,b in zip(cle_conf, cle_stat):
		if a in config:
			stat[b] = config[a]
			cons += float(config[a])
	stat[bl_consobj] = cons
	
	cle_stat = (bl_cons1, bl_cons2, bl_cons3)
	base = maintenant
	date_max = maintenant
	for	level,b in zip(arbre, cle_stat):
		if len(level):
			stat[b] = (base - level[-1].date).total_seconds()//86400
			base = level[-1].date
			date_max = min(date_max, level[-1].date)
			
	stat[bl_cons] = (maintenant - date_max).total_seconds()//86400
	
	
#Début du programme
import argparse
import os
import shlex
import subprocess
import datetime
import sys
import signal
import logging
from logging.config import dictConfig
import json
import shutil
import re
import itertools
import pickle
import time
from pathlib import Path
#from StringIO import StringIO

if __name__ == '__main__':

	# fichier de configuration du journal
	flogconf=os.path.join(os.path.split(os.path.abspath(__file__))[0],conf_log)
	# défini la référence pour le calcul de la date du md5
	ref_md5 = datetime.datetime(2010, 1, 1)

	# initialisation du journal
	try:
		logger=init_logging(flogconf)
	except init_erreur as inst:
		logging.error("Erreur d'initialisation - "+ inst.valeur)
		sys.exit()

	# Connexion du signal de fermeture à la fonction de fermeture propre
	signal.signal(signal.SIGTERM, fermer_programme)
	signal.signal(signal.SIGINT, fermer_programme)
	signal.signal(signal.SIGHUP, fermer_programme)
	signal.signal(signal.SIGALRM, fermer_programme)
	signal.signal(signal.SIGABRT, fermer_programme)


	# initialise l'interception générale des erreurs non gérées
	sys.excepthook = attrape_exceptions

	logger.info(" ")     #intercalaire
	logger.info("Sauv.py version {}".format(version))
	logger.info("--------------- Début de la sauvegarde ------------------")

	# Lecture des arguments
	args=init_args()

	# Lecture des paramètres de sauvegarde
	try:
		config=init_para(os.path.join(os.path.split(os.path.abspath(__file__))[0], conf_sauv))
	except init_erreur as inst:
		logger.error("Erreur d'initialisation - "+ inst.valeur)
		sys.exit()

	#création de l'arbre des sauvegardes antérieures

	chemin_arbre=os.path.join(os.path.split(os.path.abspath(__file__))[0], f_arbre)
	arbre={}
	try:
		arbre=charge_arbre(chemin_arbre)
	except (SyntaxError,init_erreur) as exception:
		logger.warning(exception)


	# si l'argument ignore_verrou est demandé, supprime le verrou antérieur
	if args.ignore_verrou:
		deverrouille()

	# verrouille la sauvegarde pour éviter un second lancement
	if not verrouille():
		sys.exit()

	a_demonter=set()

	for sauv in config.sections():

		logger.info("""----------------------------------------------------------------------------------------------------\n
			-------------------------  Début de sauvegarde [{0}] --------------------------------------------------""".format(sauv))
		# créé une branche vide pour l'arbre si elle n'existe pas
		if not sauv in arbre:
			arbre[sauv]=[[], [], []]

		# regarde si une sauvegarde est nécessaire
		if pas_de_sauv(config[sauv],  arbre[sauv],  args.force):
			continue

		try:
			# vérifie la présence de la source et de la destination. la monte si besoin
			a_demonter.add(monte(0, config[sauv]))
			a_demonter.add(monte(1, config[sauv]))
		except OSError as exception:
			logger.info(exception)
			logger.warning("{}-La sauvegarde  est abandonnée, les répertoires ne sont pas accessibles".format(sauv))
			# saute à la sauvegarde suivante
			continue


		# compare l'arbre sauvegardé et celui détecté, retourne le meilleur
		arbre[sauv] = verifie_arbre(config[sauv], arbre[sauv])

			# Permet de sauter si le calcul de temps n'a pas pu être fait au précédent test
			# Saute la copie si l'arbre n'était  pas défini (test=faux) et période pas atteinte
		if pas_de_sauv(config[sauv],  arbre[sauv],  args.force):
			continue

		try:
			arbre[sauv][0].insert(0, copie(config[sauv], arbre[sauv]))
		except OSError as exception:
			logger.warning("{}-{}".format(sauv,exception))
			logger.warning("{}-La sauvegarde  a renvoyée une erreur".format(sauv))
			continue

		reduit_inode(arbre[sauv])

		try:
			arbre[sauv] = analyse_repertoire(config[sauv], arbre[sauv])
		except OSError as exception:
			logger.warning("{}-{}".format(sauv, exception))
			logger.warning("{}-La compression de la sauvegarde a renvoyée une erreur".format(sauv))
			continue

	demonte(a_demonter)

	try:
		sauv_arbre(chemin_arbre, arbre)
	except SyntaxError as exception:
		logger.warning(exception)

	deverrouille()
	logger.info("--------------- Fin de la sauvegarde ------------------")
#else:
#    logger=logging.getLogger("main.sub")
