from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages,jsonify
import pymongo
import urllib.parse
import re
import html

app = Flask(__name__, static_url_path='/static')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Connect to MongoDB
client = pymongo.MongoClient("mongodb+srv://notesv2:notesv2@notesv2.ccbn6fh.mongodb.net/?retryWrites=true&w=majority&appName=notesV2")
db = client["notes"]
collection = db["practical"]
users_collection = db["users"]

def make_links(text):
    # Regular expression pattern for URLs
    url_pattern = re.compile(r'(https?://\S+)')

    return url_pattern.sub(r'<a href="\1" target="_blank">\1</a>', text)


def wrap_copyable_paragraphs(text):
    # Regular expression to find text within ```copy ... ```
    pattern = re.compile(r'```copy\n(.*?)\n```', re.DOTALL)
    
    # Replace matched text with HTML wrapped paragraphs
    wrapped_text = pattern.sub(r'<div class="copyable">\1</div>', text)
    return wrapped_text


@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
        public_notes = collection.find({"visibility": True})
        private_notes = collection.find({"username": username, "visibility": False})
        shared_notes = collection.find({"shared_with": username})  # Fetch notes shared with the user
        text_files = [doc["filename"] for doc in collection.find({}, {"filename": 1})]

        redirect_doc = collection.find_one({"redirect": {"$ne": ""}})
        if redirect_doc and collection.count_documents({"redirect": {"$ne": ""}}) == 1:
            return redirect(url_for('feature'))

        return render_template('index.html', text_files=text_files, username=username, public_notes=public_notes, private_notes=private_notes, shared_notes=shared_notes)
    
    return redirect(url_for('login'))



@app.route('/share', methods=['POST'])
def share_note():
    if 'username' in session:
        owner = session['username']
        filename = request.form['filename']
        shared_with = request.form['username']
        
        # Check if the user to share with exists
        target_user = users_collection.find_one({"username": shared_with})
        if not target_user:
            flash(f"User '{shared_with}' does not exist.")
            return redirect(url_for('index'))
        
        # Add the username to the note's 'shared_with' field
        collection.update_one(
            {"filename": filename, "username": owner},
            {"$addToSet": {"shared_with": shared_with}}  # Add without duplicates
        )
        flash(f"Note shared with {shared_with} successfully!")
        return redirect(url_for('index'))
    
    return redirect(url_for('login'))

@app.route('/get_usernames')
def get_usernames():
    query = request.args.get('query')
    if query:
        # Use MongoDB's $regex to find usernames that match the query
        matching_users = users_collection.find({"username": {"$regex": query, "$options": "i"}})
        usernames = [user["username"] for user in matching_users]
        return jsonify({'usernames': usernames})
    return jsonify({'usernames': []})



@app.route('/feature')
def feature():
    # Find a document where redirect is not an empty string
    redirect_document = collection.find_one({"redirect": {"$ne": ""}})
    if redirect_document:
        # If found, render a template or redirect to another route
        return render_template('feature.html', document=redirect_document)
    else:
        # If not found, render a default template or redirect to another route
        return render_template('feature.html', document=None)

@app.route('/text/<filename>')
def display_text(filename):
    decoded_filename = urllib.parse.unquote(filename)  # Decode the filename
    document = collection.find_one({"filename": decoded_filename})
    if document:
        file_content = document["content"]
        file_content = html.escape(file_content)  # Escape HTML content
        file_content = make_links(file_content)  # Convert URLs to clickable links
        file_content = wrap_copyable_paragraphs(file_content)  # Wrap copyable paragraphs
        return render_template('text.html', file_content=file_content)
    return "File not found"

@app.route('/create', methods=['GET', 'POST'])
def create_text():
    if session['username'] == 'Guest':
        flash("Guest account cannot create databases.")
        return redirect(url_for('index'))
    
    if 'username' in session:
        if request.method == 'POST':
            username = session['username']
            filename = request.form['file_name']
            content = request.form['file_content']
            account_password = request.form['password']  # Rename password field to account_password
            visibility = request.form['visibility'] 
            tags = request.form['tags'].split(',')
            tags = [tag.strip() for tag in tags]

            content = '\n'.join(content.splitlines())
            
            # Determine visibility
            if visibility == 'public':
                is_public = True
            else:
                is_public = False

            # Store form data in session to maintain values
            session['form_data'] = {
                'filename': filename,
                'content': content,
                'visibility': visibility,
                'tags': ', '.join(tags)
            }

            # Flash error message if account password is incorrect
            user = users_collection.find_one({"username": session['username']})
            if not user or account_password != user["password"]:
                flash("Incorrect account password, creation failed.")
                return redirect(url_for('create_text'))

            # Store data in MongoDB
            collection.insert_one({"username": username, "filename": filename, "content": content, "visibility": is_public, "tags": tags})
            
            # Remove stored form data from session
            session.pop('form_data', None)

            return redirect(url_for('index'))

        # Retrieve form data from session if available
        form_data = session.pop('form_data', None)
        return render_template('create.html', form_data=form_data)

    return redirect(url_for('login'))

@app.route('/edit/<filename>', methods=['GET', 'POST'])
def edit_text(filename):
    if session['username'] == 'Guest':
        flash("Guest account cannot edit databases.")
        return redirect(url_for('index'))

    filename = urllib.parse.unquote(filename)
    document = collection.find_one({"filename": filename})
    if document:
        if request.method == 'POST':
            entered_account_password = request.form['account_password']  # Prompt for account password
            user = users_collection.find_one({"username": session['username']})  # Retrieve user from users_collection
            if user and entered_account_password == user["password"]:  # Compare with the password stored in users_collection
                new_content = request.form['new_content']
                new_content = '\n'.join(new_content.splitlines())
                
                tags = request.form['tags'].split(',')
                tags = [tag.strip() for tag in tags]
                
                collection.update_one(
                    {"filename": filename}, 
                    {"$set": {"content": new_content, "tags": tags}}
                )
                flash("File edited successfully!")
                return redirect(url_for('index'))
            else:
                flash("Incorrect account password, editing failed.")
                return redirect(url_for('index'))
        else:
            file_content = document["content"]
            file_tags = document.get("tags", [])
            return render_template('edit.html', filename=filename, file_content=file_content, file_tags=file_tags)
    else:
        flash("File not found.")
        return redirect(url_for('index'))


@app.route('/delete/<filename>', methods=['GET', 'POST'])
def delete_text(filename):
    if session['username'] == 'Guest':
        flash("Guest account cannot delete databases.")
        return redirect(url_for('index'))

    document = collection.find_one({"filename": filename})
    if document:
        if request.method == 'POST':
            entered_account_password = request.form['account_password']  # Prompt for account password
            user = users_collection.find_one({"username": session['username']})  # Retrieve user from users_collection
            if user and entered_account_password == user["password"]:  # Compare with the password stored in users_collection
                collection.delete_one({"filename": filename})
                flash("File deleted successfully!")
                return redirect(url_for('index'))
            else:
                flash("Incorrect account password, deletion failed.")
                return redirect(url_for('index'))
        else:
            return render_template('delete.html', filename=filename)
    else:
        flash("File not found.")
        return redirect(url_for('index'))

@app.template_filter('nl2br')
def nl2br(value):
    return value.replace('\n', '<br>')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            flash("User already exists. Please choose a different username.")
            return redirect(url_for('register'))

        users_collection.insert_one({"username": username, "password": password})
        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users_collection.find_one({"username": username, "password": password})
        if user:
            session['username'] = username
            return redirect(url_for('index'))

        flash("Invalid username or password")
        return redirect(url_for('login'))
    
    if request.method == 'GET' and 'skip_login' in request.args:
        session['username'] = 'Guest'  # Setting a dummy username for non-logged-in users
        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search_notes():
    if request.method == 'POST':
        tag = request.form['tag']
        if tag:
            notes = collection.find({"tags": tag})
            return render_template('index.html', public_notes=notes, search_tag=tag)
    return redirect(url_for('index'))

@app.route('/search_content', methods=['POST'])
def search_content():
    if request.method == 'POST':
        content = request.form['content']
        if content:
            # Search for notes containing the specified content
            notes = collection.find({"content": {"$regex": content, "$options": "i"}})
            return render_template('index.html', public_notes=notes, search_content=content)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
