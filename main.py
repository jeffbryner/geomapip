#!/usr/bin/python2
import sys
import re
from kivy.app import App
from kivy.animation import Animation
from kivy.uix.relativelayout import RelativeLayout
from kivy.clock import Clock
from kivy.uix.widget import Widget
from random import randint, choice
import pygeoip
from time import sleep
from threading import Thread
from collections import deque
from kivy.properties import StringProperty
from kivy.config import Config


#constants
minLat=-90
maxLat=90
minLon=-180
maxLon=180
MAP_HEIGHT=1024
MAP_WIDTH=2048
ipre=re.compile('(?:\d{1,3}\.){3}\d{1,3}')
gi = pygeoip.GeoIP('/usr/share/GeoIP/GeoLiteCity.dat', pygeoip.MEMORY_CACHE)
homeLatitude= 45.5886
homeLongitude=-122.7064
#max ipdots to flood the screen with at once.
MAX_IPS=20

def latToY(targetLat):
    return ((targetLat - minLat) / (maxLat - minLat)) * (MAP_HEIGHT - 1)

def lonToX(targetLon):
    return ((targetLon - minLon) / (maxLon - minLon)) * (MAP_WIDTH - 1)
    
class stdinRead(Thread):
    #set as a thread to allow for lags in stdin or no stdin at all
    def __init__(self, *largs, **kwargs):
        super(stdinRead, self).__init__(*largs, **kwargs)
        self.daemon = True
        self.queue = deque()
        self.quit = False
        self.index = 0

    def run(self):
        q = self.queue
        while not self.quit:
            data = sys.stdin.readline().strip()
            if data is None or len(data)==0:
                sleep(1)
                continue
            q.appendleft(data)
            sleep(.01)

    def pop(self):
        return self.queue.pop()

class ipdot(Widget):        
    def on_complete(self,*args):
        self.parent.remove_widget(self)

    
class geoMapIP(RelativeLayout):                        
    status=StringProperty('queue: 0')
    def layoutCallback(self,dt):
        data=''        
        try:
            self.status="queue:%d"%len(self.stdin.queue)
            #extract at most X lines from the queue to map/show/animate
            for x in range(0,min(MAX_IPS,len(self.stdin.queue))):
                data = self.stdin.pop()            
                for ip in ipre.findall(data):
                    geoDict=gi.record_by_addr(ip)
                    if not geoDict==None:
                        x=lonToX(geoDict['longitude'])
                        y=latToY(geoDict['latitude'])                
                        anip = ipdot(size_hint=(None, None), size=(15, 15),pos=(x - 15, y - 15)) 
                        self.add_widget(anip)
                        transition=choice(['out_cubic','in_out_quart','in_out_quint','in_out_back'])
                        anim = Animation(x=self.homeX, y=self.homeY,duration=randint(1,5), t=transition)
                        anim.bind(on_complete=anip.on_complete)
                        anim.start(anip)
        except Exception as e:
            print(e)
            return
        
class geoMapIPApp(App):           
    def build_config(self, config):
        print('Configuring************')
        Config.set('graphics','width',MAP_WIDTH)
        Config.set('graphics','height',MAP_HEIGHT)
        Config.set('kivy','log_level','critical')
        Config.set('kivy','log_enable','0')        
        
        
    def build(self):
        kvLayout=geoMapIP()        
        kvLayout.stdin=stdinRead()
        kvLayout.stdin.start()
        kvLayout.homeX=lonToX(homeLongitude)
        kvLayout.homeY=latToY(homeLatitude)        
        Clock.schedule_interval(kvLayout.layoutCallback,1)        
        return kvLayout

if __name__ == '__main__':
    geoMapIPApp().run()
    
    
