from mutagen import File 
from pathlib import Path
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import hashlib
import cv2
import sys

sys.setrecursionlimit(10000)
MP4_DIR='/mnt/nas/private/mp4'

class MP4Files:
    def __init__(self, offset=0):
        #self.files = self._search(offset)
        self.mongo_user = os.environ['MONGO_INITDB_ROOT_USERNAME']
        self.mongo_pass = os.environ['MONGO_INITDB_ROOT_PASSWORD']
        self.client = MongoClient('mongo', 27017, username=self.mongo_user, password=self.mongo_pass)


    def search(self):
        db = self.client['videos_db']
        collection = db['fileinfo']
        
        files = collection.find({})
        files = list(files)
        for i, f in enumerate(files[:]):
            files[i]['id'] = str(f['_id'])
 
        files = [f for f in files if not f['filename'].startswith('VR')]

        tags = []
        tag_fileinfo_collection = db['tag_fileinfo']
        tag_collection = db['tag']
        for f in files:
            file_id = f['_id']
            tag_fileinfo = tag_fileinfo_collection.find({'fileinfo_id': file_id})
            tag = []
            for t_f in tag_fileinfo:
                tag_id = t_f['tag_id']
                t = tag_collection.find_one({'_id': tag_id})
                tag.append(t['tag'])
            tags.append(','.join(tag))

        return files, tags

    def _set_fileinfo(self, filename, path, hash_md5):
       db = self.client['videos_db']
       collection = db['fileinfo']
       collection.create_index([('hash_md5', 1)], unique=True )
       insert_data = {
           'filename': filename,
           'path': path,
           'hash_md5': hash_md5,
           'count': 0,
           'grade': None,
       }
       doc = collection.find_one({'hash_md5':hash_md5})
       if not doc:
           collection.update(
                {"hash_md5": hash_md5},
                {'$setOnInsert': insert_data},
                upsert=True
           )
       else:
           doc['path'] = path
           doc['filename'] = filename
           collection.save(doc)


    def _set_tags(self, tags, hash_md5):
        for tag in tags:
            db = self.client['videos_db']
            tag_collection = db['tag']
            doc = tag_collection.find_one({'tag': tag})
            if doc:
                continue
            tag_collection.insert({'tag': tag})


        fileinfo_collection = db['fileinfo']
        fileinfo = fileinfo_collection.find_one({'hash_md5':hash_md5})
        fileinfo_id = fileinfo['_id']

        tag_fileinfo_collection = db['tag_fileinfo']
        tag_fileinfo_collection.remove({'fileinfo_id': fileinfo_id})
            

        for tag in tags:
            tag = tag_collection.find_one({'tag': tag})
            tag_id = tag['_id']

            tag_fileinfo_collection.update(
                {'tag_id': tag_id, 'fileinfo_id': fileinfo_id},
                {'$setOnInsert': {'tag_id': tag_id, 'fileinfo_id': fileinfo_id}},
                upsert=True
            )


    def crawl(self):
        p = Path(MP4_DIR)
        paths = list(p.glob("**/*.mp4"))

        files = []        
        for path in paths:
            try:
                filepath = str(path) 
                filename = filepath.split('/')[-1].replace(' ', '_')
                cap = None
                cap = cv2.VideoCapture(str(path))
                hash_md5 = None
                hash_md5 = hashlib.md5(cap.read()[1]).hexdigest()
                if hash_md5:
                    self._set_fileinfo(filename, filepath, hash_md5)

                #meta = File(path)
                #if "\xa9tag" in meta:
                #    tags = meta["\xa9tag"] 
                #    self._set_tags(tags, hash_md5)
            except:
                print(path)
                import traceback
                traceback.print_exc()
            import time
            time.sleep(1)

        return files


    def get_fileinfo(self, file_id):
        file_id = ObjectId(file_id)
        db = self.client['videos_db']
        fileinfo_collection = db['fileinfo']
        fileinfo = fileinfo_collection.find_one({'_id': file_id})

        tag_fileinfo_collection = db['tag_fileinfo']
        tag_fileinfo = tag_fileinfo_collection.find({'fileinfo_id': fileinfo['_id']})
        tags = []
        for t_f in tag_fileinfo:
            tag_id = t_f['tag_id']
            tag_collection = db['tag']
            tag = tag_collection.find_one({'_id': tag_id})
            tags.append(tag['tag']) 
        return fileinfo, tags

    def _add_meta(self, path, tags):
        meta = File(path)
        meta["\xa9tag"] = tags
        meta.save()
        print("save OK:", path, tags)

    def set_tags(self, file_id, tags):
        file_id = ObjectId(file_id)
        db = self.client['videos_db']
        fileinfo_collection = db['fileinfo']
        fileinfo = fileinfo_collection.find_one({'_id': file_id}) 
        hash_md5 = fileinfo['hash_md5']

        tags = tags.split(',')
        self._set_tags(tags, hash_md5)
        
        import threading
 
        #path = fileinfo['path']  
        #th = threading.Thread(target=self._add_meta, args=(path, tags))
        #th.start()
        print("set_tags")
 

