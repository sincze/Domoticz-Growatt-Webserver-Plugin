########################################################################################
# 	Growatt Inverter Python Plugin for Domoticz                                   	   #
#                                                                                      #
# 	MIT License                                                                        #
#                                                                                      #
#	Copyright (c) 2018 tixi                                                            #
#                                                                                      #
#	Permission is hereby granted, free of charge, to any person obtaining a copy       #
#	of this software and associated documentation files (the "Software"), to deal      #
#	in the Software without restriction, including without limitation the rights       #
#	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell          #
#	copies of the Software, and to permit persons to whom the Software is              #
#	furnished to do so, subject to the following conditions:                           #
#                                                                                      #
#	The above copyright notice and this permission notice shall be included in all     #
#	copies or substantial portions of the Software.                                    #
#                                                                                      #
#	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR         #
#	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,           #
#	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE        #
#	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER             #
#	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,      #
#	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE      #
#	SOFTWARE.                                                                          #
#                                                                                      #
#   Author: sincze                                                                     #
#                                                                                      #
#   This plugin will read the status from the running inverter via the webservice.     #
#                                                                                      #
#   V 1.0.0. Initial Release (25-08-2019)                                              #
#   V 1.0.1. Initial Release (18-04-2020)                                              #
########################################################################################


"""
<plugin key="GrowattWeb-Dev" name="Growatt Web Inverter Dev" author="sincze" version="1.0.0" externallink="https://github.com/sincze/Domoticz-Growatt-Webserver-Plugin">
    <description>
        <h2>Retrieve available Growatt Inverter information from the webservice</h2><br/>        
    </description>
    <params>
        <param field="Address" label="Server Address" width="200px" required="true" default="server-api.growatt.com"/>
        <param field="Mode2" label="Portal Username" width="200px" required="true" default="admin"/>
        <param field="Mode3" label="Portal Password" width="200px" required="true" password="true"/>
        <param field="Mode4" label="Device SN" width="200px"/>
        <param field="Mode1" label="Protocol" width="75px">
            <options>
                <option label="HTTPS" value="443"/>
                <option label="HTTP" value="80"  default="true" />
            </options>
        </param>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Python" value="18"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""

try:
    import Domoticz
    import hashlib
    import json
    import re               # Needed to extract data from Some JSON result

    local = False
except ImportError:
    local = True
    import fakeDomoticz as Domoticz
    from fakeDomoticz import Devices
    from fakeDomoticz import Parameters

class BasePlugin:
    httpConn = None
    runAgain = 6
    cookieAvailable = False
    serialAvailable = False
    devicesUpdated = False
    sessionId=""                    # Part of login Cookie
    serverId=""                     # Part of login Cookie
    plantId = ""
    #serialnumber = ""
    #baseDeviceIndex = 0

    def __init__(self):
        return

    def apiRequestHeaders(self):
        return {
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',            
            'Connection': 'keep-alive',
            'Host': 'server-api.growatt.com',
            'User-Agent': 'Domoticz/1.0',
            'Accept-Encoding': 'gzip'
        }
    
    def stationDataRequest(self):
        return {
            'Verb': 'POST',
            'URL': '/newTwoPlantAPI.do?op=getUserCenterEnertyDataByPlantid',
            'Headers' : { 'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',                         
                          'Connection': 'keep-alive',
                          'Host': 'server-api.growatt.com',
                          'User-Agent': 'Domoticz/1.0',
                          'Accept-Encoding': 'gzip',
                          'Cookie': ['JSESSIONID='+self.sessionId, 'SERVERID='+self.serverId]
                        },
            'Data': "plantId="+str(self.plantId)+"&language=1"
        }

    #def cookieRequest(self):
        #password=Parameters["Mode3"]
        #password=hashlib.md5(str.encode(password))
        #return {
            #'Verb' : 'POST',
            #'URL'  : '/newTwoLoginAPI.do',
            #'Headers' : self.apiRequestHeaders(),
            #'Data': "password="+password.hexdigest()+"&userName="+Parameters["Mode2"]
        #}
		
    def cookieRequest(self):
        password=Parameters["Mode3"]	# Convert Password to correct value.
        password_md5 = hashlib.md5(password.encode("utf-8")).hexdigest()
        for i in range(0, len(password_md5), 2):
           if password_md5[i] == "0":
            password_md5 = password_md5[0:i] + "c" + password_md5[i + 1 :]
		
        return {
            'Verb' : 'POST',
            'URL'  : '/newTwoLoginAPI.do',
            'Headers' : self.apiRequestHeaders(),
            'Data': "password="+password_md5+"&userName="+Parameters["Mode2"]
        }
            
    def apiRequestHeaders_serialnumber(self):
        return {
            'Verb': 'GET',
            'URL': "/newTwoPlantAPI.do?op=getAllDeviceList&plantId="+str(self.plantId)+"&content=",
#            #'URL': "/newTwoPlantAPI.do?op=getAllDeviceList&plantId="+str(self.plantId)+"&content",
#            #'URL': "/newTwoPlantAPI.do?op=getAllDeviceList&plantId=155390&content=",
            'Headers' : { 'Connection': 'keep-alive',
                          'Host': 'server-api.growatt.com',
                          'User-Agent': 'Domoticz/1.0',
                          'Accept-Encoding': 'gzip',
                          'Accept-Charset': 'utf-8, iso-8859-1;q=0.5',
#                          Content-Type: text/html;charset=UTF-8
                          'Cookie': ['JSESSIONID='+self.sessionId, 'SERVERID='+self.serverId]
                        }
        }
    
    def apiRequestHeaders_allinfo(self):
        return {
            'Verb': 'GET',                   
            'URL': "/newInverterAPI.do?op=getInverterDetailData_two&inverterId="+Parameters["Mode4"],               
            'Headers' : { 'Connection': 'keep-alive',                          
                          'Host': 'server-api.growatt.com',
                          'User-Agent': 'Domoticz/1.0',
                          'Accept-Encoding': 'gzip',
                          'Cookie': ['JSESSIONID='+self.sessionId, 'SERVERID='+self.serverId]
                        },
        }
     
    def apiConnection(self):
        if Parameters["Mode1"] == "443":
            return Domoticz.Connection(Name="Growatt Portal API", Transport="TCP/IP", Protocol="HTTPS",
                                       Address=Parameters["Address"], Port=Parameters["Mode1"])
        else:
            return Domoticz.Connection(Name="Growatt Portal API", Transport="TCP/IP", Protocol="HTTP",
                                       Address=Parameters["Address"], Port=Parameters["Mode1"])

    def startDeviceUpdate(self, Connection):
        if not self.cookieAvailable:            
            self.devicesUpdated = False
            #DumpHTTPResponseToLog(self.cookieRequest())
            Connection.Send(self.cookieRequest())                               # Execute Login!
        else:
            #if not self.serialTest:
#                Connection.Send(self.apiRequestHeaders_serialnumber())
#            elif (self.serialAvailable):
            if (self.serialAvailable):
#                Connection.Send(self.apiRequestHeaders_serialnumber())  
                DumpHTTPResponseToLog(self.apiRequestHeaders_allinfo())
                Connection.Send(self.apiRequestHeaders_allinfo())            
            else:
                DumpHTTPResponseToLog(self.stationDataRequest())
                Connection.Send(self.stationDataRequest())


    def onStart(self):
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()
                
        if Parameters["Mode4"] != "":
            self.serialAvailable = True
            Domoticz.Debug("SM Found")
            createDevices(self.serialAvailable)            
        else:
            Domoticz.Log("No Inverter Serial Provided")
            self.serialAvailable = False
            createDevices(self.serialAvailable)                                     # Check if devices need to be created
        
        self.httpConn = self.apiConnection()
        self.httpConn.Connect()

    def onStop(self):
        Domoticz.Log("onStop - Plugin is stopping.")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect Status: "+str(Status))
        Domoticz.Log(Description)
        if (Status == 0):           
            self.startDeviceUpdate(Connection)
            UpdateDevice(Unit=3, nValue=1, sValue="On", TimedOut=0)         # Inverter device is on            
        else:
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Mode1"]+" with error: "+Description)
            UpdateDevice(Unit=3, nValue=0, sValue="Off", TimedOut=0)        # Inverter device is off

    def onMessage(self, Connection, Data):
        DumpHTTPResponseToLog(Data)
        
        try:
            strData = Data["Data"].decode("utf-8", "ignore")
            Status = int(Data["Status"])
            #LogMessage(strData)
            Domoticz.Debug("Retrieved following strData: "+str(strData))        # looks like json "data":{"e_today":15.8,"e_total":2096.3,"vpv1":357.1,"ipv1":0.0,"ppv1":0.0,"vpv2":

            if (Status == 200):
                #Domoticz.Debug("Starting to load JSON")
                apiResponse = json.loads(strData)
                Domoticz.Debug("Retrieved following json: "+json.dumps(apiResponse))

                if ('back' in apiResponse):                                             # Response to: Connection.Send(self.cookieRequest()) 
                    Domoticz.Log("Login Succesfull")
                    self.plantId = apiResponse["back"]["data"][0]["plantId"]
                    self.plantIdAvailable = True
                    Domoticz.Debug("Step 1. Plant ID: "+str(self.plantId)+" was found")
                    self.ProcessCookie(Data)                                            # The Cookie is in the RAW Response, not in the JSON
                    if not self.cookieAvailable:
                        Domoticz.Debug("No cookie extracted!")
                    else:
                        Domoticz.Debug("Request Data with retrieved cookie!")   
                        #Connection.Send(self.apiRequestHeaders_serialnumber())  
                        self.startDeviceUpdate(Connection)
                       
                elif ('powerValue' in apiResponse):
                    self.devicesUpdated = True                    
                    current = apiResponse['powerValue']
                    total = apiResponse['totalValue'] # Convert kWh to Wh
                    Wh= round(float(total)*1000)
                    sValue=str(current)+";"+str( Wh )
                    Domoticz.Log("Plugin No SN: Producing: "+str(current)+" Watt. Totall produced: "+str(total)+" kWh in Wh that is: "+str( Wh ) )
                    UpdateDevice(Unit=1, nValue=0, sValue=sValue, TimedOut=0)
                    UpdateDevice(Unit=2, nValue=0, sValue=current, TimedOut=0)
                
                elif ('deviceSn' in apiResponse):
                    Domoticz.Debug("Retrieved Serial: "+json.dumps(apiResponse))
            
                elif ('data' in apiResponse):
                    self.devicesUpdated = True
                    current = apiResponse["data"]["ppv1"]
                    total = apiResponse["data"]["e_total"]
                    Wh= round(float(total)*1000)
                    sValue=str(current)+";"+str( Wh )
                    Domoticz.Log("Plugin with SN: Producing: "+str(current)+" Watt. Totall produced: "+str(total)+" kWh in Wh that is: "+str( Wh ) )
                    UpdateDevice(Unit=1, nValue=0, sValue=sValue, TimedOut=0)
                    UpdateDevice(Unit=2, nValue=0, sValue=current, TimedOut=0)

                    #String_1
                    current_a_pv1 = apiResponse["data"]["ipv1"]                
                    voltage_v_pv1 = apiResponse["data"]["vpv1"]                
                    UpdateDevice(Unit=4, nValue=0, sValue=str(current_a_pv1))
                    UpdateDevice(Unit=5, nValue=0, sValue=str(voltage_v_pv1))
               
			        #String_2
                    current_a_pv2 = apiResponse["data"]["ipv2"]
                    voltage_v_pv2 = apiResponse["data"]["vpv2"]
                    current_w_pv2 = apiResponse["data"]["ppv2"]
                    UpdateDevice(Unit=6, nValue=0, sValue=str(current_a_pv2))
                    UpdateDevice(Unit=7, nValue=0, sValue=str(voltage_v_pv2))
    
			        # AC1
                    current_a_ac1 = apiResponse["data"]["iacr"]    
                    voltage_v_ac1 = apiResponse["data"]["vacr"]
                    power_w_ac1 =   apiResponse["data"]["pacr"]
                    UpdateDevice(Unit=8, nValue=0, sValue=str(current_a_ac1))
                    UpdateDevice(Unit=9, nValue=0, sValue=str(voltage_v_ac1))

    		        # AC2 
                    current_a_ac2 = apiResponse["data"]["iacs"]
                    voltage_v_ac2=  apiResponse["data"]["vacs"]
                    power_w_ac2 =   apiResponse["data"]["pacs"]
    
                    # AC3
                    current_a_ac3= apiResponse["data"]["iact"]
                    voltage_v_ac3= apiResponse["data"]["vact"]
                    power_w_ac3 =  apiResponse["data"]["pact"]           

                elif apiResponse is None:
                    Domoticz.Error("No data received from Growatt API")
                    self.tokenAvailable = False
                    self.httpConn.Disconnect()
            
                else:
                    Domoticz.Debug("Not received anything usefull!")

                if self.runAgain > 2:
                    Domoticz.Debug("Next active heartbeat far away, disconnecting and dropping connection.")
                    self.httpConn.Disconnect()
                    cookieAvailable = False
                    self.devicesUpdated = False		# 18-04-2020
                    self.httpConn = None
            
            elif (Status == 302):
                Domoticz.Error("Probably no login possible!.")                
                cookieAvailable = False
                self.devicesUpdated = False
                Connection.Send(self.cookieRequest())
                #self.cookieAvailable = False
                #self.httpConn.Disconnect()
                #self.httpConn = None
            elif (Status == 400):
                Domoticz.Error("Growatt Inverter returned a Bad Request Error.")
            elif (Status == 500):
                Domoticz.Error("Growatt Inverter returned a Server Error.")
            else:
                Domoticz.Error("Growatt Inverter returned a status: "+str(Status))

        except AttributeError:
            self.cookieAvailable = False            
            #DumpHTTPResponseToLog(Data)
            Domoticz.Debug("---> AttributeError starting over") 

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called for connection to: "+Connection.Address+":"+Connection.Port)

    def onHeartbeat(self):
        #Domoticz.Trace(True)
        if self.httpConn is not None and (self.httpConn.Connecting() or self.httpConn.Connected()) and not self.devicesUpdated:
            Domoticz.Debug("onHeartbeat called, Connection is alive.")
        else:
            self.runAgain = self.runAgain - 1
            if self.runAgain <= 0:
                if (self.httpConn == None):
				#if (self.httpConn == None and self.cookieAvailable == True):
                    #self.cookieAvailable = False
                    #self.httpConn = self.apiConnection()
                    self.httpConn = self.apiConnection()
                    #self.httpConn.Connect()
                    
                if not self.httpConn.Connected():
                    self.httpConn.Connect()
                else:
                    self.startDeviceUpdate(self.httpConn)
                
                self.runAgain = 6
            else:
                Domoticz.Debug("onHeartbeat called, run again in "+str(self.runAgain)+" heartbeats.")
        #Domoticz.Trace(False)


    def ProcessCookie(self, httpDict):
        if isinstance(httpDict, dict):            
            Domoticz.Debug("Analyzing Data ("+str(len(httpDict))+"):")
            for x in httpDict:
                if isinstance(httpDict[x], dict):
                    if (x == "Headers"):
                        Domoticz.Debug("---> Headers found")    
                        for y in httpDict[x]:
                            # Domoticz.Debug("------->'" + y + "':'" + str(httpDict[x][y]) + "'")
                            if (y == "Set-Cookie"):        
                                Domoticz.Debug("---> Process Cookie Started")
                                try:
                                    self.sessionId = re.search(r"(?<=JSESSIONID=).*?(?=;)", str(httpDict[x][y])).group(0)
                                    Domoticz.Debug("---> SessionID found: "+ str(self.sessionId)) 
                                    self.cookieAvailable = True
                                except AttributeError:
                                    self.cookieAvailable = False
                                    Domoticz.Debug("---> SessionID NOT found") 

                                if self.cookieAvailable:
                                    try:
                                        self.serverId = re.search(r"(?<=SERVERID=).*?(?=;)", str(httpDict[x][y])).group(0)
                                        Domoticz.Debug("---> ServerID found: "+ str(self.serverId)) 
                                    except AttributeError:
                                        self.cookieAvailable = False
                                        Domoticz.Debug("---> ServerID NOT found") 

#                               DEBUGGING ONLY
#                                if self.cookieAvailable:
#                                    self.cookie=("JSESSIONID="+self.sessionId+"; SERVERID="+self.serverId)
#                                    Domoticz.Debug("---> Cookies found "+ str(self.cookie)) 
#                                else:
#                                    Domoticz.Debug("---> Something went wrong retrieving cookie attributes") 
#------------------------------------------------------------------------------------------------------------ 




global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def LogMessage(Message):
    if Parameters["Mode6"] == "File":
        f = open(Parameters["HomeFolder"]+"http.html","w")
        f.write(Message)
        f.close()
        Domoticz.Log("File written")

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

#def DumpHTTPResponseToLog(httpDict):
#    if isinstance(httpDict, dict):
#        Domoticz.Debug("HTTP Details ("+str(len(httpDict))+"):")
#        for x in httpDict:
#            if isinstance(httpDict[x], dict):
#                Domoticz.Debug("--->'"+x+" ("+str(len(httpDict[x]))+"):")
#                for y in httpDict[x]:
#                    Domoticz.Debug("------->'" + y + "':'" + str(httpDict[x][y]) + "'")
#            else:
#                Domoticz.Debug("--->'" + x + "':'" + str(httpDict[x]) + "'")

def DumpHTTPResponseToLog(httpResp, level=0):
    if (level==0): Domoticz.Debug("HTTP Details ("+str(len(httpResp))+"):")
    indentStr = ""
    for x in range(level):
        indentStr += "----"
    if isinstance(httpResp, dict):
        for x in httpResp:
            if not isinstance(httpResp[x], dict) and not isinstance(httpResp[x], list):
                Domoticz.Debug(indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")
            else:
                Domoticz.Debug(indentStr + ">'" + x + "':")
                DumpHTTPResponseToLog(httpResp[x], level+1)
    elif isinstance(httpResp, list):
        for x in httpResp:
            Domoticz.Debug(indentStr + "['" + x + "']")
    else:
        Domoticz.Debug(indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")
       
def UpdateDevice(Unit, nValue, sValue, TimedOut=0, AlwaysUpdate=False):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (Devices[Unit].TimedOut != TimedOut):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
            Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return


#############################################################################
#                       Device specific functions                           #
#############################################################################

def createDevices(serialAvailable):

    # Images
    # Check if images are in database
    if "Growatt" not in Images:
        Domoticz.Image("Growatt.zip").Create()
        image = Images["Growatt"].ID # Get id from database
        Domoticz.Log( "Image created. ID: " + str( image ) )

    # Are there any devices?
    ###if len(Devices) != 0:
        # Could be the user deleted some devices, so do nothing
        ###return

    # Give the devices a unique unit number. This makes updating them more easy.
    # UpdateDevice() checks if the device exists before trying to update it.
    if (len(Devices) == 0):
        Domoticz.Device(Name="Inverter (kWh)", Unit=1, TypeName="kWh", Used=1).Create()
        Domoticz.Log("Inverter Device kWh created.")
        Domoticz.Device(Name="Inverter (W)", Unit=2, TypeName="Usage", Used=1).Create()
        Domoticz.Log("Inverter Device (W) created.")
        Domoticz.Device(Name="Inverter Status", Unit=3, TypeName="Switch", Used=1, Image=image).Create()
        
        Domoticz.Log("Inverter Device (Switch) created.")

        if (serialAvailable):
            Domoticz.Device(Name="Inverter output current str1 (A)", Unit=4, Type=243, Subtype=23, Used=1).Create()
            Domoticz.Log("Inverter Device (A) created.")
            Domoticz.Device(Name="Inverter output voltage str1 (V)", Unit=5, Type=243, Subtype=8, Used=1).Create()
            Domoticz.Log("Inverter Device (V) created.")
        
            Domoticz.Device(Name="Inverter output current str2 (A)", Unit=6, Type=243, Subtype=23, Used=1).Create()
            Domoticz.Log("Inverter Device (A) created.")
            Domoticz.Device(Name="Inverter output voltage str2 (V)", Unit=7, Type=243, Subtype=8, Used=1).Create()
            Domoticz.Log("Inverter Device (V) created.")

            Domoticz.Device(Name="Inverter output current AC (A)", Unit=8, Type=243, Subtype=23, Used=1).Create()
            Domoticz.Log("Inverter Device (A) created.")
            Domoticz.Device(Name="Inverter output voltage AC (V)", Unit=9, Type=243, Subtype=8, Used=1).Create()
            Domoticz.Log("Inverter Device (V) created.")
    
    Domoticz.Log( "Devices created." )
    DumpConfigToLog()
