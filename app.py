from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # Grab what the user typed in the form
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        gender = request.form.get("gender", "")
        hometown = request.form.get("hometown", "").strip()
        country = request.form.get("country", "").strip()
        not_south_sudanese = request.form.get("not_south_sudanese") == "yes"
        dob = request.form.get("dob", "")

        # Server-side checks (never trust the browser alone)
        errors = []
        if not email:
            errors.append("Please enter your email.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if not gender:
            errors.append("Please select your gender.")
        if not_south_sudanese:
            if not country:
                errors.append("Please enter your country.")
        elif not hometown:
            errors.append("Please tell us your hometown.")
        if not dob:
            errors.append("Please enter your date of birth.")

        if errors:
            # Send them back to the form with the errors and what they typed
            return render_template(
                "signup.html",
                errors=errors,
                email=email,
                gender=gender,
                hometown=hometown,
                country=country,
                not_south_sudanese=not_south_sudanese,
                dob=dob,
            )

        # Success! (In a real app you'd save this to a database here.)
        return render_template("success.html", email=email)

    # GET request — just show the empty form
    return render_template("signup.html", errors=[])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        errors = []
        if not email:
            errors.append("Please enter your email.")
        if not password:
            errors.append("Please enter your password.")

        if errors:
            return render_template("login.html", errors=errors, email=email)

        # In a real app you'd check these credentials against a database here.
        return render_template("success.html", email=email)

    return render_template("login.html", errors=[])


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            return render_template("forgot_password.html", errors=["Please enter your email."])
        # In a real app you'd email a reset link here.
        return render_template("forgot_password.html", sent=True, email=email)

    return render_template("forgot_password.html", errors=[])


if __name__ == "__main__":
    app.run(debug=True, port=5001)
