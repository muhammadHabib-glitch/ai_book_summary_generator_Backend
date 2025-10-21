from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import sha256
import random
import jwt
from datetime import datetime, timedelta
from functools import wraps


from Config import (
    Session,
    DEV_BYPASS_AUTH,
    JWT_SECRET,
    JWT_ALGO,
    JWT_EXPIRES_MIN,
)
from Model import Users, Library
from flask_mail import Message
from extensions import mail


# -------------------- helpers --------------------

def _make_token(user: Users) -> str:
    payload = {
        "sub": user.user_id,            # subject = userId
        "email": user.email,
        "plan": user.plan,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MIN),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def _hash_code(code: str) -> str:
    return sha256(code.encode("utf-8")).hexdigest()


def _new_otp():
    code = f"{random.randint(100000, 999999)}"
    return code, _hash_code(code), datetime.utcnow() + timedelta(minutes=10)


def _send_otp_email(to_email: str, code: str):
    try:
        msg = Message("Your KotuBrief verification code", recipients=[to_email])
        msg.body = f"Your verification code is: {code}\nIt expires in 10 minutes."
        mail.send(msg)
    except Exception as e:
        print("Email send failed:", e)


def _send_reset_email(to_email: str, code: str):
    try:
        msg = Message("Reset your KotuBrief password", recipients=[to_email])
        msg.body = f"Your password reset code is: {code}\nIt expires in 10 minutes."
        mail.send(msg)
    except Exception as e:
        print("Reset email send failed:", e)


def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # ---- DEV bypass (for mobile testing) ----
        if DEV_BYPASS_AUTH:
            uid = request.headers.get("X-User-Id") or request.args.get("userId")
            request.user = {"sub": int(uid) if uid else 1}  # default to user 1
            return fn(*args, **kwargs)

        # ---- normal JWT path ----
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing token"}), 401

        token = auth.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            request.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except Exception:
            return jsonify({"error": "Invalid token"}), 401

        return fn(*args, **kwargs)
    return wrapper


# -------------------- Auth: SignUp / Verify / SignIn / Me --------------------

def signup_controller():
    data = request.get_json() or {}
    full_name = data.get("full_name") or data.get("fullName")
    email = data.get("email")
    password = data.get("password")

    if not full_name or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    db = Session()
    try:
        user = db.query(Users).filter(Users.email == email).first()

        # A) Already confirmed -> block
        if user and user.email_confirmed:
            return jsonify({"error": "Email already registered."}), 400

        # B) Exists but NOT confirmed -> resend OTP (and update password if changed)
        if user and not user.email_confirmed:
            if not check_password_hash(user.password_hash, password):
                user.password_hash = generate_password_hash(password)
            code, hashed, expires = _new_otp()
            user.otp_hash = hashed
            user.otp_expires_at = expires
            user.otp_attempts = 0
            db.commit()
            _send_otp_email(email, code)
            return jsonify({"message": "OTP re-sent. Please verify your email."}), 200

        # C) New user -> create + send OTP
        new_user = Users(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
            plan="Demo",
            email_confirmed=False,
        )
        code, hashed, expires = _new_otp()
        new_user.otp_hash = hashed
        new_user.otp_expires_at = expires
        new_user.otp_attempts = 0

        db.add(new_user)
        db.commit()
        _send_otp_email(email, code)

        return jsonify({"message": "Signup successful. OTP sent to your email."}), 201

    except Exception as e:
        db.rollback()
        print("Signup Error:", e)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


def verify_otp_controller():
    data = request.get_json() or {}
    email = data.get("email")
    otp = data.get("otp")

    if not email or not otp:
        return jsonify({"error": "Email and OTP are required"}), 400

    db = Session()
    try:
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user.email_confirmed:
            return jsonify({"message": "Email already verified"}), 200

        if not user.otp_hash or not user.otp_expires_at:
            return jsonify({"error": "No OTP set. Please sign up again."}), 400
        if user.otp_expires_at < datetime.utcnow():
            return jsonify({"error": "OTP expired. Please request a new one."}), 400
        if user.otp_attempts >= 5:
            return jsonify({"error": "Too many attempts. Please request a new OTP."}), 429

        if _hash_code(str(otp)) != user.otp_hash:
            user.otp_attempts += 1
            db.commit()
            return jsonify({"error": "Invalid OTP"}), 400

        # success
        user.email_confirmed = True
        user.otp_hash = None
        user.otp_expires_at = None
        user.otp_attempts = 0
        db.commit()
        return jsonify({"message": "Email verified successfully"}), 200

    except Exception as e:
        db.rollback()
        print("Verify OTP Error:", e)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


def signin_controller():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db = Session()
    try:
        user = db.query(Users).filter(Users.email == email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid credentials"}), 401
        if not user.email_confirmed:
            return jsonify({"error": "Please verify your email first"}), 403

        token = _make_token(user)
        return jsonify({
            "message": "Login successful",
            "token": token,
            "userId": user.user_id,
            "fullName": user.full_name,
            "email": user.email,
            "plan": user.plan,
        }), 200

    except Exception as e:
        print("Signin Error:", e)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


def me_controller():
    user_id = request.user["sub"]
    db = Session()
    try:
        user = db.query(Users).filter(Users.user_id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({
            "userId": user.user_id,
            "fullName": user.full_name,
            "email": user.email,
            "plan": user.plan,
        }), 200
    finally:
        db.close()


# -------------------- Password Recovery --------------------

def forgot_password_controller():
    data = request.get_json() or {}
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    db = Session()
    try:
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            # don't leak which emails exist
            return jsonify({"message": "If this email exists, a reset code has been sent."}), 200

        if not user.email_confirmed:
            return jsonify({"error": "Please verify your email first."}), 400

        code, hashed, expires = _new_otp()
        user.otp_hash = hashed
        user.otp_expires_at = expires
        user.otp_attempts = 0
        db.commit()

        _send_reset_email(email, code)
        return jsonify({"message": "If this email exists, a reset code has been sent."}), 200

    except Exception as e:
        db.rollback()
        print("Forgot Password Error:", e)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


def reset_password_controller():
    data = request.get_json() or {}
    email = data.get("email")
    otp = data.get("otp")
    new_password = data.get("new_password") or data.get("newPassword")

    if not all([email, otp, new_password]):
        return jsonify({"error": "Email, OTP and new_password are required"}), 400

    db = Session()
    try:
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            return jsonify({"error": "Invalid OTP or email"}), 400

        if not user.otp_hash or not user.otp_expires_at:
            return jsonify({"error": "No valid reset is pending."}), 400
        if user.otp_expires_at < datetime.utcnow():
            return jsonify({"error": "OTP expired. Request a new reset."}), 400
        if user.otp_attempts >= 5:
            return jsonify({"error": "Too many attempts. Request a new reset."}), 429

        if _hash_code(str(otp)) != user.otp_hash:
            user.otp_attempts += 1
            db.commit()
            return jsonify({"error": "Invalid OTP"}), 400

        user.password_hash = generate_password_hash(new_password)
        user.otp_hash = None
        user.otp_expires_at = None
        user.otp_attempts = 0
        db.commit()
        return jsonify({"message": "Password updated successfully"}), 200

    except Exception as e:
        db.rollback()
        print("Reset Password Error:", e)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


# -------------------- Change Password (requires auth) ------------------------------

@token_required
def change_password_controller():
    data = request.get_json() or {}
    old_pw = data.get("old_password")
    new_pw = data.get("new_password")

    if not old_pw or not new_pw:
        return jsonify({"error": "old_password and new_password are required"}), 400

    user_id = request.user["sub"]
    db = Session()
    try:
        user = db.query(Users).filter(Users.user_id == user_id).first()
        if not user or not check_password_hash(user.password_hash, old_pw):
            return jsonify({"error": "Invalid old password"}), 400

        user.password_hash = generate_password_hash(new_pw)
        db.commit()
        return jsonify({"message": "Password changed"}), 200

    except Exception as e:
        db.rollback()
        print("Change Password Error:", e)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------

# -------------------------------  Create a Scraper/Importer Service
import re
import requests
from datetime import datetime
from flask import request, jsonify
from Config import Session
from Model import Books
REQUEST_TIMEOUT = 20

# ----------------- Helpers -----------------
# -------------------------- Upload Book Controller -----------------------------

def upload_book_controller():
    data = request.get_json() or {}
    required_fields = ["title", "author", "description", "user_id", "cover_image_url"]

    if not all(data.get(f) for f in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    db = Session()
    try:
        new_book = Books(
            user_id=data["user_id"],
            title=data["title"],
            author=data["author"],
            cover_image_url=data["cover_image_url"],  # ✅ save cover image
            description=data["description"],          # ✅ extracted PDF text
            created_at=datetime.utcnow()
        )
        db.add(new_book)
        db.commit()

        return jsonify({
            "message": "Book uploaded successfully",
            "book_id": new_book.book_id
        }), 201

    except Exception as e:
        db.rollback()
        print("Upload Book Error:", e)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


def get_user_books_controller(user_id):
    db = Session()
    try:
        books = db.query(Books).filter(Books.user_id == user_id).all()

        result = [
            {
                "book_id": b.book_id,
                "title": b.title,
                "author": b.author,
                "cover_image_url": b.cover_image_url,
                "main_category": b.main_category,
                "sub_category": b.sub_category,
                "description": b.description,
                "created_at": b.created_at.isoformat() if b.created_at else None
            }
            for b in books
        ]

        return jsonify(result), 200



    except Exception as e:
        print("Get User Books Error:", e)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


def update_book_controller(book_id):
    data = request.get_json() or {}
    new_description = data.get("description")

    if not new_description:
        return jsonify({"error": "Description is required"}), 400

    db = Session()
    try:
        book = db.query(Books).filter(Books.book_id == book_id).first()
        if not book:
            return jsonify({"error": "Book not found"}), 404

        book.description = new_description
        db.commit()
        return jsonify({"message": "Book updated successfully"}), 200

    except Exception as e:
        db.rollback()
        print("Update Book Error:", e)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()



def delete_book_controller(book_id):
    db = Session()
    try:
        book = db.query(Books).filter(Books.book_id == book_id).first()
        if not book:
            return jsonify({"error": "Book not found"}), 404

        db.delete(book)
        db.commit()
        return jsonify({"message": "Book deleted successfully"}), 200

    except Exception as e:
        db.rollback()
        print("Delete Book Error:", e)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()



def get_book_controller(book_id):
    db = Session()
    try:
        book = db.query(Books).filter(Books.book_id == book_id).first()
        if not book:
            return jsonify({"error": "Book not found"}), 404

        return jsonify({
            "book_id": book.book_id,
            "title": book.title,
            "author": book.author,
            "cover_image_url": book.cover_image_url,
            "main_category": book.main_category,
            "sub_category": book.sub_category,
            "description": book.description,
            "created_at": book.created_at.isoformat() if book.created_at else None
        }), 200

    except Exception as e:
        db.rollback()
        print("Get Book Error:", e)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


def get_user_books():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    db = Session()
    try:
        # Only fetch books that belong to this user
        books = (
            db.query(Books)
            .filter(Books.user_id == user_id)
            .all()
        )

        book_list = [
            {
                "book_id": b.book_id,
                "title": b.title,
                "author": b.author,
                "description": b.description,
                "user_id": b.user_id,
                "main_category": b.main_category,
                "sub_category": b.sub_category,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in books
        ]

        return jsonify({"books": book_list}), 200

    except Exception as e:
        print("Get User Books Error:", e)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()
