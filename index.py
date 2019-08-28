from flask import Flask, render_template, redirect, url_for, request, session
from flask_mysqldb import MySQL

import os
from dotenv import load_dotenv

proj_folder = os.path.expanduser("~/mid-autumn-festival")
load_dotenv(os.path.join(proj_folder, ".env"))


URLS = ["login", "/", "admin", "announcements", "visitor", "map"]

password = os.environ.get("ADMIN_PASSWORD", default=False)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", default=False)
app.config["MYSQL_HOST"] = "emilyong.mysql.pythonanywhere-services.com"
app.config["MYSQL_USER"] = "emilyong"
app.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD", default=False)
app.config["MYSQL_DB"] = "emilyong$maf_db"

mysql = MySQL(app)


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.form:
        if "opt_signup" in request.form:
            return render_template("login.html", opt_signup=True)
        if "signup_username" in request.form:
            cur = mysql.connection.cursor()
            cur.execute("SELECT username FROM USERS WHERE username=%s",
                        [request.form["signup_username"]])
            is_username_taken = len(cur.fetchall()) > 0
            cur.close()
            if is_username_taken:
                # Check if username has already been taken
                # Take note of case-sensitivity
                return render_template(
                    "login.html",
                    opt_signup=True,
                    signup_error="This username is already taken.")
            for j in range(len(request.form["signup_username"])):
                # Check for valid usernames: People might accidentally add an additional
                # space at the back of their name that they forget
                # (autocorrect has been disabled)
                if request.form["signup_username"][j] in [
                        "_boothname", "_count", "_information", " ", "*", "?",
                        "/", "!", "@", "#", "$", "%"
                ]:
                    return render_template(
                        "login.html",
                        opt_signup=True,
                        signup_error=
                        "Please ensure that your username is only alphanumeric."
                    )
            # Username is valid: Update database
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO USERS (username, first_name, last_name, contact_number, age, score, booths_visited) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (request.form["signup_username"],
                 request.form["signup_first_name"],
                 request.form["signup_last_name"],
                 request.form["signup_contact_number"],
                 request.form["signup_age"], 0, ""))
            mysql.connection.commit()
            cur.close()

            session["logged_in"] = True
            session["username"] = request.form["signup_username"]

            cur = mysql.connection.cursor()
            cur.execute("SELECT score FROM USERS WHERE username=%s",
                        [session["username"]])

            session["total_score"] = int(cur.fetchall()[0][0])

            cur.close()
            session["redirect_from_login"] = "visitor"
            return redirect(url_for("visitor"))
        if "opt_login" in request.form:
            return render_template("login.html", opt_login=True)
        if "login_username" in request.form:
            login_username = request.form["login_username"]
            login_contact_number = request.form["login_contact_number"]

            cur = mysql.connection.cursor()
            cur.execute("SELECT username FROM USERS WHERE username=%s",
                        [login_username])
            username = cur.fetchall()
            cur.close()
            # Check for valid username or contact number
            if len(username) == 0:
                # Username is not found in the database
                return render_template(
                    "login.html",
                    opt_login=True,
                    login_error=True,
                    error_msg="Username is incorrect.")
            else:
                # Assuming that database contains the username

                cur = mysql.connection.cursor()
                cur.execute(
                    "SELECT contact_number FROM USERS WHERE username=%s",
                    [login_username])
                contact_number = cur.fetchall()[0][0]
                cur.close()
                if login_contact_number != contact_number:
                    return render_template(
                        "login.html",
                        opt_login=True,
                        login_error=True,
                        error_msg="Contact number is incorrect.")

            session["logged_in"] = True
            session["username"] = request.form["login_username"]

            cur = mysql.connection.cursor()
            cur.execute("SELECT booths_visited FROM USERS WHERE username=%s",
                        [session["username"]])
            booths_visited = cur.fetchall()[0][0]
            cur.close()
            visited_booths_text = booths_visited
            if visited_booths_text and len(visited_booths_text) > 0:
                visited_booths_text = visited_booths_text.split(",")
                visited_booths_text = [
                    int(visited_booths_text[x])
                    for x in range(len(visited_booths_text))
                ]
                session["visited_booths"] = visited_booths_text

            cur = mysql.connection.cursor()
            cur.execute("SELECT score FROM USERS WHERE username=%s",
                        [session["username"]])
            total_score = cur.fetchall()[0][0]
            cur.close()
            session["total_score"] = int(total_score)
        if "redirect_from_login" not in session:
            return redirect(url_for("visitor"))
        elif session["redirect_from_login"] not in URLS:
            if "current_booth_info" not in session or str(
                    session["redirect_from_login"]) not in [
                        str(x) for x in range(1, 16)
                    ]:
                return redirect(url_for("visitor"))
            return redirect(
                url_for(
                    "booth_page",
                    variable_booth=session["redirect_from_login"]))
        else:
            return redirect(url_for(session["redirect_from_login"]))
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("visitor"))


@app.route("/", methods=["POST", "GET"])
def visitor():

    # @login_required page
    if "logged_in" not in session or not session["logged_in"]:
        session["logged_in"] = False
        return redirect(url_for("login"))
    if "current_booth_info" not in session:
        session["current_booth_info"] = []
    if "visited_booths" not in session:
        session["visited_booths"] = []
    booths_count = []
    booths_information = []
    booths_name = []

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM BOOTHS")
    booths_data = cur.fetchall()
    cur.close()

    # Get booths data to fill web page
    for i in range(1, len(booths_data)):
        booths_name.append(booths_data[i][0])
        booths_count.append(int(booths_data[i][1]))
        booths_information.append(booths_data[i][2])
    if request.form and "username" not in request.form:
        for elem in request.form:
            for i in range(len(booths_data)):
                if booths_data[i][0] == elem:
                    session["current_booth_info"] = [
                        booths_data[i][2], booths_data[i][0]
                    ]
                    return redirect(
                        url_for("booth_page", variable_booth=str(i)))
    cur = mysql.connection.cursor()
    cur.execute("SELECT score FROM USERS WHERE username=%s",
                [session["username"]])
    total_score = cur.fetchall()[0][0]
    cur.close()
    session["total_score"] = int(total_score)
    return render_template(
        "visitor.html",
        logged_in=True,
        username=session["username"],
        booths_count=booths_count,
        booths_information=booths_information,
        booths_name=booths_name,
        visited_booths=session["visited_booths"],
        total_score=session["total_score"])


@app.route("/<variable_booth>", methods=["POST", "GET"])
def booth_page(variable_booth):
    current_num = -1

    # Check validity range of variable booth to handle errors
    if str(variable_booth) in [str(x) for x in range(1, 16)]:
        current_num = int(variable_booth)
        session["redirect_from_login"] = variable_booth
    else:
        return redirect(url_for("visitor"))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM BOOTHS")
    booths_data = cur.fetchall()
    cur.close()

    if current_num > len(booths_data) - 1:
        return redirect(url_for("visitor"))

    # [Description, Booth Name]
    session["current_booth_info"] = [
        booths_data[current_num][2], booths_data[current_num][0]
    ]
    session.modified = True

    if "logged_in" not in session or not session["logged_in"]:
        session["logged_in"] = False
        return redirect(url_for("login"))

    if "visited_booths" not in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT booths_visited FROM USERS WHERE username=%s",
                    [session["username"]])
        booths_visited = cur.fetchall()[0][0]
        cur.close()
        visited_booths_text = booths_visited
        if visited_booths_text and len(visited_booths_text) > 0:
            visited_booths_text = visited_booths_text.split(",")
            visited_booths_text = [
                int(visited_booths_text[x])
                for x in range(len(visited_booths_text))
            ]
            session["visited_booths"] = visited_booths_text

        session.modified = True
    if "booth_visited" not in session:
        session["booth_visited"] = []
        session.modified = True

    booth_information = session["current_booth_info"][0]
    booth_name = session["current_booth_info"][1]

    authorize_sm = False
    if request.form:
        if "go_back" in request.form:
            return redirect(url_for("visitor"))
        if "secret_password" in request.form:
            if request.form["secret_password"] == password:
                authorize_sm = True
                return render_template(
                    "booth_page.html",
                    booth_information=booth_information,
                    booth_name=booth_name,
                    authorize_sm=authorize_sm)
        if "booth_score" in request.form:
            cur = mysql.connection.cursor()
            cur.execute("SELECT score FROM USERS WHERE username=%s",
                        [session["username"]])
            total_score = cur.fetchall()[0][0]
            cur.close()
            session["total_score"] = int(total_score) + int(
                request.form["booth_score"])
            # Update database with new total score
            cur = mysql.connection.cursor()
            cur.execute("UPDATE USERS SET score=%s WHERE username=%s",
                        [session["total_score"], session["username"]])
            mysql.connection.commit()
            # Update database with new visitor count
            cur.execute("SELECT visitors FROM BOOTHS WHERE booth=%s",
                        [session["current_booth_info"][1]])
            current_visitors_count = int(cur.fetchall()[0][0])
            cur.execute(
                "UPDATE BOOTHS SET visitors=%s WHERE booth=%s",
                [current_visitors_count + 1, session["current_booth_info"][1]])
            mysql.connection.commit()
            cur.close()
            session["booth_visited"].append(current_num)
            if "visited_booths" not in session:
                session["visited_booths"] = []
            session["visited_booths"].append(current_num)
            visited_booths_text = ""
            for i in range(len(session["visited_booths"])):
                visited_booths_text += str(session["visited_booths"][i])
                if i != len(session["visited_booths"]) - 1:
                    visited_booths_text += ","
            cur = mysql.connection.cursor()
            cur.execute("UPDATE USERS SET booths_visited=%s WHERE username=%s",
                        [visited_booths_text, session["username"]])
            mysql.connection.commit()
            cur.close()
            session.modified = True
    visited_booth = False
    if current_num in session["booth_visited"]:
        visited_booth = True
    return render_template(
        "booth_page.html",
        visited_booth=visited_booth,
        booth_information=booth_information,
        booth_name=booth_name,
        authorize_sm=authorize_sm)


@app.route("/admin", methods=["POST", "GET"])
def admin():
    select_user = False
    selected_user_data = []  # Request variable
    if "is_admin" not in session:
        session["is_admin"] = False
    if session["is_admin"]:

        if request.form:
            if "go_back" in request.form:
                return redirect(url_for("visitor"))
            cur = mysql.connection.cursor()
            for request_field in request.form:
                # Modularise this
                if "_boothname" in request_field:
                    cur.execute("SELECT booth FROM BOOTHS")
                    change_name = request_field.replace("_boothname", "")
                    result = cur.fetchall()[int(change_name)][0]
                    cur.execute("UPDATE BOOTHS SET booth=%s WHERE booth=%s",
                                [request.form[request_field], result])
                elif "_information" in request_field:
                    cur.execute("SELECT booth FROM BOOTHS")
                    change_info = request_field.replace("_information", "")
                    result = cur.fetchall()[int(change_info)][0]
                    cur.execute(
                        "UPDATE BOOTHS SET description=%s WHERE booth=%s",
                        [request.form[request_field], result])
                elif "_count" in request_field:
                    cur.execute("SELECT booth FROM BOOTHS")
                    change_count = request_field.replace("_count", "")
                    result = cur.fetchall()[int(change_count)][0]
                    cur.execute("UPDATE BOOTHS SET visitors=%s WHERE booth=%s",
                                [int(request.form[request_field]), result])
                elif "_user_name" in request_field:
                    change_username = request_field.replace("_user_name", "")
                    cur.execute(
                        "UPDATE USERS SET username=%s WHERE username=%s",
                        [request.form[request_field], change_username])
                    if "username" in session and session["username"] == change_username:
                        session["username"] = request.form[request_field]
                elif "_user_first_name" in request_field:
                    change_first_name = request_field.replace(
                        "_user_first_name", "")
                    cur.execute(
                        "UPDATE USERS SET first_name=%s WHERE username=%s",
                        [request.form[request_field], change_first_name])
                elif "_user_last_name" in request_field:
                    change_last_name = request_field.replace(
                        "_user_last_name", "")
                    cur.execute(
                        "UPDATE USERS SET last_name=%s WHERE username=%s",
                        [request.form[request_field], change_last_name])
                elif "_user_contact_number" in request_field:
                    change_contact_number = request_field.replace(
                        "_user_contact_number", "")
                    cur.execute(
                        "UPDATE USERS SET contact_number=%s WHERE username=%s",
                        [request.form[request_field], change_contact_number])
                elif "_user_age" in request_field:
                    change_age = request_field.replace("_user_age", "")
                    cur.execute("UPDATE USERS SET age=%s WHERE username=%s",
                                [int(request.form[request_field]), change_age])
                elif "_user_score" in request_field:
                    change_score = request_field.replace("_user_score", "")
                    cur.execute(
                        "UPDATE USERS SET score=%s WHERE username=%s",
                        [int(request.form[request_field]), change_score])
                    if "username" in session and session["username"] == change_score:
                        session["total_score"] = int(
                            request.form[request_field])
                elif "_user_delete" in request_field:
                    delete_user = request_field.replace("_user_delete", "")
                    if request.form[request_field] == "delete":
                        cur.execute("DELETE FROM USERS WHERE username=%s",
                                    [delete_user])
                elif request_field == "select_user":
                    # Username is selected
                    # Get relevant data
                    select_user = True
                    cur.execute(
                        "SELECT username, first_name, last_name, contact_number, age, score, booths_visited FROM USERS WHERE username=%s",
                        [request.form[request_field]])
                    selected_user_data = cur.fetchall()[0]
                elif request_field == "announcement_form":
                    announcement_data = request.form["announcement_form"]
                    cur.execute(
                        "INSERT INTO ANNOUNCEMENT (announcement_data) VALUES (%s)",
                        [announcement_data])
                else:
                    pass
                mysql.connection.commit()
            cur.close()

        booths_count = []
        booths_information = []
        booths_name = []
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM BOOTHS")
        booths_data = cur.fetchall()
        cur.close()
        for i in range(1, len(booths_data)):
            booths_count.append(int(booths_data[i][1]))
            booths_information.append(booths_data[i][2])
            booths_name.append(booths_data[i][0])

        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM USERS")
        users = cur.fetchall()
        temp = list(users)
        temp.sort()
        cur.execute("SELECT * FROM USERS")
        modal_users = cur.fetchall()
        cur.close()
        return render_template(
            "admin.html",
            select_user=select_user,
            modal_users=modal_users,
            users=temp,
            selected_user_data=selected_user_data,
            admin=True,
            no_of_booths=len(booths_data),
            booths_information=booths_information,
            booths_count=booths_count,
            booths_name=booths_name)
    else:
        if request.form:
            if "go_back" in request.form:
                return redirect(url_for("visitor"))
            if "admin_password" in request.form:
                global password
                if request.form["admin_password"] != password:
                    return render_template("admin.html", wrong_password=True)
                else:
                    session["is_admin"] = True
                    return redirect(url_for("admin"))
        return render_template("admin.html")


@app.route("/announcements", methods=["POST", "GET"])
def announcements():
    session["redirect_from_login"] = "announcements"
    session.modified = True
    if "is_admin" not in session:
        is_admin = False
    else:
        is_admin = session["is_admin"]
    if request.form:
        if "go_back" in request.form:
            return redirect(url_for("visitor"))
        for request_field in request.form:
            if "_delete_announcement" in request_field:
                announcement_deleted = request_field.replace("_delete_announcement", "")
                cur = mysql.connection.cursor()
                cur.execute("DELETE FROM ANNOUNCEMENT WHERE announcement_data=%s",
                            [announcement_deleted])
                mysql.connection.commit()
                cur.close()
    cur = mysql.connection.cursor()
    cur.execute("SELECT announcement_data FROM ANNOUNCEMENT")
    messages = cur.fetchall()
    cur.close()
    return render_template("announcements.html", is_admin=is_admin, messages=messages)


@app.route("/map")
def map():
    session["redirect_from_login"] = "map"
    session.modified = True
    return render_template("map.html")
