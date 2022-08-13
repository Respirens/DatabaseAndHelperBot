from peewee import SqliteDatabase, Model, AutoField, TextField, DoubleField


class BaseModel(Model):
    class Meta:
        database = SqliteDatabase("products.sqlite")


class Product(BaseModel):
    id = AutoField()
    name = TextField()
    image = TextField()
    price = DoubleField()
