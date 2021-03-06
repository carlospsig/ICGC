# -*- coding: utf-8 -*-
"""
/***************************************************************************
 icgcPSI
                                 A QGIS plugin
 Plugin para el ICGC
                              -------------------
        begin                : 2017-12-12
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Sergio Illera
        email                : sergiollera22@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication,QDate, Qt
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QMessageBox
from PyQt4.QtSql import *
from qgis.core import *
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from icgcPSI_dialog import icgcPSIDialog
import os.path
import csv
from psi_config import params

class icgcPSI:
    """QGIS Plugin Implementation."""

    """ GLOBAL VARIABLES INSIDE THE CLASS"""
    processat=[]
    Flagprocessat=False
    Flagcampaing=True
    conectardb={}

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'icgcPSI_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&icgcPSI')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'icgcPSI')
        self.toolbar.setObjectName(u'icgcPSI')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('icgcPSI', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.fv

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = icgcPSIDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/icgcPSI/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'icgc PSI plugin'),
            callback=self.run,
            parent=self.iface.mainWindow())
       
        #tab 1 buttons-----------------------------------------------------------
        self.dlg.pBloaddoc.clicked.connect(self.write_to_documentcitation)
        self.dlg.pBloadgeocol.clicked.connect(self.write_to_geocol)
        self.dlg.pBloadcamp.clicked.connect(self.write_to_campaing)
            #tab1 checkbuttons
        self.dlg.cBcampanya.stateChanged.connect(self.show_campbutton) #funcion asociada al checkbox campaigns             
        self.dlg.cBdocumentacio.stateChanged.connect(self.show_docbutton) #funcion asociada al checkbox documentacio
        self.dlg.cBgeocol.stateChanged.connect(self.show_geocolbutton) #funcion asociada al checkbox de projecte
        #--------------------------------------------------------------------------        
        
        #tab2 buttons----------------------------------------------------------------------
        self.dlg.pBloadcsvprocessat.clicked.connect(self.load_csvprocessat) #buscar archivo procesat
        self.dlg.pBloadcsv.clicked.connect(self.cargar_foldercsvdades) #buscar la carpeta de archivos csv
        self.dlg.pBloadprocessat.clicked.connect(self.write_to_processat) #escribir en la tabla processat
        self.dlg.pBcarregardades.clicked.connect(self.carregar_dades) #iniciar carga de datos 
            #tab2 checkbuttons
        self.dlg.cBdades.stateChanged.connect(self.show_dadesbutton) #funcion asociada al checkbox de load dades
        #----------------------------------------------------------------------------------
        
        #tab3 buttons-----------------------------------------------------------------------
        self.dlg.QPBcampinfo.clicked.connect(self.show_campaign_info)
        self.dlg.pBdeleteobs.clicked.connect(self.delete_observationname)
        self.dlg.QPBobsinfo.clicked.connect(self.show_obsinfo)
        self.dlg.QPBcampdelete.clicked.connect(self.delete_campaign)
        #-----------------------------------------------------------------------------------
        
        #tab4 buttons------------------------------------------------------------------------
        self.dlg.pBloadshp.clicked.connect(self.cargar_csv)
        self.dlg.pBcarregar.clicked.connect(self.carregarpunts)
        #------------------------------------------------------------------------------------
        
    
    
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&icgcPSI'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        
        ###SET VISIBLE OR NOT SOME LABELS INITIALLY++++++++++++++++++++++++++++++++++++++
        #tab1------------------------------------------------------------
        self.dlg.dateEdit.setDate(QDate.currentDate()) #current date in doc calendar
        self.dlg.datepojectinit.setDate(QDate.currentDate()) #current date in inici project
        self.dlg.datepojectfin.setDate(QDate.currentDate()) #current date in end project
        self.dlg.pBloaddoc.setVisible(False) #doccitation button
        self.dlg.pBloaddoc.setEnabled(False) 
        self.dlg.pBloadgeocol.setVisible(False) #projecte (geocol) button
        self.dlg.pBloadgeocol.setEnabled(False)
        self.dlg.pBloadcamp.setVisible(False) #campaign button
        self.dlg.pBloadcamp.setEnabled(False)
        #----------------------------------------------------------------
        
        #tab2------------------------------------------------------------
        self.dlg.pathcsvprocessat.clear()
        self.dlg.lEloadpath.clear() #clear the label text box (load shp path)
        self.dlg.pBcarregardades.setVisible(False) #carregar dades button
        self.dlg.pBcarregardades.setEnabled(False)
        #----------------------------------------------------------------
        
        #tab3------------------------------------------------------------
        self.dlg.campainglist.clear() #clear campaing combobox 
        #----------------------------------------------------------------
        
        #tab4------------------------------------------------------------
        #----------------------------------------------------------------
        
        #conexion to DB  (only once when the GUI is created)
        self.conectardb = self.connecttobd() 
        
        #POPULATE INITIALLY THE COMBOBOXS
        #tab1------------------------------------------------------------
        self.show_bd_doccitation() #show table I documentation combobox
        self.show_bd_geocol() #show table I prOyecte combobox (geocolection)
        self.show_bd_campaigns() #show campaigns name combobox (in all tables)
        self.show_void() #show table I projecte void
        #----------------------------------------------------------------

        #tab2------------------------------------------------------------
        self.show_processats() #show list of precessats
        #----------------------------------------------------------------
        
        #tab3------------------------------------------------------------
        #self.show_bd_campaigns() #called in tab I
        #----------------------------------------------------------------
        
        #tab4------------------------------------------------------------
        #----------------------------------------------------------------
        
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass


#####ERROR MISSAGE FUNCTION++++++++++++++++++++++++++++++++++++++++++++++++++++
    def Missatge(self,t,title="Error"): #error missatge function
            m = QMessageBox()
            m.setIcon(QMessageBox.Warning)
            m.setWindowTitle(title)
            m.setText(t)
            m.setStandardButtons(QMessageBox.Ok);
            m.setButtonText(QMessageBox.Ok,"Segueix")
            m.exec_() 
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


###################  READING FUNCTIONS ##############################        
    def cargar_foldercsvdades(self):
        #choose directory path
        self.dlg.lEloadpath.clear()
        path_dir=QFileDialog().getExistingDirectory(
            self.dlg,
            'Open folder',
            'C:\Users')
        self.dlg.lEloadpath.setText(path_dir)
        
    
    def load_csvprocessat(self): #read csv processat file
        self.dlg.pathcsvprocessat.clear()
        csvprocessfile = QFileDialog.getOpenFileName(self.dlg, self.tr(u'Selecció arxiu processat'),'C:\Users')
        self.dlg.pathcsvprocessat.setText(str(csvprocessfile))
        self.processat=[]
        self.Flagprocessat=False
        if str(csvprocessfile)[-4:]=='.csv': #check if file is a csv
            archivo=open(str(csvprocessfile),'r')
            reader=csv.reader(archivo)
            for row in reader:
                row=row[0].split(';')
                self.processat.append(row)
            archivo.close()
            self.Flagprocessat=True
        else:
            self.Missatge(self.tr(u"L'Arxiu no es .csv\n"))
            csvprocessfile=''
            self.dlg.pathcsvprocessat.clear()
        return 
            
    
#------------------------------------------------------------------------------

#########FUNCTIONS DATA BASE INTERFACE+++++++++++++++++++++++++++++++++++++++++

    def connecttobd(self):#connect to the bd
        db = QSqlDatabase.addDatabase(params[0]) 
        db.setHostName(params[1]) 
        db.setDatabaseName(params[2])
        db.setPort(params[3]) 
        db.setUserName(params[4]) 
        db.setPassword(params[5]) 
        db.open()
        if db.isOpen(): 
            #print 'Abieto sql'
            self.Missatge(self.tr(u'Conectat a la base de dades\nBase de dades: {} '.format(params[2])),'Informacio')
        else:
            #print 'Error al abrir sql'
            db.close()
            self.Missatge(self.tr(u"Error al conectar a la base de dades!\n")+db.lastError().text())
        return db
        

    def obtain_max_id(self,query,tabla,nombreid):
        lastid=0
        if query.exec_('SELECT {0} FROM {1} ORDER BY {0} DESC limit 1'.format(nombreid,tabla))==0:
            self.Missatge(self.tr(u"Error al consultar\n")+query.lastError().text())
            return
        else:
            while query.next():
                lastid = query.value(0)
        return lastid 
        
    
    def isinbd(self,query,tabla,campo,valor,campoid):
        exist=False #flag if exist
        ide=0
        if query.exec_('SELECT {0} FROM {1} WHERE {2}=\'{3}\';'.format(campoid,tabla,campo,valor))==0:
            self.Missatge(self.tr(u"Error al consultar\n")+query.lastError().text())
        else:
            exist=False
            while query.next():
                exist=True
                ide= query.value(0)
            return exist,ide
        
      
#---------------------------------------------------------------------------------------
        
# POPULATE COMBOBOX FUNCTIONS+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def show_bd_doccitation(self):
        '''
        Docstring: mostremos en la comboBox de la tabla I el campo short name de todos los registros
        de la tabla document citation
        '''
        #show all doccitation in the combobox
        
        db = self.conectardb 
        query = QSqlQuery(db)
        if query.exec_('SELECT shortname FROM documentcitation;')==0:
            self.Missatge(self.tr(u"Error:{}\n".format(query.lastError().text())))
        docs=[]
        docs.append('')
        while query.next():
            docs.append(str(query.value(0)))
        self.dlg.CBshortnamedoccit.addItems(docs)
        self.dlg.CBsprojdoccit.addItems(docs)
        self.dlg.CBdoccitdades.addItems(docs)
        
        
    def show_bd_geocol(self):
        '''
        Docstring: mostremos en el combobox de la tabla I en la zona de poyectos la lista de proyectos
        ya existentes en la tabla geocolection
        '''
        db = self.conectardb 
        query = QSqlQuery(db)
        if query.exec_('SELECT inspireid FROM geologiccollection;')==0:
            self.Missatge(self.tr(u"Error:{}\n".format(query.lastError().text())))
        geocol=[]
        while query.next():
            geocol.append(str(query.value(0)))
        self.dlg.CBgeocol.addItems(geocol)
        self.dlg.CBgeocoldades.addItems(geocol)
        
        
    def show_bd_campaigns(self):
        '''
        Docstring:  mostremos en el combobox de la tabla I en la zona de campañas la lista de campañas
        ya existentes en la tabla campaign
        '''
        db = self.conectardb 
        query = QSqlQuery(db)
        if query.exec_('SELECT name FROM campaign;')==0:
           self.Missatge(self.tr(u"Error:{}\n".format(query.lastError().text())))
        campaings=[]
        while query.next():
            campaings.append(str(query.value(0)))
        self.dlg.CBcamp.addItems(campaings)
        self.dlg.CBcampdades.addItems(campaings)
        self.dlg.campainglist.addItems(campaings)
        
        
    def show_void(self):
        '''
        Docstring: mostremos los voids en los comboboxs
        '''
        db = self.conectardb 
        query = QSqlQuery(db)
        if query.exec_('SELECT voidtypevalue FROM cl_voidtypevalue;')==0:
            self.Missatge(self.tr(u"Error:{}\n".format(query.lastError().text())))
        voids=[]
        voids.append('')
        while query.next():
            voids.append(str(query.value(0)))
        self.dlg.CBprojecvoid.addItems(voids) #table I,projecte void
        self.dlg.CBclient_void.addItems(voids) #table I, campign client void
        self.dlg.CBcontractor_void.addItems(voids) #table I, contractor client void
        self.dlg.CBdistnfo_void.addItems(voids) #table II, distribution info (metadades) void
        self.dlg.CBinformevoid.addItems(voids)
        
    def show_processats(self):
        '''
        Docstring: mostremos los processats en los comboboxs
        '''        
        db = self.conectardb 
        query = QSqlQuery(db)
        if query.exec_('SELECT name FROM processes;')==0:
            self.Missatge(self.tr(u"Error:{}\n".format(query.lastError().text())))
        processats=[]
        while query.next():
            processats.append(str(query.value(0)))
        self.dlg.CBprocessats.addItems(processats) #table II, list of processats
        
        
#-----------------------------------------------------------------------------------    

# ++++++++++++++++++++++++++ SHOW HIDDEN BUTTONS +++++++++++++++++++++++++++++++++++
    def show_dadesbutton(self):
        if self.dlg.cBdades.isChecked():
            self.dlg.pBcarregardades.setVisible(True)
            self.dlg.pBcarregardades.setEnabled(True) 
        else:
            self.dlg.pBcarregardades.setVisible(False) 
            self.dlg.pBcarregardades.setEnabled(False)

    def show_geocolbutton(self):
        if self.dlg.cBgeocol.isChecked():
            self.dlg.pBloadgeocol.setVisible(True)
            self.dlg.pBloadgeocol.setEnabled(True) 
        else:
            self.dlg.pBloadgeocol.setVisible(False) 
            self.dlg.pBloadgeocol.setEnabled(False) 

    def show_docbutton(self):
        if self.dlg.cBdocumentacio.isChecked():
            self.dlg.pBloaddoc.setVisible(True) 
            self.dlg.pBloaddoc.setEnabled(True) 
        else:
            self.dlg.pBloaddoc.setVisible(False) 
            self.dlg.pBloaddoc.setEnabled(False) 
            
    def show_campbutton(self):
        if self.dlg.cBcampanya.isChecked():
            self.dlg.pBloadcamp.setVisible(True) 
            self.dlg.pBloadcamp.setEnabled(True)
        else:
            self.dlg.pBloadcamp.setVisible(False) 
            self.dlg.pBloadcamp.setEnabled(False)

#----------------------------------------------------------------------------------
        
# ++++++++++++++++++++++++++  TABLE I FUNCTIONS +++++++++++++++++++++++++++++++++++

    def write_to_campaing(self):
        '''
        Docstring: escribir en la tabla campaign los datos de la gui
        '''
        db = self.conectardb 
        query = QSqlQuery(db)
        
        tabla='campaign'  
        id_survey=18
        id_camptype=3
        
        client=self.dlg.QLEclient.text()
        if client=='':
            client=None
            void=self.dlg.CBclient_void.currentText() #get from the  campaign client combobox void text
            if void=='':
                self.Missatge(self.tr(u"El camp client esta buit. Indica el perque"))
                return
            exist,client_void = self.isinbd(query,'cl_voidtypevalue','voidtypevalue',void,'voidtypevalueid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el void ide"))
                return 
        else:
            client_void=None
        
        contractor=self.dlg.QLEcontractor.text()
        if contractor=='':
            contractor=None
            void=self.dlg.CBcontractor_void.currentText() #get from the  campaign contractor combobox void text
            if void=='':
                self.Missatge(self.tr(u"El camp contractant esta buit. Indica el perque"))
                return
            exist,contractor_void = self.isinbd(query,'cl_voidtypevalue','voidtypevalue',void,'voidtypevalueid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el void ide"))
                return 
        else:
            contractor_void=None
        
        name=self.dlg.QLEcampname.text()
        
        campos='surveytype,campaigntype,client,client_void,contractor,contractor_void,name'
        query.prepare('INSERT INTO {} ({}) VALUES (:1,:2,:3,:4,:5,:6,:7);'.format(tabla,campos))
        query.bindValue(':1',id_survey)
        query.bindValue(':2',id_camptype)
        query.bindValue(':3',client)
        query.bindValue(':4',client_void)
        query.bindValue(':5',contractor)
        query.bindValue(':6',contractor_void)
        query.bindValue(':7',name)

        if query.exec_()==0:
            self.Missatge(self.tr(u"Error al actualitzar la taula {}\n".format(tabla))+query.lastError().text())
            return 
        else:
            self.Missatge(self.tr(u"Campanya carregada\n"),'Informacio') 
            self.dlg.CBcamp.addItems([name])
            self.dlg.CBcampdades.addItems([name])
            self.dlg.campainglist.addItems([name])
            self.dlg.QLEcampname.clear()
            self.dlg.QLEcontractor.clear()
            self.dlg.QLEclient.clear()


    def write_to_geocol(self):
        '''
        Docstring: escribir en la tabla geologiccolection los datos de la gui
        '''
        tabla='geologiccollection'
        db=self.conectardb     #create the connection and the Query        
        query = QSqlQuery(db)
        
        inspireid=self.dlg.QLEprojectcodi.text()
        name=self.dlg.QLEprojectname.text()
        
        #referencia (to doccitation)
        reference=self.dlg.CBsprojdoccit.currentText()
        if reference=='':
            if self.dlg.CBinformevoid.currentText()=='':
               self.Missatge(self.tr(u"El camp informe esta buit. Indica un motiu"))
               return
            else:
               reference=None
               exist,void_ide = self.isinbd(query,'cl_voidtypevalue','voidtypevalue',self.dlg.CBinformevoid.currentText(),'voidtypevalueid')
               if exist==0:
                   self.Missatge(self.tr(u"Error al buscar el void ide"))
                   return
        else:
            exist,ide=self.isinbd(query,'documentcitation','shortname',reference,'documentcitationid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar la documentcitation ide"))
                return
            reference=ide
            void_ide=None
        
        #fecha inicio
        fechainit=str(self.dlg.datepojectinit.date().year())+'-'       
        fechainit=fechainit+str(self.dlg.datepojectinit.date().month())+'-' 
        fechainit=fechainit+str(self.dlg.datepojectinit.date().day())
        
        #fecha fin
        if self.dlg.checkBoxprojectedate.isChecked():
            fechafin=None
            void=self.dlg.CBprojecvoid.currentText() #get from the  project combobox void text
            if void=='':
                self.Missatge(self.tr(u"Indica perque la data final esta buida"))
                return
            exist,ide = self.isinbd(query,'cl_voidtypevalue','voidtypevalue',void,'voidtypevalueid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el void ide"))
                return
            endlife_void=ide
        else:
            fechafin=str(self.dlg.datepojectfin.date().year())+'-'       
            fechafin=fechafin+str(self.dlg.datepojectfin.date().month())+'-' 
            fechafin=fechafin+str(self.dlg.datepojectfin.date().day())  
            endlife_void=None
        
        if name=='':
            self.Missatge(self.tr(u"El camp Nom del projecte no pot estar buit"))
            return
         
        campos='inspireid,name,collectiontype,reference,reference_void,beginlifespanversion,beginlifespanversion_void,'
        campos+='endlifespanversion,endlifespanversion_void'
        query.prepare('INSERT INTO {} ({}) VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9);'.format(tabla,campos))
        query.bindValue(':1',inspireid) #inspireid
        query.bindValue(':2',name) #name
        query.bindValue(':3',4) #collectiontype
        query.bindValue(':4',reference) #reference--> documentcitation id
        query.bindValue(':5',void_ide) #reference void
        query.bindValue(':6',fechainit) #beginlife
        query.bindValue(':7',None) #beginlife_void
        query.bindValue(':8',fechafin) #endlife
        query.bindValue(':9',endlife_void) #endlife_void
        
        if query.exec_()==0:
            self.Missatge(self.tr(u"Error al actualitzar la taula {}\n".format(tabla))+query.lastError().text())
            return
        else:
            self.Missatge(self.tr(u"Taula Geologiccolection actualitzada\n"),'Informacio') 
            self.dlg.CBgeocol.addItems([inspireid]) #actualizar el combobox de projectes
            self.dlg.CBgeocoldades.addItems([inspireid]) #actualizar el combobox de projectes (tab II)
            self.dlg.QLEprojectcodi.clear() #limpiar
            self.dlg.QLEprojectname.clear()
        

    def write_to_documentcitation(self):
        '''
        Docstring: funcion que lee los campos de la GUI de la documentacion y
        lo guarda en la tabla documentcitation
        '''
        # 5 campos a escribir (4 por GUI + ID)      
        tabla='documentcitation'
        
        db=self.conectardb     #create the connection and the Query        
        query = QSqlQuery(db)
        
        fecha=str(self.dlg.dateEdit.date().year())+'-'       
        fecha=fecha+str(self.dlg.dateEdit.date().month())+'-' 
        fecha=fecha+str(self.dlg.dateEdit.date().day())
        
        if (self.dlg.QLEname.text() or self.dlg.QLEshortname.text()) =='': 
            self.Missatge(self.tr(u"Els camps informe del projecte o codi estan buits"))
            return
        else:
            campos='name,shortname,date,link'
            query.prepare('INSERT INTO {} ({}) VALUES (:1,:2,:3,:4);'.format(tabla,campos)) 
            query.bindValue(':1',self.dlg.QLEname.text()) #doc name
            query.bindValue(':2',self.dlg.QLEshortname.text()) #doc short name
            query.bindValue(':3',fecha) # doc date
            query.bindValue(':4',str(self.dlg.QLElink.text())) # doc link
            if query.exec_()==0:
                self.Missatge(self.tr(u"Error al actualitzar la taula {}\n".format(tabla))+query.lastError().text())
            else:
                self.Missatge(self.tr(u"Documentacio carregada!\n"),'Informacio')
                self.dlg.CBshortnamedoccit.addItems([self.dlg.QLEshortname.text()]) #update combobox documentacio
                self.dlg.CBsprojdoccit.addItems([self.dlg.QLEshortname.text()]) #update combobox proyecte
                self.dlg.CBdoccitdades.addItems([self.dlg.QLEshortname.text()]) #update comobox doccittion tab II
                self.dlg.QLEname.clear()
                self.dlg.QLEshortname.clear()
                self.dlg.QLElink.clear()


# +++++++++++++++++++++++++++  TABLE II FUNCTIONS +++++++++++++++++++++++++++++++++
    def write_to_processat(self):
        '''
        Docstring: funcion que escribe a la tabla processes los datos almacenados en 
        la variable self.processat. Esta variable ha sido leida del archivo csv antes.
        No se mira que los datos sean correctos ni que esten o no repetidos
        Se escribe en la fila con la siguiente id (current id + 1)
        '''        
        #18 campos para escribir en la tabla processat
        # los datos del csv leido estan en la variable self.proocessat
        db = self.conectardb 
        query = QSqlQuery(db)
        
        tabla='processes'
        ide = self.obtain_max_id(query,tabla,'processesid') + 1
        dataprocessat=self.processat
        if dataprocessat==[]:
            self.Missatge(self.tr(u"No hi ha dades de processat a carregar"))
            return
        
        #change '' for None's
        for i in range(len(dataprocessat)):
            if dataprocessat[i][1]=='':
                dataprocessat[i][1]=None
        
        campos='inspireid,name,type,documentcitation,documentation_void,processparameter_name,processparameter_name_void'
        campos+=',processparameter_description,processparameter_description_void,responsibleparty,responsibleparty_void'
        campos+=',pixelarea,satellite,orbit,imagenum,firstimage,lastimage,date,incidenceangle'
        
        query.prepare('INSERT INTO {} ({}) VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14,:15,:16,:17,:18,:19);'.format(tabla,campos)) #no check nada
        query.bindValue(':1',ide) #inspire id
        query.bindValue(':2',dataprocessat[0][1]) #name
        query.bindValue(':3',dataprocessat[1][1]) #type 
        query.bindValue(':4',dataprocessat[2][1]) #dataprocessat[2][1]) #doccitation
        query.bindValue(':5',dataprocessat[3][1])   
        query.bindValue(':6',dataprocessat[4][1]) #processparam_name        
        query.bindValue(':7',dataprocessat[5][1])  
        query.bindValue(':8',dataprocessat[6][1]) #processparam_deescription
        query.bindValue(':9',dataprocessat[7][1])
        query.bindValue(':10',dataprocessat[8][1]) #responsible
        query.bindValue(':11',dataprocessat[9][1]) 
        query.bindValue(':12',dataprocessat[10][1]) #pixelarea
        query.bindValue(':13',dataprocessat[11][1]) #satellite   
        query.bindValue(':14',dataprocessat[12][1]) #orbit
        query.bindValue(':15',dataprocessat[13][1]) #imagenum
        query.bindValue(':16',dataprocessat[14][1]) #firstimage
        query.bindValue(':17',dataprocessat[15][1]) #lastimage
        query.bindValue(':18',dataprocessat[16][1]) #date
        query.bindValue(':19',dataprocessat[17][1]) #incident angle

        if query.exec_()==0:
             self.Missatge(self.tr(u"Error al actualitzar la taula processes\n")+query.lastError().text())
        else:
             self.Missatge(self.tr(u"Processat carregat\n"),'Informacio') 
             self.dlg.pathcsvprocessat.clear()
             self.dlg.CBprocessats.addItems([dataprocessat[0][1]])
        return 


    def carregar_dades(self):
        '''
        Docstring: funcion carga y escribe todos los datos en la base de datos. Rellena las tablas:
            geophobjectset, geophobject, spatialsamplingfeature, samplingfeature, samplingresult,
            observation y observation result.
            Loop sobre archivos en la carpeta y loop sobre filas en cada archivo
        ''' 
        self.Missatge(self.tr(u"Començant la carrega de dades\n"),'Informacio')
        
        db=self.conectardb     #create the connection and the Query        
        query = QSqlQuery(db)
        
        #obtain campaign id
        exist,idcampaign = self.isinbd(query,'campaign','name',self.dlg.CBcampdades.currentText(),
                                       'campaignid')
        if exist==0:
            self.Missatge(self.tr(u"Error al buscar el campaign ide"))
            return
            
        exist,idcitation = self.isinbd(query,'documentcitation','shortname', #obtain citation id
                                       self.dlg.CBdoccitdades.currentText(),'documentcitationid')
        if exist==0:
            self.Missatge(self.tr(u"Error al buscar el documentcitation ide"))
            return
            
        exist,idprocess = self.isinbd(query,'processes','name', #obtain processes id 
                                       self.dlg.CBprocessats.currentText(),'processesid')
        if exist==0:
            self.Missatge(self.tr(u"Error al buscar el processes ide"))
            return
            
        exist,idgeocol = self.isinbd(query,'geologiccollection','inspireid',#obtain geocol id
                                       self.dlg.CBgeocoldades.currentText(),'geologiccollectionid')
        if exist==0:
            self.Missatge(self.tr(u"Error al buscar el geologiccollection ide"))
            return    
        
        path_dir = self.dlg.lEloadpath.text() # folder path
        if path_dir=='':
            self.Missatge(self.tr(u'Tria una carpeta de dades!!')) 
            return
            
        files=os.listdir(str(path_dir))
        list_files=[] #list all the csv files
        for name in files:
            if name[-4:]=='.csv':
                list_files.append(name)
        if list_files==[]:
            self.Missatge(self.tr(u'No hi han arxius csv per carregar a aqueta carpeta:\n{} !!'.format(path_dir)))
            return  
            
        error=self.check_dependencias(query,list_files) #check file dependencies
        if error:
            return
        
        for num,files in enumerate(list_files): #read each csv file
        
            geometrygeoset,maxrows=self.prelectura(path_dir+'\\'+files)
            
            #write to geophobjectset
            error,idgeoset = self.write_to_geophobjectset(query,idcampaign,idcitation,idprocess,
                                                           idgeocol,geometrygeoset) 
            if error:
                self.Missatge(self.tr(u"Error al escriure a la taula geocollectionset"))
                return 
            
            #progress bar and missages
            self.dlg.progressBar.reset()
            self.dlg.progressBar.setMinimum(0)
            self.dlg.progressBar.setMaximum(maxrows)
            self.dlg.lEstatexport.clear()
            self.dlg.lEstatexport.setText('LLegint arxiu {}/{} : {}'.format(num+1,len(list_files),files))
            
            #open the file
            archivo=open(path_dir+'\\'+files,'r')
            reader=csv.reader(archivo,delimiter=';')
            init_dades=0 #index of the first column containing data
            dates=[];maxdates=[];header=[]
            name=files.split('_')[2]+'_'+files.split('_')[3] #name for table
            i=0 #first row

            for row in reader: #read each file line-by-line
                if i==0: #for the first row (the keys of the columns)
                    init_dades=row.index('EFF_AREA')+1
                    header.extend(row)
                    dates.extend(header[init_dades:])
                    maxdates.append(dates[0]);maxdates.append(dates[-1])
                    i=i+1
                    #do nothing
                else: #read not the first row--> register in the data base
                
                    UTMXY=row[1:3] #UTM_x and UTM_y
                    height=row[3] #height column
                    params=row[5:8] # v, v_std, coher
                    data=row[init_dades:] #all the "real" data
        
                    error,idgeoobj=self.write_to_geophobject(query,UTMXY,idgeocol,height)
                    if error:
                        return
                    error,idspsamp=self.write_to_spatialsampling(query,idgeoobj,idgeoset)
                    if error:
                        return
                    error,idsamp=self.write_to_samplingfeature(query,idspsamp,maxdates)
                    if error:
                        return
                    error=self.write_to_samplingresult(query,name,idsamp,params)
                    if error:
                        return
                    for j in range(len(dates)):
                        error,idobser = self.write_to_observation(query,idsamp,dates[j])
                        if error:
                            return
                        error=self.write_to_obserresult(query,idobser,name,data[j])        
                        if error:
                            return

                    i=i+1 #update row index
                self.dlg.progressBar.setValue(i) #update status bar
            archivo.close() #end row loop, close file
        self.Missatge(self.tr(u'Carrega de dades finalitzada'),'Informacio')


    def prelectura(self,archivo):

        archivo=open(archivo,'r')
        reader=csv.reader(archivo,delimiter=';')
        i=0 #first row
        UTMX=[];UTMY=[]
        for row in reader:
            if i>0:
                UTMX.append(int(float(row[1])))
                UTMY.append(int(float(row[2])))
            i=i+1

        max_xind=UTMX.index(max(UTMX))
        max_yind=UTMY.index(max(UTMY))
        min_xind=UTMX.index(min(UTMX))
        min_yind=UTMY.index(min(UTMY))
        maxrow=i
        #U4---U3
        #U1---U2
        
        U1=[UTMX[min_xind],UTMY[min_yind]] #los puntos de la geometria
        U2=[UTMX[max_xind],UTMY[min_yind]]
        U3=[UTMX[max_xind],UTMY[max_yind]]
        U4=[UTMX[min_xind],UTMY[max_yind]]
        del UTMY,UTMX
        archivo.close()
        geometry=[U1,U2,U3,U4]        
        
        return geometry,maxrow


    def write_to_geophobjectset(self,query,idcampaign,idcitation,idprocess,
                                                           idgeocol,geometrygeoset):
        '''
        Docstring: funcion que escribe en la tabla geophobjectset
        input: ides[idcampaign,idgeocollection,idcitation,idprocesses]
                geometria del poligono que envuelve los puntos (un cuadrado)
        '''
        tabla='geophobjectset'
        ide=self.obtain_max_id(query,tabla,'geophobjectsetid')+1
        
        #distribution void solo si no existe distribution (metadatos)
        if self.dlg.lEdistrinfo.text()=='': 
            distribuinfo=None
            void=self.dlg.CBdistnfo_void.currentText() #get from the  distribution combobox void text
            if void=='':
                self.Missatge(self.tr(u"El camp informe metadades esta buit. Indica el perque"))
                return True
            exist,distribuinfo_void = self.isinbd(query,'cl_voidtypevalue','voidtypevalue',void,'voidtypevalueid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el void ide"))
                return True
        else:
            distribuinfo=self.dlg.lEdistrinfo.text()
            distribuinfo_void=None
            
        #largework void solo si no existe largework (codigo ICGC)
        if self.dlg.lEgeosetlargework.text() =='': 
            largework_void=0
        else:
            largework_void=None
        
        U1=geometrygeoset[0][:];U2=geometrygeoset[1][:];U3=geometrygeoset[2][:]
        U4=geometrygeoset[3][:];U5=geometrygeoset[0][:]
        geometry='SRID=25831;POLYGON(({} {},{} {},{} {},{} {},{} {}))'.format(U1[0],U1[1],
                                                            U2[0],U2[1],U3[0],U3[1],U4[0],U4[1],U5[0],U5[1])
        
        campos='inspireid,distributioninfo,distributioninfo_void,largerwork,largerwork_void,projectedgeometry'
        campos+=',geologiccollection,campaign,citation,process'
        
        query.prepare('INSERT INTO {} ({}) VALUES (:1,:2,:3,:4,:5,ST_GeomFromEWKT(:6),:7,:8,:9,:10);'.format(tabla,campos))

        query.bindValue(':1',self.dlg.lEgeosetinspireid.text()) #inspireid
        query.bindValue(':2',distribuinfo) #distribuinfo
        query.bindValue(':3',distribuinfo_void) #distribuinfo_void
        query.bindValue(':4',self.dlg.lEgeosetlargework.text()) #largework
        query.bindValue(':5',largework_void) #largework void
        query.bindValue(':6',geometry) #geometry
        query.bindValue(':7',idgeocol) #geocollection id
        query.bindValue(':8',idcampaign) #campaign id
        query.bindValue(':9',idcitation) #citation id
        query.bindValue(':10',idprocess) #process id
        if query.exec_()==0:
            self.Missatge(self.tr(u"Error al actualitzar la taula {}\n".format(tabla))+query.lastError().text())
            error=True
        else:
            #self.Missatge(self.tr(u"Taula {} actualitzada\n".format(tabla))) 
            error=False
        return error,ide


    def write_to_obserresult(self,query,ideobser,name,data):
        '''
        Docstring: funcion que escribe a la tabla observation result el dato medido
        para una fecha determinada
        inputs: id observacion, el nombre de la medida, el valor de la medida
        '''
        error=False
        tabla='observationresult'
        campos='observation,name,value'
        query.prepare('INSERT INTO {} ({}) VALUES (:1,:2,:3);'.format(tabla,campos))

        query.bindValue(':1',ideobser) #id observation
        query.bindValue(':2',name) #name
        query.bindValue(':3',data) #value
        if query.exec_()==0:
            self.Missatge(self.tr(u"Error al actualitzar la taula {}\n".format(tabla))+query.lastError().text())
            error=True
            return error
        return error
        

    def write_to_observation(self,query,idesp,dates):
        '''
        Docstring: funcion que escribe en la tabla observation todas 
        las fechas de las observaciones
        inputs: id sampling feature, fecha de la observacion
        '''
        error=False
        tabla='observation'
        ide=ide=self.obtain_max_id(query,tabla,'observationid')+1
        data=dates[1:5]+'-'+dates[5:7]+'-'+dates[-2:]
        
        campos='phenomenontime,samplingfeature'
        query.prepare('INSERT INTO {} ({}) VALUES (:1,:2);'.format(tabla,campos))
        query.bindValue(':1',data) #phenomenontime
        query.bindValue(':2',idesp) #id samplingfeature
        if query.exec_()==0:
            self.Missatge(self.tr(u"Error al actualitzar la taula {}\n".format(tabla))+query.lastError().text())
            error=True
            return error,ide
        #self.Missatge(self.tr(u"Taula {} actualitzada\n".format(tabla)))
        return error,ide
     
     
    def write_to_samplingresult(self,query,name,idesp,datos):
        '''
        Docstring: funcion que escribe en la tabla samplingresutl los datos (vel, vel_std
        y coherencia). 3 datos para un mismo samplingfeatureregistro.
        inputs: info sobre la medida UD-LOS-EO-VERT...,id-sampling feature, 
        [vel, vel_st, coher]
        name: UD_ZONA
        '''        
        tabla='samplingresult'
        tipo=['_VEL','_V_STDEV','_COH']
        
        campos='samplingfeature,name,value'
        for i in range(3):
            query.prepare('INSERT INTO {} ({}) VALUES (:1,:2,:3);'.format(tabla,campos))
            query.bindValue(':1',idesp) #id sampling feature
            query.bindValue(':2',name+tipo[i]) #name
            query.bindValue(':3',datos[i]) #vel, vel_std o coher
            if query.exec_()==0:
                self.Missatge(self.tr(u"Error al actualitzar la taula {}\n".format(tabla))+query.lastError().text())
                error=True
                return error
                
        #self.Missatge(self.tr(u"Taula {} actualitzada\n".format(tabla))) 
        error=False
        return error
        
        
    def write_to_samplingfeature(self,query,idespsamp,dates):
        '''
        Docstring: funcion que escribe en la tabla samplingfeature
        inputs: la id de spatialsampling y la 1 y ultima fecha de los datos
        '''
        tabla = 'samplingfeature'
        ide=self.obtain_max_id(query,tabla,'samplingfeatureid')+1
        begindate=dates[0][1:5]+'-'+dates[0][5:7]+'-'+dates[0][-2:]
        enddate=dates[1][1:5]+'-'+dates[1][5:7]+'-'+dates[1][-2:]
     
        campos='spatialsamplingfeature,validtime_begin,validtime_end'
        query.prepare('INSERT INTO {} ({}) VALUES (:1,:2,:3);'.format(tabla,campos))
        query.bindValue(':1',idespsamp) #id spatialsamplingfeature
        query.bindValue(':2',begindate) # begin date
        query.bindValue(':3',enddate) # end date
        if query.exec_()==0:
            self.Missatge(self.tr(u"Error al actualitzar la taula {}\n".format(tabla))+query.lastError().text())
            error=True
        else:
            #self.Missatge(self.tr(u"Taula {} actualitzada\n".format(tabla))) 
            error=False
        return error,ide         
          
     
    def write_to_spatialsampling(self,query,idego,idegs):
        '''
        Docstring: funcion que escribe en la tabla spatialsampling
        inputs: las id's de geoobject y geoobjectset
        '''
        tabla = 'spatialsamplingfeature'
        ide=self.obtain_max_id(query,tabla,'spatialsamplingid')+1
     
        campos='geophobject,geophobjectset'
        query.prepare('INSERT INTO {} ({}) VALUES (:1,:2);'.format(tabla,campos))
        query.bindValue(':1',idego) #id geophobject
        query.bindValue(':2',idegs) #id geophobjectset
        if query.exec_()==0:
            self.Missatge(self.tr(u"Error al actualitzar la taula {}\n".format(tabla))+query.lastError().text())
            error=True
        else:
            #self.Missatge(self.tr(u"Taula {} actualitzada\n".format(tabla))) 
            error=False
        return error,ide


    def write_to_geophobject(self,query,UTMXY,idegeocol,z):
        '''
        Docstring: funcion que escribe en la tabla geophobject.
        input datos: [UTM_x, UTM_y], idgeocol, height
        '''
        tabla = 'geophobject'         
        ide=self.obtain_max_id(query,tabla,'geophobjectid')+1
                
        inspireid='es.icgc.ge.psi_{}_{}'.format(int(float(UTMXY[0])),int(float(UTMXY[1])))
        geometry='POINT({} {})'.format(UTMXY[0],UTMXY[1])
        height=z
        
        campos='inspireid,geologiccollection,projectedgeometry,height'
        query.prepare('INSERT INTO {} ({}) VALUES (:1,:2,ST_GeomFromText(:3,:4),:5);'.format(tabla,campos))
        query.bindValue(':1',inspireid) #inspireid
        query.bindValue(':2',idegeocol) # geologiccollection
        query.bindValue(':3',geometry) # geometry
        query.bindValue(':4',25831) #srid
        query.bindValue(':5',height) # height       
        if query.exec_()==0:
            self.Missatge(self.tr(u"Error al actualitzar la taula {}\n".format(tabla))+query.lastError().text())
            error=True
        else:
            #self.Missatge(self.tr(u"Taula {} actualitzada\n".format(tabla))) 
            error=False
        return error,ide

        
    def check_dependencias(self,query,list_files):
        '''
        Docstring: funcion que mira las dependencias al cargar los archivos de la carpet
                    Mirar dependencias implica que si cargas un tipo LOS, todos los que se derivan de esta medida
                    se han de borrar. Si la observacion ya esta, se borrara y se sustituye por la nueva del archivo.
        '''
        
        #obtener la id de la campaña donde queremos subir los datos
        exist,idcampaign = self.isinbd(query,'campaign','name',self.dlg.CBcampdades.currentText(),
                                       'campaignid')
        if exist==0:
            self.Missatge(self.tr(u"Error al buscar el campaign ide"))
            return
        
        #obtener todos los id-geophobjectset asociados a la campaña
        if query.exec_('SELECT public.geophobjectset.geophobjectsetid FROM public.geophobjectset'
        +' JOIN public.campaign ON public.geophobjectset.campaign=public.campaign.campaignid'
        +' WHERE public.campaign.campaignid={};'.format(idcampaign))==0:
            self.Missatge(self.tr(u"Error a la consulta de la campanya y geophobjectset\n")+query.lastError().text())
            return
        idgeopset=[]
        while query.next():
            idgeopset.append(query.value(0)) #todos los id-geophobjectset
        
        #obtener todos los tipos de medidas en la observation-result
        observaciones=[]
        for i in idgeopset:
            if query.exec_('SELECT DISTINCT ON (name) name FROM public.observationresult JOIN'
        +' public.observation ON public.observationresult.observation=public.observation.observationid'
        +' LEFT JOIN public.samplingfeature ON public.observation.samplingfeature=public.samplingfeature.samplingfeatureid'
        +' LEFT JOIN public.spatialsamplingfeature ON public.samplingfeature.spatialsamplingfeature=public.spatialsamplingfeature.spatialsamplingid '
        +' LEFT JOIN public.geophobjectset ON public.spatialsamplingfeature.geophobjectset=public.geophobjectset.geophobjectsetid'
        +' WHERE public.geophobjectset.geophobjectsetid={};'.format(i))==0:
                self.Missatge(self.tr(u"Error al consultar observation des de geophobjectset\n")+query.lastError().text())
                return
            while query.next():
                observaciones.append(query.value(0))
        
        todeleteobs=[]
        for archivo in list_files:
            if archivo.find('LOS')>=0:
                #es tipo LOS
                mapcoord=archivo.split('_')[3] #mapa de la observacion
                #borrar todos las observaciones con estas cordenadas
                for obs in observaciones:
                    if (obs.find(mapcoord)>=0) and (obs not in todeleteobs):
                        todeleteobs.append(str(obs))
            else:
                #no es tipo LOS
                medida=archivo.split('_')[2]+'_'+archivo.split('_')[3] 
                #borar la observacion si ya existe en la campaña
                for obs in observaciones:
                    if (obs.find(medida)>=0) and (obs not in todeleteobs):
                        todeleteobs.append(obs)
        
        error=False        
        if todeleteobs!=[]: #existen cosas a borrar
            m = QMessageBox()
            m.setIcon(QMessageBox.Warning)
            m.setWindowTitle('Confirmar')
            m.setText('Alguns arxius a carregar ja estan en la base de dades. \n'
            +'Avans de carregar s\'esborraran aquestes entrades a la base de dades.\n'
            +'{}\n'.format(todeleteobs)
            +'Estas segur?')
            m.setStandardButtons(QMessageBox.Ok);
            m.addButton(QMessageBox.Cancel);
            m.setButtonText(QMessageBox.Ok,"Aceptar")
            m.setButtonText(QMessageBox.Cancel,"Cancelar")
            
            if m.exec_()==  QMessageBox.Ok:
                for nombre in todeleteobs:
                    idgeoset=self.obtain_geosetid(query,nombre)
                    self.delete_observation(query,idgeoset)
                self.Missatge(self.tr(u'Entrades existents en la base de dades borrades'),'Informacio')
                error=False
            else:
                self.Missatge(self.tr(u'Cancelada la carrega de dades'),'Informacio')
                error=True
        return error

# ----------------------------------------------------------------------------------

#++++++++++++++++++++ TABLE III FUNCTIONS +++++++++++++++++++++++++++++++++++++

    def show_campaign_info(self):
        '''
        Docstring: funcion que crea un mensaje donde muestra toda la info de la
        campaña seleccionada en el combobox
        '''
        db=self.conectardb
        query = QSqlQuery(db)
        registro=self.dlg.campainglist.currentText()
        campos='client,contractor'
        datos={}
        if query.exec_('SELECT ({0}) FROM campaign WHERE campaign.name=\'{1}\';'.format(campos,registro))==0:
            self.Missatge(self.tr(u"Error al buscar informacio de la campanya\n")+query.lastError().text())
            return
        while query.next():
            datos=query.value(0)
        
        datos=datos.replace('(','')
        datos=datos.replace(')','')
        datos=datos.split(',')
        
        campos=campos.split(',')
        mensaje=''
        for i in range(len(campos)):
            mensaje=mensaje + str(campos[i])+': ' + str(datos[i]) + ' \n'
        
        mensaje='Nom de la campanya: ' + self.dlg.campainglist.currentText() +'\n'+mensaje
        mensaje='Dades de la campanya \n' + mensaje
        self.Missatge(self.tr(mensaje),'Informacio')
        
        #populate the list widget
        #ask the bd for the geophonjectsetids associated to this campaign
        #obtain campaign id
        exist,idcampaign = self.isinbd(query,'campaign','name',self.dlg.campainglist.currentText(),
                                       'campaignid')
        if exist==0:
            self.Missatge(self.tr(u"Error al buscar el campaign ide"))
            return
        
        if query.exec_('SELECT public.geophobjectset.geophobjectsetid FROM public.geophobjectset'
        +' JOIN public.campaign ON public.geophobjectset.campaign=public.campaign.campaignid'
        +' WHERE public.campaign.campaignid={};'.format(idcampaign))==0:
            self.Missatge(self.tr(u"Error a la consulta de la campanya y geophobjectset\n")+query.lastError().text())
            return
        idgeopset=[]
        while query.next():
            idgeopset.append(query.value(0))

        #from the idgeophobjectset (one per file) is posible to obtain the measure type
        self.dlg.listWidget.clear()
        self.show_observationname(query,idgeopset)


    def show_observationname(self,query,ide):
        '''
        Docstring: llena el list widget con los diferentes tipos de observacion que hay en la tabla observationresult
        '''
        for i in ide:
            if query.exec_('SELECT DISTINCT ON (name) name FROM public.observationresult JOIN'
        +' public.observation ON public.observationresult.observation=public.observation.observationid'
        +' LEFT JOIN public.samplingfeature ON public.observation.samplingfeature=public.samplingfeature.samplingfeatureid'
        +' LEFT JOIN public.spatialsamplingfeature ON public.samplingfeature.spatialsamplingfeature=public.spatialsamplingfeature.spatialsamplingid '
        +' LEFT JOIN public.geophobjectset ON public.spatialsamplingfeature.geophobjectset=public.geophobjectset.geophobjectsetid'
        +' WHERE public.geophobjectset.geophobjectsetid={};'.format(i))==0:
                self.Missatge(self.tr(u"Error al consultar observation des de geophobjectset\n")+query.lastError().text())
                return
            while query.next():
                self.dlg.listWidget.addItems([query.value(0)])

  
    def delete_observationname(self):
        '''
        Docstring: funcion que borra las entradas en la tabla que hacen referencia a un tipo de observacion
        Buscamos la idegeophobjectset (unica para cada tipo de observacion) y borraremos en cascada
        '''
        db=self.conectardb
        query = QSqlQuery(db)
        if 'LOS' in self.dlg.listWidget.currentItem().text():
            #buscar las medidas relacionadas a este LOS
            nombre=self.dlg.listWidget.currentItem().text().split('_')
            coordenada=nombre[1]
            datosaborrar=[]
            for i in range(self.dlg.listWidget.count()):
                textitem=self.dlg.listWidget.item(i).text()
                if coordenada in textitem:
                    datosaborrar.append(textitem) #todas las medidas derivadas del LOS con las coordenadas adecuadas
            m = QMessageBox()
            m.setIcon(QMessageBox.Warning)
            m.setWindowTitle('Confirmar')
            m.setText('Confirmacio per esborrar l\'observacio: {}. Es una observacio tipus LOS.\n'.format(self.dlg.listWidget.currentItem().text())
            +'S\'esborraran totes les observacions derivades d\'aquest LOS. En total: {}.\n'.format(len(datosaborrar))
            +'Estas segur?')
            m.setStandardButtons(QMessageBox.Ok);
            m.addButton(QMessageBox.Cancel);
            m.setButtonText(QMessageBox.Ok,"Aceptar")
            m.setButtonText(QMessageBox.Cancel,"Cancelar")
            
            if m.exec_()==  QMessageBox.Ok:
                for nombre in datosaborrar:
                    #borrar el listwidget
                    item=self.dlg.listWidget.findItems(nombre,Qt.MatchRegExp)
                    self.dlg.listWidget.takeItem(self.dlg.listWidget.row(item[0]))
                    #borrar en la base de datos
                    idgeoset=self.obtain_geosetid(query,nombre)
                    self.delete_observation(query,idgeoset)

                self.Missatge(self.tr(u"Entrada esborrada\n"),'Informacio')
            return 
                
        else:
            
            m = QMessageBox()
            m.setIcon(QMessageBox.Warning)
            m.setWindowTitle('Confirmar')
            m.setText('Confirmacio per esborrar l\'observacio: {}. Estas segur?'.format(self.dlg.listWidget.currentItem().text()))
            m.setStandardButtons(QMessageBox.Ok);
            m.addButton(QMessageBox.Cancel);
            m.setButtonText(QMessageBox.Ok,"Aceptar")
            m.setButtonText(QMessageBox.Cancel,"Cancelar")
            if m.exec_()==  QMessageBox.Ok:
                idgeoset=self.obtain_geosetid(query,self.dlg.listWidget.currentItem().text())
                self.delete_observation(query,idgeoset)
                self.Missatge(self.tr(u"Entrada esborrada\n"),'Informacio')
                self.dlg.listWidget.takeItem(self.dlg.listWidget.currentRow())
            return
        

    def delete_observation(self,query,idegeoset):
        '''
        Docstring: funcion que borra las entradas en la tabla que hacen referencia a un tipo de observacion
        Buscamos la idegeophobjectset (unica para cada tipo de observacion) y borraremos en cascada. ESTE ES EL 
        NUCLEO DE LA FUNCION delete_observationname
        '''    
        #para poder limpiar la tabla geophobject nos hemos de quedar con el rango de id's que comprenden el archivo que queremos borrar
        if query.exec_('SELECT geophobject FROM spatialsamplingfeature WHERE'
        + ' public.spatialsamplingfeature.geophobjectset={} ORDER BY geophobject DESC limit 1;'.format(idegeoset))==0:        
            self.Missatge(self.tr(u"Error al buscar max(id) geophobject a spatialsamplingfeature\n")+query.lastError().text())
            return 
        else:
            while query.next():
                maxid=query.value(0)
        if query.exec_('SELECT geophobject FROM spatialsamplingfeature WHERE'
        + ' public.spatialsamplingfeature.geophobjectset={} ORDER BY geophobject ASC limit 1;'.format(idegeoset))==0:        
            self.Missatge(self.tr(u"Error al buscar min(id) geophobject a spatialsamplingfeature\n")+query.lastError().text())
            return 
        else:
            while query.next():
                minid=query.value(0)
        
        #esta orden limpia las tablas observation/result, samplingresult, samplingfeature y spatialsamplingfeature        
        if query.exec_('DELETE FROM public.geophobjectset WHERE geophobjectsetid={};'.format(idegeoset))==0:
            self.Missatge(self.tr(u"Error al borrar l\'entrada a la taula geophobjectset\n")+query.lastError().text())
            return 
        
        #falta borrar la tabla geophobject
        if query.exec_('DELETE FROM public.geophobject WHERE geophobjectid>={0} and  geophobjectid<={1}'.format(minid,maxid))==0:
            self.Missatge(self.tr(u"Error al borrar la taula geophobject\n")+query.lastError().text())
            return 
        return
        
    
    def obtain_geosetid(self,query,observacion):
        '''
        Docstring: devuelve el ide de la tabla geophobjectset que corresponde al
        nombre de la observacion en la observationresult
        '''   
        
        if query.exec_('SELECT DISTINCT ON (geophobjectsetid) geophobjectsetid FROM geophobjectset JOIN' 
        + ' public.spatialsamplingfeature ON public.geophobjectset.geophobjectsetid=public.spatialsamplingfeature.geophobjectset' 
        + ' JOIN public.samplingfeature ON public.spatialsamplingfeature.spatialsamplingid=public.samplingfeature.spatialsamplingfeature'
        + ' JOIN public.observation ON public.samplingfeature.samplingfeatureid=public.observation.samplingfeature'
        + ' JOIN public.observationresult ON public.observation.observationid=public.observationresult.observation'
        + ' WHERE public.observationresult.name =\'{}\';'.format(observacion))==0:
            self.Missatge(self.tr(u"Error al consultar geophobjectset des de observationresult name\n")+query.lastError().text())
            return
        while query.next():
            return query.value(0)


    def show_obsinfo(self):
        '''
        Docstring: funcion asociada al boton de info de la observacion, devuelve mensaje con algunos campos interesantes
        '''
        if self.dlg.listWidget.currentItem()==None:
             self.Missatge(self.tr(u"No hi ha cap observacio seleccionada"),'Informacio')
             return
        else:
            db=self.conectardb
            query = QSqlQuery(db)
            idgeoset=self.obtain_geosetid(query,self.dlg.listWidget.currentItem().text())
            campos=['inspireid','largerwork','geologiccollection','citation','process']
            datos=[]
            for consulta in campos:
                if query.exec_('SELECT public.geophobjectset.{} FROM public.geophobjectset WHERE public.geophobjectset.geophobjectsetid={};'.format(consulta,idgeoset))==0:
                    self.Missatge(self.tr(u"Error al buscar informacio de l\'observacion\n")+query.lastError().text())
                    return 
                while query.next():
                    datos.append(query.value(0))
            mensaje='Identificador: '+datos[0]+'\n'
            mensaje=mensaje + 'Codi projecte ICGC: ' + datos[1]+'\n'
            
            if query.exec_('SELECT public.geologiccollection.inspireid FROM public.geologiccollection WHERE public.geologiccollection.geologiccollectionid={};'.format(datos[2]))==0:
                self.Missatge(self.tr(u"Error al buscar informacio de l\'observacion\n")+query.lastError().text())
                return 
            while query.next():
                mensaje=mensaje + 'Codi projecte: ' + str(query.value(0)) + '\n'
                    
            if query.exec_('SELECT public.documentcitation.name FROM public.documentcitation WHERE public.documentcitation.documentcitationid={};'.format(datos[3]))==0:
                    self.Missatge(self.tr(u"Error al buscar informacio de l\'observacion\n")+query.lastError().text())
                    return 
            while query.next():
                mensaje=mensaje + 'Informe del projecte:  ' + str(query.value(0)) + '\n'
            
            if query.exec_('SELECT public.processes.name FROM public.processes WHERE public.processes.processesid={};'.format(datos[4]))==0:
                self.Missatge(self.tr(u"Error al buscar informacio de l\'observacion\n")+query.lastError().text())
                return 
            while query.next():
                mensaje=mensaje + 'Nom del processat:  ' + str(query.value(0)) + '\n'
            
            mensaje='Informacio sobre l\'observacio: {}\n'.format(self.dlg.listWidget.currentItem().text())+mensaje
            self.Missatge(self.tr(mensaje),'Informacio')
            
            
    def delete_campaign(self):
        db=self.conectardb
        query = QSqlQuery(db)
        registro=self.dlg.campainglist.currentText()
        m = QMessageBox()
        m.setIcon(QMessageBox.Warning)
        m.setWindowTitle('Confirmar')
        m.setText('Confirmacio per esborrar la campanya: {}. Estas segur?'.format(registro))
        m.setStandardButtons(QMessageBox.Ok);
        m.addButton(QMessageBox.Cancel);
        m.setButtonText(QMessageBox.Ok,"Aceptar")
        m.setButtonText(QMessageBox.Cancel,"Cancelar")
        if m.exec_()==  QMessageBox.Ok:
            #obtener todos los geophobjectset correspondientes a esta campaña
            #y borrarlos uno a uno (para poder limpiar la tabla geophobject)
            if query.exec_('SELECT campaignid FROM public.campaign WHERE public.campaign.name=\'{}\';'.format(registro))==0:
                self.Missatge(self.tr(u"Error al buscar el nom de la campanya per esborrarlan")+query.lastError().text())
                return
            while query.next():
                idcamp=query.value(0)
                
            idgeosetincamp=[] #lista de idgeoset que pertenecen a la campaña
            if query.exec_('SELECT geophobjectsetid FROM public.geophobjectset WHERE public.geophobjectset.campaign={};'.format(idcamp))==0:
                self.Missatge(self.tr(u"Error al buscar el nom de la campanya per esborrarla")+query.lastError().text())
                return
            while query.next():
                idgeosetincamp.append(query.value(0))
                
            for idegeoset in idgeosetincamp:
                self.delete_observation(query,idegeoset) #borrado todas las tablas por debajo de la campaign

            #limpiar la tabla campaña
            if query.exec_('DELETE FROM campaign WHERE name=\'{}\''.format(registro)) ==0:
                self.Missatge(self.tr(u"Error al borrar la taula campanya")+query.lastError().text())
            else:
                self.Missatge(self.tr('Campanya: {} borrada'.format(registro)),'Informacio')
                self.dlg.campainglist.removeItem(self.dlg.campainglist.findText(registro))
                self.dlg.CBcamp.removeItem(self.dlg.CBcamp.findText(registro))
                self.dlg.CBcampdades.removeItem(self.dlg.CBcampdades.findText(registro))
                self.dlg.listWidget.clear()
        else:
            pass #cancel option, do nothing
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


#++++++++++++++++++++++++++++++++++ TABLE IV FUNCTIONS ++++++++++++++++++++++++
    
    def cargar_csv(self):
        #choose directory path
        self.dlg.lEshppath.setText('')
        name=QFileDialog().getOpenFileName(
            self.dlg, self.tr(u'Selecció arxiu .csv'),'C:\Users')
        if name[-4:]!='.csv':
            self.Missatge(self.tr(u"Arxiu no es .csv!\n"))
            return
        else:
            self.dlg.lEshppath.setText(name)
            uri=name+'?delimiter=;&yField=UTM_y&xField=UTM_x'
            layer = QgsVectorLayer(uri,'1.40', 'delimitedtext')
            if not layer:
                self.Missatge(self.tr(u"Error al carregar les dades\n"))
                return
                
                
    def carregarpunts(self):
        self.dlg.lEnselected.clear()
        layer=self.iface.activeLayer()
        if layer ==None: #no capa activa
             self.Missatge(self.tr('No hi ha una capa activa!'))
             return
        self.dlg.lEnselected.setText(str(layer.selectedFeatureCount()))
        if layer.selectedFeatureCount()==0 or layer.selectedFeatureCount()>4:
            self.Missatge(self.tr('Massa punts seleccionats!'))
            return 
            
        points=layer.selectedFeatures()
        #date keys
        keys=[]
        for field in layer.pendingFields():
            keys.append(field.name())
        
        indexdata=keys.index('EFF_AREA')+1
        dates=keys[indexdata:]
        x = [dt.datetime.strptime(d.replace('D',''),'%Y%m%d').date() for d in dates]
        
        #obtain data
        datos=[]
        nombre=[]
        vx=[];vcoehr=[];
        for feat in points:
            elemento=[]
            nombre.append(feat[0])
            vx.append(feat[5])
            vcoehr.append(feat[6])
            for fecha in dates:
                elemento.append(feat[fecha])
            datos.append(elemento)
        
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator())
        
        col=['coral','blue','red','green']        
        
        for i in range(len(datos)):
            plt.scatter(x,datos[i],marker='s',color=col[i],label=nombre[i]+' vel:%.4f vel_stdv:%.4f' %(vx[i],vcoehr[i]) )
            if self.dlg.cbline.isChecked():
                z=np.polyfit(mdates.date2num(x),datos[i],1)
                line=np.poly1d(z)
                xx=np.linspace(mdates.date2num(x).min(),mdates.date2num(x).max(),100)
                dd=mdates.num2date(xx)
                plt.plot(dd,line(xx),color=col[i])
            if self.dlg.cbpol.isChecked():   
                z=np.polyfit(mdates.date2num(x),datos[i],6)
                spline=np.poly1d(z)
                xx=np.linspace(mdates.date2num(x).min(),mdates.date2num(x).max(),100)
                dd=mdates.num2date(xx)
                plt.plot(dd,spline(xx),color=col[i])
            
            
            
        dates=['201601','201602','201604','201606','201608','201610','201612']
        xlab = [dt.datetime.strptime(d,'%Y%m').date() for d in dates]
        
        xlim=[dt.datetime.strptime(dates[0]+'01','%Y%m%d').date(),dt.datetime.strptime(dates[-1]+'31','%Y%m%d').date()]
        
        plt.gcf().autofmt_xdate()
        plt.xticks(xlab,rotation=45)
        plt.xlabel('Date',FontSize=16)
        plt.ylabel('mm', Fontsize=16)
        plt.xlim(xlim)
        plt.legend()
        plt.grid()
        plt.show()
        
        