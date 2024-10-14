import mysql.connector
import pandas as pd
import datetime as dt

#Please Change these to your own mysql_detail before running the program
database_user="root"#Please remain the""
database_password="ABc@328022"#Please remain the""
adminID = "sslibrary"#Please remain the""
adminPIN = "123456"#Please remain the""

connection = None
current_date = dt.datetime.now()

# This function will only run if the program is activated first time
def connect_first_running():#no database in the mysql.connector.connect()
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user=database_user,
            password=database_password
        )
        if connection.is_connected():
            return connection
    except mysql.connector.Error as error:
        print("Error connectiong to the server:", error)
        return None
    
def connect(): 
    global connection
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='library_management',
            user=database_user,
            password=database_password
        )
        if connection.is_connected():
            return connection
    except mysql.connector.Error as error:
        print("Error connecting to the server:", error)
        return None

def creating_database():
    mydb = connect_first_running()
    mycursor = mydb.cursor()
    #Check whether the database was created
    mycursor.execute("SHOW DATABASES")
    databases = [db[0] for db in mycursor.fetchall()]
    if "library_management" not in databases:
        print("Database ~~~library_management~~~ created successfully.")
    #Creates database if it doesn't exist
    mycursor.execute("CREATE DATABASE IF NOT EXISTS library_management")

def creating_tables():
    mydb = connect()
    mycursor = mydb.cursor()
    #Check whether the PersonalInformation table was created
    mycursor.execute("SHOW TABLES")
    tables = [table[0] for table in mycursor.fetchall()]
    if "PersonalInformation" not in tables:
        print("Table ~~~PersonalInformation~~~ created successfully.")
    #Creates a table if it does not exist
    mycursor.execute("CREATE TABLE IF NOT EXISTS PersonalInformation (\
                      IC VARCHAR(225)  PRIMARY KEY,\
                      Name VARCHAR(225) NOT NULL,\
                      Email VARCHAR(225) NOT NULL,\
                      Contact VARCHAR(225) NOT NULL,\
                      Address VARCHAR(225) NOT NULL,\
                      Password VARCHAR(225) NOT NULL,\
                      Membership_Status ENUM('Premiere','Normal') NOT NULL DEFAULT 'Normal',\
                      Penalty FLOAT(5,2) NOT NULL DEFAULT '0')")

    #Check whether the Membership table was created
    if "Membership" not in tables:
        print("Table ~~~Membership~~~ created successfully.")
    #Creates a table if it does not exist
    mycursor.execute("CREATE TABLE IF NOT EXISTS Membership (\
                      IC VARCHAR(225)  PRIMARY KEY,\
                      Name VARCHAR(225) NOT NULL,\
                      Membership_Period VARCHAR(225) NOT NULL,\
                      Start_Membership_Date DATE NOT NULL,\
                      End_Membership_Date DATE NOT NULL)")

    #Check whether the BorrowedMember table was created
    if "BorrowedMember" not in tables:
        print("Table ~~~BorrowedMember~~~ created successfully.")
    #Creates a table if it does not exist
    mycursor.execute("CREATE TABLE IF NOT EXISTS BorrowedMember (\
                      IC VARCHAR(225) NOT NULL,\
                      Name VARCHAR(225) NOT NULL,\
                      ISBN VARCHAR(255), \
                      Book_Title VARCHAR(225) NOT NULL,\
                      Borrowed_Date DATE NOT NULL,\
                      Due_Date DATE NOT NULL,\
                      Return_Date DATE NULL,\
                      Penalty FLOAT(4,2) NOT NULL DEFAULT '0',\
                      Payment_Condition ENUM('Paid','Un-Paid') NOT NULL DEFAULT 'Un-Paid',\
                      Lost ENUM('Lost','Not_Lost') NOT NULL DEFAULT 'Not_Lost')")
    
    #Check whether the ReservedBook table was created
    if "ReservedBook" not in tables:
        print("Table ~~~ReservedBook~~~ created successfully.")
    #Creates a table if it does not exist
    mycursor.execute("CREATE TABLE IF NOT EXISTS ReservedBook (\
                      IC VARCHAR(225),\
                      ISBN VARCHAR(255),\
                      Reservation_Date DATE)")
    
    #Check whether the BookingRoom table was created
    if "BookingRoom" not in tables:
        print("Table ~~~BookingRoom~~~ created successfully.")
    #Creates a table if it does not exist
    mycursor.execute("CREATE TABLE IF NOT EXISTS BookingRoom (\
                      Date DATE NOT NULL,\
                      IC VARCHAR(225),\
                      Name VARCHAR(225) NOT NULL,\
                      Start_Time TIME NOT NULL,\
                      End_Time TIME NOT NULL,\
                      Room VARCHAR(225) NOT NULL,\
                      Check_In ENUM('Check-in','Not Check-in') NOT NULL DEFAULT 'Not Check-in')")

    if "Borrowings" not in tables:
        print("Table ~~~Borrowings~~~ created successfully.")
    #Creates a table if it does not exist
    mycursor.execute("CREATE TABLE IF NOT EXISTS Borrowings (\
                     MemberIC VARCHAR(255),\
                     ISBN VARCHAR(255) UNIQUE,\
                     BorrowDate DATE,\
                     ReturnDate DATE)")
    
    if "MemberBorrowings" not in tables:
        print("Table ~~~MemberBorrowings~~~ created successfully.")
    #Creates a table if it does not exist
    mycursor.execute("CREATE TABLE IF NOT EXISTS MemberBorrowings (\
                     MemberIC VARCHAR(255),\
                     ISBN VARCHAR(255) UNIQUE,\
                     Book_Title VARCHAR(225) NOT NULL,\
                     BorrowDate DATE,\
                     CollectionDate DATE NULL)")
    
def creating_tables_from_excel(excel_file):
    # Connect to MySQL database
    mydb = connect()
    mycursor = mydb.cursor()

    # Read data from the Excel file and convert it into MySQL tables
    try:
        xls = pd.ExcelFile(excel_file)
        for sheet_name in xls.sheet_names:
            # Check whether the table already exists
            mycursor.execute(f"SHOW TABLES LIKE '{sheet_name}'")
            table_exists = mycursor.fetchone()
            if not table_exists:
                # Create the table if it does not exist
                try:
                    df_sheet = xls.parse(sheet_name)
                    # Clean up column names
                    df_sheet.columns = [col.replace('-', '_') for col in df_sheet.columns]  # Replace '-' with '_'
                    df_sheet.columns = [col.replace(' ', '_') for col in df_sheet.columns]  # Replace spaces with '_'
                    # Fill NaN values with empty strings
                    df_sheet = df_sheet.fillna('')
                    # Define data types based on the actual data
                    data_types = {
                        "ISBN": "VARCHAR(255) NOT NULL UNIQUE",
                        "Book_Title": "VARCHAR(1000) NOT NULL",
                        "Book_Author": "VARCHAR(255) NOT NULL",
                        "Year_Of_Publication": "INT(4) NOT NULL",
                        "Publisher": "VARCHAR(255) NOT NULL",
                        "Price_RM": "FLOAT(5,2) NOT NULL",
                        "Genre": "VARCHAR(255) NOT NULL",
                        "Language": "VARCHAR(255) NOT NULL",
                        "Availability": "ENUM('Available','Not Available') NOT NULL DEFAULT 'Available'",
                        "Reserved" : "ENUM('Reserved','Non-Reserved') NOT NULL DEFAULT 'Non-Reserved'"
                    }
                    columns = ', '.join([f"`{col}` {data_types.get(col, 'VARCHAR(255)')}" for col in df_sheet.columns])
                    mycursor.execute(f"CREATE TABLE {sheet_name} ({columns})")
                    print(f"Table ~~~{sheet_name}~~~ created successfully.")
                    
                    # Insert data into the table
                    for _, row in df_sheet.iterrows():
                        values = tuple(row)
                        placeholders = ', '.join(['%s' for _ in range(len(row))])
                        query = f"INSERT INTO {sheet_name} VALUES ({placeholders})"
                        mycursor.execute(query, values)
                    print(f"Data inserted into table {sheet_name} successfully.")
                    
                except mysql.connector.Error as error:
                    print(f"Error creating table {sheet_name}: {error}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    mydb.commit()
    mycursor.close()
    mydb.close()

def closing_connection(connection, cursor):
    if connection.is_connected():
        cursor.close()
        connection.close()

def create_table_and_insert_data():
    global connection
    if not connection or not connection.is_connected():
        connection = connect()  
    cursor = connection.cursor()

    # Check if the Room table exists
    cursor.execute("SHOW TABLES LIKE 'Room'")
    result = cursor.fetchone()

    if not result:
        # Create the Room table if it doesn't exist
        cursor.execute("CREATE TABLE Room (\
                        Room VARCHAR(225) PRIMARY KEY,\
                        Availability ENUM('Available','Not Available') NOT NULL DEFAULT 'Available')")
        print("Table Room created successfully.")

        # Insert data into the Room table
        cursor.execute("INSERT INTO Room (Room, Availability) VALUES (%s, %s)", ("Room1", "Available"))
        cursor.execute("INSERT INTO Room (Room, Availability) VALUES (%s, %s)", ("Room2", "Available"))
        cursor.execute("INSERT INTO Room (Room, Availability) VALUES (%s, %s)", ("Room3", "Available"))
        print("Data inserted into Room table.")

    connection.commit()
    cursor.close()

