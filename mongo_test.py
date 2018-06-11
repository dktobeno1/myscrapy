from pymongo import MongoClient
client = MongoClient('116.62.237.239', 27017)
db_admin = client['admin']
db_admin.authenticate('root','111111')
#db = client.test
print(db.projectdb.find({'name':'qidian_author'}))
#users=[{"name":"zan","age":18},{"name":"lisi","age":20}]
#for user in users:
    #db.test_collection.save(user)
#print(db.test_collection.find_one())
#for each in db.test_collection.find():
    #print(each)
#_id = db.test_collection.find_one()['_id']
#db.test_collection.remove(_id)
#for each in db.test_collection.find():
 #   print(each)
