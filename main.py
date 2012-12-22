#!/usr/bin/python2
import sys
import re
from kivy.app import App
from kivy.animation import Animation
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.clock import Clock
from kivy.uix.widget import Widget
from random import randint, choice
import pygeoip
from time import sleep
from threading import Thread
from collections import deque
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
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
MAX_IPS=3

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
        self.layout.ips-=1
        self.parent.remove_widget(self)


class ipdotDetailed(BoxLayout):        
    ip=StringProperty('')
    location=StringProperty('')
    def on_complete(self,*args):
        self.layout.ips-=1
        self.parent.remove_widget(self)


    
class geoMapIP(RelativeLayout):
    status=StringProperty('queue: 0')
    detail=BooleanProperty(False)
    ips=NumericProperty(0)
    
    def detail_switch(self):
        if self.detail:
            self.detail=False
        else:
            self.detail=True
        
        
    def layoutCallback(self,dt):
        data=''        
        try:
            self.status="queue:%d"%len(self.stdin.queue)
            #extract at most X lines from the queue to map/show/animate
            if self.ips<=MAX_IPS:
                for x in range(0,min(MAX_IPS,len(self.stdin.queue))):
                    data = self.stdin.pop()            
                    for ip in ipre.findall(data):
                        geoDict=gi.record_by_addr(ip)
                        if not geoDict==None:
                            x=lonToX(geoDict['longitude'])
                            y=latToY(geoDict['latitude'])
                            #show detail, or just the dot
                            if self.detail:
                                anip = ipdotDetailed(size_hint=(None, None), size=(100, 15),pos=(x - 100, y - 15)) 
                                anip.ip=ip
                                #show city for US locations.
                                #change this to your liking about what to display.
                                if not geoDict['country_code'] in ('US'):
                                    anip.location=geoDict['country_name']
                                else: 
                                    anip.location=geoDict['city'] + ' ' + geoDict['region_name']
                                    
                            else:
                                anip = ipdot(size_hint=(None, None), size=(15, 15),pos=(x - 15, y - 15)) 
                            
                            anip.layout=self
                            self.add_widget(anip)
                            transition=choice(['out_cubic','in_out_quart','in_out_quint','in_out_back'])
                            animationTime=randint(1,5)
                            if self.detail:
                                #slow down to give folks time to see the detail
                                animationTime*=2

                            #animate the ipdot going to the home coordinates.
                            anim = Animation(x=self.homeX-anip.size[0]/2, y=self.homeY,duration=animationTime, t=transition)                                
                            anim.bind(on_complete=anip.on_complete)
                            anim.start(anip)
                            self.ips+=1

        except Exception as e:
            print(e)
            return
        
class geoMapIPApp(App):           
    def build_config(self, config):
        Config.set('graphics','width',1650)
        Config.set('graphics','height',1024)
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
    
    
