from ..extensions import db

class SheetMapping(db.Model):
    __tablename__ = "sheet_mapping"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey("user.id"), nullable=False)
    sheet_name = db.Column(db.String, nullable=False)  # e.g. "Steve", "Becky"
    user = db.relationship("User", backref="sheet_mapping", lazy=True)
