#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Mark Theunissen <mark.theunissen@gmail.com>
# Sponsored by Four Kitchens http://fourkitchens.com.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#
# Added ability to use reource limits with attribute 'resource_limits'
#

from __future__ import absolute_import, division, print_function, with_statement
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: mysql_user_force
short_description: Adds or removes a user from a MySQL database
description:
   - Adds or removes a user from a MySQL database.
version_added: "0.6"
options:
  name:
    description:
      - Name of the user (role) to add or remove.
    type: str
    required: true
  password:
    description:
      - Set the user's password..
    type: str
  encrypted:
    description:
      - Indicate that the 'password' field is a `mysql_native_password` hash.
    type: bool
    default: no
    version_added: "2.0"
  host:
    description:
      - The 'host' part of the MySQL username.
    type: str
    default: localhost
  host_all:
    description:
      - Override the host option, making ansible apply changes to all hostnames for a given user.
      - This option cannot be used when creating users.
    type: bool
    default: no
    version_added: "2.1"
  priv:
    description:
      - "MySQL privileges string in the format: C(db.table:priv1,priv2)."
      - "Multiple privileges can be specified by separating each one using
        a forward slash: C(db.table:priv/db.table:priv)."
      - The format is based on MySQL C(GRANT) statement.
      - Database and table names can be quoted, MySQL-style.
      - If column privileges are used, the C(priv1,priv2) part must be
        exactly as returned by a C(SHOW GRANT) statement. If not followed,
        the module will always report changes. It includes grouping columns
        by permission (C(SELECT(col1,col2)) instead of C(SELECT(col1),SELECT(col2))).
    type: str
  append_privs:
    description:
      - Append the privileges defined by priv to the existing ones for this
        user instead of overwriting existing ones.
    type: bool
    default: no
    version_added: "1.4"
  sql_log_bin:
    description:
      - Whether binary logging should be enabled or disabled for the connection.
    type: bool
    default: yes
    version_added: "2.1"
  state:
    description:
      - Whether the user should exist.
      - When C(absent), removes the user.
    type: str
    choices: [ absent, present ]
    default: present
  check_implicit_admin:
    description:
      - Check if mysql allows login as root/nopassword before trying supplied credentials.
    type: bool
    default: no
    version_added: "1.3"
  update_password:
    description:
      - C(always) will update passwords if they differ.
      - C(on_create) will only set the password for newly created users.
    type: str
    choices: [ always, on_create ]
    default: always
    version_added: "2.0"
  resource_limits:
     description:
      - "MySQL resource limits in privileges statement string"
      - Available limits: 'MAX_QUERIES_PER_HOUR','MAX_UPDATES_PER_HOUR','MAX_CONNECTIONS_PER_HOUR','MAX_USER_CONNECTIONS','MAX_STATEMENT_TIME'
    type: dict
notes:
   - "MySQL server installs with default login_user of 'root' and no password. To secure this user
     as part of an idempotent playbook, you must create at least two tasks: the first must change the root user's password,
     without providing any login_user/login_password details. The second must drop a ~/.my.cnf file containing
     the new root credentials. Subsequent runs of the playbook will then succeed by reading the new credentials from
     the file."
   - Currently, there is only support for the `mysql_native_password` encrypted password hash module.

seealso:
- module: mysql_info
- name: MySQL access control and account management reference
  description: Complete reference of the MySQL access control and account management documentation.
  link: https://dev.mysql.com/doc/refman/8.0/en/access-control.html
- name: MySQL provided privileges reference
  description: Complete reference of the MySQL provided privileges documentation.
  link: https://dev.mysql.com/doc/refman/8.0/en/privileges-provided.html

author:
- Jonathan Mainguy (@Jmainguy)
- Benjamin Malynovytch (@bmalynovytch)
extends_documentation_fragment: mysql

Resource limits implemented by Vladimir Pereskokov (@gialloguitar)
'''

EXAMPLES = r'''
- name: Removes anonymous user account for localhost
  mysql_user_force:
    name: ''
    host: localhost
    state: absent

- name: Removes all anonymous user accounts
  mysql_user_force:
    name: ''
    host_all: yes
    state: absent

- name: Create database user with name 'bob' and password '12345' with all database privileges
  mysql_user_force:
    name: bob
    password: 12345
    priv: '*.*:ALL'
    state: present

- name: Create database user using hashed password with all database privileges
  mysql_user_force:
    name: bob
    password: '*EE0D72C1085C46C5278932678FBE2C6A782821B4'
    encrypted: yes
    priv: '*.*:ALL'
    state: present

- name: Create database user with password and all database privileges and 'WITH GRANT OPTION'
  mysql_user_force:
    name: bob
    password: 12345
    priv: '*.*:ALL,GRANT'
    state: present

# Note that REQUIRESSL is a special privilege that should only apply to *.* by itself.
- name: Modify user to require SSL connections.
  mysql_user_force:
    name: bob
    append_privs: yes
    priv: '*.*:REQUIRESSL'
    state: present

- name: Ensure no user named 'sally'@'localhost' exists, also passing in the auth credentials.
  mysql_user_force:
    login_user: root
    login_password: 123456
    name: sally
    state: absent

- name: Ensure no user named 'sally' exists at all
  mysql_user_force:
    name: sally
    host_all: yes
    state: absent

- name: Specify grants composed of more than one word
  mysql_user_force:
    name: replication
    password: 12345
    priv: "*.*:REPLICATION CLIENT"
    state: present

- name: Specify grants with one resource limit
  mysql_user_force:
    name: replication
    password: 12345
    priv: "*.*:SELECT"
    resource_limits:
       MAX_STATEMENT_TIME: 200
    state: present

- name: Revoke all privileges for user 'bob' and password '12345'
  mysql_user_force:
    name: bob
    password: 12345
    priv: "*.*:USAGE"
    state: present

# Example privileges string format
# mydb.*:INSERT,UPDATE/anotherdb.*:SELECT/yetanotherdb.*:ALL

- name: Example using login_unix_socket to connect to server
  mysql_user_force:
    name: root
    password: abc123
    login_unix_socket: /var/run/mysqld/mysqld.sock

- name: Example of skipping binary logging while adding user 'bob'
  mysql_user_force:
    name: bob
    password: 12345
    priv: "*.*:USAGE"
    state: present
    sql_log_bin: no

# Example .my.cnf file for setting the root password
# [client]
# user=root
# password=n<_665{vS43y
'''

import re
import string

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import SQLParseError
from ansible.module_utils.mysql import mysql_connect, mysql_driver, mysql_driver_fail_msg
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native


VALID_PRIVS = frozenset(('CREATE', 'DROP', 'GRANT', 'GRANT OPTION',
                         'LOCK TABLES', 'REFERENCES', 'EVENT', 'ALTER',
                         'DELETE', 'INDEX', 'INSERT', 'SELECT', 'UPDATE',
                         'CREATE TEMPORARY TABLES', 'TRIGGER', 'CREATE VIEW',
                         'SHOW VIEW', 'ALTER ROUTINE', 'CREATE ROUTINE',
                         'EXECUTE', 'FILE', 'CREATE TABLESPACE', 'CREATE USER',
                         'PROCESS', 'PROXY', 'RELOAD', 'REPLICATION CLIENT',
                         'REPLICATION SLAVE', 'SHOW DATABASES', 'SHUTDOWN',
                         'SUPER', 'ALL', 'ALL PRIVILEGES', 'USAGE', 'REQUIRESSL',
                         'CREATE ROLE', 'DROP ROLE', 'APPLICATION_PASSWORD_ADMIN',
                         'AUDIT_ADMIN', 'BACKUP_ADMIN', 'BINLOG_ADMIN',
                         'BINLOG_ENCRYPTION_ADMIN', 'CONNECTION_ADMIN',
                         'ENCRYPTION_KEY_ADMIN', 'FIREWALL_ADMIN', 'FIREWALL_USER',
                         'GROUP_REPLICATION_ADMIN', 'PERSIST_RO_VARIABLES_ADMIN',
                         'REPLICATION_SLAVE_ADMIN', 'RESOURCE_GROUP_ADMIN', 'RESOURCE_GROUP_USER',
                         'ROLE_ADMIN', 'SESSION_VARIABLES_ADMIN', 'SET_USER_ID',
                         'SYSTEM_VARIABLES_ADMIN', 'VERSION_TOKEN_ADMIN', 'XA_RECOVER_ADMIN',
                         'INVOKE LAMBDA',
                         'ALTER ROUTINE',
                         'BINLOG ADMIN',
                         'BINLOG MONITOR',
                         'BINLOG REPLAY',
                         'CONNECTION ADMIN',
                         'READ_ONLY ADMIN',
                         'REPLICATION MASTER ADMIN',
                         'REPLICATION SLAVE',
                         'REPLICATION SLAVE ADMIN',
                         'SET USER',
                         'SHOW_ROUTINE',))

VALID_RESOURCE_LIMITS = frozenset((
            'MAX_QUERIES_PER_HOUR',
            'MAX_UPDATES_PER_HOUR',
            'MAX_CONNECTIONS_PER_HOUR',
            'MAX_USER_CONNECTIONS',
            'MAX_STATEMENT_TIME',))

class InvalidPrivsError(Exception):
    pass

# ===========================================
# MySQL module specific support methods.
#


# User Authentication Management changed in MySQL 5.7 and MariaDB 10.2.0
def use_old_user_mgmt(cursor):
    cursor.execute("SELECT VERSION()")
    result = cursor.fetchone()
    version_str = result[0]
    version = version_str.split('.')

    if 'mariadb' in version_str.lower():
        # Prior to MariaDB 10.2
        if int(version[0]) * 1000 + int(version[1]) < 10002:
            return True
        else:
            return False
    else:
        # Prior to MySQL 5.7
        if int(version[0]) * 1000 + int(version[1]) < 5007:
            return True
        else:
            return False


def get_mode(cursor):
    cursor.execute('SELECT @@GLOBAL.sql_mode')
    result = cursor.fetchone()
    mode_str = result[0]
    if 'ANSI' in mode_str:
        mode = 'ANSI'
    else:
        mode = 'NOTANSI'
    return mode


def user_exists(cursor, user, host, host_all):
    if host_all:
        cursor.execute("SELECT count(*) FROM mysql.user WHERE user = %s", ([user]))
    else:
        cursor.execute("SELECT count(*) FROM mysql.user WHERE user = %s AND host = %s", (user, host))

    count = cursor.fetchone()
    return count[0] > 0


def user_add(cursor, user, host, host_all, password, encrypted, new_priv, check_mode, with_limits):
    # we cannot create users without a proper hostname
    if host_all:
        return False

    if check_mode:
        return True

    # Determine what user management method server uses
    old_user_mgmt = use_old_user_mgmt(cursor)

    if password and encrypted:
        #query = "CREATE USER {0}@{1} IDENTIFIED BY PASSWORD '{2}' {3}".format(user, host, password, with_limits)
        #cursor.execute(query)
        cursor.execute("CREATE USER %s@%s IDENTIFIED BY PASSWORD %s %s", (user, host, password))
    elif password and not encrypted:
        if old_user_mgmt:
            #query = "CREATE USER {0}@{1} IDENTIFIED BY '{2}' {3}".format(user, host, password, with_limits)
            #cursor.execute(query)
            cursor.execute("CREATE USER %s@%s IDENTIFIED BY %s %s", (user, host, password))
        else:
            cursor.execute("SELECT CONCAT('*', UCASE(SHA1(UNHEX(SHA1(%s)))))", (password,))
            encrypted_password = cursor.fetchone()[0]
            #query = "CREATE USER {0}@{1} IDENTIFIED WITH mysql_native_password AS '{2}' {3}".format(user, host, encrypted_password, with_limits)
            #cursor.execute(query)
            cursor.execute("CREATE USER %s@%s IDENTIFIED WITH mysql_native_password AS  %s", (user, host, encrypted_password))

    else:
        query = "CREATE USER {0}@{1} {2}".format(user, host, with_limits)
        cursor.execute(query)
        #cursor.execute("CREATE USER %s@%s %s", (user, host, with_limits))
    if new_priv is not None:
        for db_table, priv in iteritems(new_priv):
            privileges_grant(cursor, user, host, db_table, priv, with_limits)
    return True


def is_hash(password):
    ishash = False
    if len(password) == 41 and password[0] == '*':
        if frozenset(password[1:]).issubset(string.hexdigits):
            ishash = True
    return ishash


def user_mod(cursor, user, host, host_all, password, encrypted, new_priv, append_privs, module, with_limits):
    changed = False
    msg = "User unchanged"
    grant_option = False

    if host_all:
        hostnames = user_get_hostnames(cursor, [user])
    else:
        hostnames = [host]

    for host in hostnames:
        # Handle clear text and hashed passwords.
        if bool(password):
            # Determine what user management method server uses
            old_user_mgmt = use_old_user_mgmt(cursor)

            # Get a list of valid columns in mysql.user table to check if Password and/or authentication_string exist
            cursor.execute("""
                SELECT COLUMN_NAME FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = 'mysql' AND TABLE_NAME = 'user' AND COLUMN_NAME IN ('Password', 'authentication_string')
                ORDER BY COLUMN_NAME DESC LIMIT 1
            """)
            colA = cursor.fetchone()

            cursor.execute("""
                SELECT COLUMN_NAME FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = 'mysql' AND TABLE_NAME = 'user' AND COLUMN_NAME IN ('Password', 'authentication_string')
                ORDER BY COLUMN_NAME ASC  LIMIT 1
            """)
            colB = cursor.fetchone()

            # Select hash from either Password or authentication_string, depending which one exists and/or is filled
            cursor.execute("""
                SELECT COALESCE(
                        CASE WHEN %s = '' THEN NULL ELSE %s END,
                        CASE WHEN %s = '' THEN NULL ELSE %s END
                    )
                FROM mysql.user WHERE user = %%s AND host = %%s
                """ % (colA[0], colA[0], colB[0], colB[0]), (user, host))
            current_pass_hash = cursor.fetchone()[0]

            if encrypted:
                encrypted_password = password
                if not is_hash(encrypted_password):
                    module.fail_json(msg="encrypted was specified however it does not appear to be a valid hash expecting: *SHA1(SHA1(your_password))")
            else:
                if old_user_mgmt:
                    cursor.execute("SELECT PASSWORD(%s)", (password,))
                else:
                    cursor.execute("SELECT CONCAT('*', UCASE(SHA1(UNHEX(SHA1(%s)))))", (password,))
                encrypted_password = cursor.fetchone()[0]

            if current_pass_hash != encrypted_password:
                msg = "Password updated"
                if module.check_mode:
                    return (True, msg)
                if old_user_mgmt:
                    cursor.execute("SET PASSWORD FOR %s@%s = %s", (user, host, encrypted_password))
                    msg = "Password updated (old style)"
                else:
                    try:
                        cursor.execute("ALTER USER %s@%s IDENTIFIED WITH mysql_native_password AS %s", (user, host, encrypted_password))
                        msg = "Password updated (new style)"
                    except (mysql_driver.Error) as e:
                        # https://stackoverflow.com/questions/51600000/authentication-string-of-root-user-on-mysql
                        # Replacing empty root password with new authentication mechanisms fails with error 1396
                        if e.args[0] == 1396:
                            cursor.execute(
                                "UPDATE mysql.user SET plugin = %s, authentication_string = %s, Password = '' WHERE User = %s AND Host = %s",
                                ('mysql_native_password', encrypted_password, user, host)
                            )
                            cursor.execute("FLUSH PRIVILEGES")
                            msg = "Password forced update"
                        else:
                            raise e
                changed = True

        # Handle privileges
        if new_priv is not None:

            curr_priv = privileges_get(cursor, user, host)
            curr_limits = limits_get(cursor, user, host)

            for db_table, priv in iteritems(new_priv):
                if "GRANT" in priv:
                    with_limits = with_limits.replace('WITH', ' ')

            limits_changed = True if curr_limits.strip() != with_limits.strip() else False

            #module.fail_json(msg=curr_limits + '/' + with_limits + ' = ' + str(limits_changed) )

            if not with_limits:
                # Remove all limits explicitly if not specified
                with_limits = "WITH MAX_STATEMENT_TIME 0.000000 MAX_QUERIES_PER_HOUR 0 MAX_UPDATES_PER_HOUR 0 MAX_CONNECTIONS_PER_HOUR 0 MAX_USER_CONNECTIONS 0"

            # If the user has privileges on a db.table that doesn't appear at all in
            # the new specification, then revoke all privileges on it.
            for db_table, priv in iteritems(curr_priv):
                # If the user has the GRANT OPTION on a db.table, revoke it first.
                if "GRANT" in priv:
                    grant_option = True
                if db_table not in new_priv:
                    if user != "root" and "PROXY" not in priv and not append_privs:
                        msg = "Privileges updated"
                        if module.check_mode:
                            return (True, msg)
                        privileges_revoke(cursor, user, host, db_table, priv, grant_option)
                        changed = True

            # If the user doesn't currently have any privileges on a db.table, then
            # we can perform a straight grant operation.
            for db_table, priv in iteritems(new_priv):
                if db_table not in curr_priv or limits_changed:
                    msg = "New privileges granted"
                    if module.check_mode:
                        return (True, msg)
                    privileges_grant(cursor, user, host, db_table, priv, with_limits)
                    changed = True

            # If the db.table specification exists in both the user's current privileges
            # and in the new privileges, then we need to see if there's a difference.
            db_table_intersect = set(new_priv.keys()) & set(curr_priv.keys())
            for db_table in db_table_intersect:
                priv_diff = set(new_priv[db_table]) ^ set(curr_priv[db_table])
                if len(priv_diff) > 0 or limits_changed:
                    msg = "Privileges updated"
                    if module.check_mode:
                        return (True, msg)
                    if not append_privs:
                        privileges_revoke(cursor, user, host, db_table, curr_priv[db_table], grant_option)
                    privileges_grant(cursor, user, host, db_table, new_priv[db_table], with_limits)
                    changed = True

    return (changed, msg)


def user_delete(cursor, user, host, host_all, check_mode):
    if check_mode:
        return True

    if host_all:
        hostnames = user_get_hostnames(cursor, [user])

        for hostname in hostnames:
            cursor.execute("DROP USER %s@%s", (user, hostname))
    else:
        cursor.execute("DROP USER %s@%s", (user, host))

    return True


def user_get_hostnames(cursor, user):
    cursor.execute("SELECT Host FROM mysql.user WHERE user = %s", user)
    hostnames_raw = cursor.fetchall()
    hostnames = []

    for hostname_raw in hostnames_raw:
        hostnames.append(hostname_raw[0])

    return hostnames


def privileges_get(cursor, user, host):
    """ MySQL doesn't have a better method of getting privileges aside from the
    SHOW GRANTS query syntax, which requires us to then parse the returned string.
    Here's an example of the string that is returned from MySQL:

     GRANT USAGE ON *.* TO 'user'@'localhost' IDENTIFIED BY 'pass';

    This function makes the query and returns a dictionary containing the results.
    The dictionary format is the same as that returned by privileges_unpack() below.
    """
    output = {}
    cursor.execute("SHOW GRANTS FOR %s@%s", (user, host))
    grants = cursor.fetchall()

    def pick(x):
        if x == 'ALL PRIVILEGES':
            return 'ALL'
        else:
            return x

    for grant in grants:
        res = re.match("""GRANT (.+) ON (.+) TO (['`"]).*\\3@(['`"]).*\\4( IDENTIFIED BY PASSWORD (['`"]).+\\6)? ?(.*)""", grant[0])
        if res is None:
            raise InvalidPrivsError('unable to parse the MySQL grant string: %s' % grant[0])
        privileges = res.group(1).split(",")
        privileges = [pick(x.strip()) for x in privileges]
        if "WITH GRANT OPTION" in res.group(7):
            privileges.append('GRANT')
        if "REQUIRE SSL" in res.group(7):
            privileges.append('REQUIRESSL')
        db = res.group(2)
        output.setdefault(db, []).extend(privileges)
    return output


def limits_get(cursor, user, host):
    """ MySQL doesn't have a better method of getting privileges aside from the
    SHOW GRANTS query syntax, which requires us to then parse the returned string.
    Here's an example of the string that is returned from MySQL:

     GRANT USAGE ON *.* TO 'user'@'localhost' IDENTIFIED BY 'pass' WITH MAX_STATEMENT_TIME 10;

    """
    limits = ''
    cursor.execute("SHOW GRANTS FOR %s@%s", (user, host))
    grants = cursor.fetchall()

    for grant in grants:
        res = re.match("""GRANT (.+) ON (.+) TO (['`"]).*\\3@(['`"]).*\\4( IDENTIFIED BY PASSWORD (['`"]).+\\6)? ?(.*)""", grant[0])
        if res is None:
            raise InvalidPrivsError('unable to parse the MySQL grant string: %s' % grant[0])
        if "MAX_" in res.group(7):
            limits = res.group(7).replace('WITH GRANT OPTION', '')
    return limits

def privileges_unpack(priv, mode):
    """ Take a privileges string, typically passed as a parameter, and unserialize
    it into a dictionary, the same format as privileges_get() above. We have this
    custom format to avoid using YAML/JSON strings inside YAML playbooks. Example
    of a privileges string:

     mydb.*:INSERT,UPDATE/anotherdb.*:SELECT/yetanother.*:ALL

    The privilege USAGE stands for no privileges, so we add that in on *.* if it's
    not specified in the string, as MySQL will always provide this by default.
    """
    if mode == 'ANSI':
        quote = '"'
    else:
        quote = '`'
    output = {}
    privs = []
    for item in priv.strip().split('/'):
        pieces = item.strip().rsplit(':', 1)
        dbpriv = pieces[0].rsplit(".", 1)

        # Check for FUNCTION or PROCEDURE object types
        parts = dbpriv[0].split(" ", 1)
        object_type = ''
        if len(parts) > 1 and (parts[0] == 'FUNCTION' or parts[0] == 'PROCEDURE'):
            object_type = parts[0] + ' '
            dbpriv[0] = parts[1]

        # Do not escape if privilege is for database or table, i.e.
        # neither quote *. nor .*
        for i, side in enumerate(dbpriv):
            if side.strip('`') != '*':
                dbpriv[i] = '%s%s%s' % (quote, side.strip('`'), quote)
        pieces[0] = object_type + '.'.join(dbpriv)

        if '(' in pieces[1]:
            output[pieces[0]] = re.split(r',\s*(?=[^)]*(?:\(|$))', pieces[1].upper())
            for i in output[pieces[0]]:
                privs.append(re.sub(r'\s*\(.*\)', '', i))
        else:
            output[pieces[0]] = pieces[1].upper().split(',')
            privs = output[pieces[0]]
        new_privs = frozenset(privs)
        if not new_privs.issubset(VALID_PRIVS):
            raise InvalidPrivsError('Invalid privileges specified: %s' % new_privs.difference(VALID_PRIVS))

    if '*.*' not in output:
        output['*.*'] = ['USAGE']

    # if we are only specifying something like REQUIRESSL and/or GRANT (=WITH GRANT OPTION) in *.*
    # we still need to add USAGE as a privilege to avoid syntax errors
    if 'REQUIRESSL' in priv and not set(output['*.*']).difference(set(['GRANT', 'REQUIRESSL'])):
        output['*.*'].append('USAGE')

    return output


def privileges_revoke(cursor, user, host, db_table, priv, grant_option):
    # Escape '%' since mysql db.execute() uses a format string
    db_table = db_table.replace('%', '%%')
    if grant_option:
        query = ["REVOKE GRANT OPTION ON %s" % db_table]
        query.append("FROM %s@%s")
        query = ' '.join(query)
        cursor.execute(query, (user, host))
    priv_string = ",".join([p for p in priv if p not in ('GRANT', 'REQUIRESSL')])
    query = ["REVOKE %s ON %s" % (priv_string, db_table)]
    query.append("FROM %s@%s")
    query = ' '.join(query)
    cursor.execute(query, (user, host))


def privileges_grant(cursor, user, host, db_table, priv, with_limits):
    # Escape '%' since mysql db.execute uses a format string and the
    # specification of db and table often use a % (SQL wildcard)
    db_table = db_table.replace('%', '%%')
    priv_string = ",".join([p for p in priv if p not in ('GRANT', 'REQUIRESSL')])
    query = ["GRANT %s ON %s" % (priv_string, db_table)]
    query.append("TO %s@%s")
    if 'REQUIRESSL' in priv:
        query.append("REQUIRE SSL")
    if 'GRANT' in priv:
        query.append("WITH GRANT OPTION")
        with_limits = with_limits.replace('WITH', '')
    query = ' '.join(query) + ' ' + with_limits
    cursor.execute(query, (user, host))

# ===========================================
# Module execution.
#

def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(type='str'),
            login_password=dict(type='str', no_log=True),
            login_host=dict(type='str', default='localhost'),
            login_port=dict(type='int', default=3306),
            login_unix_socket=dict(type='str'),
            user=dict(type='str', required=True, aliases=['name']),
            password=dict(type='str', no_log=True),
            encrypted=dict(type='bool', default=False),
            host=dict(type='str', default='localhost'),
            host_all=dict(type="bool", default=False),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            priv=dict(type='str'),
            append_privs=dict(type='bool', default=False),
            check_implicit_admin=dict(type='bool', default=False),
            update_password=dict(type='str', default='always', choices=['always', 'on_create']),
            connect_timeout=dict(type='int', default=30),
            config_file=dict(type='path', default='~/.my.cnf'),
            sql_log_bin=dict(type='bool', default=True),
            client_cert=dict(type='path', aliases=['ssl_cert']),
            client_key=dict(type='path', aliases=['ssl_key']),
            ca_cert=dict(type='path', aliases=['ssl_ca']),
            resource_limits=dict(type='dict', default=dict() )
        ),
        supports_check_mode=True,
    )
    login_user = module.params["login_user"]
    login_password = module.params["login_password"]
    user = module.params["user"]
    password = module.params["password"]
    encrypted = module.boolean(module.params["encrypted"])
    host = module.params["host"].lower()
    host_all = module.params["host_all"]
    state = module.params["state"]
    priv = module.params["priv"]
    check_implicit_admin = module.params['check_implicit_admin']
    connect_timeout = module.params['connect_timeout']
    config_file = module.params['config_file']
    append_privs = module.boolean(module.params["append_privs"])
    update_password = module.params['update_password']
    ssl_cert = module.params["client_cert"]
    ssl_key = module.params["client_key"]
    ssl_ca = module.params["ca_cert"]
    db = ''
    sql_log_bin = module.params["sql_log_bin"]
    resource_limits = module.params["resource_limits"]

    if mysql_driver is None:
        module.fail_json(msg=mysql_driver_fail_msg)

    cursor = None
    try:
        if check_implicit_admin:
            try:
                cursor = mysql_connect(module, 'root', '', config_file, ssl_cert, ssl_key, ssl_ca, db,
                                       connect_timeout=connect_timeout)
            except Exception:
                pass

        if not cursor:
            cursor = mysql_connect(module, login_user, login_password, config_file, ssl_cert, ssl_key, ssl_ca, db,
                                   connect_timeout=connect_timeout)
    except Exception as e:
        module.fail_json(msg="unable to connect to database, check login_user and login_password are correct or %s has the credentials. "
                             "Exception message: %s" % (config_file, to_native(e)))

    if not sql_log_bin:
        cursor.execute("SET SQL_LOG_BIN=0;")

    if priv is not None:
        try:
            mode = get_mode(cursor)
        except Exception as e:
            module.fail_json(msg=to_native(e))
        try:
            priv = privileges_unpack(priv, mode)
        except Exception as e:
            module.fail_json(msg="invalid privileges string: %s" % to_native(e))

    with_limits = ''
    if resource_limits:
        limit = ''
        for key, value in resource_limits.items():
            if key in VALID_RESOURCE_LIMITS and isinstance(value, int):
                if key == 'MAX_STATEMENT_TIME':
                    value = str(value) + '.000000'
                limit += '{0} {1} '.format(key, str(value))
            else:
                module.fail_json(msg="invalid resource limits: {0} {1}".format(key, value))
                break
        with_limits = 'WITH {0}'.format(limit)

    if state == "present":
        if user_exists(cursor, user, host, host_all):
            try:
                if update_password == 'always':
                    changed, msg = user_mod(cursor, user, host, host_all, password, encrypted, priv, append_privs, module, with_limits)
                else:
                    changed, msg = user_mod(cursor, user, host, host_all, None, encrypted, priv, append_privs, module, with_limits)

            except (SQLParseError, InvalidPrivsError, mysql_driver.Error) as e:
                module.fail_json(msg=to_native(e))
        else:
            if host_all:
                module.fail_json(msg="host_all parameter cannot be used when adding a user")
            try:
                changed = user_add(cursor, user, host, host_all, password, encrypted, priv, module.check_mode, with_limits )
                if changed:
                    msg = "User added"

            except (SQLParseError, InvalidPrivsError, mysql_driver.Error) as e:
                module.fail_json(msg=to_native(e))
    elif state == "absent":
        if user_exists(cursor, user, host, host_all):
            changed = user_delete(cursor, user, host, host_all, module.check_mode)
            msg = "User deleted"
        else:
            changed = False
            msg = "User doesn't exist"
    module.exit_json(changed=changed, user=user, msg=msg)


if __name__ == '__main__':
    main()
