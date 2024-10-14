from Database_Bookworm import *
from PIL import Image
from tkinter import messagebox, ttk
import customtkinter as ctk
import mysql.connector
import tkinter as tk
import os
import time
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fpdf import FPDF
from collections import defaultdict
from tkcalendar import DateEntry

smtp_server = "MYDC2.suts.internal"
smtp_port = 587
library_email = "sslibrary0505@gmail.com"
email_password = "mybc ivwc dgna wrej"

#Make sure the frame will be destroyed during changing the frame
member_managementframe = None
catalog_managementframe = None
feesframe = None
borrowframe = None
returnframe = None
penaltyframe = None
membershippaymentframe = None
discussionpaymentframe = None
bookmanagerframe = None
borrowhistoryframe = None
personalinfoframe = None
reportframe = None
discussionroomframe = None
room_managementframe = None
trendingbookframe = None

# Create Borrow Frame (Admin Side)
def borrow():
    # Destroy Other frame
    admin_mainframe.destroy()
    global borrowframe
    if feesframe != None:
        feesframe.destroy()
    if member_managementframe != None:
        member_managementframe.destroy()
    if catalog_managementframe != None:
        catalog_managementframe.destroy()
    if borrowframe != None:
        borrowframe.destroy()
        clear_borrowings_table()
    if returnframe !=None:
        returnframe.destroy()
    if reportframe !=None:
        reportframe.destroy()
    if room_managementframe != None:
        room_managementframe.destroy()

     # Frame
    borrowframe = ctk.CTkFrame(master=admin_home, fg_color="#2b2b2b")
    borrowframe.grid(row=0, column=1, rowspan=50, columnspan=50, sticky="nw")
    borrow_list = ctk.CTkScrollableFrame(master=borrowframe, width=910, height=300, fg_color="#333333")
    borrow_list.grid(row=4, column=0, rowspan=3, columnspan=5, padx=30, pady=10)

    #Back To Admin Main Frame 
    def BackToHome():
        borrowframe.grid_forget()
        clear_borrowings_table()
        admin_menu()

    adminhome_btn = ctk.CTkButton(master=borrowframe, text="\U0001F3E0 Home", font=("Arial", 20, "underline"), height=30, width=50,fg_color="transparent", text_color="#808080", hover_color="#363838",command=BackToHome)
    adminhome_btn.place(relx=0.88, rely=0.04)

    title_label = ctk.CTkLabel(master=borrowframe, text="Borrow", font=("Arial", 24, "bold"))
    title_label.grid(row=0, column=0, padx=(40, 0), columnspan=6, pady=(30, 20), sticky="w")
    
    # Finalise All The Book in the cart into the borrowed table
    def AddIntoBorrowedlist():
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Borrowings")
        results = cursor.fetchall()

        for result in results:
            borrowedic = result[0]  
            borrowedISBN = result[1]  
            borrowdate = result[2]  
            duedate = result[3]

            cursor.execute("SELECT Book_Title FROM books WHERE ISBN = %s", (borrowedISBN,))
            bookresult = cursor.fetchone()
            borrowedbook = bookresult[0]

            cursor.execute("SELECT Name FROM personalinformation WHERE IC = %s", (borrowedic,))
            memberresult = cursor.fetchone()
            borrowedmember = memberresult[0]
       
            cursor.execute("INSERT INTO Borrowedmember (IC, Name, ISBN, Book_Title, Borrowed_Date, Due_Date) VALUES (%s, %s, %s, %s, %s, %s)",(borrowedic, borrowedmember, borrowedISBN, borrowedbook, borrowdate, duedate))

            cursor.execute("UPDATE books SET Availability='Not Available' WHERE ISBN = %s",(borrowedISBN,))

        messagebox.showinfo("Success", "The book is now being borrowed. ")
        connection.commit()
        cursor.close()
        clear_borrowings_table()
        borrow_table.delete(*borrow_table.get_children())

        icborrow_entry.delete(0,"end")
        currentborrowamount_display.configure(text="-")
        nameborrow_display.configure(text="-")
        add_btn.configure(state="disabled")
        delete_btn.configure(state="disabled")
        borrow_btn.configure(state="disabled")

    # Show Name Of the customers. And make sure the customer has registered the account for the program before starting borrowing the books
    def DisplayName():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        icborrow = icborrow_entry.get()
        cursor.execute("SELECT Name FROM PersonalInformation WHERE IC = %s", (icborrow,))
        result_name = cursor.fetchone()
        cursor.execute("SELECT * FROM MemberBorrowings WHERE MemberIC=%s",(icborrow,))
        pickup = cursor.fetchall()
        cursor.close()  # Close the cursor after use
        if result_name:
            name_text = result_name[0]
            nameborrow_display.configure(text=name_text)
            borrow_count = get_borrowed_count(icborrow)
            currentborrowamount_display.configure(text=str(borrow_count))
            add_btn.configure(state="normal")
            delete_btn.configure(state="normal")
            borrow_btn.configure(state="normal")
            if pickup:
                pickup_btn.configure(state="normal")
        else:
            messagebox.showerror("Info", "Not registered.")

    # Count the book in the waitinglist,which is the cart in the admin side before finalising the borrowed books, to avoid the multiple customers to borrow the same book at the same time
    def get_waitinglist_count(icborrow):
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM Borrowings WHERE MemberIC = %s", (icborrow,))
        borrow_count = cursor.fetchone()[0]
        cursor.close()
        return borrow_count
    
    # Count the book in the waitinglist,which is the cart in the member side before finalising the borrowed books, to avoid the multiple customers to borrow the same book at the same time
    def get_memberborrwinglist_count(icborrow):
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM MemberBorrowings WHERE MemberIC = %s", (icborrow,))
        borrow_count = cursor.fetchone()[0]
        cursor.close()
        return borrow_count
    
    # Count the book in the total books which are borrowed by the clients before finalising the borrowed books, to avoid the multiple customers to borrow the same book at the same time
    def get_borrowed_count(icborrow):
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM borrowedmember WHERE IC = %s AND Return_Date IS NULL AND Payment_Condition = 'Un-Paid'", (icborrow,))
        borrow_count = cursor.fetchone()[0]
        cursor.close()
        return borrow_count

    # Add the books into the waitinglist which is the cart in the admin side
    def Addintowaitinglist():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        icborrow = icborrow_entry.get()
        cursor = connection.cursor()
        cursor.execute("SELECT Membership_Status FROM PersonalInformation WHERE IC = %s", (icborrow,))
        membership_status = cursor.fetchone()
        cursor.close()

        num_borrowed_books = get_borrowed_count(icborrow)
        num_waitinglist_books = get_waitinglist_count(icborrow)
        num_memberborrowing_books=get_memberborrwinglist_count(icborrow)

        # Depend on the membership status to determine the amount of books which can be borrowed by the clients
        if membership_status:
            if membership_status[0] == "Normal":
                if (num_borrowed_books + num_waitinglist_books + num_memberborrowing_books) == 10:
                    messagebox.showinfo("Borrow Limit", "Borrow limit has been reached.")
                    return
            elif membership_status[0] == "Premiere":
                if (num_borrowed_books + num_waitinglist_books + num_memberborrowing_books) == 20:
                    messagebox.showinfo("Borrow Limit", "Borrow limit has been reached.")
                    return

        cursor = connection.cursor()
        borrowISBN = bookborrowedISBN_entry.get()
        cursor.execute("SELECT ISBN, Book_Title, Book_Author, Language, Availability FROM books WHERE ISBN = %s", (borrowISBN,))
        book_details = cursor.fetchone()
        cursor.execute("SELECT ISBN FROM MemberBorrowings WHERE ISBN=%s",(borrowISBN,))
        pickup_details = cursor.fetchone()
        cursor.close()  # Close the cursor after use

        # SubFunction of the addintowaitinglist(Read the books from the treeview and add into the waitinglist)
        def WaitingListAdded(borrowISBN):
            for row in borrow_table.get_children():
                if borrow_table.item(row, 'values')[0] == borrowISBN:
                    return True
            return False
        
        # Check the availability of the books. And determine the time when the books are borrowed.
        if book_details:
            if book_details[4]=="Available" and not WaitingListAdded(borrowISBN) and not pickup_details:
                borrow_table.insert("", "end", values=book_details)
                cursor = connection.cursor()
                borrow_date = dt.date.today()
                if membership_status[0] == "Normal":
                    return_date = borrow_date + dt.timedelta(days=13)
                elif membership_status[0] == "Premiere":
                    return_date = borrow_date + dt.timedelta(days=20)
                cursor.execute("INSERT INTO Borrowings (MemberIC, ISBN, BorrowDate, ReturnDate) VALUES (%s, %s, %s, %s)",
                (icborrow, borrowISBN, borrow_date, return_date))
                connection.commit()  # Commit the transaction
                cursor.close()  # Close the cursor after use
                delete_btn.configure(state="normal")
                borrow_btn.configure(state="normal")
            elif book_details[4]=="Not Available" or pickup_details:
                messagebox.showerror("Error", "The book has been borrowed.")
            elif WaitingListAdded(borrowISBN):
                messagebox.showerror("Error", "The book has been added.")
            bookborrowedISBN_entry.delete(0,"end")
        else:
            messagebox.showerror("Error", "The book does not exist")

    # SubFunction of the addintowaitinglist(Delete the books from the waitinglist)
    def DeleteWaitingListItem():
        selected_book = borrow_table.selection()  
        for item in selected_book:
            deleteisbn = borrow_table.item(item, 'values')[0]
            borrow_table.delete(item)
            cursor = connection.cursor()
            cursor.execute("DELETE FROM Borrowings WHERE ISBN = %s", (deleteisbn,))
            connection.commit()
            cursor.close()

    # SubFunction of the addintowaitinglist(Create the another frame to retrieve the books borrowed in the memberborrowings, which is the cart in the member side)
    def BorrowPickup():
        borrow_list.destroy()
        delete_btn.destroy()
        borrow_btn.destroy()
        pickup_listframe = ctk.CTkScrollableFrame(master=borrowframe, width=910, height=300, fg_color="#333333")
        pickup_listframe.grid(row=4, column=0, rowspan=3, columnspan=5, padx=30, pady=10)
        add_btn.configure(state="disabled")

        # SubFunction of the BorrowPickup(Delete the books from the memberborrowings,which is the cart in the member side)
        def DeletePickupListItem():
            selected_book = pickuplist.selection()
            for item in selected_book:
                deleteisbn = pickuplist.item(item, 'values')[0]
                pickuplist.delete(item)
                cursor = connection.cursor()
                cursor.execute("DELETE FROM MemberBorrowings WHERE ISBN = %s", (deleteisbn,))
                connection.commit()
                cursor.close()
        
        # SubFunction of the BorrowPickup(Retrieve the books from the cart in the member side)
        def PickupIntoBorrowedlist():
            borrow_date = dt.date.today()
            icborrow = icborrow_entry.get()
            cursor = connection.cursor()
            cursor.execute("SELECT Membership_Status FROM PersonalInformation WHERE IC = %s", (icborrow,))
            membership_status = cursor.fetchone()
            if membership_status[0] == "Normal":
                return_date = borrow_date + dt.timedelta(days=13)
            elif membership_status[0] == "Premiere":
                return_date = borrow_date + dt.timedelta(days=20)
            cursor.execute("SELECT MemberIC, ISBN, Book_Title FROM MemberBorrowings WHERE MemberIC=%s",(icborrow,))
            results = cursor.fetchall()

            for result in results:
                borrowedic = result[0]  
                borrowedISBN = result[1]
                borrowedbook  = result[2]

                cursor.execute("SELECT Name FROM personalinformation WHERE IC = %s", (borrowedic,))
                memberresult = cursor.fetchone()
                borrowedmember = memberresult[0]
                
                cursor.execute("INSERT INTO Borrowedmember (IC, Name, ISBN, Book_Title, Borrowed_Date, Due_Date) VALUES (%s, %s, %s, %s, %s, %s)",(borrowedic, borrowedmember, borrowedISBN, borrowedbook, borrow_date, return_date))
                cursor.execute("UPDATE books SET Availability='Not Available' WHERE ISBN = %s", (borrowedISBN,))
                cursor.execute("DELETE FROM MemberBorrowings WHERE MemberIC=%s",(borrowedic,))

            messagebox.showinfo("Success", "The book is now being borrowed.")
            connection.commit()
            cursor.close()

            pickuplist.delete(*pickuplist.get_children())
            icborrow_entry.delete(0,"end")
            currentborrowamount_display.configure(text="-")
            nameborrow_display.configure(text="-")
            pickup_btn.configure(state="disabled")
            deletepickup_btn.configure(state="disabled")
            borrowpickup_btn.configure(state="disabled")

        deletepickup_btn = ctk.CTkButton(master=borrowframe, text="Delete", font=("Arial", 18), corner_radius=100, height=35, command=DeletePickupListItem)
        deletepickup_btn.grid(row=7, column=3, pady=10, sticky="e")
        borrowpickup_btn = ctk.CTkButton(master=borrowframe, text="Borrow", font=("Arial", 18), corner_radius=100, height=35, command=PickupIntoBorrowedlist)
        borrowpickup_btn.grid(row=7, column=4, padx=40, pady=10, sticky="e")

        # SubFunction of the BorrowPickup(Display the books from the cart in the member side)
        def DisplayPickupList():
            icborrow = icborrow_entry.get()
            global connection
            try:
                if not connection or not connection.is_connected():
                    connection = connect()  # Reconnect if the connection is closed or lost
                cursor = connection.cursor()
                cursor.execute("SELECT ISBN, Book_Title, BorrowDate, CollectionDate FROM memberborrowings WHERE MemberIC=%s ORDER BY Book_Title ASC",(icborrow,))
                pickuplist.delete(*pickuplist.get_children())
                i=0
                for ro in cursor:
                    pickuplist.insert('',i,text="",values=(ro[0],ro[1],ro[2],ro[3]))
                cursor.close()
                connection.commit()
            except mysql.connector.Error as error:
                print(f"Error: Unable to load tasks from the database. {error}")
                exit()

        global pickuplist
        pickuplist = ttk.Treeview(pickup_listframe, show="headings", selectmode="browse", height=20)
        pickuplist['column']=("ISBN","Book_Title","Borrowed_Date","Collection_Date")

        pickuplist.column("#0",width=0,stretch=tk.NO)
        pickuplist.column("ISBN",anchor="w",width=152, minwidth=152)
        pickuplist.column("Book_Title",anchor="w",width=600, minwidth=600)
        pickuplist.column("Borrowed_Date",anchor="w",width=200, minwidth=200)
        pickuplist.column("Collection_Date",anchor="w",width=200, minwidth=200)

        # Headings
        pickuplist.heading("ISBN", text="ISBN", anchor="w")
        pickuplist.heading("Book_Title", text="Book Title", anchor="w")
        pickuplist.heading("Borrowed_Date", text="Borrow Date", anchor="w")
        pickuplist.heading("Collection_Date", text="Collection Date", anchor="w")
        DisplayPickupList()
        pickuplist.pack(fill="x")

    icborrow_label = ctk.CTkLabel(master=borrowframe, text="IC: ", font=("Arial", 18))
    icborrow_label.grid(row=1, column=0, padx=40, pady=10, sticky="w")
    icborrow_entry = ctk.CTkEntry(master=borrowframe, width=180)
    icborrow_entry.grid(row=1, column=1, pady=10, sticky="w")
    search_btn = ctk.CTkButton(master=borrowframe, text="Search", font=("Arial", 18), corner_radius=100, height=35,command=DisplayName)
    search_btn.grid(row=1, column=2, padx=30, pady=10, sticky="w")

    nameborrow_label = ctk.CTkLabel(master=borrowframe, text="Name: ", font=("Arial", 18))
    nameborrow_label.grid(row=2, column=0, padx=40, pady=10, sticky="w")
    nameborrow_display = ctk.CTkLabel(master=borrowframe, text="-", font=("Arial", 18))
    nameborrow_display.grid(row=2, column=1, pady=10, sticky="w")

    currentborrowamount = ctk.CTkLabel(master=borrowframe, text="Current borrowed amount:", font=("Arial", 18))
    currentborrowamount.grid(row=2, column=2, padx=(30,0), pady=10, sticky="w")
    currentborrowamount_display = ctk.CTkLabel(master=borrowframe, text="-", font=("Arial", 18))
    currentborrowamount_display.grid(row=2, column=3, pady=10, sticky="w")

    bookborrowedISBN_label = ctk.CTkLabel(master=borrowframe, text="ISBN: ", font=("Arial", 18))
    bookborrowedISBN_label.grid(row=3, column=0, padx=40, pady=10, sticky="w")
    bookborrowedISBN_entry= ctk.CTkEntry(master=borrowframe, width=180)
    bookborrowedISBN_entry.grid(row=3, column=1, pady=10, sticky="w")
    add_btn = ctk.CTkButton(master=borrowframe, text="Add", font=("Arial", 18), corner_radius=100, height=35,command=Addintowaitinglist)
    add_btn.grid(row=3, column=2, padx=30, pady=10, sticky="w")
    pickup_btn = ctk.CTkButton(master=borrowframe, text="Pickup", font=("Arial", 18), corner_radius=100, height=35,command=BorrowPickup)
    pickup_btn.grid(row=3, column=3, padx=30, pady=10, sticky="w")

    delete_btn = ctk.CTkButton(master=borrowframe, text="Delete", font=("Arial", 18), corner_radius=100, height=35, command=DeleteWaitingListItem)
    delete_btn.grid(row=7, column=3, pady=10, sticky="e")
    borrow_btn = ctk.CTkButton(master=borrowframe, text="Borrow", font=("Arial", 18), corner_radius=100, height=35, command=AddIntoBorrowedlist)
    borrow_btn.grid(row=7, column=4, padx=40, pady=10, sticky="e")

    add_btn.configure(state="disabled")
    delete_btn.configure(state="disabled")
    borrow_btn.configure(state="disabled")
    pickup_btn.configure(state="disabled")

    global borrow_table
    borrow_table = ttk.Treeview(borrow_list,height=20,show="headings",selectmode="browse")
    borrow_table['column']=("ISBN","Book_Title","Book_Author","Language","Availability")

    # Column
    borrow_table.column("#0",width=0,stretch=tk.NO) # Hide the default first column
    borrow_table.column("ISBN",anchor="w",width=130, minwidth=130)
    borrow_table.column("Book_Title",anchor="w",width=500, minwidth=500)
    borrow_table.column("Book_Author",anchor="w",width=160, minwidth=160)
    borrow_table.column("Language",anchor="w",width=120, minwidth=120)
    borrow_table.column("Availability",anchor="w",width=120, minwidth=120)

    # Headings
    borrow_table.heading("ISBN", text="ISBN", anchor="w")
    borrow_table.heading("Book_Title", text="Book Title", anchor="w")
    borrow_table.heading("Book_Author", text="Author", anchor="w")
    borrow_table.heading("Language", text="Language", anchor="w")
    borrow_table.heading("Availability", text="Availability", anchor="w")
    borrow_table.pack(fill="x")

# Delete the books from the cart in the admin side during changing of the frame
def clear_borrowings_table():
    global connection
    if not connection or not connection.is_connected():
        connection = connect()  
    cursor = connection.cursor()
    cursor.execute("DELETE FROM Borrowings")
    connection.commit()
    cursor.close()

# Create Return Frame(Admin Side)
def returnbook():
    # destroy frame during changing of the frame
    admin_mainframe.destroy()
    global returnframe
    if feesframe != None:
        feesframe.destroy()
    if member_managementframe != None:
        member_managementframe.destroy()
    if catalog_managementframe != None:
        catalog_managementframe.destroy()
    if borrowframe != None:
        borrowframe.destroy()
        clear_borrowings_table()
    if returnframe !=None:
        returnframe.destroy()
    if reportframe !=None:
        reportframe.destroy()
    if room_managementframe != None:
        room_managementframe.destroy()
        
    # Frame
    returnframe = ctk.CTkFrame(master=admin_home, fg_color="#2b2b2b")
    returnframe.grid(row=0, column=1, rowspan=50, columnspan=50, sticky="nw")

    # Back To Admin Main Frame 
    def BackToHome():
        returnframe.grid_forget()
        admin_menu()

    adminhome_btn = ctk.CTkButton(master=returnframe, text="\U0001F3E0 Home", font=("Arial", 20, "underline"), height=30, width=50,fg_color="transparent", text_color="#808080", hover_color="#363838",command=BackToHome)
    adminhome_btn.place(relx=0.88, rely=0.04)

    title_label = ctk.CTkLabel(master=returnframe, text="Return", font=("Arial", 24, "bold"))
    title_label.grid(row=0, column=0, padx=(40, 0), columnspan=6, pady=(30, 20), sticky="w")

    # Display the book return and details about penalty amount which is charged to the book
    def DisplayReturnInfo():
        global connection
        if not connection or not connection.is_connected():
            connection = connect() # Reconnect if the connection is closed or lost
        isbnreturn = bookreturnISBN_entry.get()
        cursor = connection.cursor()
        cursor.execute("SELECT Name, IC, Book_Title, Penalty, Borrowed_Date FROM borrowedmember WHERE ISBN = %s AND Return_Date IS NULL AND Lost = 'Not_Lost'", (isbnreturn,))
        result = cursor.fetchone()
        cursor.close()  # Close the cursor after use
        if result:
            name_text = result[0]
            IC_borrow = result[1]
            book_borrow = result[2] 
            penalty_borrow = "{:.2f}".format(float(result[3]))
            borrow_date = result[4]

            namereturn_display.configure(text=name_text)
            icreturn_display.configure(text=IC_borrow)
            bookreturn_display.configure(text=book_borrow)
            penaltydisplay.configure(text="RM " + penalty_borrow)
            borrowed_datedisplay.configure(text=borrow_date)
            return_btn.configure(state="normal")
            lost_btn.configure(state="normal")
        else:
            messagebox.showinfo("Info", "Not borrowed.")
    
    # Display the button. If the customers lost the book, they can press the book to inform the clients and the book will be charged respectively
    def Lost():
        lost = messagebox.askyesno("Lost","Are you sure to report it as lost?")
        if lost:
            global connection
            if not connection or not connection.is_connected():
                connection = connect()
            isbnreturn = bookreturnISBN_entry.get()
            cursor = connection.cursor()
            cursor.execute("SELECT `Price_(RM)` FROM books WHERE ISBN = %s", (isbnreturn,))
            price = cursor.fetchone()[0]
            cursor.execute("UPDATE borrowedmember SET Penalty=%s, Lost='Lost' WHERE ISBN = %s AND Return_Date IS NULL", (price, isbnreturn))
            connection.commit()
            cursor.close()
            messagebox.showinfo("Lost", "The book is now reported as lost.") 
        
        namereturn_display.configure(text="-")
        icreturn_display.configure(text="-")
        bookreturn_display.configure(text="-")
        penaltydisplay.configure(text="-")
        borrowed_datedisplay.configure(text="-")
        return_btn.configure(state="disabled")
        lost_btn.configure(state="disabled")
        bookreturnISBN_entry.delete(0,"end")

    # Return the book
    def ReturnButton():
        cursor = connection.cursor()
        return_date = dt.date.today()
        isbnreturn = bookreturnISBN_entry.get()
        cursor.execute("UPDATE borrowedmember SET Return_Date=%s WHERE ISBN = %s", (return_date, isbnreturn))
        cursor.execute("UPDATE books SET Availability='Available' WHERE ISBN = %s", (isbnreturn,))
        cursor.execute("SELECT IC FROM ReservedBook WHERE ISBN = %s ORDER BY Reservation_Date DESC", (isbnreturn,))
        reserve_members = cursor.fetchall()

        # Send the email to the customer who reserved the book
        def send_reservation_email(recipient_email, book_title):
            message = MIMEMultipart()
            message["From"] = library_email
            message["To"] = recipient_email
            message["Subject"] = "Your Reserved Book is Now Available"
            body = f"Hi {reservename},\n\nThe book, {book_title}, that you reserved is now available. Please come and collect it within 3 days.\n\nSincerely,\nSarawak State Library"
            message.attach(MIMEText(body, "plain"))
            try:
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(library_email, email_password)
                    server.sendmail(library_email, recipient_email, message.as_string())
                print("Email sent successfully.")
            except Exception as e:
                print("Error sending email:", str(e))

        # If there are reserved members, notify them and update book reservation status
        if reserve_members:
            cursor.execute("UPDATE books SET Reserved='Reserved' WHERE ISBN = %s", (isbnreturn,))
            for reserve_member in reserve_members:
                ic = reserve_member[0]

            cursor.execute("SELECT Book_Title FROM books WHERE ISBN = %s", (isbnreturn,))
            book_title = cursor.fetchone()[0]

            collection_date = return_date + dt.timedelta(days=3)
            cursor.execute("INSERT INTO MemberBorrowings (MemberIC,ISBN,Book_Title,BorrowDate,CollectionDate) VALUES (%s, %s, %s, %s, %s)", (ic, isbnreturn, book_title,return_date, collection_date))

            cursor.execute("SELECT Email, Name FROM personalinformation WHERE IC = %s", (ic,))
            result = cursor.fetchone()
            if result:
                recipient_email = result[0]
                reservename = result[1]

            send_reservation_email(recipient_email, book_title)
            cursor.execute("DELETE FROM ReservedBook WHERE ISBN = %s AND IC=%s", (isbnreturn,ic))

        connection.commit()
        cursor.close()

        namereturn_display.configure(text="-")
        icreturn_display.configure(text="-")
        bookreturn_display.configure(text="-")
        penaltydisplay.configure(text="-")
        borrowed_datedisplay.configure(text="-")
        return_btn.configure(state="disabled")
        lost_btn.configure(state="disabled")
        bookreturnISBN_entry.delete(0,"end")

    bookreturnISBN_label = ctk.CTkLabel(master=returnframe, text="ISBN: ", font=("Arial", 18))
    bookreturnISBN_label.grid(row=1, column=0, padx=40, pady=10, sticky="w")
    bookreturnISBN_entry= ctk.CTkEntry(master=returnframe, width=180)
    bookreturnISBN_entry.grid(row=1, column=1, pady=10, sticky="w")
    search_btn = ctk.CTkButton(master=returnframe, text="Search", font=("Arial", 18), corner_radius=100, width=125, height=35, command=DisplayReturnInfo)
    search_btn.grid(row=1, column=2, columnspan=4, padx=(30,0), pady=10, sticky="w")

    bookreturn_title = ctk.CTkLabel(master=returnframe, text="Book Title: ", font=("Arial", 18))
    bookreturn_title.grid(row=2, column=0, padx=40, pady=10, sticky="w")
    bookreturn_display = ctk.CTkLabel(master=returnframe, text="-", font=("Arial", 18))
    bookreturn_display.grid(row=2, column=1, columnspan=10, pady=10, sticky="w")

    namereturn = ctk.CTkLabel(master=returnframe, text="Name: ", font=("Arial", 18))
    namereturn.grid(row=3, column=0, padx=40, pady=10, sticky="w")
    namereturn_display = ctk.CTkLabel(master=returnframe, text="-", font=("Arial", 18))
    namereturn_display.grid(row=3, column=1, pady=10, sticky="w")

    icreturn_label = ctk.CTkLabel(master=returnframe, text="IC: ", font=("Arial", 18))
    icreturn_label.grid(row=3, column=2, pady=10, sticky="w")
    icreturn_display = ctk.CTkLabel(master=returnframe, text="-", font=("Arial", 18))
    icreturn_display.grid(row=3, column=3, columnspan=4, pady=10, sticky="w")
    
    borrowed_datelabel = ctk.CTkLabel(master=returnframe, text="Borrowed date: ", font=("Arial", 18))
    borrowed_datelabel.grid(row=4, column=0, padx=40, pady=10, sticky="w")
    borrowed_datedisplay = ctk.CTkLabel(master=returnframe, text="-", font=("Arial", 18))
    borrowed_datedisplay.grid(row=4, column=1, pady=10, sticky="w")

    penaltylabel = ctk.CTkLabel(master=returnframe, text="Penalty: ", font=("Arial", 18))
    penaltylabel.grid(row=4, column=2, pady=10, sticky="w")
    penaltydisplay = ctk.CTkLabel(master=returnframe, text="-", font=("Arial", 18))
    penaltydisplay.grid(row=4, column=3, pady=10, sticky="w")

    return_btn = ctk.CTkButton(master=returnframe, text="Return", font=("Arial", 18), corner_radius=100, width=135, height=35, command=ReturnButton)
    return_btn.grid(row=5, column=0, columnspan=20, padx=435, pady=20)
    return_btn.configure(state="disabled")

    lost_btn = ctk.CTkButton(master=returnframe, text="Report Lost", font=("Arial", 18,"underline"), width=135, height=35, corner_radius=100, command=Lost)
    lost_btn.grid(row=6, column=0, columnspan=20, padx=435, pady=(0,250))
    lost_btn.configure(state="disabled")

# Send the email to customer when the due date of the borrowed books is around the corner[more specific(this function will be executed when the due date is left 1 day and 3days)]
def ReminderEmail():
    def send_email(subject, recipient_email):
        message = MIMEMultipart()
        message["From"] = library_email
        message["To"] = recipient_email
        message["Subject"] = subject
        body = "Hello, \n\nPlease return the books within the specified time or there will be additional charges.\n\nSincerely,\nSarawak State Library"
        message.attach(MIMEText(body, "plain"))
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(library_email, email_password)
                server.sendmail(library_email, recipient_email, message.as_string())
            print("Email sent successfully.")
        except Exception as e:
            print("Error sending email:", str(e))
    global connection
    if not connection or not connection.is_connected():
        connection = connect() 
    cursor = connection.cursor()

    cursor.execute("SELECT IC FROM personalinformation")
    ics = cursor.fetchall()

    for ic_tuple in ics:
        ic = ic_tuple[0]  
        cursor.execute("SELECT b.Email FROM borrowedmember AS a INNER JOIN personalinformation AS b ON a.IC = b.IC WHERE a.IC=%s", (ic,))
        recipient_email_row = cursor.fetchone()
        if recipient_email_row:
            recipient_email = recipient_email_row[0]
            cursor.execute("SELECT Due_Date FROM borrowedmember WHERE IC = %s", (ic,))
            due_dates = cursor.fetchall()

            if due_dates:
                for due_date in due_dates:
                    todaydate = dt.datetime.now().date()
                    leftdate = due_date[0] - todaydate 

                    if leftdate.days == 3:
                        send_email("Reminder: Due Date Around the Corner", recipient_email)
                    elif leftdate.days == 1:
                        send_email("Alert: One More Day Before Due", recipient_email)
            else:
                print("No due dates found for IC:", ic)
        else:
            print("No email found for IC:", ic)
    cursor.close()

#Create the fee frame
def fees():
    #destroy frame during changing of the frame
    admin_mainframe.destroy()
    global feesframe
    if feesframe != None:
        feesframe.destroy()
    if member_managementframe != None:
        member_managementframe.destroy()
    if catalog_managementframe != None:
        catalog_managementframe.destroy()
    if borrowframe != None:
        borrowframe.destroy()
        clear_borrowings_table()
    if returnframe !=None:
        returnframe.destroy()
    if reportframe !=None:
        reportframe.destroy()
    if room_managementframe != None:
        room_managementframe.destroy()

    # Frame
    feesframe = ctk.CTkFrame(master=admin_home, fg_color="#2b2b2b")
    feesframe.grid(row=0, column=1, rowspan=50, columnspan=50, sticky="nw")
    feeprocessingframe = ctk.CTkFrame(master=feesframe, width=910, height=330, fg_color="#333333")
    feeprocessingframe.grid(row=4, column=0, rowspan=6, columnspan=5, padx=40, pady=(0,30))
    
    #Back To Admin Main Frame 
    def BackToHome():
        feesframe.grid_forget()
        admin_menu()

    adminhome_btn = ctk.CTkButton(master=feesframe, text="\U0001F3E0 Home", font=("Arial", 20, "underline"), height=30, width=50,fg_color="transparent", text_color="#808080", hover_color="#363838",command=BackToHome)
    adminhome_btn.place(relx=0.88, rely=0.04)

    title_label = ctk.CTkLabel(master=feesframe, text="Fee Management", font=("Arial", 24, "bold"))
    title_label.grid(row=0, column=0, padx=(40, 0), columnspan=6, pady=(30, 20), sticky="w")

    # Calculate the penalty charged for each book using the for loop concept
    def penaltycalculation():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()
        cursor = connection.cursor()
        cursor.execute("SELECT ISBN, Return_Date, Due_Date, Penalty, Lost FROM Borrowedmember WHERE IC = %s AND Payment_Condition='Un-Paid'", (penaltyic,))
        penalty_dates = cursor.fetchall()
        
        total_penalty_lost = 0
        total_penalty_late = 0

        for isbn, return_date, due_date, penalty, lost in penalty_dates:
            if lost == "Lost":
                cursor.execute("UPDATE BorrowedMember SET Penalty = %s WHERE ISBN=%s AND Payment_Condition='Un-Paid' AND Lost='Lost' AND IC = %s", (penalty, isbn, penaltyic,))
                total_penalty_lost += penalty
            else:
                if return_date is None:
                    return_date = dt.datetime.now()

                due_date = dt.datetime.combine(due_date, dt.datetime.min.time())
                return_date = dt.datetime.combine(return_date, dt.datetime.min.time())

                days_diff = (return_date - due_date).days

                if days_diff <= 0:
                    penalty = 0
                elif days_diff <= 3:
                    penalty = 0.1 * days_diff
                elif days_diff <= 6:
                    penalty = 0.1 * 3 + 0.2 * (days_diff - 3)
                elif days_diff <= 24:
                    penalty = 0.1 * 3 + 0.2 * 3 + 0.3 * (days_diff - 6)
                else:
                    penalty = 10

                cursor.execute("UPDATE BorrowedMember SET Penalty = %s WHERE ISBN=%s AND Payment_Condition='Un-Paid' AND IC = %s", (penalty, isbn, penaltyic,))
                total_penalty_late += penalty

        total_penalty = total_penalty_lost + total_penalty_late
        cursor.execute("UPDATE PersonalInformation SET Penalty = %s WHERE IC = %s", (total_penalty, penaltyic))
        connection.commit()
        cursor.close()

    #Display the total penalties charged
    def DisplayPenalty():
        global connection
        global name_text
        if not connection or not connection.is_connected():
            connection = connect()  
        cursor = connection.cursor()
        global penaltyic
        penaltyic = ic_entry.get()
        penaltycalculation()
        cursor.execute("SELECT Name, Penalty FROM PersonalInformation WHERE IC = %s", (penaltyic,))
        result = cursor.fetchone()
        connection.commit()
        cursor.close()  
        if result:
            name_text=result[0]
            penalty_amount = "{:.2f}".format(float(result[1]))

            membername_display.configure(text=name_text)
            feespenalty_label.configure(text="Penalty:\tRM " + penalty_amount)
            
            penaltypayment_btn.configure(state="normal") 
            discussionroompayment_btn.configure(state="normal")
            membershippayment_btn.configure(state="normal")
            return penalty_amount
        else:
            membername_display.configure(text="-")
            feespenalty_label.configure(text="Penalty:\t-")
            return None

    #Send an email when the members buying the membership first time
    def SendFirstBecomingMembershipEmail():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()
        cursor = connection.cursor()
        cursor.execute("SELECT Email FROM PersonalInformation WHERE IC=%s",(penaltyic,))
        recipient_email=cursor.fetchone()[0]
        cursor.execute("SELECT Name FROM PersonalInformation WHERE IC=%s",(penaltyic,))
        name=cursor.fetchone()[0]
        cursor.execute("SELECT End_Membership_Date FROM Membership WHERE IC=%s",(penaltyic,))
        end_date_membership=cursor.fetchone()[0]
        message = MIMEMultipart()
        message["From"] = library_email
        message["To"] = recipient_email
        message["Subject"] = "Welcome to Premiere Family"
        body = f"Hello {name}, \n\nCongratulations, you are now a Premiere Member of Sarawak State Library. You can now enjoy more benefits from our library. It will be valid until {end_date_membership}.\n\nFor any inquiries or assistance, please contact sslibrary0505@gmail.com.\nThank you.\n\nSincerely,\nSarawak State Library"
        message.attach(MIMEText(body, "plain"))
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(library_email, email_password)
                server.sendmail(library_email, recipient_email, message.as_string())
            print("Email sent successfully.")
        except Exception as e:
            print("Error sending email:", str(e))
        cursor.close()
        connection.commit()
    
    #Send an email when the members extending their membership period
    def ExtendMembershipEmail():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()
        cursor = connection.cursor()
        cursor.execute("SELECT Email FROM PersonalInformation WHERE IC=%s",(penaltyic,))
        recipient_email=cursor.fetchone()[0]
        cursor.execute("SELECT Name FROM PersonalInformation WHERE IC=%s",(penaltyic,))
        name=cursor.fetchone()[0]
        cursor.execute("SELECT End_Membership_Date FROM Membership WHERE IC=%s",(penaltyic,))
        end_date_membership=cursor.fetchone()[0]
        message = MIMEMultipart()
        message["From"] = library_email
        message["To"] = recipient_email
        message["Subject"] = "Premiere Subscription Renewal"
        body = f"Hello {name}, \n\nCongratulations, your membership has been renewed and will be valid until {end_date_membership}.\n\nFor any inquiries or assistance, please contact sslibrary0505@gmail.com.\nThank you.\n\nSincerely,\nSarawak State Library"
        message.attach(MIMEText(body, "plain"))
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(library_email, email_password)
                server.sendmail(library_email, recipient_email, message.as_string())
            print("Email sent successfully.")
        except Exception as e:
            print("Error sending email:", str(e))
        cursor.close()
        connection.commit()
    
    #Create the Membershippayment frame
    def MembershipPayment():
        global membershippaymentframe
        if penaltyframe != None:
            penaltyframe.destroy()
        if membershippaymentframe != None:
            membershippaymentframe.destroy()
        if discussionpaymentframe != None:
            discussionpaymentframe.destroy()

        membershippaymentframe = ctk.CTkFrame(master=feeprocessingframe, width=910, height=330,fg_color="#333333")
        membershippaymentframe.place(relx=0.5,rely=0.5,anchor="center")

        membershiptitle_label = ctk.CTkLabel(master=membershippaymentframe, text="Subscription Payment", font=("Arial", 24, "bold"))
        membershiptitle_label.grid(row=0, column=0, columnspan=3, pady=(30, 20), sticky="w")

        #Forget the membershippayment frame after making the payment
        def done():
            membershippaymentframe.place_forget()

        #Display the price of the membership
        def ViewmembershipPrice():
            try:
                duration_unit = float(duration_entry.get())
                pricemembership = duration_unit * 30
                pricemembership_label.configure(text=f"Price:\t\tRM {pricemembership:.2f}")
            except:
                messagebox.showerror("Error","Invalid Input!")

        #Make the payment for the membership
        def ProcessMembership():
            try:
                duration_unit = int(duration_entry.get())
                pricemembership = duration_unit * 30
                input_membership = float(inputamountmembership_entry.get())
                membershipbalance = input_membership - pricemembership
                membership_status="None"
                if duration_unit <= 0:
                    messagebox.showerror("Error", "Please input duration unit.")
                    return
                elif membershipbalance >= 0:
                    connection = connect()
                    cursor = connection.cursor()
                    penaltyic = ic_entry.get()
                    cursor.execute("SELECT IC, membership_period, end_membership_date FROM Membership WHERE IC = %s", (penaltyic,))
                    result = cursor.fetchone()

                    if result:
                        currentmembership_period = result[1]
                        membership_expiry = result[2]
                        extend_membership_period = dt.timedelta(30 * 6 * duration_unit )
                        updated_membership_period = int(currentmembership_period) + 30 * 6 * duration_unit 
                        updated_membership_expiry = membership_expiry + extend_membership_period
                        cursor.execute("UPDATE Membership SET Membership_Period=%s, End_Membership_Date=%s WHERE IC = %s", (updated_membership_period, updated_membership_expiry, penaltyic))
                        cursor.execute("UPDATE PersonalInformation SET Membership_Status='Premiere' WHERE IC = %s",(penaltyic,))
                        membership_status="existed"
                    else:
                        starting_membership_date = dt.date.today()
                        membershipperiod = dt.timedelta(days=30 * 6 * duration_unit)
                        ending_membership_date = starting_membership_date + membershipperiod

                        cursor.execute("INSERT INTO Membership(IC,Name,Membership_Period,Start_Membership_Date,End_Membership_Date)VALUES(%s,%s,%s,%s,%s)", (penaltyic, name_text, membershipperiod.days, starting_membership_date, ending_membership_date))
                        cursor.execute("UPDATE PersonalInformation SET Membership_Status='Premiere' WHERE IC = %s",(penaltyic,))
                        membership_status="new"

                    connection.commit()
                    cursor.close()
                    connection.close()
                    
                    paymentmembership_label.configure(text=f"Balance:\t\tRM {membershipbalance:.2f}")
                    done_btn.configure(state="normal")
                    
                else:
                    paymentmembership_label.configure(text=f"Balance:\t\tRM {membershipbalance:.2f}")
                    messagebox.showerror("Error", "Insufficient payment.")
                    done_btn.configure(state="disabled")
                
                if membership_status=="new":
                    SendFirstBecomingMembershipEmail()
                elif membership_status=="existed":
                    ExtendMembershipEmail()
                else:
                    print()
            except:
                messagebox.showerror("Error","Invalid Input!")
        #Delete the membership automatically when it is expired
        def deletemembership():
            today = dt.datetime.now()
            global connection
            if not connection or not connection.is_connected():
                connection = connect()
            cursor = connection.cursor()
            cursor.execute("SELECT End_Membership_Date FROM membership")
            end_membership_dates = cursor.fetchall()
            for end_date in end_membership_dates:
                end_date_datetime = dt.datetime.combine(end_date[0], dt.time())
                if today >= end_date_datetime:
                    cursor.execute("UPDATE personalinformation SET Membership_Status='Normal' WHERE IC=%s", (penaltyic,))
                    cursor.execute("DELETE FROM membership WHERE End_Membership_Date = %s", (end_date[0],))
            cursor.close()
            connection.commit()

        duration_label = ctk.CTkLabel(master=membershippaymentframe, text="Duration unit (6 mths per unit): ", font=("Arial", 18))
        duration_label.grid(row=1, column=0, sticky="w")
        duration_entry= ctk.CTkEntry(master=membershippaymentframe,width=80)
        duration_entry.grid(row=1, column=1, padx=10, sticky="w")
        viewmembershipprice_btn = ctk.CTkButton(master=membershippaymentframe, text="View Price", font=("Arial", 18),corner_radius=100, height=30,command=ViewmembershipPrice)
        viewmembershipprice_btn.grid(row=1, column=2, padx=10, sticky="w")

        pricemembership_label = ctk.CTkLabel(master=membershippaymentframe, text="Price:\t\tRM 0.00", font=("Arial", 18))
        pricemembership_label.grid(row=2, column=0, columnspan=2, pady=10, sticky="w")
 
        inputamountmembership_label = ctk.CTkLabel(master=membershippaymentframe, text="Amount paid:\tRM", font=("Arial", 18))
        inputamountmembership_label.grid(row=3, column=0, sticky="w")
        inputamountmembership_entry = ctk.CTkEntry(master=membershippaymentframe, width=80)
        inputamountmembership_entry.grid(row=3, column=1, sticky="w")
        processmembership_btn = ctk.CTkButton(master=membershippaymentframe, text="Process", font=("Arial", 18),corner_radius=100, height=30, command=ProcessMembership)
        processmembership_btn.grid(row=3, column=2, padx=10, sticky="w")

        paymentmembership_label = ctk.CTkLabel(master=membershippaymentframe, text="Balance:\t\tRM 0.00", font=("Arial", 18))
        paymentmembership_label.grid(row=4, column=0, columnspan=2, pady=(10,60), sticky="w")

        done_btn = ctk.CTkButton(master=membershippaymentframe, text="Done", font=("Arial", 18), corner_radius=100, height=30, command=done)
        done_btn.place(relx=0.5, rely=0.9, anchor="center")
        done_btn.configure(state="disabled")
        deletemembership()

    #Create the DiscussionRoomPayment frame
    def DiscussionRoomPayment():
        global discussionpaymentframe
        if penaltyframe != None:
            penaltyframe.destroy()
        if membershippaymentframe != None:
            membershippaymentframe.destroy()
        if discussionpaymentframe != None:
            discussionpaymentframe.destroy()

        discussionpaymentframe = ctk.CTkFrame(master=feeprocessingframe, width=910, height=330,fg_color="#333333")
        discussionpaymentframe.place(relx=0.5,rely=0.5,anchor="center")

        discussiontitle_label = ctk.CTkLabel(master=discussionpaymentframe, text="Discussion Room Payment", font=("Arial", 24, "bold"))
        discussiontitle_label.grid(row=0, column=0, columnspan=3, pady=(30, 20), sticky="w")

        #Send the email as the receipt to customers
        def BookingReceipt():
            input_bookingamount = float(inputamountbooking_entry.get())
            bookingbalance = input_bookingamount - bookingprice
            global connection
            if not connection or not connection.is_connected():
                connection = connect()
            cursor = connection.cursor()
            cursor.execute("SELECT Email FROM PersonalInformation WHERE IC=%s",(penaltyic,))
            recipient_email=cursor.fetchone()[0]
            cursor.execute("SELECT Name FROM PersonalInformation WHERE IC=%s",(penaltyic,))
            name=cursor.fetchone()[0]
            message = MIMEMultipart()
            message["From"] = library_email
            message["To"] = recipient_email
            message["Subject"] = "Discussion Room Receipt"
            body = f"Hello {name}, \n\nThank you for choosing the discussion room in Sarawak State Library. This is your receipt prior to your booking payment.\n\nAmount:\t\tRM{"{:.2f}".format(float(bookingprice))}\nPayment:\tRM{"{:.2f}".format(float(input_bookingamount))}\nBalance:\t RM{"{:.2f}".format(float(bookingbalance))}\n\nFor any inquiries or assistance, please contact sslibrary0505@gmail.com.\nThank you.\n\nSincerely,\nSarawak State Library"
            message.attach(MIMEText(body, "plain"))
            try:
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(library_email, email_password)
                    server.sendmail(library_email, recipient_email, message.as_string())
                print("Email sent successfully.")
            except Exception as e:
                print("Error sending email:", str(e))

        #Forget the frame after paying the money
        def checkin():
            BookingReceipt()
            discussionpaymentframe.place_forget()
        
        #Display the price of discussion room booked
        def ViewBookingPrice():
            start_time = dt.datetime.strptime(booking_result.get().split(' ')[0], "%H:%M:%S")
            end_time = dt.datetime.strptime(booking_result.get().split(' ')[2], "%H:%M:%S")
            room = booking_result.get().split(' ')[4]
            time_range = end_time - start_time
            hours = time_range.seconds // 3600
            if room == "Room1" or room == "Room2":
                roomprice = 5
            else:
                roomprice = 10
            global bookingprice
            bookingprice = hours * roomprice
            pricebooking_label.configure(text=f"Price:\t\tRM{bookingprice:.2f}") 

        #Making the payment for the room booked
        def ProcessBooking():
            current_date = dt.datetime.now().strftime('%Y-%m-%d')
            start_time = dt.datetime.strptime(booking_result.get().split(' ')[0], "%H:%M:%S")
            end_time = dt.datetime.strptime(booking_result.get().split(' ')[2], "%H:%M:%S")
            room = booking_result.get().split(' ')[4]
            try:
                input_bookingamount = float(inputamountbooking_entry.get())
                bookingbalance = input_bookingamount - bookingprice
                if bookingbalance >=0:
                    global connection
                    if not connection or not connection.is_connected():
                        connection = connect()  
                    cursor = connection.cursor()
                    cursor.execute("UPDATE BookingRoom SET Check_In = 'Check-in' WHERE IC=%s AND Date=%s AND Start_Time=%s AND End_Time=%s AND Room=%s", (penaltyic,current_date,start_time,end_time,room))
                    connection.commit()
                    cursor.close()

                    paymentbooking_label.configure(text=f"Balance:\t\tRM{bookingbalance:.2f}")
                    done_btn.configure(state="normal")
                else:
                    paymentbooking_label.configure(text=f"Balance:\t\tRM {bookingbalance:.2f}") 
                    messagebox.showerror("Discussion Room","Insufficient payment.") 
                    done_btn.configure(state="disabled")
            except:
                messagebox.showerror("Error","Invalid Input!")

        #Display the room and the time booked by the customers
        def GetTdyBooking():
            current_date = dt.datetime.now().strftime('%Y-%m-%d')
            current_time = time.strftime("%H:%M:%S")
            global connection
            if not connection or not connection.is_connected():
                connection = connect()
            cursor = connection.cursor()
            cursor.execute("SELECT Start_Time, End_Time, Room FROM bookingroom WHERE Date=%s AND IC=%s AND Check_In='Not Check-in' AND DATE_ADD(Start_Time, INTERVAL 5 MINUTE) > %s ORDER BY Start_Time ASC",(current_date,penaltyic,current_time))
            tdy_booking = cursor.fetchall()
            formatted_booking = [f"{start_time} - {end_time}  {room}" for start_time, end_time, room in tdy_booking]
            cursor.close()
            return formatted_booking
            
        formatted_booking = GetTdyBooking()
        if formatted_booking:
            booking_result = ctk.StringVar()
            booking_result.set(formatted_booking[0])

            room_booking = ctk.CTkOptionMenu(master=discussionpaymentframe, values=formatted_booking, variable=booking_result, width=250, height=30, font=("Arial", 16), fg_color="#363838")
            room_booking.grid(row=1, column=1, columnspan=2, padx=(50,10), sticky="w")
        else:
            room_booking = ctk.CTkLabel(master=discussionpaymentframe, text="-", font=("Arial", 18))
            room_booking.grid(row=1, column=1, columnspan=2, padx=10, sticky="w")
        
        room_booking_label = ctk.CTkLabel(master=discussionpaymentframe, text="Bookings: ", font=("Arial", 18))
        room_booking_label.grid(row=1, column=0, sticky="w")
        viewbookingprice_btn = ctk.CTkButton(master=discussionpaymentframe, text="View Price", font=("Arial", 18),corner_radius=100, height=30, command=ViewBookingPrice)
        viewbookingprice_btn.grid(row=1, column=3, padx=10, sticky="w")

        pricebooking_label = ctk.CTkLabel(master=discussionpaymentframe, text="Price:\t\t-", font=("Arial", 18))
        pricebooking_label.grid(row=2, column=0, columnspan=2, pady=10, sticky="w")

        inputbookingprice_label = ctk.CTkLabel(master=discussionpaymentframe, text="Amount paid:\tRM ", font=("Arial", 18))
        inputbookingprice_label.grid(row=3, column=0, columnspan=2, sticky="w")
        inputamountbooking_entry = ctk.CTkEntry(master=discussionpaymentframe, width=80)
        inputamountbooking_entry.grid(row=3, column=2, sticky="w")
        processbooking_btn = ctk.CTkButton(master=discussionpaymentframe, text="Process", font=("Arial", 18),corner_radius=100, height=30, command=ProcessBooking)
        processbooking_btn.grid(row=3, column=3, padx=10, sticky="w")

        paymentbooking_label = ctk.CTkLabel(master=discussionpaymentframe, text="Balance:\t\tRM 0.00", font=("Arial", 18))
        paymentbooking_label.grid(row=4, column=0, columnspan=2, pady=(10,60), sticky="w")

        done_btn = ctk.CTkButton(master=discussionpaymentframe, text="Check In", font=("Arial", 18),corner_radius=100, height=30, command=checkin)
        done_btn.place(relx=0.5,rely=0.9,anchor="center")
        done_btn.configure(state="disabled")

    #Create Penaltypayment frame
    def PenaltyPayment():
        global penaltyframe
        if penaltyframe != None:
            penaltyframe.destroy()
        if membershippaymentframe != None:
            membershippaymentframe.destroy()
        if discussionpaymentframe != None:
            discussionpaymentframe.destroy()

        penaltyframe = ctk.CTkFrame(master=feeprocessingframe, width=910, height=330, fg_color="#333333")
        penaltyframe.place(relx=0.5,rely=0.5,anchor="center")

        penaltytitle_label = ctk.CTkLabel(master=penaltyframe, text="Penalty Payment", font=("Arial", 24, "bold"))
        penaltytitle_label.grid(row=0, column=0, columnspan=3, pady=(30, 20), sticky="w")

        penalty_amount=DisplayPenalty()

        #Send the email to the customers after making the payment for penalties
        def PenaltyPaymentEmail():
            input_amount = float(inputamount_entry.get())
            balance = input_amount - float(penalty_amount)
            global connection
            if not connection or not connection.is_connected():
                connection = connect()
            cursor = connection.cursor()
            cursor.execute("SELECT Email FROM PersonalInformation WHERE IC=%s",(penaltyic,))
            recipient_email=cursor.fetchone()[0]
            cursor.execute("SELECT Name FROM PersonalInformation WHERE IC=%s",(penaltyic,))
            name=cursor.fetchone()[0]
            message = MIMEMultipart()
            message["From"] = library_email
            message["To"] = recipient_email
            message["Subject"] = "Penalty Payment Receipt"
            body = f"Hello {name}, \n\nThank you for clearing your penalties. This is your receipt prior to your penalty payment.\n\nPenalties:\t RM{"{:.2f}".format(float(penalty_amount))}\nPayment:\tRM{"{:.2f}".format(float(input_amount))}\nBalance:\t RM{"{:.2f}".format(float(balance))}\n\nFor any inquiries or assistance, please contact sslibrary0505@gmail.com.\nThank you.\n\nSincerely,\nSarawak State Library"
            message.attach(MIMEText(body, "plain"))
            try:
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(library_email, email_password)
                    server.sendmail(library_email, recipient_email, message.as_string())
                print("Email sent successfully.")
            except Exception as e:
                print("Error sending email:", str(e))

        #After making the payment for penalties, the penalyframe will be forgot
        def done():
            PenaltyPaymentEmail()
            penaltyframe.place_forget()

        #Making the payment for the penalties
        def process_penalty():
            try:
                input_amount = float(inputamount_entry.get())
                balance = input_amount - float(penalty_amount)
                
                if balance >= 0:
                    global connection, payment_label
                    if not connection or not connection.is_connected():
                        connection = connect() 
                    cursor = connection.cursor()
                    cursor.execute("UPDATE PersonalInformation SET Penalty=0 WHERE IC = %s", (penaltyic,))
                    cursor.execute("UPDATE BorrowedMember SET Payment_Condition='Paid' WHERE IC = %s AND (Return_Date IS NOT NULL OR (Lost='Lost' AND Payment_Condition='Un-Paid'))", (penaltyic,))
                    connection.commit()
                    cursor.close()

                    payment_label.configure(text=f"Balance:\t\tRM {balance:.2f}")
                    DisplayPenalty()
                    done_btn.configure(state="normal")

                else:
                    payment_label.configure(text=f"Balance:\t\tRM {balance:.2f}") 
                    messagebox.showerror("Penalty","Insufficient payment.") 
                    done_btn.configure(state="disabled")
                
            except:
                messagebox.showerror("Error","Invalid Input!")

        feespenalty_label = ctk.CTkLabel(master=penaltyframe, text=("Penalty:\t\tRM "+str(penalty_amount)), font=("Arial", 18))
        feespenalty_label.grid(row=1, column=0, columnspan=2, sticky="w")

        inputamount_label = ctk.CTkLabel(master=penaltyframe, text="Amount paid:\tRM", font=("Arial", 18))
        inputamount_label.grid(row=2, column=0, pady=10, sticky="w")
        inputamount_entry = ctk.CTkEntry(master=penaltyframe, width=80)
        inputamount_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        process_btn = ctk.CTkButton(master=penaltyframe, text="Process", font=("Arial", 18),corner_radius=100, height=30, command=process_penalty)
        process_btn.grid(row=2, column=2, padx=10, pady=10, sticky="w")
        
        global payment_label
        payment_label = ctk.CTkLabel(master=penaltyframe, text="Balance:\t\tRM 0.00", font=("Arial", 18))
        payment_label.grid(row=3, column=0, columnspan=2, pady=(0,80), sticky="w")

        done_btn = ctk.CTkButton(master=penaltyframe, text="Done", font=("Arial", 18),corner_radius=100, height=30, command=done)
        done_btn.place(relx=0.5,rely=0.9,anchor="center")
        done_btn.configure(state="disabled")

    ic_label = ctk.CTkLabel(master=feesframe, text="IC: ", font=("Arial", 18))
    ic_label.grid(row=1, column=0, padx=40, pady=10, sticky="w")
    ic_entry = ctk.CTkEntry(master=feesframe, width=180)
    ic_entry.grid(row=1, column=1, pady=10, sticky="w")

    search_btn = ctk.CTkButton(master=feesframe, text="Search", font=("Arial", 18), corner_radius=100, height=35,command=DisplayPenalty)
    search_btn.grid(row=1, column=2, pady=10, sticky="w")

    membername_label = ctk.CTkLabel(master=feesframe, text="Name: ", font=("Arial", 18))
    membername_label.grid(row=2, column=0, padx=40, pady=10, sticky="w")
    membername_display = ctk.CTkLabel(master=feesframe, text="-", font=("Arial", 18))
    membername_display.grid(row=2, column=1, pady=10, sticky="w")

    feespenalty_label = ctk.CTkLabel(master=feesframe, text="Penalty:\t-", font=("Arial", 18))
    feespenalty_label.grid(row=2, column=2, columnspan=2, pady=10, sticky="w")

    # fee selection button
    penaltypayment_btn = ctk.CTkButton(master=feesframe, text="Penalty Payment", font=("Arial", 18),corner_radius=100, width=250, height=35, command=PenaltyPayment)
    penaltypayment_btn.grid(row=1, column=4, padx=40, pady=10, sticky="e")
    discussionroompayment_btn = ctk.CTkButton(master=feesframe, text="Discussion Room Payment", font=("Arial", 18),corner_radius=100, width=250, height=35, command=DiscussionRoomPayment)
    discussionroompayment_btn.grid(row=2, column=4, padx=40, pady=10, sticky="e")
    membershippayment_btn = ctk.CTkButton(master=feesframe, text="Subscription Payment", font=("Arial", 18),corner_radius=100, width=250, height=35,command=MembershipPayment)
    membershippayment_btn.grid(row=3, column=4, padx=40, pady=(10,30), sticky="e")

    penaltypayment_btn.configure(state="disabled") 
    discussionroompayment_btn.configure(state="disabled")
    membershippayment_btn.configure(state="disabled")

#Create MemberManagementFrame (Admin Side)
def member_management():
    #Destroy other frames during changing of the frame
    admin_mainframe.destroy()
    global member_managementframe
    if member_managementframe != None:
        member_managementframe.destroy()
    if feesframe != None:
        feesframe.destroy()
    if catalog_managementframe != None:
        catalog_managementframe.destroy()
    if borrowframe != None:
        borrowframe.destroy()
        clear_borrowings_table()
    if returnframe !=None:
        returnframe.destroy()
    if reportframe !=None:
        reportframe.destroy()
    if room_managementframe != None:
        room_managementframe.destroy()
        
    # Frame
    member_managementframe = ctk.CTkFrame(master=admin_home,fg_color="#2b2b2b")
    member_managementframe.grid(row=0, column=1, rowspan=50, columnspan=50,sticky="nw")
    member_list = ctk.CTkScrollableFrame(master=member_managementframe, width=910, height=250,fg_color="#333333")
    member_list.grid(row=6, column=0, rowspan=3, columnspan=5, padx=30, pady=(10,30))

    # home
    def BackToHome():
        member_managementframe.grid_forget()
        admin_menu()

    adminhome_btn = ctk.CTkButton(master=member_managementframe, text="\U0001F3E0 Home", font=("Arial", 20, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=BackToHome) 
    adminhome_btn.place(relx=0.88,rely=0.04)

    title_label = ctk.CTkLabel(master=member_managementframe, text="Member Management",font=("Arial", 24, "bold"))
    title_label.grid(row=0, column=0, padx=(40,0), columnspan=5, pady=(30,20), sticky="w")

    # String variable
    membernric = ctk.StringVar()
    membername = ctk.StringVar()
    memberemail = ctk.StringVar()
    membercontact = ctk.StringVar()
    
    #Cooperate with the treeview,if select the specific row of the tree view, the data in the treeview will also appear in the respective entry.
    def MemberInfo(ev):
        viewInfo = member_search.focus()
        memberData = member_search.item(viewInfo)
        row = memberData ['values']
        if len(row)>=7:
            membernric.set(row[0])
            membername.set(row[1])
            memberemail.set(row[2])
            membercontact.set(row[3])
            address_entry.delete("1.0", "end")
            address_entry.insert("0.0",row[4])
            membership_display.configure(text=row[5])

            global connection
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM borrowedmember WHERE IC = %s AND Return_Date IS NULL AND Payment_Condition = 'Un-Paid'", (membernric.get(),))
            borrow_count = cursor.fetchone()[0]
            cursor.execute("SELECT End_Membership_Date FROM Membership WHERE IC = %s", (membernric.get(),))
            membershipdue = cursor.fetchone()
            cursor.close()
        
            borrowed_books.configure(text="Current borrowed books:\t" + str(borrow_count))
            penalty.configure(text="Penalty:\t\tRM " + row[6]) 
            if membershipdue:
                membership_due.configure(text=membershipdue)
            else:
                membership_due.configure(text="-")

    #search
    def SearchData():
        member_ic = membernric.get()
        member_name = membername.get().title()
        def displaySearchData():
            global connection
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            cursor = connection.cursor()
            cursor.execute("SELECT IC,Name,Email,Contact,Address,Membership_Status,Penalty FROM PersonalInformation WHERE IC = %s OR Name LIKE %s", (member_ic,member_name+'%'))
            member_result = cursor.fetchall()
            member_search.delete(*member_search.get_children())
            member_search.insert('',0,text="",values=("No result found.","","","","",""))

            if member_name == "" and member_ic == "":
                member_search.delete(*member_search.get_children())
                member_search.insert('',0,text="",values=("No result found.","","","","",""))
            elif len(member_result) != 0:
                member_search.delete(*member_search.get_children())
                for row in member_result:
                    member_search.insert('', 'end', values=row)
            cursor.close()  # Close the cursor after use

        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost

        cursor = connection.cursor()
        cursor.execute("SELECT IC,Name,Email,Contact,Address,Membership_Status,Penalty FROM PersonalInformation WHERE IC = %s OR Name LIKE %s", (member_ic,member_name+'%'))
        rows = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM borrowedmember WHERE IC = %s AND Return_Date IS NULL AND Payment_Condition = 'Un-Paid'", (member_ic,))
        borrow_count = cursor.fetchone()[0]
        
        if not rows:
            member_search.delete(*member_search.get_children())
            member_search.insert('',0,text="",values=("No result found.","","","","",""))
        
        row = rows[0]
        membernric.set(row[0])
        membername.set(row[1])
        memberemail.set(row[2])
        membercontact.set(row[3])
        address_entry.delete("1.0", "end")
        address_entry.insert("0.0", row[4])
        membership_display.configure(text=row[5])
        borrowed_books.configure(text="Current borrowed books:\t"+str(borrow_count))
        penalty.configure(text="Penalty:\t\tRM " + "{:.2f}".format(float(row[6])))
        
        if row[5] == "Premiere":
            cursor.execute("SELECT End_Membership_Date FROM Membership WHERE IC = %s OR Name LIKE %s", (member_ic,member_name+'%'))
            membershipdue = cursor.fetchone()
            if membershipdue:
                membership_due.configure(text=membershipdue[0])
            else:
                membership_due.configure(text="-")
        connection.commit
        cursor.close
        displaySearchData()

        memberborrow_list = ctk.CTkScrollableFrame(master=member_managementframe, width=910, height=250,fg_color="#333333")
        memberborrow_list.grid(row=6, column=0, rowspan=3, columnspan=5, padx=30, pady=(10,30))
        
        #Display borrow record of the customers
        def DisplayBorrowHistory():
            global connection
            try:
                if not connection or not connection.is_connected():
                    connection = connect()  # Reconnect if the connection is closed or lost
                cursor = connection.cursor()
                cursor.execute("SELECT ISBN, Book_Title, Borrowed_Date, Return_Date, Due_Date, Penalty, Payment_Condition FROM borrowedmember WHERE IC=%s ORDER BY Borrowed_Date ASC",(membernric.get(),))
                borrowhistory_search.delete(*borrowhistory_search.get_children())
                i=0
                for ro in cursor:
                    borrowhistory_search.insert('',i,text="",values=(ro[0],ro[1],ro[2],ro[3],ro[4],ro[5],ro[6]))
                cursor.close()  # Close the cursor after use
                connection.commit()
            except mysql.connector.Error as error:
                print(f"Error: Unable to load tasks from the database. {error}")
                exit()

        global borrowhistory_search
        borrowhistory_search = ttk.Treeview(memberborrow_list,show="headings", selectmode="browse", height=100)
        borrowhistory_search['column']=("ISBN","Book_Title","Borrowed_Date","Return_Date","Due_Date","Penalty","Payment")

        # Column
        borrowhistory_search.column("#0",width=0,stretch=tk.NO) # Hide the default first column
        borrowhistory_search.column("ISBN",anchor="w",width=120, minwidth=120)
        borrowhistory_search.column("Book_Title",anchor="w",width=300, minwidth=300)
        borrowhistory_search.column("Borrowed_Date",anchor="w",width=120, minwidth=120)
        borrowhistory_search.column("Return_Date",anchor="w",width=120, minwidth=120)
        borrowhistory_search.column("Due_Date",anchor="w",width=120, minwidth=120)
        borrowhistory_search.column("Penalty",anchor="w",width=120, minwidth=120)
        borrowhistory_search.column("Payment",anchor="w",width=130, minwidth=130)

        # Headings
        borrowhistory_search.heading("ISBN", text="ISBN", anchor="w")
        borrowhistory_search.heading("Book_Title", text="Book_Title", anchor="w")
        borrowhistory_search.heading("Borrowed_Date", text="Borrow Date", anchor="w")
        borrowhistory_search.heading("Return_Date", text="Return Date", anchor="w")
        borrowhistory_search.heading("Due_Date", text="Due Date", anchor="w")
        borrowhistory_search.heading("Penalty", text="Penalty (RM)", anchor="w")
        borrowhistory_search.heading("Payment", text="Payment", anchor="w")
        DisplayBorrowHistory()
        borrowhistory_search.pack(fill="x") 
        
    #update
    def UpdateData():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("UPDATE PersonalInformation SET Name =%s,Email=%s,Contact=%s,Address=%s WHERE IC = %s ", (membername.get(), memberemail.get(), membercontact.get(), address_entry.get("0.0", "end-1c"), membernric.get()))
        connection.commit()
        cursor.close()  # Close the cursor after use
        messagebox.showinfo("Success", "Data has been updated successfully.")
        SearchData()

    # delete
    def DeleteData():
        delete = messagebox.askquestion("Delete", "The data will be removed permanently.")
        if delete == "yes":
            global connection
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            cursor = connection.cursor()
            cursor.execute("Delete FROM PersonalInformation WHERE IC = %s ", (membernric.get(),))
            cursor.execute("Delete FROM membership WHERE IC = %s ", (membernric.get(),))
            connection.commit()
            cursor.close()  # Close the cursor after use
            messagebox.showinfo("Success", "Data has been removed successfully.")
            ic_entry.delete("0","end")
            email_entry.delete("0","end")
            name_entry.delete("0","end")
            contact_entry.delete("0","end")
            address_entry.delete("1.0", "end")
            membership_display.configure(text="-")
            borrowed_books.configure(text="Current borrowed books:\t-")
            penalty.configure(text="Penalty:\t\tRM 0.00")
            membership_due.configure(text="-")
            SearchData()
    
    #Calculate the penalties for the customers
    def penaltycalculation():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()
        cursor = connection.cursor()
        cursor.execute("SELECT ISBN, IC, Return_Date, Due_Date, Penalty, Lost FROM Borrowedmember WHERE Payment_Condition='Un-Paid'")
        penalty_dates = cursor.fetchall()
        penalties = {}  

        for isbn, due_ic, return_date, due_date, penalty, lost in penalty_dates:
            if due_ic not in penalties:
                penalties[due_ic] = 0

            if lost == "Lost":
                penalties[due_ic] += penalty
                cursor.execute("UPDATE BorrowedMember SET Penalty = %s WHERE ISBN=%s AND Payment_Condition='Un-Paid' AND Lost='Lost' AND IC = %s", (penalty,isbn,due_ic,))
            else:
                if return_date is None:
                    returnbook_date = dt.datetime.now()
                else:
                    returnbook_date = return_date

                returnbook_datetime = dt.datetime.combine(returnbook_date, dt.datetime.min.time())
                due_datetime = dt.datetime.combine(due_date, dt.datetime.min.time())
                penaltydays = (returnbook_datetime - due_datetime).days

                if 0 < penaltydays <= 3:
                    penalty = 0.1 * penaltydays
                elif 3 < penaltydays <= 6:
                    penalty = 0.1 * 3 + 0.2 * (penaltydays - 3)
                elif 6 < penaltydays <= 24:
                    penalty = 0.1 * 3 + 0.2 * 3 + 0.3 * (penaltydays - 6)
                elif penaltydays > 24:
                    penalty = 10
                else:
                    penalty = 0
                cursor.execute("UPDATE BorrowedMember SET Penalty = %s WHERE ISBN=%s AND Payment_Condition='Un-Paid' AND IC = %s", (penalty,isbn,due_ic,))
                penalties[due_ic] += penalty

        # Update penalties in the database
        for due_ic, totalpenalty in penalties.items():
            cursor.execute("UPDATE PersonalInformation SET Penalty = %s WHERE IC = %s", (totalpenalty, due_ic,))
        
        connection.commit()
        cursor.close()

    ic_label = ctk.CTkLabel(master=member_managementframe, text="IC: ",font=("Arial", 18))
    ic_label.grid(row=1, column=0, padx=40, pady=10, sticky="w")
    ic_entry = ctk.CTkEntry(master=member_managementframe, width=180,textvariable=membernric)
    ic_entry.grid(row=1, column=1, pady=10, sticky="w")

    email_label = ctk.CTkLabel(master=member_managementframe, text="Email: ", font=("Arial", 18))
    email_label.grid(row=1, column=2, pady=10, sticky="w")
    email_entry = ctk.CTkEntry(master=member_managementframe, width=180,textvariable=memberemail)
    email_entry.grid(row=1, column=3, pady=10, sticky="w")

    name_label = ctk.CTkLabel(master=member_managementframe, text="Name:", font=("Arial", 18))
    name_label.grid(row=2, column=0, padx=40, pady=10, sticky="w")
    name_entry = ctk.CTkEntry(master=member_managementframe, width=180,textvariable=membername)
    name_entry.grid(row=2, column=1, pady=10, sticky="w")

    contact_label = ctk.CTkLabel(master=member_managementframe, text="Contact:", font=("Arial", 18))
    contact_label.grid(row=2, column=2, pady=10, sticky="w")
    contact_entry = ctk.CTkEntry(master=member_managementframe, width=180,textvariable=membercontact)
    contact_entry.grid(row=2, column=3, pady=10, sticky="w")

    membership_label = ctk.CTkLabel(master=member_managementframe, text="Membership:", font=("Arial", 18))
    membership_label.grid(row=3, column=0, padx=40, pady=10, sticky="w")
    membership_display = ctk.CTkLabel(master=member_managementframe, text="-", font=("Arial", 18))
    membership_display.grid(row=3, column=1, pady=10, sticky="w")

    membership_due_label = ctk.CTkLabel(master=member_managementframe, text="Membership due: ", font=("Arial", 18))
    membership_due_label.grid(row=3, column=2, pady=10, sticky="w")
    membership_due = ctk.CTkLabel(master=member_managementframe, text="-", font=("Arial", 18))
    membership_due.grid(row=3, column=3, pady=10, sticky="w")

    borrowed_books = ctk.CTkLabel(master=member_managementframe, text="Current borrowed books:\t-", font=("Arial", 18))
    borrowed_books.grid(row=4, column=0, padx=40, columnspan=2, pady=10, sticky="w")
    penalty = ctk.CTkLabel(master=member_managementframe, text="Penalty:\t\tRM 0.00", font=("Arial", 18))
    penalty.grid(row=4, column=2, columnspan=2, pady=10, sticky="w")

    address_label = ctk.CTkLabel(master=member_managementframe, text="Address:", font=("Arial", 18))
    address_label.grid(row=5, column=0, padx=40, pady=10, sticky="nw")
    address_entry = ctk.CTkTextbox(master=member_managementframe,width=400, height=50)
    address_entry.grid(row=5, column=1, columnspan=4, pady=10, sticky="w")

    # side buttons
    btn_width = 100
    searchmember = ctk.CTkButton(master=member_managementframe, text="View", font=("Arial", 18), width=btn_width, height=30, corner_radius=100, command=SearchData)
    searchmember.grid(row=1,column=4,padx=(0,30),pady=10)

    updatemember = ctk.CTkButton(master=member_managementframe, text="Update", font=("Arial", 18), width=btn_width, height=30, corner_radius=100, command=UpdateData)
    updatemember.grid(row=2,column=4,padx=(0,30),pady=10)

    deletemember = ctk.CTkButton(master=member_managementframe, text="Delete", font=("Arial", 18), width=btn_width, height=30, corner_radius=100, command=DeleteData)
    deletemember.grid(row=3,column=4,padx=(0,30),pady=10)

    resetbtn = ctk.CTkButton(master=member_managementframe, text="Reset", font=("Arial", 18), width=btn_width, height=30, corner_radius=100, command=member_management)
    resetbtn.grid(row=4,column=4,padx=(0,30),pady=10, sticky="n")

    #Display all the members detail
    def DisplayMembers():
        penaltycalculation()
        global connection
        try:
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            cursor = connection.cursor()
            cursor.execute("SELECT IC,Name,Email,Contact,Address,Membership_Status,Penalty FROM personalinformation ORDER BY Name DESC")
            member_search.delete(*member_search.get_children())
            i=0
            for ro in cursor:
                member_search.insert('',i,text="",values=(ro[0],ro[1],ro[2],ro[3],ro[4],ro[5],ro[6]))
            cursor.close()  # Close the cursor after use
            connection.commit()
            member_search.after(1000, DisplayMembers)
        except mysql.connector.Error as error:
            print(f"Error: Unable to load tasks from the database. {error}")
            exit()

    global member_search
    member_search = ttk.Treeview(member_list,height=50,show="headings",selectmode="browse")
    member_search['column']=("IC","Name","Email","Contact","Address","Membership_Status","Penalty")

    # Column
    member_search.column("#0",width=0,stretch=tk.NO) # Hide the default first column
    member_search.column("IC",anchor="w",width=152, minwidth=152)
    member_search.column("Name",anchor="w",width=220, minwidth=220)
    member_search.column("Email",anchor="w",width=200, minwidth=200)
    member_search.column("Contact",anchor="w",width=150, minwidth=150)
    member_search.column("Address",anchor="w",width=200, minwidth=200)
    member_search.column("Membership_Status",anchor="w",width=100, minwidth=100)
    member_search.column("Penalty",anchor="w",width=120, minwidth=120)

    # Headings
    member_search.heading("IC", text="IC", anchor="w")
    member_search.heading("Name", text="Name", anchor="w")
    member_search.heading("Email", text="Email", anchor="w")
    member_search.heading("Contact", text="Contact", anchor="w")
    member_search.heading("Address", text="Address", anchor="w")
    member_search.heading("Membership_Status", text="Status", anchor="w")
    member_search.heading("Penalty", text="Penalty(RM)", anchor="w")
    DisplayMembers()
    member_search.pack(fill="both")
    member_search.bind("<ButtonRelease-1>",MemberInfo)

#Create Catalog(book) Management Frame (Admin Side)
def catalog_management(): 
    #Destroy the frame during changing of the frame
    admin_mainframe.destroy()
    global catalog_managementframe
    if catalog_managementframe != None:
        catalog_managementframe.destroy()
    if feesframe != None:
        feesframe.destroy()
    if borrowframe != None:
        borrowframe.destroy()
        clear_borrowings_table()
    if member_managementframe != None:
        member_managementframe.destroy()
    if returnframe !=None:
        returnframe.destroy()
    if room_managementframe != None:
        room_managementframe.destroy()
        
    # Frame
    catalog_managementframe = ctk.CTkFrame(master=admin_home,fg_color="#2b2b2b")
    catalog_managementframe.grid(row=0, column=1, rowspan=50, columnspan=50,sticky="nw")
    book_list = ctk.CTkScrollableFrame(master=catalog_managementframe, width=910, height=250,fg_color="#333333")
    book_list.grid(row=6, column=0, rowspan=3, columnspan=5, padx=30, pady=(10,30))
    
    # home
    def BackToHome():
        catalog_managementframe.grid_forget()
        admin_menu()

    adminhome_btn = ctk.CTkButton(master=catalog_managementframe, text="\U0001F3E0 Home", font=("Arial", 20, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=BackToHome) 
    adminhome_btn.place(relx=0.88,rely=0.04)

    title_label = ctk.CTkLabel(master=catalog_managementframe, text="Catalog Management",font=("Arial", 24, "bold"))
    title_label.grid(row=0, column=0, padx=(40,0), columnspan=5, pady=(30,20), sticky="w")

    # String variable
    catalog_ISBN = ctk.StringVar()
    booktitle = ctk.StringVar()
    author = ctk.StringVar()
    year_published = ctk.StringVar()
    publisher = ctk.StringVar()
    price = ctk.StringVar()
    genre = ctk.StringVar()
    language = ctk.StringVar()
    availability = ctk.StringVar()

    #search
    def searchData():
        book_isbn = catalog_ISBN.get()
        search_result = book_entry.get().title()
        def displaysearchData():
            global connection
            try:
                if not connection or not connection.is_connected():
                    connection = connect()  # Reconnect if the connection is closed or lost
                cursor = connection.cursor()
                query = "SELECT * FROM books WHERE ISBN = %s OR Book_Title LIKE %s ORDER BY CASE WHEN Book_Title REGEXP CONCAT(%s,'%') THEN 1 ELSE 2 END DESC, LENGTH(Book_Title) ASC"
                cursor.execute(query, (book_isbn, search_result + '%', search_result + '%'))
                book_result = cursor.fetchall()
                catalog_search.delete(*catalog_search.get_children())
                catalog_search.insert('',0,text="",values=("No result found.","","","","","","","",""))

                if search_result == "" and book_isbn == "":
                    catalog_search.delete(*catalog_search.get_children())
                    catalog_search.insert('',0,text="",values=("No result found.","","","","","","","",""))
                elif len(book_result) != 0:
                    catalog_search.delete(*catalog_search.get_children())
                    for row in book_result:
                        catalog_search.insert('', 'end', values=row)
                    cursor.close()  # Close the cursor after use
            except mysql.connector.Error as error:
                print(f"Error: Unable to load tasks from the database. {error}")
                exit()
        
        global connection
        try:
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost

            cursor = connection.cursor()
            query = "SELECT * FROM books WHERE ISBN = %s OR Book_Title LIKE %s ORDER BY CASE WHEN Book_Title REGEXP CONCAT(%s,'%') THEN 1 ELSE 2 END DESC, LENGTH(Book_Title) ASC"
            cursor.execute(query, (book_isbn, search_result + '%', search_result + '%'))  
            rows = cursor.fetchall()
            
            if rows:
                if search_result == "" and book_isbn == "":
                    catalog_search.delete(*catalog_search.get_children())
                    catalog_search.insert('',0,text="",values=("No result found.","","","","","","","",""))
                else:
                    row = rows[0]  # Assuming you only want to display the first result
                    catalog_ISBN.set(row[0])
                    booktitle.set(row[1])
                    author.set(row[2])
                    year_published.set(row[3])
                    publisher.set(row[4])
                    price.set(row[5])
                    genre.set(row[6])
                    language.set(row[7])
                    availability.set(row[8])
            else:
                # Handle case when no matching record is found
                pass
            
            connection.commit()
            cursor.close()  # Close the cursor after use
            displaysearchData()
        except mysql.connector.Error as err:
            # Handle MySQL errors
            print("MySQL Error:", err)

    #Display All the books in the database
    def DisplayCatalog():
        global connection
        try:
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM books ORDER BY Book_Title ASC")
            book_result = cursor.fetchall()
            if len(book_result) != 0:
                catalog_search.delete(*catalog_search.get_children())
                for row in book_result:
                    catalog_search.insert('', 'end', values=row)
                cursor.close()  # Close the cursor after use
        except mysql.connector.Error as error:
            print(f"Error: Unable to load tasks from the database. {error}")
            exit()

    #Cooperate with the treeview,if select the specific row of the tree view, the data in the treeview will also appear in the respective entry.
    def BookInfo(ev):
        viewInfo = catalog_search.focus()
        bookData = catalog_search.item(viewInfo)
        row = bookData ['values']
        #Due to the limitation of the mysql, the 0 in front of any digit, it will be ignored, hence, to make sure it will be same as the database and show them, we need to add 0
        if len(str(row[0]))< 10:
            row[0] =  "0" * (10 - len(str(row[0])))+str(row[0])
        catalog_ISBN.set(row[0])
        booktitle.set(row[1])
        author.set(row[2])
        year_published.set(row[3])
        publisher.set(row[4])
        price.set(row[5])
        genre.set(row[6])
        language.set(row[7])
        availability.set(row[8])

    #Update info of the books
    def UpdateData():
        global connection
        if not connection or not connection.is_connected():
            connection = connect() # Reconnect if the connection is closed or lost
        bookprice=float(price.get())
        cursor = connection.cursor()
        cursor.execute("UPDATE books SET Book_Title=%s, Book_Author=%s, Year_Of_Publication=%s, Publisher=%s, `Price_(RM)`=%s, Genre=%s, Language=%s WHERE ISBN = %s ", (booktitle.get().title(),author.get(),year_published.get(), publisher.get(), bookprice, genre.get(), language.get(),catalog_ISBN.get()))
        connection.commit()
        cursor.close()
        messagebox.showinfo("Success", "Data has been updated successfully.")
        searchData()

    #Add More books data into the database
    def AddData():
        if book_entry.get()=="" or ISBN_entry.get()=="" or author_entry.get()=="" or publisher_entry.get()=="" or price_entry.get()=="":
            messagebox.showerror("Error","Please input correct details.")
        else:
            global connection
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            bookprice=float(price.get())
            cursor = connection.cursor()
            cursor.execute("INSERT INTO books (ISBN, Book_Title, Book_Author, Year_Of_Publication, Publisher, `Price_(RM)`, Genre, Language) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",(catalog_ISBN.get(),booktitle.get().title(),author.get(),year_published.get(), publisher.get(), bookprice, genre.get(), language.get()))
            connection.commit()
            cursor.close()  # Close the cursor after use
            messagebox.showinfo("Success", "Data has been successfully stored in database.")
            searchData()

    #Delete books from the database
    def DeleteData():
        delete = messagebox.askquestion("Delete", "The data will be removed permanently.")
        if delete == "yes":
            global connection
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            cursor = connection.cursor()
            cursor.execute("DELETE FROM books WHERE ISBN = %s", (catalog_ISBN.get(),))
            connection.commit()
            cursor.close()  # Close the cursor after use
            messagebox.showinfo("Success", "Data has been removed successfully.")
            ISBN_entry.delete("0","end")
            book_entry.delete("0","end")
            author_entry.delete("0","end")
            year_entry.delete("0","end")
            publisher_entry.delete("0","end")
            price_entry.delete("0","end")
            genre_entry.delete("0","end")
            language_entry.delete("0","end")
            availability_entry.delete("0","end")
            searchData()

    #Initialise the displaying of the books
    def Reset():
        catalog_ISBN.set("")
        booktitle.set("")
        author.set("")
        year_published.set("")
        publisher.set("")
        price.set("")
        genre.set("")
        language.set("")
        availability.set("")
        catalog_search.delete(*catalog_search.get_children())

    book_label = ctk.CTkLabel(master=catalog_managementframe, text="Book Ttile: ",font=("Arial", 18))
    book_label.grid(row=1, column=0, padx=40, pady=10, sticky="w")
    book_entry = ctk.CTkEntry(master=catalog_managementframe, width=300, textvariable=booktitle)
    book_entry.grid(row=1, column=1, columnspan=2, pady=10, sticky="w")

    ISBN_label = ctk.CTkLabel(master=catalog_managementframe, text="ISBN: ", font=("Arial", 18))
    ISBN_label.grid(row=2, column=0, padx=40, pady=10, sticky="w")
    ISBN_entry = ctk.CTkEntry(master=catalog_managementframe, width=180,textvariable=catalog_ISBN)
    ISBN_entry.grid(row=2, column=1, pady=10, sticky="w")

    year_label = ctk.CTkLabel(master=catalog_managementframe, text="Year:", font=("Arial", 18))
    year_label.grid(row=2, column=2, pady=10, sticky="w")
    year_entry = ctk.CTkEntry(master=catalog_managementframe, width=180,textvariable=year_published)
    year_entry.grid(row=2, column=3, pady=10, sticky="w")

    author_label = ctk.CTkLabel(master=catalog_managementframe, text="Author:", font=("Arial", 18))
    author_label.grid(row=3, column=0, padx=40, pady=10, sticky="w")
    author_entry = ctk.CTkEntry(master=catalog_managementframe, width=180,textvariable=author)
    author_entry.grid(row=3, column=1, pady=10, sticky="w")

    publisher_label = ctk.CTkLabel(master=catalog_managementframe, text="Publisher: ", font=("Arial", 18))
    publisher_label.grid(row=3, column=2, pady=10, sticky="w")
    publisher_entry = ctk.CTkEntry(master=catalog_managementframe, width=180,textvariable=publisher)
    publisher_entry.grid(row=3, column=3, pady=10, sticky="w")

    genre_label = ctk.CTkLabel(master=catalog_managementframe, text="Genre: ", font=("Arial", 18))
    genre_label.grid(row=4, column=0, padx=40, pady=10, sticky="w")
    genre_entry = ctk.CTkEntry(master=catalog_managementframe, width=180,textvariable=genre)
    genre_entry.grid(row=4, column=1, pady=10, sticky="w")

    language_label = ctk.CTkLabel(master=catalog_managementframe, text="Language: ", font=("Arial", 18))
    language_label.grid(row=4, column=2, pady=10, sticky="w")
    language_entry = ctk.CTkEntry(master=catalog_managementframe, width=180,textvariable=language)
    language_entry.grid(row=4, column=3, pady=10, sticky="w")

    price_label = ctk.CTkLabel(master=catalog_managementframe, text="Price (RM): ", font=("Arial", 18))
    price_label.grid(row=5, column=0, padx=40, pady=10, sticky="w")
    price_entry = ctk.CTkEntry(master=catalog_managementframe, width=180,textvariable=price)
    price_entry.grid(row=5, column=1, pady=10, sticky="w")

    availability_label = ctk.CTkLabel(master=catalog_managementframe, text="Availability: ", font=("Arial", 18))
    availability_label.grid(row=5, column=2, pady=10, sticky="w")
    availability_entry = ctk.CTkEntry(master=catalog_managementframe, width=180,textvariable=availability)
    availability_entry.grid(row=5, column=3, pady=10, sticky="w")

    # side buttons
    btn_width = 100
    searchcatalog = ctk.CTkButton(master=catalog_managementframe, text="Search", font=("Arial", 18), width=btn_width, height=30, corner_radius=100, command=searchData)
    searchcatalog.grid(row=1,column=3,pady=10, sticky="w")

    displaycatalog = ctk.CTkButton(master=catalog_managementframe, text="Display", font=("Arial", 18), width=btn_width, height=30, corner_radius=100, command=DisplayCatalog)
    displaycatalog.grid(row=1,column=4,padx=(0,30),pady=10)

    addcatalog = ctk.CTkButton(master=catalog_managementframe, text="Add", font=("Arial", 18), width=btn_width, height=30, corner_radius=100, command=AddData)
    addcatalog.grid(row=2,column=4,padx=(0,30),pady=10)

    updatecatalog = ctk.CTkButton(master=catalog_managementframe, text="Update", font=("Arial", 18), width=btn_width, height=30, corner_radius=100, command=UpdateData)
    updatecatalog.grid(row=3,column=4,padx=(0,30),pady=10)

    deletecatalog = ctk.CTkButton(master=catalog_managementframe, text="Delete", font=("Arial", 18), width=btn_width, height=30, corner_radius=100, command=DeleteData)
    deletecatalog.grid(row=4,column=4,padx=(0,30),pady=10)

    resetbtn = ctk.CTkButton(master=catalog_managementframe, text="Reset", font=("Arial", 18), width=btn_width, height=30, corner_radius=100, command=Reset)
    resetbtn.grid(row=5,column=4,padx=(0,30),pady=10, sticky="n")

    global catalog_search
    catalog_search = ttk.Treeview(book_list,height=50,show="headings",selectmode="browse")
    catalog_search['column']=("ISBN","Book_Title","Book_Author","Year_Of_Publication","Publisher","Price","Genre","Language","Availability")

    # Column
    catalog_search.column("#0",width=0,stretch=tk.NO) # Hide the default first column
    catalog_search.column("ISBN",anchor="w",width=130, minwidth=130)
    catalog_search.column("Book_Title",anchor="w",width=250, minwidth=250)
    catalog_search.column("Book_Author",anchor="w",width=160, minwidth=160)
    catalog_search.column("Year_Of_Publication",anchor="w",width=50, minwidth=50)
    catalog_search.column("Publisher",anchor="w",width=180, minwidth=180)
    catalog_search.column("Price",anchor="w",width=100, minwidth=100)
    catalog_search.column("Genre",anchor="w",width=150, minwidth=150)
    catalog_search.column("Language",anchor="w",width=120, minwidth=120)
    catalog_search.column("Availability",anchor="w",width=120, minwidth=120)

    # Headings
    catalog_search.heading("ISBN", text="ISBN", anchor="w")
    catalog_search.heading("Book_Title", text="Book Title", anchor="w")
    catalog_search.heading("Book_Author", text="Author", anchor="w")
    catalog_search.heading("Year_Of_Publication", text="Year", anchor="w")
    catalog_search.heading("Publisher", text="Publisher", anchor="w")
    catalog_search.heading("Price", text="Price (RM)", anchor="w")
    catalog_search.heading("Genre", text="Genre", anchor="w")
    catalog_search.heading("Language", text="Language", anchor="w")
    catalog_search.heading("Availability", text="Availability", anchor="w")
    catalog_search.pack(fill="x")
    catalog_search.bind("<ButtonRelease-1>",BookInfo)

#Create the discussion room management frame (Admin Side)
def DiscussionRoomManagement():
    #Destroy other frame during changing of the frame
    admin_mainframe.destroy()
    global room_managementframe
    if member_managementframe != None:
        member_managementframe.destroy()
    if feesframe != None:
        feesframe.destroy()
    if catalog_managementframe != None:
        catalog_managementframe.destroy()
    if borrowframe != None:
        borrowframe.destroy()
        clear_borrowings_table()
    if returnframe !=None:
        returnframe.destroy()
    if reportframe !=None:
        reportframe.destroy()
    if room_managementframe != None:
        room_managementframe.destroy()

    # Frame
    room_managementframe = ctk.CTkFrame(master=admin_home,fg_color="#2b2b2b")
    room_managementframe.grid(row=0, column=1, rowspan=50, columnspan=50,sticky="nw")
    roombooking_list = ctk.CTkScrollableFrame(master=room_managementframe, width=910, height=250,fg_color="#333333")
    roombooking_list.grid(row=2, column=0, rowspan=3, columnspan=20, padx=30, pady=30)
    roominfoframe = tk.LabelFrame(master=room_managementframe, text= "Discussion Room Status", width=550, height=200, bg="#2b2b2b", fg="white", font=("Arial", 18))
    roominfoframe.grid(row=5, column=0, rowspan=8, columnspan=8, padx=50, pady=(0,30), sticky="w")

    # home
    def BackToHome():
        room_managementframe.grid_forget()
        admin_menu()

    adminhome_btn = ctk.CTkButton(master=room_managementframe, text="\U0001F3E0 Home", font=("Arial", 20, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=BackToHome) 
    adminhome_btn.place(relx=0.88,rely=0.04)

    title_label = ctk.CTkLabel(master=room_managementframe, text="Discussion Room Management", font=("Arial", 24, "bold"))
    title_label.grid(row=0, column=0, padx=(40,0), columnspan=5, pady=(30,20), sticky="w")

    #Check whether the room is booked or not
    def CheckRoomStatus(room, current_date, current_time):
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM bookingroom WHERE Date=%s AND ((Start_Time <= %s AND End_Time > %s) OR (Start_Time < %s AND End_Time >= %s)) AND Room=%s AND Check_In='Check-in'", (current_date,current_time,current_time,current_time,current_time,room))
        room_confirmation=cursor.fetchone()
        connection.commit()
        cursor.close()
        return room_confirmation is not None
    
    #Check the room specifically
    def GetCurrentBookingStatus():
        current_time = time.strftime("%H:%M:%S")
        current_date = dt.datetime.now().strftime('%Y-%m-%d')
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  
        cursor = connection.cursor()

        # Fetch availability for Room1
        cursor.execute("SELECT availability FROM Room WHERE Room= 'Room1'")
        room1_availability = cursor.fetchone()[0]  # Fetch the availability value directly

        # Fetch availability for Room2
        cursor.execute("SELECT availability FROM Room WHERE Room = 'Room2'")
        room2_availability = cursor.fetchone()[0]  # Fetch the availability value directly

        # Fetch availability for Room3
        cursor.execute("SELECT availability FROM Room WHERE Room = 'Room3'")
        room3_availability = cursor.fetchone()[0]  # Fetch the availability value directly
        
        cursor.execute("SELECT Room, Start_Time, End_Time FROM bookingroom WHERE Date = %s",(current_date,))
        booking_status = cursor.fetchall()
        room1_booked = False
        room2_booked = False
        room3_booked = False

        #Check all the rooms in the database
        for result in booking_status:
            room1_booked = CheckRoomStatus('Room1', current_date, current_time)
            room2_booked = CheckRoomStatus('Room2', current_date, current_time)
            room3_booked = CheckRoomStatus('Room3', current_date, current_time)

        #If switch the button, the room1 will display grey and means not available
        if room1_availability == "Not Available":
            room1_status.configure(fg_color="grey")
            room1_switch.toggle()
        else:
            if not room1_booked:
                room1_status.configure(fg_color="green")
            else:
                room1_status.configure(fg_color="red")
        
        #If switch the button, the room2 will display grey and means not available
        if room2_availability == "Not Available":
            room2_status.configure(fg_color="grey")
            room2_switch.toggle()
        else:
            if not room2_booked:
                room2_status.configure(fg_color="green")
            else:
                room2_status.configure(fg_color="red")
        
        #If switch the button, the room3 will display grey and means not available
        if room3_availability == "Not Available":
            room3_status.configure(fg_color="grey")
            room3_switch.toggle()
        else:
            if not room3_booked:
                room3_status.configure(fg_color="green")
            else:
                room3_status.configure(fg_color="red")
        connection.commit()
        cursor.close()

    #Specific for room 1 checking
    def GetCurrentBookingRoom1Status():
        current_time = time.strftime("%H:%M:%S")
        current_date = dt.datetime.now().strftime('%Y-%m-%d')
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  
        cursor = connection.cursor()
        cursor.execute("SELECT Room, Start_Time, End_Time FROM bookingroom WHERE Date = %s",(current_date,))
        booking_status = cursor.fetchall()
        cursor.execute("UPDATE Room SET Availability=%s WHERE Room='Room1'",("Available",))
        room1_booked = False
        for result in booking_status:
            room1_booked = CheckRoomStatus('Room1', current_date, current_time)
        if not room1_booked:
            room1_status.configure(fg_color="green")
        else:
            room1_status.configure(fg_color="red")
        connection.commit()
        cursor.close()
    
    #Specific for room 2 checking
    def GetCurrentBookingRoom2Status():
        current_time = time.strftime("%H:%M:%S")
        current_date = dt.datetime.now().strftime('%Y-%m-%d')
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  
        cursor = connection.cursor()
        cursor.execute("SELECT Room, Start_Time, End_Time FROM bookingroom WHERE Date = %s",(current_date,))
        booking_status = cursor.fetchall()
        cursor.execute("UPDATE Room SET Availability=%s WHERE Room='Room2'",("Available",))
        room2_booked = False
        for result in booking_status:
            room2_booked = CheckRoomStatus('Room2', current_date, current_time)
        if not room2_booked:
            room2_status.configure(fg_color="green")
        else:
            room2_status.configure(fg_color="red")
        connection.commit()
        cursor.close()

    #Specific for room 3 checking
    def GetCurrentBookingRoom3Status():
        current_time = time.strftime("%H:%M:%S")
        current_date = dt.datetime.now().strftime('%Y-%m-%d')
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  
        cursor = connection.cursor()
        cursor.execute("SELECT Room, Start_Time, End_Time FROM bookingroom WHERE Date = %s",(current_date,))
        booking_status = cursor.fetchall()
        cursor.execute("UPDATE Room SET Availability=%s WHERE Room='Room3'",("Available",))
        room3_booked = False
        for result in booking_status:
            room3_booked = CheckRoomStatus('Room3', current_date, current_time)
        if not room3_booked:
            room3_status.configure(fg_color="green")
        else:
            room3_status.configure(fg_color="red")
        connection.commit()
        cursor.close()

    #Get date for room booking
    def GetDate():
        startdate_entry = start_date.get_date()
        enddate_entry = end_date.get_date()
        roomstart_date = dt.datetime.strftime(startdate_entry, "%Y-%m-%d")
        roomend_date = dt.datetime.strftime(enddate_entry, "%Y-%m-%d")

        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM bookingroom WHERE Date BETWEEN %s AND %s ORDER BY Date ASC", (roomstart_date, roomend_date))
        bookingdata = cursor.fetchall()
        cursor.close()
        room_table.delete(*room_table.get_children())
        for row in bookingdata:
            room_table.insert('', 'end', values=row)

    #Delete room the from booking
    def DeleteBooking():
        selected_room = room_table.selection()
        for item in selected_room:
            delete = messagebox.askquestion("Delete","The data will be removed permanently.")
            if delete == "yes":
                deletebooking = room_table.item(item, 'values')
                room_table.delete(item)
                global connection
                if not connection or not connection.is_connected():
                    connection = connect()
                cursor = connection.cursor()
                cursor.execute("Delete FROM bookingroom WHERE Date = %s AND IC = %s AND Start_Time = %s AND End_Time = %s AND Room = %s", (deletebooking[0],deletebooking[1],deletebooking[3],deletebooking[4],deletebooking[5]))
                connection.commit()
                cursor.close()
                messagebox.showinfo("Success", "Data has been removed successfully.")

    from_label = ctk.CTkLabel(master=room_managementframe, text="From:", font=("Arial", 18))
    from_label.grid(row=1, column=0, padx=(40,0), pady=20, sticky="w")
    start_date = DateEntry(room_managementframe, selectmode="day", width=20, font=("Arial", 14))
    start_date.grid(row=1,column=1,padx=20,pady=20)

    to_label = ctk.CTkLabel(master=room_managementframe, text="To:", font=("Arial", 18))
    to_label.grid(row=1, column=2, padx=(40,0), pady=20, sticky="w")
    end_date = DateEntry(room_managementframe, selectmode="day", width=20, font=("Arial", 14))
    end_date.grid(row=1,column=3,padx=20,pady=20)

    view_btn = ctk.CTkButton(master=room_managementframe, text="View", font=("Arial", 18), width=100, height=30, corner_radius=100, command=GetDate)
    view_btn.grid(row=1, column=4, padx=20, pady=20)

    global room_table
    room_table = ttk.Treeview(roombooking_list,height=10, show="headings", selectmode="browse")
    room_table['column']=("Date","IC","Name","Start_Time","End_Time","Room","Check_in")

    # Column
    room_table.column("#0",width=0,stretch=tk.NO) # Hide the default first column
    room_table.column("Date",anchor="w",width=150,minwidth=150)
    room_table.column("IC",anchor="w",width=180,minwidth=180)
    room_table.column("Name",anchor="w",width=300,minwidth=300)
    room_table.column("Start_Time",anchor="w",width=130,minwidth=130)
    room_table.column("End_Time",anchor="w",width=130,minwidth=130)
    room_table.column("Room",anchor="w",width=120,minwidth=120)
    room_table.column("Check_in",anchor="w",width=130,minwidth=130)

    # Headings
    room_table.heading("Date", text="Date", anchor="w")
    room_table.heading("IC", text="IC", anchor="w")
    room_table.heading("Name", text="Name", anchor="w")
    room_table.heading("Start_Time", text="Start Time", anchor="w")
    room_table.heading("End_Time", text="End Time", anchor="w")
    room_table.heading("Room", text="Room", anchor="w")
    room_table.heading("Check_in", text="Check In", anchor="w")
    GetDate()
    room_table.pack(fill="x")

    delete_btn = ctk.CTkButton(master=room_managementframe, text="Delete", font=("Arial", 18), width=100, height=30, corner_radius=100, command=DeleteBooking)
    delete_btn.grid(row=5, column=10, sticky="ne")

    # Discussion Room Info
    switch1_var = ctk.StringVar(value="available")
    switch2_var = ctk.StringVar(value="available")
    switch3_var = ctk.StringVar(value="available")
    
    #function for room1's button to make the room unavailable after switching the button
    def switch1_event():
        if switch1_var.get() == "unavailable":
            global connection
            if not connection or not connection.is_connected():
                connection = connect()  
            cursor = connection.cursor()
            room1_status.configure(fg_color="grey")
            cursor.execute("UPDATE Room SET Availability=%s WHERE Room='Room1'",("Not Available",))
            connection.commit()
            cursor.close()
        else:
            GetCurrentBookingRoom1Status()

    #function for room2's button to make the room unavailable after switching the button
    def switch2_event():
        if switch2_var.get() == "unavailable":
            global connection
            if not connection or not connection.is_connected():
                connection = connect()  
            cursor = connection.cursor()
            room2_status.configure(fg_color="grey")
            cursor.execute("UPDATE Room SET Availability=%s WHERE Room='Room2'",("Not Available",))
            connection.commit()
            cursor.close()
        else:
            GetCurrentBookingRoom2Status()
    
    #function for room3's button to make the room unavailable after switching the button
    def switch3_event():
        if switch3_var.get() == "unavailable":
            global connection
            if not connection or not connection.is_connected():
                connection = connect()  
            cursor = connection.cursor()
            room3_status.configure(fg_color="grey")
            cursor.execute("UPDATE Room SET Availability=%s WHERE Room='Room3'",("Not Available",))
            connection.commit()
            cursor.close()
        else:
            GetCurrentBookingRoom3Status()

    room1_label = ctk.CTkLabel(master=roominfoframe, text="Room 1:", font=("Arial", 18))
    room1_label.grid(row=0, column=0, padx=40, pady=10, sticky="w")
    room1_switch = ctk.CTkSwitch(master=roominfoframe, text="", command=switch1_event, variable=switch1_var, onvalue="available",offvalue="unavailable")
    room1_switch.grid(row=0, column=1, pady=10, sticky="w")
    room1_status = ctk.CTkLabel(master=roominfoframe, text="",width=30,height=30,corner_radius=100,fg_color="green",bg_color="#2b2b2b")
    room1_status.grid(row=0, column=2, padx=(0,20), pady=10, sticky="w")

    room2_label = ctk.CTkLabel(master=roominfoframe, text="Room 2:", font=("Arial", 18))
    room2_label.grid(row=1, column=0, padx=40, sticky="w")
    room2_switch = ctk.CTkSwitch(master=roominfoframe, text="", command=switch2_event, variable=switch2_var, onvalue="available",offvalue="unavailable")
    room2_switch.grid(row=1, column=1, pady=10, sticky="w")
    room2_status = ctk.CTkLabel(master=roominfoframe, text="",width=30,height=30,corner_radius=100,fg_color="green",bg_color="#2b2b2b")
    room2_status.grid(row=1, column=2, padx=(0,20), sticky="w")

    room3_label = ctk.CTkLabel(master=roominfoframe, text="Room 3:", font=("Arial", 18))
    room3_label.grid(row=2, column=0, padx=40, pady=10, sticky="w")
    room3_switch = ctk.CTkSwitch(master=roominfoframe, text="", command=switch3_event, variable=switch3_var, onvalue="available",offvalue="unavailable")
    room3_switch.grid(row=2, column=1, pady=10, sticky="w")
    room3_status = ctk.CTkLabel(master=roominfoframe, text="",width=30,height=30,corner_radius=100,fg_color="green",bg_color="#2b2b2b")
    room3_status.grid(row=2, column=2, padx=(0,20), pady=10, sticky="w")
    GetCurrentBookingStatus()

#Create Report Frame(Admin Side) 
def Report():
    #Destroy the frame during changing of the frame
    admin_mainframe.destroy()
    global reportframe
    if member_managementframe != None:
        member_managementframe.destroy()
    if feesframe != None:
        feesframe.destroy()
    if catalog_managementframe != None:
        catalog_managementframe.destroy()
    if borrowframe != None:
        borrowframe.destroy()
        clear_borrowings_table()
    if returnframe !=None:
        returnframe.destroy()
    if reportframe !=None:
        reportframe.destroy()
    if room_managementframe != None:
        room_managementframe.destroy()

    # Frame
    reportframe = ctk.CTkFrame(master=admin_home,fg_color="#2b2b2b")
    reportframe.grid(row=0, column=1, rowspan=50, columnspan=50,sticky="nw")
    report_list = ctk.CTkScrollableFrame(master=reportframe, width=910, height=400,fg_color="#333333")
    report_list.grid(row=2, column=0, rowspan=3, columnspan=20, padx=30, pady=10)

    # home
    def BackToHome():
        reportframe.grid_forget()
        admin_menu()

    adminhome_btn = ctk.CTkButton(master=reportframe, text="\U0001F3E0 Home", font=("Arial", 20, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=BackToHome) 
    adminhome_btn.place(relx=0.88,rely=0.04)

    title_label = ctk.CTkLabel(master=reportframe, text="Borrow Report", font=("Arial", 24, "bold"))
    title_label.grid(row=0, column=0, padx=(40,0), columnspan=5, pady=(30,20), sticky="w")
    
    #Select the date for the borrowed books record that you would like to see
    def GetDate():
        startdate_entry = start_date.get_date()
        enddate_entry = end_date.get_date()
        global start_date_input, end_date_input
        start_date_input = dt.datetime.strftime(startdate_entry, "%Y-%m-%d")
        end_date_input = dt.datetime.strftime(enddate_entry, "%Y-%m-%d")

        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM BorrowedMember WHERE Borrowed_Date BETWEEN %s AND %s", (start_date_input, end_date_input))
        global reportdata
        reportdata = cursor.fetchall()
        cursor.close()
        report_table.delete(*report_table.get_children())
        for row in reportdata:
            report_table.insert('', 'end', values=row)

    #Produce the PDF
    def GeneratePDF():
        data_selected = defaultdict(list)
        for row in reportdata:
            borrowed_date = row[4] 
            month_year = borrowed_date.strftime("%B %Y")
            data_selected[month_year].append(row)

        for month, rows in data_selected.items():
            pdf = FPDF(orientation='L')
            pdf.set_auto_page_break(auto=True, margin=10)
            pdf.add_page()
            pdf.set_font("Times", size=12)

            # Add logo
            pdf.image("images/Logo-Pustaka-Negeri-Sarawak.png", x=5, y=7, w=40)  # Adjust the path and size as needed

            # Add title
            pdf.set_font("Times", size=16, style="B")  # Set font to bold and larger
            pdf.cell(0, 10, "Borrow History of Sarawak State Library", ln=True, align="C")
            pdf.ln(10)
            
            # Reset font to normal
            pdf.set_font("Times", size=16)
            pdf.cell(0, 10, start_date_input + "\tto\t" + end_date_input, ln=True, align="C")

            pdf.cell(0, 10, month, ln=True, align="C")
            pdf.ln(5)

            pdf.set_font("Times", size=12)

            # Add data
            for row in rows:
                pdf.cell(0, 10, f"IC: {row[0]}", ln=True)
                pdf.cell(0, 10, f"Name: {row[1]}", ln=True)
                pdf.cell(0, 10, f"ISBN: {row[2]}", ln=True)
                pdf.cell(0, 10, f"Book Title: {row[3]}", ln=True)
                pdf.cell(0, 10, f"Borrowed Date: {row[4].strftime('%Y-%m-%d') if row[4] else ''}", ln=True)
                pdf.cell(0, 10, f"Return Date: {row[6].strftime('%Y-%m-%d') if row[6] else ''}", ln=True)
                pdf.cell(0, 10, f"Due Date: {row[5].strftime('%Y-%m-%d') if row[5] else 'None'}", ln=True)
                pdf.cell(0, 10, f"Penalty (RM): {row[7]}", ln=True)
                pdf.cell(0, 10, f"Payment Condition: {row[8]}", ln=True)
                pdf.ln()
                y = pdf.get_y()  # Get current y position
                pdf.line(10, y, 290, y)  # Draw a line from left margin to right margin
                pdf.ln()

            base_filename = f"BorrowedMember_{start_date_input}-{end_date_input}.pdf"
            counter = 1
            pdf_filename = base_filename
            while os.path.exists(pdf_filename):  # Check if file already exists
                pdf_filename = f"BorrowedMember_{start_date_input}-{end_date_input}_{counter}.pdf"
                counter += 1
            pdf.output(pdf_filename)
            messagebox.showinfo("Success", "The record is generated to PDF.")

    from_label = ctk.CTkLabel(master=reportframe, text="From:", font=("Arial", 18))
    from_label.grid(row=1, column=0, padx=(40,0), pady=20, sticky="w")
    start_date = DateEntry(reportframe, selectmode="day", width=20, font=("Arial", 14))
    start_date.grid(row=1,column=1,padx=20,pady=20)

    to_label = ctk.CTkLabel(master=reportframe, text="To:", font=("Arial", 18))
    to_label.grid(row=1, column=2, padx=(40,0), pady=20, sticky="w")
    end_date = DateEntry(reportframe, selectmode="day", width=20, font=("Arial", 14))
    end_date.grid(row=1,column=3,padx=20,pady=20)

    view_btn = ctk.CTkButton(master=reportframe, text="View", font=("Arial", 18), width=100, height=30, corner_radius=100, command=GetDate)
    view_btn.grid(row=1, column=4, padx=20, pady=20)

    pdf_btn = ctk.CTkButton(master=reportframe, text="Generate PDF", font=("Arial", 18), width=100, height=30, corner_radius=100, command=GeneratePDF)
    pdf_btn.grid(row=6, column=19, padx=40, pady=20)

    global report_table
    report_table = ttk.Treeview(report_list,height=50, show="headings", selectmode="browse")
    report_table['column']=("IC","Name","ISBN","Book_Title","Borrowed_Date","Due_Date","Return_Date","Penalty","Payment_Condition")

    # Column
    report_table.column("#0",width=0,stretch=tk.NO) # Hide the default first column
    report_table.column("IC",anchor="w",width=130,minwidth=130)
    report_table.column("Name",anchor="w",width=150,minwidth=150)
    report_table.column("ISBN",anchor="w",width=120, minwidth=120)
    report_table.column("Book_Title",anchor="w",width=170, minwidth=170)
    report_table.column("Borrowed_Date",anchor="w",width=120, minwidth=120)
    report_table.column("Return_Date",anchor="w",width=120, minwidth=120)
    report_table.column("Due_Date",anchor="w",width=120, minwidth=120)
    report_table.column("Penalty",anchor="w",width=120, minwidth=120)
    report_table.column("Payment_Condition",anchor="w",width=130, minwidth=130)

    # Headings
    report_table.heading("IC", text="IC", anchor="w")
    report_table.heading("Name", text="Name", anchor="w")
    report_table.heading("ISBN", text="ISBN", anchor="w")
    report_table.heading("Book_Title", text="Book_Title", anchor="w")
    report_table.heading("Borrowed_Date", text="Borrow Date", anchor="w")
    report_table.heading("Return_Date", text="Return Date", anchor="w")
    report_table.heading("Due_Date", text="Due Date", anchor="w")
    report_table.heading("Penalty", text="Penalty (RM)", anchor="w")
    report_table.heading("Payment_Condition", text="Payment Condition", anchor="w")
    report_table.pack(fill="x")

#Create Main Frame (Admin Side)
def admin_menu():
    admin_home.lift()

    # Frame for admin menu
    global admin_mainframe
    admin_mainframe = ctk.CTkFrame(master=admin_home,fg_color="#2b2b2b")
    admin_mainframe.grid(row=0, column=1, rowspan=50, columnspan=50,sticky="nw")
    global admin_btnselection
    admin_btnselection = ctk.CTkFrame(master=admin_home)
    admin_btnselection.grid(row=0,column=0, rowspan=20)

    book_searchframe = ctk.CTkScrollableFrame(master= admin_mainframe, width=910, height=400)
    book_searchframe.grid(row=2, column=0, rowspan=18, columnspan=8, padx=30, pady=(30,50))

    # admin_menu navbar
    btn_width = 245
    borrow_book = ctk.CTkButton(master=admin_btnselection, text="Borrow", font=("Arial", 20), width=btn_width, height=40, corner_radius=100, command=borrow)
    borrow_book.grid(row=0,column=0,padx=30,pady=(40,10))
    return_book = ctk.CTkButton(master=admin_btnselection, text="Return", font=("Arial", 20), width=btn_width, height=40, corner_radius=100, command=returnbook)
    return_book.grid(row=1,column=0,padx=30,pady=(15,0))
    hr_line = ctk.CTkLabel(master=admin_btnselection, font=("Arial", 8), width=btn_width, height=40, text="_"*60, text_color="#808080")
    hr_line.grid(row=2,column=0)

    membermanagement_btn = ctk.CTkButton(master=admin_btnselection, text="Member Management",font=("Arial", 20), width=btn_width, height=40, corner_radius=100, command=member_management)
    membermanagement_btn.grid(row=3,column=0,padx=30,pady=15)
    catalogmanagement_btn = ctk.CTkButton(master=admin_btnselection, text="Catalog Management", font=("Arial", 20), width=btn_width, height=40, corner_radius=100, command=catalog_management)
    catalogmanagement_btn.grid(row=4,column=0,padx=30,pady=15)
    feemanagement_btn = ctk.CTkButton(master=admin_btnselection, text="Fee Management", font=("Arial", 20), width=btn_width, height=40, corner_radius=100,command=fees)
    feemanagement_btn.grid(row=5,column=0,padx=30,pady=15)
    discussionmanagement_btn = ctk.CTkButton(master=admin_btnselection, text="Discussion Rooms", font=("Arial", 20), width=btn_width, height=40, corner_radius=100,command=DiscussionRoomManagement)
    discussionmanagement_btn.grid(row=6,column=0,padx=30,pady=15)
    report_btn = ctk.CTkButton(master=admin_btnselection, text="Borrow Report", font=("Arial", 20), width=btn_width, height=40, corner_radius=100, command=Report)
    report_btn.grid(row=7,column=0,padx=30,pady=15)

    def admin_logout():
        logout = messagebox.askokcancel("Log Out","Log Out")
        if logout == True:
            back_startup()
            clear_borrowings_table()
            #Added
            if member_managementframe != None:
                member_managementframe.destroy()
            if catalog_managementframe != None:
                catalog_managementframe.destroy()
            if feesframe != None:
                feesframe.destroy()
            if borrowframe != None:
                borrowframe.destroy()
            if returnframe != None:
                returnframe.destroy()
            if room_managementframe != None:
                room_managementframe.destroy()

    logout_btn = ctk.CTkButton(master=admin_btnselection, text="Log Out", font=("Arial", 16, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=admin_logout) 
    logout_btn.grid(row=8,column=0,rowspan=2,padx=30,pady=60)

    # clock
    def current_time():
        display_time = time.strftime("%H:%M:%S %p")
        clock.configure(text=display_time)
        clock.after(1000, current_time)

    clock = ctk.CTkLabel(master=admin_mainframe, font=("Arial", 24))
    clock.grid(row=0, column=0, padx=40, pady=(30,50), sticky="w")
    current_time()
    date = ctk.CTkLabel(master=admin_mainframe, text=f"{current_date:%A, %B %d, %Y}", font=("Arial", 24))
    date.grid(row=0, column=1, pady=(30,50), sticky="w")
    
    #Search Book Bar
    def searchbooks():
        search_result = searchadmin_entry.get().title()
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT ISBN, Book_Title, Book_Author, Publisher, Genre, Language, Availability FROM books WHERE ISBN = '"+search_result+"' OR Book_Title LIKE '%"+search_result+"%' OR Book_Author LIKE '"+search_result+"%' OR Publisher LIKE '"+search_result+"%' OR Genre = '"+search_result+"' OR Language = '"+search_result+"' ORDER BY CASE WHEN Book_Title REGEXP CONCAT('"+search_result+"','%') THEN 1 ELSE 2 END DESC,LENGTH(Book_Title) DESC")
        
        book_search.delete(*book_search.get_children())
        book_search.insert('',0,text="",values=("No result found.","","","","","",""))

        i=0
        for ro in cursor:
            if search_result == "":
                book_search.delete(*book_search.get_children())
                book_search.insert('',0,text="",values=("No result found.","","","","","",""))
            else:
                book_search.insert('',i,text="",values=(ro[0],ro[1],ro[2],ro[3],ro[4],ro[5],ro[6]))
        cursor.close()  # Close the cursor after use
         
    searchadmin_entry = ctk.CTkEntry(master=admin_mainframe, placeholder_text="Search (Please include punctuation if there is any (e.g. , ! ?))", width=650, height=35)
    searchadmin_entry.grid(row=1, column=0, columnspan=5, padx=(35,0), sticky="w")
    searchadmin_btn = ctk.CTkButton(master=admin_mainframe, text="Search", font=("Arial", 18), corner_radius=100, height=35, command=searchbooks)
    searchadmin_btn.grid(row=1, column=5, padx=30, sticky="w")

    global book_search
    book_search = ttk.Treeview(book_searchframe,height=70,show="headings",selectmode="browse")
    book_search['column']=("ISBN","Book_Title","Book_Author","Publisher","Genre","Language","Availability")

    # Column
    book_search.column("#0",width=0,stretch=tk.NO) # Hide the default first column
    book_search.column("ISBN",anchor="w",width=150, minwidth=150)
    book_search.column("Book_Title",anchor="w",width=250, minwidth=250)
    book_search.column("Book_Author",anchor="w",width=150, minwidth=150)
    book_search.column("Publisher",anchor="w",width=180, minwidth=180)
    book_search.column("Genre",anchor="w",width=180, minwidth=180)
    book_search.column("Language",anchor="w",width=120, minwidth=120)
    book_search.column("Availability",anchor="w",width=120, minwidth=120)

    # Headings
    book_search.heading("ISBN", text="ISBN", anchor="w")
    book_search.heading("Book_Title", text="Book Title", anchor="w")
    book_search.heading("Book_Author", text="Author", anchor="w")
    book_search.heading("Publisher", text="Publisher", anchor="w")
    book_search.heading("Genre", text="Genre", anchor="w")
    book_search.heading("Language", text="Language", anchor="w")
    book_search.heading("Availability", text="Availability", anchor="w")
    book_search.pack(fill="x")

#Admin login function
def admin_login(): 
    admin_signinpage.lift()

    #Press enter to login in
    def onclick():
        if (admin_entry.get()!=adminID or password_entry.get()!=adminPIN):
            messagebox.showerror("Error","Invalid ID or password.")
        else:
            admin_menu()
    
    #Press enter to go to the password entry
    def admin_login_on_enter(event=None, entry=None):
        if entry is None:
            entry = admin_entry
        else:
            entry.tk_focusNext().focus_set()
    
    back_btn = ctk.CTkButton(master=admin_signinpage, text="Back", font=("Arial", 16, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838",command=back_startup) 
    back_btn.place(relx=0.03,rely=0.03)

    login = ctk.CTkLabel(master=admin_signinpage, text="Admin", font=("Arial", 32, "bold"))
    login.place(relx=0.5, rely=0.25, anchor=ctk.CENTER)

    admin_label = ctk.CTkLabel(master=admin_signinpage, text="Admin ID:", font=("Arial", 16))
    admin_label.place(relx=0.15, rely=0.4)
    admin_entry = ctk.CTkEntry(master=admin_signinpage)
    admin_entry.place(relx=0.5, rely=0.4)

    password_label = ctk.CTkLabel(master=admin_signinpage, text="Password:", font=("Arial", 16))
    password_label.place(relx=0.15, rely=0.5)
    password_entry = ctk.CTkEntry(master=admin_signinpage, show="*")
    password_entry.place(relx=0.5, rely=0.5)

    login_button = ctk.CTkButton(master=admin_signinpage, text="Sign In", font=("Arial", 20), height=40, command=onclick, corner_radius=100)
    login_button.place(relx=0.5, rely=0.75, anchor=ctk.CENTER)

    admin_entry.bind('<Return>', lambda event: admin_login_on_enter(entry=password_entry))
    password_entry.bind('<Return>', lambda event: onclick())

#Create Trending Frame(Member Side)
def TrendingBooks():
    #Destroy frame during changing of the frame
    member_mainframe.destroy()
    global trendingbookframe
    if bookmanagerframe != None:
        bookmanagerframe.destroy()
    if borrowhistoryframe != None:
        borrowhistoryframe.destroy()
    if personalinfoframe != None:
        personalinfoframe.destroy()
    if discussionroomframe != None:
        discussionroomframe.destroy()
    if trendingbookframe != None:
        trendingbookframe.destroy()

    # Frame
    trendingbookframe = ctk.CTkFrame(master=member_home, fg_color="#2b2b2b")
    trendingbookframe.grid(row=0, column=1, rowspan=50, columnspan=50,sticky="nw")

    # home
    def BackToHome():
        trendingbookframe.grid_forget()
        member_menu()
    
    memberhome_btn = ctk.CTkButton(master=trendingbookframe, text="\U0001F3E0 Home", font=("Arial", 20, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=BackToHome)
    memberhome_btn.place(relx=0.88,rely=0.04)

    title_label = ctk.CTkLabel(master=trendingbookframe, text="Monthly Trending Books",font=("Arial", 24, "bold"))
    title_label.grid(row=0, column=0, padx=40, columnspan=5, pady=(30,20), sticky="w")

    #Display top 5 genre
    def top5genre():
        current_date = dt.date.today()
        start_of_month = current_date.replace(day=1)
        end_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1) - dt.timedelta(days=1)
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT b.Genre, COUNT(*) AS num_borrowed FROM borrowedmember AS a INNER JOIN books AS b ON a.isbn = b.isbn WHERE a.Borrowed_Date BETWEEN %s AND %s GROUP BY b.genre ORDER BY num_borrowed DESC",(start_of_month,end_of_month))
        genre_top5 = cursor.fetchall()

        category_labels = [category1, category2, category3, category4, category5]
        for i in range(min(len(genre_top5), 5)):
            category_labels[i].configure(text=genre_top5[i][0])
        
        cursor.close()
        connection.commit()

    #Display top 5 book title for first genre
    def Top5genre1():
        current_date = dt.date.today()
        start_of_month = current_date.replace(day=1)
        end_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1) - dt.timedelta(days=1)

        global connection
        if not connection or not connection.is_connected():
            connection = connect()

        cursor = connection.cursor()

        cursor.execute("SELECT b.Genre, COUNT(*) AS num_borrowed FROM borrowedmember AS a INNER JOIN books AS b ON a.isbn = b.isbn WHERE a.Borrowed_Date BETWEEN %s AND %s GROUP BY b.genre ORDER BY num_borrowed DESC",(start_of_month,end_of_month))
        genre_top5 = cursor.fetchall()

        cursor.execute("SELECT b.book_title, COUNT(*) AS num_borrowed FROM borrowedmember AS a INNER JOIN books AS b ON a.isbn = b.isbn WHERE Genre = %s AND a.Borrowed_Date BETWEEN %s AND %s GROUP BY b.book_title ORDER BY num_borrowed DESC",(genre_top5[0][0], start_of_month, end_of_month))
        top_genre_books = cursor.fetchall()

        topfiveframe = ctk.CTkFrame(master=trendingbookframe, fg_color="#2b2b2b")
        topfiveframe.grid(row=1, column=0, rowspan=50, columnspan=50,sticky="nw")

        #back to the top5 genre
        def back_books():
            topfiveframe.destroy()
            back_btn.destroy()

        back_btn = ctk.CTkButton(master=trendingbookframe, text="\U0001F4DA Back", font=("Arial", 20, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=back_books) 
        back_btn.place(relx=0.78,rely=0.04)

        top1 = ctk.CTkLabel(master=topfiveframe, text="Top1", font=("Arial", 20,"bold"), height=250, width=200, fg_color="blue", corner_radius=10,wraplength=180)
        top1.grid(row=1, column=0, padx=100, pady=25, sticky="w")
        top2 = ctk.CTkLabel(master=topfiveframe, text="Top2", font=("Arial", 20,"bold"), height=250, width=200, fg_color="darkorange",corner_radius=10,wraplength=180)
        top2.grid(row=1, column=1, pady=25, sticky="w")
        top3 = ctk.CTkLabel(master=topfiveframe, text="Top3", font=("Arial", 20,"bold"), height=250, width=200, fg_color="deeppink",corner_radius=10,wraplength=180)
        top3.grid(row=1, column=2, padx=100, pady=25, sticky="w")
        top4 = ctk.CTkLabel(master=topfiveframe, text="Top4", font=("Arial", 20,"bold"), height=250, width=200, fg_color="plum",corner_radius=10,wraplength=180)
        top4.grid(row=2, column=0, columnspan=2, pady=25)
        top5 = ctk.CTkLabel(master=topfiveframe, text="Top5", font=("Arial", 20,"bold"), height=250, width=200,fg_color="darkturquoise",corner_radius=10,wraplength=180)
        top5.grid(row=2, column=1, columnspan=2, pady=25)

        top_labels = [top1, top2, top3, top4, top5]

        for i, (book_title, _) in enumerate(top_genre_books[:5]):
            top_label = top_labels[i]
            top_label.configure(text=book_title)

    #Display top 5 book title for second genre
    def Top5genre2():
        current_date = dt.date.today()
        start_of_month = current_date.replace(day=1)
        end_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1) - dt.timedelta(days=1)

        global connection
        if not connection or not connection.is_connected():
            connection = connect()

        cursor = connection.cursor()

        cursor.execute("SELECT b.Genre, COUNT(*) AS num_borrowed FROM borrowedmember AS a INNER JOIN books AS b ON a.isbn = b.isbn WHERE a.Borrowed_Date BETWEEN %s AND %s GROUP BY b.genre ORDER BY num_borrowed DESC",(start_of_month,end_of_month))
        genre_top5 = cursor.fetchall()

        cursor.execute("SELECT b.book_title, COUNT(*) AS num_borrowed FROM borrowedmember AS a INNER JOIN books AS b ON a.isbn = b.isbn WHERE Genre = %s AND a.Borrowed_Date BETWEEN %s AND %s GROUP BY b.book_title ORDER BY num_borrowed DESC",(genre_top5[1][0], start_of_month, end_of_month))
        top_genre_books = cursor.fetchall()

        topfiveframe = ctk.CTkFrame(master=trendingbookframe, fg_color="#2b2b2b")
        topfiveframe.grid(row=1, column=0, rowspan=50, columnspan=50,sticky="nw")

        #back to the top5 genre
        def back_books():
            topfiveframe.destroy()
            back_btn.destroy()

        back_btn = ctk.CTkButton(master=trendingbookframe, text="\U0001F4DA Back", font=("Arial", 20, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=back_books) 
        back_btn.place(relx=0.78,rely=0.04)

        top1 = ctk.CTkLabel(master=topfiveframe, text="Top1", font=("Arial", 20,"bold"), height=250, width=200, fg_color="blue", corner_radius=10, wraplength=180)
        top1.grid(row=1, column=0, padx=100, pady=25, sticky="w")
        top2 = ctk.CTkLabel(master=topfiveframe, text="Top2", font=("Arial", 20,"bold"), height=250, width=200, fg_color="darkorange",corner_radius=10, wraplength=180)
        top2.grid(row=1, column=1, pady=25, sticky="w")
        top3 = ctk.CTkLabel(master=topfiveframe, text="Top3", font=("Arial", 20,"bold"), height=250, width=200, fg_color="deeppink",corner_radius=10, wraplength=180)
        top3.grid(row=1, column=2, padx=100, pady=25, sticky="w")
        top4 = ctk.CTkLabel(master=topfiveframe, text="Top4", font=("Arial", 20,"bold"), height=250, width=200, fg_color="plum",corner_radius=10, wraplength=180)
        top4.grid(row=2, column=0, columnspan=2, pady=25)
        top5 = ctk.CTkLabel(master=topfiveframe, text="Top5", font=("Arial", 20,"bold"), height=250, width=200,fg_color="darkturquoise",corner_radius=10, wraplength=180)
        top5.grid(row=2, column=1, columnspan=2, pady=25)

        top_labels = [top1, top2, top3, top4, top5]

        for i, (book_title, _) in enumerate(top_genre_books[:5]):
            top_label = top_labels[i]
            top_label.configure(text=book_title)

    #Display top 5 book title for third genre
    def Top5genre3():
        current_date = dt.date.today()
        start_of_month = current_date.replace(day=1)
        end_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1) - dt.timedelta(days=1)

        global connection
        if not connection or not connection.is_connected():
            connection = connect()

        cursor = connection.cursor()

        cursor.execute("SELECT b.Genre, COUNT(*) AS num_borrowed FROM borrowedmember AS a INNER JOIN books AS b ON a.isbn = b.isbn WHERE a.Borrowed_Date BETWEEN %s AND %s GROUP BY b.genre ORDER BY num_borrowed DESC",(start_of_month,end_of_month))
        genre_top5 = cursor.fetchall()

        cursor.execute("SELECT b.book_title, COUNT(*) AS num_borrowed FROM borrowedmember AS a INNER JOIN books AS b ON a.isbn = b.isbn WHERE Genre = %s AND a.Borrowed_Date BETWEEN %s AND %s GROUP BY b.book_title ORDER BY num_borrowed DESC",(genre_top5[2][0], start_of_month, end_of_month))
        top_genre_books = cursor.fetchall()

        topfiveframe = ctk.CTkFrame(master=trendingbookframe, fg_color="#2b2b2b")
        topfiveframe.grid(row=1, column=0, rowspan=50, columnspan=50,sticky="nw")

        #back to the top5 genre
        def back_books():
            topfiveframe.destroy()
            back_btn.destroy()

        back_btn = ctk.CTkButton(master=trendingbookframe, text="\U0001F4DA Back", font=("Arial", 20, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=back_books) 
        back_btn.place(relx=0.78,rely=0.04)

        top1 = ctk.CTkLabel(master=topfiveframe, text="Top1", font=("Arial", 20,"bold"), height=250, width=200, fg_color="blue", corner_radius=10, wraplength=180)
        top1.grid(row=1, column=0, padx=100, pady=25, sticky="w")
        top2 = ctk.CTkLabel(master=topfiveframe, text="Top2", font=("Arial", 20,"bold"), height=250, width=200, fg_color="darkorange",corner_radius=10, wraplength=180)
        top2.grid(row=1, column=1, pady=25, sticky="w")
        top3 = ctk.CTkLabel(master=topfiveframe, text="Top3", font=("Arial", 20,"bold"), height=250, width=200, fg_color="deeppink",corner_radius=10,wraplength=180)
        top3.grid(row=1, column=2, padx=100, pady=25, sticky="w")
        top4 = ctk.CTkLabel(master=topfiveframe, text="Top4", font=("Arial", 20,"bold"), height=250, width=200, fg_color="plum",corner_radius=10,wraplength=180)
        top4.grid(row=2, column=0, columnspan=2, pady=25)
        top5 = ctk.CTkLabel(master=topfiveframe, text="Top5", font=("Arial", 20,"bold"), height=250, width=200,fg_color="darkturquoise",corner_radius=10,wraplength=180)
        top5.grid(row=2, column=1, columnspan=2, pady=25)

        top_labels = [top1, top2, top3, top4, top5]

        for i, (book_title, _) in enumerate(top_genre_books[:5]):
            top_label = top_labels[i]
            top_label.configure(text=book_title)

    #Display top 5 book title for fourth genre
    def Top5genre4():
        current_date = dt.date.today()
        start_of_month = current_date.replace(day=1)
        end_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1) - dt.timedelta(days=1)

        global connection
        if not connection or not connection.is_connected():
            connection = connect()

        cursor = connection.cursor()

        cursor.execute("SELECT b.Genre, COUNT(*) AS num_borrowed FROM borrowedmember AS a INNER JOIN books AS b ON a.isbn = b.isbn WHERE a.Borrowed_Date BETWEEN %s AND %s GROUP BY b.genre ORDER BY num_borrowed DESC",(start_of_month,end_of_month))
        genre_top5 = cursor.fetchall()

        cursor.execute("SELECT b.book_title, COUNT(*) AS num_borrowed FROM borrowedmember AS a INNER JOIN books AS b ON a.isbn = b.isbn WHERE Genre = %s AND a.Borrowed_Date BETWEEN %s AND %s GROUP BY b.book_title ORDER BY num_borrowed DESC",(genre_top5[3][0], start_of_month, end_of_month))
        top_genre_books = cursor.fetchall()

        topfiveframe = ctk.CTkFrame(master=trendingbookframe, fg_color="#2b2b2b")
        topfiveframe.grid(row=1, column=0, rowspan=50, columnspan=50,sticky="nw")

        #back to the top5 genre
        def back_books():
            topfiveframe.destroy()
            back_btn.destroy()

        back_btn = ctk.CTkButton(master=trendingbookframe, text="\U0001F4DA Back", font=("Arial", 20, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=back_books) 
        back_btn.place(relx=0.78,rely=0.04)

        top1 = ctk.CTkLabel(master=topfiveframe, text="Top1", font=("Arial", 20,"bold"), height=250, width=200, fg_color="blue", corner_radius=10, wraplength=180)
        top1.grid(row=1, column=0, padx=100, pady=25, sticky="w")
        top2 = ctk.CTkLabel(master=topfiveframe, text="Top2", font=("Arial", 20,"bold"), height=250, width=200, fg_color="darkorange",corner_radius=10, wraplength=180)
        top2.grid(row=1, column=1, pady=25, sticky="w")
        top3 = ctk.CTkLabel(master=topfiveframe, text="Top3", font=("Arial", 20,"bold"), height=250, width=200, fg_color="deeppink",corner_radius=10, wraplength=180)
        top3.grid(row=1, column=2, padx=100, pady=25, sticky="w")
        top4 = ctk.CTkLabel(master=topfiveframe, text="Top4", font=("Arial", 20,"bold"), height=250, width=200, fg_color="plum",corner_radius=10, wraplength=180)
        top4.grid(row=2, column=0, columnspan=2, pady=25)
        top5 = ctk.CTkLabel(master=topfiveframe, text="Top5", font=("Arial", 20,"bold"), height=250, width=200,fg_color="darkturquoise",corner_radius=10, wraplength=180)
        top5.grid(row=2, column=1, columnspan=2, pady=25)

        top_labels = [top1, top2, top3, top4, top5]

        for i, (book_title, _) in enumerate(top_genre_books[:5]):
            top_label = top_labels[i]
            top_label.configure(text=book_title)

    #Display top 5 book title for fifth genre
    def Top5genre5():
        current_date = dt.date.today()
        start_of_month = current_date.replace(day=1)
        end_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1) - dt.timedelta(days=1)

        global connection
        if not connection or not connection.is_connected():
            connection = connect()

        cursor = connection.cursor()

        cursor.execute("SELECT b.Genre, COUNT(*) AS num_borrowed FROM borrowedmember AS a INNER JOIN books AS b ON a.isbn = b.isbn WHERE a.Borrowed_Date BETWEEN %s AND %s GROUP BY b.genre ORDER BY num_borrowed DESC",(start_of_month,end_of_month))
        genre_top5 = cursor.fetchall()

        cursor.execute("SELECT b.book_title, COUNT(*) AS num_borrowed FROM borrowedmember AS a INNER JOIN books AS b ON a.isbn = b.isbn WHERE Genre = %s AND a.Borrowed_Date BETWEEN %s AND %s GROUP BY b.book_title ORDER BY num_borrowed DESC",(genre_top5[4][0], start_of_month, end_of_month))
        top_genre_books = cursor.fetchall()
        
        topfiveframe = ctk.CTkFrame(master=trendingbookframe, fg_color="#2b2b2b")
        topfiveframe.grid(row=1, column=0, rowspan=50, columnspan=50,sticky="nw")

        #back to the top5 genre
        def back_books():
            topfiveframe.destroy()
            back_btn.destroy()

        back_btn = ctk.CTkButton(master=trendingbookframe, text="\U0001F4DA Back", font=("Arial", 20, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=back_books) 
        back_btn.place(relx=0.78,rely=0.04)

        top1 = ctk.CTkLabel(master=topfiveframe, text="Top1", font=("Arial", 20,"bold"), height=250, width=200, fg_color="blue", corner_radius=10, wraplength=180)
        top1.grid(row=1, column=0, padx=100, pady=25, sticky="w")
        top2 = ctk.CTkLabel(master=topfiveframe, text="Top2", font=("Arial", 20,"bold"), height=250, width=200, fg_color="darkorange",corner_radius=10, wraplength=180)
        top2.grid(row=1, column=1, pady=25, sticky="w")
        top3 = ctk.CTkLabel(master=topfiveframe, text="Top3", font=("Arial", 20,"bold"), height=250, width=200, fg_color="deeppink",corner_radius=10, wraplength=180)
        top3.grid(row=1, column=2, padx=100, pady=25, sticky="w")
        top4 = ctk.CTkLabel(master=topfiveframe, text="Top4", font=("Arial", 20,"bold"), height=250, width=200, fg_color="plum",corner_radius=10, wraplength=180)
        top4.grid(row=2, column=0, columnspan=2, pady=25)
        top5 = ctk.CTkLabel(master=topfiveframe, text="Top5", font=("Arial", 20,"bold"), height=250, width=200,fg_color="darkturquoise",corner_radius=10, wraplength=180)
        top5.grid(row=2, column=1, columnspan=2, pady=25)    

        top_labels = [top1, top2, top3, top4, top5]

        for i, (book_title, _) in enumerate(top_genre_books[:5]):
            top_label = top_labels[i]
            top_label.configure(text=book_title)

    category1 = ctk.CTkButton(master=trendingbookframe, text="Category1", font=("Arial", 20, "bold"), height=250, width=200, command=Top5genre1)
    category1.grid(row=1, column=0, padx=100, pady=25, sticky="w")
    category2 = ctk.CTkButton(master=trendingbookframe, text="Category2", font=("Arial", 20, "bold"), height=250, width=200, command=Top5genre2)
    category2.grid(row=1, column=1, pady=25, sticky="w")
    category3 = ctk.CTkButton(master=trendingbookframe, text="Category3", font=("Arial", 20, "bold"), height=250, width=200, command=Top5genre3)
    category3.grid(row=1, column=2, padx=100, pady=25, sticky="w")
    category4 = ctk.CTkButton(master=trendingbookframe, text="Category4", font=("Arial", 20, "bold"), height=250, width=200, command=Top5genre4)
    category4.grid(row=2, column=0, columnspan=2, pady=25)
    category5 = ctk.CTkButton(master=trendingbookframe, text="Category5", font=("Arial", 20, "bold"), height=250, width=200, command=Top5genre5)
    category5.grid(row=2, column=1, columnspan=2, pady=25)
    top5genre()

#Create discussionroombooking(Member Side)
def DiscussionRoomBooking():
    member_mainframe.destroy()
    global discussionroomframe
    if bookmanagerframe != None:
        bookmanagerframe.destroy()
    if borrowhistoryframe != None:
        borrowhistoryframe.destroy()
    if personalinfoframe != None:
        personalinfoframe.destroy()
    if discussionroomframe != None:
        discussionroomframe.destroy()
    if trendingbookframe != None:
        trendingbookframe.destroy()
    
    # Frame
    discussionroomframe = ctk.CTkFrame(master=member_home,fg_color="#2b2b2b")
    discussionroomframe.grid(row=0, column=1, rowspan=50, columnspan=50,sticky="nw")

    # home
    def BackToHome():
        discussionroomframe.grid_forget()
        member_menu()

    memberhome_btn = ctk.CTkButton(master=discussionroomframe, text="\U0001F3E0 Home", font=("Arial", 20, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=BackToHome) 
    memberhome_btn.place(relx=0.88,rely=0.04)

    title_label = ctk.CTkLabel(master=discussionroomframe, text="Discussion Rooms",font=("Arial", 24, "bold"))
    title_label.grid(row=0, column=0, padx=40, columnspan=5, pady=(30,20), sticky="w")

    #Get date for the booking
    def GetBookingDate():
        bookingdate = select_date.get_date()
        start_time = dt.datetime.strptime(timeclicked1.get(), "%H:%M").time()
        end_time = dt.datetime.strptime(timeclicked2.get(), "%H:%M").time()
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT Room, Start_Time, End_Time FROM BookingRoom WHERE Date = %s", (bookingdate,))
        booking_result = cursor.fetchall()
        room1_booked = False
        room2_booked = False
        room3_booked = False
        for result in booking_result:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM BookingRoom WHERE Date=%s AND (Start_Time < %s AND End_Time > %s) AND Room='Room1'", (bookingdate,end_time,start_time))
            room1_confirmation=cursor.fetchall()
            if room1_confirmation:
                room1_booked = True
            
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM BookingRoom WHERE Date=%s AND (Start_Time < %s AND End_Time > %s) AND Room='Room2'", (bookingdate,end_time,start_time))
            room2_confiramtion=cursor.fetchall()
            if room2_confiramtion:
                room2_booked = True

            cursor = connection.cursor()
            cursor.execute("SELECT * FROM BookingRoom WHERE Date=%s AND (Start_Time < %s AND End_Time > %s) AND Room='Room3'", (bookingdate,end_time,start_time))
            room3_confiramtion=cursor.fetchall()
            if room3_confiramtion:
                room3_booked = True
                  
        if end_time<=start_time:
            messagebox.showerror("Error","Invalid booking!")
            room1_booked = True
            room2_booked = True
            room3_booked = True
    
        cursor.execute("SELECT * FROM room WHERE Availability ='Not Available' AND Room='Room1'")
        room1_mantainanence=cursor.fetchone()
        if room1_mantainanence:
            disroom1_status.configure(fg_color="grey")
            discussionroom1.configure(state="disabled")
        else:
            if not room1_booked:
                disroom1_status.configure(fg_color="green")
                discussionroom1.configure(state="normal")
            else:
                disroom1_status.configure(fg_color="red")
                discussionroom1.configure(state="disabled")
        
        cursor.execute("SELECT * FROM room WHERE Availability ='Not Available' AND Room='Room2'")
        room2_mantainanence=cursor.fetchone()
        if room2_mantainanence:
            disroom2_status.configure(fg_color="grey")
            discussionroom2.configure(state="disabled")
        else:
            if not room2_booked:
                disroom2_status.configure(fg_color="green")
                discussionroom2.configure(state="normal")
            else:
                disroom2_status.configure(fg_color="red")
                discussionroom2.configure(state="disabled")
        

        cursor.execute("SELECT * FROM room WHERE Availability ='Not Available' AND Room='Room3'")
        room3_mantainanence=cursor.fetchone()
        if room3_mantainanence:
            disroom3_status.configure(fg_color="grey")
            discussionroom3.configure(state="disabled")
        else:
            if not room3_booked:
                disroom3_status.configure(fg_color="green")
                discussionroom3.configure(state="normal")
            else:
                disroom3_status.configure(fg_color="red")
                discussionroom3.configure(state="disabled")
        connection.commit()
        cursor.close()

    #Book Room1
    def BookRoom1():
        room_selection.set("Room1")
        bookingdate = select_date.get_date()
        start_time = timeclicked1.get()
        end_time = timeclicked2.get()
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM BookingRoom WHERE Date = %s AND Start_Time = %s AND End_Time=%s AND Room='Room1'", (bookingdate, start_time,end_time,))
        room1_confiramtion=cursor.fetchone()
        if room1_confiramtion:
            messagebox.showinfo("Info","The room is booked")
            return
        else:
            if int(end_time[0:2]) < int(start_time[0:2]):
                messagebox.showerror("Error","Please input valid time selection.")
            else:
                agree = messagebox.askyesno("Discussion Room","Are you sure you want to book the room?")
                if agree:
                    cursor.execute("SELECT Name FROM PersonalInformation WHERE IC = %s", (ic,))
                    name = cursor.fetchone()[0]
                    cursor.execute("INSERT INTO BookingRoom (IC, Name, Room, Start_Time, End_Time, Date) VALUES (%s, %s, %s, %s, %s, %s)", (ic, name, room_selection.get(), start_time, end_time, bookingdate))
                    connection.commit()
                    cursor.close()
                    messagebox.showinfo("Discussion Room","You have successfully booked the room.")
                    disroom1_status.configure(fg_color="red")
                    discussionroom1.configure(state="disabled")
                else:
                    None

    #Book Room2
    def BookRoom2():
        room_selection.set("Room2")
        bookingdate = select_date.get_date()
        start_time = timeclicked1.get()
        end_time = timeclicked2.get()
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM BookingRoom WHERE Date = %s AND Start_Time = %s AND End_Time=%s AND Room='Room2'", (bookingdate,start_time,end_time,))
        room2_confiramtion=cursor.fetchone()
        if room2_confiramtion:
            messagebox.showinfo("Info","The room is booked")
            return
        else:
            if int(end_time[0:2]) < int(start_time[0:2]):
                messagebox.showerror("Error","Please input valid time selection.")
            else:
                agree = messagebox.askyesno("Discussion Room","Are you sure you want to book the room?")
                if agree:
                    cursor.execute("SELECT Name FROM PersonalInformation WHERE IC = %s", (ic,))
                    name = cursor.fetchone()[0]
                    cursor.execute("INSERT INTO BookingRoom (IC, Name, Room, Start_Time, End_Time, Date) VALUES (%s, %s, %s, %s, %s, %s)", (ic, name, room_selection.get(), start_time, end_time, bookingdate))
                    connection.commit()
                    cursor.close()
                    messagebox.showinfo("Discussion Room","You have successfully booked the room.")
                    disroom2_status.configure(fg_color="red")
                    discussionroom2.configure(state="disabled")
                else:
                    None
    
    #Book Room3
    def BookRoom3():
        room_selection.set("Room3")
        bookingdate = select_date.get_date()
        start_time = timeclicked1.get()
        end_time = timeclicked2.get()
        global connection
        if not connection or not connection.is_connected():
            connection = connect() # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM BookingRoom WHERE Date = %s AND Start_Time = %s AND End_Time=%s AND Room='Room3'", (bookingdate, start_time,end_time,))
        room3_confiramtion=cursor.fetchone()
        if room3_confiramtion:
            messagebox.showinfo("Info","The room is booked")
            return
        else:
            if int(end_time[0:2]) < int(start_time[0:2]):
                messagebox.showerror("Error","Please input valid time selection.")
            else:
                agree = messagebox.askyesno("Discussion Room","Are you sure you want to book the room?")
                if agree:
                    cursor.execute("SELECT Name FROM PersonalInformation WHERE IC = %s", (ic,))
                    name = cursor.fetchone()[0]
                    cursor.execute("INSERT INTO BookingRoom (IC, Name, Room, Start_Time, End_Time, Date) VALUES (%s, %s, %s, %s, %s, %s)", (ic, name, room_selection.get(), start_time, end_time, bookingdate))
                    connection.commit()
                    cursor.close()
                    messagebox.showinfo("Discussion Room","You have successfully booked the room.")
                    disroom3_status.configure(fg_color="red")
                    discussionroom3.configure(state="disabled")
                else:
                    None
        
    dt_current = dt.datetime.now()
    dt_max = dt.datetime.now()+dt.timedelta(days=7)
    date_label = ctk.CTkLabel(master=discussionroomframe, text="Date:", font=("Arial", 18))
    date_label.grid(row=1, column=0, padx=(40,0), pady=20, sticky="w")
    select_date = DateEntry(discussionroomframe, selectmode="day", width=19, font=("Arial", 14),mindate=dt_current,maxdate=dt_max)
    select_date.grid(row=1,column=1, columnspan=2, padx=40,pady=20)

    timeoption1 = ["09:00","10:00", "11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00"]
    timeclicked1 = ctk.StringVar()
    timeclicked1.set(timeoption1[0])
    timeoption2 = ["10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00"]
    timeclicked2 = ctk.StringVar()
    timeclicked2.set(timeoption2[0])

    time_label = ctk.CTkLabel(master=discussionroomframe, text="Time:", font=("Arial", 18))
    time_label.grid(row=1, column=3, pady=20, sticky="w")
    timedropdown1 = ctk.CTkOptionMenu(master=discussionroomframe, values=timeoption1, variable=timeclicked1, width=150, height=30, font=("Arial", 16),fg_color="#363838")
    timedropdown1.grid(row=1, column=4, padx=(40,20), pady=20, sticky="w")
    timerange_label = ctk.CTkLabel(master=discussionroomframe, text="-", font=("Arial", 18))
    timerange_label.grid(row=1, column=5, pady=20)
    timedropdown2 = ctk.CTkOptionMenu(master=discussionroomframe, values=timeoption2, variable=timeclicked2, width=150, height=30, font=("Arial", 16),fg_color="#363838")
    timedropdown2.grid(row=1, column=6, padx=(20,40), pady=20, sticky="w")

    proceed_btn = ctk.CTkButton(master=discussionroomframe, text="Proceed", font=("Arial", 18), corner_radius=100, height=35, command=GetBookingDate)
    proceed_btn.grid(row=1, column=7, pady=20, sticky="w")

    price_label = ctk.CTkLabel(master=discussionroomframe, text="Small Room: RM5 / hour\tBig Room: RM10 / hour", font=("Arial", 18))
    price_label.grid(row=2,column=0,columnspan=10,padx=40,sticky="w")

    room_selection = ctk.StringVar()
    room_selection.set("")
    # Discussion Rooms
    discussionroom1_image = ctk.CTkImage(Image.open("images/smallroom.png"), size=(250, 450))
    discussionroom1=ctk.CTkButton(master=discussionroomframe, text="", font=("Arial", 18), image=discussionroom1_image, fg_color="#333333", hover_color="#3F3F3F",command=BookRoom1)
    discussionroom1.grid(row=3, column=0, columnspan=3, padx=(30,20), pady=20)
    disroom1_label=ctk.CTkLabel(master=discussionroomframe, text="Discussion Room 1", font=("Arial", 18), fg_color="#333333")
    disroom1_label.grid(row=3,column=0,columnspan=3,pady=35, sticky="n")
    disroom1_status = ctk.CTkLabel(master=discussionroomframe, text="",width=30,height=30,corner_radius=100,fg_color="grey",bg_color="#333333")
    disroom1_status.grid(row=3,column=0,columnspan=3,padx=(10,0))

    discussionroom2_image = ctk.CTkImage(Image.open("images/smallroom.png"), size=(250, 450))
    discussionroom2=ctk.CTkButton(master=discussionroomframe, text="", font=("Arial", 18), image=discussionroom2_image, fg_color="#333333", hover_color="#3F3F3F",command=BookRoom2)
    discussionroom2.grid(row=3, column=3, columnspan=2, pady=20)
    disroom2_label=ctk.CTkLabel(master=discussionroomframe, text="Discussion Room 2", font=("Arial", 18), fg_color="#333333")
    disroom2_label.grid(row=3,column=3,columnspan=2,pady=35, sticky="n")
    disroom2_status = ctk.CTkLabel(master=discussionroomframe, text="",width=30,height=30,corner_radius=100,fg_color="grey",bg_color="#333333")
    disroom2_status.grid(row=3,column=3,columnspan=2,padx=(5,0))

    discussionroom3_image = ctk.CTkImage(Image.open("images/bigroom.png"), size=(350, 450))
    discussionroom3=ctk.CTkButton(master=discussionroomframe, font=("Arial", 18), image=discussionroom3_image, text="", fg_color="#333333", hover_color="#3F3F3F",command=BookRoom3)
    discussionroom3.grid(row=3, column=6, columnspan=6, padx=(20,30), pady=20)
    disroom3_label=ctk.CTkLabel(master=discussionroomframe, text="Discussion Room 3", font=("Arial", 18), fg_color="#333333")
    disroom3_label.grid(row=3,column=6,columnspan=6,pady=35, sticky="n")
    disroom3_status = ctk.CTkLabel(master=discussionroomframe, text="",width=30,height=30,corner_radius=100,fg_color="grey",bg_color="#333333")
    disroom3_status.grid(row=3,column=6,columnspan=6,padx=(0,5))

    discussionroom1.configure(state="disabled")
    discussionroom2.configure(state="disabled")
    discussionroom3.configure(state="disabled")

# Create the Personal Info Frame(Member Side)
def PersonalInfo():
    #Destroy the frame during the changing of the frame
    member_mainframe.destroy()
    global personalinfoframe
    if bookmanagerframe != None:
        bookmanagerframe.destroy()
    if borrowhistoryframe != None:
        borrowhistoryframe.destroy()
    if personalinfoframe != None:
        personalinfoframe.destroy()
    if discussionroomframe != None:
        discussionroomframe.destroy()
    if trendingbookframe != None:
        trendingbookframe.destroy()

    # Frame
    personalinfoframe = ctk.CTkFrame(master=member_home,fg_color="#2b2b2b")
    personalinfoframe.grid(row=0, column=1, rowspan=50, columnspan=50,sticky="nw")

    # home
    def BackToHome():
        personalinfoframe.grid_forget()
        member_menu()

    memberhome_btn = ctk.CTkButton(master=personalinfoframe, text="\U0001F3E0 Home", font=("Arial", 20, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=BackToHome) 
    memberhome_btn.place(relx=0.88,rely=0.04)

    title_label = ctk.CTkLabel(master=personalinfoframe, text="Personal Information",font=("Arial", 24, "bold"))
    title_label.grid(row=0, column=0, padx=40, columnspan=5, pady=(30,20), sticky="w")

    #Display Personal Info
    def SearchPersonalInfoData():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT IC, Name, Email, Contact, Address,Membership_Status FROM PersonalInformation WHERE IC = %s", (ic,))
        member_personal_info = cursor.fetchone()
        cursor.execute("SELECT End_Membership_Date FROM Membership WHERE IC = %s", (ic,))
        membershipdue = cursor.fetchone()
        if member_personal_info:   
            ic_entry.configure(text=member_personal_info[0])
            name_entry.delete(0, "end")
            name_entry.insert(0,member_personal_info[1])
            email_entry.delete(0, "end")
            email_entry.insert(0,member_personal_info[2])
            contact_entry.delete(0, "end")
            contact_entry.insert(0,member_personal_info[3])
            address_entry.delete("1.0", "end")
            address_entry.insert("0.0",member_personal_info[4])
            membership_display.configure(text=member_personal_info[5])
        if membershipdue:
            membership_due.configure(text=membershipdue)
    
    #Update the Personal Info
    def UpdatePersonalInfo():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("UPDATE PersonalInformation SET Name =%s,Email=%s,Contact=%s,Address=%s WHERE IC = %s ", (name_entry.get(),email_entry.get(),contact_entry.get(),address_entry.get("0.0", "end-1c"),ic))
        connection.commit()
        cursor.close()  # Close the cursor after use
        messagebox.showinfo("Success", "Personal info has been updated successfully.")
        SearchPersonalInfoData()

    ic_label = ctk.CTkLabel(master=personalinfoframe, text="IC: ",font=("Arial", 18))
    ic_label.grid(row=1, column=0, padx=40, pady=10, sticky="w")
    ic_entry = ctk.CTkLabel(master=personalinfoframe, text="",font=("Arial", 18))
    ic_entry.grid(row=1, column=1, padx=(0,185), pady=10, sticky="w")

    email_label = ctk.CTkLabel(master=personalinfoframe, text="Email: ", font=("Arial", 18))
    email_label.grid(row=1, column=2, pady=10, sticky="w")
    email_entry = ctk.CTkEntry(master=personalinfoframe, width=180)
    email_entry.grid(row=1, column=3, padx=(30,100), pady=10, sticky="w")

    name_label = ctk.CTkLabel(master=personalinfoframe, text="Name:", font=("Arial", 18))
    name_label.grid(row=2, column=0, padx=40, pady=10, sticky="w")
    name_entry = ctk.CTkEntry(master=personalinfoframe, width=180)
    name_entry.grid(row=2, column=1, padx=(0,185), pady=10, sticky="w")

    contact_label = ctk.CTkLabel(master=personalinfoframe, text="Contact:", font=("Arial", 18))
    contact_label.grid(row=2, column=2, pady=10, sticky="w")
    contact_entry = ctk.CTkEntry(master=personalinfoframe, width=180)
    contact_entry.grid(row=2, column=3, padx=(30,100), pady=10, sticky="w")

    membership_label = ctk.CTkLabel(master=personalinfoframe, text="Membership:", font=("Arial", 18))
    membership_label.grid(row=3, column=0, padx=40, pady=10, sticky="w")
    membership_display = ctk.CTkLabel(master=personalinfoframe, text="-", font=("Arial", 18))
    membership_display.grid(row=3, column=1, padx=(0,185), pady=10, sticky="w")

    membership_due_label = ctk.CTkLabel(master=personalinfoframe, text="Membership due: ", font=("Arial", 18))
    membership_due_label.grid(row=3, column=2, pady=10, sticky="w")
    membership_due = ctk.CTkLabel(master=personalinfoframe, text="-", font=("Arial", 18))
    membership_due.grid(row=3, column=3, padx=(30,100), pady=10, sticky="w")

    address_label = ctk.CTkLabel(master=personalinfoframe, text="Address:", font=("Arial", 18))
    address_label.grid(row=5, column=0, padx=40, pady=10, sticky="nw")
    address_entry = ctk.CTkTextbox(master=personalinfoframe,width=400, height=50)
    address_entry.grid(row=5, column=1, columnspan=4, pady=10, sticky="w")
    SearchPersonalInfoData()

    update_btn = ctk.CTkButton(master=personalinfoframe, text="Save", font=("Arial", 18), width=100, height=35, corner_radius=100, command=UpdatePersonalInfo)
    update_btn.grid(row=6, column=3, padx=(30,100), pady=(10,300), sticky="e")

#Create BorrowHistory Frame(Member Side)
def BorrowHistory():
    member_mainframe.destroy()
    global borrowhistoryframe
    if bookmanagerframe != None:
        bookmanagerframe.destroy()
    if borrowhistoryframe != None:
        borrowhistoryframe.destroy()
    if personalinfoframe != None:
        personalinfoframe.destroy()
    if discussionroomframe != None:
        discussionroomframe.destroy()
    if trendingbookframe != None:
        trendingbookframe.destroy()

    # Frame
    borrowhistoryframe = ctk.CTkFrame(master=member_home,fg_color="#2b2b2b")
    borrowhistoryframe.grid(row=0, column=1, rowspan=50, columnspan=50,sticky="nw")
    borrowhistorylist = ctk.CTkScrollableFrame(master=borrowhistoryframe, width=910, height=250,fg_color="#333333")
    borrowhistorylist.grid(row=2, column=0, rowspan=8, columnspan=8, padx=30,pady=(10,30))
    booksinfoframe = tk.LabelFrame(master=borrowhistoryframe, text= "Book Info", width=550, height=200, bg="#2b2b2b", fg="white", font=("Arial", 18))
    booksinfoframe.grid(row=10, column=0, rowspan=8, columnspan=8, padx=50, pady=(0,30), sticky="w")

    # home
    def BackToHome():
        borrowhistoryframe.grid_forget()
        member_menu()

    memberhome_btn = ctk.CTkButton(master=borrowhistoryframe, text="\U0001F3E0 Home", font=("Arial", 20, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=BackToHome) 
    memberhome_btn.place(relx=0.88,rely=0.04)

    title_label = ctk.CTkLabel(master=borrowhistoryframe, text="Borrow History",font=("Arial", 24, "bold"))
    title_label.grid(row=0, column=0, padx=40, columnspan=5, pady=(30,20), sticky="w")

    #Dislay Borrow History
    def DisplayBorrowHistory():
        global connection
        try:
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            cursor = connection.cursor()
            cursor.execute("SELECT ISBN, Book_Title, Borrowed_Date, Return_Date, Due_Date, Penalty, Payment_Condition FROM borrowedmember WHERE IC=%s ORDER BY Borrowed_Date ASC",(ic,))
            borrowhistory_search.delete(*borrowhistory_search.get_children())
            i=0
            for ro in cursor:
                borrowhistory_search.insert('',i,text="",values=(ro[0],ro[1],ro[2],ro[3],ro[4],ro[5],ro[6]))
            cursor.close()  # Close the cursor after use
            connection.commit()
        except mysql.connector.Error as error:
            print(f"Error: Unable to load tasks from the database. {error}")
            exit()

    #Count the book borrowed  
    def get_borrowed_count():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM borrowedmember WHERE IC = %s", (ic,))
        borrow_count = cursor.fetchone()[0]
        cursor.close()
        borrowed_books.configure(text="Total borrowed books:\t"+str(borrow_count))

    member_ISBN = ctk.StringVar()
    booktitle = ctk.StringVar()

    #Cooperate with the treeview,if select the specific row of the tree view, the data in the treeview will also appear in the respective entry.
    def MemberbookInfo(ev):
        viewInfo = borrowhistory_search.focus()
        bookData = borrowhistory_search.item(viewInfo)
        row = bookData ['values']
        if len(str(row[0]))<10:
            row[0]=(10-int(len(str(row[0]))))*"0"+str(row[0])

        member_ISBN.set(row[0])
        booktitle.set(row[1])
            
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT Book_Author, publisher, genre, language FROM books WHERE ISBN = %s", (row[0],))
        detail = cursor.fetchone()
        cursor.close()
        if detail:
            author_entry.delete(0, "end")  
            author_entry.insert(0, detail[0])  

            publisher_entry.delete(0, "end")
            publisher_entry.insert(0, detail[1])

            genre_entry.delete(0, "end")
            genre_entry.insert(0, detail[2])

            language_entry.delete(0, "end")
            language_entry.insert(0, detail[3])

    global borrowhistory_search
    borrowhistory_search = ttk.Treeview(borrowhistorylist,show="headings", selectmode="browse", height=100)
    borrowhistory_search['column']=("ISBN","Book_Title","Borrowed_Date","Return_Date","Due_Date","Penalty","Payment")

    # Column
    borrowhistory_search.column("#0",width=0,stretch=tk.NO) # Hide the default first column
    borrowhistory_search.column("ISBN",anchor="w",width=120, minwidth=120)
    borrowhistory_search.column("Book_Title",anchor="w",width=300, minwidth=300)
    borrowhistory_search.column("Borrowed_Date",anchor="w",width=120, minwidth=120)
    borrowhistory_search.column("Return_Date",anchor="w",width=120, minwidth=120)
    borrowhistory_search.column("Due_Date",anchor="w",width=120, minwidth=120)
    borrowhistory_search.column("Penalty",anchor="w",width=120, minwidth=120)
    borrowhistory_search.column("Payment",anchor="w",width=130, minwidth=130)

    # Headings
    borrowhistory_search.heading("ISBN", text="ISBN", anchor="w")
    borrowhistory_search.heading("Book_Title", text="Book_Title", anchor="w")
    borrowhistory_search.heading("Borrowed_Date", text="Borrow Date", anchor="w")
    borrowhistory_search.heading("Return_Date", text="Return Date", anchor="w")
    borrowhistory_search.heading("Due_Date", text="Due Date", anchor="w")
    borrowhistory_search.heading("Penalty", text="Penalty (RM)", anchor="w")
    borrowhistory_search.heading("Payment", text="Payment", anchor="w")
    DisplayBorrowHistory()
    borrowhistory_search.pack(fill="x") 
    borrowhistory_search.bind("<ButtonRelease-1>",MemberbookInfo)

    borrowed_books = ctk.CTkLabel(master=borrowhistoryframe, text="Total borrowed books:\t-", font=("Arial", 18))
    borrowed_books.grid(row=1, column=0, padx=40, columnspan=2, pady=10, sticky="w")
    get_borrowed_count()

    # Book Info
    book_label = ctk.CTkLabel(master=booksinfoframe, text="Book Ttile: ",font=("Arial", 18))
    book_label.grid(row=0, column=0, padx=(30,5), pady=10, sticky="w")
    book_entry = ctk.CTkEntry(master=booksinfoframe, width=450,textvariable=booktitle)
    book_entry.grid(row=0, column=1, columnspan=3, pady=10, sticky="w")

    publisher_label = ctk.CTkLabel(master=booksinfoframe, text="Publisher: ", font=("Arial", 18))
    publisher_label.grid(row=1, column=0, padx=(30,5), pady=10, sticky="w")
    publisher_entry = ctk.CTkEntry(master=booksinfoframe, width=200)
    publisher_entry.grid(row=1, column=1, pady=10, sticky="w")

    author_label = ctk.CTkLabel(master=booksinfoframe, text="Author:", font=("Arial", 18))
    author_label.grid(row=2, column=0, padx=(30,5), pady=10, sticky="w")
    author_entry = ctk.CTkEntry(master=booksinfoframe, width=200)
    author_entry.grid(row=2, column=1, pady=10, sticky="w")

    ISBN_label = ctk.CTkLabel(master=booksinfoframe, text="ISBN: ", font=("Arial", 18))
    ISBN_label.grid(row=2, column=2, padx=(30,10), pady=10, sticky="w")
    ISBN_entry = ctk.CTkEntry(master=booksinfoframe, width=150,textvariable=member_ISBN)
    ISBN_entry.grid(row=2, column=3, padx=(0,30), pady=10, sticky="w")

    genre_label = ctk.CTkLabel(master=booksinfoframe, text="Genre: ", font=("Arial", 18))
    genre_label.grid(row=3, column=0, padx=(30,5), pady=(10,20), sticky="w")
    genre_entry = ctk.CTkEntry(master=booksinfoframe, width=135)
    genre_entry.grid(row=3, column=1, pady=(10,20), sticky="w")

    language_label = ctk.CTkLabel(master=booksinfoframe, text="Language: ", font=("Arial", 18))
    language_label.grid(row=3, column=2, padx=(30,10), pady=(10,20), sticky="w")
    language_entry = ctk.CTkEntry(master=booksinfoframe, width=150)
    language_entry.grid(row=3, column=3, padx=(0,30), pady=(5,20), sticky="w")

#Create frame for borrow and reserve(Member Side)
def Borrow_Reserve():
    member_mainframe.destroy()
    global bookmanagerframe
    if bookmanagerframe != None:
        bookmanagerframe.destroy()
    if borrowhistoryframe != None:
        borrowhistoryframe.destroy()
    if personalinfoframe != None:
        personalinfoframe.destroy()
    if discussionroomframe != None:
        discussionroomframe.destroy()
    if trendingbookframe != None:
        trendingbookframe.destroy()

    # Frame
    bookmanagerframe = ctk.CTkFrame(master=member_home,fg_color="#2b2b2b")
    bookmanagerframe.grid(row=0, column=1, rowspan=50, columnspan=50,sticky="nw")
    book_searchframe = ctk.CTkScrollableFrame(master=bookmanagerframe, width=910, height=200,fg_color="#333333")
    book_searchframe.grid(row=2, column=0, rowspan=8, columnspan=8, padx=30,pady=30)
    booksdetailframe = tk.LabelFrame(master=bookmanagerframe, text= "Book Info", width=550, height=200, bg="#2b2b2b", fg="white", font=("Arial", 18))
    booksdetailframe.grid(row=10, column=0, rowspan=8, columnspan=8, pady=(0,30))

    # home
    def BackToHome():
        bookmanagerframe.grid_forget()
        member_menu()

    memberhome_btn = ctk.CTkButton(master=bookmanagerframe, text="\U0001F3E0 Home", font=("Arial", 20, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=BackToHome) 
    memberhome_btn.place(relx=0.88,rely=0.04)
    
    title_label = ctk.CTkLabel(master=bookmanagerframe, text="Borrow Pickup",font=("Arial", 24, "bold"))
    title_label.grid(row=0, column=0, padx=40, columnspan=5, pady=(30,40), sticky="w")

    #Search Bar for the book
    def searchbooks():
        search_result = search_entry.get().title()
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT ISBN, Book_Title, Book_Author, Publisher, Genre, Language, Availability FROM books WHERE ISBN = '"+search_result+"' OR Book_Title LIKE '%"+search_result+"%' OR Book_Author LIKE '"+search_result+"%' OR Publisher LIKE '"+search_result+"%' OR Genre = '"+search_result+"' OR Language = '"+search_result+"' ORDER BY CASE WHEN Book_Title REGEXP CONCAT('"+search_result+"','%') THEN 1 ELSE 2 END DESC,LENGTH(Book_Title) DESC")
        
        book_search.delete(*book_search.get_children())
        book_search.insert('',0,text="",values=("No result found.","","","","","",""))

        i=0
        for ro in cursor:
            if search_result == "":
                book_search.delete(*book_search.get_children())
                book_search.insert('',0,text="",values=("No result found.","","","","","",""))
            else:
                book_search.insert('',i,text="",values=(ro[0],ro[1],ro[2],ro[3],ro[4],ro[5],ro[6]))
        cursor.close()  # Close the cursor after use

    member_ISBN = ctk.StringVar()
    booktitle = ctk.StringVar()
    author = ctk.StringVar()
    publisher = ctk.StringVar()
    genre = ctk.StringVar()
    language = ctk.StringVar()
    bookavailability = ctk.StringVar()

    #Cooperate with the treeview,if select the specific row of the tree view, the data in the treeview will also appear in the respective entry.
    def MemberbookInfo(ev):
        viewInfo = book_search.focus()
        bookData = book_search.item(viewInfo)
        row = bookData ['values']
        if row and len(row) >= 7:
            member_ISBN.set(row[0])
            booktitle.set(row[1])
            author.set(row[2])
            publisher.set(row[3])
            genre.set(row[4])
            language.set(row[5])
            bookavailability.set(row[6])
            
            global connection
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            cursor = connection.cursor()
            cursor.execute("SELECT lost FROM borrowedmember WHERE ISBN = %s AND Lost = 'Lost'", (row[0],))
            lost = cursor.fetchone()

            cursor.execute("SELECT Reservation_Date FROM ReservedBook WHERE ISBN = %s ORDER BY Reservation_Date DESC LIMIT 1", (row[0],))
            reserved_date = cursor.fetchone()
            if reserved_date:
                availability_date.configure(text="Available date:\t"+str(reserved_date[0]))
            
            else:
                cursor.execute("SELECT due_date FROM borrowedmember WHERE ISBN = %s AND Return_Date IS NULL", (row[0],))
                available_date = cursor.fetchone()

                if available_date:
                    availability_date.configure(text="Available date:\t"+str(available_date[0]))
                else:
                    availability_date.configure(text="Available date:\t-")
        
            if row[6] == "Available":
                memberborrow_btn.configure(state="normal")
                reserve_btn.configure(state="disabled")
            elif row[6] == "Not Available" and lost:
                memberborrow_btn.configure(state="disabled")
                reserve_btn.configure(state="disabled")
                availability_date.configure(text="Available date:\t-")
            elif row[6] == "Not Available": 
                memberborrow_btn.configure(state="disabled")
                reserve_btn.configure(state="normal")
            
            connection.commit()
            cursor.close()

    #Borrow book
    def memberborrowbook():
        def get_waitinglist_count(ic):
            global connection
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM Borrowings WHERE MemberIC = %s", (ic,))
            borrow_count = cursor.fetchone()[0]
            cursor.close()
            return borrow_count

        #Count the amount of borrowed book
        def get_borrowed_count(ic):
            global connection
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM borrowedmember WHERE IC = %s AND Return_Date IS NULL AND Payment_Condition = 'Un-Paid'", (ic,))
            borrow_count = cursor.fetchone()[0]
            cursor.close()
            return borrow_count
        
        #Count the amount of the book in the member cart
        def get_memberborrwinglist_count(ic):
            global connection
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM MemberBorrowings WHERE MemberIC = %s", (ic,))
            borrow_count = cursor.fetchone()[0]
            cursor.close()
            return borrow_count
        
        viewInfo = book_search.focus()
        bookData = book_search.item(viewInfo)
        row = bookData['values']
        isbn_book=row[0]
        global connection
        if not connection or not connection.is_connected():
            connection = connect()
        cursor = connection.cursor()
        cursor.execute("SELECT Membership_Status FROM PersonalInformation WHERE IC = %s", (ic,))
        membership_status = cursor.fetchone()
        current_time = dt.datetime.now().time()
        num_borrowed_books = get_borrowed_count(ic)
        num_waitinglist_books = get_waitinglist_count(ic)
        num_memberborrowing_books=get_memberborrwinglist_count(ic)
        if membership_status:
            if membership_status[0] == "Normal":
                if (num_borrowed_books + num_waitinglist_books+num_memberborrowing_books) == 10:
                    messagebox.showinfo("Borrow Limit", "Borrow limit has been reached.")
                    SendBorrowedMemberEmail()
                    return
            elif membership_status[0] == "Premiere":
                if (num_borrowed_books + num_waitinglist_books+num_memberborrowing_books) == 20:
                    messagebox.showinfo("Borrow Limit", "Borrow limit has been reached.")
                    SendBorrowedMemberEmail()
                    return
        cursor.execute("SELECT ISBN, Book_Title, Book_Author, Language, Availability FROM books WHERE ISBN = %s", (isbn_book,))
        book_details = cursor.fetchone()
        cursor.execute("SELECT ISBN FROM Borrowings WHERE ISBN = %s", (isbn_book,))
        check_borrowing = cursor.fetchone()
        cursor.execute("SELECT ISBN FROM MemberBorrowings WHERE ISBN = %s", (isbn_book,))
        check_memberborrowings=cursor.fetchone()
        if book_details:
            if book_details[4]=="Available" and not check_borrowing and not check_memberborrowings:
                if current_time.hour >= 12:
                    borrow_confirmation=messagebox.askyesno("Borrow Confirmation","You may collect the book latest by tomorrow. \nDo you want to borrow?")
                else:
                    borrow_confirmation=messagebox.askyesno("Borrow Confirmation","You may collect the book by today.\nDo you want to borrow?")
                if borrow_confirmation:
                    borrow_date = dt.date.today()
                    collection_date=borrow_date+dt.timedelta(days=1)
                    isbn_length=len(str(row[0]))
                    if isbn_length<10:
                        row[0]=(10-isbn_length)*"0"+str(row[0])
                    cursor.execute("INSERT INTO MemberBorrowings (MemberIC, ISBN, Book_Title, BorrowDate, CollectionDate) VALUES (%s, %s, %s, %s, %s)",
                    (ic, row[0], row[1], borrow_date, collection_date))
                    borrow_again=messagebox.askyesno("Borrow","Do you want to borrow more books?")
                    if borrow_again == False:
                        SendBorrowedMemberEmail()
            else:
                messagebox.showinfo("Warm reminder", "The book has been pending for pickup.")
        cursor.close()
        connection.commit()

    #Send the email to the admin for preparation of the book
    def SendBorrowedMemberEmail():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()

        cursor = connection.cursor()
        cursor.execute("SELECT Name, IC FROM PersonalInformation WHERE IC = %s", (ic,))
        borrower_info = cursor.fetchone()

        message = MIMEMultipart()
        message["From"] = library_email
        message["To"] = library_email
        message["Subject"] = "Please prepare the books"

        body = f"Books borrowed for {borrower_info[0]} ({borrower_info[1]}) is stored in the pickup table. You may retrieve from it to see the exact books."
        
        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(library_email, email_password)
                server.sendmail(library_email, library_email, message.as_string())
                print("Email sent successfully.")
        except Exception as e:
            print("Error sending email:", str(e))
        finally:
            cursor.close()
            connection.commit()

    #Delete the book from the cart in member side
    def delete_memberborrowing_list():
        today = dt.datetime.now().date()
        global connection
        if not connection or not connection.is_connected():
            connection = connect()
        cursor = connection.cursor()
        cursor.execute("SELECT MemberIC, CollectionDate FROM MemberBorrowings")
        ic_list=cursor.fetchall()
        for icmember,collection_date in ic_list:
            if today > collection_date:
                cursor.execute("DELETE FROM MemberBorrowings WHERE MemberIC = %s AND CollectionDate = %s", (icmember,collection_date))
        connection.commit()
        cursor.close()
    
    #Reserve the book
    def MemberReserve():
        viewInfo = book_search.focus()
        bookData = book_search.item(viewInfo)
        row = bookData['values']
        isbn_length = len(str(row[0]))
        if isbn_length < 10:
            isbn_book = (10 - isbn_length) * "0" + str(row[0])
        else:
            isbn_book = str(row[0])

        global connection
        if not connection or not connection.is_connected():
            connection = connect()
        
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM borrowedmember WHERE IC = %s AND ISBN = %s AND Return_Date IS NULL", (ic, isbn_book))
        avoid_reserve = cursor.fetchone()
        
        if avoid_reserve:
            messagebox.showerror("Error", "You have already borrowed the book.")
        else:
            cursor.execute("SELECT Membership_Status FROM PersonalInformation WHERE IC = %s", (ic,))
            membership_status = cursor.fetchone()
            cursor.fetchall()  # Consume the result
            
            cursor.execute("SELECT COUNT(*) FROM ReservedBook WHERE ISBN = %s", (isbn_book,))
            reserve_frequency = cursor.fetchone()[0]
            cursor.fetchall()  # Consume the result
            
            cursor.execute("SELECT Due_Date FROM BorrowedMember WHERE ISBN = %s", (isbn_book,))
            return_date = cursor.fetchone()[0]
            cursor.fetchall()  # Consume the result
            
            cursor.execute("SELECT Reservation_Date FROM ReservedBook WHERE ISBN = %s", (isbn_book,))
            reserve_dates_result = cursor.fetchall()
            reserve_dates = [row[0] for row in reserve_dates_result]
            latest_reserve_date = max(reserve_dates) if reserve_dates else None
            cursor.fetchall()  # Consume the result
            
            cursor.execute("SELECT * FROM ReservedBook WHERE IC = %s AND ISBN = %s", (ic, isbn_book,))
            confirm_reserved = cursor.fetchall()
            cursor.fetchall()  # Consume the result
            
            cursor.close()

            if confirm_reserved:
                messagebox.showinfo("Info", "You have already reserved the book.")
            else:
                if latest_reserve_date is None and reserve_frequency == 0:
                    if membership_status:
                        if membership_status[0] == "Normal":
                            reservation_date = return_date + dt.timedelta(days=13)
                        elif membership_status[0] == "Premiere":
                            reservation_date = return_date + dt.timedelta(days=20)

                        reserve_confirmation = messagebox.askyesno("Reserve Confirmation", "Do you want to reserve the book?")
                        
                        if reserve_confirmation:
                            cursor = connection.cursor()
                            cursor.execute("INSERT INTO ReservedBook (IC, ISBN, Reservation_Date) VALUES (%s, %s, %s)", (ic, isbn_book, reservation_date))
                            cursor.close()
                            messagebox.showinfo("Info", "You have successfully reserved the book.")
                
                elif latest_reserve_date is not None and reserve_frequency < 3:
                    if membership_status:
                        if membership_status[0] == "Normal":
                            reservation_date = latest_reserve_date + dt.timedelta(days=13)
                        elif membership_status[0] == "Premiere":
                            reservation_date = latest_reserve_date + dt.timedelta(days=20)

                        reserve_confirmation = messagebox.askyesno("Reserve Confirmation", "Do you want to reserve the book?")
                        
                        if reserve_confirmation:
                            cursor = connection.cursor()
                            cursor.execute("INSERT INTO ReservedBook (IC, ISBN, Reservation_Date) VALUES (%s, %s, %s)", (ic, isbn_book, reservation_date))
                            cursor.close()
                            messagebox.showinfo("Info", "You have successfully reserved the book.")
                
                else:
                    messagebox.showinfo("Sorry", "Sorry, the book is currently unavailable for reservation. It has reached the maximum amount of reservation for this book.")
        connection.commit()

    search_entry = ctk.CTkEntry(master=bookmanagerframe, placeholder_text="Search (Please include punctuation if there is any (e.g. , ! ?))", width=650, height=35)
    search_entry.grid(row=1, column=0, columnspan=5, padx=(35,0), sticky="w")
    search_btn = ctk.CTkButton(master=bookmanagerframe, text="Search", font=("Arial", 18), corner_radius=100, height=35, command=searchbooks)
    search_btn.grid(row=1, column=5, padx=30, sticky="w")

    global book_search
    book_search = ttk.Treeview(book_searchframe,height=50,show="headings",selectmode="browse")
    book_search['column']=("ISBN","Book_Title","Book_Author","Publisher","Genre","Language","Availability")

    # Column
    book_search.column("#0",width=0,stretch=tk.NO) # Hide the default first column
    book_search.column("ISBN",anchor="w",width=150, minwidth=150)
    book_search.column("Book_Title",anchor="w",width=250, minwidth=250)
    book_search.column("Book_Author",anchor="w",width=150, minwidth=150)
    book_search.column("Publisher",anchor="w",width=180, minwidth=180)
    book_search.column("Genre",anchor="w",width=180, minwidth=180)
    book_search.column("Language",anchor="w",width=120, minwidth=120)
    book_search.column("Availability",anchor="w",width=120, minwidth=120)

    # Headings
    book_search.heading("ISBN", text="ISBN", anchor="w")
    book_search.heading("Book_Title", text="Book Title", anchor="w")
    book_search.heading("Book_Author", text="Author", anchor="w")
    book_search.heading("Publisher", text="Publisher", anchor="w")
    book_search.heading("Genre", text="Genre", anchor="w")
    book_search.heading("Language", text="Language", anchor="w")
    book_search.heading("Availability", text="Availability", anchor="w")
    book_search.pack(fill="x")
    book_search.bind("<ButtonRelease-1>", MemberbookInfo)
    
    # Book Info
    book_label = ctk.CTkLabel(master=booksdetailframe, text="Book Ttile: ",font=("Arial", 18))
    book_label.grid(row=0, column=0, padx=(30,5), pady=(10,5), sticky="w")
    book_entry = ctk.CTkEntry(master=booksdetailframe, width=450,textvariable=booktitle)
    book_entry.grid(row=0, column=1, columnspan=3, pady=(10,5), sticky="w")
    book_entry.configure(state="disabled")

    publisher_label = ctk.CTkLabel(master=booksdetailframe, text="Publisher: ", font=("Arial", 18))
    publisher_label.grid(row=1, column=0, padx=(30,5), pady=5, sticky="w")
    publisher_entry = ctk.CTkEntry(master=booksdetailframe, width=200,textvariable=publisher)
    publisher_entry.grid(row=1, column=1, pady=5, sticky="w")
    publisher_entry.configure(state="disabled")

    author_label = ctk.CTkLabel(master=booksdetailframe, text="Author:", font=("Arial", 18))
    author_label.grid(row=2, column=0, padx=(30,5), pady=5, sticky="w")
    author_entry = ctk.CTkEntry(master=booksdetailframe, width=200,textvariable=author)
    author_entry.grid(row=2, column=1, pady=5, sticky="w")
    author_entry.configure(state="disabled")

    ISBN_label = ctk.CTkLabel(master=booksdetailframe, text="ISBN: ", font=("Arial", 18))
    ISBN_label.grid(row=2, column=2, padx=(30,10), pady=5, sticky="w")
    ISBN_entry = ctk.CTkEntry(master=booksdetailframe, width=150,textvariable=member_ISBN)
    ISBN_entry.grid(row=2, column=3, padx=(0,30), pady=5, sticky="w")
    ISBN_entry.configure(state="disabled")

    genre_label = ctk.CTkLabel(master=booksdetailframe, text="Genre: ", font=("Arial", 18))
    genre_label.grid(row=3, column=0, padx=(30,5), pady=5, sticky="w")
    genre_entry = ctk.CTkEntry(master=booksdetailframe, width=135,textvariable=genre)
    genre_entry.grid(row=3, column=1, pady=5, sticky="w")
    genre_entry.configure(state="disabled")

    language_label = ctk.CTkLabel(master=booksdetailframe, text="Language: ", font=("Arial", 18))
    language_label.grid(row=3, column=2, padx=(30,10), pady=5, sticky="w")
    language_entry = ctk.CTkEntry(master=booksdetailframe, width=150,textvariable=language)
    language_entry.grid(row=3, column=3, padx=(0,30), pady=5, sticky="w")
    language_entry.configure(state="disabled")

    availability_label = ctk.CTkLabel(master=booksdetailframe, text="Availability: ", font=("Arial", 18))
    availability_label.grid(row=4, column=0, padx=(30,5), pady=(5,20), sticky="w")
    availability_entry = ctk.CTkEntry(master=booksdetailframe, width=135, textvariable=bookavailability)
    availability_entry.grid(row=4, column=1, pady=(5,20), sticky="w")
    availability_entry.configure(state="disabled")

    availability_date = ctk.CTkLabel(master=booksdetailframe, text="Available date:\t-", font=("Arial", 18))
    availability_date.grid(row=4, column=2, columnspan=2, padx=30, pady=(5,20), sticky="w")

    memberborrow_btn = ctk.CTkButton(master=booksdetailframe, text="Borrow", font=("Arial", 18), corner_radius=100, height=30,command=memberborrowbook)
    memberborrow_btn.grid(row=3, column=4, padx=30, sticky="w")
    reserve_btn = ctk.CTkButton(master=booksdetailframe, text="Reserve", font=("Arial", 18), corner_radius=100, height=30,command=MemberReserve)
    reserve_btn.grid(row=4, column=4, padx=30, pady=(5,20), sticky="w")
    memberborrow_btn.configure(state="disabled")
    reserve_btn.configure(state="disabled")
    delete_memberborrowing_list()

#Create the main frame(Member Side)
def member_menu():
    member_home.lift()

    # Frame for admin menu
    global member_mainframe
    member_mainframe = ctk.CTkFrame(master=member_home,fg_color="#2b2b2b")
    member_mainframe.grid(row=0, column=1, rowspan=50, columnspan=50, sticky="nw")
    global member_btnselection
    member_btnselection = ctk.CTkFrame(master=member_home)
    member_btnselection.grid(row=0,column=0, rowspan=30)

    currentborrowframe = ctk.CTkScrollableFrame(master=member_mainframe, width=910, height=200, fg_color="#333333")
    currentborrowframe.grid(row=3, column=0, rowspan=4, columnspan=8, padx=30, pady=(0,30))
    pickupborrowframe = ctk.CTkScrollableFrame(master=member_mainframe, width=500, height=150, fg_color="#333333")
    pickupborrowframe.grid(row=8, column=0, rowspan=4, columnspan=4, padx=30, pady=(0,30), sticky ="w")
    roomframe = ctk.CTkScrollableFrame(master=member_mainframe, width=350, height=150, fg_color="#333333")
    roomframe.grid(row=8, column=4, rowspan=4, padx=(0,30), pady=(0,30), sticky="e")
    
    # member_menu navbar
    btn_width = 245
    borrow_manager = ctk.CTkButton(master=member_btnselection, text="Borrow Pickup", font=("Arial", 20), width=btn_width, height=40, corner_radius=100, command=Borrow_Reserve)
    borrow_manager.grid(row=0,column=0,padx=30,pady=(60,20))
    trending_books = ctk.CTkButton(master=member_btnselection, text="Trending Books", font=("Arial", 20), width=btn_width, height=40, corner_radius=100, command=TrendingBooks)
    trending_books.grid(row=1,column=0,padx=30,pady=20)
    book_discussion = ctk.CTkButton(master=member_btnselection, text="Book Discussion Room",font=("Arial", 20), width=btn_width, height=40, corner_radius=100, command=DiscussionRoomBooking)
    book_discussion.grid(row=2,column=0,padx=30,pady=20)
    book_history = ctk.CTkButton(master=member_btnselection, text="Borrow History", font=("Arial", 20), width=btn_width, height=40, corner_radius=100, command=BorrowHistory)
    book_history.grid(row=3,column=0,padx=30,pady=20)
    personal_info = ctk.CTkButton(master=member_btnselection, text="Personal Info", font=("Arial", 20), width=btn_width, height=40, corner_radius=100, command=PersonalInfo)
    personal_info.grid(row=4,column=0,padx=30,pady=20)

    #Logout the main member menu
    def member_logout():
        logout = messagebox.askokcancel("Log Out","Log Out")
        if logout == True:
            back_startup()
            welcome_label.destroy()
            if bookmanagerframe != None:
                bookmanagerframe.destroy()
            if borrowhistoryframe != None:
                borrowhistoryframe.destroy()
            if personalinfoframe != None:
                personalinfoframe.destroy()
            if discussionroomframe != None:
                discussionroomframe.destroy()
            if trendingbookframe != None:
                trendingbookframe.destroy()

    logout_btn = ctk.CTkButton(master=member_btnselection, text="Log Out", font=("Arial", 16, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=member_logout) 
    logout_btn.grid(row=7,column=0,rowspan=2,padx=30,pady=(160,60))
    
    # Welcome Label
    welcome_label = ctk.CTkLabel(master=member_mainframe, text="", font=("Arial", 24, "bold"))
    welcome_label.grid(row=0, column=0, padx=(40,0), pady=30, sticky="w")
    membership_status = ctk.CTkLabel(master=member_mainframe, text="", font=("Arial", 20))
    membership_status.grid(row=0, column=1, pady=30, sticky="w")
    currentlist_label = ctk.CTkLabel(master=member_mainframe, text="Currently Borrowing: ", font=("Arial", 20, "bold"))
    currentlist_label.grid(row=1, column=0, padx=(40,0), pady=(0,10), sticky="w")
    pickup_label = ctk.CTkLabel(master=member_mainframe, text="Pending for Pickup: ", font=("Arial", 20, "bold"))
    pickup_label.grid(row=7, column=0, padx=(40,0), pady=(0,10), sticky="w")
    booking_label = ctk.CTkLabel(master=member_mainframe, text="Discussion Room Booking: ", font=("Arial", 20, "bold"))
    booking_label.grid(row=7, column=4, padx=10, pady=(0,10), sticky="w")

    #Display Name
    def search_name():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT Name FROM PersonalInformation WHERE IC = %s", (ic,))
        name = cursor.fetchone()
        cursor.close()  # Close the cursor after use
        return name[0]
    name=search_name()
    welcome_label.configure(text=("Hello,  " + name))

    # Membership status
    def search_status():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        cursor.execute("SELECT Membership_Status FROM PersonalInformation WHERE IC = %s", (ic,))
        status = cursor.fetchone()
        cursor.close()  # Close the cursor after use
        return status[0]
    status=search_status()
    if status=="Premiere":
        membership_image = ctk.CTkImage(Image.open("images/crown.png"),size=(30,30))
        membership_status.configure(image=membership_image)
    else:
        None

    #Display current borrowing books
    def DisplayCurrentList():
        global connection
        try:
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            cursor = connection.cursor()
            cursor.execute("SELECT ISBN, Book_Title, Borrowed_Date, Due_Date, Penalty FROM borrowedmember WHERE IC=%s AND Return_Date IS NULL AND Payment_Condition = 'Un-Paid' ORDER BY Borrowed_Date DESC",(ic,))
            currentborrowlist.delete(*currentborrowlist.get_children())
            i=0
            for ro in cursor:
                currentborrowlist.insert('',i,text="",values=(ro[0],ro[1],ro[2],ro[3],ro[4]))
            cursor.close()  # Close the cursor after use
            connection.commit()
        except mysql.connector.Error as error:
            print(f"Error: Unable to load tasks from the database. {error}")
            exit()

    global currentborrowlist
    currentborrowlist = ttk.Treeview(currentborrowframe, show="headings", selectmode="browse", height=20)
    currentborrowlist['column']=("ISBN","Book_Title","Borrowed_Date","Due_Date","Penalty")

    # Column
    currentborrowlist.column("#0",width=0,stretch=tk.NO) # Hide the default first column
    currentborrowlist.column("ISBN",anchor="w",width=135, minwidth=135)
    currentborrowlist.column("Book_Title",anchor="w",width=580, minwidth=580)
    currentborrowlist.column("Borrowed_Date",anchor="w",width=120, minwidth=120)
    currentborrowlist.column("Due_Date",anchor="w",width=120, minwidth=120)
    currentborrowlist.column("Penalty",anchor="w",width=100, minwidth=100)

    # Headings
    currentborrowlist.heading("ISBN", text="ISBN", anchor="w")
    currentborrowlist.heading("Book_Title", text="Book_Title", anchor="w")
    currentborrowlist.heading("Borrowed_Date", text="Borrow Date", anchor="w")
    currentborrowlist.heading("Due_Date", text="Due Date", anchor="w")
    currentborrowlist.heading("Penalty", text="Penalty (RM)", anchor="w")
    DisplayCurrentList()
    currentborrowlist.pack(fill="x")
    
    #Display the book in the waiting list
    def DisplayPickupList():
        global connection
        try:
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            cursor = connection.cursor()
            cursor.execute("SELECT ISBN, Book_Title, CollectionDate FROM memberborrowings WHERE MemberIC=%s ORDER BY Book_Title ASC",(ic,))
            pickuplist.delete(*pickuplist.get_children())
            i=0
            for ro in cursor:
                pickuplist.insert('',i,text="",values=(ro[0],ro[1],ro[2]))
            cursor.close()
            connection.commit()
        except mysql.connector.Error as error:
            print(f"Error: Unable to load tasks from the database. {error}")
            exit()

    global pickuplist
    pickuplist = ttk.Treeview(pickupborrowframe, show="headings", selectmode="browse", height=20)
    pickuplist['column']=("ISBN","Book_Title","Collection_Date")

    pickuplist.column("#0",width=0,stretch=tk.NO)
    pickuplist.column("ISBN",anchor="w",width=130, minwidth=130)
    pickuplist.column("Book_Title",anchor="w",width=250, minwidth=250)
    pickuplist.column("Collection_Date",anchor="w",width=150, minwidth=150)

     # Headings
    pickuplist.heading("ISBN", text="ISBN", anchor="w")
    pickuplist.heading("Book_Title", text="Book Title", anchor="w")
    pickuplist.heading("Collection_Date", text="Collection Date", anchor="w")
    DisplayPickupList()
    pickuplist.pack(fill="x") 

    #Dispaly the booking rooms
    def DisplayBooking():
        current_date = dt.datetime.now().strftime('%Y-%m-%d')
        current_time = time.strftime("%H:%M:%S")
        global connection
        try:
            if not connection or not connection.is_connected():
                connection = connect()  # Reconnect if the connection is closed or lost
            cursor = connection.cursor()
            cursor.execute("SELECT Date, Room, Start_Time, End_Time FROM bookingroom WHERE IC=%s AND ((Date=%s AND (Start_Time>%s OR (Start_Time<%s AND %s<End_Time))) OR (Date>%s)) ORDER BY Date DESC, Start_Time DESC",(ic, current_date, current_time, current_time, current_time, current_date))
            memberbookinglist.delete(*memberbookinglist.get_children())
            i=0
            for ro in cursor:
                memberbookinglist.insert('',i,text="",values=(ro[0],ro[1],ro[2],ro[3]))
            cursor.close()
            connection.commit()
        except mysql.connector.Error as error:
            print(f"Error: Unable to load tasks from the database. {error}")
            exit()

    global memberbookinglist
    memberbookinglist = ttk.Treeview(roomframe, show="headings", selectmode="browse", height=20)
    memberbookinglist['column']=("Date","Room","Start_Time","End_Time")

    memberbookinglist.column("#0",width=0,stretch=tk.NO)
    memberbookinglist.column("Date",anchor="w",width=130, minwidth=130)
    memberbookinglist.column("Room",anchor="w",width=100, minwidth=100)
    memberbookinglist.column("Start_Time",anchor="w",width=100, minwidth=100)
    memberbookinglist.column("End_Time",anchor="w",width=100, minwidth=100)

     # Headings
    memberbookinglist.heading("Date", text="Date", anchor="w")
    memberbookinglist.heading("Room", text="Room", anchor="w")
    memberbookinglist.heading("Start_Time", text="Start", anchor="w")
    memberbookinglist.heading("End_Time", text="End", anchor="w")
    DisplayBooking()
    memberbookinglist.pack(fill="x")

#Member login
def member_login(): 
    image.lift()
    member_signinpage.lift()

    #validate IC from database
    def search_IC():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        ic = member_entry.get()
        cursor.execute("SELECT IC FROM PersonalInformation WHERE IC = %s",(ic,))
        result = cursor.fetchone()
        cursor.close()  # Close the cursor after use
        return result

    #validate password from database
    def search_IC_password():
        global connection
        if not connection or not connection.is_connected():
            connection = connect()  # Reconnect if the connection is closed or lost
        cursor = connection.cursor()
        global ic
        ic = member_entry.get()
        password = password_entry.get()
        cursor.execute("SELECT IC FROM PersonalInformation WHERE IC = %s AND Password = %s", (ic, password))
        result = cursor.fetchone()
        cursor.close()  # Close the cursor after use
        return result

    #Validate the ic and password
    def login_check():
        ic_validation = r"^([0-9]{2}(0[1-9]|1[0-2])([0-2][0-9]|3[01])+-[0-9]{2}+-[0-9]{4})$"
        ic = member_entry.get()
        if re.match(ic_validation, ic) and not search_IC():
            messagebox.showerror("Error","IC not registered.")
        elif not search_IC_password():
            messagebox.showerror("Error","Invalid IC or password.")
        else:
            member_menu()
    
    #Press 'enter' to the password_entry
    def member_login_on_enter(event=None, entry=None):
        if entry is None:
            entry = member_entry
        else:
            entry.tk_focusNext().focus_set()
    
    back_btn = ctk.CTkButton(master=member_signinpage, text="Back", font=("Arial", 16, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=back_startup) 
    back_btn.place(relx=0.03,rely=0.03)

    login = ctk.CTkLabel(master=member_signinpage, text="Member", font=("Arial", 32,"bold"))
    login.place(relx=0.5, rely=0.25, anchor=ctk.CENTER)

    member_label = ctk.CTkLabel(master=member_signinpage, text="NRIC No. :", font=("Arial", 16))
    member_label.place(relx=0.15, rely=0.4)
    member_entry = ctk.CTkEntry(master=member_signinpage, placeholder_text="e.g. XXXXXX-XX-XXXX")
    member_entry.place(relx=0.5, rely=0.4)

    password_label = ctk.CTkLabel(master=member_signinpage, text="Password:", font=("Arial", 16))
    password_label.place(relx=0.15, rely=0.5)
    password_entry = ctk.CTkEntry(master=member_signinpage, show="*")
    password_entry.place(relx=0.5, rely=0.5)

    login_button = ctk.CTkButton(master=member_signinpage, text="Sign In", command=login_check, font=("Arial", 20), height=40, corner_radius=100)
    login_button.place(relx=0.5, rely=0.7, anchor=ctk.CENTER)

    reg_label = ctk.CTkLabel(master=member_signinpage, text="Not yet a member?", font=("Arial",16), text_color="#808080")
    reg_label.place(relx=0.5, rely=0.83, anchor=ctk.CENTER)
    reg_button = ctk.CTkButton(master=member_signinpage, text="Sign Up", command=register, font=("Arial", 16, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838")
    reg_button.place(relx=0.5, rely=0.9, anchor=ctk.CENTER)

    member_entry.bind('<Return>', lambda event: member_login_on_enter(entry=password_entry))
    password_entry.bind('<Return>', lambda event: login_check())

#Register
def register():
    #Save into the database
    def save_to_database():
        global connection
        nric = ic_entry.get()
        name = name_entry.get().title()
        email = email_entry.get().lower()
        contact = contact_entry.get()
        address = address_entry.get('1.0', 'end-1c').title()
        password01 = password01_entry.get()
        password = password_entry.get()

        ic_validation = r"^([0-9]{2}(0[1-9]|1[0-2])([0-2][0-9]|3[01])+-[0-9]{2}+-[0-9]{4})$"
        email_validation = r"^([a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.com)$"
        contact_validation = r"^01[0-9]-\d{7,8}$"
        address_validation = [
            r'\b(?:Jalan|Jln)\b',
            r'\b(?:Taman|Tmn)\b',
            r'\b(?:Kampung|Kpg)\b',
            r'\b(?:Lorong|Lrg)\b',
            r'\b(?:Persiaran|Persiaran)\b',
            r'\b(?:Pejabat Pos)\b',
            r'\b(?:Poskod|Poscode)\b',
        ]
        password_validation = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,16}$"

        if not re.match(ic_validation, nric):
            messagebox.showerror("Error", "Invalid IC No.")
            return
        if not re.match(email_validation, email):
            messagebox.showerror("Error", "Invalid email.")
            return
        if not re.match(contact_validation, contact) or len(contact)>12:
            messagebox.showerror("Error", "Invalid contact number.")
            return
        if not any(re.search(pattern, address, re.IGNORECASE) for pattern in address_validation):
            messagebox.showerror("Error", "Invalid address.")
            return
        if not re.match(password_validation, password01):
            messagebox.showerror("Error", "Invalid password.No required the special symbol")
            return
        if password != password01:
            messagebox.showerror("Error", "The password is not the same.")
            return

        try:
            connection = connect()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO PersonalInformation (IC, Name, Email, Contact, Address, Password) \
                            VALUES (%s, %s, %s, %s, %s, %s)",
                            (nric, name, email, contact, address, password))
            connection.commit()
            messagebox.showinfo("Success", "Data has been successfully stored in database.")
            SendWelcomeEmail(email)
        except mysql.connector.Error as error:
            messagebox.showerror("Error","You have registered.")
        finally:
            closing_connection(connection, cursor)
            member_login()

    # Create labels and entry widgets for personal information
    try:
        reg_form.lift()
    except tk.TclError as e:
        # Handle the case where the Tkinter application window has been destroyed
        print("Application window has been destroyed")
        return
    
    def on_enter_register(event=None, entry=None):
        if entry is None:
            entry = ic_entry
        else:
            entry.tk_focusNext().focus_set()

    #Sending email to the customers after registration
    def SendWelcomeEmail(recipient_email):
        name = name_entry.get().title()
        message = MIMEMultipart()
        message["From"] = library_email
        message["To"] = recipient_email
        message["Subject"] = "Welcome To Sarawak State Library"
        body = f"Hello {name}, \n\nWelcome to the Sarawak State Library Family. You can now start borrowing books from the library and indulge in the sea of knowledge.\n\nFor any inquiries or assistance, please contact sslibrary0505@gmail.com.\nThank you.\n\nSincerely,\nSarawak State Library"
        message.attach(MIMEText(body, "plain"))
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(library_email, email_password)
                server.sendmail(library_email, recipient_email, message.as_string())
            print("Email sent successfully.")
        except Exception as e:
            print("Error sending email:", str(e))
        
    back_btn = ctk.CTkButton(master=reg_form, text="Back", font=("Arial", 16, "underline"), height=30, width=50, fg_color="transparent", text_color="#808080", hover_color="#363838", command=member_login) 
    back_btn.place(relx=0.03,rely=0.03)

    reg_label = ctk.CTkLabel(master=reg_form, text="Registration Form", font=("Arial", 32))
    reg_label.grid(row=0, column=0, columnspan=2,pady=20)

    ic_label = ctk.CTkLabel(master=reg_form, text="NRIC No.:", font=("Arial", 16))
    ic_label.grid(row=1, column=0, padx=20, sticky="w")
    ic_entry = ctk.CTkEntry(master=reg_form, placeholder_text="e.g. XXXXXX-XX-XXXX", width=215)
    ic_entry.grid(row=1, column=1, padx=20, pady=5, sticky="w")

    name_label = ctk.CTkLabel(master=reg_form, text="Full Name (as in NRIC):", font=("Arial", 16))
    name_label.grid(row=2, column=0, padx=20, sticky="w")
    name_entry = ctk.CTkEntry(master=reg_form, width=215)
    name_entry.grid(row=2, column=1, padx=20, pady=5, sticky="w")

    email_label = ctk.CTkLabel(master=reg_form, text="Email:", font=("Arial", 16))
    email_label.grid(row=3, column=0, padx=20, sticky="w")
    email_entry = ctk.CTkEntry(master=reg_form, placeholder_text="e.g. XXXXXXX@XXXXX.com", width=215)
    email_entry.grid(row=3, column=1, padx=20, pady=5, sticky="w")

    contact_label = ctk.CTkLabel(master=reg_form, text="Contact:", font=("Arial", 16))
    contact_label.grid(row=4, column=0, padx=20, sticky="w")
    contact_entry = ctk.CTkEntry(master=reg_form, placeholder_text="e.g. XXX-XXXXXXXX", width=215)
    contact_entry.grid(row=4, column=1, padx=20, pady=5, sticky="w")

    address_label = ctk.CTkLabel(master=reg_form, text="Address:", font=("Arial", 16))
    address_label.grid(row=5, column=0, padx=20, sticky="nw")
    address_entry = ctk.CTkTextbox(master=reg_form,width=215, height=80)
    address_entry.grid(row=5, column=1, padx=20, pady=5, sticky="w")

    password01_label = ctk.CTkLabel(master=reg_form, text="Password:", font=("Arial", 16))
    password01_label.grid(row=6, column=0, padx=20, sticky="w")
    password01_entry = ctk.CTkEntry(master=reg_form, show="*", width=215)
    password01_entry.grid(row=6, column=1, padx=20, pady=5, sticky="w")
    password_hint = ctk.CTkLabel(master=reg_form, text="- Password should be 8-16 characters.  \n- Password should include at least one \nuppercase, lowercase and digit.         ",text_color="#999999")
    password_hint.grid(row=7, column=1, padx=20, pady=5, sticky="w")

    password_label = ctk.CTkLabel(master=reg_form, text="Confirm Your Password:", font=("Arial", 16))
    password_label.grid(row=8, column=0, padx=20, sticky="w")
    password_entry = ctk.CTkEntry(master=reg_form, show="*", width=215)
    password_entry.grid(row=8, column=1, padx=20, pady=5, sticky="w")

    join_button = ctk.CTkButton(master=reg_form, text="Join", font=("Arial", 20), height=40, command=save_to_database, corner_radius=100)
    join_button.grid(row=9, columnspan=2, pady=20)

    #Allow 'enter' key will be function. If press enter it will go the following entry and after the password_entry,save_to_database function will be execued and registeration is completed 
    ic_entry.bind('<Return>', lambda event: on_enter_register(entry=name_entry))
    name_entry.bind('<Return>', lambda event: on_enter_register(entry=email_entry))
    email_entry.bind('<Return>', lambda event: on_enter_register(entry=contact_entry))
    contact_entry.bind('<Return>', lambda event: on_enter_register(entry=address_entry))
    address_entry.bind('<Return>', lambda event: on_enter_register(entry=password01_entry))
    password01_entry.bind('<Return>', lambda event: on_enter_register(entry=password_entry))
    password_entry.bind('<Return>', lambda event: save_to_database())

#The background image of the program will be appeared after back to the main frame(Select Admin or Member Frame)
def back_startup():
    image.lift()
    startup.lift()
        
# Initialize the Tkinter window
root = ctk.CTk()
root.title("Bookworm")
ctk.set_appearance_mode("dark")
screen_width=root.winfo_screenwidth()
screen_height=root.winfo_screenheight()
root.geometry("%dx%d" % (screen_width,screen_height))
root.state('zoomed')
root.resizable(False, False)

# Style Treeview
style = ttk.Style()
style.theme_use('default')
style.configure("Treeview", background="#2a2d2e", foreground="white", rowheight=40, fieldbackground="#343638", bordercolor="#343638", borderwidth=0, font=("Arial",14))
style.map('Treeview', background=[('selected', "#22559b")])
style.configure("Treeview.Heading", foreground="white", background="#565b5e", font=("Arial",14,"bold"), rowheight=45, relief="flat")
style.map("Treeview.Heading", background=[("active","#3484F0")])

# Background image
image = ctk.CTkFrame(master=root, width=screen_width, height=screen_height)
image.pack(fill="both")
current_path = os.path.join(os.path.dirname(__file__),"images/ssl.jpg")
bg_image = ctk.CTkImage(Image.open(current_path),size=(screen_width,screen_height))
bg_image_label = ctk.CTkLabel(master=image, image=bg_image, text="")
bg_image_label.place(relx=0,rely=0)

# Frame
admin_home = ctk.CTkFrame(master=root, width=360, height=400)
admin_home.place(relx=0.5,rely=0.5,anchor=ctk.CENTER)
member_home = ctk.CTkFrame(master=root, width=360, height=400)
member_home.place(relx=0.5,rely=0.5,anchor=ctk.CENTER)
reg_form = ctk.CTkFrame(master=root, width=360, height=400)
reg_form.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)
admin_signinpage = ctk.CTkFrame(master=root, width=360, height=400)
admin_signinpage.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)
member_signinpage = ctk.CTkFrame(master=root, width=360, height=400)
member_signinpage.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)
startup = ctk.CTkFrame(master=root, width=360, height=400)
startup.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

# Startup
welcome = ctk.CTkLabel(master=startup, text="Welcome to\nSarawak State Library",font=("Arial", 24,"bold"))
welcome.place(relx=0.5, rely=0.23, anchor=ctk.CENTER)
role = ctk.CTkLabel(master=startup, text="Please choose your role:", font=("Arial", 20))
role.place(relx=0.5, rely=0.4, anchor=ctk.CENTER)
admin_btn = ctk.CTkButton(master=startup,text="Admin",font=("Arial", 20),command=admin_login, width=215, height=50, corner_radius=100)
admin_btn.place(relx=0.5, rely=0.55, anchor=ctk.CENTER)
member_btn = ctk.CTkButton(master=startup,text="Member", font=("Arial", 20),command=member_login, width=215, height=50, corner_radius=100)
member_btn.place(relx=0.5, rely=0.73, anchor=ctk.CENTER)
