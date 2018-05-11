# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations

"""
Esta migracion reemplaza a la migración South 0050_crea_tablas_gammu
"""


def generate_runsqls():
    pg = 'django.db.backends.postgresql_psycopg2'
    if settings.DATABASES['default']['ENGINE'] != pg:
        print("Ignorando migracion: BD no es postgresql")
        return []

    sql_statements = []

    # Crea tabla daemons
    sql = """
    CREATE TABLE daemons (
        "Start" text NOT NULL,
        "Info" text NOT NULL
    )
    """
    sql_statements.append(sql)

    # Crea tabla gammu
    sql = """
    CREATE TABLE gammu (
        "Version" smallint NOT NULL DEFAULT '0'
    )
    """
    sql_statements.append(sql)

    # Insert tabla gammu
    sql = """
    INSERT INTO gammu ("Version") VALUES (14)
    """
    sql_statements.append(sql)

    # Crea tabla inbox
    sql = """
    CREATE TABLE inbox (
        "UpdatedInDB" timestamp(0) WITHOUT time zone NOT NULL DEFAULT LOCALTIMESTAMP(0),
        "ReceivingDateTime" timestamp(0) WITHOUT time zone NOT NULL DEFAULT LOCALTIMESTAMP(0),
        "Text" text NOT NULL,
        "SenderNumber" varchar(20) NOT NULL DEFAULT '',
        "Coding" varchar(255) NOT NULL DEFAULT 'Default_No_Compression',
        "UDH" text NOT NULL,
        "SMSCNumber" varchar(20) NOT NULL DEFAULT '',
        "Class" integer NOT NULL DEFAULT '-1',
        "TextDecoded" text NOT NULL DEFAULT '',
        "ID" serial PRIMARY KEY,
        "RecipientID" text NOT NULL,
        "Processed" boolean NOT NULL DEFAULT 'false',
        CHECK ("Coding" IN
        ('Default_No_Compression','Unicode_No_Compression','8bit','Default_Compression','Unicode_Compression')) 
    )
    """
    sql_statements.append(sql)

    # Create trigger for table "inbox"
    sql = """
    CREATE TRIGGER update_timestamp BEFORE UPDATE ON inbox FOR EACH ROW EXECUTE PROCEDURE update_timestamp()
    """
    sql_statements.append(sql)

    # Crea tabla outbox
    sql = """
    CREATE TABLE outbox (
        "UpdatedInDB" timestamp(0) WITHOUT time zone NOT NULL DEFAULT LOCALTIMESTAMP(0),
        "InsertIntoDB" timestamp(0) WITHOUT time zone NOT NULL DEFAULT LOCALTIMESTAMP(0),
        "SendingDateTime" timestamp NOT NULL DEFAULT LOCALTIMESTAMP(0),
        "SendBefore" time NOT NULL DEFAULT '23:59:59',
        "SendAfter" time NOT NULL DEFAULT '00:00:00',
        "Text" text,
        "DestinationNumber" varchar(20) NOT NULL DEFAULT '',
        "Coding" varchar(255) NOT NULL DEFAULT 'Default_No_Compression',
        "UDH" text,
        "Class" integer DEFAULT '-1',
        "TextDecoded" text NOT NULL DEFAULT '',
        "ID" serial PRIMARY KEY,
        "MultiPart" boolean NOT NULL DEFAULT 'false',
        "RelativeValidity" integer DEFAULT '-1',
        "SenderID" varchar(255),
        "SendingTimeOut" timestamp(0) WITHOUT time zone NOT NULL DEFAULT LOCALTIMESTAMP(0),
        "DeliveryReport" varchar(10) DEFAULT 'default',
        "CreatorID" text NOT NULL,
        CHECK ("Coding" IN
        ('Default_No_Compression','Unicode_No_Compression','8bit','Default_Compression','Unicode_Compression')),
        CHECK ("DeliveryReport" IN ('default','yes','no'))
    )
    """
    sql_statements.append(sql)

    # Crea indices para la tabla outbox
    sql = """
    CREATE INDEX outbox_date ON outbox("SendingDateTime", "SendingTimeOut")
    """
    sql_statements.append(sql)

    sql = """
    CREATE INDEX outbox_sender ON outbox("SenderID")
    """
    sql_statements.append(sql)

    # Create trigger for table "outbox"
    sql = """
    CREATE TRIGGER update_timestamp BEFORE UPDATE ON outbox FOR EACH ROW EXECUTE PROCEDURE update_timestamp()
    """
    sql_statements.append(sql)

    # Crea tabla outbox_multipart
    sql = """
    CREATE TABLE outbox_multipart (
        "Text" text,
        "Coding" varchar(255) NOT NULL DEFAULT 'Default_No_Compression',
        "UDH" text,
        "Class" integer DEFAULT '-1',
        "TextDecoded" text DEFAULT NULL,
        "ID" serial,
        "SequencePosition" integer NOT NULL DEFAULT '1',
        PRIMARY KEY ("ID", "SequencePosition"),
        CHECK ("Coding" IN
        ('Default_No_Compression','Unicode_No_Compression','8bit','Default_Compression','Unicode_Compression'))
    )
    """
    sql_statements.append(sql)

    # Crea tabla pbk
    sql = """
    CREATE TABLE pbk (
        "ID" serial PRIMARY KEY,
        "GroupID" integer NOT NULL DEFAULT '-1',
        "Name" text NOT NULL,
        "Number" text NOT NULL
    )
    """
    sql_statements.append(sql)

    # Crea tabla pbk_groups
    sql = """
    CREATE TABLE pbk_groups (
        "Name" text NOT NULL,
        "ID" serial PRIMARY KEY
    )
    """
    sql_statements.append(sql)

    # Crea tabla phones
    sql = """
    CREATE TABLE phones (
        "ID" text NOT NULL,
        "UpdatedInDB" timestamp(0) WITHOUT time zone NOT NULL DEFAULT LOCALTIMESTAMP(0),
        "InsertIntoDB" timestamp(0) WITHOUT time zone NOT NULL DEFAULT LOCALTIMESTAMP(0),
        "TimeOut" timestamp(0) WITHOUT time zone NOT NULL DEFAULT LOCALTIMESTAMP(0),
        "Send" boolean NOT NULL DEFAULT 'no',
        "Receive" boolean NOT NULL DEFAULT 'no',
        "IMEI" varchar(35) PRIMARY KEY NOT NULL,
        "NetCode" varchar(10) DEFAULT 'ERROR',
        "NetName" varchar(35) DEFAULT 'ERROR',
        "Client" text NOT NULL,
        "Battery" integer NOT NULL DEFAULT -1,
        "Signal" integer NOT NULL DEFAULT -1,
        "Sent" integer NOT NULL DEFAULT 0,
        "Received" integer NOT NULL DEFAULT 0
    )
    """
    sql_statements.append(sql)

    # Create trigger for table "phones"
    sql = """
    CREATE TRIGGER update_timestamp BEFORE UPDATE ON phones FOR EACH ROW EXECUTE PROCEDURE update_timestamp()
    """
    sql_statements.append(sql)

    # Crea tabla sentitems
    sql = """
    CREATE TABLE sentitems (
        "UpdatedInDB" timestamp(0) WITHOUT time zone NOT NULL DEFAULT LOCALTIMESTAMP(0),
        "InsertIntoDB" timestamp(0) WITHOUT time zone NOT NULL DEFAULT LOCALTIMESTAMP(0),
        "SendingDateTime" timestamp(0) WITHOUT time zone NOT NULL DEFAULT LOCALTIMESTAMP(0),
        "DeliveryDateTime" timestamp(0) WITHOUT time zone NULL,
        "Text" text NOT NULL,
        "DestinationNumber" varchar(20) NOT NULL DEFAULT '',
        "Coding" varchar(255) NOT NULL DEFAULT 'Default_No_Compression',
        "UDH" text NOT NULL,
        "SMSCNumber" varchar(20) NOT NULL DEFAULT '',
        "Class" integer NOT NULL DEFAULT '-1',
        "TextDecoded" text NOT NULL DEFAULT '',
        "ID" serial,
        "SenderID" varchar(255) NOT NULL,
        "SequencePosition" integer NOT NULL DEFAULT '1',
        "Status" varchar(255) NOT NULL DEFAULT 'SendingOK',
        "StatusError" integer NOT NULL DEFAULT '-1',
        "TPMR" integer NOT NULL DEFAULT '-1',
        "RelativeValidity" integer NOT NULL DEFAULT '-1',
        "CreatorID" text NOT NULL,
        CHECK ("Status" IN
        ('SendingOK','SendingOKNoReport','SendingError','DeliveryOK','DeliveryFailed','DeliveryPending',
        'DeliveryUnknown','Error')),
        CHECK ("Coding" IN
        ('Default_No_Compression','Unicode_No_Compression','8bit','Default_Compression','Unicode_Compression')),
        PRIMARY KEY ("ID", "SequencePosition")
    )
    """
    sql_statements.append(sql)

    # Crea indices para la tabla sentitems
    sql = """
    CREATE INDEX sentitems_date ON sentitems("DeliveryDateTime")
    """
    sql_statements.append(sql)

    sql = """
    CREATE INDEX sentitems_tpmr ON sentitems("TPMR")
    """
    sql_statements.append(sql)

    sql = """
    CREATE INDEX sentitems_dest ON sentitems("DestinationNumber")
    """
    sql_statements.append(sql)

    sql = """
    CREATE INDEX sentitems_sender ON sentitems("SenderID")
    """
    sql_statements.append(sql)

    # Create trigger for table "sentitems"
    sql = """
    CREATE TRIGGER update_timestamp BEFORE UPDATE ON sentitems FOR EACH ROW EXECUTE PROCEDURE update_timestamp()
    """
    sql_statements.append(sql)

    return list(map(migrations.RunSQL, sql_statements))


class Migration(migrations.Migration):

    dependencies = [
        ('fts_web', '0004_auto_20180405_1122'),
    ]

    operations = generate_runsqls()
