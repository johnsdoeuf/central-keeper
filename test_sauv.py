import sauv
import unittest
import os
import configparser
import datetime
import shutil
import logging.config
import json
import subprocess
import glob
from pathlib import Path

def config_log():
	logging.config.dictConfig({
		"version": 1,
		"formatters": {
			"simple": {
				"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
			}
		},

		"handlers": {
			"console_handler": {
				"level": "DEBUG",
				"class": "logging.StreamHandler",
				"formatter": "simple"
			}
		},

		"loggers": {
			"main": {
				"handlers": ["console_handler"],
				"level": "DEBUG"
			}
		}
	})

	sauv.logger = logging.getLogger('main')
	sauv.logger.info("")
	sauv.logger.info("*************** Début du test unitaire *************")


def fin_log():
	sauv.logger.info("*************** Fin du test unitaire *************")
	sauv.logger = None


class Init_para(unittest.TestCase):
	fich = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'essaiconf.conf')

	def setUp(self):
		config_log()

	def tearDown(self):
		fin_log()
		try:
			os.remove(self.fich)
		except OSError:
			pass

	def test_fichier_absent(self):
		"""teste si l'absence du fichier ou le fichier vide renvoi une exception"""
		sauv.logger.info("test_fichier_absent")
		self.assertRaises(sauv.init_erreur, sauv.init_para,
						  os.path.join(os.path.split(__file__)[0], 'jytyjtyjtyjtyj.conf'))

	def test_fichier_vide(self):
		"""Si aucune sauvegarde n'est configurée"""

		with open(self.fich, mode='w') as file:
			file.write(' ')
		self.assertRaises(sauv.init_erreur, sauv.init_para, self.fich)

	def test_fichier_erroné(self):
		"""Si paramètre sans section"""

		with open(self.fich, mode='w') as file:
			file.write('PERIODE1=0.1')
		self.assertRaises(sauv.init_erreur, sauv.init_para, self.fich)

	def test_mauvais_format(self):
		"""teste si du texte est présent """

		with open(self.fich, 'w') as configfile:
			configfile.write("Bonjour")
		self.assertRaises(sauv.init_erreur, sauv.init_para, self.fich)

	def test_source(self):
		"""teste si la section contient une source et éjecte bien les sources invalides"""

		config = sauv.My_configparser()
		config['dessus'] = {sauv.dest.upper(): '/gg'}
		with open(self.fich, 'w') as configfile:
			config.write(configfile)
		del config['dessus']
		self.assertEqual(sauv.init_para(self.fich), config)

		config['dessus'] = {sauv.dest: '/gg', sauv.src: '-'}
		with open(self.fich, 'w') as configfile:
			config.write(configfile)
		del config['dessus']
		self.assertEqual(sauv.init_para(self.fich), config)

		config['dessus'] = {sauv.dest: '/gg', sauv.src: '/ggtr;-;/ffrttt'}
		with open(self.fich, 'w') as configfile:
			config.write(configfile)
		config['dessus'] = {sauv.dest: '/gg', sauv.src: '/ggtr;/ffrttt'}
		self.assertEqual(sauv.init_para(self.fich), config)

		config['dessus'] = {sauv.dest: '/gg', sauv.src: '-;-;-'}
		with open(self.fich, 'w') as configfile:
			config.write(configfile)
		del config['dessus']
		self.assertEqual(sauv.init_para(self.fich), config)

		config['dessus'] = {sauv.dest: '/dfgd', sauv.src: '/lll'}
		with open(self.fich, 'w') as configfile:
			config.write(configfile)
		self.assertEqual(sauv.init_para(self.fich), config)

	def test_destination(self):
		"""teste si la section contient une destination et conserve bien la config 'ref'"""

		config = sauv.My_configparser()
		config['dessus'] = {sauv.src: '/gg'}
		config['ref'] = {sauv.src: '/gg', sauv.dest: ' /rrr'}
		with open(self.fich, 'w') as configfile:
			config.write(configfile)
		del config['dessus']

		self.assertEqual(sauv.init_para(self.fich), config)

		config['ref'] = {sauv.src: '/gg', sauv.dest: ' /rrr'}
		config['dessus'] = {sauv.src: 'gg', sauv.dest: '    '}
		with open(self.fich, 'w') as configfile:
			config.write(configfile)
		del config['dessus']
		self.assertEqual(sauv.init_para(self.fich), config)

	def test_intervalle_num(self):
		"""teste si le paramètre per1 est bien un nombre"""

		config = sauv.My_configparser()
		for para in sauv.l_clenum:
			config['test'] = {para: 'tt', sauv.src: 'gg', sauv.dest: 'hgg'}
			with open(self.fich, 'w') as configfile:
				config.write(configfile)
			del config['test']
			self.assertEqual(sauv.init_para(self.fich), config)

	def test_validité_cle(self):
		"""teste si les clés non valide sont biens supprimées """

		config = sauv.My_configparser()

		config['test'] = {'eerr': 'tt', sauv.src: 'gg', sauv.dest: 'hgg'}
		with open(self.fich, 'w') as configfile:
			config.write(configfile)
		del config['test']['eerr']
		self.assertEqual(sauv.init_para(self.fich), config)

	def test_source_valide(self):
		"""Teste si la source est bien un chemin valide"""
		pass

	def test_destination_valide(self):
		"""Teste si la destination est bien un chemin valide"""
		pass

	def test_toutes_les_clés(self):
		"""Teste que les clés valides ne créées pas d'erreur"""

		config = sauv.My_configparser()
		config['KKK'] = {cle: '/gg' for cle in sauv.l_cle}
		a = 0.0
		for cle in sauv.l_clenum:
			a += 1
			config['KKK'][cle] = str(a)

		with open(self.fich, 'w') as configfile:
			config.write(configfile)

		ggggg = sauv.init_para(self.fich)
		self.assertEqual(config, ggggg)

	def test_sortie(self):
		"""teste si le résultat correspond avec deux sauvegardes"""

		config = sauv.My_configparser()
		config['test'] = {sauv.per1.upper(): '0.2', sauv.src: '/gg', sauv.dest: '/hgg'}
		config['Films'] = {sauv.src: '/gg', sauv.dest: '/hgg'}
		with open(self.fich, 'w') as configfile:
			config.write(configfile)
		self.assertEqual(config, sauv.init_para(self.fich))




class verifie_arbre(unittest.TestCase):
	fichconf = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'essaiconf.conf')
	repsauv = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'tmp_essai')
	arbre_null = [[], [], []]

	def setUp(self):
		config_log()
		# créé un fichier config
		self.config = sauv.My_configparser()
		self.config['dessus'] = {sauv.dest: self.repsauv}

	def tearDown(self):
		try:
			shutil.rmtree(self.repsauv)
		except OSError:
			pass

	def cree_rep(self, rep):
		"""fonction de création d'un répertoire"""
		os.makedirs(os.path.join(self.repsauv, rep), mode=0o777)

	def test_arbre_conforme(self):
		"""teste la sortie arbre"""
		arbre = [[], [], []]
		try:
			shutil.rmtree(self.repsauv)
		except OSError:
			pass

		for rep in ['2016-12-12 15-18_2_2000', '2017-01-02 15-12_1', '2016-12-20 15-50_1', '2017-01-02 15-50_1_45685']:
			# créé des répertoires
			self.cree_rep(rep)
			res = rep.split('_')
			# créé l'élément
			élém = sauv.rep_sauv(datetime.datetime.strptime(res[0], sauv.formatdate), os.path.join(self.repsauv, rep))
			élém.taille = 0
			élém.lnoeud = {}
			# créé l'arbre
			arbre[int(res[1]) - 1].append(élém)

		tri = lambda p: p.date
		arbre[0].sort(key=tri, reverse=True)
		sauv.ref_md5 = datetime.datetime(2010, 1, 1)

		self.assertEqual(sauv.verifie_arbre(self.config['dessus'], self.arbre_null), arbre)
		self.assertEqual(self.config['dessus'][sauv.md5], '45685')

	def test_arbre_pb_date(self):
		"""teste le comportement quand un niveau 2 apparait avec une date trop proche
			Le répertoire doit etre ignoré"""
		arbre = [[], [], []]
		try:
			shutil.rmtree(self.repsauv)
		except OSError:
			pass

		for rep in ['2016-12-12 15-18_2_2000', '2017-01-02 15-12_2', '2016-12-20 15-50_1', '2017-01-02 15-50_1_45685']:
			# créé des répertoires
			self.cree_rep(rep)
			res = rep.split('_')
			# créé l'élément
			élém = sauv.rep_sauv(datetime.datetime.strptime(res[0], sauv.formatdate), os.path.join(self.repsauv, rep))
			élém.taille = 0
			élém.lnoeud = {}
			# créé l'arbre
			if rep != '2016-12-20 15-50_1':
				arbre[int(res[1]) - 1].append(élém)

		tri = lambda p: p.date
		arbre[0].sort(key=tri, reverse=True)
		arbre[1].sort(key=tri, reverse=True)

		sauv.ref_md5 = datetime.datetime(2010, 1, 1)
		resultat = sauv.verifie_arbre(self.config['dessus'], self.arbre_null)
		self.assertEqual(resultat, arbre)

	def test_conservation_arbre(self):
		"""teste la sortie arbre"""
		arbre = [[], [], []]
		try:
			shutil.rmtree(self.repsauv)
		except OSError:
			pass

		for rep in ['2016-12-12 15-18_2_2000', '2017-01-02 15-12_1', '2016-12-20 15-50_1', '2017-01-02 15-50_1_45685']:
			# créé des répertoires
			self.cree_rep(rep)
			res = rep.split('_')
			# créé l'élément
			élém = sauv.rep_sauv(datetime.datetime.strptime(res[0], sauv.formatdate), os.path.join(self.repsauv, rep))
			# élém.taille = 0
			# élém.lnoeud = {}
			# créé l'arbre
			arbre[int(res[1]) - 1].append(élém)

		tri = lambda p: p.date
		arbre[0].sort(key=tri, reverse=True)
		sauv.ref_md5 = datetime.datetime(2010, 1, 1)

		self.assertEqual(sauv.verifie_arbre(self.config['dessus'], arbre), arbre)
		self.assertEqual(self.config['dessus'][sauv.md5], '45685')


	def test_date_nonconforme(self):
		"""teste le comportement avec des répertoires erronés (minutes >60)"""

		self.cree_rep('1_2017-01-02 15-62-53-555')
		self.assertEqual(sauv.verifie_arbre(self.config['dessus'], self.arbre_null), self.arbre_null)

	def test_niveau_nonconforme(self):
		"""teste le comportement avec des répertoires erronés (niveau inexistant)"""

		self.cree_rep('0_2018-01-02 15-02-53-555')
		self.cree_rep('4_2018-01-02 15-02-53-555')
		self.assertEqual(sauv.verifie_arbre(self.config['dessus'], self.arbre_null), self.arbre_null)

	def test_répertoire_nonconforme(self):
		"""teste le comportement avec des répertoires erronés (entête)"""

		self.cree_rep('1rtt')
		self.cree_rep('.1_2018-01-02 15-02-53-555')
		self.assertEqual(sauv.verifie_arbre(self.config['dessus'], self.arbre_null), self.arbre_null)

	def test_chemin_absent(self):
		"""teste si le chemin ne répond pas"""
		self.config['dessus'] = {sauv.dest: '/ertte/ttt'}
		self.assertEqual(sauv.verifie_arbre(self.config['dessus'], self.arbre_null), self.arbre_null)



class Init_log(unittest.TestCase):
	fichconf = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'essailog.conf')

	def setUp(self):
		config_log()

	def tearDown(self):
		try:
			os.remove(self.fichconf)
		except OSError:
			pass

	def test_fichier_erroné(self):
		"""si fichier de logging n'existe pas """
		self.assertEqual(type(sauv.init_logging("kkkkkkk")), logging.RootLogger)

	def test_importation(self):
		"""si la configuration n'est pas au format json """
		with open(self.fichconf, 'w') as configfile:
			configfile.write('{ffffff')
		self.assertRaises(sauv.init_erreur, sauv.init_logging, self.fichconf)

	def test_configuration(self):
		"""Si la configuration n'est pas accepté par le module logging"""
		with open(self.fichconf, 'w') as configfile:
			configfile.write(json.dumps({
				'version': 0,  # 0 au lieu de version 1
				'loggers': {
					'main': {
						'level': 'DEBUG',
					},}
			}))
		self.assertRaises(sauv.init_erreur, sauv.init_logging, self.fichconf)

		with open(self.fichconf, 'w') as configfile:
			configfile.write(json.dumps({
				'version': 1,
				'loggers': ['main', 'level']
			}))
		self.assertRaises(sauv.init_erreur, sauv.init_logging, self.fichconf)

	def test_mot_clé(self):
		"""Si la configuration ne contient pas 'logger'"""

		with open(self.fichconf, 'w') as configfile:
			configfile.write(json.dumps({
				'version': 1,
				'logers': {  # erreur sur la clé
					'main': {
						'level': 'DEBUG',
					},}
			}))
		self.assertRaises(sauv.init_erreur, sauv.init_logging, self.fichconf)

	def test_handlers(self):
		"""Si la configuration ne contient pas de handlers"""

		with open(self.fichconf, 'w') as configfile:
			configfile.write(json.dumps({
				'version': 1,
				'loggers': {
					'main': {
						'level': 'DEBUG',
					},}
			}))
		self.assertRaises(sauv.init_erreur, sauv.init_logging, self.fichconf)


class Verrou(unittest.TestCase):
	fichverrou = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'essai.lock')

	def setUp(self):
		config_log()
		try:
			os.remove(self.fichverrou)
		except OSError:
			pass

	def tearDown(self):
		try:
			os.remove(self.fichverrou)
		except OSError:
			pass

	def test_fonctionnel(self):
		"""test fonctionnel de verrouille puis déverrouille"""

		self.assertTrue(sauv.verrouille(self.fichverrou))
		self.assertTrue(os.path.exists(self.fichverrou))
		maintenant = (datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds() - 2 * 60 * 60 - 10
		self.assertLess(maintenant, os.stat(self.fichverrou).st_mtime)

		sauv.deverrouille(self.fichverrou)
		self.assertFalse(os.path.exists(self.fichverrou))

	def test_verrou_présent(self):
		"""test du comportement si un fichier lock existe déjà"""
		# créé un fichier
		with open(self.fichverrou, 'w', encoding='utf8') as f:
			f.write("Lancement d'une sauvegarde le {0}".format(datetime.datetime.now()))
		# modifie sa date (4 heures en arrière
		dat = (datetime.datetime.now() - datetime.timedelta(days=0, hours=4, minutes=3, seconds=12)).strftime(
			'%Y%m%d%H%M.%S')
		commande = "touch -t " + dat + " " + self.fichverrou
		subprocess.call(commande, shell=True)
		self.assertFalse(sauv.verrouille(self.fichverrou))

		dat = (datetime.datetime.now() - datetime.timedelta(days=0, hours=21, minutes=50, seconds=12)).strftime(
			'%Y%m%d%H%M.%S')
		commande = "touch -t " + dat + " " + self.fichverrou
		subprocess.call(commande, shell=True)
		self.assertFalse(sauv.verrouille(self.fichverrou))
		#
		maintenant = (datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds() - 2 * 60 * 60 - 10
		dat = (datetime.datetime.now() - datetime.timedelta(days=1, hours=2, minutes=3, seconds=12)).strftime(
			'%Y%m%d%H%M.%S')
		commande = "touch -t " + dat + " " + self.fichverrou
		subprocess.call(commande, shell=True)
		self.assertTrue(sauv.verrouille(self.fichverrou))

		# test si un nouveau verrou a bien été créé
		self.assertLess(maintenant, os.stat(self.fichverrou).st_mtime)

	def test_deverouille_bloqué(self):
		"""test deverrouille avec fichier ouvert"""
		with open(self.fichverrou, 'w', encoding='utf8') as f:
			f.write("Lancement d'une sauvegarde le {0}".format(datetime.datetime.now()))
			sauv.deverrouille(self.fichverrou)
			self.assertFalse(os.path.exists(self.fichverrou))


class monte(unittest.TestCase):
	repsauv = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'Xedrg5g6')

	def setUp(self):
		config_log()

	def tearDown(self):
		fin_log()
		try:
			shutil.rmtree(self.repsauv)
		except OSError:
			pass

	def test_sens1(self):
		""" teste qu'il n'y a pas de problème dans le sens destination """
		config = sauv.My_configparser()

		config['test'] = {sauv.dest: self.repsauv}
		os.makedirs(os.path.join(self.repsauv, 'non_vide'), mode=0o777)
		self.assertEqual(sauv.monte(1, config['test']), None)

	def test_sens0(self):
		""" teste qu'il n'y a pas de problème dans le sens source """
		config = sauv.My_configparser()

		config['test'] = {sauv.src: self.repsauv}
		os.makedirs(os.path.join(self.repsauv, 'non_vide'), mode=0o777)
		self.assertEqual(sauv.monte(0, config['test']), None)

	def test_sens2(self):
		""" teste avec un sens erroné """
		config = sauv.My_configparser()

		config['test'] = {sauv.dest: self.repsauv}
		os.makedirs(os.path.join(self.repsauv, 'non_vide'), mode=0o777)
		self.assertRaises(ValueError, sauv.monte, 2, config['test'])

	def test_source_inexistante(self):
		""" teste si la source n'existe pas"""
		config = sauv.My_configparser()

		config['test'] = {sauv.src: self.repsauv}

		self.assertRaises(OSError, sauv.monte, 0, config['test'])

	def test_source_vide(self):
		""" teste si la source est vide """
		config = sauv.My_configparser()

		config['test'] = {sauv.src: self.repsauv}
		os.makedirs(self.repsauv, mode=0o777)
		self.assertRaises(OSError, sauv.monte, 0, config['test'])

	def test_seconde_source_OK(self):
		""" teste si seulement la seconde source est bonne """
		config = sauv.My_configparser()

		config['test'] = {sauv.src: "/rep_bibon;{}".format(self.repsauv)}
		os.makedirs(os.path.join(self.repsauv, 'non_vide'), mode=0o777)
		self.assertEqual(sauv.monte(0, config['test']), None)

	def test_avec_montage(self):
		""" teste si seulement la seconde source est bonne """
		config = sauv.My_configparser()

		config['test'] = {
			sauv.src: "/rep_bibon;{}".format(self.repsauv),
			sauv.mntsrc: "mkdir {}".format(os.path.join(self.repsauv, 'non_vide')),
			sauv.umntsrc: "retour_commande"
		}
		os.makedirs(self.repsauv, mode=0o777)
		self.assertEqual(sauv.monte(0, config['test']), "retour_commande")

	def test_sources_fausses(self):
		""" teste si toules sources ne fonctionnent pas"""

		config = sauv.My_configparser()
		config['test'] = {sauv.src: '/ezrte/bidon;/test/bidon'}

		self.assertRaises(OSError, sauv.monte, 0, config['test'])

	def test_sources_fausses_et_montage_faux(self):
		""" teste si toules sources ne fonctionnent pas"""

		config = sauv.My_configparser()
		config['test'] = {
			sauv.dest: '/ezrte/bidon;/test/bidon',
			sauv.mntsrc: 'cmd_bidon'}

		self.assertRaises(OSError, sauv.monte, 1, config['test'])

	def test_sources_fausses_et_demontage_faux(self):
		""" teste si toules sources ne fonctionnent pas"""

		config = sauv.My_configparser()
		config['test'] = {
			sauv.src: '/ezrte/bidon;/test/bidon',
			sauv.mntsrc: 'cmd_bidon',
			sauv.umntsrc: 'cmd_bidon'}
		self.assertRaises(OSError, sauv.monte, 0, config['test'])


class Copie(unittest.TestCase):
	racine = os.path.split(os.path.abspath(__file__))[0]
	source = os.path.join(racine, 'rep_essai/')
	dest = os.path.join(racine, 'sauvegarde')

	def setUp(self):
		config_log()
		try:
			os.makedirs(self.source)
			os.makedirs(self.dest)
		except OSError:
			pass

	def tearDown(self):
		try:
			shutil.rmtree(self.source)
			shutil.rmtree(os.path.join(os.path.split(__file__)[0], 'sauvegarde'))
		except OSError:
			pass

	def test_source_absente(self):
		"""teste source absente"""

		arbre = [[], [], []]
		config = configparser.ConfigParser()
		config.read_dict({'sauv': {sauv.src: '/dddfffff/ffrfff/erer', sauv.dest: '/'}})

		self.assertRaises(OSError, sauv.copie, config['sauv'], arbre)

	def test_destination_absente(self):
		"""teste destination absente"""

		arbre = [[], [], []]
		config = {sauv.src: self.source, sauv.dest: self.dest}
		shutil.rmtree(os.path.join(os.path.split(__file__)[0], 'sauvegarde'))

		self.assertRaises(OSError, sauv.copie, config, arbre)

	def test_reference_absente(self):
		"""teste reference_absente"""
		source2 = os.path.join(os.path.split(self.dest)[0], 'essai2')

		config = configparser.ConfigParser()
		config.read_dict({'sauv': {sauv.src: self.source, sauv.dest: self.dest}})

		arbre = [[sauv.rep_sauv(datetime.datetime(2017, 5, 3), source2)], [], []]

		ret = sauv.copie(config['sauv'], arbre)
		self.assertTrue(ret.chemin[0:-12], (self.dest + datetime.datetime.now().strftime(sauv.formatdate))[0:-12])
		self.assertEqual(ret.date.day, datetime.datetime.now().day)

	#        self.assertEqual( sauv.copie (config, arbre) ,  None )

	def test_espace_dans_chemin(self):
		"""teste si le programme supporte les espaces et test la copie"""
		dest = os.path.join(self.dest, 'essai 2')
		source = os.path.join(self.source, 'Sour ce')
		fich = os.path.join(source, 'essai.txt')
		try:
			os.makedirs(source)
			os.makedirs(dest)
			with open(fich, 'w', encoding='utf8') as f:
				f.write("Lancement d'une sauvegarde le ")
		except OSError:
			pass

		arbre = [[], [], []]
		config = {sauv.src: source, sauv.dest: dest}

		# vérifie la sortie de la fonction
		ret = sauv.copie(config, arbre)
		self.assertTrue(ret.chemin[0:-12], (self.dest + datetime.datetime.now().strftime(sauv.formatdate))[0:-12])
		self.assertEqual(ret.date.day, datetime.datetime.now().day)
		# vérifie la taille
		arbre[0].insert(0,ret)
		self.assertEqual(sauv.taille_arbre(arbre), 30)

	def test_copie_avec_ref(self):
		"""teste la copie avec lien en dur"""
		dest = os.path.join(self.dest, 'essai 2')
		source = os.path.join(self.source, 'Sour ce/')
		ref = os.path.join(self.dest, 'ESSAI3')
		fich = os.path.join(source, 'essai.txt')
		fichref = os.path.join(ref, 'essai.txt')
		try:
			os.makedirs(source)
			os.makedirs(dest)
			os.makedirs(ref)
			with open(fich, 'w', encoding='utf8') as f:
				f.write("Lancement d'une sauvegarde le ")
			shutil.copyfile(fich, fichref)
		except OSError:
			pass

		rsauv = sauv.rep_sauv(datetime.datetime(2017, 5, 3), ref)
		rsauv.analyse()

		arbre = [[rsauv], [], []]
		config = {sauv.src: source, sauv.dest: dest}
		# Vérifie le retour de la fonction
		ret = sauv.copie(config, arbre)
		self.assertTrue(ret.chemin[0:-12], (self.dest + datetime.datetime.now().strftime(sauv.formatdate))[0:-12])
		self.assertEqual(ret.date.day, datetime.datetime.now().day)
		#        self.assertEqual( sauv.copie (config, arbre) ,  sauv.rep_sauv(datetime.datetime(2017, 5, 3), ref) )
		# Vérifie que le fichier est bien copié
		self.assertTrue(os.path.exists(glob.glob(os.path.join(dest, '*/essai.txt'))[0]))
		# Vérifie que la taille est bien celle d'un seul fichier'
		self.assertEqual(sauv.taille_arbre(arbre), 30)

	def test_parametre_erronées(self):
		"""Essai avec des paramètres erronées"""
		arbre = [[], [], []]
		config = {sauv.src: self.source, sauv.dest: self.dest, sauv.para: '--ogfggthth'}
		# paramètre long inexistant
		self.assertRaises(OSError, sauv.copie, config, arbre)

		config = {sauv.src: self.source, sauv.dest: self.dest, sauv.para: '-Z'}
		# paramètre inexistant
		self.assertRaises(OSError, sauv.copie, config, arbre)


class demonte(unittest.TestCase):
	def setUp(self):
		config_log()

	def test_set_vide(self):
		"""Essai avec un set de données vide"""
		a_dem = set()
		sauv.demonte(a_dem)

	def test_set_entier(self):
		"""Essai avec un set contenant un entier"""
		a_dem = {45}
		sauv.demonte(a_dem)

	def test_entier(self):
		"""Essai avec pour paramètre un entier"""
		a_dem = 45
		sauv.demonte(a_dem)

	def test_commande_fausse(self):
		"""Essai avec une commande erronée"""
		a_dem = {"ddfhfgh"}
		sauv.demonte(a_dem)

	def test_commande_bonne(self):
		"""Essai avec une commande existante: ls"""
		a_dem = {"ls"}
		sauv.demonte(a_dem)

	def test_null(self):
		"""Essai avec une valeur null"""
		a_dem = {None}
		sauv.demonte(a_dem)


class commande_ext(unittest.TestCase):
	def setUp(self):
		config_log()

	def test_chaine(self):
		"""teste si une chaine est transmise au lieu d'une liste de paramètres"""
		self.assertRaises(SyntaxError, sauv.commande_ext, "ls", False)

	def test_liste(self):
		"""teste si une simple liste est transmise au lieu d'une liste de paramètres"""
		sauv.commande_ext(["ls"], False)

	def test_liste_unique(self):
		"""teste le passage de paramètres via une chaîne unique"""
		self.assertRaises(OSError, sauv.commande_ext, ["ls -l"], False)

	def test_liste_multiple(self):
		"""teste le passage de paramètres via une chaîne multiple"""
		sauv.commande_ext(["ls", "-l"], False)

	def test_none(self):
		"""teste avec un set de None"""
		self.assertRaises(SyntaxError, sauv.commande_ext, None, False)

	def test_chaine_vide(self):
		"""teste avec une chaine vide"""
		self.assertRaises(SyntaxError, sauv.commande_ext, "", False)


class charge_arbre(unittest.TestCase):
	fich = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'essai.hist')

	def setUp(self):
		config_log()

	def tearDown(self):
		try:
			os.remove(self.fich)
		except OSError:
			pass

	def test_fichier_vide(self):
		"""teste avec un fichier vide"""
		try:
			with open(self.fich, 'w', encoding='utf8') as f:
				f.write("")
		except OSError:
			pass

		self.assertRaises(SyntaxError, sauv.charge_arbre, self.fich)

	def test_fichier_inexistant(self):
		"""teste avec unchemin inexistant"""

		self.assertRaises(sauv.init_erreur, sauv.charge_arbre, '/fsddfsdf/dfsdf/sdfsdf.f')

	def test_format_non_json(self):
		"""teste avec un fichier vide"""
		try:
			with open(self.fich, 'w', encoding='utf8') as f:
				f.write("{ ertt[hfghf }dfgrefg]")
		except OSError:
			pass

		self.assertRaises(SyntaxError, sauv.charge_arbre, self.fich)

	def test_non_dictionnaire(self):
		"""teste si premier niveau liste"""
		val = json.dumps(["sdfgsdfgs"])
		try:
			with open(self.fich, 'w', encoding='utf8') as f:
				f.write(val)
		except OSError:
			pass

		self.assertRaises(SyntaxError, sauv.charge_arbre, self.fich)

	def test_taille_liste(self):
		"""teste avec une liste plus longue"""
		test = sauv.rep_sauv(datetime.datetime(2000, 1, 1), "/home/ghhhjhjh.n")
		arbre = {'sauv': [[test, test], [5], [], [test, test]]}
		val = sauv.my_encoder().encode(arbre)
		try:
			with open(self.fich, 'w', encoding='utf8') as f:
				f.write(val)
		except OSError:
			pass

		self.assertRaises(SyntaxError, sauv.charge_arbre, self.fich)

	def test_contenu(self):
		"""teste de la correspondance résultat"""
		test = sauv.rep_sauv(datetime.datetime(2000, 1, 1), "/home/ghhhjhjh.n")
		arbre = {'sauv': [[test, test], [5], []]}
		val = sauv.my_encoder().encode(arbre)
		try:
			with open(self.fich, 'w', encoding='utf8') as f:
				f.write(val)
		except OSError:
			pass

		self.assertRaises(SyntaxError, sauv.charge_arbre, self.fich)

	def test_fonctionnel(self):
		"""teste de la correspondance résultat"""
		test = sauv.rep_sauv(datetime.datetime(2000, 1, 1), "/home/ghhhjhjh.n")
		test.taille = 485121
		test.lnoeud = {'1548255':4548,'45245':452,'45':0}
		arbre = {'sauv': [[test, test], [test], []]}
		val = sauv.my_encoder().encode(arbre)
		try:
			with open(self.fich, 'w', encoding='utf8') as f:
				f.write(val)
		except OSError:
			pass

		res_arbre = sauv.charge_arbre(self.fich)
		self.assertEqual(res_arbre, arbre)

	def test_avec_null(self):
		"""teste avec 'Home_jeux': null"""

		val = '{"Home_jeux": null}'
		try:
			with open(self.fich, 'w', encoding='utf8') as f:
				f.write(val)
		except OSError:
			pass

		self.assertRaises(SyntaxError, sauv.charge_arbre, self.fich)


class rep_sauv(unittest.TestCase):

	repsauv = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'tmp_essai')
	repsauv2 = Path(repsauv)

	def setUp(self):
		config_log()
		self.sauv = 'clef'
		try:
			os.makedirs(self.repsauv, mode=0o777)
		except OSError:
			pass


	def tearDown(self):
		try:
			shutil.rmtree(self.repsauv)
		except OSError:
			pass

	def test_fonctionnel(self):
		""" teste si le résultat est conforme dans une situation normale """

		os.makedirs(os.path.join(self.repsauv, 'srep'), mode=0o777)
		liste_fichier = ["srep/ffffé", "h12222"]

		for fich in liste_fichier:
			# créé le fichier

			fpremier = os.path.join(self.repsauv, fich)
			# créé le fichier source
			with open(fpremier, 'w') as configfile:
				configfile.write('ffffff')

		info = [os.stat(os.path.join(self.repsauv, f)) for f in liste_fichier]

		resultat = sauv.rep_sauv(datetime.datetime(2000, 1, 1), self.repsauv)
		resultat.taille = 12
		resultat.lnoeud = {str(f.st_ino):f.st_size for f in info}

		resultat2 = sauv.rep_sauv(datetime.datetime(2000, 1, 1), self.repsauv)
		resultat2.analyse()

		self.assertEqual(resultat2, resultat)

	def test_chemin_inexistant(self):

		resultat = sauv.rep_sauv(datetime.datetime(2000, 1, 1), "/dfdf/dfff")
		self.assertRaises(sauv.init_erreur,resultat.analyse)


	def test_vide(self):
		""" teste si le résultat est conforme dans une situation normale """

		os.makedirs(os.path.join(self.repsauv, 'srep'), mode=0o777)

		resultat = sauv.rep_sauv(datetime.datetime(2000, 1, 1), self.repsauv)
		resultat.taille = 0
		resultat.lnoeud = {}

		resultat2 = sauv.rep_sauv(datetime.datetime(2000, 1, 1), self.repsauv)
		resultat2.analyse()

		self.assertEqual(resultat2, resultat)

	def test_analyse_fichiers_lié(self):
		"""teste le résultat de la taille avec deux fichiers liés"""
		liste_rep = ["ffffé", "h12222","rrt"]
		premier = True

		élément = []
		for rep in liste_rep:
			# créé le répertoire
			try:
				os.makedirs(os.path.join(self.repsauv, rep), mode=0o777)
			except OSError:
				pass

			if premier:
				fpremier = os.path.join(self.repsauv, rep, "fichier.txt")
				# créé le fichier source
				with open(fpremier, 'w') as configfile:
					configfile.write('ffffff')
				premier = False

			else:
				# créé un lien dur
				os.link(fpremier, os.path.join(self.repsauv, rep, "identique.txt"))

			#ajoute un fichier différent de 4 caractères
			fpremier = os.path.join(self.repsauv, rep, "différent.txt")
			# créé le fichier source
			with open(fpremier, 'w') as configfile:
				configfile.write('ffqq')

			rsauv = sauv.rep_sauv(datetime.datetime(2005, 12, 30), os.path.join(self.repsauv, rep))
			élément.append(rsauv)
			rsauv.analyse()

		arbre = [élément, [], []]
		sauv.reduit_inode(arbre)

		# regarde la taille totale
		self.assertEqual(sauv.taille_arbre(arbre), 18)
		self.assertEqual(arbre[0][0].taille, 6+4)
		self.assertEqual(arbre[0][1].taille, 4)

class reduit_inode(unittest.TestCase):
	def setUp(self):
		config_log()

	def tearDown(self):
		pass

	def test_fonctionnel(self):
		"""teste de la correspondance résultat"""

		test = sauv.rep_sauv(datetime.datetime(2005, 1, 1), "/home/ghhhjhjh.n")
		test.lnoeud = {'45':50,'46':20,'47':10}

		test2 = sauv.rep_sauv(datetime.datetime(2006, 1, 1), "/home/ghhhjhjh.n")
		test2.lnoeud = {'46': 20, '47': 10}


		test3 = sauv.rep_sauv(datetime.datetime(2006, 3, 1), "/home/ghhhjhjh.n")
		test3.lnoeud = { '47': 10,'48':5}

		resultat = [[test3, test2], [test],[]]


		test21 = sauv.rep_sauv(datetime.datetime(2005, 1, 1), "/home/ghhhjhjh.n")
		test21.lnoeud = {}
		test21.taille = 50

		test22 = sauv.rep_sauv(datetime.datetime(2006, 1, 1), "/home/ghhhjhjh.n")
		test22.lnoeud = {}
		test22.taille = 20

		test23 = sauv.rep_sauv(datetime.datetime(2006, 3, 1), "/home/ghhhjhjh.n")
		test23.lnoeud = { '47': 10,'48':5}

		resultat2 =  [[test23, test22], [test21],[]]

		sauv.reduit_inode(resultat)
		self.assertEqual(resultat2, resultat)

	def test_fonctionnel2(self):
		"""teste de la correspondance résultat avec arbre déjà réduit"""

		test = sauv.rep_sauv(datetime.datetime(2005, 1, 1), "/home/ghhhjhjh.n")
		test.lnoeud = {}
		test.taille = 50

		test2 = sauv.rep_sauv(datetime.datetime(2006, 1, 1), "/home/ghhhjhjh.n")
		test2.lnoeud = {}
		test2.taille = 20

		test3 = sauv.rep_sauv(datetime.datetime(2006, 3, 1), "/home/ghhhjhjh.n")
		test3.lnoeud = {'47': 10, '48': 5}

		resultat =  [[test3, test2], [test], []]

		test21 = sauv.rep_sauv(datetime.datetime(2005, 1, 1), "/home/ghhhjhjh.n")
		test21.lnoeud = {}
		test21.taille = 50

		test22 = sauv.rep_sauv(datetime.datetime(2006, 1, 1), "/home/ghhhjhjh.n")
		test22.lnoeud = {}
		test22.taille = 20

		test23 = sauv.rep_sauv(datetime.datetime(2006, 3, 1), "/home/ghhhjhjh.n")
		test23.lnoeud = {'47': 10, '48': 5}

		resultat2 = [[test23, test22], [test21], []]

		sauv.reduit_inode(resultat)
		self.assertEqual(resultat2, resultat)


	def test_mauvais_ordre(self):
		"""teste si l'ordre n'est pas respecté"""


		test = sauv.rep_sauv(datetime.datetime(2005, 1, 1), "/home/ghhhjhjh.n")
		test.lnoeud = {'45': 50, '46': 20, '47': 10}

		test2 = sauv.rep_sauv(datetime.datetime(2004, 1, 1), "/home/ghhhjhjh.n")
		test2.lnoeud = {'46': 20, '47': 10}

		test3 = sauv.rep_sauv(datetime.datetime(2006, 3, 1), "/home/ghhhjhjh.n")
		test3.lnoeud = {'47': 10, '48': 5}

		resultat =  [[test3, test2], [test], []]

		self.assertRaises(SyntaxError, sauv.reduit_inode, resultat)



class sauv_arbre(unittest.TestCase):
	fich = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'essai.hist')

	def setUp(self):
		config_log()

	def tearDown(self):
		try:
			os.remove(self.fich)
		except OSError:
			pass

	def test_fonctionnel(self):
		"""teste de la correspondance résultat"""
		test = sauv.rep_sauv(datetime.datetime(2000, 1, 1), "/home/ghhhjhjh.n")
		arbre = {'sauv': [[test, test], [test], []]}
		sauv.sauv_arbre(self.fich, arbre)

		self.assertEqual(sauv.charge_arbre(self.fich), arbre)

	def test_mauvais_chemin(self):
		"""teste si le chemin d'accès n'existe pas"""
		arbre = {'ert': 56}
		self.fich = '/tmp/erergererg/ttgh4tg/zerze.f'
		self.assertRaises(SyntaxError, sauv.sauv_arbre, self.fich, arbre)

	def test_arbre_vide(self):
		"""teste si l'arbre ne contient rien"""

		self.assertRaises(SyntaxError, sauv.sauv_arbre, self.fich, None)


class pas_de_sauv(unittest.TestCase):
	def setUp(self):
		config_log()

	def test_fonctionnel(self):
		"""test si renvoi bien true si les conditions sont réunies"""
		config = sauv.My_configparser()
		config['sauv'] = {}
		config['sauv'][sauv.per1] = '4'
		rsauv = sauv.rep_sauv(datetime.datetime.now() - datetime.timedelta(hours=5), '/rerg/gdfdfhdtuip')
		arbre = [[rsauv, rsauv], [], []]
		force = False
		self.assertTrue(sauv.pas_de_sauv(config['sauv'], arbre, force))

	def test_fonctionnel2(self):
		"""test si autorise si la dernière sauvegarde est lointaine"""
		config = sauv.My_configparser()
		config['sauv'] = {}
		config['sauv'][sauv.per1] = '4'
		rsauv = sauv.rep_sauv(datetime.datetime.now() - datetime.timedelta(days=5), '/rerg/gdfdfhdtuip')
		arbre = [[rsauv, rsauv], [], []]
		force = False
		self.assertFalse(sauv.pas_de_sauv(config['sauv'], arbre, force))

	def test_fonctionnel3(self):
		"""teste si trouve bien la date de la sauvegarde de rang 2"""
		config = sauv.My_configparser()
		config['sauv'] = {}
		config['sauv'][sauv.per1] = '4'
		rsauv = sauv.rep_sauv(datetime.datetime.now() - datetime.timedelta(days=3), '/rerg/gdfdfhdtuip')
		arbre = [[], [rsauv], []]
		force = False
		self.assertTrue(sauv.pas_de_sauv(config['sauv'], arbre, force))

	def test_fonctionnel4(self):
		"""teste si trouve bien la date de la sauvegarde de rang 2"""
		config = sauv.My_configparser()
		config['sauv'] = {}
		config['sauv'][sauv.per1] = '4'
		rsauv = sauv.rep_sauv(datetime.datetime.now() - datetime.timedelta(days=3), '/rerg/gdfdfhdtuip')
		arbre = [[], [], [rsauv]]
		force = False
		self.assertTrue(sauv.pas_de_sauv(config['sauv'], arbre, force))

	def test_sans_per1(self):
		"""test si renvoi bien false si periode1 n'existe pas """
		config = sauv.My_configparser()
		config['sauv'] = {}
		config['sauv'][sauv.dest] = '4'
		rsauv = sauv.rep_sauv(datetime.datetime.now() - datetime.timedelta(hours=5), '/rerg/gdfdfhdtuip')
		arbre = [[rsauv, rsauv], [], []]
		force = False
		self.assertFalse(sauv.pas_de_sauv(config['sauv'], arbre, force))

	def test_sans_arbre(self):
		"""test si renvoi bien false si l'arbre est vide"""
		config = sauv.My_configparser()
		config['sauv'] = {}
		config['sauv'][sauv.per1] = '4'

		arbre = [[], [], []]
		force = False
		self.assertFalse(sauv.pas_de_sauv(config['sauv'], arbre, force))

	def test_avec_force(self):
		"""test si renvoi bien false quand force est activé"""
		config = sauv.My_configparser()
		config['sauv'] = {}
		config['sauv'][sauv.per1] = '4'
		rsauv = sauv.rep_sauv(datetime.datetime.now() - datetime.timedelta(hours=5), '/rerg/gdfdfhdtuip')
		arbre = [[rsauv, rsauv], [], []]
		force = True
		self.assertFalse(sauv.pas_de_sauv(config['sauv'], arbre, force))

class fusion_rep(unittest.TestCase):
	rep = os.path.join(os.path.split(os.path.abspath(__file__))[0], "TruxfgHHHfg45")


	def setUp(self):
		config_log()
		try:
			os.makedirs(self.rep)
		except OSError:
			pass


	def tearDown(self):
		try:
			shutil.rmtree(self.rep)
		except OSError:
			pass


	def test_fonctionnel(self):
		"""teste si la source disparait et les fichiers se retouvent bien dans dst  """

		test  = ['source/video/fich1.txt','source/video/fich2.txt','destination/video/fich1.txt','destination/video/fich3.txt']
		l_rep = [Path(self.rep, rep) for rep in test]
		for prep in l_rep:
			prep.parent.mkdir(parents=True, exist_ok=True)
			with prep.open('w', encoding='utf8') as f:
				# ecrit le string de test correspondant
				f.write(test[l_rep.index(prep)])

		sauv.fusion_rep(Path(self.rep,'source'),Path(self.rep,'destination'))

		# verifie l'effacement  de la source
		self.assertFalse(l_rep[0].parent.parent.exists())
		# verifie que les 3 fichiers existent
		self.assertTrue(l_rep[2].with_name('fich2.txt').exists())
		self.assertTrue(l_rep[3].exists())
		self.assertTrue(l_rep[2].exists())
		# regarde si le contenu est bien celui provenant de la source (écrasement)
		with l_rep[2].open('r', encoding='utf8') as f:
			self.assertTrue(f.read() == test[0] )

	def test_fonctionnel2(self):
		"""teste si la source disparait et les fichiers se retouvent bien dans dst  """

		test  = ['source/video/fich1.txt','source/fich2.txt','source/tt/hh/fich4.pps','destination/video/fich1.txt','destination/video/fich3.txt','destination/video/JJ/fich5.txt']
		l_rep = [Path(self.rep, rep) for rep in test]
		for prep in l_rep:
			prep.parent.mkdir(parents=True, exist_ok=True)
			with prep.open('w', encoding='utf8') as f:
				# ecrit le string de test correspondant
				f.write(test[l_rep.index(prep)])

		sauv.fusion_rep(Path(self.rep,'source'),Path(self.rep,'destination'))

		# verifie l'effacement  de la source
		self.assertFalse(l_rep[0].parent.parent.exists())
		# verifie que les 3 fichiers existent
		self.assertTrue(l_rep[3].parent.with_name('fich2.txt').exists())
		self.assertTrue(l_rep[4].exists())
		self.assertTrue(l_rep[3].exists())
		self.assertTrue(l_rep[5].exists())
		# regarde si le contenu est bien celui provenant de la source (écrasement)
		with l_rep[3].open('r', encoding='utf8') as f:
			self.assertTrue(f.read() == test[0] )

	def test_source_non_path(self):
		"""teste si renvoie bien valuerror si la source n'est pas un path"""

		test = ['dest/vidéo/fich1.txt']
		l_rep = [Path(self.rep, rep) for rep in test]
		for prep in l_rep:
			prep.parent.mkdir(parents=True, exist_ok=True)
			with prep.open('w', encoding='utf8') as f:
				# ecrit le string de test correspondant
				f.write('test')

		self.assertRaises(ValueError, sauv.fusion_rep, 'source', Path(self.rep, 'dest'))


	def test_dest_non_path(self):
		"""teste si renvoie bien valuerror si la source n'est pas un path"""

		test = ['dest/vidéo/fich1.txt']
		l_rep = [Path(self.rep, rep) for rep in test]
		for prep in l_rep:
			prep.parent.mkdir(parents=True, exist_ok=True)
			with prep.open('w', encoding='utf8') as f:
				f.write('test')

		self.assertRaises(ValueError, sauv.fusion_rep, Path(self.rep, 'dest'), 'source')

	def test_source_inexistante(self):
		"""teste si renvoit bien FileNotFoundError lorsque la source n'existe pas  """

		test = ['dest/vidéo/fich1']
		l_rep = [Path(self.rep, rep) for rep in test]
		for prep in l_rep:
			prep.parent.mkdir(parents=True, exist_ok=True)
			with prep.open('w', encoding='utf8') as f:
				f.write('test')

		self.assertRaises(FileNotFoundError, sauv.fusion_rep, Path(self.rep, 'source'), Path(self.rep, 'dest'))

	def test_destination_inexistante(self):
		"""teste si créé bien la destination si elle n'existe pas  """

		test = ['source/vidéo/fich1', 'source/musique/fich1']
		l_rep = [Path(self.rep, rep) for rep in test]
		for prep in l_rep:
			prep.parent.mkdir(parents=True, exist_ok=True)
			with prep.open('w', encoding='utf8') as f:
				f.write('test')

		sauv.fusion_rep(Path(self.rep, 'source'), Path(self.rep, 'destination'))
		# verifie l'effacement  de la source
		self.assertFalse(l_rep[0].parent.parent.exists())
		# verifie que les 2 fichiers existent dans la destination
		self.assertTrue(( Path(self.rep, 'destination') / l_rep[0].parts[-2] / l_rep[0].parts[-1] ).exists())
		self.assertTrue(( Path(self.rep, 'destination') / l_rep[1].parts[-2] / l_rep[1].parts[-1] ).exists())
'''
	def test_erreur_fichier(self):
		"""verifie que renvoie bien une erreur OSError """

		test  = ['source/video/fich1.txt','destination/video/fich1.txt']
		l_rep = [Path(self.rep, rep) for rep in test]
		for prep in l_rep:
			prep.parent.mkdir(parents=True, exist_ok=True)
			with prep.open('w', encoding='utf8') as f:
				# ecrit le string de test correspondant
				f.write(test[l_rep.index(prep)])

		# Met en lecture seule
		#l_rep[1].chmod(0o444)

		# verifie l'effacement  de la source
		self.assertRaises(OSError, sauv.fusion_rep, Path(self.rep,'source'), Path(self.rep,'destination'))
'''
class regroupe(unittest.TestCase):
	rep = os.path.join(os.path.split(os.path.abspath(__file__))[0], "AZEezrenn568ht")

	def setUp(self):
		config_log()
		try:
			os.makedirs(self.rep)
		except OSError:
			pass

	def tearDown(self):
		try:
			shutil.rmtree(self.rep)
		except OSError:
			pass

	def test_fonctionnel(self):
		"""teste si renvoi bien l'arbre réduit et le passage au niveau 2 du dernier repertoire """

		cons = 1
		per_suiv = 10
		now = datetime.datetime.now()

		arbre = []
		arbre_origine = []
		modèle = []
		test = [('er_1', 5), ('tyëu_1', 23), ('kkk_1', 25), ('dfg_1', 40)]

		for fichier in test:
			try:
				os.mkdir(os.path.join(self.rep, fichier[0]))
				os.mkdir(os.path.join(self.rep, fichier[0], 'musique'))
			except OSError:
				logger.error("problème de création de fichier")

			rsauv = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			arbre.append(rsauv)
			# fait une copie de arbre
			rsauv2 = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			arbre_origine.append(rsauv2)

			rsauv3 = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			modèle.append(rsauv3)

			with open(os.path.join(self.rep,  fichier[0], 'musique', fichier[0]), 'w', encoding='utf8') as f:
			 	f.write("Lancement d'une sauvegarde")


		# création de la liste source et de reférence
		che, rep = os.path.split(arbre_origine[1].chemin)
		modèle = [[modèle[0]], [modèle[1]], []]
		modèle[1][0].chemin = os.path.join(che, rep[:-2] + "_2")
		retour = [list(arbre[0:4]), [], []]
		sauv.regroupe(cons, per_suiv, retour, 0, now)

		self.assertEqual(modèle, retour)
		self.assertFalse(os.path.exists(arbre_origine[2].chemin))
		self.assertTrue(os.path.exists(os.path.join(self.rep, arbre_origine[0].chemin)))
		self.assertFalse(os.path.exists(os.path.join(self.rep, arbre_origine[-1].chemin)))

		self.assertTrue(os.path.exists(os.path.join(che, rep[:-2] + "_2")))
		# teste que les 3 fichiers sont biens présents
		self.assertEqual(set(os.listdir(os.path.join(che, rep[:-2] + "_2", 'musique'))),{t[0] for t in test[1:]})


	def test_fonctionnel2(self):
		"""teste si renvoi bien l'arbre de niveau 2 réduit """

		cons = 100
		per_suiv = 200
		now = datetime.datetime.now()

		arbre = []
		arbre_origine = []
		modèle = []
		test = [('er', 75), ('tyu', 99), ('kkk', 100), ('dfg', 150), ('niv2', 190)]

		for fichier in test:
			try:
				os.mkdir(os.path.join(self.rep, fichier[0]))
			except OSError:
				logger.error("problème de création de fichier")
			rsauv = sauv.rep_sauv(now - datetime.timedelta(days=fichier[1], hours=23),
								  os.path.join(self.rep, fichier[0]))
			rsauv.analyse()
			arbre.append(rsauv)
			# fait une copie de arbre
			rsauv2 = sauv.rep_sauv(now - datetime.timedelta(days=fichier[1], hours=23),
								  os.path.join(self.rep, fichier[0]))
			arbre_origine.append(rsauv2)

			rsauv3 = sauv.rep_sauv(now - datetime.timedelta(days=fichier[1], hours=23),
								  os.path.join(self.rep, fichier[0]))
			modèle.append(rsauv3)

		# création de la liste source et de reférence

		modèle = [[], list(modèle[0:2]), [modèle[-1]]]
		retour = [[], list(arbre[0:4]), [arbre[-1]]]
		sauv.regroupe(cons, per_suiv, retour, 1, now)

		self.assertEqual(modèle, retour)
		self.assertFalse(os.path.exists(os.path.join(self.rep, arbre_origine[2].chemin)))
		self.assertTrue(os.path.exists(os.path.join(self.rep, arbre_origine[1].chemin)))
		self.assertTrue(os.path.exists(os.path.join(self.rep, arbre_origine[-1].chemin)))

	def test_fonctionnel_avecmd5(self):
		"""teste si le md5 est bien préservé """

		cons = 1
		per_suiv = 10
		now = datetime.datetime.now()

		arbre = []
		arbre_origine = []
		modèle = []
		test = [('er_1', 5), ('tyëu_1', 23), ('kkk_1_78', 25), ('dfg_1_50', 40)]

		for fichier in test:
			try:
				os.mkdir(os.path.join(self.rep, fichier[0]))

			except OSError:
				logger.error("problème de création de fichier")
			rsauv = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			rsauv.analyse()
			arbre.append(rsauv)

			# fait une copie de arbre
			rsauv2 = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			arbre_origine.append(rsauv2)

			rsauv3 = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			modèle.append(rsauv3)

			# fait une copie de arbre

		# création de la liste source et de reférence
		che, rep = os.path.split(arbre_origine[1].chemin)
		modèle = [[modèle[0]], [modèle[1]], []]
		modèle[1][0].chemin = os.path.join(che, rep[:-2] + "_2_78")
		retour = [list(arbre[0:4]), [], []]
		sauv.regroupe(cons, per_suiv, retour, 0, now)

		self.assertEqual(modèle, retour)
		self.assertFalse(os.path.exists(arbre_origine[2].chemin))
		self.assertTrue(os.path.exists(os.path.join(self.rep, arbre_origine[0].chemin)))
		self.assertFalse(os.path.exists(os.path.join(self.rep, arbre_origine[-1].chemin)))

		self.assertTrue(os.path.exists(os.path.join(che, rep[:-2] + "_2_78")))

	def test_fonctionnel_avec2md5(self):
		"""teste si le md5 le plus récent est bien préservé """

		cons = 1
		per_suiv = 10
		now = datetime.datetime.now()

		arbre = []
		arbre_origine = []
		modèle = []
		test = [('er_1', 5), ('tyëu_1_100', 23), ('kkk_1_78', 25), ('dfg_1', 40)]

		for fichier in test:
			try:
				os.mkdir(os.path.join(self.rep, fichier[0]))

			except OSError:
				logger.error("problème de création de fichier")
			rsauv = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			rsauv.analyse()
			arbre.append(rsauv)
			# fait une copie de arbre
			rsauv2 = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			arbre_origine.append(rsauv2)

			rsauv3 = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			modèle.append(rsauv3)

		# création de la liste source et de reférence
		che, rep = os.path.split(arbre_origine[1].chemin)
		modèle = [[modèle[0]], [modèle[1]], []]
		modèle[1][0].chemin = os.path.join(che, rep.split('_')[0] + "_2_100")
		retour = [list(arbre[0:4]), [], []]
		sauv.regroupe(cons, per_suiv, retour, 0, now)

		self.assertEqual(modèle, retour)
		self.assertFalse(os.path.exists(arbre_origine[2].chemin))
		self.assertTrue(os.path.exists(os.path.join(self.rep, arbre_origine[0].chemin)))
		self.assertFalse(os.path.exists(os.path.join(self.rep, arbre_origine[-1].chemin)))

		self.assertTrue(os.path.exists(os.path.join(che, rep.split('_')[0] + "_2_100")))

	def test_un_seul_repertoire(self):
		"""teste la promotion d'un seul répertoire """

		cons = 10
		per_suiv = 10
		now = datetime.datetime.now()

		arbre = []
		test = [('répertoire_1', 5)]

		for fichier in test:
			try:
				os.mkdir(os.path.join(self.rep, fichier[0]))

			except OSError:
				logger.error("problème de création de fichier")
			rsauv = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			rsauv.analyse()
			arbre.append(rsauv)

			# fait une copie de arbre
		arbre_origine = list(arbre)
		# création de la liste source et de reférence
		che, rep = os.path.split(arbre_origine[0].chemin)
		retour = [list(arbre[0:1]), [], []]
		modèle = [[], [sauv.rep_sauv(arbre[0].date, os.path.join(che, rep[:-2] + "_2"))], []]

		sauv.regroupe(cons, per_suiv, retour, 0, now)

		self.assertEqual(modèle, retour)
		self.assertFalse(os.path.exists(os.path.join(che, rep)))

		self.assertTrue(os.path.exists(os.path.join(che, rep[:-2] + "_2")))

	def test_conservation_passe(self):
		"""teste la promotion d'un seul répertoire """

		cons = 10
		per_suiv = 10
		now = datetime.datetime.now()

		arbre = []
		test = [('ertr ter_1', 15)]

		for fichier in test:
			try:
				os.mkdir(os.path.join(self.rep, fichier[0]))

			except OSError:
				logger.error("problème de création de fichier")
			rsauv = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			arbre.append(rsauv)

			# fait une copie de arbre
		arbre_origine = list(arbre)
		# création de la liste source et de reférence
		che, rep = os.path.split(arbre_origine[0].chemin)
		retour = [list(arbre[0:1]), [], []]
		modèle = [[], [sauv.rep_sauv(arbre[0].date, os.path.join(che, rep[:-2] + "_2"))], []]

		sauv.regroupe(cons, per_suiv, retour, 0, now)

		self.assertEqual(modèle, retour)
		self.assertFalse(os.path.exists(os.path.join(che, rep)))

		self.assertTrue(os.path.exists(os.path.join(che, rep[:-2] + "_2")))

	def test_avec_erreur_déplacement(self):
		"""teste si saute bien le répertoire avec erreur """

		cons = 1
		per_suiv = 10
		now = datetime.datetime.now()

		arbre = []
		test = [('er_1', 5), ('tyëu_1', 23), ('kkk_1', 25), ('dfg_1', 40)]

		for fichier in test:
			try:
				os.mkdir(os.path.join(self.rep, fichier[0]))

			except OSError:
				logger.error("problème de création de fichier")
			rsauv = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			rsauv.analyse()
			arbre.append(rsauv)

			# fait une copie de arbre
		arbre_origine = list(arbre)
		# création de la liste source et de reférence
		che, rep = os.path.split(arbre_origine[1].chemin)
		modèle = [list(arbre[0:2]), [], []]
		modèle[0].append(arbre[3])
		retour = [list(arbre[0:4]), [], []]

		# suprimme le troisième pour générer une erreur
		shutil.rmtree(arbre[3].chemin)

		sauv.regroupe(cons, per_suiv, retour, 0, now)

		self.assertEqual(modèle, retour)
		self.assertFalse(os.path.exists(arbre_origine[2].chemin))
		self.assertTrue(os.path.exists(os.path.join(self.rep, arbre_origine[1].chemin)))
		self.assertTrue(os.path.exists(os.path.join(self.rep, arbre_origine[0].chemin)))

	def test_supérieur_non_vide(self):
		"""teste si la promotion s'incorpore correctement si le supérieur hiérarchique n'est pas vide """

		cons = 1
		per_suiv = 10
		now = datetime.datetime.now()

		arbre = []
		test = [('kkk_1', 25), ('dfg_2', 500), ('gggg_2', 600)]

		for fichier in test:
			try:
				os.mkdir(os.path.join(self.rep, fichier[0]))

			except OSError:
				logger.error("problème de création de fichier")
			rsauv = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			rsauv.analyse()
			arbre.append(rsauv)

			# fait une copie de arbre
		arbre_origine = list(arbre)
		# création de la liste source et de reférence
		che, rep = os.path.split(arbre_origine[0].chemin)
		retour = [list(arbre[0:1]), list(arbre[1:3]), []]
		modèle = [[], [sauv.rep_sauv(arbre[0].date, os.path.join(che, rep[:-2] + "_2")), ], []]
		modèle[1].extend(list(arbre[1:3]))

		sauv.regroupe(cons, per_suiv, retour, 0, now)

		self.assertEqual(modèle, retour)
		self.assertTrue(os.path.exists(arbre_origine[1].chemin))
		self.assertTrue(os.path.exists(os.path.join(self.rep, arbre_origine[2].chemin)))
		self.assertFalse(os.path.exists(os.path.join(che, rep)))

		self.assertTrue(os.path.exists(os.path.join(che, rep[:-2] + "_2")))

	def test_supérieur_non_vide2(self):
		"""teste si tout reste inchangé """

		cons = 1
		per_suiv = 10
		now = datetime.datetime.now()

		arbre = []
		test = [('1_kkk', 25), ('2_dfg', 200), ('2_gggg', 600)]

		for fichier in test:
			try:
				os.mkdir(os.path.join(self.rep, fichier[0]))

			except OSError:
				logger.error("problème de création de fichier")
			rsauv = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			rsauv.analyse()
			arbre.append(rsauv)

			# fait une copie de arbre
		arbre_origine = list(arbre)
		# création de la liste source et de reférence
		che, rep = os.path.split(arbre_origine[0].chemin)
		retour = [list(arbre[0:1]), list(arbre[1:3]), []]
		modèle = [list(arbre[0:1]), list(arbre[1:3]), []]

		sauv.regroupe(cons, per_suiv, retour, 0, now)

		self.assertEqual(modèle, retour)
		self.assertTrue(os.path.exists(arbre_origine[1].chemin))
		self.assertTrue(os.path.exists(os.path.join(self.rep, arbre_origine[2].chemin)))
		self.assertTrue(os.path.exists(os.path.join(self.rep, arbre_origine[0].chemin)))

	def test_cons_negatif(self):
		"""teste si renvoi bien l'arbre réduit et le passage au niveau 2 du dernier repertoire """

		cons = -1
		per_suiv = 10
		now = datetime.datetime.now()

		arbre = []
		test = [('er_1', 5), ('tyu_1', 23), ('kkk_1', 25), ('dfg_1', 40)]

		for fichier in test:
			try:
				os.mkdir(os.path.join(self.rep, fichier[0]))

			except OSError:
				logger.error("problème de création de fichier")
			rsauv = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			rsauv.analyse()
			arbre.append(rsauv)

			# fait une copie de arbre
		arbre_origine = list(arbre)
		# création de la liste source et de reférence
		che, rep = os.path.split(arbre_origine[0].chemin)
		modèle = [[], [sauv.rep_sauv(arbre[0].date, os.path.join(che, rep[:-2] + "_2")), ], []]
		retour = [list(arbre[0:4]), [], []]

		sauv.regroupe(cons, per_suiv, retour, 0, now)

		self.assertEqual(modèle, retour)
		self.assertFalse(os.path.exists(arbre_origine[2].chemin))
		self.assertFalse(os.path.exists(os.path.join(che, rep)))
		self.assertFalse(os.path.exists(os.path.join(self.rep, arbre_origine[-1].chemin)))

		self.assertTrue(os.path.exists(os.path.join(che, rep[:-2] + "_2")))

	def test_per_suiv_negatif(self):
		"""teste si renvoi bien l'arbre réduit et le passage au niveau 2 du dernier repertoire """

		cons = 1
		per_suiv = -10
		now = datetime.datetime.now()

		arbre = []
		arbre_origine = []
		modèle = []
		test = [('er_1', 5), ('tyu_1', 23), ('kkk_1', 25), ('dfg_1', 40)]

		for fichier in test:
			try:
				os.mkdir(os.path.join(self.rep, fichier[0]))

			except OSError:
				logger.error("problème de création de fichier")
			rsauv = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			rsauv.analyse()
			arbre.append(rsauv)
			# fait une copie de arbre
			rsauv2 = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			arbre_origine.append(rsauv2)

			rsauv3 = sauv.rep_sauv(now - datetime.timedelta(hours=fichier[1]), os.path.join(self.rep, fichier[0]))
			modèle.append(rsauv3)

		# création de la liste source et de reférence
		che, rep = os.path.split(arbre_origine[1].chemin)
		modèle = [[modèle[0]], [modèle[1]], []]
		modèle[1][0].chemin = os.path.join(che, rep[:-2] + "_2")
		retour = [list(arbre[0:4]), [], []]
		sauv.regroupe(cons, per_suiv, retour, 0, now)

		self.assertEqual(modèle, retour)
		self.assertFalse(os.path.exists(arbre_origine[2].chemin))
		self.assertTrue(os.path.exists(os.path.join(self.rep, arbre_origine[0].chemin)))
		self.assertFalse(os.path.exists(os.path.join(self.rep, arbre_origine[-1].chemin)))

		self.assertTrue(os.path.exists(os.path.join(che, rep[:-2] + "_2")))
# todo - ajouter un test de conservation de taille

class reduction(unittest.TestCase):
	rep = os.path.join(os.path.split(os.path.abspath(__file__))[0], "K45kjioyuG")
	now = datetime.datetime.now()

	def setUp(self):
		config_log()
		try:
			shutil.rmtree(self.rep)
		except OSError:
			pass
		try:
			os.makedirs(self.rep)
		except OSError:
			pass

	def tearDown(self):
		try:
			shutil.rmtree(self.rep)
		except OSError:
			pass

	def test_fonctionnel(self):
		"""teste si renvoi bien l'arbre réduit pour le niveau 1 """
		# légendes des données: nom de répertoire, niveau, jour
		arbre = [[], [], []]
		reference = [[], [], []]
		test = [('er_1', 1, 2), ('tyu_1', 1, 4), ('kkk_1', 1, 25), ('dfg_2', 2, 40)]
		for rep in test:
			# créé les répertoires avec un fichier
			try:
				os.mkdir(os.path.join(self.rep, rep[0]))

			except OSError:
				logger.error("problème de création de fichier")

			fichier = os.path.join(self.rep, rep[0], "essai")
			with open(fichier, mode='w') as file:
				file.write('hello boys')
			# créé les arbres
			rsauv = sauv.rep_sauv(self.now - datetime.timedelta(days=rep[2]), os.path.join(self.rep, rep[0]))
			rsauv.analyse()
			arbre[rep[1] - 1].append(rsauv)
			reference[rep[1] - 1].append(rsauv)

			# apportes les modifications du résultat
		del (reference[1][0])
		del (reference[0][-1])

		# Créé la configuration
		config = sauv.My_configparser()
		config['sauv'] = {}
		config['sauv'][sauv.cons1] = '1'
		config['sauv'][sauv.cons2] = '50'
		config['sauv'][sauv.cons3] = '500'
		config['sauv'][sauv.qta] = '0.000000025'
		config['sauv'][sauv.dest] = self.rep

		# lance la fonction
		sauv.reduction(config['sauv'], arbre)

		self.assertEqual(arbre, reference)
		# teste existance entre du second
		self.assertTrue(os.path.exists(os.path.join(self.rep, test[1][0])))
		self.assertFalse(os.path.exists(os.path.join(self.rep, test[2][0])))

	def test_conservation_une_sauv(self):
		"""teste si une sauvegarde est bien conservée si Qta très faible """
		# légendes des données: nom de répertoire, niveau, jour
		arbre = [[], [], []]
		reference = [[], [], []]
		test = [('er_1', 1, 2), ('tyu_1', 1, 4), ('kkk_1', 1, 25), ('dfg_2', 2, 40)]
		for rep in test:
			# créé les répertoires avec un fichier
			try:
				os.mkdir(os.path.join(self.rep, rep[0]))

			except OSError:
				logger.error("problème de création de fichier")

			fichier = os.path.join(self.rep, rep[0], "essai")
			with open(fichier, mode='w') as file:
				file.write('hello boys')
			# créé les arbres
			rsauv = sauv.rep_sauv(self.now - datetime.timedelta(days=rep[2]), os.path.join(self.rep, rep[0]))
			rsauv.analyse()
			arbre[rep[1] - 1].append(rsauv)
			reference[rep[1] - 1].append(rsauv)

			# apportes les modifications du résultat
		del (reference[1][0])
		del (reference[0][-1])
		del (reference[0][-1])

		# Créé la configuration
		config = sauv.My_configparser()
		config['sauv'] = {}
		config['sauv'][sauv.cons1] = '1'
		config['sauv'][sauv.cons2] = '50'
		config['sauv'][sauv.cons3] = '500'
		config['sauv'][sauv.qta] = '0.000000001'
		config['sauv'][sauv.dest] = self.rep

		# lance la fonction
		sauv.reduction(config['sauv'], arbre)

		self.assertEqual(arbre, reference)
		# teste existance entre du second
		self.assertTrue(os.path.exists(os.path.join(self.rep, test[0][0])))
		self.assertFalse(os.path.exists(os.path.join(self.rep, test[1][0])))

	def test_erreur_deffacement(self):
		"""teste l'erreur d'effacement et la protection du niveau 1"""
		# légendes des données de test: nom de répertoire, niveau, jour
		arbre = [[], [], []]
		reference = [[], [], []]
		test = [('1_er', 1, 2), ('1_tyu', 1, 4), ('1_kkk', 1, 25), ('1_dfg', 2, 40), ('2_bloque', 2, 45)]
		for rep in test:
			# créé les répertoires avec un fichier
			try:
				os.mkdir(os.path.join(self.rep, rep[0]))

			except OSError:
				print("problème de création de fichier :{}".format(rep[0]))

			fichier = os.path.join(self.rep, rep[0], "essai")
			with open(fichier, mode='w') as file:
				file.write('hello boys')
				# créé les arbres
			rsauv = sauv.rep_sauv(self.now - datetime.timedelta(days=rep[2]), os.path.join(self.rep, rep[0]))
			rsauv.analyse()
			arbre[rep[1] - 1].append(rsauv)
			reference[rep[1] - 1].append(rsauv)

			# apportes les modifications du résultat
		del (reference[1][0])

		# Créé la configuration
		config = sauv.My_configparser()
		config['sauv'] = {}
		config['sauv'][sauv.cons1] = '1'
		config['sauv'][sauv.cons2] = '50'
		config['sauv'][sauv.cons3] = '500'
		config['sauv'][sauv.qta] = '0.000000025'
		config['sauv'][sauv.dest] = self.rep

		# modifie le dernier répertoire
		os.rename(os.path.join(self.rep, test[-1][0]), os.path.join(self.rep, test[-1][0][:5]))
		# lance la fonction
		sauv.reduction(config['sauv'], arbre)

		self.assertEqual(arbre, reference)
		# teste existance entre du second
		self.assertTrue(os.path.exists(os.path.join(self.rep, test[1][0])))
		self.assertTrue(os.path.exists(os.path.join(self.rep, test[2][0])))
		self.assertFalse(os.path.exists(os.path.join(self.rep, test[3][0])))
		self.assertTrue(os.path.exists(os.path.join(self.rep, test[4][0][:5])))

	def test_niveau2et3(self):
		"""teste si renvoi bien l'arbre réduit pour le niveau 1 """
		# légendes des données: nom de répertoire, niveau, jour
		arbre = [[], [], []]
		reference = [[], [], []]
		test = [('1_er', 2, 2), ('1_tyu', 3, 4), ('1_kkk', 3, 25), ('1_dfg', 3, 40)]
		for rep in test:
			# créé les répertoires avec un fichier
			try:
				os.mkdir(os.path.join(self.rep, rep[0]))

			except OSError:
				print("problème de création de fichier :{}".format(rep[0]))

			fichier = os.path.join(self.rep, rep[0], "essai")
			with open(fichier, mode='w') as file:
				file.write('hello boys')
			# créé les arbres
			rsauv = sauv.rep_sauv(self.now - datetime.timedelta(days=rep[2]), os.path.join(self.rep, rep[0]))
			rsauv.analyse()
			arbre[rep[1] - 1].append(rsauv)
			reference[rep[1] - 1].append(rsauv)

			# apportes les modifications du résultat
		del (reference[2][-1])
		del (reference[2][-1])

		# Créé la configuration
		config = sauv.My_configparser()
		config['sauv'] = {}
		config['sauv'][sauv.cons1] = '1'
		config['sauv'][sauv.cons2] = '50'
		config['sauv'][sauv.cons3] = '500'
		config['sauv'][sauv.qta] = '0.000000025'
		config['sauv'][sauv.dest] = self.rep

		# lance la fonction
		sauv.reduction(config['sauv'], arbre)

		self.assertEqual(arbre, reference)
		# teste existance entre du second
		self.assertTrue(os.path.exists(os.path.join(self.rep, test[1][0])))
		self.assertFalse(os.path.exists(os.path.join(self.rep, test[2][0])))

	def test_conservation2_vide(self):
		"""teste l'absence de cons2"""

		arbre = [[], [], []]
		reference = [[], [], []]
		test = [('1_er', 1, 2), ('1_tyu', 1, 4), ('1_kkk', 1, 25), ('1_dfg', 2, 40)]
		for rep in test:
			# créé les répertoires avec un fichier
			try:
				os.mkdir(os.path.join(self.rep, rep[0]))

			except OSError:
				print("problème de création de fichier :{}".format(rep[0]))

			fichier = os.path.join(self.rep, rep[0], "essai")
			with open(fichier, mode='w') as file:
				file.write('hello boys')
				# créé les arbres
			rsauv = sauv.rep_sauv(self.now - datetime.timedelta(days=rep[2]), os.path.join(self.rep, rep[0]))
			rsauv.analyse()
			arbre[rep[1] - 1].append(rsauv)
			reference[rep[1] - 1].append(rsauv)

			# apporte les modifications du résultat
		del (reference[1][0])
		del (reference[0][-1])

		# Créé la configuration
		config = sauv.My_configparser()
		config['sauv'] = {}
		config['sauv'][sauv.cons1] = '1'
		config['sauv'][sauv.cons3] = '60'
		config['sauv'][sauv.qta] = '0.000000025'
		config['sauv'][sauv.dest] = self.rep

		# lance la fonction
		sauv.reduction(config['sauv'], arbre)

		self.assertEqual(arbre, reference)
		# teste existance entre du second
		self.assertTrue(os.path.exists(os.path.join(self.rep, test[1][0])))
		self.assertFalse(os.path.exists(os.path.join(self.rep, test[2][0])))



class en_decode_json(unittest.TestCase):
	def setUp(self):
		config_log()

	def test_endecode(self):
		""" Encode puis décode un objet rep_sauv"""
		rsauv = sauv.rep_sauv(datetime.datetime(2017, 10, 5), "/ertert/erte")
		arbre = [[], [rsauv]]

		try:
			fichier = sauv.my_encoder().encode(arbre)
		except json.decoder.JSONDecodeError as exception:
			pass

		try:
			resultat = sauv.my_decoder().decode(fichier)
		except json.decoder.JSONDecodeError as exception:
			pass

		self.assertEqual(arbre, resultat)

	def test_decode_erroné(self):
		""" Encode puis décode un objet rep_sauv"""
		l_entree = ('{"date": "2017-10-05 00-0045", "chemin": "/ertert/erte", "__class__": "rep_sauv"}',
					'{"date": "55-10-05 00-00", "chemin": "/ertert/erte", "__class__": "rep_sauv"}',
					'{"date": "2016-10-05 00-00", "chemin": 5, "__class__": "rep_sauv"}',
					'{"date": "2017-10-05 00-00",  "__class__": "rep_sauv"}',
					'{"date": "2017-10-05 00-00", "chemin": ["dffdggdfg"], "__class__": "rep_sauv"}')

		for entree in l_entree:
			self.assertRaises(json.decoder.JSONDecodeError, sauv.my_decoder().decode, entree)


# Programme principal

if __name__ == '__main__':
	unittest.main()
