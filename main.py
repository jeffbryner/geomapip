#!/usr/bin/python2
import sys
import os
import re
from kivy.app import App
from kivy.animation import Animation
from kivy.uix.relativelayout import RelativeLayout
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty
from kivy.vector import Vector
from kivy.factory import Factory
from random import randint
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.core.window import Window
from StringIO import StringIO
import pygeoip
from time import sleep
from threading import Thread
from collections import deque

#constants
minLat=-90
maxLat=90
minLon=-180
maxLon=180
MAP_HEIGHT=1024
MAP_WIDTH=1680
ipre=re.compile('(?:\d{1,3}\.){3}\d{1,3}')
gi = pygeoip.GeoIP('/usr/share/GeoIP/GeoLiteCity.dat', pygeoip.MEMORY_CACHE)
homeLatitude= 45.5886
homeLongitude=-122.7064

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
            data = sys.stdin.readline()
            if data is None:
                #sleep(2)
                continue
            q.appendleft(data)

    def pop(self):
        return self.queue.pop()

class ipdot(Widget):        
    def on_complete(self,*args):
        self.parent.remove_widget(self)

    
class geoMapIP(RelativeLayout):                        
    def layoutCallback(self,dt):
        data=''        
        try:
            data = self.stdin.pop()
        except Exception as e:
            print(e)
            return
        for ip in ipre.findall(data):
            geoDict=gi.record_by_addr(ip)
            if not geoDict==None:
                x=lonToX(geoDict['longitude'])
                y=latToY(geoDict['latitude'])                
                anip = ipdot(size_hint=(None, None), size=(15, 15),pos=(x - 15, y - 15)) 
                self.add_widget(anip)
                anim = Animation(x=self.homeX, y=self.homeY,duration=3, t='out_back')                
                anim.bind(on_complete=anip.on_complete)
                anim.start(anip)
        
class geoMapIPApp(App):           

    def build(self):
        root = self.root        
        kvLayout=geoMapIP()
        kvLayout.stdin=stdinRead()
        kvLayout.stdin.start()
        kvLayout.homeX=lonToX(homeLongitude)
        kvLayout.homeY=latToY(homeLatitude)
        Clock.schedule_interval(kvLayout.layoutCallback,1)        
        return kvLayout

#Factory.register("ipdot", ipdot)
if __name__ == '__main__':
    geoMapIPApp().run()
    
    
