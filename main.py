#! /usr/bin/python

import flask
import os
import json
from flask import render_template, request, redirect

import userlib as ul

app = flask.Flask(__name__)
app.secret_key = os.urandom(12)


@app.route("/index")
@app.route("/")
def root():
    subs_json_file = open(
        os.path.join("userdata", "PROT", "subs.json"), "r"
    )  # {"subid": {"author":, "file":, "pwhash":}}
    ret = render_template("index.html.jinja", submissions=json.load(subs_json_file))
    subs_json_file.close()
    return ret


@app.route("/getsub", methods=["GET"])
def getsub():
    subs_json_file = open(os.path.join("userdata", "PROT", "subs.json"), "r")
    data = json.load(subs_json_file)
    subid = request.args.get("subid")

    with open(os.path.join("userdata", data[subid]["file"]), "r") as f:
        code = f.read()

        ret = render_template(
            "getsub.html.jinja",
            subid=subid,
            author=data[subid]["author"],
            file=data[subid]["file"],
            code=json.dumps(code),
            codepy=code,  # can't seem to get jinja to parse JSON ;-;
        )
        return ret


@app.route("/submit", methods=["GET", "POST"])
def submit():
    return render_template("submit.html.jinja")


@app.route("/postsubmit", methods=["POST"])
def postsubmit():
    try:

        mtitle = request.form["title"].replace("/", "")  # strip /

        # Create file if it does not exist, else do nothing
        f = open(os.path.join("userdata", mtitle), "x")
        f.close()
        f = open(os.path.join("userdata", mtitle), "w")
        f.write(request.form["codebox"])
        f.close()

        with open(os.path.join("userdata", "PROT", "subs.json"), "r+") as subsf:
            # add it to our submission JSON file
            curdata = json.loads(subsf.read())
            curdata[mtitle] = {
                "author": request.form["author"],
                "file": mtitle,
            }
            subsf.seek(0)
            subsf.truncate()
            subsf.write(json.dumps(curdata))

            uf = ul.userfile(
                os.path.join("userdata", "PROT", "passwd"),
                os.path.join("userdata", "PROT", "shadow"),
            )

            uf.add_user(mtitle, request.form["passwd"])

    except OSError:  # ...no overwriting other submissions, sorry mate
        pass

    return redirect("/")


@app.route("/editsub", methods=["GET", "POST"])
def editsub():
    with open(os.path.join("userdata", "PROT", "subs.json"), "r+") as subsf:
        curdata = json.loads(subsf.read())
        with open(
            os.path.join("userdata", curdata[request.args.get("subid")]["file"]), "r+"
        ) as cbf:
            return render_template(
                "edit.html.jinja", subid=request.args.get("subid"), codebox=cbf.read()
            )


@app.route("/auth", methods=["GET", "POST"])
def auth():
    return render_template(
        "auth.html.jinja",
        action=request.args.get("action"),
        subid=request.args.get("subid"),
        codebox=request.form.get("codebox"),
    )


@app.route("/postauth", methods=["GET", "POST"])
def postauth():
    uf = ul.userfile(
        os.path.join("userdata", "PROT", "passwd"),
        os.path.join("userdata", "PROT", "shadow"),
    )
    if not uf.check(request.args.get("subid"), request.form["passwd"]):
        return """
<link rel="stylesheet" href="static/css/style.css">
<title>Authentication failure</title>
<center><h1>Authentication failure</h1></center>
<center><a class="button" href="/">Go back</a></center>
            """
    if request.args.get("action") == "delete":
        # Delete
        with open(os.path.join("userdata", "PROT", "subs.json"), "r+") as subsf:
            curdata = json.loads(subsf.read())
            try:
                os.remove(
                    os.path.join("userdata", curdata[request.args.get("subid")]["file"])
                )  # remove the file...
            except OSError:
                #  for some reason the file did not exist... or maybe permissions messed up?
                pass

            uf.del_user(request.args.get("subid"))
            del curdata[request.args.get("subid")]  # remove that entry...

            subsf.seek(0)
            subsf.truncate()
            subsf.write(json.dumps(curdata))  # and write the new one

        return redirect("/")

    else:
        # Edit
        with open(os.path.join("userdata", "PROT", "subs.json"), "r+") as subsf:
            curdata = json.loads(subsf.read())
        with open(
            os.path.join("userdata", curdata[request.args.get("subid")]["file"]), "w"
        ) as cbf:
            cbf.write(request.form["codebox"])
        return redirect("/")


app.run(host="0.0.0.0", port=8080, debug=True)
