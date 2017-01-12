 # -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import *
from qgis.core import *
from qgis.gui import *

import sys
import traceback

from veriso.base.utils.doLoadLayer import LoadLayer

try:
    _encoding = QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)

class ComplexCheck(QObject):

    def __init__(self, iface):
        self.iface = iface
        
        self.root = QgsProject.instance().layerTreeRoot()        
        self.layerLoader = LoadLayer(self.iface)

    def run(self):        
        self.settings = QSettings("CatAIS","VeriSO")
        project_id = self.settings.value("project/id")
        epsg = self.settings.value("project/epsg")
        
        locale = QSettings().value('locale/userLocale')[0:2] # Für Multilingual-Legenden.

        if not project_id:
            self.iface.messageBar().pushMessage("Error",  _translate("VeriSO_EE_FP3_pro_TS", "project_id not set", None), level=QgsMessageBar.CRITICAL, duration=5)                                
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            group = _translate("VeriSO_EE_FP3", "FixpunkteKategorie3_pro_TS", None)
            group += " (" + str(project_id) + ")"


            layer = {}
            layer["type"] = "postgres"
            layer["title"] = "LFP3"
            layer["featuretype"] = "fixpunktekategorie3_lfp3"
            layer["geom"] = "geometrie"
            layer["key"] = "ogc_fid"            
            layer["sql"] = ""
            layer["readonly"] = True            
            layer["group"] = group
            layer["style"] = "fixpunkte/lfp3.qml"

            vlayer = self.layerLoader.load(layer)

            layer = {}
            layer["type"] = "postgres"
            layer["title"] = "Toleranzstufen"
            layer["featuretype"] = "tseinteilung_toleranzstufe"
            layer["geom"] = "geometrie"
            layer["key"] = "ogc_fid"            
            layer["sql"] = ""
            layer["readonly"] = True
            layer["group"] = group    
            layer["style"] = "liegenschaften/TS.qml"
            vlayer = self.layerLoader.load(layer, False, True)

            layer = {}
            layer["type"] = "postgres"
            layer["title"] = "LFP3 ausserhalb Perimeter"
            layer["featuretype"] = "fixpunktekategorie3_lfp3_ausserhalb_perimeter_v"
            layer["geom"] = "geometrie"
            layer["key"] = "ogc_fid"            
            layer["sql"] = ""
            layer["readonly"] = True
            layer["group"] = group    
            layer["style"] = "fixpunkte/lfp3_aussen.qml"
            vlayerOutsidePerimeter = self.layerLoader.load(layer, True, True)
      
            layer = {}
            layer["type"] = "postgres"
            layer["title"] = "LFP3 pro Toleranzstufe"
            layer["featuretype"] = "fixpunktekategorie3_lfp3_pro_toleranzstufe_v"
            #layer["geom"] = ""
            layer["key"] = "ogc_fid"            
            layer["sql"] = ""
            layer["readonly"] = True
            layer["group"] = group    
            vlayer = self.layerLoader.load(layer)
      

           # Bitmap erzeugen.
            QgsMessageLog.logMessage("0", "VeriSO", QgsMessageLog.CRITICAL)         

        # Statistik aus Datenbank lesen.
        
            settings = QSettings("CatAIS","VeriSO")
            module_name = settings.value("project/appmodule")
            provider = settings.value("project/provider")
            db_host = settings.value("project/dbhost")
            db_port = settings.value("project/dbport")
            db_name = settings.value("project/dbname")
            db_schema = settings.value("project/dbschema")
            db_user = settings.value("project/dbuser")
            db_pwd = settings.value("project/dbpwd")


            db = QSqlDatabase.addDatabase("QPSQL", "db")
            db.setHostName(db_host)
            db.setPort(int(db_port))
            db.setDatabaseName(db_name)
            db.setUserName(db_user)
            db.setPassword(db_pwd)

            
    

            if db.open():
                message = "Could open database: "
                QgsMessageLog.logMessage(self.tr(message) + db.lastError().driverText(), "VeriSO", QgsMessageLog.CRITICAL)                                
                return -1
                
            abfrage = """SELECT a.art+1 as toleranzstufe, count(b.tid) as ist, 
CASE 
 WHEN a.art=0 THEN (round(150*c.ts_flaeche/1000000)) 
 WHEN a.art=1 THEN (round(70*c.ts_flaeche/1000000)) 
 WHEN a.art=2 THEN (round(20*c.ts_flaeche/1000000)) 
 WHEN a.art=3 THEN (round(10*c.ts_flaeche/1000000)) 
 WHEN a.art=4 THEN (round(2*c.ts_flaeche/1000000)) 
END as soll, 
CASE 
 WHEN a.art=0 THEN (count(b.tid)-round(150*c.ts_flaeche/1000000)) 
 WHEN a.art=1 THEN (count(b.tid)-round(70*c.ts_flaeche/1000000)) 
 WHEN a.art=2 THEN (count(b.tid)-round(20*c.ts_flaeche/1000000)) 
 WHEN a.art=3 THEN (count(b.tid)-round(10*c.ts_flaeche/1000000)) 
 WHEN a.art=4 THEN (count(b.tid)-round(2*c.ts_flaeche/1000000)) 
END as diff, 
c.ts_flaeche, round((c.ts_flaeche/10000)::numeric, 2) as ts_hektare, c.ts_flaeche/1000000 as ts_km2
FROM """+db_schema+""".tseinteilung_toleranzstufe as a, """+db_schema+""".fixpunktekategorie3_lfp3 as b, 
 (SELECT art, sum(ST_Area(a.geometrie)) as ts_flaeche
 FROM """+db_schema+""".tseinteilung_toleranzstufe a
 GROUP BY art
 ORDER BY art) as c
WHERE 
a.art = c.art
AND ST_Distance(a.geometrie, b.geometrie) = 0
GROUP BY a.art, c.ts_flaeche
ORDER BY a.art"""


            QgsMessageLog.logMessage(str(abfrage), "VeriSO", QgsMessageLog.WARNING)      

            query = db.exec_(abfrage)
            
            if not query.isActive():
                message = "Error while reading from projects database."
                QgsMessageLog.logMessage(self.tr(message), "VeriSO", QgsMessageLog.CRITICAL)            
                QgsMessageLog.logMessage(str(QSqlQuery.lastError(query).text()), "VeriSO", QgsMessageLog.CRITICAL)      
                return -1

            QgsMessageLog.logMessage(str("hallo stefan"), "VeriSO", QgsMessageLog.WARNING)      
            
            record = query.record()
            while query.next():
                gaga = str(query.value(record.indexOf("toleranzstufe")))
                QgsMessageLog.logMessage(str(gaga), "VeriSO", QgsMessageLog.WARNING)      
            
            QgsMessageLog.logMessage(str("hallo stefan 222"), "VeriSO", QgsMessageLog.WARNING)      
#            self.dbobj = DbObj("default", "postgres",  host,  port,  database,  username,  password)
#            self.connected = self.dbobj.connect()
#
##
#            if self.connected == True:
#                statistik = self.dbobj.read( abfrage )  
#                QgsMessageLog.logMessage(str("hallo stefan oo"), "VeriSO", QgsMessageLog.WARNING)        
#                print statistik
 
            QgsMessageLog.logMessage(str("hallo stefan oo"), "VeriSO", QgsMessageLog.WARNING)        


            if self.connected == True:
               statistik = self.dbobj.read( abfrage )        
               print statistik

#                
            if len(statistik['TOLERANZSTUFE']) <> 0:
                    try:
                        # Die Excel-Datei anlegen und die Statistik hineinschreiben.
                        wb = pycel.Workbook(encoding='utf-8')
                        wb.country_code = 41

                        style1 = pycel.easyxf('font: bold on;');
                        style2 = pycel.easyxf('font: italic on;');
                        
                        ws = wb.add_sheet(u'LFP3-Statistik')
                        
                        # Operatsinfo in die Datei schreiben.
                        self.writeXLSTitle(ws,  fosnr,  lotnr,  date)
                                    
                        # Die Statistik hineinschreiben.
                        ws.write(4, 0, "Toleranzstufe", style2)
                        ws.write(4, 1, u'Fläche [ha]', style2)
                        ws.write(4, 2, "Ist-Anzahl (LFP3)", style2)
                        ws.write(4, 3, "Soll-Anzahl (LFP3)", style2)
                        ws.write(4, 4, "Ist-Soll (LFP3)", style2)    
                        
                        for i in range(len(statistik['TOLERANZSTUFE'])):
                            ws.write(5+i,  0,  str( statistik['TOLERANZSTUFE'][i] ) )
                            ws.write(5+i,  1,  float( statistik['TS_HEKTARE'][i] ) )
                            ws.write(5+i,  2,  int( statistik['IST'][i] ) )
                            ws.write(5+i,  3,  int( statistik['SOLL'][i] ) )
                            ws.write(5+i,  4,  int( statistik['DIFF'][i] ) )

                        ws.write(5+i+2,  0,  "Total")
                        ws.write(5+i+2,  1,  pycel.Formula("SUM(B6:B"+(str(5+1+i))+")"))
                        ws.write(5+i+2,  2,  pycel.Formula("SUM(C6:C"+(str(5+1+i))+")"))                
                        ws.write(5+i+2,  3,  pycel.Formula("SUM(D6:D"+(str(5+1+i))+")"))                     
                        ws.write(5+i+2,  4,  pycel.Formula("SUM(E6:E"+(str(5+1+i))+")"))     
                        
                        # Punkte ausserhalb Gemeindegrenze.
                        ws.write(5+i+4,  0,  "Punkte ausserhalb Perimetergrenze")
                        ws.write(5+i+4,  1,  int(vlayerOutsidePerimeter.featureCount()))
#                        
#                        # Das Bild in die Datei einfügen.
#        #                ws.insert_bitmap(tempdir+os.sep+"render.bmp", 5+i+6,  0)
#                        
#                        # Excel-Datei speichern.
                        file = tempdir+os.sep+"lfp3-statistik_"+date+".xls"
                        try:
                            wb.save(file)
                            QApplication.restoreOverrideCursor()
                            QMessageBox.information( None, "Export LFP3 statistics", "File written:\n"+ file)
                        except IOError:
                            QApplication.restoreOverrideCursor()
                            QMessageBox.warning( None, "Export LFP3 statistics", "File <b>not</b> written!<br>"+ file)                    
                            return
#            
#
#                    except KeyError:
#                        QMessageBox.warning( None, "", "Database query error.")                
                    except Exception:
                        QMessageBox.warning( None, "", "Could not connect to database.")
                        QApplication.restoreOverrideCursor()            
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        self.iface.messageBar().pushMessage("Error", str(traceback.format_exc(exc_traceback)), level=QgsMessageBar.CRITICAL, duration=5)                            
                        QApplication.restoreOverrideCursor()
            

            
            def writeXLSTitle(self,  ws,  fosnr,  lotnr,  date):
        
               style1 = pycel.easyxf('font: bold on;');
            


        except Exception:
            QApplication.restoreOverrideCursor()            
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.iface.messageBar().pushMessage("Error", str(traceback.format_exc(exc_traceback)), level=QgsMessageBar.CRITICAL, duration=5)                    
        QApplication.restoreOverrideCursor()  
                