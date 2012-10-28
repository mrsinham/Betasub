#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""BetaSub - version Console & Module

Ce script permet de t�l�charger, extraire et filtrer les sous-titres de
Betaseries <www.betaseries.com>.

Pour son utilisation, consultez la documentation en ligne.

Auteur:                Thammas <thammas2000@gmail.com>
Homepage:              sites.google.com/site/thammasprojects/betasub
Documentation script:  sites.google.com/site/thammasprojects/betasub/doc-fr
Documentation module:  sites.google.com/site/thammasprojects/betasub/module-fr
"""
__version__ = '0.6'


import os
import sys
import urllib
import urllib2
import hashlib
import json
import time
import re
import glob,zipfile
import sqlite3
import difflib
import shutil
import random
from optparse import OptionParser
from threading import Timer
import ConfigParser
import logging
import string

#mode debug
#logging.basicConfig( format='%(levelname)s:[%(funcName)s,%(lineno)s]:%(message)s',level=logging.DEBUG)
#mode user
logging.basicConfig( format='%(message)s',level=logging.INFO)


class Beta:
    """Class utilisant l'api de Betaseries
    Elle se focalise essentiellement sur le t�l�chargement des sous-titres.

    voir la doc en ligne:
    http://sites.google.com/site/thammasprojects/betasub/module-fr

    """
    def __init__(self, api="76e584dfaf7b"):
        """Initialisation des param�tres.

        """
        self.api = api
        self.api_url = "http://api.betaseries.com"



    def source_get(self, url):
        """R�cup�re ce qui est renvoy� � partir d'une url.

        Permet �galement de cr�er l'user-agent.

        """
        opener = urllib2.build_opener()
        ua = 'BetaSub %s' % __version__
        opener.addheaders = [('User-agent', ua)]
        source = opener.open(url)
        return source.read()



    def auth(self, login, password):
        """Retourne le token � utiliser pour les requ�tes futures.
        Identifie le membre avec son login et mot de pass sur Beteseries.

        """
        hash_pass = hashlib.md5(password).hexdigest()
        params = urllib.urlencode({'login': login,
                                   'password': hash_pass,
                                   'key': self.api})

        url = "%s/members/auth.json?%s" % (self.api_url, params)
        source = self.source_get(url)
        json_data = json.loads(source)
        try:
            token = json_data['root']['member']['token']
            return token
        except:
            for error in json_data['root']['errors']:
                logging.error("Betaseries: %s" %json_data['root']['errors'][error]['content'])


    def last_subtitles(self, language="", number=""):
        """Retourne les derniers sous-titres r�cup�r�s par BetaSeries, dans la limite de 100.

        >>> last_subtitles()
        [{ 'url': 'http://www.betaseries.com/srt/310234',
           'source': 'addic7ed',
           'quality': 3,
           'language': u'VO',
           'filename': 'Chuck - 04x14 - Chuck Versus...x.srt'},...]

        """
        params = urllib.urlencode({ 'language' : language,
                                   'number': number,
                                   'title':"biglove",
                                   'key': self.api})

        url = "%s/subtitles/last.json?%s" % (self.api_url, params)
        source = self.source_get(url)
        json_data = json.loads(source)
        try:
            subtitles = json_data['root']['subtitles']
            all_subtitles = []
            for subtitle in subtitles:
                all_subtitles.append(subtitles[subtitle])
            return all_subtitles
        except:
            for error in json_data['root']['errors']:
                logging.error("Betaseries: %s" %json_data['root']['errors'][error]['content'])



    def member_subtitles(self, login, password, language="vovf", view=""):
        """Retourne la liste des sous-titres des �pisodes restant � regarder du membre identifi�.

        >>> beta.member_subtitles('user','psw')
        [  {'url': 'http://www.betaseries.com/srt/310234',
            'source': 'addic7ed', 'quality': 3, 'language': u'VO',
            'filename': 'Chuck - 04x14 - Chuck Versus...x.srt'},...]

        """
        params = urllib.urlencode({  'view' : view,
                                    'token': self.auth(login, password),
                                    'key': self.api})

        url = "%s/members/episodes/%s.json?%s" % (self.api_url, language, params)
        source = self.source_get(url)
        json_data = json.loads(source)
        subs_listing = []
        try:
            episodes = json_data['root']['episodes']
            for episode in episodes:
                #for items in episodes[episode]['subs']:
                    #subs_listing.append(episodes[episode]['subs'][items])
                subs_listing.append(episodes[episode])
            return subs_listing
        except:
            for error in json_data['root']['errors']:
                logging.error("Betaseries: %s" %json_data['root']['errors'][error]['content'])
            return subs_listing



    def search_subtitles(self, show, season="", episode="", language=""):
        """Retourne la liste des urls des �pisodes � partir d'une recherche

        >>> beta.search_subtitles('chuck 4 14')
        [{ 'url': 'http://www.betaseries.com/srt/310234',
           'source': 'addic7ed',
           'quality': 3,
           'language': u'VO',
           'filename': 'Chuck - 04x14 - Chuck Versus...x.srt'},...]

        """
        params = urllib.urlencode({ 'language' : language,
                                    'season': season,
                                    'episode': episode,
                                    'key': self.api})

        url = "%s/subtitles/show/%s.json?%s" % (self.api_url, show, params)
        source = self.source_get(url)
        json_data = json.loads(source)
        all_subtitles = []
        try:
            subtitles = json_data['root']['subtitles']
            for subtitle in subtitles:
                all_subtitles.append(subtitles[subtitle])
            return all_subtitles
        except:
            for error in json_data['root']['errors']:
                logging.error("Betaseries: %s" %json_data['root']['errors'][error]['content'])
            return all_subtitles



    def file_subtitles(self, file_path):
        """Retourne la liste des sous-titres � partir d'un nom de fichier

        >>> beta.file_subtitles('d:\\series\\')
        [{ 'url': 'http://www.betaseries.com/srt/310234',
           'source': 'addic7ed',
           'quality': 3,
           'language': u'VO',
           'filename': 'Chuck - 04x14 - Chuck Versus...x.srt'},...]

        """
        #extrait le nom de fichier
        path = os.path.split(file_path)[-1]
        if path == "":
            logging.info(self.info("no_file"))
        else:
            file_name = path
        data = self.extract_data(file_name)
        
        #v�rification du nom de la s�rie
        try:
            show = data[0].lower()
            show_list = self.show_url(show)

            #si il y a plusieurs choix de s�ries on prend celui qui correspond le mieux
            for item in show_list:
                #test whether every element in showurl is in show
                if set(item['url']) <= set(show):
                    show = item['url']
                else:
                    show = show_list[0]['url']

            season = data[1]
            episode = data[2]
            return self.search_subtitles(show, season, episode)
        except:
            return []




    def show_url(self, search_show):
        """Retourne et v�rifie l'existence du "nom url" de la s�rie recherch�e.

        Cela Permet d'avoir le nom url exact de la s�rie.
        EXAMPLE: criminaljustice pour criminal justice

        >>> beta.show_url("the office")
        [ {u'url': u'theofficeus', u'title': u'The Office US'},
          {u'url': u'theofficeuk', u'title': u'The Office (UK)'}]

        """
        params = urllib.urlencode({ 'title' : search_show,
                                    'key': self.api})
        url = "%s/shows/search.json?%s" % (self.api_url, params)
        source = self.source_get(url)
        json_data = json.loads(source)
        shows_listing = []
        try:
            shows = json_data['root']['shows']
            for show in shows:
                shows_listing.append(shows[show])
            return shows_listing

        #warnings si la recherche fait moin de de 2 caract�res, il y a erreurs
        except:
            for error in json_data['root']['errors']:
                logging.error("Betaseries: %s" %json_data['root']['errors'][error]['content'])
            return shows_listing




    def extract_data(self, value):
        """Extrait les infos � partir d'une recherche ou d'un nom de fichier.

        Retourne une liste ['show', 'season', 'episode', 'language']

        >>> beta.extract_data('Southland - 3x01 - Episode 1.HDTV.en.avi')
        ['Southland','3','01','en']

        """
        #regex pour la recherche
        pattern1 = re.compile(r"""
              ^(?P<show>.*?)\s*                     #show
              (                                     #season,episode
              season?|saison?|[s .n]?(?P<season>\d+)#season
              [e .x]?(?P<episode>\d+)?              #episode
              )+
              .*                                    #any before language
              [ .]+(?P<language>fren|enfr|vovf|vfvo|fr|en|vo|vf)+? #language
              .*?$ #end
              """,re.IGNORECASE|re.VERBOSE)
        
        #deuxi�me regex pour ceux sans langue:
        pattern2 = re.compile(r"""
              ^(?P<show>.*?)\s*                     #show
              (                                     #season,episode
              season?|saison?|[s .n]?(?P<season>\d+)#season
              [e .x]?(?P<episode>\d+)?              #episode
              )+
              (?P<language>)?                       #MODIF.
              """,re.IGNORECASE|re.VERBOSE)
        #remplace les caract. inutiles
        value = re.sub('[\.\-\_\,\:\;\[\]\(\)]',' ',value)
        #remplace les dates
        for date in range(2000, 2020):
        	value = value.replace(str(date), '')
        #solution pour premier regex
        pattern1 = re.match(pattern1,value)
        #autre possibilit� pour regex 2
        pattern2 = re.match(pattern2,value)
        #si correspondant � regex 1:
        if pattern1:
            result = pattern1.groupdict('')#''=defaut instead None
        #si correspondant � regex 2:
        elif pattern2:
            result = pattern2.groupdict('')
        #si rien, retourne l'original ou False, pas encore d�cid�...
        #... cela d�pend du mode search
        else:
            #return value
            #logging.debug(value)
            return False
        #accepting there is no season with 3 digits
        season = result['season']
        if len(season) == 3:
            result["season"] = season[0]
            result["episode"] = season[1:]
        #accepting there is no season with 4 digits
        season = result['season']
        if len(season) >= 4:
            result["season"] = season[0:2]
            result["episode"] = season[2:]

        show = result['show'].strip()
        season = result['season']
        episode = result['episode']
        #normalisation langue
        language = result['language'].lower()
        language = re.sub('fren|enfr|vfvo','vovf',language)
        language = re.sub('en','vo',language)
        language = re.sub('fr','vf',language)
        #solution finale
        
        #exceptions pour certaines s�ries ex: V(2009).
        if show.lower() == 'v':
            return  ['V (2009)', season, episode, language]
        else:
            return  [show, season, episode, language]



            

    def member_downloaded(self, login, password, show, season, episode):
        """Marque l'�pisode de la saison de la s�rie url comme r�cup�r�.
        
        Pour fonctionner, l'option doit �tre activ�e dans le compte du membre.
        
        """
        params = urllib.urlencode({  'season' : str(season),
                                    'episode': str(episode),
                                    'token': self.auth(login, password),
                                    'key': self.api})


        url = "%s/members/downloaded/%s.json?%s" % (self.api_url, show, params)
        source = self.source_get(url)
        json_data = json.loads(source)
        try:
            downloaded = json_data['root']['downloaded']
            return downloaded

        except:
            for error in json_data['root']['errors']:
                logging.error("Betaseries: %s" %json_data['root']['errors'][error]['content'])
                
                
    def member_watched(self, login, password, show, season, episode, note=""):
        """Marque l'�pisode de la saison de la s�rie url comme vu sur BetaSeries.


        """
        params = urllib.urlencode({  'season' : str(season),
                                    'episode': str(episode),
                                    'note'   : str(note),
                                    'token': self.auth(login, password),
                                    'key': self.api})


        url = "%s/members/watched/%s.json?%s" % (self.api_url, show, params)
        source = self.source_get(url)
        json_data = json.loads(source)
        try:
            watched = json_data['root']['code']
            return watched

        except:
            for error in json_data['root']['errors']:
                logging.error("Betaseries: %s" %json_data['root']['errors'][error]['content'])

                

    def show_info(self, show):
        """Retourne les informations sur la s�rie-nom-url sous forme de dict

        ex: {u'status': u'Continuing', u'id_thetvdb': u'79349', ...}

        """
        params = urllib.urlencode({'key': self.api})
        url = "%s/shows/display/%s.json?%s" % (self.api_url, show, params)
        source = self.source_get(url)
        json_data = json.loads(source)
        try:
            show = json_data['root']['show']
            return show
        except:
            for error in json_data['root']['errors']:
                logging.error("Betaseries: %s" %json_data['root']['errors'][error]['content'])






class Sub:
    """Class fournissant des outils pour les sous-titres

    """
    def __init__(self):
        """Initialisation des param�tres.

        """

    def download_file(self, file_name, file_url, directory):
        """T�l�charge les sous-titres dans le r�pertoire indiqu�

        """
        if os.path.isdir(directory) :
            logging.info(file_name)
            # need to strip weirds characters
            urllib.urlretrieve(file_url, directory+file_name)

        else:
            # message d'avertissement
            logging.critical("error: directory do not exist.")
            return False

    def clean_filename(self, sPreviousFilename):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        return ''.join(c for c in sPreviousFilename if c in valid_chars)


    def unzip_file(self, zip_file, directory,  use_filter=False, filters_regex=""):
        """Unzip subs from subtitles folder with filter pattern.
        Return a list of the unzipped files

        """
        #on cr�e une liste qui sera retourn�e � la fin
        return_list = []
        #si pas de regex, on d�sactive les filtres
        if filters_regex == "":
            use_filter = False
        #seulement si l'archive est valide
        if zipfile.is_zipfile(zip_file):
            zip_data = zipfile.ZipFile(zip_file, 'r')
            for subs in zip_data.namelist():
                # si utilisation des filtres
                if use_filter == True or use_filter == "True":
                    # si �chappent au filtres
                    if re.search(filters_regex, subs) == None:
                        #on ouvre le sous-titres en m�moire
                        data = zip_data.read(subs, directory)
                        #on transforme le chemin des sous-dossier en dossier commun
                        sub_path = os.path.join(directory, subs.split("/")[-1])
                        # cleaning name
                        sub_path = self.clean_filename(sub_path)
                        #on �vite les dossier
                        if os.path.isdir(sub_path): continue
                        #on �crit les fichiers
                        sub = open(sub_path, "wb")
                        sub.write(data)
                        sub.close()
                        #on cr�e la liste des fichiers de retour
                        return_list.append(sub_path)
                #Si on utilise pas les filtres
                else:
                    #on ouvre le sous-titres en m�moire
                    data = zip_data.read(subs, directory)
                    #on transforme le chemin des sous-dossier en dossier commun
                    sub_path = os.path.join(directory, subs.split("/")[-1])
                    #on �vite les dossier
                    if os.path.isdir(sub_path): continue
                    #on �crit les fichiers
                    sub = open(sub_path, "wb")
                    sub.write(data)
                    sub.close()
                    #on cr�e la liste des fichiers de retour
                    return_list.append(sub_path)
            zip_data.close()
            # efface le zip
            os.remove(zip_file)
            #retour de la liste des fichiers d�zipper
            return return_list
        else:
            return_list.append(zip_file)
            #retour de la liste des fichiers qui ne sont pas des zip
            return return_list


    def files_list(self, directory, extensions=['avi','mkv','mp4'], subfolders=False):
        """Return all files list from directory.
        Possibility to add extensions list and subfolders

        """
        all_files = []
        #si on veut les sous-dossiers
        if subfolders == True:
            for root, dirs, names in os.walk(directory):
                subdir = os.path.join(root,"")
                for ext in extensions:
                    for files in glob.glob(subdir+'*.%s' % ext):
                        all_files.append(files)
        else:
            for ext in extensions:
                for files in glob.glob(directory+'*.%s' % ext):
                    all_files.append(files)
        # Si il y a au moins un fichier
        if all_files:
            return all_files

        else:
            logging.info("No file.")
            return []










class Program:
    """Main program
    
    """
    def __init__( self, mode="", login="",  password="",
                  unzip=False, use_filters=False, filters_regex="",
                  use_database=False, use_updater=False, delay_sec=3600,
                  search="", use_subfolders=False, rename_subtitles=False,
                  language_priority="VF", set_episode_downloaded=False,
                  series_extensions='avi', no_download_if_present=False,
                  default_directory="", extensions_filter_mode="srt|txt|ass",
                  subtitles_directory="", use_quotes=True,
                  quality_subtitles="", language_subtitles="",
                  keep_only_one_subtitle=False):
        """Initialisation des param�tres.
        
        * En tant que script, les param�tres sont ceux par d�fauts
        * En ligne de commande, mode= est obligatoire.
                                On rajoute ceux n�cessaires.

        """
        # define default options from settings
        self.Beta                   = Beta()
        self.Sub                    = Sub()
        self.mode                   = mode
        self.login                  = login
        self.password               = password
        self.default_dir            = default_directory
        self.subtitles_dir          = subtitles_directory
        self.use_database           = use_database
        self.unzip                  = unzip
        self.use_filters            = use_filters
        self.filters_regex          = filters_regex
        self.extensions_filter_mode = extensions_filter_mode
        self.use_updater            = use_updater
        self.delay_sec              = delay_sec
        self.search                 = search
        self.use_subfolders         = use_subfolders
        self.rename_subtitles       = rename_subtitles
        self.language_priority      = language_priority
        self.set_episode_downloaded = set_episode_downloaded
        self.series_extensions      = series_extensions
        self.movie_path             = ""
        self.use_quotes             = use_quotes
        self.quality_subtitles      = quality_subtitles
        self.language_subtitles     = language_subtitles
        self.no_download_if_present = no_download_if_present
        self.keep_only_one_subtitle = keep_only_one_subtitle

        self.db_file     = 'betasub.db'
        self.modes       = [ 'episodes','prompt','search','file',
                                'utorrent', 'unzip', 'filter', 'stat']

        
        #initialise si ligne de commande
        try:
            sys.argv[1]
            self.verify_command_line()
        #sinon, initialise les param�tres du script
        except:
            self.splash()
            pass
        
        #test des options du programme
        self.verify_program()





    def verify_program(self):
        """ Verify program settings

        """
        #d�sactivation des filtres si pas de caract�res
        if self.filters_regex == "":
            self.use_filters = False
            
        #d�finition du choix de qualit� du sous-titre de l'utilisateur
        if self.quality_subtitles:
            self.quality_subtitles = list(str(self.quality_subtitles))
        else:
            self.quality_subtitles = list("12345")

        #d�finition du choix de langue du sous-titre de l'utilisateur
        if self.language_subtitles:
            self.language_subtitles = self.language_subtitles.upper()
        else:
            self.language_subtitles = "VOVF"
            

        #si mode d�fini
        if self.mode and self.mode in self.modes:
            #si sub dir correct
            if os.path.isdir(self.default_dir):
                #on corrige le path principal si mal form�
                if self.default_dir[-1] not in [os.sep]:
                    self.default_dir = self.default_dir+os.sep

                #on s'assure que l'utilisateur a bien param�tr� le sub_dir
                #si l'utilisateur veut ses srt dans un dossier special
                if self.subtitles_dir == "" or self.subtitles_dir[0] == "|":
                    # ce n'est qu'en mode file ou utorrent
                    if self.mode in ["file", "utorrent"]:
                        self.subtitles_dir = self.subtitles_dir
                    #alors le dossiers sous-titre est celui par d�faut
                    else:
                        self.subtitles_dir = self.default_dir

                #alors il a mis un path et il doit �tre valide
                elif os.path.isdir(self.subtitles_dir):
                    self.subtitles_dir = self.subtitles_dir
                #si le chemin n'est pas valide
                else:
                    logging.critical(self.info("critical_subsdir"))
                    time.sleep(self.info("sleep"))
                    sys.exit()

                #quand toutes les conditions sont remplies, on lance le prog
                self.program()

            else:
                logging.critical(self.info("critical_dir"))
                time.sleep(self.info("sleep"))
        else:
            logging.critical(self.info("critical_mode"))
            time.sleep(self.info("sleep"))





    def verify_command_line(self):
        """ Verify command line settings

        """
        (options, args) = self.command_line()

        #si on veut juste mettre un �pisode comme regard�
        if args and os.path.isfile(args[0]):
            #on passe en mini mode watched
            self.mode = "watched"
            self.splash()
            #on essaie de  marquer l'�pisode comme vu sur Betaseries
            self.mode_watched(args[0])


        else:
            #v�rifie qu'il y a bien un mode d'activ�
            if (options.mode in self.modes):
            
                self.mode = options.mode
                self.splash()
                self.args = " ".join(args) #les autres arguments
                

                if options.search:
                    self.search = options.search

                if options.rename_subtitles:
                    self.rename_subtitles = options.rename_subtitles
                    
                if options.subfolders:
                    self.use_subfolders = options.subfolders

                if options.login:
                    self.login = options.login

                if options.password:
                    self.password = options.password

                if options.database:
                    self.use_database = options.database

                if options.updater:
                    self.use_updater = options.updater

                if options.frequency:
                    self.delay_sec = options.frequency

                if options.default_directory:
                    self.default_dir = options.default_directory

                if options.unzip:
                    self.unzip = options.unzip

                if options.filters:
                    self.use_filters = True
                    self.filters_regex = options.filters
                    
                if options.use_quotes:
                    self.use_quotes = options.use_quotes

                if options.language_priority:
                    self.language_priority = options.language_priority

                if options.series_extensions:
                    self.series_extensions = options.series_extensions

                if options.set_episode_downloaded:
                    self.set_episode_downloaded = options.set_episode_downloaded

                if options.extensions_filter_mode:
                    self.extensions_filter_mode = options.extensions_filter_mode

                if options.subtitles_directory:
                    self.subtitles_dir = options.subtitles_directory
                    
                if options.quality_subtitles:
                    self.quality_subtitles = options.quality_subtitles
                    
                if options.language_subtitles:
                    self.language_subtitles = options.language_subtitles
                    
                if options.no_download_if_present:
                    self.no_download_if_present = options.no_download_if_present

                if options.keep_only_one_subtitle:
                    self.keep_only_one_subtitle = options.keep_only_one_subtitle
                    
                #exception pour le mode search
                if self.mode == "search":
                    if options.search:
                        self.search = options.search
                    elif self.args != "":
                        self.search = self.args
                    else:
                       self.search = raw_input("search: ")


            else:
                logging.critical(self.info('warning_cmdl')), raw_input(self.info("pause"))
                os._exit(1)







    def program(self):
        """Run program
        
        """
        #si timer avec mode episodes ou file
        if ((self.use_updater == True or self.use_updater == "True") and
            self.mode in ["episodes", "file"] ):
            logging.info("%s %s\n" % (self.info("using_updater"), self.delay_sec))
            self.updater(self.delay_sec,self.mode_operation)
        else:
            self.mode_operation()
            time.sleep(self.info("sleep"))
            sys.exit(self.info('exit'))


    def mode_operation(self):
        """Mode op�ratoire

        """
        #la mani�re dont le programme va op�rer d�pend du mode
        if self.mode == 'utorrent':
            subs_list = self.mode_utorrent()
            self.get_subtitles(subs_list)

        if self.mode == 'prompt':
            subs_list = self.mode_prompt()
            self.get_subtitles(subs_list)

        if self.mode == 'search':
            subs_list = self.mode_search()
            self.get_subtitles(subs_list)

        if self.mode == 'file':
            self.mode_file()
            
        if self.mode == 'episodes':
            subs_list = self.mode_episodes()
            self.get_subtitles(subs_list)

        if self.mode == 'unzip':
            self.mode_unzip()

        if self.mode == 'filter':
            self.mode_filter()
            
        if self.mode == 'stat':
            self.mode_statistics()



    def subtitles_preferences(self, subs_list):
        """Filtre les sous-titres disponibles en fonction du choix de l'utilisateur

        """
        #�liminiation des sous-titres ne correspndant pas � la qualit�
        #on ne garde que ceux qui on la bonne qualit�
        subs_list[:] = (sub for sub in subs_list if str(sub['quality']) in self.quality_subtitles)

        #exception pour le mode episodes
        if self.mode != "episodes":
            #�liminiation des saison compl�te pour les modes concern�s
            subs_list[:] = (sub for sub in subs_list if sub['episode'] != "0")
        
        #�liminiation des sous-titres ne correspndant pas � la langue
        if self.language_subtitles == "VF":
            subs_list[:] = (sub for sub in subs_list if sub['language'] in ["VF", 'VOVF'])
                    
        if self.language_subtitles == "VO":
            subs_list[:] = (sub for sub in subs_list if sub['language'] in ["VO", 'VOVF'])
            
        return subs_list
        
        


    def get_subtitles(self, subs_list):
        """T�l�charge et extrait les sous-titres selon le mode
        
        """
        #filtrage des sous-titres en fonction du mode
        if self.mode in ["file", "utorrent", "episodes"]:
            subs_list = self.subtitles_preferences(subs_list)
            
        #exception car duplication intitul� filename dans l'api
        title = "file"
        if self.mode == 'episodes':
            title = "filename"

        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
            
        # si sous-titres
        if subs_list != []:
            # si on utilise une base de donn�e et les bons modes
            if ((self.use_database == True  or self.use_database == "True") and
                (self.mode in ["episodes", "file", "utorrent"])):
                #r�cup�ration de la base de donn�e
                database = Database(self.db_file).get_urls()
                #sous-titres qui ne sont pas dans la base de donn�e
                new_subs = list(set([item['url'] for item in subs_list]) - set(database))
                #si tous les sous-titres sont dans la base donn�e
                if new_subs == []:
                    if self.mode in ["file", "utorrent"]:
                        movie = self.file_base(self.movie_path)["name"]
                        logging.info("%s %s" % (self.info('sub_downloaded_for'), movie))
                    else:
                        logging.info("%s %s" % (self.info('sub_downloaded'), movie))
                #si il y a de nouveaux sous-titres
                else:

                    logging.info('\n%s %s in %s ...\n' % ( len(new_subs),
                                                   self.info('sub_download'),
                                                   self.default_dir))
                    #cr�e un dictionnaire pour la fonction best_subtitle
                    subs_dict_to_compar = {}
                    for subs in subs_list:
                        if subs['url'] not in database:
                            subs_dict_to_compar[subs['url']] = {}
                            subs_dict_to_compar[subs['url']]["file_subs_list"] = list()

                            # strip weird char
                            subs[title] = ''.join(c for c in subs[title] if c in valid_chars)

                            #download
                            self.Sub.download_file(  subs[title],
                                                      subs['url'],
                                                      self.subtitles_dir)
                            #save in database
                            Database(self.db_file).set_data(subs['title'], subs['url'])

                            subtitle_path = os.path.join(self.subtitles_dir,subs[title])
                            #on cr�e une liste des srt(non zip) si jamais unzip = False
                            if not zipfile.is_zipfile(subtitle_path):
                                subs_dict_to_compar[subs['url']]["file_info"] = subs
                                subs_dict_to_compar[subs['url']]["file_subs_list"].append(subtitle_path)


                            #unzip
                            if self.unzip == True or self.unzip == "True":
                                #on prend la liste retourn�e par la fonction unzip
                                zip_files_list = self.Sub.unzip_file(
                                                  subtitle_path,
                                                  self.subtitles_dir,
                                                  self.use_filters,
                                                  self.filters_regex)

                                subs_dict_to_compar[subs['url']]["file_info"] = subs
                                subs_dict_to_compar[subs['url']]["file_subs_list"] = zip_files_list


                    #seulement en mode file&utorrent, on cr�e the best of the best, qui convient au mieux
                    if self.mode in ['file', 'utorrent'] and self.rename_subtitles in [True, 'True']:
                        self.best_subtitle(subs_dict_to_compar, self.movie_path)
                        
                    #retour final de validition
                    return True
                            
                            
            #Si on utilise pas de base de donn�e
            else:
                logging.info('\n%s %s' % ( len(subs_list),
                                         self.info('sub_download')))
                                         
                #cr�e un dictionnaire pour la fonction best_subtitle
                subs_dict_to_compar = {}
                all_file_list = []
                for subs in subs_list:
                    subs_dict_to_compar[subs['url']] = {}
                    subs_dict_to_compar[subs['url']]["file_subs_list"] = list()

                    # strip weird char
                    subs[title] = ''.join(c for c in subs[title] if c in valid_chars)
                    #download
                    self.Sub.download_file(  subs[title],
                                              subs['url'],
                                              self.subtitles_dir)

                    subtitle_path = os.path.join(self.subtitles_dir,subs[title])
                    #on cr�e une liste des srt(non zip) si jamais unzip = False
                    if not zipfile.is_zipfile(subtitle_path):
                        subs_dict_to_compar[subs['url']]["file_info"] = subs
                        subs_dict_to_compar[subs['url']]["file_subs_list"].append(subtitle_path)

                    #unzip
                    if self.unzip == True or self.unzip == "True":
                        #on prend la liste retourn�e par la fonction unzip
                        zip_files_list = self.Sub.unzip_file(
                                              subtitle_path,
                                              self.subtitles_dir,
                                              self.use_filters,
                                              self.filters_regex)

                        subs_dict_to_compar[subs['url']]["file_info"] = subs
                        subs_dict_to_compar[subs['url']]["file_subs_list"] = zip_files_list
                
                #seulement en mode file, on cr�e le srt qui convient au mieux
                if self.mode in ['file', 'utorrent'] and self.rename_subtitles in [True, 'True']:
                    self.best_subtitle(subs_dict_to_compar, self.movie_path)

        # si il n'y a pas de sous-titres
        else:
            logging.info(self.info('no_sub'))



    def best_subtitle(self, subs_list_to_compar, movie):
        """Algorithme de comparaison +
        renommage du srt qui convient le mieux � l'�pisode

        subs_list_to_compar = {
                             sub_url1: {
                                file_subs_list:[path1, path2, path3],
                                file_info: {language:"vf", quality:"3",...}
                                },
                             sub_url2:{...},
                             ...
                          }
        
        """
        d = subs_list_to_compar
        #seulement si il y a des sous-titres
        if d:
            try:
                score = 0
                winner = ""
                quality = 0
                junk_subtitles = []
                for key in d:
                    file_list = d[key]['file_subs_list']
                    #pour chaque srt
                    for item in file_list:
                        sub_language = d[key]['file_info']['language']
                        sub_quality = d[key]['file_info']['quality']
                        sub_dict = self.file_base(item) #dict with basename, ext,...
                        movie_dict = self.file_base(movie) #dict with basename, ext,...
                        junk_subtitles.append(sub_dict['path'])
                        #si l'utilisateur pr�f�re du fran�ais
                        if self.language_priority.upper() in ["FR", "VF"]:
                            #alors si les sous-titres sont bien en fran�ais
                            if sub_language.upper() in ['VF','VOVF']:
                                #et si parmi ceux pr�sents ils sont bien fr
                                if re.match(".*(\.FR|\.VF)", sub_dict['name'], re.IGNORECASE):
                                    #on compare le titre du srt avec celui du film
                                    compar = difflib.SequenceMatcher(None, movie_dict['name'], sub_dict['name'])
                                    #cela donne un ratio de ressemblance
                                    ratio = compar.ratio()
                                    #on ne va garder que celui dont le ratio est le plus �lev�...
                                    if ratio >= score:
                                        #avec la qualit� la plus �lev�e
                                        if sub_quality >= quality:
                                            score = ratio
                                            quality = sub_quality
                                            winner = sub_dict['path']


                        #si l'utilisateur pr�f�re de l'anglais
                        if self.language_priority.upper() in ["EN", "VO"]:
                            #alors si les sous-titres sont bien en anglais
                            if sub_language.upper() in ['VO','VOVF']:
                                #et si parmi ceux pr�sents ils sont bien anglais
                                if not re.match( ".*(\.FR|\.VF)",
                                                 sub_dict['name'],
                                                 re.IGNORECASE):
                                    #on compare le titre du srt avec celui du film
                                    compar = difflib.SequenceMatcher( None,
                                                                     movie_dict['name'],
                                                                     sub_dict['name'])
                                    #cela donne un ratio de ressemblance
                                    ratio = compar.ratio()
                                    #on ne va garder que celui dont le ratio est le plus �lev�...
                                    if ratio >= score:
                                        # avec la qualit� la plus �lev�e
                                        if sub_quality >= quality:
                                            score = ratio
                                            quality = sub_quality
                                            winner = sub_dict['path']


                if winner == "":
                    score = 0
                    quality = 0
                    for key in d:
                        file_list = d[key]['file_subs_list']
                        #pour chaque srt
                        for item in file_list:
                            sub_language = d[key]['file_info']['language']
                            sub_quality = d[key]['file_info']['quality']
                            sub_dict = self.file_base(item) #dict with basename, ext,...
                            movie_dict = self.file_base(movie) #dict with basename, ext,..
                            #on compare le titre du srt avec celui du film
                            compar= difflib.SequenceMatcher( None,
                                                             movie_dict['name'],
                                                             sub_dict['name'])
                            #cela donne un ratio de ressemblance
                            ratio = compar.ratio()
                            #on ne va garder que celui dont le ratio est le plus �lev�...
                            if ratio >= score:
                                # avec la qualit� la plus �lev�e
                                if sub_quality >= quality:
                                    score = ratio
                                    quality = sub_quality
                                    winner = sub_dict['path']


                #au final, on a le gagnant..
                winner = self.file_base(winner)
                src = winner['path']
                dst = os.path.join(winner['dir'], movie_dict['name']+ winner['ext'])
                #Cr�e une copie du fichier renomm�e
                self.rename_file(src, dst)
                #supprime les autres sous-titres si l'utilisateur le souhaite
                self.remove_junk_subtitles(junk_subtitles)
            except:
                logging.error('Failed to find the best subtitle to rename %s' % movie)
        

    def remove_junk_subtitles(self, junk_subtitles):
        """Supprime les sous-titres restant apr�s avoir r�cup�rer le bon

        """
        if self.keep_only_one_subtitle:
            try:
                #suppresion des dupliqu�s
                junk_subtitles = list(set(junk_subtitles))
                for j in junk_subtitles:
                    os.remove(j)
            except:
                pass


    def rename_file(self, source, destination):
        """Cr�e une copie du fichier

        """
        try:
            shutil.copyfile(source, destination)
        except:
            logging.error('Problem to rename %s' % source)
            pass


    def define_subtitles_dir(self):
        """defintion du dossier de t�l�chargement en fonction des pref utilisateur

        """
        # on d�fnit maintenant le dossier de t�l�chargement des srt
        #si le dossier subs_dir existe,...
        if os.path.isdir(self.subtitles_dir):
            #...on doit t�l�charger srt dans un tout autre dossier
            self.subtitles_dir = self.subtitles_dir
        #si le dossier subs_dir est vide,...
        elif self.subtitles_dir == "":
            #... on doit t�l�charger srt dans le dossier de la vid�o
            self.subtitles_dir = self.default_dir
        #si le dossier subs_dir est un nom,...
        elif self.subtitles_dir[0] == "|":
            #... on doit t�l�charger srt dans dossier special pour chaque video
            special_sub_dir = os.path.join(self.default_dir, self.subtitles_dir[1:])
            if os.path.isdir(special_sub_dir):
                 self.subtitles_dir = special_sub_dir
            else:
                 os.makedirs(special_sub_dir)
                 self.subtitles_dir = special_sub_dir



    def define_video_list(self):
        """Cr�e la liste des vid�os dont les sous-titres devront �tre recup�r�s

        """
        ext = re.split('\|', self.series_extensions)
        #liste des vid�os pr�sentes
        video_list = self.Sub.files_list(  self.default_dir,
                                          extensions=ext,
                                          subfolders=self.use_subfolders)

        #si l'utilisateur ne veut pas de sous-titres si la vid�o en a d�j�
        if self.no_download_if_present:
            #si dossier unique de srt
            if os.path.isdir(self.subtitles_dir):
                #liste des sous-titres pour comparaison
                subtitles_list= self.Sub.files_list(self.subtitles_dir,
                                                  extensions= ['srt'],
                                                  subfolders= self.use_subfolders)
                #videos restantes
                video_list[:] = (video for video in video_list if os.path.join(self.file_base(self.subtitles_dir)["dir"], self.file_base(video)["name"]+".srt") not in subtitles_list)


            #si srt dans dossier vid�o
            elif self.subtitles_dir == "":
                #liste des sous-titres pour comparaison
                subtitles_list= self.Sub.files_list(self.default_dir,
                                                  extensions=['srt'],
                                                  subfolders=self.use_subfolders)
                #videos restantes
                video_list[:] = (video for video in video_list if video[:-4]+".srt" not in subtitles_list)


            #si srt dans dossier sp�cial
            elif self.subtitles_dir[0] == "|":
                #liste des sous-titres pour comparaison
                subtitles_list = self.Sub.files_list(self.default_dir,
                                                  extensions=['srt'],
                                                  subfolders=self.use_subfolders)
                #videos restantes
                video_list[:] = (video for video in video_list if os.path.join(self.file_base(video)["dir"], self.subtitles_dir[1:] ,self.file_base(video)["name"]+".srt") not in subtitles_list)

        #retour la liste final des vid�os
        return video_list






        
    def mode_watched(self, file_path):
        """Marque un �pisode comme t�l�charg� sur BetaSeries

        """
        try:
            file_name = self.file_base(file_path)["name"]
            #extraction des donn�es de la recherche
            data = self.Beta.extract_data(file_name)
            if data == False:
                logging.info('%s%s' % (self.info('extract_info_failed'), file_name))
                os._exit(1)

            #v�rification du nom de la s�rie en la transformant en nom url
            show = data[0].lower()
            show_list = self.Beta.show_url(show)
            #si il y a plusieurs choix de s�ries on prend celui qui correspond le mieux
            for item in show_list:
                #test whether every element in showurl is in show
                if set(item['url']) <= set(show):
                    show=item['url']
                    show_name = item['title']
                else:
                    show = show_list[0]['url']
                    show_name = show_list[0]['title']
            season = data[1]
            episode = data[2]

            watched = self.Beta.member_watched(  self.login, self.password,
                                                show, season, episode)
            if watched == 1:
                logging.info("\n[%s season %s episode %s] is watched on Betaseries !" % (show_name,
                                                                                        season,
                                                                                        episode))
            time.sleep(self.info("sleep"))
            os._exit(1)
        except:
            logging.error('something\'s wrong...')
            time.sleep(self.info("sleep"))
            os._exit(1)




    def mode_statistics(self):
        """Retourne des statistiques sur les subs t�l�charg�s

        """
        logging.info(self.info("working"))
        db = Database(database=self.db_file, stat=True)
        db.get_summary()
        logging.info("\n\n")
        raw_input(self.info("pause"))
        sys.exit(self.info('exit'))

        


    def mode_unzip(self):
        """Elaboration du mode unzip
        
        """
        logging.info(self.info("unzip"))
        reset_default_dir = self.default_dir
        #va chercher tous les zip du dossier
        for zip_file in self.Sub.files_list( self.default_dir,
                                             extensions=['zip'],
                                             subfolders=self.use_subfolders):
                                             
            #dossier du fichier zip
            real_default_dir = "%s\\" % os.path.dirname(zip_file)
            #d�finition du dossier des  vid�os
            self.default_dir = real_default_dir
            #dezippe tous les zips
            self.Sub.unzip_file(  zip_file,
                                  self.default_dir,
                                  self.use_filters,
                                  self.filters_regex)
            logging.info(os.path.basename(zip_file))
            #reset du dossier de t�l�chargement pour la suite
            self.default_dir = reset_default_dir



    def mode_filter(self):
        """Elaboration du mode filter

        """
        logging.info(self.info("filter"))
        ext = re.split('\|', self.extensions_filter_mode)
        #va chercher tous les srt et autres du dossier
        for _file in self.Sub.files_list(  self.default_dir,
                                           extensions=ext,
                                           subfolders=self.use_subfolders):

            if re.search(self.filters_regex, _file) != None:
                #efface les fichiers filtr�s
                os.remove(_file)
                logging.info(os.path.basename(_file))



    def mode_episodes(self):
        """Elaboration du mode episodes
        
        """
        logging.info(self.info("sub_search"))

        subs_list = self.Beta.member_subtitles( self.login,
                                                self.password)
        # Uniquement pour le mode episodes:
        # on doit ajouter title pour normaliser les infos pour la database

        #ajout de la key title manquante dans le dictionnaire
        for sub in subs_list:
            title = sub['url']
            for item in sub['subs']:
                sub['subs'][item]['title'] = title
        #cr�ation de la subs_list � partir du nouveau dictionnaire.
        new_subs_list = []
        for sub in subs_list:
            for item in sub['subs']:
                item_value = sub['subs'][item]
                new_subs_list.append(item_value)

        return new_subs_list


        
    def mode_utorrent(self):
        """Elaboration du mode utorrent
        
        R�cup�re les sous-titres du fichier t�l�charg� dans Utorrent.
        Marque l'�pisode comme t�l�charg�.
        
        """
        #extraction des donn�es de la recherche
        data = self.Beta.extract_data(self.search)
        if data == False:
            logging.info('%s%s' % (self.info('extract_info_failed'), self.search))
            sys.exit(self.info('exit'))
            
        #v�rification du nom de la s�rie en la transformant en nom url
        show = data[0].lower()
        show_list = self.Beta.show_url(show)
        #si il y a plusieurs choix de s�ries on prend celui qui correspond le mieux
        for item in show_list:
            #test whether every element in showurl is in show
            if set(item['url']) <= set(show):
                show = item['url']
            else:
                show = show_list[0]['url']
        season = data[1]
        episode = data[2]
        if self.set_episode_downloaded:
            #marque l'�pisode comme t�l�charg� sur Betaseries
            downloaded = self.Beta.member_downloaded( self.login,
                                                     self.password,
                                                     show, season, episode)
            #affiche message en console en fonction dur retour
            if downloaded == "1":
                logging.info("%s S%sE%s downloaded on Betaseries!" % (
                                                    show,season, episode))
            if downloaded == "0":
                logging.info("%s S%sE%s not downloaded on Betaseries!" % (
                                                      show, season, episode))

        #le mode utorrent �tant similaire, on utilise le mode search.
        subs_list = self.Beta.search_subtitles(show, season, episode)
        #d�finition du nom du fichier
        self.movie_path = os.path.join(self.default_dir, self.search)

        #on d�fini le dossier de t�l�chargement des sous-titres
        self.define_subtitles_dir()
        
        return subs_list
        




    def mode_file(self):
        """Elaboration du mode file
        
        """
        #variable de remise � zero du dossier de t�l�chargement
        reset_default_dir = self.default_dir
        resest_subtitles_dir = self.subtitles_dir
        video_list = self.define_video_list()

        #si il n'y a aucune video
        if not video_list:
            logging.info("You've no need BetaSub right now !")
            time.sleep(self.info("sleep"))
            sys.exit()
            
        for files in video_list:
            #dossier du fichier vid�o

            #real_default_dir = "%s\\" % os.path.dirname(files)
            real_default_dir = os.path.dirname(files) + os.sep
            #liste des srt du fichier
            subs_list = self.Beta.file_subtitles(files)

            if not subs_list != []:
                file_name = self.file_base(files)['name']
                logging.info("No Subtitles for %s" % file_name)
                pass
            else:
                #d�finition du dossier des  vid�os
                self.default_dir = real_default_dir
                #on d�fini le dossier de t�l�chargement des sous-titres
                self.define_subtitles_dir()
                #d�finition du nom du fichier
                self.movie_path = files
                #t�l�chargement
                self.get_subtitles(subs_list)

                #reset du dossier de t�l�chargement pour la suite
                self.default_dir = reset_default_dir
                self.subtitles_dir = resest_subtitles_dir



        
    def mode_prompt(self):
        """Elaboration du mode prompt

        """
        search = raw_input('search show: ')
        #v�rifie si la recherche ne correspond pas � plusieurs shows
        show = self.show_choice(search)
        print
        logging.info("show:     %s" % show['title'])
        season = raw_input("season:   ")
        episode = raw_input("episode:  ")
        language = raw_input("language: ")
        print
        logging.info(self.info("sub_search"))
        subs_list = self.Beta.search_subtitles(show['url'], season, episode, language)
        return subs_list


    def mode_search(self):
        """Elaboration du mode search

        """
        while len(self.search) < 2:
            logging.info(self.info('warning_mode_search'))
            self.search = raw_input('search: ')
        #astuce pour switcher de mode.
        if self.search in ['episodes', 'prompt', 'file', 'stat', 'unzip', 'filter']:
            self.mode = self.search
            self.mode_operation()
        else:
            #extraction des donn�es de la recherche
            data = self.Beta.extract_data(self.search)

            #test1 : si c'est � cause des espaces
            if data == False:
                data2 = "%s %s" % (self.search,self.args)
                data = self.Beta.extract_data(data2)
                #test2
                if data == False:
                    data = self.Beta.extract_data(self.args)
                    if data == False:
                        #r�initialisation de la recherche
                        self.search = ""
                        self.mode_operation()
                    

        #v�rifie si la recherche ne correspond pas � plusieurs shows
        show = self.show_choice(data[0])
        season = data[1]
        episode = data[2]
        language = data[3]
        logging.info("\n%s  season:%s  episode:%s  language:%s\n" % (show['title'], season, episode, language))
        logging.info(self.info("sub_search"))
        subs_list = self.Beta.search_subtitles(show['url'], season, episode, language)
        return subs_list



    def show_choice(self, search):
        """Si une recherche retourne plusieurs s�ries, permet � l'utilisateur de la pr�ciser.

        """
        if len(search) >= 2:
            shows_listing = self.Beta.show_url(search)
            #en fonction du nombre de r�sultats trouv�s...
            list_length = len(shows_listing)
            # si pas de s�ries...
            if list_length == 0:
                logging.info("%s... %s" % (search, self.info("show_not_exist")))
                if self.mode == "prompt":
                    self.mode_operation()

            # si une seule s�rie est trouv�e, on passe directement
            elif list_length == 1:
                return shows_listing[0]
            # si plusieurs s�ries sont trouv�es on retourne la liste
            else:
                logging.info('\n  %s %s' % (list_length,self.info('show_founded')))
                for num,shows in enumerate(shows_listing):
                    logging.info("    %s %s" %(num, shows['title']))
                # on demande � l'utisateur de choisir un num�ro
                show_choice = int(raw_input("\n  show number: "))
                return shows_listing[show_choice]
                
        else:
            logging.error(self.info('warning_search'))
            if self.mode == "prompt":
                self.mode_operation()



    def file_base(self, file_path):
        """return a dict with filename,ext,dir and path from a file path

        """
        d = {}
        file_name, file_ext = os.path.splitext(file_path)
        file_name = os.path.basename(file_name)
        dir_path = os.path.dirname(file_path)
        d['name'] = file_name
        d['ext'] = file_ext
        d['path'] = file_path
        d['dir'] = dir_path
        return d



    def command_line(self):
        """Retourne les arguments fournis en ligne de commande.
        
        Example:
        betasubs.py --mode=episodes --directory=c://download//subs// --unzip=True

        Remarques:
        * l'argument --mode= est obligatoire pour commencer.
        * les autres arguments ne sont pas obligatoires � partir du moment o� les options par d�fauts sont d�finies.
        * les arguments ont priorit� sur les options par d�faut.
        * Si un argument n�cessaire � un mode n'est pas fourni, c'est l'option par d�faut qui est prise.
        * les donn�es avec espace doivent �tre mise entre guillemets.
          ex: --search="Desperate Housewife"

        """
        usage = 'use: %prog --mode=file --directory="c:\\download\\subs\\" --unzip=True'
        parser = OptionParser(usage=usage)
        parser.add_option("-m","--mode", dest="mode",
                          help="mode to use: episodes/search/prompt/file/unzip/filter/stat")
                          
        parser.add_option("-l","--login", dest="login",
                          help="login")

        parser.add_option("-p","--password", dest="password",
                          help="password")

        parser.add_option("-d","--directory", dest="default_directory",
                          help="subtitles directory.  Use double slash // ")

        parser.add_option("--subfolders", dest="subfolders",
                          help="use subfolders. True or False")

        parser.add_option("-u","--unzip",dest="unzip",
                          help="unzip subtitles from files")

        parser.add_option("-f","--filters",dest="filters",
                          help="use filters.  Accept regex")

        parser.add_option("--database",dest="database",
                          help="use database")
                          
        parser.add_option("--updater", dest="updater",
                          help="use updater")
                          
        parser.add_option("--freq", dest="frequency",
                          help="Updater frequency in secondes")

        parser.add_option("-s","--search", dest="search",
                          help="Search subtitles.  Search must be 2 or more characters")

        parser.add_option("--rename", dest="rename_subtitles",
                          help="Rename subtitles")
                          
        parser.add_option("--quotes", dest="use_quotes",
                          help="use quotes")

        parser.add_option("--langpriority", dest="language_priority",
                          help="Set the language priority")

        parser.add_option("--seriesext", dest="series_extensions",
                          help="Series extentions to consider")
                          
        parser.add_option("--downloaded", dest="set_episode_downloaded",
                          help="Set donwloaded episode on Betaseris")

        parser.add_option("--filterext", dest="extensions_filter_mode",
                          help="extensions to consider in filter mode")
                          
        parser.add_option("--subsdir", dest="subtitles_directory",
                          help="subtitles directory")
                          
        parser.add_option("--qualitysub", dest="quality_subtitles",
                          help="Define quality subtitles")

        parser.add_option("--languagesub", dest="language_subtitles",
                          help="Define language subtitles")

        parser.add_option("--nodlifpresent", dest="no_download_if_present",
                          help="No download if video have already subtitles")
                                  
        parser.add_option("--onlyone", dest="keep_only_one_subtitle",
                          help="Keep only one subtitle for the video")
                          
        #si l'aide est demand�e, on l'affiche et ferme le programme
        if sys.argv[1] in ["-h", "--help"]:
            parser.print_help()
            raw_input(self.info("pause"))
            os._exit(1)

        else:
            return parser.parse_args()

            

    def updater(self, frequence, action):
        """Lance une action en boucle � une frequence donn�e en sec.
        
        Fonction mise en place pour mettre � jour le dossier de t�l�chargement des sous-titres.

        """
        Timer(1, action, ()).start()
        #on passe en boucle
        time.sleep(float(frequence))
        print "\n\n"
        self.updater(frequence,action)



    def splash(self):
        """Splash infos at the top
        
        """
        #si on utilise les citations
        if self.use_quotes:
            logging.info("[Mode %s] BetaSub %s\n\n%s\n\n" % ( self.mode,
                                                              __version__,
                                                              self.quotes() ))
        else:
            logging.info("[Mode %s] BetaSub %s\n\n" % ( self.mode,
                                                              __version__))



        
    def quotes(self):
        q = ['Is that your final answer?', 'Yabba dabba do!',
        'The truth is out there.', 'Don\'t stop, believin\'!',
        'Just one more thing ...', 'Tell me what you don\'t like about yourself.',
        'That\'s what she said.', 'I have a bad feeling about this.', 'Whoa!',
        'Resistance is futile.', 'Yatta!', 'I don\'t want Garbage! I want Sprinkles!',
        'You are an impressive specimen.','We provide... Leverage!',
        'Look, you want to push the button, you do it yourself.',
        'See you in another life then, eh brother?', 'Are you Donald Draper?',
        'Oh, hi. Lisbon. Still here?','Damn good coffee!',
        'There\'s an old Italian saying: you fuck up once, you lose two teeth.',  
        'Freakin\' SHWEEET!', 'I am not a number, I am a free man!',
        'It\'s dreadful!', 'I\'m sorry, I don\'t know what that is. Massive Dynamics...',
        'Who\'s Bone-oh?  It\'s Bono, actually. He\'s a musician.',
        'There has got to be a scientific explanation to this!',
        'I\'m normally not a praying man, but if you\'re up there, please save me Superman.',
        'Read less, more TV.', 'They killed Kenny!', 'Go Panter!',
        'I hate television. I hate it as much as peanuts. But I can\'t stop eating peanuts.',
        'I got sick of turning on the TV and seeing my face.',
        'Louis Brazzi sleeps with the fishes.',
        'You prefer Corrado or Junior? I prefer Mr. Soprano.',
        'You can\'t take a picture of this. It\'s already gone.',
        'I am aware of the reality of death. I work with it every day.',
        'He had a nickname at the academy... Spooky Mulder.',
        '... in most of my work, the laws of physics rarely seems to apply.'
        ]
        return random.choice(q)



    def info(self, value):
        """Retourne les messages pour la console.

        La fonction est mise en place dans le but de faciliter:
            1)les changements
            2)les traductions en/fr
        
        """
        message_en = dict(
        critical_mode         = "Mode is not define or not correctly define",
        critical_dir          = "default_directory is not define or not correctly define",
        critical_subsdir      = "Subtitles_directory is not correctly define",
        pause                 = "Press ENTER to exit",
        sleep                 = 3,
        warning_mode_search   = "Holy crap!\nThe search must:\n    1) use a pattern like: dexter s01e01  or  the office 3\n    2) be more than 2 chararcter\n\n",
        warning_mode          = "You must provide mode parameter --mode=episodes/file/search/prompt/utorrent/unzip/filter",
        warning_cmdl          = 'Frak!\nIt seems you use command line.\n\nYou must at least provide MODE argument to start:\n\n--mode=episodes/search/file/prompt/unzip/filter/stat\n\n\nexample:   BetaSub.py --mode=episodes   ',
        warning_search        = 'Show title must be 2 or more characters.\n',
        show_not_exist        = 'This show do not exist on Betaseries!\n',
        dir_not_exist         = 'D\'oh! Subtitles directory do not exist.  Verify settings or create the subtitles directory\n',
        show_founded          = 'shows founded:\n',
        sub_search            = "Search subtitles...\n",
        sub_downloaded        = 'Woo-hoo! All subtitles are already downloaded!',
        sub_downloaded_for    = 'Subtitles already downloaded for',
        sub_download          = 'subtitles to download', #pas de majuscule
        unzip                 = 'Unzip...\n',
        filter                = 'Filter...\n',
        working               = 'Working...\n',
        no_file               = 'No videos or movies in you default directory.\n',
        no_sub                = 'No Subtitles at the moment for all you files. Try later!',
        no_unzip              = 'No file to unzip\n',
        no_match              = 'No match',
        extract_error         = 'Frak! Search failed...',
        using_updater         = 'You activate the updater!\nsec:',
        extract_info_failed   = 'extract infos failed with file:',
        exit                  = 'exit program.'

        )
        
        return message_en[value]


class Database:
    """Base de donn�e de BetSub.  Cr�ation, R�cup�ration, statistiques.

    Important: Pour activer les statistiques,
               il faut d�clarer dans l'instanciation stat=True

    !!! cr�er des statistics pour les dates.
    """
    def __init__(self, database='betasub.db', stat=False):
        """itialisation des variables

        """
        self.db = database

        #creation de la base de donn�e
        database = sqlite3.connect(self.db)
        database.close()

        #si on veux des statistiques:
        if stat:
            try:
                self.dbdata = self.get_data()
            except:
                logging.warning('no data to make statistics')


    def set_data(self, title, url):
        """Enregistre les donn�es dans la base.

        """
        database = sqlite3.connect(self.db)
        cur = database.cursor()
        try:
            # Create base
            cur.execute("CREATE TABLE betasub (title TEXT, subs TEXT, time TEXT)")
        except:
            pass
        #place les valeurr dans la base
        cur.execute("INSERT INTO betasub VALUES ('%s','%s','%s')"%( title,
                                                                    url,
                                                                    time.time()
                                                                    ))
        #enregistre dans la base de donn�e
        database.commit()
        cur.close()


    def get_data(self):
        """R�cup�re les donn�es de la base
        
        {0: {'url': u'srt4_url', 'time': u'1299089210.94', 'title': u'criminal'},
         1: {'url': u'srt4_url', 'time': u'1299089212.16', 'title': u'criminal'},...}
         
        """
        database = sqlite3.connect(self.db)
        cur = database.cursor()
        try:
            #va chercher les colonne dans l'ordre SELECT
            cur.execute("SELECT title, subs, time FROM betasub")
        except:
            pass

        #cr�ation du dictionnaire de retour
        db = {}
        for num, values in enumerate(cur):
            db[num] = {'title': values[0], 'url': values[1], 'time': values[2]}
        cur.close()
        database.close()

        return db


    def get_urls(self):
        """retourne la liste des url pr�sentes dans la base de donn�e
        
        � utiliser pour le programme.
        
        """
        urls_list = []
        db = self.get_data()
        for i in db:
            urls_list.append(db[i]['url'])
        return urls_list


    def get_titles(self):
        """retourne la liste des s�ries pr�sentes dans la base de donn�e

        """
        titles_list = []
        db = self.dbdata
        for i in db:
            titles_list.append(db[i]['title'])
        titles_list = set(titles_list)

        return list(titles_list)


    def get_len(self):
        """Retourne le nombre de srt t�l�charg�s

        """
        db = self.dbdata
        return len(db)


    def get_show_info(self, show):
        """retourne les infos du show.

        """
        beta = Beta()
        show_list = beta.show_url(show)
        #si il y a plusieurs choix de s�ries on prend celui qui correspond le mieux
        for item in show_list:
            #test whether every element in showurl is in show
            if set(item['url']) <= set(show):
                show = item['url']
            else:
                show = show_list[0]['url']

        show_info = beta.show_info(show)
        return show_info


    def get_top_genres(self):
        """top des srt clas�s par s�ries et par occurences

        [(3, u'Drama'), (3, u'Action and Adventure'), (2, u'Science-Fiction')]

        """
        genres = {}
        for show in self.get_titles():
            genres_list =self.get_show_info(show)['genres'].values()
            for genre in genres_list:
                genres[genre] = genres.get(genre, 0)+1

        genres = sorted(((value,key) for key,value in genres.items()), reverse=True)
        return genres


    def get_top_series(self):
        """top des srt class�s par s�ries et par occurences

        [(3, u'fringe'), (3, u'criminal'), (2, u'friends'), (1, u'heroes')]

        """
        db = self.get_data()
        series = {}
        for i in db:
            series[db[i]['title']] = series.get(db[i]['title'], 0)+1

        series = sorted(((value,key) for key,value in series.items()), reverse=True)
        return series


    def get_summary(self):
        """retourne les donn�es mises en forme.  Peut �tre imprim� ou affich�.
        
        """
        total = self.get_len()
        series = self.get_top_series()
        genres = self.get_top_genres()
        #head
        logging.info("SUBTITLES STATISTICS\n====================")
        #total
        logging.info("\nTOTAL DOWNLOADED: %s" % total)
        #top series
        logging.info("\nTOP SERIES:")
        for n,s in series:
            average = "%.1f" % (float(100)/float(total)*float(n))
            logging.info("   %s  %s (%s%%)" %(n, s, average))
        #top genres
        logging.info("\nTOP GENRES:")
        #calcul de la quantit� de genres par s�rie pr�sentes
        len_genres = 0
        for n,s in genres:
            len_genres = len_genres+n
        
        for n,g in genres:
            average = "%.1f" % (float(100)/float(len_genres)*float(n))
            logging.info("   %s  %s (%s%%)" %(n, g, average))




class Settings:
    """Load Settings.
    
    R�cup�re la config.

    """
    def __init__(self, settings_file="settings.ini"):
        """itialisation des variables

        """
        self.settings_file = settings_file
        #v�rifie que settings file existe
        if os.path.isfile(self.settings_file):
            self.load = self.load_settings()
        else:
            logging.error("no settings file !")
            sys.exit()

        
    def load_settings(self):
        """load settings

        """
        config = ConfigParser.ConfigParser()
        config.read(self.settings_file)
        settings = config.items("Default")
        # retourne keys_config en dictionnaire
        sett = {}
        for i in settings:
            sett[i[0]] = i[1]

        sett = self.validate_settings(sett)
        return sett

        
    def validate_settings(self, original_settings):
        """Transform boolean in dictionnary. Return a copy
        
        """
        bool = {"false":False, "true":True}
        settings = original_settings

        for key in settings:
            value = settings.get(key).lower()
            #si la valeur est cens�e �tre boolean
            if value.lower() == "true" or value.lower() == "false":
                #transforme la valeur en boolean
                settings[key] = bool[value]
            #si value est int
            if re.match('^\d+$',value):
                settings[key] = int(value)

        return settings



 
# importation du module sans l'executer
if __name__ == "__main__":
    #d�fini le dossier de travail � partir de BetaSub > pour mode utorrent
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    set_ = Settings("settings.ini").load

    Program( mode                    = set_['mode'],
             login                   = set_['login'],
             password                = set_['password'],
             use_database            = set_['use_database'],
             unzip                   = set_['unzip_files'],
             use_filters             = set_['use_filters'],
             filters_regex           = set_['filters_regex'],
             use_updater             = set_['use_updater'],
             delay_sec               = set_['updater_freq_sec'],
             use_subfolders          = set_['use_subdirectories'],
             rename_subtitles        = set_['rename_subtitles'],
             language_priority       = set_['language_priority'],
             set_episode_downloaded  = set_['set_episode_downloaded'],
             series_extensions       = set_['series_extensions'],
             default_directory       = set_['default_directory'],
             subtitles_directory     = set_['subtitles_directory'],
             extensions_filter_mode  = set_['extensions_filter_mode'],
             use_quotes              = set_['use_quotes'],
             quality_subtitles       = set_['quality_subtitles'],
             language_subtitles      = set_['language_subtitles'],
             no_download_if_present  = set_['no_download_if_present'],
             keep_only_one_subtitle  = set_['keep_only_one_subtitle']
             )


