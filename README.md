# Mid Autumn Festival

The MAF webapp was built in order to improve upon the traditional pen-and-paper method of score-recording and instructions relaying, hence easing workload and facilitating the crowd.

## Getting Started

### Set up environment variables
In the root folder of your project, create a .env file.

https://help.pythonanywhere.com/pages/environment-variables-for-web-apps/

```
export SECRET_KEY=secret_key
export MYSQL_PASSWORD=sql_password
export ADMIN_PASSWORD=admin_password
```

#### Secret key
Generate the secret key using the built-in Python method, which return a string of n random bytes suitable for cryptographic use. This secret key is needed to encrypt the cookies and save send them to the browser when using sessions in Flask.

```
import os
print(os.urandom(n))
```

### Set up MySQL database

https://help.pythonanywhere.com/pages/UsingMySQL/

From the docs,

> To start using MySQL, you'll need to go to the MySQL tab on your dashboard, and set up a password. You'll also find the connection settings (host name, username) on that tab, as well as the ability to create new databases.

Initialize and call the database:
```
app.config["MYSQL_HOST"] = "emilyong.mysql.pythonanywhere-services.com"
app.config["MYSQL_USER"] = "emilyong"
app.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD", default=False)
app.config["MYSQL_DB"] = "emilyong$maf_db"

mysql = MySQL(app)
```

### Prerequisites

* flask
* flask_mysqldb
* os
* dotenv


## Running the tests

https://docs.locust.io/

> The idea is that during a test, a swarm of locusts will attack your website. The behavior of each locust (or test user if you will) is defined by you and the swarming process is monitored from a web UI in real-time. This will help you battle test and identify bottlenecks in your code before letting real users in.

Locust was used as means of load testing the web app.

```
from locust import HttpLocust, TaskSet, task

class UserBehavior (TaskSet):
    def on_start (self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.login()

    def on_stop (self):
        """ on_stop is called when the TaskSet is stopping """
        self.logout()

    def login (self):
        self.client.post("/login", {"opt_signup":"注册 Sign Up"})
        self.client.post("/login", {"signup_username":username, 
                                    "signup_first_name":"emily",
                                    "signup_last_name":"ong", "signup_age":18,
                                    "signup_contact_number":81234567})

    def logout (self):
        self.client.post("/logout")

    @task(1)
    def my_task (self):
        self.client.post("/", {"陀螺 Spinning Top":"陀螺 Spinning Top"})
        self.client.post("/10", {"secret_password": password})
        self.client.post("/10", {"booth_score": 100})

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 300
    max_wait = 1000
```

### Coding style

The set of Python code in this repository follows the PEP8 standard as per https://www.python.org/dev/peps/pep-0008/.

* Python formatter: https://htmlformatter.com/
* HTML formatter: https://yapf.now.sh/

## Built With

* [Pythonanywhere](https://www.pythonanywhere.com/) - The web framework used
* [Locust](https://docs.locust.io/) - Load testing
* [MySQL](https://www.mysql.com) - Database server used
