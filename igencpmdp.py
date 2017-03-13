#!/usr/bin/env python
# -*- coding: utf8 -*-
##	This is the Cherrypy/REST service w/ method dispatch

import cherrypy
import base64
import simplejson
import pymongo
from pymongo import MongoClient
from bson import Binary

rcsid = "$Id: igencpmdp.py,v 1.06 2017/03/13 10:13:00 marty Exp $"

@cherrypy.tools.json_in()
@cherrypy.tools.json_out()
@cherrypy.tools.accept(media='application/json; charset=utf-8')  # must add this for add to work?
class Root:
	exposed = True
	client = MongoClient()

	def GET(self, key):
		try:
			db = self.client.dbgenerals

			j = simplejson.loads(key)
			cursor = db.igenerals.find({'_id': j})

			document = cursor.next()

			response = {
				"first_name": document['first_name'],
				"last_name": document['last_name'],
				"state": document['state'],
				"country": document['country'],
				"bio": document['bio'],
				"picture": base64.b64encode(document['picture'])
			}
			cherrypy.response.headers['Content-Type'] = "application/json; charset=utf-8"
			return response

		except (Exception) as e:
			print "Mongo Error(get): %s" % str(e)

	def POST(self):
		# Invoke the service worker code
		try:
			db = self.client.dbgenerals

			def getNextSequenceValue(sequenceName):
				sequenceDocument = db.counters.find_and_modify(
					query={'_id': sequenceName},
					update={"$inc": {'sequence_value': 1}},
					new=True,
					upsert=False
				)
				return sequenceDocument['sequence_value']

			rawData = cherrypy.request.json

			document = {
				"_id": getNextSequenceValue("genid"),
				"first_name": rawData['first_name'],
				"last_name": rawData['last_name'],
				"state": rawData['state'],
				"country": rawData['country'],
				"bio": rawData['bio'],
				"picture": Binary(base64.b64decode(rawData['picture'])),
			}

			db.igenerals.insert(document)

			cherrypy.response.headers['Content-Type'] = "application/json; charset=utf-8"
			response = {'res': 1}
			return response

		except (Exception) as e:
			print "Mongo Error: %s" % str(e)
			response = {'res': 0}
			return response

	def PUT(self):
		try:
			db = self.client.dbgenerals
			rawData = cherrypy.request.json

			document = {
				"first_name": rawData['first_name'],
				"last_name": rawData['last_name'],
				"state": rawData['state'],
				"country": rawData['country'],
				"bio": rawData['bio'],
			}

			db.igenerals.update({
						'_id': int(rawData['key'])
					}, {
						'$set': document
					}, upsert=False, multi=False)

			cherrypy.response.headers['Content-Type'] = "application/json; charset=utf-8"
			response = {'res': 1}
			return response

		except (Exception) as e:
			print "Mongo Error(chg): %s" % str(e)
			response = {'res': 0}
			return response

	def DELETE(self):
		try:
			db = self.client.dbgenerals
			cursor = db.igenerals.find().sort("_id", -1)

			max = cursor.next()

			genid = str(max['_id']).split(".", 1)

			cherrypy.response.headers['Content-Type'] = "application/json; charset=utf-8"
			return {'_id': int(genid[0])}

		except (Exception) as e:
			print "Mongo Error(top): %s" % str(e)

if __name__ == '__main__':

	cherrypy.tree.mount(
		Root(), '/api',
			{'/':
				{'request.dispatch': cherrypy.dispatch.MethodDispatcher()},
			'/public':
				{
				'tools.staticdir.on': True,
				'tools.staticdir.dir': '/home/marty/Documents/mongodb/python/cp-dispatching/public'
				}
			}
	)

	cherrypy.engine.start()
	cherrypy.engine.block()
