# -*- coding:utf-8 -*-
import requests
import json
import datetime
import pymysql
import time
from bs4 import BeautifulSoup
from rooms import rooms


class MazerRooms:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWeb'
                              'Kit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Mobile Safari/537.36'
            }
        )
        self.rooms=rooms
        configs = self.getconfig()
        lostime = datetime.datetime.now() + datetime.timedelta(hours=int(configs[5]))
        self.date=lostime.strftime('%Y-%m-%d')
        self.time=lostime.strftime('%H:%M:%S')
        self.datetime=lostime.strftime('%Y-%m-%d %H:%M:%S')
        self.weekLength=3
        self.conn = pymysql.connect(
            host=configs[0],
            port=int(configs[1]),
            user=configs[2],
            password=configs[3],
            db=configs[4],
            charset='utf8'
        )
        self.cur = self.conn.cursor()

    def getconfig(self):
        with open('config.ini','r',encoding='utf-8') as f:
            configs=f.readlines()
        for i in range(len(configs)):
            configs[i]=configs[i].strip()
        return configs[:6]

    def getbookinginfo(self,api,item_id, room):
        postdata={
            'item_id': item_id,
            'date': self.date,
            'weekLength': self.weekLength,
        }
        error=3
        while True:
            try:
                page=self.session.post(api,postdata).content.decode()
                break
            except:
                if error==0:
                    raise ConnectionError('Please Check your Network!')
                else:
                    error-=1
        print(page)
        bookinginfo=json.loads(page)
        bookingtimes=bookinginfo['times']
        for bookingtime in bookingtimes:
            try:
                booking=bookingtime['days'][self.date]
            except:
                booking=bookingtime['days'][0]
            try:
                bookingtype=booking['type']
                if bookingtype=='empty':
                    break
            except:
                if booking['class']=='closed':
                    bookingtype = 'closed'
                elif booking['class']=='booked':
                    bookingtype = 'booked'
                else:
                    bookingtype='None'
            try:
                bookingtime = bookingtime['name']
            except:
                try:
                    bookingtime = booking['name']
                except:
                    bookingtime =booking['time']
            print(bookingtime,bookingtype)
            sql = "INSERT INTO bookingstate VALUES ('%s','%s','%s','%s','mazeroom')" % (room,self.datetime,self.date+' '+bookingtime, bookingtype)
            self.cur.execute(sql)
        self.conn.commit()

    def getbookinginfo60room(self,url,room):
        error = 3
        while True:
            try:
                page = self.session.get(url).content.decode()
                break
            except:
                if error == 0:
                    raise ConnectionError('Please Check your Network!')
                else:
                    error -= 1
        soup=BeautifulSoup(page,'html.parser')
        #print(soup.prettify())
        bookinginfos=soup.find('table',{'class':'table_rooms'}).find('tbody').find_all('tr')
        for bookinginfo in bookinginfos:
            bookingtime=bookinginfo.td.text
            if bookingtime[-2:]=='PM':
                bookingtime=str(int(bookingtime[:bookingtime.index(':')])+12)+bookingtime[bookingtime.index(':'):-2]
            else:
                bookingtime=bookingtime[:-2]
            bookingtime=self.date+' '+bookingtime
            bookingtype=bookinginfo.find('td',{'class':'column_selection_at_today'}).text
            print(bookingtime,bookingtype)
            sql = "INSERT INTO bookingstate VALUES ('%s','%s','%s','%s','60out')" % (
            room, self.datetime,bookingtime, bookingtype)
            self.cur.execute(sql)
        self.conn.commit()


    def run(self):
        for room in rooms.keys():
            print(room)
            if rooms[room]['item_id']=='60out':
                self.getbookinginfo60room(rooms[room]['api'],room)
            else:
                self.getbookinginfo(rooms[room]['api'], rooms[room]['item_id'], room)
            time.sleep(0)

    def runontime(self):
        with open('time.txt','r') as f:
            times=f.readlines()
        for i in range(len(times)):
            times[i]=times[i].strip()
        while True:
            lostime = (datetime.datetime.now() + datetime.timedelta(hours=-15)).strftime('%H:%M')
            print(self.date+' '+lostime)
            if lostime in times:
                self.run()
            else:
                time.sleep(5)

MazerRooms().runontime()
