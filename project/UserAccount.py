class UserAccount(UserMixin, db.Model):
    __tablename__ = "UserAccount"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True,  nullable=False)
    password = db.Column(db.String(30), nullable=False)  # password_hash
    email = db.Column(db.String(70), unique=True, nullable=False)
    email_active = db.Column(db.Boolean, default=False, nullable=False)
    is_reset_password = db.Column(
        db.Boolean, default=False, nullable=False)  # for resetting password

   # i want to add a dictonary to the database of pairs of key:value and max lenght of a dictorany for a user can be 5

    i want to add a dictonary to the database where i will save the APIkey: api value pairs fo

    def _repr_():
        return 'User id: ' + str(self.id)
