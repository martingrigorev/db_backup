#!/usr/bin/env python

'''
Create full backup every user's database.

Creation date: 15.10.2014
Last modify date: 16.10.2014
'''

import MySQLdb
import socket
import os
import logging
import time
import subprocess
import sys
import smtplib
import mimetypes
import email
import email.mime.application
import socket

BACKDIR = '/home/setevoy/backups/'
LOGPATH = '/var/log/database_backup.log'
DBROOT = 'root'
_DBROOTPW = 'PasswordHere'
DBHOST = 'localhost'

# exclude databases list - will not be added to backup
EXCLUDE = 'mysqlslap'
HOST = socket.gethostname()

logging.basicConfig(format = '%(filename)s - %(levelname)-3s [%(asctime)s] %(message)s ', filename=LOGPATH, level=logging.DEBUG)


def dir_bkptype(day):

    '''On Sunday - create full weekly backup with 'full_backup()';
       other days - incremental backup with inc_backup()';
       also used in 'back_dir_create()' to create BACKDIR/weekly or daily;
       also used in 'clear_old_dirs()' for deleting old directories.'''

    if day == 'Mon':
        bkptype = 'weekly'
    else:
        bkptype = 'daily'

    logging.info('Today is %s, will use backuptype %s.' % (day, bkptype))

    return(bkptype)


def back_dir_create(user, bkptype):

    '''Creates new directory for each day;
       depending on data recieved from 'dir_bkptype()'
       can create 'weekly' or 'daily' directory.'''

    dirname = os.path.join(BACKDIR, user, bkptype, '%s-database/' % time.strftime('%Y-%m-%d'))

    if not os.path.exists(dirname):
        os.makedirs(dirname)
        logging.info('Directory %s created' % dirname)

    return(dirname)

def mysql_connect(dbroot, dbhost, dbrootpw):

    '''Calls in 'run_backup()' with [DBROOT], [_DBROOTPW] and [DBHOST]
       in arguments.
       Creates object [cursor] for use in select_user_dbs()'''

    db = MySQLdb.connect(dbhost, dbroot, dbrootpw)
    cursor = db.cursor()

    return(cursor)


def select_user_dbs(cursor):

    '''Calls with [cursor] from 'mysql_connect()';
       returns two lists like:
       for users - ['setevoy', 'setevoy', 'hudeem', [...] 'vexim', 'worlddesign', 'zabbix']
       and their databases: ['setevoy_test', 'autocomtestdb', 'hudeem_db', [...] 'vexim', 'worlddesign_db1', 'zabbix']'''

    users_list = []
    database_list = []

    cursor.execute('select user, db from mysql.db')

    for line in cursor.fetchall():
        users_list.append(line[0])
        database_list.append(line[1])

    return(users_list, database_list)

    cursor.close()


def mysql_dump(dbroot, dbrootpw, database, archname):

    '''Calls in 'run_backup()' to create dump'''

    subprocess.call('mysqldump -u %s -p%s %s | bzip2 > %s' % (dbroot, dbrootpw, database, archname), shell=True)
    logging.info('Database backup complete: database %s saved to %s' % (database, archname))


def sendmail():

    '''Send email report to [to] with used disk space information.'''

    sender = 'backup@venti.domain.org.ua'
    to = ['root@domain.org.ua']

    msg = email.mime.Multipart.MIMEMultipart()

    msg['Subject'] = ('Database backup report')
    msg['From'] = 'Backup Manager <backup@venti.domain.org.ua>'
    msg['To'] = 'root <root@domain.org.ua>'

    body = email.mime.Text.MIMEText("""

    Databases backup on %s finished.

    """ % (HOST))

    msg.attach(body)

    smtpconnect = smtplib.SMTP('localhost:25')
    #smtpconnect.set_debuglevel(1)
    smtpconnect.sendmail(sender, to, msg.as_string())
    smtpconnect.quit()
    logging.info('Email sent from ['%s'] to %s.' % (sender, to))

def run_backup():

    '''Main function.
       cursor - creates 'cursor' object from 'mysql_connect()' first;
       user, database - receives lists (users_list[] and database_list[]) from 'select_user_dbs()';
       bkptype - determines backup type (weekly, daily) from 'dir_bkptype()'.

       For each user looks for it's databases, creates directory,
       and if there is no backup ('archname') yet - calls 'mysql_dump()' function.'''

    cursor = mysql_connect(DBROOT, DBHOST, _DBROOTPW)
    user, database = select_user_dbs(cursor)
    bkptype = dir_bkptype(curday)

    curday = time.strftime('%a')

    for user, database in zip(user, database):

        if database not in EXCLUDE:

            backup_dir = back_dir_create(user, bkptype)

            if backup_dir:

                archname = (backup_dir + database + '.sql.bz2')

                if not os.path.isfile(archname):
                    mysql_dump(DBROOT, _DBROOTPW, database, archname)
                else:
                    logging.info('Backup %s already present, skip' % archname)

                else:
            logging.info('Database %s in exclude list, skip' % database)

    sendmail()

if __name__ == '__main__':
    starttime = time.strftime('%Y-%m-%d %H:%M:%S')
    logging.info('Backup started at: %s' % starttime)
    run_backup()
    finishtime = time.strftime('%Y-%m-%d %H:%M:%S')
    logging.info('Backup finished at: %s' % finishtime)
