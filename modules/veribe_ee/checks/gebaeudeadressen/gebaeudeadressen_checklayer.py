 # -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

import sys
import traceback


try:
    _encoding = QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)

from veriso.modules.complexcheck_base import ComplexCheckBase


class ComplexCheck(ComplexCheckBase):

    def __init__(self, iface):
        super(ComplexCheck, self).__init__(iface)
        self.iface = iface
        
        self.root = QgsProject.instance().layerTreeRoot()        
        self.layerLoader = LoadLayer(self.iface)

    def run(self):        
        self.settings = QSettings("CatAIS","VeriSO")
        project_id = self.settings.value("project/id")
        epsg = self.settings.value("project/epsg")
        
        locale = QSettings().value('locale/userLocale')[0:2] 

        if not project_id:
            self.iface.messageBar().pushMessage("Error",  _translate("VeriSO_EE_Geb_Check", "project_id not set", None), level=QgsMessageBar.CRITICAL, duration=5)                                
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            group = _translate("VeriSO_EE_Geb_Check", "Gebaeudeadressen - Checklayer", None)
            group += " (" + str(project_id) + ")"
    
            layer = {}
            layer["type"] = "postgres"
            layer["title"] =  _translate("VeriSO_EE_Geb_Check", "Spinnennetz", None)
            layer["featuretype"] = "t_gebaeudeadressen_spinnennetz"
            layer["geom"] = "line"
            layer["key"] = "ogc_fid"            
            layer["sql"] = ""
            layer["readonly"] = True
            layer["group"] = group
            layer["style"] = "gebaeudeadressen/spinnennetz_blau.qml"
            
            vlayer = self.layerLoader.load(layer, False)
                
            layer = {}
            layer["type"] = "postgres"
            layer["title"] =  _translate("VeriSO_EE_Geb_Check", u"Kürzeste Linie", None)
            layer["featuretype"] = "t_shortestline_hausnummerpos"
            layer["geom"] = "the_geom"
            layer["key"] = "ogc_fid"            
            layer["sql"] = ""
            layer["readonly"] = True
            layer["group"] = group
            layer["style"] = "gebaeudeadressen/shortestline_linie.qml"
            
            vlayer = self.layerLoader.load(layer)
            
            layer = {}
            layer["type"] = "postgres"
            layer["title"] = _translate("VeriSO_EE_Geb_Check", "HausnummerPos", None)
            layer["featuretype"] = "v_gebaeudeadressen_hausnummerpos"
            layer["geom"] = "pos"
            layer["key"] = "ogc_fid"            
            layer["sql"] = ""
            layer["group"] = group
            layer["style"] = "gebaeudeadressen/shortestline_hausnummerpos.qml"
 
            vlayer = self.layerLoader.load(layer)
            
            layer = {}
            layer["type"] = "postgres"
            layer["title"] = _translate("VeriSO_EE_Geb_Check", u"Gebäude > 12m2 ohne Eingang", None)
            layer["featuretype"] = "t_gebaeude_groesser_12m2_ohne_eingang"
            layer["geom"] = "geometrie"
            layer["key"] = "ogc_fid"            
            layer["sql"] = ""
            layer["group"] = group
            layer["style"] = "gebaeudeadressen/gebaeude_12m2_ohne_eingang.qml"
            
            vlayer = self.layerLoader.load(layer)

            layer = {}
            layer["type"] = "postgres"
#            layer["title"] =  _translate("VeriSO_EE_Geb_Basis", "LokalisationsName", None)
            layer["title"] = "LokalisationsName"

            layer["featuretype"] = "gebaeudeadressen_lokalisationsname"
            layer["key"] = "ogc_fid"            
            layer["sql"] = ""
            layer["group"] = group
            
            vlayer = self.layerLoader.load(layer)
            
        except Exception, e:
            QApplication.restoreOverrideCursor()            
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.iface.messageBar().pushMessage("Error", str(traceback.format_exc(exc_traceback)), level=QgsMessageBar.CRITICAL, duration=5)                    
        QApplication.restoreOverrideCursor()      
